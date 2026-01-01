-- ============================================================================
-- SCHEMA: Sistema de Asistente IA Conversacional
-- Proyecto: Mineria Ambiental
-- Version: 1.0
-- Fecha: 2025-12-31
-- Descripcion: Tablas para el asistente IA con tool use, memoria y proactividad
-- ============================================================================

-- Crear schema
CREATE SCHEMA IF NOT EXISTS asistente;

-- ============================================================================
-- TABLA: asistente.conversaciones
-- Sesiones de chat del asistente
-- ============================================================================
CREATE TABLE IF NOT EXISTS asistente.conversaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identificacion de sesion
    session_id UUID NOT NULL,

    -- Usuario (referencia a clientes como "usuarios" del sistema)
    user_id UUID REFERENCES proyectos.clientes(id) ON DELETE SET NULL,

    -- Metadatos de la conversacion
    titulo VARCHAR(255),

    -- Contexto activo durante la conversacion
    proyecto_activo_id INTEGER REFERENCES proyectos.proyectos(id) ON DELETE SET NULL,
    vista_actual VARCHAR(50) DEFAULT 'dashboard',

    -- Estado
    activa BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Datos adicionales (preferencias de sesion, etc.)
    datos_extra JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_conversaciones_session
    ON asistente.conversaciones(session_id);
CREATE INDEX IF NOT EXISTS idx_conversaciones_user
    ON asistente.conversaciones(user_id);
CREATE INDEX IF NOT EXISTS idx_conversaciones_proyecto
    ON asistente.conversaciones(proyecto_activo_id);
CREATE INDEX IF NOT EXISTS idx_conversaciones_activa
    ON asistente.conversaciones(activa) WHERE activa = TRUE;
CREATE INDEX IF NOT EXISTS idx_conversaciones_created
    ON asistente.conversaciones(created_at DESC);

COMMENT ON TABLE asistente.conversaciones IS 'Sesiones de chat del asistente IA';
COMMENT ON COLUMN asistente.conversaciones.session_id IS 'ID de sesion del navegador/cliente';
COMMENT ON COLUMN asistente.conversaciones.vista_actual IS 'Vista del frontend donde esta el usuario';

-- ============================================================================
-- TABLA: asistente.mensajes
-- Mensajes de la conversacion (user, assistant, system, tool)
-- ============================================================================
CREATE TABLE IF NOT EXISTS asistente.mensajes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Conversacion padre
    conversacion_id UUID NOT NULL REFERENCES asistente.conversaciones(id) ON DELETE CASCADE,

    -- Rol del mensaje
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('user', 'assistant', 'system', 'tool')),

    -- Contenido del mensaje
    contenido TEXT NOT NULL,

    -- Tool use (para mensajes del asistente que llaman herramientas)
    tool_calls JSONB,
    -- Ejemplo: [{"id": "call_123", "name": "buscar_normativa", "input": {"query": "art 11"}}]

    -- Tool result (para mensajes de tipo 'tool')
    tool_call_id VARCHAR(100),
    tool_name VARCHAR(100),

    -- Fuentes citadas en la respuesta
    fuentes JSONB,
    -- Ejemplo: [{"tipo": "legal", "titulo": "Ley 19300", "articulo": "11"}]

    -- Metricas de uso
    tokens_input INTEGER,
    tokens_output INTEGER,
    latencia_ms INTEGER,
    modelo_usado VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Datos adicionales
    datos_extra JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_mensajes_conversacion
    ON asistente.mensajes(conversacion_id);
CREATE INDEX IF NOT EXISTS idx_mensajes_rol
    ON asistente.mensajes(rol);
CREATE INDEX IF NOT EXISTS idx_mensajes_created
    ON asistente.mensajes(created_at);
CREATE INDEX IF NOT EXISTS idx_mensajes_tool_call
    ON asistente.mensajes(tool_call_id) WHERE tool_call_id IS NOT NULL;

