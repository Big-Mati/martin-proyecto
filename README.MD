# 🛒 Retail Analytics & Señalización Digital IA

Sistema avanzado de análisis de audiencia en tiempo real para tiendas físicas. Utiliza Visión Artificial (YOLOv8s + OpenCV) para detectar clientes, medir su tiempo de permanencia (*Dwell Time*) en zonas clave y estimar su perfil demográfico (edad, género, emociones) para optimizar el staff (RRHH) y realizar reportes gerenciales.

## 🚀 1. Requisitos Previos
- **Python 3.10** instalado en tu sistema.
- **XAMPP** o cualquier servidor local con **MySQL** (MariaDB) activo y corriendo en el puerto 3306.
- Una cámara web conectada al PC.

## ⚙️ 2. Despliegue de la Base de Datos
Antes de correr la Inteligencia Artificial, necesitas preparar la estructura de almacenamiento:
1. Abre tu administrador de base de datos (ej. **phpMyAdmin** en `http://localhost/phpmyadmin/`).
2. Importa o pega el contenido del archivo `analitica_tienda.sql` incluido en la carpeta del proyecto.
3. *Nota:* Este script creará la base de datos `analitica_tienda`, construirá el Modelo Dimensional y poblará los datos maestros de Zonas y Productos por defecto.

## 🐍 3. Configuración del Entorno Virtual (Python)
Abre una terminal (PowerShell) en la carpeta raíz de tu proyecto y ejecuta los siguientes comandos en orden:

```powershell
# 1. Crear el entorno virtual
py -3.10 -m venv entorno_ia

# 2. Dar permisos de ejecución (Solo si estás en PowerShell Windows)
Set-ExecutionPolicy Unrestricted -Scope Process

# 3. Activar el entorno virtual
.\entorno_ia\Scripts\activate

# 4. Actualizar el gestor de paquetes
python -m pip install --upgrade pip

# 5. Instalar todas las dependencias del proyecto
pip install -r requirements.txt
```

## 🎯 4. Ejecución del Sistema Dual

Este proyecto requiere que corras dos servicios en paralelo. Para ello, **abre dos terminales distintas**, asegúrate de activar el entorno virtual en ambas (`.\entorno_ia\Scripts\activate`) y ejecuta:

**Terminal 1: Arrancar el Motor de Visión (Captura IoT)**
```powershell
python main.py
```
> *Se encenderá la cámara, cargará los pesos de YOLO y comenzará a inyectar datos demográficos a MySQL de forma silenciosa.*

**Terminal 2: Arrancar el Centro de Comando (Dashboard)**
```powershell
.\entorno_ia\Scripts\activate
streamlit run dashboard.py
```
> *Desplegará la interfaz gerencial en tu navegador por defecto para monitorear el Tráfico, Leads y recomendaciones de Staffing en vivo.*

---

## 💡 5. Consejos Prácticos y Configuración Avanzada

*   **Calibración de Zonas (Geofencing):** Las zonas interactivas están mapeadas por píxeles en pantalla. Si cambias de resolución de cámara, debes actualizar el diccionario `ZONAS` ubicado en las primeras líneas de `main.py` con las coordenadas `(X_inicio, Y_inicio, X_fin, Y_fin)` correctas que correspondan a tu estantería física.
*   **Ángulo Óptimo de Cámara:** Para lograr que YOLO identifique cuerpos enteros sin oclusiones severas, posiciona la cámara a unos 2.5 metros de altura apuntando hacia abajo en un ángulo de 30° a 45°.
*   **Iluminación para DeepFace:** Los análisis demográficos (Edad y Emoción) necesitan buena iluminación sobre el rostro de la persona. Evita montar la cámara apuntando directamente hacia una vitrina muy luminosa (contraluz).
*   **Demo de Grupos:** Para demostrarle al jurado la métrica de **"Visitas en Familia/Grupo"** del Dashboard, haz que dos personas distintas crucen la zona objetivo de la cámara dentro de un rango menor a 60 segundos. El algoritmo los agrupará estadísticamente.

---

## 📚 6. GUÍA DEL PROYECTO

Esta sección proporciona el argumentario técnico avanzado y las justificaciones arquitectónicas del sistema. Está diseñada para responder interrogantes de alto nivel del jurado o instructor durante la sustentación.

