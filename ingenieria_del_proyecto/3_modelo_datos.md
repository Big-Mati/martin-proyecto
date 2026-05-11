# 3. Modelo de Datos

Para asegurar la persistencia en tiempo real, el rendimiento de las analíticas de Dashboard y permitir la exportación de métricas sin bloqueo transaccional, la base de datos MySQL (`analitica_tienda`) ha sido diseñada empleando un esquema **Dimensional** (estrella/copo de nieve).

Este diseño separa los catálogos estáticos (Dimensiones) de los eventos de alta velocidad detectados por la Inteligencia Artificial (Hechos/Facts).

## 3.1 Tablas Dimensionales (Catálogos)
Estas tablas almacenan la estructura física del negocio y son estáticas.

* **`dim_zonas`:** 
  Almacena las diferentes áreas de calor establecidas sobre el video.
  - `id_zona` (PK, INT)
  - `nombre_zona` (VARCHAR): Ej. "Gaming", "Chilled", "Entrada".
* **`dim_empleados`:** 
  Catálogo en preparación para funcionalidades futuras donde la IA discrimine al personal del Staff para evitar que contaminen las métricas de clientes (Staff Exclusion).
  - `id_empleado` (PK, INT)
  - `nombre`, `rol`.
* **`dim_productos`:** 
  Inventario general referencial (opcional para el cruce futuro de ventas ERP vs Analítica IoT).
  - `id_producto` (PK, INT)
  - `nombre_producto`, `id_zona` (FK).

## 3.2 Tablas de Hechos (Transaccionales IoT)
Estas tablas reciben un gran volumen de ráfagas (inserts) provenientes de los hilos de ejecución concurrentes del motor IA (`main.py`).

* **`fact_visitas_ia`:**
  Guarda el "Perfil Maestro" de la persona detectada. Se crea una sola fila en el momento en que alguien entra al local.
  - `id_visita` (PK, INT)
  - `track_id` (VARCHAR): Identificador anónimo alfanumérico generado por YOLO.
  - `fecha_ingreso` (DATETIME): Timestamp automático de la base de datos.
  - `edad_estimada` (INT), `genero` (VARCHAR), `emocion_dominante` (VARCHAR): Estos campos se actualizan asíncronamente milisegundos después del insert, a medida que la red neuronal DeepFace retorna los resultados.

* **`fact_movimientos_ia`:**
  Captura el recorrido (customer journey) interno del usuario. Una misma visita puede tener múltiples movimientos.
  - `id_movimiento` (PK, INT)
  - `id_visita` (FK)
  - `id_zona` (FK)
  - `fecha_ingreso` (DATETIME)
  - `fecha_salida` (DATETIME): Vital para que el Dashboard pueda efectuar la diferencia de tiempo (Dwell Time).

* **`fact_interacciones_ia`:**
  Esta es la tabla clave de intersección espacial. Registra cuando una persona y un objeto se superponen en cámara, conectando al ERP con el comportamiento humano.
  - `id_interaccion` (PK, INT)
  - `id_visita` (FK) - Quién hizo la interacción.
  - `id_producto` (FK) - Qué producto del ERP (Mochila, Celular) fue tocado.
  - `emocion_detectada` (VARCHAR) - Su reacción al interactuar.
  - `fecha_hora` (DATETIME).

* **`fact_entradas_salidas`:**
  Tabla de contabilización estricta del Trip-Wire para medir picos de hora.
  - `id_evento` (PK, INT)
  - `track_id` (VARCHAR)
  - `tipo` (ENUM): "ENTRADA" o "SALIDA".
  - `fecha_hora` (DATETIME).

* **`fact_objetos_detectados`:**
  Captura eventos donde la IA detecta objetos de interés sobre o alrededor de los clientes.
  - `id_deteccion` (PK, INT)
  - `clase_objeto` (VARCHAR): Ej. mochila, botella, celular.
  - `confianza` (DECIMAL): Porcentaje de certeza de la red neuronal.
  - `zona_detectada` (VARCHAR), `fecha_hora` (DATETIME).

## 3.3 Vistas Analíticas (Views)
* **`vw_metricas_dashboard`:**
  El Dashboard (Streamlit) no ataca las tablas en bruto directamente para los cálculos complejos; consume esta vista SQL precalculada que aplica JOINs entre `fact_visitas_ia`, `dim_zonas` y `fact_movimientos_ia`. Esta vista utiliza la función interna `timestampdiff(SECOND, fecha_ingreso, fecha_salida)` para entregar el tiempo de permanencia (`dwell_time_segundos`) servido en bandeja para los mapas de calor gerenciales.