COMMENT ON TABLE asistente.mensajes IS 'Mensajes de las conversaciones del asistente';
COMMENT ON COLUMN asistente.mensajes.tool_calls IS 'Llamadas a herramientas solicitadas por el asistente';
COMMENT ON COLUMN asistente.mensajes.tool_call_id IS 'ID de la llamada de herramienta que este mensaje responde';

-- ============================================================================
-- TABLA: asistente.acciones_pendientes
-- Acciones que requieren confirmacion del usuario
-- ============================================================================
CREATE TABLE IF NOT EXISTS asistente.acciones_pendientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Conversacion donde se genero la accion
    conversacion_id UUID NOT NULL REFERENCES asistente.conversaciones(id) ON DELETE CASCADE,

    -- Mensaje que genero la accion
    mensaje_id UUID REFERENCES asistente.mensajes(id) ON DELETE SET NULL,

    -- Tipo de accion
    tipo VARCHAR(50) NOT NULL,
    -- Valores: crear_proyecto, ejecutar_analisis, actualizar_proyecto, exportar_informe

    -- Parametros de la accion
    parametros JSONB NOT NULL,
    -- Ejemplo: {"nombre": "Mina Norte", "region": "Atacama", "tipo_mineria": "cielo_abierto"}

    -- Descripcion legible para el usuario
    descripcion TEXT NOT NULL,

    -- Estado de la accion
    estado VARCHAR(20) DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'confirmada', 'cancelada', 'expirada', 'ejecutada', 'error')),

    -- Resultado de la ejecucion (si se confirmo)
    resultado JSONB,
    error_mensaje TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '5 minutes',
    confirmed_at TIMESTAMP WITH TIME ZONE,
    executed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_acciones_conversacion
    ON asistente.acciones_pendientes(conversacion_id);
CREATE INDEX IF NOT EXISTS idx_acciones_estado
    ON asistente.acciones_pendientes(estado);
CREATE INDEX IF NOT EXISTS idx_acciones_pendientes_activas
    ON asistente.acciones_pendientes(estado, expires_at)
    WHERE estado = 'pendiente';
CREATE INDEX IF NOT EXISTS idx_acciones_tipo
    ON asistente.acciones_pendientes(tipo);

COMMENT ON TABLE asistente.acciones_pendientes IS 'Acciones del asistente que requieren confirmacion del usuario';
COMMENT ON COLUMN asistente.acciones_pendientes.expires_at IS 'Tiempo limite para confirmar (default 5 minutos)';

-- ============================================================================
-- TABLA: asistente.memoria_usuario
-- Memoria a largo plazo por usuario
-- ============================================================================
CREATE TABLE IF NOT EXISTS asistente.memoria_usuario (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Usuario
    user_id UUID REFERENCES proyectos.clientes(id) ON DELETE CASCADE,

    -- Tipo de memoria
    tipo VARCHAR(50) NOT NULL,
    -- Valores: preferencia, consulta_frecuente, feedback, hecho_importante

    -- Clave-valor
    clave VARCHAR(100),
    valor JSONB NOT NULL,

    -- Embedding para busqueda semantica (hechos importantes)
    embedding vector(384),

    -- Relevancia/peso
    importancia FLOAT DEFAULT 1.0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraint para preferencias unicas por usuario
    CONSTRAINT memoria_preferencia_unica UNIQUE NULLS NOT DISTINCT (user_id, tipo, clave)
);

CREATE INDEX IF NOT EXISTS idx_memoria_user
    ON asistente.memoria_usuario(user_id);
CREATE INDEX IF NOT EXISTS idx_memoria_tipo
    ON asistente.memoria_usuario(tipo);
CREATE INDEX IF NOT EXISTS idx_memoria_clave
    ON asistente.memoria_usuario(clave) WHERE clave IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_memoria_embedding
    ON asistente.memoria_usuario USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)
    WHERE embedding IS NOT NULL;

