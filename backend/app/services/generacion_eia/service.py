"""
Servicio Orquestador de Generación de EIA (Fase 4).

Coordina la generación de documentos EIA completos,
integrando GeneradorTextoService, ValidadorSEAService y ExportadorService.
"""
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.db.models import Proyecto
from app.db.models.generacion_eia import (
    DocumentoEIA,
    VersionEIA,
    ObservacionValidacion,
    EstadoDocumento,
    EstadoObservacion
)
from app.db.models.generacion_eia import TemplateCapitulo
from app.schemas.generacion_eia import (
    DocumentoEIACreate,
    DocumentoEIAResponse,
    DocumentoEIAUpdate,
    CompilarDocumentoRequest,
    GenerarCapituloRequest,
    RegenerarSeccionRequest,
    VersionEIACreate,
    VersionEIAResponse,
    ProgresoGeneracion,
    GeneracionResponse,
    EstadisticasDocumento,
    ContenidoCapitulo,
    DocumentoCompletoResponse,
    ExportacionResponse,
    ResultadoValidacion,
    SeveridadEnum
)
from .generador_texto import GeneradorTextoService
from .validador_sea import ValidadorSEAService
from .exportador import ExportadorService


logger = logging.getLogger(__name__)


# Títulos estándar de capítulos EIA según SEA
CAPITULOS_EIA = {
    1: "Descripción del Proyecto",
    2: "Determinación y Justificación del Área de Influencia",
    3: "Línea de Base",
    4: "Predicción y Evaluación de Impactos Ambientales",
    5: "Plan de Medidas de Mitigación, Reparación y Compensación",
    6: "Plan de Prevención de Contingencias y Emergencias",
    7: "Plan de Seguimiento Ambiental",
    8: "Descripción de la Participación Ciudadana",
    9: "Relación con Políticas, Planes y Programas",
    10: "Compromisos Ambientales Voluntarios",
    11: "Ficha Resumen del EIA"
}


