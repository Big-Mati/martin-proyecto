-- ============================================================
-- analitica_tienda
-- ============================================================

DROP DATABASE IF EXISTS `analitica_tienda`;

CREATE DATABASE IF NOT EXISTS `analitica_tienda`
 DEFAULT CHARACTER SET utf8mb4
 COLLATE utf8mb4_unicode_ci;

USE `analitica_tienda`;

-- ============================================================
-- 1. TABLAS DE DIMENSIÓN
-- ============================================================

CREATE TABLE IF NOT EXISTS `dim_zonas` (
 `id_zona`   int     NOT NULL AUTO_INCREMENT PRIMARY KEY,
 `nombre_zona` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dim_productos` (
 `id_producto`   int      NOT NULL AUTO_INCREMENT PRIMARY KEY,
 `nombre_producto` varchar(150)  NOT NULL,
 `categoria`    varchar(100)  DEFAULT NULL,
 `precio`      decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `dim_empleados` (
 `id_empleado`   int     NOT NULL AUTO_INCREMENT PRIMARY KEY,
 `nombre_vendedor` varchar(150) NOT NULL,
 `rol`       varchar(100) DEFAULT NULL,
 `ruta_foto_facial` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 2. TABLA DE ENTIDAD PRINCIPAL (debe crearse antes que las fact_*)
-- ============================================================

CREATE TABLE IF NOT EXISTS `fact_visitas_ia` (
 `id_visita`       int     NOT NULL AUTO_INCREMENT PRIMARY KEY,
 `track_id`        varchar(100) NOT NULL,
 `genero`         varchar(20) DEFAULT NULL,
 `edad_estimada`     int     DEFAULT NULL,
 `emocion_dominante`   varchar(50) DEFAULT NULL,
 `es_empleado`      tinyint(1)  DEFAULT 0,
 `id_empleado_detectado` int     DEFAULT NULL,
 `vector_facial`     mediumtext,
 `fecha_visita`      datetime   DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT `fk_visita_empleado`
  FOREIGN KEY (`id_empleado_detectado`) REFERENCES `dim_empleados`(`id_empleado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 3. TABLAS DE EVENTOS (todas conectadas a fact_visitas_ia)
-- ============================================================

CREATE TABLE IF NOT EXISTS `fact_movimientos_ia` (
 `id_movimiento` int    NOT NULL AUTO_INCREMENT PRIMARY KEY,
 `id_visita`   int    NOT NULL,
 `id_zona`    int    NOT NULL,
 `fecha_ingreso` datetime NOT NULL,
 `fecha_salida`  datetime DEFAULT NULL,
 CONSTRAINT `fk_movimiento_visita`
  FOREIGN KEY (`id_visita`) REFERENCES `fact_visitas_ia`(`id_visita`),
 CONSTRAINT `fk_movimiento_zona`
  FOREIGN KEY (`id_zona`)  REFERENCES `dim_zonas`(`id_zona`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `fact_interacciones_ia` (
 `id_interaccion`  int     NOT NULL AUTO_INCREMENT PRIMARY KEY,
 `id_visita`     int     NOT NULL,
 `id_producto`    int     NOT NULL,
 `tipo_accion`    varchar(50) DEFAULT NULL,
 `emocion_detectada` varchar(50) DEFAULT NULL,
 `fecha_hora`    datetime   NOT NULL,
 CONSTRAINT `fk_interaccion_visita`
  FOREIGN KEY (`id_visita`)  REFERENCES `fact_visitas_ia`(`id_visita`),
 CONSTRAINT `fk_interaccion_producto`
  FOREIGN KEY (`id_producto`) REFERENCES `dim_productos`(`id_producto`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CORREGIDO: se agrega id_visita para conectar ventas al visitante
CREATE TABLE IF NOT EXISTS `fact_ventas` (
 `id_ticket`  int      NOT NULL AUTO_INCREMENT PRIMARY KEY,
 `id_visita`  int      DEFAULT NULL,  -- NULL si el POS no identifica al visitante
 `id_producto` int      NOT NULL,
 `cantidad`   int      NOT NULL,
 `total_pagado` decimal(10,2) NOT NULL,
 `fecha_hora`  datetime    NOT NULL,
 CONSTRAINT `fk_ventas_visita`
  FOREIGN KEY (`id_visita`)  REFERENCES `fact_visitas_ia`(`id_visita`),
 CONSTRAINT `fk_ventas_producto`
  FOREIGN KEY (`id_producto`) REFERENCES `dim_productos`(`id_producto`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CORREGIDO: se agrega id_visita para conectar entradas/salidas al visitante
CREATE TABLE IF NOT EXISTS `fact_entradas_salidas` (
 `id`     int      NOT NULL AUTO_INCREMENT PRIMARY KEY,
 `id_visita`  int      DEFAULT NULL,  -- NULL hasta que se resuelva el reid
 `track_id`  varchar(100) NOT NULL,
 `tipo`    enum('ENTRADA','SALIDA') NOT NULL,
 `fecha_hora` datetime   DEFAULT CURRENT_TIMESTAMP,
 `reid_match` tinyint(1)  DEFAULT 0,
 CONSTRAINT `fk_entsal_visita`
  FOREIGN KEY (`id_visita`) REFERENCES `fact_visitas_ia`(`id_visita`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- CORREGIDO: se agrega id_zona (FK) además del campo texto zona_detectada
CREATE TABLE IF NOT EXISTS `fact_objetos_detectados` (
 `id_objeto`   int      NOT NULL AUTO_INCREMENT PRIMARY KEY,
 `clase_objeto`  varchar(100) NOT NULL,
 `confianza`   float     NOT NULL DEFAULT 0,
 `id_zona`    int      DEFAULT NULL,  -- FK a dim_zonas
 `zona_detectada` varchar(100) DEFAULT 'Desconocida', -- conservado para compatibilidad
 `fecha_hora`   datetime   DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT `fk_objetos_zona`
  FOREIGN KEY (`id_zona`) REFERENCES `dim_zonas`(`id_zona`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 4. DATOS INICIALES
-- ============================================================

INSERT IGNORE INTO `dim_productos` (`id_producto`, `nombre_producto`, `categoria`, `precio`) VALUES
 (1, 'Mochila Escolar',  'Escolar',  45.00),
 (2, 'Celular Smartphone', 'Tecno',   250.00),
 (3, 'Refresco / Botella', 'Escolar',  1.50),
 (4, 'Cuaderno / Libro',  'Papelería', 3.00);

INSERT IGNORE INTO `dim_zonas` (`id_zona`, `nombre_zona`) VALUES
 (1, 'Escolar'),
 (2, 'Tecno'),
 (3, 'Papelería');

-- ============================================================
-- 5. VISTAS ANALÍTICAS PARA EL DASHBOARD
-- ============================================================

-- Vista principal: perfil del visitante + zona + tiempo de permanencia
CREATE OR REPLACE VIEW `vw_metricas_dashboard` AS
SELECT
 v.track_id,
 v.genero,
 v.edad_estimada,
 v.emocion_dominante,
 m.id_zona,
 z.nombre_zona,
 m.fecha_ingreso,
 m.fecha_salida,
 TIMESTAMPDIFF(SECOND, m.fecha_ingreso, IFNULL(m.fecha_salida, NOW())) AS dwell_time_segundos
FROM `fact_visitas_ia`  v
JOIN `fact_movimientos_ia` m ON v.id_visita = m.id_visita
JOIN `dim_zonas`      z ON m.id_zona  = z.id_zona
WHERE v.es_empleado = FALSE;

-- Vista de objetos detectados por zona y hora
CREATE OR REPLACE VIEW `vw_objetos_dashboard` AS
SELECT
 o.clase_objeto,
 IFNULL(z.nombre_zona, o.zona_detectada) AS zona_detectada, -- usa nombre real si hay FK
 COUNT(*)                AS total_detecciones,
 ROUND(AVG(o.confianza) * 100, 1)    AS confianza_prom_pct,
 MAX(o.fecha_hora)            AS ultima_vez,
 HOUR(o.fecha_hora)           AS hora
FROM `fact_objetos_detectados` o
LEFT JOIN `dim_zonas`      z ON o.id_zona = z.id_zona
GROUP BY
 o.clase_objeto,
 zona_detectada,
 HOUR(o.fecha_hora);

-- NUEVA Vista: ventas cruzadas con perfil del visitante
CREATE OR REPLACE VIEW `vw_ventas_con_perfil` AS
SELECT
 fv.id_ticket,
 fv.fecha_hora,
 p.nombre_producto,
 p.categoria,
 fv.cantidad,
 fv.total_pagado,
 v.track_id,
 v.genero,
 v.edad_estimada,
 v.emocion_dominante
FROM `fact_ventas`  fv
JOIN `dim_productos` p ON fv.id_producto = p.id_producto
LEFT JOIN `fact_visitas_ia` v ON fv.id_visita = v.id_visita;

-- ============================================================
-- ⚠️ NOTA: Se ha comentado la vista vw_flujo_visita debido a que
-- generaba un riesgo severo de "Producto Cartesiano" (Fan Trap).
-- Multiplicaría registros si un visitante tiene múltiples
-- interacciones, movimientos y ventas simultáneamente.
-- ============================================================
/*
-- NUEVA Vista: flujo completo entrada → zona → interacción → venta
CREATE OR REPLACE VIEW `vw_flujo_visita` AS
SELECT
 v.id_visita,
 v.track_id,
 v.genero,
 v.edad_estimada,
 es.tipo                  AS tipo_evento,
 es.fecha_hora               AS hora_evento,
 z.nombre_zona,
 m.fecha_ingreso,
 m.fecha_salida,
 TIMESTAMPDIFF(SECOND, m.fecha_ingreso,
  IFNULL(m.fecha_salida, NOW()))      AS segundos_en_zona,
 p.nombre_producto,
 i.tipo_accion,
 i.emocion_detectada,
 fven.total_pagado
FROM    `fact_visitas_ia`   v
LEFT JOIN `fact_entradas_salidas` es  ON v.id_visita = es.id_visita
LEFT JOIN `fact_movimientos_ia`  m  ON v.id_visita = m.id_visita
LEFT JOIN `dim_zonas`       z  ON m.id_zona  = z.id_zona
LEFT JOIN `fact_interacciones_ia` i  ON v.id_visita = i.id_visita
LEFT JOIN `dim_productos`     p  ON i.id_producto = p.id_producto
LEFT JOIN `fact_ventas`      fven ON v.id_visita = fven.id_visita
WHERE v.es_empleado = FALSE;
*/