COMMENT ON TABLE asistente.memoria_usuario IS 'Memoria persistente del asistente por usuario';
COMMENT ON COLUMN asistente.memoria_usuario.embedding IS 'Vector para busqueda semantica de hechos importantes';

-- ============================================================================
-- TABLA: asistente.documentacion_sistema
-- Documentacion del sistema para RAG (CLAUDE.md, docstrings, etc.)
-- ============================================================================
CREATE TABLE IF NOT EXISTS asistente.documentacion_sistema (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Tipo de documentacion
    tipo VARCHAR(50) NOT NULL,
    -- Valores: archivo_md, docstring, endpoint, componente, guia_uso

    -- Ubicacion
    ruta VARCHAR(500),

    -- Contenido
    titulo VARCHAR(255),
    contenido TEXT NOT NULL,

    -- Embedding para busqueda semantica
    embedding vector(384),

    -- Metadatos
    version VARCHAR(50),
    tags VARCHAR(100)[] DEFAULT '{}',

    -- Estado
    activo BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Metadatos adicionales
    datos_extra JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_documentacion_tipo
    ON asistente.documentacion_sistema(tipo);
CREATE INDEX IF NOT EXISTS idx_documentacion_ruta
    ON asistente.documentacion_sistema(ruta);
CREATE INDEX IF NOT EXISTS idx_documentacion_tags
    ON asistente.documentacion_sistema USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_documentacion_activo
    ON asistente.documentacion_sistema(activo) WHERE activo = TRUE;
CREATE INDEX IF NOT EXISTS idx_documentacion_embedding
    ON asistente.documentacion_sistema USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
    WHERE embedding IS NOT NULL;

-- Full-text search en titulo y contenido
CREATE INDEX IF NOT EXISTS idx_documentacion_fts
    ON asistente.documentacion_sistema
    USING GIN(to_tsvector('spanish', coalesce(titulo, '') || ' ' || contenido));

COMMENT ON TABLE asistente.documentacion_sistema IS 'Documentacion del sistema para RAG del asistente';

-- ============================================================================
-- TABLA: asistente.triggers_proactivos
-- Configuracion de triggers para modo proactivo
-- ============================================================================
CREATE TABLE IF NOT EXISTS asistente.triggers_proactivos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identificacion
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,

    -- Configuracion
    activo BOOLEAN DEFAULT TRUE,
    prioridad INTEGER DEFAULT 5,  -- 1 = maxima, 10 = minima

    -- Condicion SQL (se evalua periodicamente)
    condicion_sql TEXT NOT NULL,

    -- Template del mensaje
    mensaje_template TEXT NOT NULL,

    -- Accion sugerida
    accion_sugerida VARCHAR(100),
    accion_parametros JSONB,

    -- Limites
    max_por_hora INTEGER DEFAULT 3,
    cooldown_minutos INTEGER DEFAULT 30,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insertar triggers predefinidos
INSERT INTO asistente.triggers_proactivos (codigo, nombre, descripcion, prioridad, condicion_sql, mensaje_template, accion_sugerida) VALUES
    (
        'proyecto_sin_geometria',
        'Proyecto sin geometria',
        'Detecta proyectos en borrador sin geometria definida despues de 1 dia',
        3,
        'SELECT p.id, p.nombre FROM proyectos.proyectos p WHERE p.estado IN (''borrador'', ''completo'') AND p.geom IS NULL AND p.created_at < NOW() - INTERVAL ''1 day''',
        'El proyecto "{nombre}" no tiene geometria definida. ¿Desea ir al mapa para dibujarla?',
        'navegar_mapa'
    ),
    (
        'analisis_desactualizado',
        'Analisis desactualizado',
        'Detecta proyectos cuya geometria fue modificada despues del ultimo analisis',
        2,
        'SELECT p.id, p.nombre FROM proyectos.proyectos p JOIN proyectos.analisis a ON a.proyecto_id = p.id WHERE p.updated_at > a.fecha_analisis ORDER BY p.updated_at DESC',
        'La geometria del proyecto "{nombre}" fue modificada despues del ultimo analisis. ¿Desea ejecutar un nuevo analisis?',
        'ejecutar_analisis'
    ),
    (
        'alertas_criticas_sin_revisar',
        'Alertas criticas sin revisar',
        'Detecta analisis con alertas criticas que no han sido revisadas',
        1,
        'SELECT p.id, p.nombre, a.id as analisis_id FROM proyectos.proyectos p JOIN proyectos.analisis a ON a.proyecto_id = p.id WHERE a.datos_extra->''alertas_criticas'' IS NOT NULL AND (a.datos_extra->>''alertas_revisadas'')::boolean IS NOT TRUE',
        'El analisis del proyecto "{nombre}" tiene alertas criticas que requieren atencion. ¿Desea revisarlas?',
        'ver_analisis'
    ),
    (
        'proyecto_listo_analisis',
        'Proyecto listo para analisis',
        'Detecta proyectos con geometria que nunca han sido analizados',
        4,
        'SELECT p.id, p.nombre FROM proyectos.proyectos p WHERE p.geom IS NOT NULL AND NOT EXISTS (SELECT 1 FROM proyectos.analisis a WHERE a.proyecto_id = p.id)',
        'El proyecto "{nombre}" tiene geometria definida pero no ha sido analizado. ¿Desea ejecutar el analisis de prefactibilidad?',
        'ejecutar_analisis'
    )
ON CONFLICT (codigo) DO NOTHING;

COMMENT ON TABLE asistente.triggers_proactivos IS 'Configuracion de triggers para notificaciones proactivas del asistente';

-- ============================================================================
-- TABLA: asistente.notificaciones_enviadas
-- Registro de notificaciones proactivas enviadas
-- ============================================================================
CREATE TABLE IF NOT EXISTS asistente.notificaciones_enviadas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Trigger que genero la notificacion
    trigger_id UUID REFERENCES asistente.triggers_proactivos(id) ON DELETE SET NULL,
    trigger_codigo VARCHAR(50),

    -- Usuario destinatario
    user_id UUID REFERENCES proyectos.clientes(id) ON DELETE CASCADE,
    session_id UUID,

    -- Contexto
    proyecto_id INTEGER REFERENCES proyectos.proyectos(id) ON DELETE SET NULL,

    -- Mensaje enviado
    mensaje TEXT NOT NULL,

    -- Estado
    leida BOOLEAN DEFAULT FALSE,
    accion_tomada VARCHAR(50),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    leida_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_notificaciones_user
    ON asistente.notificaciones_enviadas(user_id);
CREATE INDEX IF NOT EXISTS idx_notificaciones_session
    ON asistente.notificaciones_enviadas(session_id);
CREATE INDEX IF NOT EXISTS idx_notificaciones_trigger
    ON asistente.notificaciones_enviadas(trigger_codigo);
CREATE INDEX IF NOT EXISTS idx_notificaciones_no_leidas
    ON asistente.notificaciones_enviadas(user_id, leida) WHERE leida = FALSE;
CREATE INDEX IF NOT EXISTS idx_notificaciones_created
    ON asistente.notificaciones_enviadas(created_at DESC);

COMMENT ON TABLE asistente.notificaciones_enviadas IS 'Historial de notificaciones proactivas enviadas';

-- ============================================================================
-- TABLA: asistente.feedback
-- Feedback del usuario sobre respuestas del asistente
-- ============================================================================
CREATE TABLE IF NOT EXISTS asistente.feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Mensaje evaluado
    mensaje_id UUID NOT NULL REFERENCES asistente.mensajes(id) ON DELETE CASCADE,

    -- Usuario que da feedback
    user_id UUID REFERENCES proyectos.clientes(id) ON DELETE SET NULL,

    -- Valoracion
    valoracion INTEGER CHECK (valoracion BETWEEN 1 AND 5),
    es_util BOOLEAN,

    -- Comentario opcional
    comentario TEXT,

    -- Categorias de problema (si aplica)
    categorias_problema VARCHAR(50)[] DEFAULT '{}',
    -- Valores: incorrecto, incompleto, confuso, lento, otro

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_mensaje
    ON asistente.feedback(mensaje_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user
    ON asistente.feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_valoracion
    ON asistente.feedback(valoracion);

COMMENT ON TABLE asistente.feedback IS 'Feedback de usuarios sobre respuestas del asistente';

-- ============================================================================
-- VISTA: asistente.corpus_unificado
-- Vista unificada para RAG (legal + sistema)
-- ============================================================================
CREATE OR REPLACE VIEW asistente.corpus_unificado AS
SELECT
    f.id::text as id,
    'legal' as origen,
    f.contenido,
    f.embedding,
    jsonb_build_object(
        'documento_id', f.documento_id,
        'articulo', f.articulo,
        'seccion', f.seccion,
        'documento_titulo', d.titulo,
        'documento_tipo', d.tipo
    ) as metadata
FROM legal.fragmentos f
JOIN legal.documentos d ON f.documento_id = d.id
WHERE f.embedding IS NOT NULL

UNION ALL

SELECT
    ds.id::text as id,
    'sistema' as origen,
    ds.contenido,
    ds.embedding,
    jsonb_build_object(
        'tipo', ds.tipo,
        'ruta', ds.ruta,
        'titulo', ds.titulo,
        'tags', ds.tags
    ) as metadata
FROM asistente.documentacion_sistema ds
WHERE ds.embedding IS NOT NULL AND ds.activo = TRUE;

COMMENT ON VIEW asistente.corpus_unificado IS 'Vista unificada del corpus para busqueda RAG (legal + sistema)';

-- ============================================================================
-- VISTA: asistente.v_conversaciones_recientes
-- Conversaciones recientes con estadisticas
-- ============================================================================
CREATE OR REPLACE VIEW asistente.v_conversaciones_recientes AS
SELECT
    c.id,
    c.session_id,
    c.user_id,
    cl.razon_social as usuario_nombre,
    c.titulo,
    c.proyecto_activo_id,
    p.nombre as proyecto_nombre,
    c.created_at,
    c.updated_at,
    (SELECT COUNT(*) FROM asistente.mensajes m WHERE m.conversacion_id = c.id) as total_mensajes,
    (SELECT COUNT(*) FROM asistente.mensajes m WHERE m.conversacion_id = c.id AND m.rol = 'user') as mensajes_usuario,
    (SELECT MAX(created_at) FROM asistente.mensajes m WHERE m.conversacion_id = c.id) as ultimo_mensaje_at
FROM asistente.conversaciones c
LEFT JOIN proyectos.clientes cl ON c.user_id = cl.id
LEFT JOIN proyectos.proyectos p ON c.proyecto_activo_id = p.id
WHERE c.activa = TRUE
ORDER BY c.updated_at DESC;

-- ============================================================================
-- VISTA: asistente.v_metricas_uso
-- Metricas de uso del asistente
-- ============================================================================
CREATE OR REPLACE VIEW asistente.v_metricas_uso AS
SELECT
    DATE(m.created_at) as fecha,
    COUNT(DISTINCT c.id) as conversaciones,
    COUNT(DISTINCT c.user_id) as usuarios_unicos,
    COUNT(*) FILTER (WHERE m.rol = 'user') as mensajes_usuario,
    COUNT(*) FILTER (WHERE m.rol = 'assistant') as mensajes_asistente,
    COUNT(*) FILTER (WHERE m.tool_calls IS NOT NULL) as llamadas_herramientas,
    AVG(m.tokens_input) FILTER (WHERE m.tokens_input IS NOT NULL) as avg_tokens_input,
    AVG(m.tokens_output) FILTER (WHERE m.tokens_output IS NOT NULL) as avg_tokens_output,
    AVG(m.latencia_ms) FILTER (WHERE m.latencia_ms IS NOT NULL) as avg_latencia_ms
FROM asistente.mensajes m
JOIN asistente.conversaciones c ON m.conversacion_id = c.id
GROUP BY DATE(m.created_at)
ORDER BY fecha DESC;

-- ============================================================================
-- FUNCIONES UTILES
-- ============================================================================

-- Funcion: Actualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION asistente.fn_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger a tablas con updated_at
DROP TRIGGER IF EXISTS trg_conversaciones_updated ON asistente.conversaciones;
CREATE TRIGGER trg_conversaciones_updated
    BEFORE UPDATE ON asistente.conversaciones
    FOR EACH ROW EXECUTE FUNCTION asistente.fn_update_timestamp();

DROP TRIGGER IF EXISTS trg_memoria_updated ON asistente.memoria_usuario;
CREATE TRIGGER trg_memoria_updated
    BEFORE UPDATE ON asistente.memoria_usuario
    FOR EACH ROW EXECUTE FUNCTION asistente.fn_update_timestamp();

DROP TRIGGER IF EXISTS trg_documentacion_updated ON asistente.documentacion_sistema;
CREATE TRIGGER trg_documentacion_updated
    BEFORE UPDATE ON asistente.documentacion_sistema
    FOR EACH ROW EXECUTE FUNCTION asistente.fn_update_timestamp();

DROP TRIGGER IF EXISTS trg_triggers_updated ON asistente.triggers_proactivos;
CREATE TRIGGER trg_triggers_updated
    BEFORE UPDATE ON asistente.triggers_proactivos
    FOR EACH ROW EXECUTE FUNCTION asistente.fn_update_timestamp();

-- Funcion: Expirar acciones pendientes
CREATE OR REPLACE FUNCTION asistente.fn_expirar_acciones()
RETURNS INTEGER AS $$
DECLARE
    filas_afectadas INTEGER;
BEGIN
    UPDATE asistente.acciones_pendientes
    SET estado = 'expirada'
    WHERE estado = 'pendiente' AND expires_at < NOW();

    GET DIAGNOSTICS filas_afectadas = ROW_COUNT;
    RETURN filas_afectadas;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION asistente.fn_expirar_acciones IS 'Expira acciones pendientes que superaron el tiempo limite';

-- Funcion: Obtener historial de conversacion para contexto LLM
CREATE OR REPLACE FUNCTION asistente.fn_obtener_historial(
    p_conversacion_id UUID,
    p_limite INTEGER DEFAULT 20
)
RETURNS TABLE (
    rol VARCHAR(20),
    contenido TEXT,
    tool_calls JSONB,
    tool_call_id VARCHAR(100),
    tool_name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.rol,
        m.contenido,
        m.tool_calls,
        m.tool_call_id,
        m.tool_name,
        m.created_at
    FROM asistente.mensajes m
    WHERE m.conversacion_id = p_conversacion_id
    ORDER BY m.created_at DESC
    LIMIT p_limite;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION asistente.fn_obtener_historial IS 'Obtiene el historial de mensajes de una conversacion para el contexto del LLM';

-- Funcion: Buscar en corpus unificado por similitud de embedding
CREATE OR REPLACE FUNCTION asistente.fn_buscar_corpus(
    p_embedding vector(384),
    p_origen VARCHAR(20) DEFAULT NULL,
    p_limite INTEGER DEFAULT 10
)
RETURNS TABLE (
    id TEXT,
    origen VARCHAR(20),
    contenido TEXT,
    metadata JSONB,
    similitud FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cu.id,
        cu.origen,
        cu.contenido,
        cu.metadata,
        1 - (cu.embedding <=> p_embedding) as similitud
    FROM asistente.corpus_unificado cu
    WHERE (p_origen IS NULL OR cu.origen = p_origen)
    ORDER BY cu.embedding <=> p_embedding
    LIMIT p_limite;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION asistente.fn_buscar_corpus IS 'Busca en el corpus unificado por similitud semantica';

-- Funcion: Contar notificaciones por trigger en la ultima hora
CREATE OR REPLACE FUNCTION asistente.fn_contar_notificaciones_recientes(
    p_trigger_codigo VARCHAR(50),
    p_user_id UUID DEFAULT NULL
)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(*)
        FROM asistente.notificaciones_enviadas
        WHERE trigger_codigo = p_trigger_codigo
        AND (p_user_id IS NULL OR user_id = p_user_id)
        AND created_at > NOW() - INTERVAL '1 hour'
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION asistente.fn_contar_notificaciones_recientes IS 'Cuenta notificaciones de un trigger en la ultima hora (para rate limiting)';

-- ============================================================================
-- DATOS INICIALES
-- ============================================================================

-- Insertar documentacion del sistema basica
INSERT INTO asistente.documentacion_sistema (tipo, ruta, titulo, contenido, tags) VALUES
    (
        'guia_uso',
        NULL,
        'Bienvenida al Asistente',
        'Soy el asistente del Sistema de Prefactibilidad Ambiental Minera. Puedo ayudarte a:

1. **Consultar normativa**: Pregunta sobre la Ley 19.300, DS 40, o cualquier aspecto del SEIA.
2. **Entender clasificaciones**: Te explico por que un proyecto se clasifica como DIA o EIA.
3. **Gestionar proyectos**: Puedo crear proyectos, ejecutar analisis, o mostrarte informacion.
4. **Buscar precedentes**: Consulto proyectos similares aprobados en e-SEIA.

Solo pregunta lo que necesites. Para acciones que modifiquen datos, te pedire confirmacion antes de ejecutar.',
        ARRAY['bienvenida', 'ayuda', 'inicio']
    ),
    (
        'guia_uso',
        NULL,
        'Articulo 11 - Triggers EIA',
        'El Articulo 11 de la Ley 19.300 establece los criterios que determinan si un proyecto debe ingresar como EIA en lugar de DIA:

**Letra a)** Riesgo para la salud de la poblacion
**Letra b)** Efectos adversos sobre recursos naturales renovables (incluye glaciares)
**Letra c)** Reasentamiento de comunidades humanas
**Letra d)** Localizacion en o proxima a areas protegidas, sitios prioritarios o glaciares
**Letra e)** Alteracion significativa del patrimonio cultural
**Letra f)** Alteracion significativa del valor paisajistico o turistico

