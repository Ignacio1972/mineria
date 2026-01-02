"""
Servicio principal del Asistente IA.

Implementa el agente conversacional con soporte para tool use,
manejo de contexto, memoria y confirmacion de acciones.
"""
import logging
import time
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import anthropic
from anthropic import APIError, RateLimitError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, update
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.models.asistente import (
    Conversacion,
    Mensaje,
    AccionPendiente,
    MemoriaUsuario,
    NotificacionEnviada,
    Feedback,
    RolMensaje,
    EstadoAccion,
)
from app.db.models import Proyecto, Cliente
from app.schemas.asistente import (
    ChatRequest,
    ChatResponse,
    MensajeResponse,
    AccionPendienteResponse,
    ConfirmacionAccion,
    ResultadoAccion,
    ContextoAsistente,
    FuenteCitada,
    ToolCall,
    ToolResult,
    TipoAccion,
)
from .tools import (
    registro_herramientas,
    ResultadoHerramienta,
    PermisoHerramienta,
    CategoriaHerramienta,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Constantes y Configuracion
# =============================================================================

SYSTEM_PROMPT_BASE = """Eres el Asistente IA del Sistema de Prefactibilidad Ambiental Minera de Chile.

Tu rol es ayudar a usuarios (consultores ambientales, empresas mineras, profesionales) a:
1. Entender la normativa ambiental chilena (Ley 19.300, DS 40/2012, guias SEA)
2. Evaluar si sus proyectos mineros requieren DIA o EIA segun el Art. 11
3. Interpretar resultados de analisis de prefactibilidad
4. Gestionar proyectos en el sistema

CAPACIDADES:
- Buscar en corpus legal (Ley 19.300, DS 40, guias SEA)
- Consultar proyectos y analisis del sistema
- Explicar clasificaciones DIA/EIA con fundamento legal
- Crear y modificar proyectos (requiere confirmacion)
- Ejecutar analisis de prefactibilidad (requiere confirmacion)

REGLAS IMPORTANTES:
1. SIEMPRE cita fuentes legales cuando expliques normativa
2. Las acciones que modifican datos REQUIEREN confirmacion del usuario
3. Si no encuentras informacion, indicalo claramente
4. Se conciso pero completo en tus respuestas
5. Usa lenguaje tecnico apropiado para profesionales ambientales

CONTEXTO DEL SISTEMA:
- Art. 11 Ley 19.300 define triggers para EIA (letras a-f)
- Clasificacion se basa en triggers detectados y matriz de decision
- Proyectos necesitan geometria definida para analisis espacial"""

MAX_TOOL_ITERATIONS = 10
MAX_CONTEXT_MESSAGES = 20
CONTEXT_WINDOW_TOKENS = 150000  # Reservar margen del limite de 200k

# Patrones de seguridad para sanitizacion
PATRONES_BLOQUEADOS = [
    r"ignore\s+(previous|all|your)\s+instructions?",
    r"disregard\s+(your|all)\s+instructions?",
    r"you\s+are\s+now",
    r"new\s+instructions?:",
    r"system\s+prompt:",
    r"jailbreak",
]


# =============================================================================
# Sanitizacion de Entrada
# =============================================================================

class SanitizadorEntrada:
    """Sanitiza entradas del usuario para prevenir prompt injection."""

    MAX_LENGTH = 4000

    @classmethod
    def sanitizar(cls, texto: str) -> str:
        """
        Sanitiza el texto de entrada.

        Args:
            texto: Texto a sanitizar

        Returns:
            Texto sanitizado

        Raises:
            ValueError: Si se detecta contenido malicioso
        """
        # Truncar si excede limite
        texto = texto[:cls.MAX_LENGTH]

        # Detectar intentos de inyeccion
        texto_lower = texto.lower()
        for patron in PATRONES_BLOQUEADOS:
            if re.search(patron, texto_lower, re.IGNORECASE):
                logger.warning(f"Intento de prompt injection detectado: {patron}")
                raise ValueError("Contenido no permitido detectado")

        # Solo eliminar caracteres de control, mantener puntuacion
        texto = ''.join(c for c in texto if c.isprintable() or c in '\n\t')

        return texto.strip()


# =============================================================================
# Gestor de Contexto
# =============================================================================

class GestorContexto:
    """Gestiona el contexto de la conversacion para el prompt."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def obtener_contexto(
        self,
        session_id: UUID,
        user_id: Optional[UUID] = None,
        proyecto_id: Optional[int] = None,
        vista_actual: str = "dashboard",
    ) -> ContextoAsistente:
        """
        Obtiene el contexto actual para incluir en el prompt.

        Args:
            session_id: ID de sesion
            user_id: ID de usuario opcional
            proyecto_id: ID de proyecto activo opcional
            vista_actual: Vista actual del frontend

        Returns:
            ContextoAsistente con la informacion relevante
        """
        contexto = ContextoAsistente(
            session_id=session_id,
            user_id=user_id,
            vista_actual=vista_actual,
        )

        # Obtener datos del usuario
        if user_id:
            result = await self.db.execute(
                select(Cliente).where(Cliente.id == user_id)
            )
            usuario = result.scalar()
            if usuario:
                contexto.usuario_nombre = usuario.razon_social

        # Obtener datos del proyecto activo
        if proyecto_id:
            result = await self.db.execute(
                select(Proyecto).where(Proyecto.id == proyecto_id)
            )
            proyecto = result.scalar()
            if proyecto:
                contexto.proyecto_id = proyecto.id
                contexto.proyecto_nombre = proyecto.nombre
                contexto.proyecto_estado = proyecto.estado
                contexto.proyecto_tiene_geometria = proyecto.geom is not None

                # Verificar si tiene analisis
                from sqlalchemy import text
                result = await self.db.execute(
                    text("SELECT COUNT(*) FROM proyectos.analisis WHERE proyecto_id = :id"),
                    {"id": proyecto_id}
                )
                count = result.scalar()
                contexto.proyecto_tiene_analisis = count > 0

        # Contar acciones pendientes
        result = await self.db.execute(
            select(func.count(AccionPendiente.id)).where(
                AccionPendiente.estado == "pendiente"
            )
        )
        contexto.acciones_pendientes = result.scalar() or 0

        return contexto

    def construir_prompt_contexto(self, contexto: ContextoAsistente) -> str:
        """
        Construye la seccion de contexto para el system prompt.

        Args:
            contexto: Contexto del asistente

        Returns:
            String con el contexto formateado
        """
        partes = ["\n\nCONTEXTO ACTUAL:"]

        if contexto.usuario_nombre:
            partes.append(f"- Usuario: {contexto.usuario_nombre}")

        if contexto.proyecto_id:
            partes.append(f"- Proyecto activo: {contexto.proyecto_nombre} (ID: {contexto.proyecto_id})")
            partes.append(f"  - Estado: {contexto.proyecto_estado}")
            partes.append(f"  - Tiene geometria: {'Si' if contexto.proyecto_tiene_geometria else 'No'}")
            partes.append(f"  - Tiene analisis: {'Si' if contexto.proyecto_tiene_analisis else 'No'}")

            if not contexto.proyecto_tiene_geometria:
                partes.append("  NOTA: El proyecto necesita geometria para ejecutar analisis")
        else:
            partes.append("- No hay proyecto activo seleccionado")

        partes.append(f"- Vista actual: {contexto.vista_actual}")

        if contexto.acciones_pendientes > 0:
            partes.append(f"- Acciones pendientes de confirmacion: {contexto.acciones_pendientes}")

        if contexto.resumen_conversacion:
            partes.append(f"\nRESUMEN CONVERSACION ANTERIOR:\n{contexto.resumen_conversacion}")

        return "\n".join(partes)


# =============================================================================
# Gestor de Memoria
# =============================================================================

class GestorMemoria:
    """Gestiona la memoria de conversacion a corto y largo plazo."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def obtener_historial(
        self,
        conversacion_id: UUID,
        limite: int = MAX_CONTEXT_MESSAGES,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de mensajes en formato Anthropic.

        Args:
            conversacion_id: ID de la conversacion
            limite: Numero maximo de mensajes

        Returns:
            Lista de mensajes en formato Anthropic
        """
        result = await self.db.execute(
            select(Mensaje)
            .where(Mensaje.conversacion_id == conversacion_id)
            .order_by(desc(Mensaje.created_at))
            .limit(limite)
        )
        mensajes_db = result.scalars().all()

        # Invertir para orden cronologico
        mensajes_db = list(reversed(mensajes_db))

        mensajes = []
        for msg in mensajes_db:
            if msg.rol == "user":
                mensajes.append({
                    "role": "user",
                    "content": msg.contenido,
                })
            elif msg.rol == "assistant":
                content = []
                # Agregar contenido de texto
                if msg.contenido:
                    content.append({
                        "type": "text",
                        "text": msg.contenido,
                    })
                # Agregar tool_use si existe
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        content.append({
                            "type": "tool_use",
                            "id": tc.get("id"),
                            "name": tc.get("name"),
                            "input": tc.get("input", {}),
                        })
                # Si hay tool_calls, siempre usar el formato de lista para content
                # para asegurar que los tool_use blocks se incluyan correctamente
                if msg.tool_calls:
                    mensajes.append({
                        "role": "assistant",
                        "content": content,
                    })
                else:
                    mensajes.append({
                        "role": "assistant",
                        "content": msg.contenido or "",
                    })
            elif msg.rol == "tool":
                mensajes.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id,
                        "content": msg.contenido,
                    }],
                })

        return mensajes

    async def guardar_mensaje(
        self,
        conversacion_id: UUID,
        rol: str,
        contenido: str,
        tool_calls: Optional[List[Dict]] = None,
        tool_call_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        fuentes: Optional[List[Dict]] = None,
        tokens_input: Optional[int] = None,
        tokens_output: Optional[int] = None,
        latencia_ms: Optional[int] = None,
        modelo_usado: Optional[str] = None,
    ) -> Mensaje:
        """
        Guarda un mensaje en la base de datos.

        Args:
            conversacion_id: ID de la conversacion
            rol: Rol del mensaje (user, assistant, tool)
            contenido: Contenido del mensaje
            tool_calls: Lista de tool calls (para assistant)
            tool_call_id: ID del tool call (para tool results)
            tool_name: Nombre de la herramienta
            fuentes: Fuentes citadas
            tokens_input: Tokens de entrada usados
            tokens_output: Tokens de salida generados
            latencia_ms: Latencia en milisegundos
            modelo_usado: Modelo LLM usado

        Returns:
            Mensaje creado
        """
        mensaje = Mensaje(
            conversacion_id=conversacion_id,
            rol=rol,
            contenido=contenido,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            fuentes=fuentes,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            latencia_ms=latencia_ms,
            modelo_usado=modelo_usado,
        )
        self.db.add(mensaje)
        await self.db.flush()
        return mensaje


# =============================================================================
# Ejecutor de Herramientas
# =============================================================================

class EjecutorHerramientas:
    """Ejecuta herramientas y maneja acciones pendientes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def ejecutar_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        conversacion_id: UUID,
    ) -> Tuple[ResultadoHerramienta, Optional[AccionPendiente]]:
        """
        Ejecuta una herramienta.

        Args:
            tool_name: Nombre de la herramienta
            tool_input: Parametros de entrada
            conversacion_id: ID de la conversacion

        Returns:
            Tupla con (resultado, accion_pendiente si requiere confirmacion)
        """
        herramienta = registro_herramientas.obtener(tool_name)
        if not herramienta:
            return ResultadoHerramienta(
                exito=False,
                contenido=None,
                error=f"Herramienta '{tool_name}' no encontrada"
            ), None

        # Verificar si requiere confirmacion
        if herramienta.requiere_confirmacion:
            # Crear accion pendiente en lugar de ejecutar
            accion = await self._crear_accion_pendiente(
                tool_name=tool_name,
                parametros=tool_input,
                conversacion_id=conversacion_id,
            )

            # Generar descripcion legible
            if hasattr(herramienta, 'generar_descripcion_confirmacion'):
                descripcion = herramienta.generar_descripcion_confirmacion(**tool_input)
            else:
                descripcion = f"Ejecutar {tool_name}"

            accion.descripcion = descripcion
            await self.db.flush()

            return ResultadoHerramienta(
                exito=True,
                contenido={
                    "accion_pendiente": True,
                    "accion_id": str(accion.id),
                    "tipo": tool_name,
                    "descripcion": descripcion,
                    "mensaje": "Esta accion requiere confirmacion del usuario antes de ejecutarse.",
                },
                metadata={"requiere_confirmacion": True}
            ), accion

        # Ejecutar directamente
        herramienta.set_db(self.db)
        resultado = await herramienta.ejecutar(**tool_input, db=self.db)
        return resultado, None

    async def _crear_accion_pendiente(
        self,
        tool_name: str,
        parametros: Dict[str, Any],
        conversacion_id: UUID,
    ) -> AccionPendiente:
        """Crea una accion pendiente de confirmacion."""
        # Mapear tool_name a TipoAccion
        tipo_mapping = {
            "crear_proyecto": "crear_proyecto",
            "actualizar_proyecto": "actualizar_proyecto",
            "ejecutar_analisis": "ejecutar_analisis",
        }
        tipo = tipo_mapping.get(tool_name, tool_name)

        accion = AccionPendiente(
            conversacion_id=conversacion_id,
            tipo=tipo,
            parametros=parametros,
            descripcion=f"Accion: {tool_name}",
            estado="pendiente",
            expires_at=datetime.utcnow() + timedelta(minutes=5),
        )
        self.db.add(accion)
        await self.db.flush()
        return accion

    async def confirmar_accion(
        self,
        accion_id: UUID,
        confirmacion: ConfirmacionAccion,
    ) -> ResultadoAccion:
        """
        Procesa la confirmacion o cancelacion de una accion.

        Args:
            accion_id: ID de la accion
            confirmacion: Datos de confirmacion

        Returns:
            ResultadoAccion con el resultado
        """
        result = await self.db.execute(
            select(AccionPendiente).where(AccionPendiente.id == accion_id)
        )
        accion = result.scalar()

        if not accion:
            return ResultadoAccion(
                exito=False,
                mensaje="Accion no encontrada",
                error="La accion solicitada no existe"
            )

        if accion.estado != "pendiente":
            return ResultadoAccion(
                exito=False,
                mensaje=f"La accion ya fue procesada (estado: {accion.estado})",
                error="Accion ya procesada"
            )

        if accion.esta_expirada:
            accion.estado = "expirada"
            await self.db.flush()
            return ResultadoAccion(
                exito=False,
                mensaje="La accion ha expirado",
                error="Accion expirada"
            )

        if not confirmacion.confirmada:
            accion.estado = "cancelada"
            await self.db.flush()
            return ResultadoAccion(
                exito=True,
                mensaje="Accion cancelada por el usuario",
            )

        # Ejecutar la accion
        try:
            herramienta = registro_herramientas.obtener(accion.tipo)
            if not herramienta:
                accion.estado = "error"
                accion.error_mensaje = f"Herramienta '{accion.tipo}' no encontrada"
                await self.db.flush()
                return ResultadoAccion(
                    exito=False,
                    mensaje="Error al ejecutar la accion",
                    error=accion.error_mensaje
                )

            herramienta.set_db(self.db)
            resultado = await herramienta.ejecutar(**accion.parametros, db=self.db)

            if resultado.exito:
                accion.estado = "ejecutada"
                accion.resultado = resultado.contenido
                accion.confirmed_at = datetime.utcnow()
                accion.executed_at = datetime.utcnow()
            else:
                accion.estado = "error"
                accion.error_mensaje = resultado.error

            await self.db.flush()

            return ResultadoAccion(
                exito=resultado.exito,
                mensaje="Accion ejecutada exitosamente" if resultado.exito else "Error al ejecutar",
                datos=resultado.contenido if resultado.exito else None,
                error=resultado.error if not resultado.exito else None,
            )

        except Exception as e:
            logger.error(f"Error ejecutando accion {accion_id}: {e}")
            accion.estado = "error"
            accion.error_mensaje = str(e)
            await self.db.flush()
            return ResultadoAccion(
                exito=False,
                mensaje="Error al ejecutar la accion",
                error=str(e)
            )


