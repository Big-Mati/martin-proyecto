# 4. Implementación y Despliegue

La solución está desarrollada para ser desplegada bajo una arquitectura cliente/servidor (SaaS/Local) de doble componente: el Motor IoT de Inferencia y el Centro de Comando Gerencial.

## 4.1 Tecnologías y Requisitos Previos (Stack)
* **Lenguaje:** Python 3.11 o superior.
* **Inteligencia Artificial:** 
  * `ultralytics` (YOLOv8s) para Tracking de Personas y Objetos.
  * `mediapipe` y Haar Cascades para Detección Facial.
  * `deepface` (Facenet) para Análisis Demográfico y de Emociones.
* **Procesamiento de Video:** `opencv-python`.
* **Visualización Gerencial:** `streamlit`, `pandas`, `plotly`.
* **Persistencia:** Servidor local XAMPP con `MySQL`/MariaDB (`mysql-connector-python`).
* **Hardware Mínimo:** 
  * Cámara web USB estándar, Cámara IP RSTP o un CCTV genérico.
  * Procesador CPU intermedio (i5/i7) o Acelerador GPU si se despliega en Cloud.

## 4.2 Proceso de Despliegue en Entorno de Producción
La instalación del sistema se ejecuta bajo un proceso controlado de dependencias aisladas.

### Paso 1: Configuración de la Base de Datos
1. Asegurar que MySQL esté operativo (Puerto 3306).
2. Importar o ejecutar el script `analitica_tienda.sql` incluido en los archivos del proyecto. Este archivo contiene la definición DDL de las tablas, la vista de métricas y la inserción de zonas de muestra.

### Paso 2: Creación del Entorno Aislado
Para evitar conflictos de librerías en el servidor, se debe instanciar un entorno virtual nativo de Python:
```powershell
python -m venv entorno_ia
.\entorno_ia\Scripts\activate
pip install -r requirements.txt
```

### Paso 3: Calibración Física (Geofencing)
El área física de la tienda debe mapearse hacia el código. Dentro de `main.py`, se debe ubicar el diccionario `ZONAS` y actualizar las coordenadas lógicas `(X1, Y1, X2, Y2)` de acuerdo al tiro visual de la cámara en la sucursal.
*Ejemplo:* `"#1 Gaming": {"id_db": 1, "coords": (0, 0, 640, 720)}`

Asimismo, el algoritmo de entrada (Trip-Wire) evalúa una coordenada horizontal paramétrica (`DOOR_LINE_Y_PCT`), la cual por defecto representa el 75% del alto de la cámara, simulando la puerta principal.

### Paso 4: Puesta en Marcha (El Sistema Dual)
El entorno exige dos instancias concurrentes corriendo en paralelo:

1. **Terminal 1 - El Motor IA (`main.py`):**
   Activa la visión artificial, levanta los pesos pesados de la red neuronal y se queda en bucle perpetuo inyectando *Data Points* a MySQL en segundo plano usando subprocesos (`ThreadPoolExecutor`).
2. **Terminal 2 - El Dashboard (`dashboard.py`):**
   Levanta un servidor local web (`streamlit run dashboard.py`). Esta aplicación web asíncrona consulta MySQL periódicamente y sirve los gráficos analíticos, métricas y los archivos `.CSV` bajo demanda para que la Gerencia analice los resultados cada 72 horas.
