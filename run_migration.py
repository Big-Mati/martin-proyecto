import mysql.connector

con = mysql.connector.connect(
    host='localhost', database='analitica_tienda', user='root', password=''
)
cur = con.cursor()

sql1 = (
    "CREATE TABLE IF NOT EXISTS fact_objetos_detectados ("
    "id_objeto INT AUTO_INCREMENT PRIMARY KEY,"
    "clase_objeto VARCHAR(100) NOT NULL,"
    "confianza FLOAT NOT NULL DEFAULT 0,"
    "zona_detectada VARCHAR(100) DEFAULT 'Desconocida',"
    "fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP"
    ")"
)

sql2 = (
    "CREATE OR REPLACE VIEW vw_objetos_dashboard AS "
    "SELECT clase_objeto, zona_detectada, "
    "COUNT(*) AS total_detecciones, "
    "ROUND(AVG(confianza)*100,1) AS confianza_prom_pct, "
    "MAX(fecha_hora) AS ultima_vez, "
    "HOUR(fecha_hora) AS hora "
    "FROM fact_objetos_detectados "
    "GROUP BY clase_objeto, zona_detectada, HOUR(fecha_hora)"
)

cur.execute(sql1)
cur.execute(sql2)
con.commit()
print("OK: Tabla fact_objetos_detectados y vista creadas correctamente.")
con.close()
