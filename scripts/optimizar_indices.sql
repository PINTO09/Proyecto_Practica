-- ============================================================
-- Índices recomendados para fcacc_academica (PostgreSQL)
-- Ejecutar como superusuario o con permisos CREATE INDEX.
-- Usar CONCURRENTLY para evitar bloqueos en producción.
-- ============================================================

-- planificacion_asignacion_docente
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asignacion_docente_periodo ON planificacion_asignacion_docente (id_periodo);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asignacion_docente_carrera ON planificacion_asignacion_docente (id_carrera);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_asignacion_docente_asignatura ON planificacion_asignacion_docente (id_asignatura);

-- planificacion_reparto_horas
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reparto_horas_periodo ON planificacion_reparto_horas (id_periodo);

-- planificacion_matriz_f4
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_matriz_f4_periodo ON planificacion_matriz_f4 (id_periodo);

-- planificacion_demanda_academica
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_demanda_periodo ON planificacion_demanda_academica (id_periodo);

-- auditoria_registro_cambios
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auditoria_fecha ON auditoria_registro_cambios (fecha_hora_cambio DESC);

-- historial_limitacion
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_historial_limitacion_docente ON historial_limitacion (id_docente);
