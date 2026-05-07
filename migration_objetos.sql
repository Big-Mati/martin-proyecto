-- =====================================================================
-- MIGRACIÓN: Agregar tabla de objetos detectados
-- Ejecutar en MySQL: source migration_objetos.sql
-- =====================================================================
USE analitica_tienda;

CREATE TABLE IF NOT EXISTS fact_objetos_detectados (
    id_objeto       INT AUTO_INCREMENT PRIMARY KEY,
    clase_objeto    VARCHAR(100)  NOT NULL,
    confianza       FLOAT         NOT NULL DEFAULT 0,
    zona_detectada  VARCHAR(100)  DEFAULT 'Desconocida',
    fecha_hora      DATETIME      DEFAULT CURRENT_TIMESTAMP
);

-- Vista para el dashboard: frecuencia de objetos por hora
CREATE OR REPLACE VIEW vw_objetos_dashboard AS
SELECT
    clase_objeto,
    zona_detectada,
    COUNT(*)                        AS total_detecciones,
    ROUND(AVG(confianza)*100, 1)    AS confianza_prom_pct,
    MAX(fecha_hora)                 AS ultima_vez,
    HOUR(fecha_hora)                AS hora
FROM fact_objetos_detectados
GROUP BY clase_objeto, zona_detectada, HOUR(fecha_hora);