class GeneracionEIAService:
    """
    Servicio orquestador para la generación de documentos EIA.

    Responsabilidades:
    - Compilar documentos EIA completos
    - Generar capítulos individuales
    - Gestionar versionado
    - Calcular estadísticas y progreso
    - Integrar validación y exportación
    """

    def __init__(self):
        """Inicializa el servicio con sus dependencias."""
        self.generador = GeneradorTextoService()
        self.validador = ValidadorSEAService()
        self.exportador = ExportadorService()

    # =========================================================================
    # MÉTODOS PRINCIPALES - DOCUMENTO
    # =========================================================================

    async def compilar_documento(
        self,
        db: AsyncSession,
        proyecto_id: int,
        request: CompilarDocumentoRequest
    ) -> GeneracionResponse:
        """
        Compila un documento EIA completo generando todos los capítulos.

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto
            request: Configuración de compilación

        Returns:
            GeneracionResponse con resultados de la compilación
        """
        logger.info(f"Compilando documento EIA para proyecto {proyecto_id}")
        inicio = datetime.now()

        # 1. Obtener o crear documento
        documento = await self._get_or_create_documento(db, proyecto_id)

        # 2. Determinar capítulos a generar
        capitulos_a_generar = request.incluir_capitulos or list(range(1, 12))

        # Filtrar capítulos ya existentes si no se quiere regenerar
        if not request.regenerar_existentes and documento.contenido_capitulos:
            capitulos_existentes = [int(k) for k in documento.contenido_capitulos.keys()]
            capitulos_a_generar = [c for c in capitulos_a_generar if c not in capitulos_existentes]

        # 3. Generar capítulos
        capitulos_generados = []
        capitulos_con_error = []
        contenido_capitulos = documento.contenido_capitulos or {}

        for num_capitulo in capitulos_a_generar:
            try:
                logger.info(f"Generando capítulo {num_capitulo}...")
                resultado = await self.generador.generar_texto_capitulo(
                    db=db,
                    proyecto_id=proyecto_id,
                    capitulo_numero=num_capitulo
                )

                contenido_capitulos[str(num_capitulo)] = {
                    'titulo': resultado.get('titulo', CAPITULOS_EIA.get(num_capitulo, f'Capítulo {num_capitulo}')),
                    'contenido': resultado.get('contenido', ''),
                    'subsecciones': resultado.get('subsecciones', {}),
                    'estadisticas': resultado.get('estadisticas', {})
                }
                capitulos_generados.append(num_capitulo)

            except Exception as e:
                logger.error(f"Error generando capítulo {num_capitulo}: {e}")
                capitulos_con_error.append(num_capitulo)

        # 4. Actualizar documento
        documento.contenido_capitulos = contenido_capitulos
        documento.estadisticas = self._calcular_estadisticas(contenido_capitulos)
        documento.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(documento)

        # 5. Calcular tiempo total
        tiempo_total = (datetime.now() - inicio).total_seconds()

        logger.info(
            f"Compilación completada: {len(capitulos_generados)} capítulos generados, "
            f"{len(capitulos_con_error)} errores, {tiempo_total:.2f}s"
        )

        return GeneracionResponse(
            documento_id=documento.id,
            capitulos_generados=capitulos_generados,
            capitulos_con_error=capitulos_con_error,
            tiempo_total_segundos=tiempo_total,
            estadisticas=EstadisticasDocumento(**documento.estadisticas)
        )

    async def generar_capitulo(
        self,
        db: AsyncSession,
        proyecto_id: int,
        capitulo_numero: int,
        instrucciones_adicionales: Optional[str] = None,
        regenerar: bool = False
    ) -> ContenidoCapitulo:
        """
        Genera un capítulo específico del EIA.

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto
            capitulo_numero: Número del capítulo (1-11)
            instrucciones_adicionales: Instrucciones opcionales
            regenerar: Si True, regenera aunque ya exista

        Returns:
            ContenidoCapitulo con el contenido generado
        """
        logger.info(f"Generando capítulo {capitulo_numero} para proyecto {proyecto_id}")

        # Validar número de capítulo
        if capitulo_numero < 1 or capitulo_numero > 11:
            raise ValueError(f"Número de capítulo inválido: {capitulo_numero}. Debe estar entre 1 y 11.")

        # Obtener o crear documento
        documento = await self._get_or_create_documento(db, proyecto_id)

        # Verificar si ya existe y no se quiere regenerar
        contenido_capitulos = documento.contenido_capitulos or {}
        if str(capitulo_numero) in contenido_capitulos and not regenerar:
            logger.info(f"Capítulo {capitulo_numero} ya existe, retornando existente")
            cap_data = contenido_capitulos[str(capitulo_numero)]
            return ContenidoCapitulo(
                numero=capitulo_numero,
                titulo=cap_data.get('titulo', ''),
                contenido=cap_data.get('contenido', ''),
                subsecciones=cap_data.get('subsecciones', {}),
                figuras=cap_data.get('figuras', []),
                tablas=cap_data.get('tablas', []),
                referencias=cap_data.get('referencias', [])
            )

        # Generar con LLM
        resultado = await self.generador.generar_texto_capitulo(
            db=db,
            proyecto_id=proyecto_id,
            capitulo_numero=capitulo_numero,
            instrucciones_adicionales=instrucciones_adicionales
        )

        # Actualizar documento
        contenido_capitulos[str(capitulo_numero)] = {
            'titulo': resultado.get('titulo', CAPITULOS_EIA.get(capitulo_numero, f'Capítulo {capitulo_numero}')),
            'contenido': resultado.get('contenido', ''),
            'subsecciones': resultado.get('subsecciones', {}),
            'estadisticas': resultado.get('estadisticas', {})
        }

        documento.contenido_capitulos = contenido_capitulos
        documento.estadisticas = self._calcular_estadisticas(contenido_capitulos)
        documento.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(documento)

        return ContenidoCapitulo(
            numero=capitulo_numero,
            titulo=resultado.get('titulo', ''),
            contenido=resultado.get('contenido', ''),
            subsecciones=resultado.get('subsecciones', {}),
            figuras=resultado.get('figuras', []),
            tablas=resultado.get('tablas', []),
            referencias=resultado.get('referencias', [])
        )

    async def regenerar_seccion(
        self,
        db: AsyncSession,
        proyecto_id: int,
        request: RegenerarSeccionRequest
    ) -> str:
        """
        Regenera una sección específica de un capítulo.

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto
            request: Datos de la sección a regenerar

        Returns:
            Texto regenerado de la sección
        """
        logger.info(
            f"Regenerando sección {request.seccion_codigo} del capítulo "
            f"{request.capitulo_numero} para proyecto {proyecto_id}"
        )

        # Obtener documento
        documento = await self._get_documento_by_proyecto(db, proyecto_id)
        if not documento:
            raise ValueError(f"No existe documento EIA para proyecto {proyecto_id}")

        # Obtener contenido actual de la sección
        contenido_capitulos = documento.contenido_capitulos or {}
        capitulo_key = str(request.capitulo_numero)

        if capitulo_key not in contenido_capitulos:
            raise ValueError(f"Capítulo {request.capitulo_numero} no existe en el documento")

        capitulo = contenido_capitulos[capitulo_key]
        texto_actual = ""

        # Buscar en subsecciones
        subsecciones = capitulo.get('subsecciones', {})
        if request.seccion_codigo in subsecciones:
            texto_actual = subsecciones[request.seccion_codigo]

        # Expandir/regenerar con LLM
        texto_regenerado = await self.generador.expandir_seccion(
            db=db,
            proyecto_id=proyecto_id,
            capitulo_numero=request.capitulo_numero,
            seccion_codigo=request.seccion_codigo,
            texto_actual=texto_actual,
            instrucciones=request.instrucciones
        )

        # Actualizar sección
        subsecciones[request.seccion_codigo] = texto_regenerado
        capitulo['subsecciones'] = subsecciones

        # Reconstruir contenido del capítulo si la sección es parte del texto principal
        if request.seccion_codigo in capitulo.get('contenido', ''):
            # Actualizar subsección en el contenido general
            pass  # TODO: Implementar merge de sección en contenido principal

        contenido_capitulos[capitulo_key] = capitulo
        documento.contenido_capitulos = contenido_capitulos
        documento.updated_at = datetime.utcnow()

        await db.commit()

        return texto_regenerado

    async def get_documento(
        self,
        db: AsyncSession,
        proyecto_id: int,
        version: Optional[int] = None
    ) -> Optional[DocumentoEIAResponse]:
        """
        Obtiene el documento EIA de un proyecto.

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto
            version: Versión específica (None = última)

        Returns:
            DocumentoEIAResponse o None si no existe
        """
        documento = await self._get_documento_by_proyecto(db, proyecto_id)

        if not documento:
            return None

        # Si se pide una versión específica, buscar en historial
        if version is not None and version != documento.version:
            version_obj = await self._get_version(db, documento.id, version)
            if version_obj and version_obj.contenido_snapshot:
                # Crear respuesta con datos del snapshot
                return DocumentoEIAResponse(
                    id=documento.id,
                    proyecto_id=proyecto_id,
                    titulo=documento.titulo,
                    estado=documento.estado,
                    version=version,
                    contenido_capitulos=version_obj.contenido_snapshot,
                    metadatos=documento.metadatos,
                    validaciones=documento.validaciones,
                    estadisticas=documento.estadisticas,
                    created_at=documento.created_at,
                    updated_at=version_obj.created_at
                )

        return DocumentoEIAResponse(
            id=documento.id,
            proyecto_id=proyecto_id,
            titulo=documento.titulo,
            estado=documento.estado,
            version=documento.version,
            contenido_capitulos=documento.contenido_capitulos,
            metadatos=documento.metadatos,
            validaciones=documento.validaciones,
            estadisticas=documento.estadisticas,
            created_at=documento.created_at,
            updated_at=documento.updated_at
        )

    async def get_documento_completo(
        self,
        db: AsyncSession,
        proyecto_id: int
    ) -> Optional[DocumentoCompletoResponse]:
        """
        Obtiene el documento EIA completo con todas sus relaciones.

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto

        Returns:
            DocumentoCompletoResponse con documento, versiones, exportaciones, etc.
        """
        documento = await self._get_documento_by_proyecto(db, proyecto_id)

        if not documento:
            return None

        # Cargar relaciones
        query = select(DocumentoEIA).where(
            DocumentoEIA.id == documento.id
        ).options(
            selectinload(DocumentoEIA.versiones),
            selectinload(DocumentoEIA.exportaciones),
            selectinload(DocumentoEIA.observaciones)
        )

        result = await db.execute(query)
        doc_completo = result.scalar_one_or_none()

        if not doc_completo:
            return None

        # Construir respuesta
        documento_response = DocumentoEIAResponse(
            id=doc_completo.id,
            proyecto_id=proyecto_id,
            titulo=doc_completo.titulo,
            estado=doc_completo.estado,
            version=doc_completo.version,
            contenido_capitulos=doc_completo.contenido_capitulos,
            metadatos=doc_completo.metadatos,
            validaciones=doc_completo.validaciones,
            estadisticas=doc_completo.estadisticas,
            created_at=doc_completo.created_at,
            updated_at=doc_completo.updated_at
        )

        # Convertir versiones
        from app.schemas.generacion_eia import VersionEIAResponse, ExportacionResponse, ObservacionValidacionResponse

        versiones = [
            VersionEIAResponse(
                id=v.id,
                documento_id=v.documento_id,
                version=v.version,
                cambios=v.cambios,
                creado_por=v.creado_por,
                created_at=v.created_at
            )
            for v in doc_completo.versiones
        ]

        # Convertir exportaciones
        from app.db.models.generacion_eia import FormatoExportacion

        exportaciones = [
            ExportacionResponse(
                id=e.id,
                documento_id=e.documento_id,
                formato=e.formato,
                archivo_path=e.archivo_path,
                tamano_bytes=e.tamano_bytes,
                generado_exitoso=e.generado_exitoso,
                error_mensaje=e.error_mensaje,
                created_at=e.created_at,
                url_descarga=f"/api/v1/generacion/{proyecto_id}/export/{e.id}" if e.generado_exitoso else None
            )
            for e in doc_completo.exportaciones
        ]

        # Filtrar observaciones pendientes
        observaciones_pendientes = [
            ObservacionValidacionResponse(
                id=o.id,
                documento_id=o.documento_id,
                regla_id=o.regla_id,
                capitulo_numero=o.capitulo_numero,
                seccion=o.seccion,
                tipo_observacion=o.tipo_observacion,
                severidad=o.severidad,
                mensaje=o.mensaje,
                sugerencia=o.sugerencia,
                contexto=o.contexto,
                estado=o.estado,
                created_at=o.created_at,
                resuelta_at=o.resuelta_at
            )
            for o in doc_completo.observaciones
            if o.estado == EstadoObservacion.PENDIENTE.value
        ]

        # Calcular estadísticas
        estadisticas = EstadisticasDocumento(**(doc_completo.estadisticas or {}))

        # Calcular progreso por capítulo
        progreso = await self.get_progreso_generacion(db, proyecto_id)

        return DocumentoCompletoResponse(
            documento=documento_response,
            versiones=versiones,
            exportaciones=exportaciones,
            observaciones_pendientes=observaciones_pendientes,
            estadisticas=estadisticas,
            progreso_capitulos=progreso
        )

    # =========================================================================
    # MÉTODOS DE VERSIONADO
    # =========================================================================

    async def crear_version(
        self,
        db: AsyncSession,
        proyecto_id: int,
        cambios: str,
        creado_por: Optional[str] = None
    ) -> VersionEIAResponse:
        """
        Crea una nueva versión del documento (snapshot).

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto
            cambios: Descripción de los cambios
            creado_por: Usuario que crea la versión

        Returns:
            VersionEIAResponse con datos de la versión creada
        """
        documento = await self._get_documento_by_proyecto(db, proyecto_id)

        if not documento:
            raise ValueError(f"No existe documento EIA para proyecto {proyecto_id}")

        # Crear snapshot
        version = VersionEIA(
            documento_id=documento.id,
            version=documento.version,
            cambios=cambios,
            contenido_snapshot=documento.contenido_capitulos,
            creado_por=creado_por
        )

        db.add(version)

        # Incrementar versión del documento
        documento.version += 1
        documento.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(version)

        logger.info(f"Versión {version.version} creada para documento {documento.id}")

        return VersionEIAResponse(
            id=version.id,
            documento_id=version.documento_id,
            version=version.version,
            cambios=version.cambios,
            creado_por=version.creado_por,
            created_at=version.created_at
        )

    async def listar_versiones(
        self,
        db: AsyncSession,
        proyecto_id: int
    ) -> List[VersionEIAResponse]:
        """
        Lista todas las versiones de un documento.

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto

        Returns:
            Lista de VersionEIAResponse
        """
        documento = await self._get_documento_by_proyecto(db, proyecto_id)

        if not documento:
            return []

        query = select(VersionEIA).where(
            VersionEIA.documento_id == documento.id
        ).order_by(VersionEIA.version.desc())

        result = await db.execute(query)
        versiones = result.scalars().all()

        return [
            VersionEIAResponse(
                id=v.id,
                documento_id=v.documento_id,
                version=v.version,
                cambios=v.cambios,
                creado_por=v.creado_por,
                created_at=v.created_at
            )
            for v in versiones
        ]

    async def restaurar_version(
        self,
        db: AsyncSession,
        proyecto_id: int,
        version_a_restaurar: int
    ) -> DocumentoEIAResponse:
        """
        Restaura el documento a una versión anterior.

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto
            version_a_restaurar: Número de versión a restaurar

        Returns:
            DocumentoEIAResponse con el documento restaurado
        """
        documento = await self._get_documento_by_proyecto(db, proyecto_id)

        if not documento:
            raise ValueError(f"No existe documento EIA para proyecto {proyecto_id}")

        # Buscar versión
        version = await self._get_version(db, documento.id, version_a_restaurar)

        if not version:
            raise ValueError(f"Versión {version_a_restaurar} no encontrada")

        # Guardar versión actual antes de restaurar
        await self.crear_version(
            db, proyecto_id,
            f"Snapshot antes de restaurar a versión {version_a_restaurar}",
            "sistema"
        )

        # Restaurar contenido
        documento.contenido_capitulos = version.contenido_snapshot
        documento.estadisticas = self._calcular_estadisticas(version.contenido_snapshot or {})
        documento.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(documento)

        logger.info(f"Documento restaurado a versión {version_a_restaurar}")

        return DocumentoEIAResponse(
            id=documento.id,
            proyecto_id=proyecto_id,
            titulo=documento.titulo,
            estado=documento.estado,
            version=documento.version,
            contenido_capitulos=documento.contenido_capitulos,
            metadatos=documento.metadatos,
            validaciones=documento.validaciones,
            estadisticas=documento.estadisticas,
            created_at=documento.created_at,
            updated_at=documento.updated_at
        )

    # =========================================================================
    # MÉTODOS DE PROGRESO Y ESTADÍSTICAS
    # =========================================================================

    async def get_progreso_generacion(
        self,
        db: AsyncSession,
        proyecto_id: int
    ) -> List[ProgresoGeneracion]:
        """
        Obtiene el progreso de generación por capítulo.

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto

        Returns:
            Lista de ProgresoGeneracion por capítulo
        """
        documento = await self._get_documento_by_proyecto(db, proyecto_id)

        progreso = []
        contenido_capitulos = documento.contenido_capitulos if documento else {}

        for num in range(1, 12):
            capitulo_key = str(num)
            titulo = CAPITULOS_EIA.get(num, f'Capítulo {num}')

            if capitulo_key in contenido_capitulos:
                cap_data = contenido_capitulos[capitulo_key]
                contenido = cap_data.get('contenido', '')
                palabras = len(contenido.split()) if contenido else 0

                progreso.append(ProgresoGeneracion(
                    capitulo_numero=num,
                    titulo=cap_data.get('titulo', titulo),
                    estado='completado',
                    progreso_porcentaje=100,
                    palabras_generadas=palabras,
                    tiempo_estimado_segundos=None,
                    error=None
                ))
            else:
                progreso.append(ProgresoGeneracion(
                    capitulo_numero=num,
                    titulo=titulo,
                    estado='pendiente',
                    progreso_porcentaje=0,
                    palabras_generadas=0,
                    tiempo_estimado_segundos=60,  # Estimación
                    error=None
                ))

        return progreso

    # =========================================================================
    # MÉTODOS DE VALIDACIÓN (delegados a ValidadorSEAService)
    # =========================================================================

    async def validar_documento(
        self,
        db: AsyncSession,
        proyecto_id: int,
        nivel_severidad_minima: SeveridadEnum = SeveridadEnum.INFO
    ) -> ResultadoValidacion:
        """
        Valida el documento contra reglas SEA.

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto
            nivel_severidad_minima: Nivel mínimo de severidad a reportar

        Returns:
            ResultadoValidacion con observaciones
        """
        documento = await self._get_documento_by_proyecto(db, proyecto_id)

        if not documento:
            raise ValueError(f"No existe documento EIA para proyecto {proyecto_id}")

        resultado = await self.validador.validar_documento(
            db=db,
            documento_id=documento.id,
            nivel_severidad_minima=nivel_severidad_minima
        )

        # Guardar resultado en documento
        documento.validaciones = {
            'ultima_validacion': datetime.utcnow().isoformat(),
            'es_valido': resultado.es_valido,
            'total_observaciones': resultado.total_observaciones,
            'por_severidad': resultado.observaciones_por_severidad
        }

        await db.commit()

        return resultado

    # =========================================================================
    # MÉTODOS DE EXPORTACIÓN (delegados a ExportadorService)
    # =========================================================================

    async def exportar(
        self,
        db: AsyncSession,
        proyecto_id: int,
        formato: str,
        config: Optional[Dict[str, Any]] = None
    ) -> ExportacionResponse:
        """
        Exporta el documento a un formato específico.

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto
            formato: Formato de exportación (pdf, docx, eseia_xml)
            config: Configuración de exportación

        Returns:
            ExportacionResponse con datos de la exportación
        """
        documento = await self._get_documento_by_proyecto(db, proyecto_id)

        if not documento:
            raise ValueError(f"No existe documento EIA para proyecto {proyecto_id}")

        formato_lower = formato.lower()

        if formato_lower == 'pdf':
            from app.schemas.generacion_eia import ConfiguracionPDF
            pdf_config = ConfiguracionPDF(**config) if config else None
            return await self.exportador.exportar_pdf(db, documento.id, pdf_config)

        elif formato_lower == 'docx':
            from app.schemas.generacion_eia import ConfiguracionDOCX
            docx_config = ConfiguracionDOCX(**config) if config else None
            return await self.exportador.exportar_docx(db, documento.id, docx_config)

        elif formato_lower in ('eseia_xml', 'eseia', 'xml'):
            from app.schemas.generacion_eia import ConfiguracionESEIA
            eseia_config = ConfiguracionESEIA(**config) if config else None
            return await self.exportador.exportar_eseia(db, documento.id, eseia_config)

        else:
            raise ValueError(f"Formato de exportación no soportado: {formato}")

    async def listar_exportaciones(
        self,
        db: AsyncSession,
        proyecto_id: int
    ) -> List[ExportacionResponse]:
        """
        Lista todas las exportaciones de un documento.

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto

        Returns:
            Lista de ExportacionResponse
        """
        documento = await self._get_documento_by_proyecto(db, proyecto_id)

        if not documento:
            return []

        exportaciones = await self.exportador.listar_exportaciones(db, documento.id)

        return [
            ExportacionResponse(
                id=e.id,
                documento_id=e.documento_id,
                formato=e.formato,
                archivo_path=e.archivo_path,
                tamano_bytes=e.tamano_bytes,
                generado_exitoso=e.generado_exitoso,
                error_mensaje=e.error_mensaje,
                created_at=e.created_at,
                url_descarga=f"/api/v1/generacion/{proyecto_id}/export/{e.id}" if e.generado_exitoso else None
            )
            for e in exportaciones
        ]

    # =========================================================================
    # MÉTODOS DE ACTUALIZACIÓN DE DOCUMENTO
    # =========================================================================

    async def actualizar_documento(
        self,
        db: AsyncSession,
        proyecto_id: int,
        update_data: DocumentoEIAUpdate
    ) -> DocumentoEIAResponse:
        """
        Actualiza los datos de un documento.

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto
            update_data: Datos a actualizar

        Returns:
            DocumentoEIAResponse actualizado
        """
        documento = await self._get_documento_by_proyecto(db, proyecto_id)

        if not documento:
            raise ValueError(f"No existe documento EIA para proyecto {proyecto_id}")

        # Actualizar campos
        if update_data.titulo is not None:
            documento.titulo = update_data.titulo

        if update_data.estado is not None:
            documento.estado = update_data.estado.value

        if update_data.contenido_capitulos is not None:
            documento.contenido_capitulos = {
                str(k): v.model_dump() if hasattr(v, 'model_dump') else v
                for k, v in update_data.contenido_capitulos.items()
            }
            documento.estadisticas = self._calcular_estadisticas(documento.contenido_capitulos)

        if update_data.metadatos is not None:
            documento.metadatos = update_data.metadatos.model_dump() if hasattr(update_data.metadatos, 'model_dump') else update_data.metadatos

        documento.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(documento)

        return DocumentoEIAResponse(
            id=documento.id,
            proyecto_id=proyecto_id,
            titulo=documento.titulo,
            estado=documento.estado,
            version=documento.version,
            contenido_capitulos=documento.contenido_capitulos,
            metadatos=documento.metadatos,
            validaciones=documento.validaciones,
            estadisticas=documento.estadisticas,
            created_at=documento.created_at,
            updated_at=documento.updated_at
        )

    async def actualizar_capitulo(
        self,
        db: AsyncSession,
        proyecto_id: int,
        capitulo_numero: int,
        contenido: str,
        titulo: Optional[str] = None
    ) -> ContenidoCapitulo:
        """
        Actualiza el contenido de un capítulo específico.

        Args:
            db: Sesión de base de datos
            proyecto_id: ID del proyecto
            capitulo_numero: Número del capítulo
            contenido: Nuevo contenido
            titulo: Nuevo título (opcional)

        Returns:
            ContenidoCapitulo actualizado
        """
        documento = await self._get_documento_by_proyecto(db, proyecto_id)

        if not documento:
            raise ValueError(f"No existe documento EIA para proyecto {proyecto_id}")

        contenido_capitulos = documento.contenido_capitulos or {}
        capitulo_key = str(capitulo_numero)

        # Obtener o crear capítulo
        if capitulo_key in contenido_capitulos:
            cap_data = contenido_capitulos[capitulo_key]
        else:
            cap_data = {
                'titulo': CAPITULOS_EIA.get(capitulo_numero, f'Capítulo {capitulo_numero}'),
                'contenido': '',
                'subsecciones': {}
            }

        # Actualizar
        cap_data['contenido'] = contenido
        if titulo:
            cap_data['titulo'] = titulo

        # Recalcular estadísticas del capítulo
        cap_data['estadisticas'] = {
            'palabras': len(contenido.split()),
            'caracteres': len(contenido)
        }

        contenido_capitulos[capitulo_key] = cap_data
        documento.contenido_capitulos = contenido_capitulos
        documento.estadisticas = self._calcular_estadisticas(contenido_capitulos)
        documento.updated_at = datetime.utcnow()

        await db.commit()

        return ContenidoCapitulo(
            numero=capitulo_numero,
            titulo=cap_data['titulo'],
            contenido=contenido,
            subsecciones=cap_data.get('subsecciones', {}),
            figuras=[],
            tablas=[],
            referencias=[]
        )

    # =========================================================================
    # MÉTODOS PRIVADOS
    # =========================================================================

    async def _get_or_create_documento(
        self,
        db: AsyncSession,
        proyecto_id: int
    ) -> DocumentoEIA:
        """Obtiene o crea el documento EIA de un proyecto."""
        documento = await self._get_documento_by_proyecto(db, proyecto_id)

        if documento:
            return documento

        # Obtener información del proyecto para el título
        proyecto = await self._get_proyecto(db, proyecto_id)

        # Crear nuevo documento
        documento = DocumentoEIA(
            proyecto_id=proyecto_id,
            titulo=f"Estudio de Impacto Ambiental - {proyecto.nombre}" if proyecto else f"EIA Proyecto {proyecto_id}",
            version=1,
            estado=EstadoDocumento.BORRADOR.value,
            contenido_capitulos={},
            metadatos={
                'fecha_elaboracion': datetime.now().isoformat(),
                'empresa_consultora': None,
                'autores': [],
                'revisores': []
            },
            estadisticas={
                'total_paginas': 0,
                'total_palabras': 0,
                'total_figuras': 0,
                'total_tablas': 0,
                'total_referencias': 0,
                'capitulos_completados': 0,
                'porcentaje_completitud': 0.0
            }
        )

        db.add(documento)
        await db.commit()
        await db.refresh(documento)

        logger.info(f"Documento EIA creado para proyecto {proyecto_id}")

        return documento

    async def _get_documento_by_proyecto(
        self,
        db: AsyncSession,
        proyecto_id: int
    ) -> Optional[DocumentoEIA]:
        """Obtiene el documento EIA de un proyecto."""
        query = select(DocumentoEIA).where(
            DocumentoEIA.proyecto_id == proyecto_id
        ).order_by(DocumentoEIA.id.desc())

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def _get_proyecto(
        self,
        db: AsyncSession,
        proyecto_id: int
    ) -> Optional[Proyecto]:
        """Obtiene un proyecto por ID."""
        query = select(Proyecto).where(Proyecto.id == proyecto_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def _get_version(
        self,
        db: AsyncSession,
        documento_id: int,
        version: int
    ) -> Optional[VersionEIA]:
        """Obtiene una versión específica de un documento."""
        query = select(VersionEIA).where(
            VersionEIA.documento_id == documento_id,
            VersionEIA.version == version
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    def _calcular_estadisticas(
        self,
        contenido_capitulos: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calcula estadísticas del documento."""
        total_palabras = 0
        total_figuras = 0
        total_tablas = 0
        capitulos_completados = 0

        for num_str, cap_data in contenido_capitulos.items():
            if isinstance(cap_data, dict):
                contenido = cap_data.get('contenido', '')
                if contenido:
                    capitulos_completados += 1
                    total_palabras += len(contenido.split())

                    # Contar figuras y tablas (aproximado)
                    total_figuras += contenido.lower().count('figura ')
                    total_tablas += contenido.lower().count('tabla ')

        # Estimar páginas (~400 palabras por página)
        total_paginas = max(1, total_palabras // 400)

        # Calcular porcentaje de completitud (11 capítulos)
        porcentaje = (capitulos_completados / 11) * 100

        return {
            'total_paginas': total_paginas,
            'total_palabras': total_palabras,
            'total_figuras': total_figuras,
            'total_tablas': total_tablas,
            'total_referencias': 0,  # TODO: Implementar conteo de referencias
            'capitulos_completados': capitulos_completados,
            'porcentaje_completitud': round(porcentaje, 1)
        }