Si un proyecto presenta cualquiera de estos efectos, debe ingresar obligatoriamente como EIA.',
        ARRAY['articulo_11', 'eia', 'dia', 'triggers', 'ley_19300']
    ),
    (
        'guia_uso',
        NULL,
        'Proceso de Analisis',
        'El sistema realiza el analisis de prefactibilidad en los siguientes pasos:

1. **Analisis GIS**: Verifica intersecciones con areas protegidas, glaciares, comunidades indigenas, etc.
2. **Evaluacion de Triggers**: Evalua cada letra del Art. 11 basado en los datos del proyecto y GIS.
3. **Motor de Reglas SEIA**: Aplica la matriz de decision ponderada para clasificar como DIA o EIA.
4. **Busqueda RAG**: Busca normativa relevante para fundamentar la clasificacion.
5. **Generacion de Informe**: El LLM genera un informe detallado con justificacion legal.

Puedes ejecutar un analisis rapido (sin LLM) o completo (con generacion de informe).',
        ARRAY['analisis', 'proceso', 'gis', 'rag', 'llm']
    )
ON CONFLICT DO NOTHING;

-- ============================================================================
-- COMENTARIOS FINALES
-- ============================================================================
COMMENT ON SCHEMA asistente IS 'Schema para el Asistente IA conversacional del sistema de prefactibilidad';