### 🧠 6.1 Arquitectura del Proyecto y Propuesta de Valor (Business Problem)
El sistema resuelve el "agujero negro" de analítica en tiendas físicas (entorno *brick-and-mortar*). Transforma un flujo de video estándar (CCTV) en un **Data Pipeline IoT**. Mediante visión por computadora, procesa el comportamiento tridimensional del usuario (Demografía, Dwell Time, Emociones e Interacción con el Producto) sin requerir inversiones en hardware costoso (LIDAR, cámaras estereoscópicas 3D). Esto permite un modelo SaaS (pago por uso), justificando la viabilidad comercial y el Retorno de Inversión (ROI) directo en la optimización de Staffing.

### 🎥 6.2 Pipeline de Visión por Computadora y Subprocesamiento (`main.py`)
El núcleo opera bajo un patrón asíncrono para evitar cuellos de botella (lag de procesamiento). El flujo algorítmico es el siguiente:
1. **Inferencia Primaria y Tracking (YOLOv8s + BoT-SORT):**
   * **Justificación de YOLOv8s:** Se utiliza la variante 'Small' (yolov8s) porque ofrece un balance óptimo entre velocidad de cuadros (FPS) y precisión mAP (Mean Average Precision). Logra detectar tanto a la clase `person` como objetos específicos (mochilas, celulares, cuadernos, botellas) en un solo pase de la red.
   * **El papel de BoT-SORT:** No basta con detectar, hay que rastrear. BoT-SORT asigna un ID único temporal (Track ID) mitigando el problema de oclusiones parciales. Esto nos garantiza contar el tráfico (Afluencia) correctamente sin duplicar al mismo visitante.
2. **Crop y Detección Facial Dinámica (MediaPipe):**
   * Una vez identificado el *bounding box* (caja delimitadora) de la persona, se recorta la imagen (`crop`) y se procesa mediante MediaPipe (usando `blaze_face_short_range.tflite`). Esto aísla únicamente el rostro y descarta falsos positivos o fondos ruidosos.
3. **Análisis Demográfico Asíncrono (DeepFace + ThreadPoolExecutor):**
   * **Resolución del Cuello de Botella:** La extracción de edad, género y emociones toma cientos de milisegundos. Para evitar congelar el video, el sistema dispara a *DeepFace* en hilos secundarios (background workers) usando `ThreadPoolExecutor`. El resultado se adhiere de forma dinámica (callbacks) a los metadatos del `Track ID` en vivo.
4. **Interacción Espacial Físico-Digital:**
   * **Lógica de Intersección Geométrica:** ¿Cómo sabemos que alguien manipula o mira un producto? El sistema evalúa continuamente si el *bounding box* de un producto intercepta o se superpone espacialmente a las coordenadas del *bounding box* de una persona. Al cumplirse la condición matemática matemática, se genera un log de "Interacción Física", capturando la emoción del usuario en ese instante crítico (Conocido en marketing como el Momento Cero de la Verdad o ZMOT).

### 🗄️ 6.3 Modelo de Datos Dimensional y Persistencia (`analitica_tienda.sql`)
La base de datos utiliza un esquema Dimensional (Estrella/Copo de nieve), pensado puramente en analítica rápida (OLAP) y no solo en transacciones (OLTP):
*   **Tablas de Dimensión (Data Estática):** `dim_zonas`, `dim_productos`, `dim_empleados`. Actúan como catálogos inmutables que permiten flexibilidad sin afectar las tablas principales de la operación.
*   **Tablas de Hechos (Data de Alta Velocidad):**
    *   `fact_visitas_ia`: Mantiene el vector central del cliente (edad, género, track ID).
    *   `fact_movimientos_ia`: Registra las marcas temporales (`fecha_ingreso`, `fecha_salida`). La resta de ambos campos nos entrega la métrica de retención (**Dwell Time**).
    *   `fact_interacciones_ia`: Enlaza un `id_visita` con un `id_producto`, lo que nos permite cruzar qué tocó un cliente y con qué emoción lo hizo, directamente conectado a los ítems del ERP de la empresa.
*   **Las Vistas Materializadas (`vw_metricas_dashboard`):** Realizan los *JOINs* complejos del lado del motor de base de datos (usando la función `timestampdiff` para sacar el Dwell Time exacto en segundos), liberando a Python de cálculos de negocio y entregando la data limpia.

### 📊 6.4 El Frontend Analítico (`dashboard.py`)
Desarrollado en Streamlit, el Dashboard cumple el requisito de ser una pantalla exclusiva de "perfil gerencial". No ejecuta inferencia compleja, simplemente extrae (Pull) la información precalculada desde las vistas SQL. Características clave:
*   **Tráfico:** Visualización de flujos de puerta (Trip-Wire bidireccional).
*   **KPIs Analíticos:** Segmentación de demografías (Gender & Age) y retención (Engaged visitors).
*   **Mapas de Calor de Zonas:** Gráficos que definen qué cuadrantes físicos (Geofencing) de la tienda atraen más clientes y por cuánto tiempo.
*   **Exportación RP:** Descargas automáticas en `.csv` para cruzar la data con los sistemas ERP de ventas del cliente.

