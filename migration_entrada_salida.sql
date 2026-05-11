USE analitica_tienda;

CREATE TABLE IF NOT EXISTS fact_entradas_salidas (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    track_id    VARCHAR(100) NOT NULL,
    tipo        ENUM('ENTRADA','SALIDA') NOT NULL,
    fecha_hora  DATETIME DEFAULT CURRENT_TIMESTAMP,
    reid_match  BOOLEAN DEFAULT FALSE
);