# =============================================================================
# Servicio Principal del Asistente
# =============================================================================

class AsistenteService:
    """
    Servicio principal del Asistente IA.

    Implementa el loop de tool use con Claude, manejo de contexto,
    memoria de conversacion y confirmacion de acciones.
    """

    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio.

        Args:
            db: Sesion de base de datos
        """
        self.db = db
        self.gestor_contexto = GestorContexto(db)
        self.gestor_memoria = GestorMemoria(db)
        self.ejecutor = EjecutorHerramientas(db)
        self._cliente: Optional[anthropic.AsyncAnthropic] = None

    @property
    def cliente(self) -> anthropic.AsyncAnthropic:
        """Lazy loading del cliente Anthropic."""
        if self._cliente is None:
            api_key = settings.ANTHROPIC_API_KEY
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY no configurada")
            self._cliente = anthropic.AsyncAnthropic(
                api_key=api_key,
                timeout=settings.LLM_TIMEOUT_SECONDS if hasattr(settings, 'LLM_TIMEOUT_SECONDS') else 120,
            )
        return self._cliente

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Procesa un mensaje del usuario y genera una respuesta.

        Args:
            request: Solicitud de chat

        Returns:
            ChatResponse con la respuesta del asistente
        """
        inicio = time.time()

        try:
            # Sanitizar entrada
            mensaje_sanitizado = SanitizadorEntrada.sanitizar(request.mensaje)
        except ValueError as e:
            raise ValueError(f"Mensaje invalido: {e}")

        # Obtener o crear conversacion
        conversacion = await self._obtener_o_crear_conversacion(request)

        # Guardar mensaje del usuario
        await self.gestor_memoria.guardar_mensaje(
            conversacion_id=conversacion.id,
            rol="user",
            contenido=mensaje_sanitizado,
        )

        # Obtener contexto
        contexto = await self.gestor_contexto.obtener_contexto(
            session_id=request.session_id,
            user_id=request.user_id,
            proyecto_id=request.proyecto_contexto_id,
            vista_actual=request.vista_actual or "dashboard",
        )

        # Construir system prompt
        system_prompt = SYSTEM_PROMPT_BASE + self.gestor_contexto.construir_prompt_contexto(contexto)

        # Obtener historial
        historial = await self.gestor_memoria.obtener_historial(conversacion.id)

        # Agregar mensaje actual si no esta en historial
        if not historial or historial[-1].get("content") != mensaje_sanitizado:
            historial.append({
                "role": "user",
                "content": mensaje_sanitizado,
            })

        # Obtener herramientas disponibles
        tools = registro_herramientas.obtener_tools_anthropic()

        # Ejecutar loop de tool use
        respuesta_final, tool_calls, fuentes, accion_pendiente = await self._ejecutar_loop_tool_use(
            system_prompt=system_prompt,
            messages=historial,
            tools=tools,
            conversacion_id=conversacion.id,
        )

        # Calcular metricas
        latencia_ms = int((time.time() - inicio) * 1000)

        # Guardar respuesta del asistente
        # Nota: Los tool_calls ya fueron guardados en los mensajes intermedios dentro del loop,
        # por lo que el mensaje final no debe incluirlos para evitar duplicados en el historial
        mensaje_guardado = await self.gestor_memoria.guardar_mensaje(
            conversacion_id=conversacion.id,
            rol="assistant",
            contenido=respuesta_final,
            tool_calls=None,  # Los tool_calls ya fueron guardados en mensajes intermedios
            fuentes=[f.model_dump() for f in fuentes] if fuentes else None,
            latencia_ms=latencia_ms,
            modelo_usado=settings.LLM_MODEL,
        )

        await self.db.commit()

        # Construir respuesta
        return ChatResponse(
            conversacion_id=conversacion.id,
            mensaje=MensajeResponse(
                id=mensaje_guardado.id,
                conversacion_id=conversacion.id,
                rol=RolMensaje.ASSISTANT,
                contenido=respuesta_final,
                tool_calls=tool_calls,
                fuentes=fuentes,
                latencia_ms=latencia_ms,
                created_at=mensaje_guardado.created_at,
            ),
            accion_pendiente=AccionPendienteResponse(
                id=accion_pendiente.id,
                conversacion_id=accion_pendiente.conversacion_id,
                tipo=TipoAccion(accion_pendiente.tipo),
                parametros=accion_pendiente.parametros,
                descripcion=accion_pendiente.descripcion,
                estado=EstadoAccion(accion_pendiente.estado),
                created_at=accion_pendiente.created_at,
                expires_at=accion_pendiente.expires_at,
            ) if accion_pendiente else None,
            sugerencias=self._generar_sugerencias(contexto, respuesta_final),
        )

    async def _obtener_o_crear_conversacion(self, request: ChatRequest) -> Conversacion:
        """Obtiene una conversacion existente o crea una nueva."""
        if request.conversacion_id:
            result = await self.db.execute(
                select(Conversacion).where(
                    Conversacion.id == request.conversacion_id,
                    Conversacion.activa == True,
                )
            )
            conversacion = result.scalar()
            if conversacion:
                # Actualizar contexto
                conversacion.proyecto_activo_id = request.proyecto_contexto_id
                conversacion.vista_actual = request.vista_actual or conversacion.vista_actual
                conversacion.updated_at = datetime.utcnow()
                return conversacion

        # Crear nueva conversacion
        conversacion = Conversacion(
            session_id=request.session_id,
            user_id=request.user_id,
            proyecto_activo_id=request.proyecto_contexto_id,
            vista_actual=request.vista_actual or "dashboard",
            titulo=self._generar_titulo(request.mensaje),
        )
        self.db.add(conversacion)
        await self.db.flush()
        return conversacion

    def _generar_titulo(self, mensaje: str) -> str:
        """Genera un titulo para la conversacion basado en el primer mensaje."""
        # Tomar las primeras palabras
        palabras = mensaje.split()[:8]
        titulo = " ".join(palabras)
        if len(mensaje.split()) > 8:
            titulo += "..."
        return titulo[:100]

    async def _ejecutar_loop_tool_use(
        self,
        system_prompt: str,
        messages: List[Dict],
        tools: List[Dict],
        conversacion_id: UUID,
    ) -> Tuple[str, List[ToolCall], List[FuenteCitada], Optional[AccionPendiente]]:
        """
        Ejecuta el loop de tool use hasta obtener respuesta final.

        Args:
            system_prompt: Prompt de sistema
            messages: Historial de mensajes
            tools: Herramientas disponibles
            conversacion_id: ID de la conversacion

        Returns:
            Tupla con (respuesta_final, tool_calls, fuentes, accion_pendiente)
        """
        tool_calls_realizados = []
        fuentes = []
        accion_pendiente = None
        iteracion = 0

        while iteracion < MAX_TOOL_ITERATIONS:
            iteracion += 1

            try:
                response = await self.cliente.messages.create(
                    model=settings.LLM_MODEL,
                    max_tokens=settings.LLM_MAX_TOKENS,
                    system=system_prompt,
                    messages=messages,
                    tools=tools,
                )
            except RateLimitError as e:
                logger.warning(f"Rate limit alcanzado: {e}")
                raise
            except APIError as e:
                logger.error(f"Error API Anthropic: {e}")
                raise

            # Procesar respuesta
            texto_respuesta = ""
            tool_uses = []

            for block in response.content:
                if block.type == "text":
                    texto_respuesta += block.text
                elif block.type == "tool_use":
                    tool_uses.append(block)
                    tool_calls_realizados.append(ToolCall(
                        id=block.id,
                        name=block.name,
                        input=block.input,
                    ))

            # Si no hay tool_use, retornar respuesta
            if response.stop_reason == "end_turn" or not tool_uses:
                return texto_respuesta, tool_calls_realizados, fuentes, accion_pendiente

            # Primero, guardar el mensaje del asistente con tool_use en la BD
            # Esto debe hacerse ANTES de guardar los tool results para mantener el orden correcto
            assistant_tool_calls = [
                {"id": tu.id, "name": tu.name, "input": tu.input}
                for tu in tool_uses
            ]
            await self.gestor_memoria.guardar_mensaje(
                conversacion_id=conversacion_id,
                rol="assistant",
                contenido=texto_respuesta or "",
                tool_calls=assistant_tool_calls,
            )

            # Procesar tool_uses
            tool_results = []
            for tool_use in tool_uses:
                logger.info(f"Ejecutando herramienta: {tool_use.name}")

                resultado, accion = await self.ejecutor.ejecutar_tool(
                    tool_name=tool_use.name,
                    tool_input=tool_use.input,
                    conversacion_id=conversacion_id,
                )

                if accion:
                    accion_pendiente = accion

                # Guardar mensaje de tool result
                await self.gestor_memoria.guardar_mensaje(
                    conversacion_id=conversacion_id,
                    rol="tool",
                    contenido=str(resultado.to_dict()),
                    tool_call_id=tool_use.id,
                    tool_name=tool_use.name,
                )

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": str(resultado.to_dict()),
                })

                # Extraer fuentes de herramientas RAG
                if resultado.exito and tool_use.name in ["buscar_normativa", "explicar_clasificacion"]:
                    fuentes.extend(self._extraer_fuentes(tool_use.name, resultado))

            # Agregar respuesta del asistente y tool results al historial local
            assistant_content = []
            if texto_respuesta:
                assistant_content.append({"type": "text", "text": texto_respuesta})
            for tu in tool_uses:
                assistant_content.append({
                    "type": "tool_use",
                    "id": tu.id,
                    "name": tu.name,
                    "input": tu.input,
                })

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

            # Si hay accion pendiente, detener loop y solicitar confirmacion
            if accion_pendiente:
                # Agregar mensaje indicando accion pendiente
                texto_respuesta = await self._generar_mensaje_confirmacion(
                    accion_pendiente, system_prompt, messages
                )
                return texto_respuesta, tool_calls_realizados, fuentes, accion_pendiente

        # Limite de iteraciones alcanzado
        logger.warning("Limite de iteraciones de tool use alcanzado")
        return texto_respuesta, tool_calls_realizados, fuentes, accion_pendiente

    async def _generar_mensaje_confirmacion(
        self,
        accion: AccionPendiente,
        system_prompt: str,
        messages: List[Dict],
    ) -> str:
        """Genera mensaje solicitando confirmacion al usuario."""
        try:
            # Pedir al modelo que genere mensaje de confirmacion
            prompt_confirmacion = f"""
El usuario ha solicitado una accion que requiere confirmacion.

Accion: {accion.tipo}
Descripcion: {accion.descripcion}
Parametros: {accion.parametros}

Genera un mensaje breve y claro explicando lo que se va a hacer y pidiendo confirmacion al usuario.
"""
            messages_confirm = messages.copy()
            messages_confirm.append({
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": "confirm", "content": prompt_confirmacion}]
            })

            response = await self.cliente.messages.create(
                model=settings.LLM_MODEL,
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt_confirmacion}],
            )

            for block in response.content:
                if block.type == "text":
                    return block.text

            return f"Para ejecutar esta accion ({accion.descripcion}), por favor confirma."
        except Exception as e:
            logger.error(f"Error generando mensaje de confirmacion: {e}")
            return f"Se requiere confirmacion para: {accion.descripcion}"

    def _extraer_fuentes(
        self,
        tool_name: str,
        resultado: ResultadoHerramienta,
    ) -> List[FuenteCitada]:
        """Extrae fuentes citadas de resultados de herramientas RAG."""
        fuentes = []

        if not resultado.contenido:
            return fuentes

        if tool_name == "buscar_normativa":
            fragmentos = resultado.contenido.get("fragmentos", [])
            for frag in fragmentos[:5]:  # Limitar a 5 fuentes
                documento_id = frag.get("documento_id")
                fuentes.append(FuenteCitada(
                    tipo="legal",
                    titulo=frag.get("documento_titulo", ""),
                    referencia=frag.get("articulo") or frag.get("seccion"),
                    fragmento=frag.get("contenido", "")[:200],
                    confianza=frag.get("similitud"),
                    documento_id=documento_id,
                    url_documento=f"/corpus?doc={documento_id}" if documento_id else None,
                    url_descarga=f"/api/v1/corpus/{documento_id}/archivo" if documento_id else None,
                ))

        elif tool_name == "explicar_clasificacion":
            fundamentos = resultado.contenido.get("fundamentos_legales", [])
            for fund in fundamentos:
                fuentes.append(FuenteCitada(
                    tipo="legal",
                    titulo=fund.get("articulo", ""),
                    referencia=f"Letra {fund.get('letra', '')}",
                    fragmento=fund.get("descripcion", ""),
                ))

        return fuentes

    def _generar_sugerencias(
        self,
        contexto: ContextoAsistente,
        respuesta: str,
    ) -> List[str]:
        """Genera sugerencias de acciones siguientes basadas en el contexto."""
        sugerencias = []

        if contexto.proyecto_id:
            if not contexto.proyecto_tiene_geometria:
                sugerencias.append("Definir geometria del proyecto en el mapa")
            elif not contexto.proyecto_tiene_analisis:
                sugerencias.append("Ejecutar analisis de prefactibilidad")
            else:
                sugerencias.append("Ver resultados del analisis")
                sugerencias.append("Exportar informe")
        else:
            sugerencias.append("Crear nuevo proyecto")
            sugerencias.append("Ver proyectos existentes")

        return sugerencias[:3]  # Limitar a 3 sugerencias

    async def confirmar_accion(
        self,
        accion_id: UUID,
        confirmacion: ConfirmacionAccion,
    ) -> ResultadoAccion:
        """
        Confirma o cancela una accion pendiente.

        Args:
            accion_id: ID de la accion
            confirmacion: Datos de confirmacion

        Returns:
            ResultadoAccion con el resultado
        """
        resultado = await self.ejecutor.confirmar_accion(accion_id, confirmacion)
        await self.db.commit()
        return resultado

    async def obtener_historial(
        self,
        session_id: UUID,
        limite: int = 50,
    ) -> List[Conversacion]:
        """
        Obtiene el historial de conversaciones de una sesion.

        Args:
            session_id: ID de sesion
            limite: Numero maximo de conversaciones

        Returns:
            Lista de conversaciones
        """
        result = await self.db.execute(
            select(Conversacion)
            .where(Conversacion.session_id == session_id)
            .options(selectinload(Conversacion.mensajes))
            .order_by(desc(Conversacion.updated_at))
            .limit(limite)
        )
        return result.scalars().all()

    async def obtener_conversacion(
        self,
        conversacion_id: UUID,
    ) -> Optional[Conversacion]:
        """
        Obtiene una conversacion con sus mensajes.

        Args:
            conversacion_id: ID de la conversacion

        Returns:
            Conversacion o None
        """
        result = await self.db.execute(
            select(Conversacion)
            .where(Conversacion.id == conversacion_id)
            .options(selectinload(Conversacion.mensajes))
        )
        return result.scalar()


# =============================================================================
# Factory Function
# =============================================================================

def get_asistente_service(db: AsyncSession) -> AsistenteService:
    """
    Factory function para obtener el servicio del asistente.

    Args:
        db: Sesion de base de datos

    Returns:
        AsistenteService configurado
    """
    return AsistenteService(db)