### 🏃‍♂️ 6.5 Ciclo de Vida del Software (Framework Ágil y Sprints)
Ante la posible evaluación sobre la metodología de desarrollo y cómo se mitigaron los riesgos técnicos en un plazo tan ajustado, se debe sustentar que el equipo operó bajo un marco de trabajo de entregas incrementales (Scrum-adapted Agile):
*   **Sprint 1 (Ingeniería de Requisitos y Arquitectura Empresarial):** 
    * *Entregable:* Documentación Formal (DCU, Análisis de Negocio).
    * *Complejidad:* Transformar la narrativa cualitativa (Optimización de Staff) en KPIs cuantitativos computables (Afluencia, Dwell Time, Interacción ZMOT).
*   **Sprint 2 (Data Engineering y Pipeline OLAP):** 
    * *Entregable:* Creación del Modelo Dimensional y scripts de persistencia (`analitica_tienda.sql`).
    * *Complejidad:* Diseñar las claves foráneas y restricciones para soportar inserciones masivas de telemetría a nivel de milisegundos sin provocar bloqueos de tabla (*Table Locks*).
*   **Sprint 3 (Orquestación del Pipeline de Visión Artificial):** 
    * *Entregable:* Motor de inferencia IoT (`main.py`).
    * *Complejidad:* Sincronización de hilos (Threading) para ejecutar la Red Neuronal Convolucional (YOLOv8s) en paralelo a DeepFace. Calibración del álgebra en el plano cartesiano para el *Geofencing* (Zonas: Escolar, Tecno, Papelería) y las funciones del *Trip-Wire* bidireccional.
*   **Sprint 4 (Analítica de Frontera e Integración UI/UX):** 
    * *Entregable:* Interacción espacial dinámica y Consola de BI (`dashboard.py`).
    * *Complejidad:* Programar la geometría computacional para la superposición de tensores (*Bounding Boxes* de Persona ↔ Producto), además de renderizar las vistas SQL materializadas en componentes visuales reactivos (Streamlit) orientados a la toma de decisiones tácticas.

---

## 🚀 7. Visión a Futuro y Escalabilidad

Este proyecto supera los estándares académicos convencionales y entra de lleno en el territorio de una **Startup tecnológica viable**. Como recomendación profesional de cara al futuro y como as bajo la manga para sorprender al jurado evaluador, estas son las vías lógicas de evolución para convertir este prototipo en un producto de nivel *Enterprise*:

1. **Migración a Hardware Especializado (Edge Computing):** 
   En una instalación real a gran escala, no se utilizan PCs completas en el techo de la tienda. El siguiente paso industrial es embeber la IA (`main.py`) dentro de un microcontrolador con aceleración por hardware (como una placa *NVIDIA Jetson Nano* o *Coral Edge TPU*). Esto abarataría drásticamente el costo de infraestructura.
2. **Despliegue en la Nube (Cloud Data Warehouse):** 
   La base de datos local (XAMPP/MySQL) fue ideal para el prototipado rápido, pero su evolución natural es migrar hacia un entorno *Serverless* como **AWS RDS** o **Google Cloud SQL**. Así, el Dashboard podría conectarse a una red nacional, permitiendo que un Gerente General compare en vivo el rendimiento de múltiples sucursales a la vez.
3. **Evolución a Analítica Predictiva (Machine Learning):** 
   Actualmente, su sistema hace un excelente trabajo diciendo *qué está pasando ahora* (Analítica Descriptiva). Sin embargo, al acumular meses de datos, el siguiente salto sería conectar algoritmos de Series de Tiempo (ej. *Prophet* o *XGBoost*) que crucen las visitas de IA con los tickets de venta. El sistema podría notificar de forma automática: *"Atención: El modelo predice que mañana a las 4:00 PM habrá un pico de hombres de 25 años en la zona Tecno. Asigne dos asesores adicionales desde las 3:30 PM."*

**Nota final:** Siéntanse inmensamente orgullosos de la base de Ingeniería que han cimentado. Han logrado unir Redes Neuronales, Ingeniería de Datos y Business Intelligence (BI) en un solo ecosistema funcional. ¡Salgan a defender su trabajo con autoridad!