"""
Motor de Reglas del Sistema de Evaluación de Impacto Ambiental (SEIA)

Implementa la lógica de clasificación de proyectos y la matriz de decisión
para determinar si un proyecto debe ingresar como DIA o EIA.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.services.reglas.triggers import (
    EvaluadorTriggers,
    TriggerEIA,
    SeveridadTrigger,
    LetraArticulo11,
)

logger = logging.getLogger(__name__)


class ViaIngreso(str, Enum):
    """Vías de ingreso al SEIA"""
    DIA = "DIA"  # Declaración de Impacto Ambiental
    EIA = "EIA"  # Estudio de Impacto Ambiental


class NivelConfianza(str, Enum):
    """Nivel de confianza de la clasificación"""
    MUY_ALTA = "MUY_ALTA"  # > 0.9
    ALTA = "ALTA"          # 0.75 - 0.9
    MEDIA = "MEDIA"        # 0.5 - 0.75
    BAJA = "BAJA"          # < 0.5


@dataclass
class ClasificacionSEIA:
    """Resultado de la clasificación SEIA"""
    via_ingreso: ViaIngreso
    confianza: float
    nivel_confianza: NivelConfianza
    triggers: list[TriggerEIA]
    justificacion: str
    recomendaciones_generales: list[str] = field(default_factory=list)
    factores_proyecto: dict[str, Any] = field(default_factory=dict)
    puntaje_matriz: float = 0.0

    def to_dict(self) -> dict:
        return {
            "via_ingreso_recomendada": self.via_ingreso.value,
            "confianza": round(self.confianza, 3),
            "nivel_confianza": self.nivel_confianza.value,
            "triggers": [t.to_dict() for t in self.triggers],
            "justificacion": self.justificacion,
            "recomendaciones_generales": self.recomendaciones_generales,
            "factores_proyecto": self.factores_proyecto,
            "puntaje_matriz": round(self.puntaje_matriz, 3),
            "resumen": {
                "total_triggers": len(self.triggers),
                "letras_afectadas": list(set(t.letra.value for t in self.triggers)),
            }
        }


class MotorReglasSSEIA:
    """
    Motor de reglas para el Sistema de Evaluación de Impacto Ambiental.

    Implementa la matriz de decisión que combina:
    1. Triggers del Art. 11 (Ley 19.300)
    2. Características del proyecto (tipología, escala)
    3. Sensibilidad del territorio
    """

    # Pesos de la matriz de decisión
    PESO_TRIGGERS_CRITICOS = 0.40
    PESO_TRIGGERS_ALTOS = 0.25
    PESO_TRIGGERS_MEDIOS = 0.10
    PESO_CARACTERISTICAS_PROYECTO = 0.15
    PESO_SENSIBILIDAD_TERRITORIO = 0.10

    # Umbrales de clasificación
    UMBRAL_EIA_AUTOMATICO = 0.75
    UMBRAL_EIA_PROBABLE = 0.50
    UMBRAL_DIA_PROBABLE = 0.30

    # Factores del proyecto que aumentan complejidad
    FACTORES_PROYECTO = {
        "superficie_ha": {"umbral": 500, "peso": 0.3, "descripcion": "Superficie mayor a 500 ha"},
        "uso_agua_lps": {"umbral": 100, "peso": 0.25, "descripcion": "Uso de agua mayor a 100 L/s"},
        "trabajadores_construccion": {"umbral": 500, "peso": 0.15, "descripcion": "Más de 500 trabajadores"},
        "inversion_musd": {"umbral": 100, "peso": 0.15, "descripcion": "Inversión mayor a 100 MUSD"},
        "vida_util_anos": {"umbral": 20, "peso": 0.15, "descripcion": "Vida útil mayor a 20 años"},
    }

    def __init__(self):
        self.evaluador_triggers = EvaluadorTriggers()
        logger.info("MotorReglasSSEIA inicializado")

    def clasificar_proyecto(
        self,
        resultado_gis: dict[str, Any],
        datos_proyecto: dict[str, Any]
    ) -> ClasificacionSEIA:
        """
        Clasifica un proyecto minero para determinar su vía de ingreso al SEIA.

        Args:
            resultado_gis: Resultado del análisis espacial GIS
            datos_proyecto: Datos del proyecto minero

        Returns:
            ClasificacionSEIA con la vía de ingreso recomendada y justificación
        """
        logger.info(f"Clasificando proyecto: {datos_proyecto.get('nombre', 'Sin nombre')}")

        # 1. Evaluar triggers del Art. 11
        triggers = self.evaluador_triggers.evaluar(resultado_gis, datos_proyecto)
        resumen_triggers = self.evaluador_triggers.obtener_resumen()

        # 2. Calcular puntaje de triggers
        puntaje_triggers = self._calcular_puntaje_triggers(triggers)

        # 3. Calcular puntaje de características del proyecto
        puntaje_proyecto, factores_activos = self._calcular_puntaje_proyecto(datos_proyecto)

        # 4. Calcular puntaje de sensibilidad territorial
        puntaje_territorio = self._calcular_sensibilidad_territorio(resultado_gis)

        # 5. Calcular puntaje final de la matriz
        puntaje_final = (
            puntaje_triggers * 0.70 +  # Triggers son el factor principal
            puntaje_proyecto * 0.20 +
            puntaje_territorio * 0.10
        )

        logger.debug(f"Puntajes - Triggers: {puntaje_triggers:.2f}, "
                    f"Proyecto: {puntaje_proyecto:.2f}, "
                    f"Territorio: {puntaje_territorio:.2f}, "
                    f"Final: {puntaje_final:.2f}")

        # 6. Determinar clasificación
        via_ingreso, confianza, justificacion = self._determinar_clasificacion(
            puntaje_final, triggers, resumen_triggers, factores_activos
        )

        # 7. Generar recomendaciones
        recomendaciones = self._generar_recomendaciones(via_ingreso, triggers, datos_proyecto)

        # 8. Determinar nivel de confianza
        nivel_confianza = self._determinar_nivel_confianza(confianza)

        clasificacion = ClasificacionSEIA(
            via_ingreso=via_ingreso,
            confianza=confianza,
            nivel_confianza=nivel_confianza,
            triggers=triggers,
            justificacion=justificacion,
            recomendaciones_generales=recomendaciones,
            factores_proyecto=factores_activos,
            puntaje_matriz=puntaje_final,
        )

        logger.info(f"Clasificación: {via_ingreso.value} (confianza: {confianza:.2f})")
        return clasificacion

    def _calcular_puntaje_triggers(self, triggers: list[TriggerEIA]) -> float:
        """Calcula el puntaje basado en los triggers detectados."""
        if not triggers:
            return 0.0

        # Contar por severidad
        criticos = sum(1 for t in triggers if t.severidad == SeveridadTrigger.CRITICA)
        altos = sum(1 for t in triggers if t.severidad == SeveridadTrigger.ALTA)
        medios = sum(1 for t in triggers if t.severidad == SeveridadTrigger.MEDIA)
        bajos = sum(1 for t in triggers if t.severidad == SeveridadTrigger.BAJA)

        # Puntaje base por severidad (máximo 1.0)
        puntaje = min(1.0, (
            criticos * 0.35 +
            altos * 0.20 +
            medios * 0.10 +
            bajos * 0.05
        ))

        # Bonus por peso acumulado de triggers
        peso_total = sum(t.peso for t in triggers)
        bonus_peso = min(0.2, peso_total * 0.05)

        # Bonus por múltiples letras afectadas (indica impacto diverso)
        letras_afectadas = len(set(t.letra for t in triggers))
        bonus_letras = min(0.15, letras_afectadas * 0.03)

        return min(1.0, puntaje + bonus_peso + bonus_letras)

    def _calcular_puntaje_proyecto(self, datos_proyecto: dict[str, Any]) -> tuple[float, dict]:
        """Calcula el puntaje basado en las características del proyecto."""
        puntaje = 0.0
        factores_activos = {}

        for campo, config in self.FACTORES_PROYECTO.items():
            valor = datos_proyecto.get(campo, 0) or 0
            if valor > config["umbral"]:
                puntaje += config["peso"]
                factores_activos[campo] = {
                    "valor": valor,
                    "umbral": config["umbral"],
                    "descripcion": config["descripcion"],
                }

        # Factor adicional por tipo de minería
        tipo_mineria = (datos_proyecto.get("tipo_mineria") or "").lower()
        if "tajo abierto" in tipo_mineria or "rajo" in tipo_mineria:
            puntaje += 0.15
            factores_activos["tipo_mineria"] = {
                "valor": datos_proyecto.get("tipo_mineria"),
                "descripcion": "Minería a cielo abierto (mayor impacto visual y territorial)",
            }

        return min(1.0, puntaje), factores_activos

    def _calcular_sensibilidad_territorio(self, resultado_gis: dict[str, Any]) -> float:
        """Calcula el puntaje de sensibilidad del territorio."""
        puntaje = 0.0

        # Áreas protegidas
        areas = resultado_gis.get("areas_protegidas", [])
        if any(a.get("intersecta") for a in areas):
            puntaje += 0.4
        elif areas:
            puntaje += 0.15

        # Glaciares
        glaciares = resultado_gis.get("glaciares", [])
        if any(g.get("intersecta") for g in glaciares):
            puntaje += 0.4
        elif glaciares:
            puntaje += 0.2

        # Cuerpos de agua
        cuerpos = resultado_gis.get("cuerpos_agua", [])
        ramsar = any(c.get("es_sitio_ramsar") for c in cuerpos)
        if any(c.get("intersecta") for c in cuerpos):
            puntaje += 0.3 if ramsar else 0.2
        elif cuerpos:
            puntaje += 0.1

        # Comunidades indígenas
        comunidades = resultado_gis.get("comunidades_indigenas", [])
        if comunidades:
            dist_min = min(c.get("distancia_m", float("inf")) for c in comunidades)
            if dist_min < 5000:
                puntaje += 0.3
            elif dist_min < 10000:
                puntaje += 0.15

        return min(1.0, puntaje)

    def _determinar_clasificacion(
        self,
        puntaje: float,
        triggers: list[TriggerEIA],
        resumen: dict,
        factores: dict
    ) -> tuple[ViaIngreso, float, str]:
        """Determina la vía de ingreso basada en el puntaje y reglas."""

        # Regla 1: Trigger crítico = EIA automático
        if resumen.get("triggers_criticos", 0) > 0:
            criticos = [t for t in triggers if t.severidad == SeveridadTrigger.CRITICA]
            letras = ", ".join(set(t.letra.value for t in criticos))
            return (
                ViaIngreso.EIA,
                0.95,
                f"Se detectó al menos un trigger CRÍTICO del Art. 11 (letra(s) {letras}). "
                f"Según la Ley 19.300, esto determina ingreso obligatorio como EIA."
            )

        # Regla 2: Múltiples triggers altos = EIA muy probable
        if resumen.get("triggers_altos", 0) >= 2:
            return (
                ViaIngreso.EIA,
                0.85,
                f"Se detectaron {resumen['triggers_altos']} triggers de severidad ALTA. "
                f"La combinación de estos efectos indica que el proyecto genera impactos "
                f"significativos según el Art. 11 de la Ley 19.300."
            )

        # Regla 3: Puntaje alto de matriz
        if puntaje >= self.UMBRAL_EIA_AUTOMATICO:
            return (
                ViaIngreso.EIA,
                0.80,
                f"El análisis integrado (puntaje: {puntaje:.2f}) indica alta probabilidad "
                f"de efectos significativos. Se detectaron {len(triggers)} trigger(s) "
                f"y factores del proyecto que ameritan un EIA."
            )

        # Regla 4: Puntaje medio-alto
        if puntaje >= self.UMBRAL_EIA_PROBABLE:
            return (
                ViaIngreso.EIA,
                0.65,
                f"El análisis indica efectos potencialmente significativos (puntaje: {puntaje:.2f}). "
                f"Se recomienda EIA para abordar adecuadamente los {len(triggers)} trigger(s) detectados, "
                f"aunque un DIA con medidas robustas podría ser viable."
            )

        # Regla 5: Puntaje bajo-medio con triggers
        if puntaje >= self.UMBRAL_DIA_PROBABLE and triggers:
            return (
                ViaIngreso.DIA,
                0.60,
                f"El proyecto presenta {len(triggers)} trigger(s) de severidad menor (puntaje: {puntaje:.2f}). "
                f"Puede ingresar como DIA con medidas de mitigación y compensación adecuadas."
            )

        # Regla 6: Sin triggers significativos
        if not triggers:
            return (
                ViaIngreso.DIA,
                0.85,
                "No se detectaron triggers significativos del Art. 11. "
                "El proyecto puede ingresar como DIA con medidas de manejo ambiental estándar."
            )

        # Regla 7: Default - DIA con triggers menores
        return (
            ViaIngreso.DIA,
            0.70,
            f"El análisis indica impactos menores (puntaje: {puntaje:.2f}). "
            f"El proyecto puede ingresar como DIA implementando medidas específicas "
            f"para los {len(triggers)} aspecto(s) identificado(s)."
        )

    def _generar_recomendaciones(
        self,
        via_ingreso: ViaIngreso,
        triggers: list[TriggerEIA],
        datos_proyecto: dict
    ) -> list[str]:
        """Genera recomendaciones generales basadas en la clasificación."""
        recomendaciones = []

        if via_ingreso == ViaIngreso.EIA:
            recomendaciones.extend([
                "Elaborar Estudio de Impacto Ambiental (EIA) completo según DS 40/2012",
                "Incluir descripción detallada del proyecto y sus partes, obras y acciones",
                "Desarrollar línea base en todas las componentes ambientales relevantes",
                "Elaborar plan de medidas de mitigación, reparación y/o compensación",
                "Diseñar plan de seguimiento de variables ambientales",
                "Considerar proceso de Participación Ciudadana (PAC)",
            ])

            # Agregar recomendaciones específicas por trigger
            for trigger in triggers:
                recomendaciones.extend(trigger.recomendaciones[:2])  # Top 2 por trigger

        else:  # DIA
            recomendaciones.extend([
                "Elaborar Declaración de Impacto Ambiental (DIA) según DS 40/2012",
                "Describir el proyecto y sus obras, incluyendo cronograma",
                "Identificar permisos ambientales sectoriales (PAS) requeridos",
                "Presentar compromisos ambientales voluntarios",
            ])

            if triggers:
                recomendaciones.append(
                    "Incluir medidas de mitigación específicas para los aspectos identificados"
                )

        # Recomendaciones por tipo de proyecto
        tipo = (datos_proyecto.get("tipo_mineria") or "").lower()
        if "subterránea" in tipo:
            recomendaciones.append("Incluir plan de manejo de túneles y estabilidad geotécnica")
        elif "tajo" in tipo or "rajo" in tipo:
            recomendaciones.append("Elaborar plan de cierre y rehabilitación del rajo")

        # Eliminar duplicados manteniendo orden
        seen = set()
        return [x for x in recomendaciones if not (x in seen or seen.add(x))]

    def _determinar_nivel_confianza(self, confianza: float) -> NivelConfianza:
        """Determina el nivel de confianza basado en el valor numérico."""
        if confianza > 0.9:
            return NivelConfianza.MUY_ALTA
        elif confianza >= 0.75:
            return NivelConfianza.ALTA
        elif confianza >= 0.5:
            return NivelConfianza.MEDIA
        else:
            return NivelConfianza.BAJA

    def obtener_matriz_decision(self) -> dict[str, Any]:
        """Retorna la configuración de la matriz de decisión para documentación."""
        return {
            "pesos": {
                "triggers_criticos": self.PESO_TRIGGERS_CRITICOS,
                "triggers_altos": self.PESO_TRIGGERS_ALTOS,
                "triggers_medios": self.PESO_TRIGGERS_MEDIOS,
                "caracteristicas_proyecto": self.PESO_CARACTERISTICAS_PROYECTO,
                "sensibilidad_territorio": self.PESO_SENSIBILIDAD_TERRITORIO,
            },
            "umbrales": {
                "eia_automatico": self.UMBRAL_EIA_AUTOMATICO,
                "eia_probable": self.UMBRAL_EIA_PROBABLE,
                "dia_probable": self.UMBRAL_DIA_PROBABLE,
            },
            "factores_proyecto": self.FACTORES_PROYECTO,
            "reglas": [
                "1. Trigger CRÍTICO = EIA obligatorio (confianza 0.95)",
                "2. >=2 triggers ALTOS = EIA muy probable (confianza 0.85)",
                "3. Puntaje >= 0.75 = EIA recomendado (confianza 0.80)",
                "4. Puntaje 0.50-0.75 = EIA sugerido (confianza 0.65)",
                "5. Puntaje 0.30-0.50 con triggers = DIA con medidas (confianza 0.60)",
                "6. Sin triggers = DIA estándar (confianza 0.85)",
            ],
        }
