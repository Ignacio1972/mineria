"""
Evaluador de Triggers del Art. 11 de la Ley 19.300

El Art. 11 establece los criterios que determinan si un proyecto debe
someterse a Evaluación de Impacto Ambiental (EIA) en lugar de una
Declaración de Impacto Ambiental (DIA).
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class LetraArticulo11(str, Enum):
    """Letras del Art. 11 de la Ley 19.300"""
    A = "a"  # Riesgo para salud de la población
    B = "b"  # Efectos adversos sobre recursos naturales
    C = "c"  # Reasentamiento de comunidades humanas
    D = "d"  # Localización en áreas protegidas / pueblos indígenas
    E = "e"  # Alteración de monumentos o patrimonio
    F = "f"  # Alteración de paisaje o turismo


class SeveridadTrigger(str, Enum):
    """Nivel de severidad del trigger"""
    CRITICA = "CRITICA"  # Requiere EIA obligatoriamente
    ALTA = "ALTA"        # Muy probable EIA
    MEDIA = "MEDIA"      # Puede requerir EIA según contexto
    BAJA = "BAJA"        # Probable DIA con medidas


@dataclass
class TriggerEIA:
    """Representa un trigger detectado del Art. 11"""
    letra: LetraArticulo11
    descripcion: str
    detalle: str
    severidad: SeveridadTrigger
    fundamento_legal: str
    elementos_afectados: list[dict] = field(default_factory=list)
    recomendaciones: list[str] = field(default_factory=list)
    peso: float = 1.0  # Para ponderación en matriz de decisión

    def to_dict(self) -> dict:
        return {
            "letra": self.letra.value,
            "descripcion": self.descripcion,
            "detalle": self.detalle,
            "severidad": self.severidad.value,
            "fundamento_legal": self.fundamento_legal,
            "elementos_afectados": self.elementos_afectados,
            "recomendaciones": self.recomendaciones,
            "peso": self.peso,
        }


class EvaluadorTriggers:
    """
    Evalúa los triggers del Art. 11 de la Ley 19.300.

    Art. 11.- Los proyectos o actividades enumerados en el artículo precedente
    requerirán la elaboración de un Estudio de Impacto Ambiental, si generan o
    presentan a lo menos uno de los siguientes efectos, características o
    circunstancias:
    """

    # Umbrales configurables
    UMBRAL_DISTANCIA_POBLACION_M = 2000
    UMBRAL_DISTANCIA_COMUNIDADES_M = 10000
    UMBRAL_DISTANCIA_COMUNIDADES_CRITICA_M = 5000
    UMBRAL_DISTANCIA_CUERPO_AGUA_M = 500
    UMBRAL_POBLACION_RIESGO = 1000
    UMBRAL_TRABAJADORES_GRAN_PROYECTO = 500
    UMBRAL_SUPERFICIE_GRAN_PROYECTO_HA = 500
    UMBRAL_INVERSION_GRAN_PROYECTO_MUSD = 100

    def __init__(self):
        self.triggers_detectados: list[TriggerEIA] = []
        logger.info("EvaluadorTriggers inicializado")

    def evaluar(
        self,
        resultado_gis: dict[str, Any],
        datos_proyecto: dict[str, Any]
    ) -> list[TriggerEIA]:
        """
        Evalúa todos los triggers del Art. 11.

        Args:
            resultado_gis: Resultado del análisis espacial
            datos_proyecto: Datos del proyecto minero

        Returns:
            Lista de triggers detectados
        """
        logger.info("Iniciando evaluación completa de triggers Art. 11")
        self.triggers_detectados = []

        # Evaluar cada letra del Art. 11
        self._evaluar_letra_a(resultado_gis, datos_proyecto)
        self._evaluar_letra_b(resultado_gis, datos_proyecto)
        self._evaluar_letra_c(resultado_gis, datos_proyecto)
        self._evaluar_letra_d(resultado_gis, datos_proyecto)
        self._evaluar_letra_e(resultado_gis, datos_proyecto)
        self._evaluar_letra_f(resultado_gis, datos_proyecto)

        logger.info(f"Evaluación completada: {len(self.triggers_detectados)} triggers detectados")
        return self.triggers_detectados

    def _evaluar_letra_a(
        self,
        resultado_gis: dict[str, Any],
        datos_proyecto: dict[str, Any]
    ) -> None:
        """
        Letra a) Riesgo para la salud de la población, debido a la cantidad
        y calidad de efluentes, emisiones o residuos.
        """
        centros_poblados = resultado_gis.get("centros_poblados", [])
        centros_cercanos = [
            c for c in centros_poblados
            if c.get("distancia_m", float("inf")) < self.UMBRAL_DISTANCIA_POBLACION_M
        ]

        if not centros_cercanos:
            return

        poblacion_total = sum(
            c.get("poblacion", 0) or 0 for c in centros_cercanos
        )

        # Determinar severidad según población afectada y distancia
        distancia_min = min(c.get("distancia_m", float("inf")) for c in centros_cercanos)

        if distancia_min < 500 or poblacion_total > 5000:
            severidad = SeveridadTrigger.CRITICA
            peso = 1.0
        elif distancia_min < 1000 or poblacion_total > self.UMBRAL_POBLACION_RIESGO:
            severidad = SeveridadTrigger.ALTA
            peso = 0.8
        else:
            severidad = SeveridadTrigger.MEDIA
            peso = 0.5

        # Evaluar factores agravantes del proyecto
        uso_agua = datos_proyecto.get("uso_agua_lps", 0) or 0
        tipo_mineria = (datos_proyecto.get("tipo_mineria") or "").lower()

        if "tajo abierto" in tipo_mineria or "rajo" in tipo_mineria:
            peso += 0.2
        if uso_agua > 100:  # Alto consumo de agua
            peso += 0.1

        trigger = TriggerEIA(
            letra=LetraArticulo11.A,
            descripcion="Riesgo para la salud de la población",
            detalle=f"{len(centros_cercanos)} centro(s) poblado(s) a menos de {self.UMBRAL_DISTANCIA_POBLACION_M}m. "
                   f"Población estimada en riesgo: {poblacion_total:,} habitantes. "
                   f"Centro más cercano a {distancia_min:.0f}m.",
            severidad=severidad,
            fundamento_legal="Art. 11 letra a) Ley 19.300: Riesgo para la salud de la población, "
                           "debido a la cantidad y calidad de efluentes, emisiones o residuos.",
            elementos_afectados=[
                {"tipo": "centro_poblado", "nombre": c.get("nombre"), "distancia_m": c.get("distancia_m")}
                for c in centros_cercanos
            ],
            recomendaciones=[
                "Elaborar estudio de dispersión de emisiones atmosféricas",
                "Evaluar impacto acústico en receptores sensibles",
                "Diseñar plan de manejo de residuos con énfasis en protección de población",
                "Considerar participación ciudadana anticipada (PAC)",
            ],
            peso=min(peso, 1.0),
        )
        self.triggers_detectados.append(trigger)
        logger.debug(f"Trigger letra a) detectado: {severidad.value}")

    def _evaluar_letra_b(
        self,
        resultado_gis: dict[str, Any],
        datos_proyecto: dict[str, Any]
    ) -> None:
        """
        Letra b) Efectos adversos significativos sobre la cantidad y calidad
        de los recursos naturales renovables, incluidos el suelo, agua y aire.
        """
        # Evaluar glaciares
        glaciares = resultado_gis.get("glaciares", [])
        glaciares_intersectados = [g for g in glaciares if g.get("intersecta")]
        glaciares_cercanos = [
            g for g in glaciares
            if not g.get("intersecta") and g.get("distancia_m", float("inf")) < 5000
        ]

        if glaciares_intersectados:
            trigger = TriggerEIA(
                letra=LetraArticulo11.B,
                descripcion="Efectos adversos sobre glaciares",
                detalle=f"El proyecto intersecta directamente con {len(glaciares_intersectados)} glaciar(es). "
                       f"Esta situación constituye una restricción legal según Ley 21.455.",
                severidad=SeveridadTrigger.CRITICA,
                fundamento_legal="Art. 11 letra b) Ley 19.300 y Ley 21.455 de Protección de Glaciares: "
                               "Prohibición de actividades en glaciares y ambiente periglacial.",
                elementos_afectados=[
                    {"tipo": "glaciar", "nombre": g.get("nombre"), "intersecta": True}
                    for g in glaciares_intersectados
                ],
                recomendaciones=[
                    "CRÍTICO: Rediseñar proyecto para evitar afectación de glaciares",
                    "Realizar estudio glaciológico completo",
                    "Evaluar alternativas de localización",
                    "La afectación directa de glaciares puede impedir la aprobación del proyecto",
                ],
                peso=1.0,
            )
            self.triggers_detectados.append(trigger)
            logger.debug("Trigger letra b) CRITICO: intersección con glaciar")

        elif glaciares_cercanos:
            trigger = TriggerEIA(
                letra=LetraArticulo11.B,
                descripcion="Proximidad a glaciares",
                detalle=f"{len(glaciares_cercanos)} glaciar(es) en radio de 5km. "
                       f"Requiere evaluación de efectos indirectos.",
                severidad=SeveridadTrigger.ALTA,
                fundamento_legal="Art. 11 letra b) Ley 19.300: Efectos adversos sobre recursos naturales renovables.",
                elementos_afectados=[
                    {"tipo": "glaciar", "nombre": g.get("nombre"), "distancia_m": g.get("distancia_m")}
                    for g in glaciares_cercanos
                ],
                recomendaciones=[
                    "Realizar estudio de impacto sobre régimen hídrico glacial",
                    "Evaluar emisiones de polvo y material particulado",
                    "Monitoreo de glaciares durante operación",
                ],
                peso=0.8,
            )
            self.triggers_detectados.append(trigger)

        # Evaluar cuerpos de agua
        cuerpos_agua = resultado_gis.get("cuerpos_agua", [])
        cuerpos_intersectados = [c for c in cuerpos_agua if c.get("intersecta")]
        cuerpos_cercanos = [
            c for c in cuerpos_agua
            if not c.get("intersecta") and c.get("distancia_m", float("inf")) < self.UMBRAL_DISTANCIA_CUERPO_AGUA_M
        ]
        sitios_ramsar = [c for c in cuerpos_agua if c.get("es_sitio_ramsar")]

        if cuerpos_intersectados:
            severidad = SeveridadTrigger.CRITICA if sitios_ramsar else SeveridadTrigger.ALTA
            trigger = TriggerEIA(
                letra=LetraArticulo11.B,
                descripcion="Efectos adversos sobre recursos hídricos",
                detalle=f"Intersección con {len(cuerpos_intersectados)} cuerpo(s) de agua. "
                       f"{'Incluye sitio(s) RAMSAR protegido(s).' if sitios_ramsar else ''}",
                severidad=severidad,
                fundamento_legal="Art. 11 letra b) Ley 19.300 y Código de Aguas: "
                               "Protección de cantidad y calidad de recursos hídricos.",
                elementos_afectados=[
                    {"tipo": c.get("tipo"), "nombre": c.get("nombre"), "ramsar": c.get("es_sitio_ramsar")}
                    for c in cuerpos_intersectados
                ],
                recomendaciones=[
                    "Elaborar estudio hidrogeológico detallado",
                    "Plan de manejo de aguas de contacto",
                    "Sistema de tratamiento de efluentes",
                    "Monitoreo continuo de calidad de agua",
                ],
                peso=1.0 if sitios_ramsar else 0.85,
            )
            self.triggers_detectados.append(trigger)

        elif cuerpos_cercanos:
            trigger = TriggerEIA(
                letra=LetraArticulo11.B,
                descripcion="Proximidad a recursos hídricos",
                detalle=f"{len(cuerpos_cercanos)} cuerpo(s) de agua a menos de {self.UMBRAL_DISTANCIA_CUERPO_AGUA_M}m.",
                severidad=SeveridadTrigger.MEDIA,
                fundamento_legal="Art. 11 letra b) Ley 19.300: Efectos sobre recursos hídricos.",
                elementos_afectados=[
                    {"tipo": c.get("tipo"), "nombre": c.get("nombre"), "distancia_m": c.get("distancia_m")}
                    for c in cuerpos_cercanos
                ],
                recomendaciones=[
                    "Evaluar riesgo de contaminación de acuíferos",
                    "Diseñar sistemas de contención de derrames",
                ],
                peso=0.5,
            )
            self.triggers_detectados.append(trigger)

        # Evaluar uso intensivo de agua del proyecto
        uso_agua = datos_proyecto.get("uso_agua_lps", 0) or 0
        if uso_agua > 50:  # Más de 50 L/s es significativo
            trigger = TriggerEIA(
                letra=LetraArticulo11.B,
                descripcion="Alto consumo de recursos hídricos",
                detalle=f"El proyecto requiere {uso_agua} L/s de agua. "
                       f"Fuente: {datos_proyecto.get('fuente_agua', 'No especificada')}.",
                severidad=SeveridadTrigger.ALTA if uso_agua > 200 else SeveridadTrigger.MEDIA,
                fundamento_legal="Art. 11 letra b) Ley 19.300 y Código de Aguas: "
                               "Efectos sobre disponibilidad de recursos hídricos.",
                elementos_afectados=[],
                recomendaciones=[
                    "Obtener derechos de agua o demostrar disponibilidad",
                    "Evaluar impacto en otros usuarios de la cuenca",
                    "Considerar alternativas de recirculación y agua de mar",
                ],
                peso=0.7 if uso_agua > 200 else 0.4,
            )
            self.triggers_detectados.append(trigger)

    def _evaluar_letra_c(
        self,
        resultado_gis: dict[str, Any],
        datos_proyecto: dict[str, Any]
    ) -> None:
        """
        Letra c) Reasentamiento de comunidades humanas, o alteración
        significativa de los sistemas de vida y costumbres de grupos humanos.
        """
        comunidades = resultado_gis.get("comunidades_indigenas", [])
        centros_poblados = resultado_gis.get("centros_poblados", [])

        # Comunidades indígenas muy cercanas
        comunidades_criticas = [
            c for c in comunidades
            if c.get("distancia_m", float("inf")) < self.UMBRAL_DISTANCIA_COMUNIDADES_CRITICA_M
        ]

        comunidades_cercanas = [
            c for c in comunidades
            if self.UMBRAL_DISTANCIA_COMUNIDADES_CRITICA_M <= c.get("distancia_m", float("inf")) < self.UMBRAL_DISTANCIA_COMUNIDADES_M
        ]

        if comunidades_criticas:
            # Determinar si hay ADI
            en_adi = any(c.get("es_adi") for c in comunidades_criticas)

            trigger = TriggerEIA(
                letra=LetraArticulo11.C,
                descripcion="Alteración de sistemas de vida de pueblos indígenas",
                detalle=f"{len(comunidades_criticas)} comunidad(es) indígena(s) a menos de {self.UMBRAL_DISTANCIA_COMUNIDADES_CRITICA_M}m. "
                       f"{'Proyecto en Área de Desarrollo Indígena (ADI).' if en_adi else ''} "
                       f"Pueblos: {', '.join(set(c.get('pueblo', 'N/D') for c in comunidades_criticas))}.",
                severidad=SeveridadTrigger.CRITICA if en_adi else SeveridadTrigger.ALTA,
                fundamento_legal="Art. 11 letra c) Ley 19.300 y Convenio 169 OIT: "
                               "Alteración significativa de sistemas de vida de grupos humanos.",
                elementos_afectados=[
                    {
                        "tipo": "comunidad_indigena",
                        "nombre": c.get("nombre"),
                        "pueblo": c.get("pueblo"),
                        "es_adi": c.get("es_adi"),
                        "distancia_m": c.get("distancia_m")
                    }
                    for c in comunidades_criticas
                ],
                recomendaciones=[
                    "OBLIGATORIO: Realizar Consulta Indígena según Convenio 169 OIT",
                    "Elaborar línea base de medio humano indígena",
                    "Estudiar uso ancestral del territorio",
                    "Diseñar plan de relacionamiento comunitario",
                    "Evaluar medidas de compensación y beneficio compartido",
                ],
                peso=1.0 if en_adi else 0.9,
            )
            self.triggers_detectados.append(trigger)
            logger.debug(f"Trigger letra c) CRITICO: comunidades indígenas a <{self.UMBRAL_DISTANCIA_COMUNIDADES_CRITICA_M}m")

        elif comunidades_cercanas:
            trigger = TriggerEIA(
                letra=LetraArticulo11.C,
                descripcion="Proximidad a comunidades indígenas",
                detalle=f"{len(comunidades_cercanas)} comunidad(es) indígena(s) en radio de {self.UMBRAL_DISTANCIA_COMUNIDADES_M}m.",
                severidad=SeveridadTrigger.ALTA,
                fundamento_legal="Art. 11 letra c) Ley 19.300: Alteración de sistemas de vida.",
                elementos_afectados=[
                    {"tipo": "comunidad_indigena", "nombre": c.get("nombre"), "pueblo": c.get("pueblo")}
                    for c in comunidades_cercanas
                ],
                recomendaciones=[
                    "Evaluar necesidad de Consulta Indígena",
                    "Incluir componente indígena en línea base",
                ],
                peso=0.7,
            )
            self.triggers_detectados.append(trigger)

        # Evaluar reasentamiento por tamaño del proyecto
        superficie = datos_proyecto.get("superficie_ha", 0) or 0
        trabajadores = datos_proyecto.get("trabajadores_construccion", 0) or 0

        if superficie > self.UMBRAL_SUPERFICIE_GRAN_PROYECTO_HA:
            centros_muy_cercanos = [
                c for c in centros_poblados
                if c.get("distancia_m", float("inf")) < 1000
            ]
            if centros_muy_cercanos:
                trigger = TriggerEIA(
                    letra=LetraArticulo11.C,
                    descripcion="Potencial reasentamiento de comunidades",
                    detalle=f"Proyecto de gran superficie ({superficie} ha) con centros poblados muy cercanos. "
                           f"Evaluar necesidad de reasentamiento.",
                    severidad=SeveridadTrigger.ALTA,
                    fundamento_legal="Art. 11 letra c) Ley 19.300: Reasentamiento de comunidades humanas.",
                    elementos_afectados=[
                        {"tipo": "centro_poblado", "nombre": c.get("nombre")}
                        for c in centros_muy_cercanos
                    ],
                    recomendaciones=[
                        "Evaluar alternativas que eviten reasentamiento",
                        "Plan de reasentamiento voluntario si es inevitable",
                    ],
                    peso=0.8,
                )
                self.triggers_detectados.append(trigger)

    def _evaluar_letra_d(
        self,
        resultado_gis: dict[str, Any],
        datos_proyecto: dict[str, Any]
    ) -> None:
        """
        Letra d) Localización en o próxima a poblaciones, recursos y áreas
        protegidas, sitios prioritarios para la conservación, humedales
        protegidos y glaciares, susceptibles de ser afectados, así como el
        valor ambiental del territorio en que se pretende emplazar.
        """
        areas_protegidas = resultado_gis.get("areas_protegidas", [])
        areas_intersectadas = [a for a in areas_protegidas if a.get("intersecta")]
        areas_cercanas = [
            a for a in areas_protegidas
            if not a.get("intersecta") and a.get("distancia_m", float("inf")) < 10000
        ]

        if areas_intersectadas:
            tipos_afectados = set(a.get("tipo", "N/D") for a in areas_intersectadas)
            categorias = set(a.get("categoria", "N/D") for a in areas_intersectadas)

            # SNASPE es más restrictivo
            es_snaspe = any(
                "parque nacional" in (a.get("tipo", "") or "").lower() or
                "reserva nacional" in (a.get("tipo", "") or "").lower()
                for a in areas_intersectadas
            )

            trigger = TriggerEIA(
                letra=LetraArticulo11.D,
                descripcion="Localización en áreas protegidas",
                detalle=f"El proyecto intersecta con {len(areas_intersectadas)} área(s) protegida(s): "
                       f"{', '.join(a.get('nombre', 'N/D') for a in areas_intersectadas)}. "
                       f"Tipos: {', '.join(tipos_afectados)}.",
                severidad=SeveridadTrigger.CRITICA,
                fundamento_legal="Art. 11 letra d) Ley 19.300 y Ley 18.362 (SNASPE): "
                               "Localización en áreas protegidas susceptibles de ser afectadas.",
                elementos_afectados=[
                    {
                        "tipo": "area_protegida",
                        "nombre": a.get("nombre"),
                        "categoria": a.get("categoria"),
                        "tipo_area": a.get("tipo")
                    }
                    for a in areas_intersectadas
                ],
                recomendaciones=[
                    "CRÍTICO: Evaluar viabilidad legal del proyecto en área protegida",
                    "Obtener pronunciamiento de CONAF si es SNASPE",
                    "Evaluar alternativas de localización fuera del área protegida",
                    "Medidas de compensación de biodiversidad",
                ] if es_snaspe else [
                    "Evaluar compatibilidad con objetivos de conservación del área",
                    "Medidas de mitigación y compensación de biodiversidad",
                ],
                peso=1.0,
            )
            self.triggers_detectados.append(trigger)
            logger.debug("Trigger letra d) CRITICO: intersección con área protegida")

        elif areas_cercanas:
            trigger = TriggerEIA(
                letra=LetraArticulo11.D,
                descripcion="Proximidad a áreas protegidas",
                detalle=f"{len(areas_cercanas)} área(s) protegida(s) en radio de 10km.",
                severidad=SeveridadTrigger.MEDIA,
                fundamento_legal="Art. 11 letra d) Ley 19.300: Proximidad a áreas protegidas.",
                elementos_afectados=[
                    {"tipo": "area_protegida", "nombre": a.get("nombre"), "distancia_m": a.get("distancia_m")}
                    for a in areas_cercanas
                ],
                recomendaciones=[
                    "Evaluar efectos indirectos sobre área protegida",
                    "Línea base de biodiversidad en zona de influencia",
                ],
                peso=0.5,
            )
            self.triggers_detectados.append(trigger)

    def _evaluar_letra_e(
        self,
        resultado_gis: dict[str, Any],
        datos_proyecto: dict[str, Any]
    ) -> None:
        """
        Letra e) Alteración significativa, en términos de magnitud o duración,
        del valor paisajístico o turístico de una zona.
        """
        # Evaluar sitios patrimoniales si están en el resultado GIS
        sitios_patrimoniales = resultado_gis.get("sitios_patrimoniales", [])

        if sitios_patrimoniales:
            sitios_intersectados = [s for s in sitios_patrimoniales if s.get("intersecta")]
            sitios_cercanos = [
                s for s in sitios_patrimoniales
                if not s.get("intersecta") and s.get("distancia_m", float("inf")) < 2000
            ]

            if sitios_intersectados:
                trigger = TriggerEIA(
                    letra=LetraArticulo11.E,
                    descripcion="Alteración de monumentos o patrimonio cultural",
                    detalle=f"El proyecto afecta {len(sitios_intersectados)} sitio(s) patrimonial(es).",
                    severidad=SeveridadTrigger.CRITICA,
                    fundamento_legal="Art. 11 letra e) Ley 19.300 y Ley 17.288 de Monumentos Nacionales: "
                                   "Alteración de monumentos, sitios con valor antropológico, arqueológico o histórico.",
                    elementos_afectados=[
                        {"tipo": "sitio_patrimonial", "nombre": s.get("nombre")}
                        for s in sitios_intersectados
                    ],
                    recomendaciones=[
                        "Obtener pronunciamiento del Consejo de Monumentos Nacionales",
                        "Estudio de impacto patrimonial",
                        "Plan de rescate arqueológico si corresponde",
                    ],
                    peso=1.0,
                )
                self.triggers_detectados.append(trigger)

            elif sitios_cercanos:
                trigger = TriggerEIA(
                    letra=LetraArticulo11.E,
                    descripcion="Proximidad a sitios patrimoniales",
                    detalle=f"{len(sitios_cercanos)} sitio(s) patrimonial(es) cercano(s).",
                    severidad=SeveridadTrigger.MEDIA,
                    fundamento_legal="Art. 11 letra e) Ley 19.300: Alteración de patrimonio.",
                    elementos_afectados=[
                        {"tipo": "sitio_patrimonial", "nombre": s.get("nombre"), "distancia_m": s.get("distancia_m")}
                        for s in sitios_cercanos
                    ],
                    recomendaciones=[
                        "Evaluar impacto visual y de vibraciones",
                        "Estudio arqueológico preventivo",
                    ],
                    peso=0.4,
                )
                self.triggers_detectados.append(trigger)

        # Evaluar impacto paisajístico por tamaño
        superficie = datos_proyecto.get("superficie_ha", 0) or 0
        tipo_mineria = (datos_proyecto.get("tipo_mineria") or "").lower()

        if superficie > 100 and ("tajo abierto" in tipo_mineria or "rajo" in tipo_mineria):
            trigger = TriggerEIA(
                letra=LetraArticulo11.E,
                descripcion="Potencial alteración del paisaje",
                detalle=f"Proyecto de minería a cielo abierto de {superficie} ha. "
                       f"Alto potencial de modificación paisajística.",
                severidad=SeveridadTrigger.MEDIA,
                fundamento_legal="Art. 11 letra e) Ley 19.300: Alteración del valor paisajístico.",
                elementos_afectados=[],
                recomendaciones=[
                    "Estudio de paisaje y cuenca visual",
                    "Plan de cierre y rehabilitación paisajística",
                    "Medidas de integración paisajística",
                ],
                peso=0.4,
            )
            self.triggers_detectados.append(trigger)

    def _evaluar_letra_f(
        self,
        resultado_gis: dict[str, Any],
        datos_proyecto: dict[str, Any]
    ) -> None:
        """
        Letra f) Alteración de monumentos, sitios con valor antropológico,
        arqueológico, histórico y, en general, los pertenecientes al
        patrimonio cultural.

        Nota: Se complementa con letra e). La diferencia es que f) incluye
        explícitamente sitios turísticos y de valor escénico.
        """
        # Esta evaluación se complementa con la de letra e)
        # Agregar evaluación específica de turismo si hay datos disponibles

        # Evaluar si el proyecto está en zona reconocida como turística
        region = (datos_proyecto.get("region") or "").lower()
        zonas_turisticas = ["atacama", "antofagasta", "aysén", "magallanes", "los lagos"]

        if any(zona in region for zona in zonas_turisticas):
            # Verificar si hay áreas protegidas cercanas (proxy de valor turístico)
            areas_protegidas = resultado_gis.get("areas_protegidas", [])
            if areas_protegidas:
                areas_cercanas = [a for a in areas_protegidas if a.get("distancia_m", float("inf")) < 20000]
                if areas_cercanas:
                    trigger = TriggerEIA(
                        letra=LetraArticulo11.F,
                        descripcion="Potencial impacto en zona de valor turístico",
                        detalle=f"Proyecto en región {datos_proyecto.get('region', 'N/D')} "
                               f"con áreas protegidas cercanas que pueden tener valor turístico.",
                        severidad=SeveridadTrigger.BAJA,
                        fundamento_legal="Art. 11 letra f) Ley 19.300: Alteración de valor turístico de una zona.",
                        elementos_afectados=[],
                        recomendaciones=[
                            "Evaluar compatibilidad con actividades turísticas de la zona",
                            "Considerar impacto en imagen territorial",
                        ],
                        peso=0.3,
                    )
                    self.triggers_detectados.append(trigger)

    def obtener_resumen(self) -> dict[str, Any]:
        """Genera un resumen de la evaluación de triggers."""
        if not self.triggers_detectados:
            return {
                "total_triggers": 0,
                "triggers_criticos": 0,
                "triggers_altos": 0,
                "letras_afectadas": [],
                "requiere_eia": False,
            }

        criticos = sum(1 for t in self.triggers_detectados if t.severidad == SeveridadTrigger.CRITICA)
        altos = sum(1 for t in self.triggers_detectados if t.severidad == SeveridadTrigger.ALTA)
        letras = list(set(t.letra.value for t in self.triggers_detectados))

        return {
            "total_triggers": len(self.triggers_detectados),
            "triggers_criticos": criticos,
            "triggers_altos": altos,
            "letras_afectadas": sorted(letras),
            "requiere_eia": criticos > 0 or altos >= 2,
            "peso_total": sum(t.peso for t in self.triggers_detectados),
        }
