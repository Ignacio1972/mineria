"""
Servicio de Validación de Documentos EIA según requisitos SEA.

Valida completitud, formato, referencias cruzadas y normativa.
"""
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.generacion_eia import (
    DocumentoEIA,
    ReglaValidacionSEA,
    ObservacionValidacion,
    Severidad,
    EstadoObservacion
)
from app.schemas.generacion_eia import (
    ResultadoValidacion,
    ObservacionValidacionResponse,
    SeveridadEnum
)


logger = logging.getLogger(__name__)


class ValidadorSEAService:
    """Servicio para validar documentos EIA contra requisitos SEA."""

    async def validar_documento(
        self,
        db: AsyncSession,
        documento_id: int,
        nivel_severidad_minima: SeveridadEnum = SeveridadEnum.INFO
    ) -> ResultadoValidacion:
        """
        Valida un documento completo contra reglas SEA.

        Args:
            db: Sesión de base de datos
            documento_id: ID del documento a validar
            nivel_severidad_minima: Nivel mínimo de severidad a reportar

        Returns:
            ResultadoValidacion con observaciones detectadas
        """
        logger.info(f"Validando documento {documento_id}")

        # 1. Obtener documento
        query = select(DocumentoEIA).where(DocumentoEIA.id == documento_id)
        result = await db.execute(query)
        documento = result.scalar_one_or_none()

        if not documento:
            raise ValueError(f"Documento {documento_id} no encontrado")

        # 2. Obtener reglas aplicables
        reglas = await self._get_reglas_aplicables(db, documento.proyecto_id)

        # 3. Ejecutar validaciones
        observaciones = []
        for regla in reglas:
            obs = await self._aplicar_regla(db, documento, regla)
            if obs:
                observaciones.extend(obs)

        # 4. Filtrar por severidad
        observaciones_filtradas = [
            obs for obs in observaciones
            if self._comparar_severidad(obs.severidad, nivel_severidad_minima) >= 0
        ]

        # 5. Construir respuesta
        resultado = self._construir_resultado(documento_id, observaciones_filtradas)

        logger.info(f"Validación completada: {len(observaciones_filtradas)} observaciones")

        return resultado

    async def validar_capitulo(
        self,
        db: AsyncSession,
        documento_id: int,
        capitulo_numero: int
    ) -> List[ObservacionValidacionResponse]:
        """
        Valida un capítulo específico.

        Args:
            db: Sesión de base de datos
            documento_id: ID del documento
            capitulo_numero: Número del capítulo

        Returns:
            Lista de observaciones del capítulo
        """
        logger.info(f"Validando capítulo {capitulo_numero} del documento {documento_id}")

        # Obtener documento
        query = select(DocumentoEIA).where(DocumentoEIA.id == documento_id)
        result = await db.execute(query)
        documento = result.scalar_one_or_none()

        if not documento:
            raise ValueError(f"Documento {documento_id} no encontrado")

        # Obtener reglas del capítulo
        query_reglas = select(ReglaValidacionSEA).where(
            ReglaValidacionSEA.activo == True,
            (ReglaValidacionSEA.capitulo_numero == capitulo_numero) |
            (ReglaValidacionSEA.capitulo_numero == None)
        )

        result = await db.execute(query_reglas)
        reglas = result.scalars().all()

        # Aplicar reglas
        observaciones = []
        for regla in reglas:
            obs = await self._aplicar_regla(db, documento, regla)
            if obs:
                observaciones.extend(obs)

        return observaciones

    # =========================================================================
    # Métodos privados
    # =========================================================================

    async def _get_reglas_aplicables(
        self,
        db: AsyncSession,
        proyecto_id: int
    ) -> List[ReglaValidacionSEA]:
        """Obtiene reglas de validación aplicables al proyecto."""
        # Obtener tipo de proyecto
        from app.db.models import Proyecto
        query = select(Proyecto.tipo_proyecto_id).where(Proyecto.id == proyecto_id)
        result = await db.execute(query)
        tipo_proyecto_id = result.scalar_one_or_none()

        # Obtener reglas generales y específicas del tipo
        query_reglas = select(ReglaValidacionSEA).where(
            ReglaValidacionSEA.activo == True,
            (ReglaValidacionSEA.tipo_proyecto_id == tipo_proyecto_id) |
            (ReglaValidacionSEA.tipo_proyecto_id == None)
        )

        result = await db.execute(query_reglas)
        return result.scalars().all()

    async def _aplicar_regla(
        self,
        db: AsyncSession,
        documento: DocumentoEIA,
        regla: ReglaValidacionSEA
    ) -> List[ObservacionValidacionResponse]:
        """
        Aplica una regla de validación al documento.

        Args:
            db: Sesión de base de datos
            documento: Documento a validar
            regla: Regla a aplicar

        Returns:
            Lista de observaciones (vacía si la regla se cumple)
        """
        try:
            criterio = regla.criterio
            tipo_validacion = criterio.get('tipo')

            if tipo_validacion == 'campo_requerido':
                return await self._validar_campo_requerido(documento, regla, criterio)

            elif tipo_validacion == 'campos_requeridos':
                return await self._validar_campos_requeridos(documento, regla, criterio)

            elif tipo_validacion == 'longitud_minima':
                return await self._validar_longitud_minima(documento, regla, criterio)

            elif tipo_validacion == 'longitud_maxima':
                return await self._validar_longitud_maxima(documento, regla, criterio)

            else:
                logger.warning(f"Tipo de validación no soportado: {tipo_validacion}")
                return []

        except Exception as e:
            logger.error(f"Error aplicando regla {regla.codigo_regla}: {e}")
            return []

    async def _validar_campo_requerido(
        self,
        documento: DocumentoEIA,
        regla: ReglaValidacionSEA,
        criterio: Dict[str, Any]
    ) -> List[ObservacionValidacionResponse]:
        """Valida que un campo requerido esté presente."""
        campo = criterio.get('campo')
        capitulo_numero = regla.capitulo_numero

        # Verificar en diferentes ubicaciones
        valor_encontrado = False

        # 1. Nivel de documento
        if campo == 'titulo' and documento.titulo:
            valor_encontrado = True

        # 2. Nivel de metadatos
        elif documento.metadatos and campo in documento.metadatos:
            valor_encontrado = bool(documento.metadatos[campo])

        # 3. Nivel de capítulo
        elif capitulo_numero and documento.contenido_capitulos:
            capitulo_key = str(capitulo_numero)
            if capitulo_key in documento.contenido_capitulos:
                capitulo = documento.contenido_capitulos[capitulo_key]
                if isinstance(capitulo, dict) and campo in capitulo:
                    valor_encontrado = bool(capitulo[campo])

        if not valor_encontrado:
            return [ObservacionValidacionResponse(
                id=0,  # Se generará al guardar
                documento_id=documento.id,
                regla_id=regla.id,
                capitulo_numero=capitulo_numero,
                seccion=None,
                tipo_observacion=regla.tipo_validacion,
                severidad=regla.severidad,
                mensaje=regla.mensaje_error,
                sugerencia=regla.mensaje_sugerencia,
                contexto={'campo': campo, 'regla': regla.codigo_regla},
                estado=EstadoObservacion.PENDIENTE.value,
                created_at=None,  # Se generará al guardar
                resuelta_at=None
            )]

        return []

    async def _validar_campos_requeridos(
        self,
        documento: DocumentoEIA,
        regla: ReglaValidacionSEA,
        criterio: Dict[str, Any]
    ) -> List[ObservacionValidacionResponse]:
        """Valida que múltiples campos requeridos estén presentes."""
        campos = criterio.get('campos', [])
        campos_faltantes = []

        for campo in campos:
            if not documento.metadatos or campo not in documento.metadatos:
                campos_faltantes.append(campo)

        if campos_faltantes:
            return [ObservacionValidacionResponse(
                id=0,
                documento_id=documento.id,
                regla_id=regla.id,
                capitulo_numero=regla.capitulo_numero,
                seccion=None,
                tipo_observacion=regla.tipo_validacion,
                severidad=regla.severidad,
                mensaje=f"{regla.mensaje_error}. Faltantes: {', '.join(campos_faltantes)}",
                sugerencia=regla.mensaje_sugerencia,
                contexto={'campos_faltantes': campos_faltantes},
                estado=EstadoObservacion.PENDIENTE.value,
                created_at=None,
                resuelta_at=None
            )]

        return []

    async def _validar_longitud_minima(
        self,
        documento: DocumentoEIA,
        regla: ReglaValidacionSEA,
        criterio: Dict[str, Any]
    ) -> List[ObservacionValidacionResponse]:
        """Valida longitud mínima de un capítulo."""
        palabras_minimas = criterio.get('palabras', 0)
        capitulo_numero = regla.capitulo_numero

        if not capitulo_numero or not documento.contenido_capitulos:
            return []

        capitulo_key = str(capitulo_numero)
        if capitulo_key not in documento.contenido_capitulos:
            return []

        capitulo = documento.contenido_capitulos[capitulo_key]
        contenido = capitulo.get('contenido', '') if isinstance(capitulo, dict) else str(capitulo)
        palabras = len(contenido.split())

        if palabras < palabras_minimas:
            return [ObservacionValidacionResponse(
                id=0,
                documento_id=documento.id,
                regla_id=regla.id,
                capitulo_numero=capitulo_numero,
                seccion=None,
                tipo_observacion=regla.tipo_validacion,
                severidad=regla.severidad,
                mensaje=f"{regla.mensaje_error} (actual: {palabras} palabras, mínimo: {palabras_minimas})",
                sugerencia=regla.mensaje_sugerencia,
                contexto={'palabras_actuales': palabras, 'palabras_minimas': palabras_minimas},
                estado=EstadoObservacion.PENDIENTE.value,
                created_at=None,
                resuelta_at=None
            )]

        return []

    async def _validar_longitud_maxima(
        self,
        documento: DocumentoEIA,
        regla: ReglaValidacionSEA,
        criterio: Dict[str, Any]
    ) -> List[ObservacionValidacionResponse]:
        """Valida longitud máxima de un capítulo."""
        palabras_maximas = criterio.get('palabras', float('inf'))
        capitulo_numero = regla.capitulo_numero

        if not capitulo_numero or not documento.contenido_capitulos:
            return []

        capitulo_key = str(capitulo_numero)
        if capitulo_key not in documento.contenido_capitulos:
            return []

        capitulo = documento.contenido_capitulos[capitulo_key]
        contenido = capitulo.get('contenido', '') if isinstance(capitulo, dict) else str(capitulo)
        palabras = len(contenido.split())

        if palabras > palabras_maximas:
            return [ObservacionValidacionResponse(
                id=0,
                documento_id=documento.id,
                regla_id=regla.id,
                capitulo_numero=capitulo_numero,
                seccion=None,
                tipo_observacion=regla.tipo_validacion,
                severidad=regla.severidad,
                mensaje=f"{regla.mensaje_error} (actual: {palabras} palabras, máximo: {palabras_maximas})",
                sugerencia=regla.mensaje_sugerencia,
                contexto={'palabras_actuales': palabras, 'palabras_maximas': palabras_maximas},
                estado=EstadoObservacion.PENDIENTE.value,
                created_at=None,
                resuelta_at=None
            )]

        return []

    def _comparar_severidad(self, severidad: str, minima: SeveridadEnum) -> int:
        """
        Compara niveles de severidad.

        Returns:
            1 si severidad > minima, 0 si igual, -1 si menor
        """
        niveles = {
            'info': 0,
            'warning': 1,
            'error': 2
        }

        nivel_actual = niveles.get(severidad.lower(), 0)
        nivel_minimo = niveles.get(minima.value.lower(), 0)

        return 1 if nivel_actual > nivel_minimo else (0 if nivel_actual == nivel_minimo else -1)

    def _construir_resultado(
        self,
        documento_id: int,
        observaciones: List[ObservacionValidacionResponse]
    ) -> ResultadoValidacion:
        """Construye el resultado de validación."""
        # Contar por severidad
        conteo_severidad = {'error': 0, 'warning': 0, 'info': 0}
        conteo_capitulo = {}

        for obs in observaciones:
            conteo_severidad[obs.severidad] = conteo_severidad.get(obs.severidad, 0) + 1

            if obs.capitulo_numero:
                conteo_capitulo[obs.capitulo_numero] = conteo_capitulo.get(obs.capitulo_numero, 0) + 1

        # Determinar si es válido (sin errores críticos)
        es_valido = conteo_severidad['error'] == 0

        # Mensaje resumen
        if es_valido:
            if conteo_severidad['warning'] == 0:
                mensaje = "✓ Documento válido. No se encontraron observaciones."
            else:
                mensaje = f"⚠ Documento válido con {conteo_severidad['warning']} advertencias."
        else:
            mensaje = f"✗ Documento no válido. Se encontraron {conteo_severidad['error']} errores."

        return ResultadoValidacion(
            documento_id=documento_id,
            total_observaciones=len(observaciones),
            observaciones_por_severidad=conteo_severidad,
            observaciones_por_capitulo=conteo_capitulo,
            observaciones=observaciones,
            es_valido=es_valido,
            mensaje_resumen=mensaje
        )
