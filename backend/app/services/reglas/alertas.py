"""
Sistema de Alertas por Tipo de Impacto

Genera y gestiona alertas ambientales clasificadas por tipo de impacto,
componente ambiental afectado y nivel de criticidad.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from datetime import datetime

logger = logging.getLogger(__name__)


class NivelAlerta(str, Enum):
    """Nivel de severidad de la alerta"""
    CRITICA = "CRITICA"      # Requiere acción inmediata / puede impedir proyecto
    ALTA = "ALTA"            # Requiere atención prioritaria
    MEDIA = "MEDIA"          # Requiere evaluación detallada
    BAJA = "BAJA"            # Informativa / requiere monitoreo
    INFO = "INFO"            # Puramente informativa


class CategoriaImpacto(str, Enum):
    """Categorías de impacto ambiental"""
    BIODIVERSIDAD = "BIODIVERSIDAD"
    RECURSOS_HIDRICOS = "RECURSOS_HIDRICOS"
    AIRE_RUIDO = "AIRE_RUIDO"
    SUELO = "SUELO"
    PATRIMONIO = "PATRIMONIO"
    MEDIO_HUMANO = "MEDIO_HUMANO"
    PAISAJE = "PAISAJE"
    RIESGOS = "RIESGOS"


class ComponenteAmbiental(str, Enum):
    """Componentes ambientales del SEIA"""
    CLIMA_METEOROLOGIA = "clima_meteorologia"
    CALIDAD_AIRE = "calidad_aire"
    RUIDO_VIBRACIONES = "ruido_vibraciones"
    GEOLOGIA = "geologia"
    GEOMORFOLOGIA = "geomorfologia"
    HIDROLOGIA = "hidrologia"
    HIDROGEOLOGIA = "hidrogeologia"
    EDAFOLOGIA = "edafologia"
    FLORA_VEGETACION = "flora_vegetacion"
    FAUNA = "fauna"
    ECOSISTEMAS_ACUATICOS = "ecosistemas_acuaticos"
    PATRIMONIO_ARQUEOLOGICO = "patrimonio_arqueologico"
    PATRIMONIO_CULTURAL = "patrimonio_cultural"
    PAISAJE = "paisaje"
    TURISMO = "turismo"
    AREAS_PROTEGIDAS = "areas_protegidas"
    MEDIO_HUMANO = "medio_humano"
    PUEBLOS_INDIGENAS = "pueblos_indigenas"


@dataclass
class Alerta:
    """Representa una alerta ambiental"""
    id: str
    nivel: NivelAlerta
    categoria: CategoriaImpacto
    titulo: str
    descripcion: str
    componentes_afectados: list[ComponenteAmbiental] = field(default_factory=list)
    elementos_gis: list[dict] = field(default_factory=list)
    normativa_relacionada: list[str] = field(default_factory=list)
    acciones_requeridas: list[str] = field(default_factory=list)
    permisos_sectoriales: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    fecha_generacion: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nivel": self.nivel.value,
            "categoria": self.categoria.value,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "componentes_afectados": [c.value for c in self.componentes_afectados],
            "elementos_gis": self.elementos_gis,
            "normativa_relacionada": self.normativa_relacionada,
            "acciones_requeridas": self.acciones_requeridas,
            "permisos_sectoriales": self.permisos_sectoriales,
            "metadata": self.metadata,
            "fecha_generacion": self.fecha_generacion.isoformat(),
        }


class SistemaAlertas:
    """
    Sistema de generación y gestión de alertas ambientales.

    Analiza los resultados GIS y datos del proyecto para generar
    alertas clasificadas por tipo de impacto y componente ambiental.
    """

    # Mapeo de permisos ambientales sectoriales (PAS)
    PAS_POR_COMPONENTE = {
        ComponenteAmbiental.CALIDAD_AIRE: ["PAS 138 - Emisiones atmosféricas"],
        ComponenteAmbiental.RUIDO_VIBRACIONES: ["PAS 138 - Emisiones (ruido)"],
        ComponenteAmbiental.HIDROLOGIA: [
            "PAS 155 - Obras en cauces",
            "PAS 156 - Extracción de aguas"
        ],
        ComponenteAmbiental.HIDROGEOLOGIA: [
            "PAS 156 - Derechos de agua",
            "PAS 157 - Obras de regularización"
        ],
        ComponenteAmbiental.FLORA_VEGETACION: [
            "PAS 148 - Plan de manejo forestal",
            "PAS 150 - Corta de bosque nativo"
        ],
        ComponenteAmbiental.FAUNA: [
            "PAS 146 - Caza o captura de fauna",
            "PAS 147 - Recolección de huevos/crías"
        ],
        ComponenteAmbiental.PATRIMONIO_ARQUEOLOGICO: [
            "PAS 132 - Intervención de monumentos"
        ],
        ComponenteAmbiental.AREAS_PROTEGIDAS: [
            "PAS 160 - Intervención en SNASPE"
        ],
        ComponenteAmbiental.PUEBLOS_INDIGENAS: [
            "Consulta Indígena (Convenio 169 OIT)"
        ],
    }

    def __init__(self):
        self.alertas: list[Alerta] = []
        self._contador_id = 0
        logger.info("SistemaAlertas inicializado")

    def _generar_id(self) -> str:
        """Genera un ID único para la alerta."""
        self._contador_id += 1
        return f"ALR-{self._contador_id:04d}"

    def generar_alertas(
        self,
        resultado_gis: dict[str, Any],
        datos_proyecto: dict[str, Any]
    ) -> list[Alerta]:
        """
        Genera alertas basadas en el análisis GIS y datos del proyecto.

        Args:
            resultado_gis: Resultado del análisis espacial
            datos_proyecto: Datos del proyecto minero

        Returns:
            Lista de alertas generadas
        """
        logger.info("Generando alertas ambientales")
        self.alertas = []
        self._contador_id = 0

        # Generar alertas por categoría
        self._alertas_biodiversidad(resultado_gis, datos_proyecto)
        self._alertas_recursos_hidricos(resultado_gis, datos_proyecto)
        self._alertas_medio_humano(resultado_gis, datos_proyecto)
        self._alertas_patrimonio(resultado_gis, datos_proyecto)
        self._alertas_aire_ruido(resultado_gis, datos_proyecto)
        self._alertas_paisaje(resultado_gis, datos_proyecto)

        # Ordenar por nivel de severidad
        orden_severidad = {
            NivelAlerta.CRITICA: 0,
            NivelAlerta.ALTA: 1,
            NivelAlerta.MEDIA: 2,
            NivelAlerta.BAJA: 3,
            NivelAlerta.INFO: 4,
        }
        self.alertas.sort(key=lambda a: orden_severidad[a.nivel])

        logger.info(f"Generadas {len(self.alertas)} alertas")
        return self.alertas

    def _alertas_biodiversidad(
        self,
        resultado_gis: dict[str, Any],
        datos_proyecto: dict[str, Any]
    ) -> None:
        """Genera alertas relacionadas con biodiversidad."""

        # Áreas protegidas
        areas = resultado_gis.get("areas_protegidas", [])
        areas_intersectadas = [a for a in areas if a.get("intersecta")]

        if areas_intersectadas:
            # Determinar si es SNASPE
            snaspe = [
                a for a in areas_intersectadas
                if "parque nacional" in (a.get("tipo", "") or "").lower()
                or "reserva nacional" in (a.get("tipo", "") or "").lower()
                or "monumento natural" in (a.get("tipo", "") or "").lower()
            ]

            nivel = NivelAlerta.CRITICA if snaspe else NivelAlerta.ALTA

            alerta = Alerta(
                id=self._generar_id(),
                nivel=nivel,
                categoria=CategoriaImpacto.BIODIVERSIDAD,
                titulo="Intersección con Área Protegida",
                descripcion=f"El proyecto se localiza dentro de {len(areas_intersectadas)} área(s) protegida(s). "
                           f"{'Incluye unidad(es) del SNASPE.' if snaspe else ''}",
                componentes_afectados=[
                    ComponenteAmbiental.AREAS_PROTEGIDAS,
                    ComponenteAmbiental.FLORA_VEGETACION,
                    ComponenteAmbiental.FAUNA,
                ],
                elementos_gis=[
                    {"nombre": a.get("nombre"), "tipo": a.get("tipo"), "categoria": a.get("categoria")}
                    for a in areas_intersectadas
                ],
                normativa_relacionada=[
                    "Ley 19.300 Art. 11 letra d)",
                    "Ley 18.362 - Sistema Nacional de Áreas Silvestres Protegidas",
                    "DS 40/2012 Art. 8",
                ],
                acciones_requeridas=[
                    "Evaluar compatibilidad legal del proyecto",
                    "Obtener pronunciamiento de CONAF" if snaspe else "Evaluar impactos sobre objetivos de conservación",
                    "Elaborar línea base de biodiversidad detallada",
                    "Plan de medidas de mitigación y compensación",
                ],
                permisos_sectoriales=self.PAS_POR_COMPONENTE[ComponenteAmbiental.AREAS_PROTEGIDAS],
            )
            self.alertas.append(alerta)

        # Glaciares
        glaciares = resultado_gis.get("glaciares", [])
        glaciares_intersectados = [g for g in glaciares if g.get("intersecta")]
        glaciares_cercanos = [g for g in glaciares if not g.get("intersecta") and g.get("distancia_m", float("inf")) < 10000]

        if glaciares_intersectados:
            alerta = Alerta(
                id=self._generar_id(),
                nivel=NivelAlerta.CRITICA,
                categoria=CategoriaImpacto.BIODIVERSIDAD,
                titulo="Afectación Directa de Glaciares",
                descripcion=f"El proyecto intersecta con {len(glaciares_intersectados)} glaciar(es). "
                           f"La Ley 21.455 prohíbe actividades en glaciares.",
                componentes_afectados=[
                    ComponenteAmbiental.ECOSISTEMAS_ACUATICOS,
                    ComponenteAmbiental.HIDROLOGIA,
                ],
                elementos_gis=[
                    {"nombre": g.get("nombre"), "tipo": g.get("tipo")}
                    for g in glaciares_intersectados
                ],
                normativa_relacionada=[
                    "Ley 21.455 - Ley de Protección de Glaciares",
                    "Ley 19.300 Art. 11 letra b)",
                    "Política Nacional de Glaciares",
                ],
                acciones_requeridas=[
                    "CRÍTICO: Rediseñar proyecto para evitar afectación",
                    "Realizar estudio glaciológico",
                    "Evaluar alternativas de localización",
                    "Consultar viabilidad legal con autoridad competente",
                ],
                permisos_sectoriales=[],
                metadata={"restriccion_legal": True},
            )
            self.alertas.append(alerta)

        elif glaciares_cercanos:
            alerta = Alerta(
                id=self._generar_id(),
                nivel=NivelAlerta.ALTA,
                categoria=CategoriaImpacto.BIODIVERSIDAD,
                titulo="Proximidad a Glaciares",
                descripcion=f"{len(glaciares_cercanos)} glaciar(es) en radio de 10km. "
                           f"Evaluar impactos indirectos.",
                componentes_afectados=[
                    ComponenteAmbiental.ECOSISTEMAS_ACUATICOS,
                    ComponenteAmbiental.HIDROLOGIA,
                ],
                elementos_gis=[
                    {"nombre": g.get("nombre"), "distancia_m": g.get("distancia_m")}
                    for g in glaciares_cercanos
                ],
                normativa_relacionada=[
                    "Ley 21.455",
                    "Ley 19.300 Art. 11 letra b)",
                ],
                acciones_requeridas=[
                    "Estudio de efectos indirectos (polvo, vibraciones)",
                    "Monitoreo de glaciares",
                    "Medidas de control de emisiones de polvo",
                ],
                permisos_sectoriales=[],
            )
            self.alertas.append(alerta)

    def _alertas_recursos_hidricos(
        self,
        resultado_gis: dict[str, Any],
        datos_proyecto: dict[str, Any]
    ) -> None:
        """Genera alertas relacionadas con recursos hídricos."""

        cuerpos = resultado_gis.get("cuerpos_agua", [])
        cuerpos_intersectados = [c for c in cuerpos if c.get("intersecta")]
        cuerpos_cercanos = [c for c in cuerpos if not c.get("intersecta") and c.get("distancia_m", float("inf")) < 1000]
        sitios_ramsar = [c for c in cuerpos if c.get("es_sitio_ramsar")]

        if cuerpos_intersectados:
            tiene_ramsar = any(c.get("es_sitio_ramsar") for c in cuerpos_intersectados)
            nivel = NivelAlerta.CRITICA if tiene_ramsar else NivelAlerta.ALTA

            alerta = Alerta(
                id=self._generar_id(),
                nivel=nivel,
                categoria=CategoriaImpacto.RECURSOS_HIDRICOS,
                titulo="Afectación de Cuerpos de Agua",
                descripcion=f"El proyecto intersecta {len(cuerpos_intersectados)} cuerpo(s) de agua. "
                           f"{'Incluye Sitio RAMSAR protegido.' if tiene_ramsar else ''}",
                componentes_afectados=[
                    ComponenteAmbiental.HIDROLOGIA,
                    ComponenteAmbiental.HIDROGEOLOGIA,
                    ComponenteAmbiental.ECOSISTEMAS_ACUATICOS,
                ],
                elementos_gis=[
                    {"nombre": c.get("nombre"), "tipo": c.get("tipo"), "ramsar": c.get("es_sitio_ramsar")}
                    for c in cuerpos_intersectados
                ],
                normativa_relacionada=[
                    "Código de Aguas",
                    "Ley 19.300 Art. 11 letra b)",
                    "DS 90/2000 - Norma de emisión de residuos líquidos",
                ] + (["Convención RAMSAR"] if tiene_ramsar else []),
                acciones_requeridas=[
                    "Estudio hidrogeológico detallado",
                    "Plan de manejo de aguas de contacto",
                    "Sistema de tratamiento de efluentes",
                    "Monitoreo de calidad de agua",
                ],
                permisos_sectoriales=(
                    self.PAS_POR_COMPONENTE[ComponenteAmbiental.HIDROLOGIA] +
                    self.PAS_POR_COMPONENTE[ComponenteAmbiental.HIDROGEOLOGIA]
                ),
            )
            self.alertas.append(alerta)

        # Alerta por uso de agua del proyecto
        uso_agua = datos_proyecto.get("uso_agua_lps", 0) or 0
        if uso_agua > 50:
            nivel = NivelAlerta.ALTA if uso_agua > 200 else NivelAlerta.MEDIA

            alerta = Alerta(
                id=self._generar_id(),
                nivel=nivel,
                categoria=CategoriaImpacto.RECURSOS_HIDRICOS,
                titulo="Alto Consumo de Agua",
                descripcion=f"El proyecto requiere {uso_agua} L/s de agua. "
                           f"Fuente: {datos_proyecto.get('fuente_agua', 'No especificada')}.",
                componentes_afectados=[
                    ComponenteAmbiental.HIDROLOGIA,
                    ComponenteAmbiental.HIDROGEOLOGIA,
                ],
                elementos_gis=[],
                normativa_relacionada=[
                    "Código de Aguas",
                    "DGA - Resolución de derechos de aprovechamiento",
                ],
                acciones_requeridas=[
                    "Demostrar disponibilidad del recurso hídrico",
                    "Obtener/transferir derechos de agua",
                    "Evaluar impacto en otros usuarios de la cuenca",
                    "Plan de eficiencia hídrica y recirculación",
                ],
                permisos_sectoriales=self.PAS_POR_COMPONENTE[ComponenteAmbiental.HIDROGEOLOGIA],
            )
            self.alertas.append(alerta)

    def _alertas_medio_humano(
        self,
        resultado_gis: dict[str, Any],
        datos_proyecto: dict[str, Any]
    ) -> None:
        """Genera alertas relacionadas con medio humano."""

        # Comunidades indígenas
        comunidades = resultado_gis.get("comunidades_indigenas", [])
        comunidades_cercanas = [c for c in comunidades if c.get("distancia_m", float("inf")) < 10000]

        if comunidades_cercanas:
            muy_cercanas = [c for c in comunidades_cercanas if c.get("distancia_m", float("inf")) < 5000]
            en_adi = any(c.get("es_adi") for c in comunidades_cercanas)

            nivel = NivelAlerta.CRITICA if muy_cercanas or en_adi else NivelAlerta.ALTA

            pueblos = list(set(c.get("pueblo", "N/D") for c in comunidades_cercanas))

            alerta = Alerta(
                id=self._generar_id(),
                nivel=nivel,
                categoria=CategoriaImpacto.MEDIO_HUMANO,
                titulo="Proximidad a Comunidades Indígenas",
                descripcion=f"{len(comunidades_cercanas)} comunidad(es) indígena(s) en radio de 10km. "
                           f"Pueblos: {', '.join(pueblos)}. "
                           f"{'Proyecto en ADI.' if en_adi else ''}",
                componentes_afectados=[
                    ComponenteAmbiental.PUEBLOS_INDIGENAS,
                    ComponenteAmbiental.MEDIO_HUMANO,
                ],
                elementos_gis=[
                    {
                        "nombre": c.get("nombre"),
                        "pueblo": c.get("pueblo"),
                        "es_adi": c.get("es_adi"),
                        "distancia_m": c.get("distancia_m")
                    }
                    for c in comunidades_cercanas
                ],
                normativa_relacionada=[
                    "Convenio 169 OIT",
                    "Ley 19.300 Art. 11 letra c) y d)",
                    "DS 66/2013 - Reglamento de Consulta Indígena",
                    "Ley 19.253 - Ley Indígena",
                ],
                acciones_requeridas=[
                    "OBLIGATORIO: Proceso de Consulta Indígena" if muy_cercanas or en_adi else "Evaluar necesidad de Consulta Indígena",
                    "Línea base de medio humano indígena",
                    "Estudio de uso ancestral del territorio",
                    "Plan de relacionamiento comunitario",
                    "Evaluar medidas de beneficio compartido",
                ],
                permisos_sectoriales=self.PAS_POR_COMPONENTE[ComponenteAmbiental.PUEBLOS_INDIGENAS],
            )
            self.alertas.append(alerta)

        # Centros poblados
        centros = resultado_gis.get("centros_poblados", [])
        centros_cercanos = [c for c in centros if c.get("distancia_m", float("inf")) < 5000]

        if centros_cercanos:
            muy_cercanos = [c for c in centros_cercanos if c.get("distancia_m", float("inf")) < 2000]
            poblacion_total = sum(c.get("poblacion", 0) or 0 for c in centros_cercanos)

            nivel = (NivelAlerta.ALTA if muy_cercanos or poblacion_total > 5000
                    else NivelAlerta.MEDIA)

            alerta = Alerta(
                id=self._generar_id(),
                nivel=nivel,
                categoria=CategoriaImpacto.MEDIO_HUMANO,
                titulo="Proximidad a Centros Poblados",
                descripcion=f"{len(centros_cercanos)} centro(s) poblado(s) en radio de 5km. "
                           f"Población estimada: {poblacion_total:,} habitantes.",
                componentes_afectados=[
                    ComponenteAmbiental.MEDIO_HUMANO,
                    ComponenteAmbiental.CALIDAD_AIRE,
                    ComponenteAmbiental.RUIDO_VIBRACIONES,
                ],
                elementos_gis=[
                    {
                        "nombre": c.get("nombre"),
                        "tipo": c.get("tipo"),
                        "poblacion": c.get("poblacion"),
                        "distancia_m": c.get("distancia_m")
                    }
                    for c in centros_cercanos
                ],
                normativa_relacionada=[
                    "Ley 19.300 Art. 11 letra a)",
                    "DS 38/2011 - Norma de ruido",
                    "DS 144/1961 - Prevención de contaminación",
                ],
                acciones_requeridas=[
                    "Estudio de dispersión de emisiones",
                    "Evaluación de impacto acústico",
                    "Plan de gestión de residuos",
                    "Plan de comunicación con la comunidad",
                    "Participación Ciudadana Anticipada (PAC)" if muy_cercanos else "Informar a comunidades locales",
                ],
                permisos_sectoriales=self.PAS_POR_COMPONENTE[ComponenteAmbiental.CALIDAD_AIRE],
            )
            self.alertas.append(alerta)

    def _alertas_patrimonio(
        self,
        resultado_gis: dict[str, Any],
        datos_proyecto: dict[str, Any]
    ) -> None:
        """Genera alertas relacionadas con patrimonio."""

        sitios = resultado_gis.get("sitios_patrimoniales", [])

        if sitios:
            sitios_intersectados = [s for s in sitios if s.get("intersecta")]
            sitios_cercanos = [s for s in sitios if not s.get("intersecta") and s.get("distancia_m", float("inf")) < 2000]

            if sitios_intersectados:
                alerta = Alerta(
                    id=self._generar_id(),
                    nivel=NivelAlerta.CRITICA,
                    categoria=CategoriaImpacto.PATRIMONIO,
                    titulo="Afectación de Patrimonio Cultural",
                    descripcion=f"El proyecto afecta {len(sitios_intersectados)} sitio(s) patrimonial(es).",
                    componentes_afectados=[
                        ComponenteAmbiental.PATRIMONIO_ARQUEOLOGICO,
                        ComponenteAmbiental.PATRIMONIO_CULTURAL,
                    ],
                    elementos_gis=[
                        {"nombre": s.get("nombre"), "tipo": s.get("tipo")}
                        for s in sitios_intersectados
                    ],
                    normativa_relacionada=[
                        "Ley 17.288 - Monumentos Nacionales",
                        "Ley 19.300 Art. 11 letra e) y f)",
                        "DS 40/2012 Art. 10",
                    ],
                    acciones_requeridas=[
                        "Pronunciamiento del Consejo de Monumentos Nacionales",
                        "Estudio de impacto patrimonial",
                        "Plan de rescate arqueológico",
                        "Evaluar alternativas que eviten afectación",
                    ],
                    permisos_sectoriales=self.PAS_POR_COMPONENTE[ComponenteAmbiental.PATRIMONIO_ARQUEOLOGICO],
                )
                self.alertas.append(alerta)

            elif sitios_cercanos:
                alerta = Alerta(
                    id=self._generar_id(),
                    nivel=NivelAlerta.MEDIA,
                    categoria=CategoriaImpacto.PATRIMONIO,
                    titulo="Proximidad a Sitios Patrimoniales",
                    descripcion=f"{len(sitios_cercanos)} sitio(s) patrimonial(es) cercano(s).",
                    componentes_afectados=[
                        ComponenteAmbiental.PATRIMONIO_ARQUEOLOGICO,
                    ],
                    elementos_gis=[
                        {"nombre": s.get("nombre"), "distancia_m": s.get("distancia_m")}
                        for s in sitios_cercanos
                    ],
                    normativa_relacionada=[
                        "Ley 17.288",
                        "Ley 19.300 Art. 11 letra e)",
                    ],
                    acciones_requeridas=[
                        "Estudio arqueológico preventivo",
                        "Evaluar impactos indirectos (vibraciones, visual)",
                    ],
                    permisos_sectoriales=[],
                )
                self.alertas.append(alerta)

        # Alerta por potencial hallazgo arqueológico (proyectos grandes en zonas andinas)
        superficie = datos_proyecto.get("superficie_ha", 0) or 0
        region = (datos_proyecto.get("region") or "").lower()
        zonas_arqueologicas = ["atacama", "antofagasta", "tarapacá", "arica"]

        if superficie > 100 and any(z in region for z in zonas_arqueologicas):
            alerta = Alerta(
                id=self._generar_id(),
                nivel=NivelAlerta.MEDIA,
                categoria=CategoriaImpacto.PATRIMONIO,
                titulo="Zona de Alto Potencial Arqueológico",
                descripcion=f"Proyecto de {superficie} ha en {datos_proyecto.get('region', 'N/D')}. "
                           f"Región con alto potencial de hallazgos arqueológicos.",
                componentes_afectados=[
                    ComponenteAmbiental.PATRIMONIO_ARQUEOLOGICO,
                ],
                elementos_gis=[],
                normativa_relacionada=[
                    "Ley 17.288",
                    "DS 40/2012 Art. 10",
                ],
                acciones_requeridas=[
                    "Prospección arqueológica del área del proyecto",
                    "Protocolo de hallazgos fortuitos",
                    "Capacitación a trabajadores en patrimonio",
                ],
                permisos_sectoriales=[],
            )
            self.alertas.append(alerta)

    def _alertas_aire_ruido(
        self,
        resultado_gis: dict[str, Any],
        datos_proyecto: dict[str, Any]
    ) -> None:
        """Genera alertas relacionadas con calidad del aire y ruido."""

        centros = resultado_gis.get("centros_poblados", [])
        tipo_mineria = (datos_proyecto.get("tipo_mineria") or "").lower()

        # Proyectos de minería a cielo abierto cercanos a poblaciones
        if ("tajo abierto" in tipo_mineria or "rajo" in tipo_mineria):
            centros_cercanos = [c for c in centros if c.get("distancia_m", float("inf")) < 10000]

            if centros_cercanos:
                alerta = Alerta(
                    id=self._generar_id(),
                    nivel=NivelAlerta.MEDIA,
                    categoria=CategoriaImpacto.AIRE_RUIDO,
                    titulo="Potencial Impacto por Emisiones y Ruido",
                    descripcion=f"Minería a cielo abierto con {len(centros_cercanos)} centro(s) poblado(s) "
                               f"en radio de 10km. Evaluar dispersión de material particulado y ruido.",
                    componentes_afectados=[
                        ComponenteAmbiental.CALIDAD_AIRE,
                        ComponenteAmbiental.RUIDO_VIBRACIONES,
                    ],
                    elementos_gis=[],
                    normativa_relacionada=[
                        "DS 144/1961",
                        "DS 38/2011 - Norma de ruido",
                        "DS 59/1998 - MP10",
                        "DS 12/2011 - MP2.5",
                    ],
                    acciones_requeridas=[
                        "Modelación de dispersión de MP10 y MP2.5",
                        "Estudio de impacto acústico",
                        "Plan de control de polvo",
                        "Sistema de monitoreo de calidad del aire",
                    ],
                    permisos_sectoriales=self.PAS_POR_COMPONENTE[ComponenteAmbiental.CALIDAD_AIRE],
                )
                self.alertas.append(alerta)

    def _alertas_paisaje(
        self,
        resultado_gis: dict[str, Any],
        datos_proyecto: dict[str, Any]
    ) -> None:
        """Genera alertas relacionadas con paisaje."""

        superficie = datos_proyecto.get("superficie_ha", 0) or 0
        tipo_mineria = (datos_proyecto.get("tipo_mineria") or "").lower()

        if superficie > 100 and ("tajo abierto" in tipo_mineria or "rajo" in tipo_mineria):
            alerta = Alerta(
                id=self._generar_id(),
                nivel=NivelAlerta.BAJA,
                categoria=CategoriaImpacto.PAISAJE,
                titulo="Modificación del Paisaje",
                descripcion=f"Proyecto de minería a cielo abierto de {superficie} ha. "
                           f"Alto potencial de modificación paisajística.",
                componentes_afectados=[
                    ComponenteAmbiental.PAISAJE,
                    ComponenteAmbiental.GEOMORFOLOGIA,
                ],
                elementos_gis=[],
                normativa_relacionada=[
                    "Ley 19.300 Art. 11 letra e)",
                    "DS 40/2012 Art. 6 - Descripción de proyecto",
                ],
                acciones_requeridas=[
                    "Análisis de paisaje y cuenca visual",
                    "Fotomontajes del escenario futuro",
                    "Plan de cierre con rehabilitación paisajística",
                    "Medidas de integración paisajística",
                ],
                permisos_sectoriales=[],
            )
            self.alertas.append(alerta)

    def obtener_resumen(self) -> dict[str, Any]:
        """Genera un resumen de las alertas."""
        if not self.alertas:
            return {
                "total_alertas": 0,
                "por_nivel": {},
                "por_categoria": {},
                "componentes_afectados": [],
                "permisos_requeridos": [],
            }

        # Contar por nivel
        por_nivel = {}
        for nivel in NivelAlerta:
            count = sum(1 for a in self.alertas if a.nivel == nivel)
            if count > 0:
                por_nivel[nivel.value] = count

        # Contar por categoría
        por_categoria = {}
        for cat in CategoriaImpacto:
            count = sum(1 for a in self.alertas if a.categoria == cat)
            if count > 0:
                por_categoria[cat.value] = count

        # Componentes afectados únicos
        componentes = set()
        for a in self.alertas:
            componentes.update(c.value for c in a.componentes_afectados)

        # Permisos únicos
        permisos = set()
        for a in self.alertas:
            permisos.update(a.permisos_sectoriales)

        return {
            "total_alertas": len(self.alertas),
            "por_nivel": por_nivel,
            "por_categoria": por_categoria,
            "componentes_afectados": sorted(list(componentes)),
            "permisos_requeridos": sorted(list(permisos)),
        }
