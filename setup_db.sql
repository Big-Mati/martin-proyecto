DROP DATABASE IF EXISTS analitica_tienda;

CREATE DATABASE IF NOT EXISTS analitica_tienda;
USE analitica_tienda;

-- ==========================================
-- A. TABLAS DE DIMENSIÓN
-- ==========================================

CREATE TABLE dim_zonas (
    id_zona INT AUTO_INCREMENT PRIMARY KEY,
    nombre_zona VARCHAR(100) NOT NULL
);

-- INSERCIÓN DE DATOS MAESTROS (ZONAS)
INSERT INTO dim_zonas (id_zona, nombre_zona) VALUES 
(1, 'Gaming'), 
(2, 'Chilled Beverages');

CREATE TABLE dim_productos (
    id_producto INT AUTO_INCREMENT PRIMARY KEY,
    nombre_producto VARCHAR(150) NOT NULL,
    categoria VARCHAR(100),
    precio DECIMAL(10, 2) NOT NULL
);

-- INSERCIÓN DE DATOS MAESTROS (PRODUCTOS)
INSERT INTO dim_productos (nombre_producto, categoria, precio) VALUES 
('Mochila Urbana', 'Accesorios', 45.99),
('Cuaderno Universitario', 'Papelería', 5.50),
('Refresquera Térmica', 'Accesorios', 15.00),
('Celular Smartphone X', 'Electrónica', 899.99);

CREATE TABLE dim_empleados (
    id_empleado INT AUTO_INCREMENT PRIMARY KEY,
    nombre_vendedor VARCHAR(150) NOT NULL,
    rol VARCHAR(100),
    ruta_foto_facial VARCHAR(255)
);

-- ==========================================
-- B. TABLAS DE ENTIDAD Y PERFIL
-- ==========================================

CREATE TABLE fact_visitas_ia (
    id_visita INT AUTO_INCREMENT PRIMARY KEY,
    track_id VARCHAR(100) NOT NULL,
    genero VARCHAR(20),
    edad_estimada INT,
    emocion_dominante VARCHAR(50),
    es_empleado BOOLEAN DEFAULT FALSE,
    id_empleado_detectado INT NULL,
    FOREIGN KEY (id_empleado_detectado) REFERENCES dim_empleados(id_empleado)
);

-- ==========================================
-- C. TABLAS DE EVENTOS Y LÍNEA DE TIEMPO
-- ==========================================

CREATE TABLE fact_movimientos_ia (
    id_movimiento INT AUTO_INCREMENT PRIMARY KEY,
    id_visita INT NOT NULL,
    id_zona INT NOT NULL,
    fecha_ingreso DATETIME NOT NULL,
    fecha_salida DATETIME NULL, -- NULL temporalmente hasta que la persona salga de la zona
    FOREIGN KEY (id_visita) REFERENCES fact_visitas_ia(id_visita),
    FOREIGN KEY (id_zona) REFERENCES dim_zonas(id_zona)
);

CREATE TABLE fact_interacciones_ia (
    id_interaccion INT AUTO_INCREMENT PRIMARY KEY,
    id_visita INT NOT NULL,
    id_producto INT NOT NULL,
    tipo_accion VARCHAR(50), 
    emocion_detectada VARCHAR(50),
    fecha_hora DATETIME NOT NULL,
    FOREIGN KEY (id_visita) REFERENCES fact_visitas_ia(id_visita),
    FOREIGN KEY (id_producto) REFERENCES dim_productos(id_producto)
);

CREATE TABLE fact_ventas (
    id_ticket INT AUTO_INCREMENT PRIMARY KEY,
    id_producto INT NOT NULL,
    cantidad INT NOT NULL,
    total_pagado DECIMAL(10, 2) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    FOREIGN KEY (id_producto) REFERENCES dim_productos(id_producto)
);

ALTER TABLE fact_visitas_ia ADD COLUMN vector_facial MEDIUMTEXT;
ALTER TABLE fact_visitas_ia ADD COLUMN fecha_visita DATETIME DEFAULT CURRENT_TIMESTAMP;

-- ==========================================
-- D. VISTAS PARA DASHBOARD
-- ==========================================
CREATE VIEW vw_metricas_dashboard AS
SELECT 
    v.track_id,
    v.genero,
    v.edad_estimada,
    v.emocion_dominante,
    m.id_zona,
    z.nombre_zona,
    m.fecha_ingreso,
    m.fecha_salida,
    TIMESTAMPDIFF(SECOND, m.fecha_ingreso, IFNULL(m.fecha_salida, CURRENT_TIMESTAMP)) AS dwell_time_segundos
FROM fact_visitas_ia v
JOIN fact_movimientos_ia m ON v.id_visita = m.id_visita
JOIN dim_zonas z ON m.id_zona = z.id_zona
WHERE v.es_empleado = FALSE;