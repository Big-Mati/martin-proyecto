# 📚 Documentación Completa, Explícita y Detallada: Sistema de Analítica Retail y Señalización Digital IA

Esta documentación ha sido elaborada de manera exhaustiva para abarcar absolutamente todas las aristas del proyecto. Está estructurada en tres secciones fundamentales:
1. **Sección de Negocio y Gerencia:** Explicación del valor comercial, casos de uso y cumplimiento legal.
2. **Manual de Usuario:** Guía paso a paso sobre cómo leer e interpretar el Dashboard.
3. **Sección de Ingeniería y Desarrollo:** Arquitectura profunda, explicación de algoritmos, diccionarios de base de datos y solución de problemas.

---

## 🏢 Parte 1: Resumen Ejecutivo y Valor de Negocio

### 🌟 1.1 ¿Qué es este sistema y cuál es su propósito?
El **Sistema de Analítica Retail IA** es una plataforma de software avanzado que transforma las cámaras de seguridad estándar de una tienda física en sensores inteligentes de datos. Inspirado en plataformas de vanguardia mundial como *DISPL*, este sistema aplica algoritmos de Visión Computacional e Inteligencia Artificial (Machine Learning) para entender exactamente cómo interactúan los clientes con el espacio físico.

Su propósito central es **cerrar la brecha analítica entre el comercio electrónico y el comercio físico**. Mientras que una tienda online sabe exactamente cuántos clics da un usuario, cuánto tiempo ve un producto y en qué punto abandona el carrito, la tienda física tradicional opera a ciegas. Este sistema le otorga a la tienda física métricas del nivel del e-commerce.

### ⚖️ 1.2 Privacidad y Cumplimiento Legal (GDPR / EU AI Act)
Es de suma importancia para la gerencia entender que este sistema es **100% anónimo por diseño**. 
- **No se guardan fotografías ni videos de las personas.**
- La inteligencia artificial extrae las características del rostro en tiempo real y las convierte en un **Vector Matemático (Embedding Facial)**. Este vector es una lista irreversible de números.
- Una vez extraído el género y la edad estimada, la imagen se descarta de la memoria de la computadora en milisegundos.
- Esto hace que el sistema cumpla con normativas estrictas de protección de datos como la **GDPR (Reglamento General de Protección de Datos de Europa)** y actúe de manera ética sin infringir la privacidad de los consumidores.

### 🚀 1.3 Casos de Uso y Retorno de Inversión (ROI)
- **Marketing y Merchandising (Optimización de vitrinas):** Si el Dashboard muestra que la zona "Gaming" tiene un alto número de visitantes, pero un *Dwell Time* (tiempo de permanencia) menor a 5 segundos, significa que la exhibición atrae, pero no retiene. Marketing debe cambiar la presentación.
- **Recursos Humanos (Staffing Inteligente):** Al conocer los picos exactos de afluencia por hora, el gerente de tienda puede programar los horarios de los empleados de atención al cliente para que coincidan con las horas de mayor tráfico, mejorando la conversión de ventas.
- **Prevención de Pérdidas (Seguridad):** El sistema puede detectar automáticamente si las personas ingresan con mochilas grandes o bolsos a zonas restringidas de la tienda.
- **Medición de Campañas:** Si se lanza una campaña orientada a mujeres de 20 a 30 años, el sistema medirá exactamente si el tráfico en tienda ese día corresponde a ese segmento demográfico.

---

## 📊 Parte 2: Manual de Usuario del Dashboard Gerencial

El panel de control (Dashboard) está diseñado para ser consultado en cualquier momento por el gerente de turno. Se actualiza en tiempo real. A continuación, se detalla cómo interpretar cada métrica:

### 🚪 2.1 Flujo de Puerta (Entradas y Salidas)
Esta sección contabiliza cada vez que una persona cruza físicamente la línea de entrada/salida de la tienda.
- **Entradas hoy:** Total acumulado de personas que han ingresado desde las 00:00 horas.
- **Salidas hoy:** Total de personas que han salido.
- **En tienda ahora:** Es la resta matemática entre entradas y salidas. Indica el volumen exacto de personas en el local.
- **Flujo por hora (Gráfico de barras):** Muestra los picos de entrada y salida separados por horas del día. Útil para planificar horarios de empleados.

### 👥 2.2 Indicadores de Afluencia (KPIs Generales)
- **Visitantes únicos:** Cantidad de personas distintas (contando agrupaciones inteligentes gracias al motor de Re-Identificación).
- **Dwell Time promedio:** El promedio global de cuántos segundos pasa una persona dentro del alcance de la cámara.
- **En grupo (est.):** Porcentaje estimado de personas que visitaron la tienda acompañadas (familia o amigos), calculado si entran al cuadro de visión en el mismo minuto.
- **Zona más visitada:** El área de la tienda con más tráfico histórico acumulado.

### 📈 2.3 Perfiles Demográficos & Tráfico
- **Gender & Age (Barras cruzadas):** Agrupa a los clientes en bloques de edad (<20, 20-29, 30-45, >45) y los divide por género. Permite saber cuál es el cliente ideal (*Buyer Persona*) real de la tienda.
- **Engaged Visitors (Gráfico Circular - Pie):** Segmenta a los visitantes según su tiempo de permanencia. Un cliente de "< 5s" es alguien de paso o desinteresado. Un cliente de "> 15s" es un prospecto altamente enganchado (Engaged).
- **Afluencia por hora (Gráfico de área):** Muestra el volumen histórico de personas detectadas, para observar tendencias de horarios "pico" y horarios "valle".

### 🎯 2.4 Engagement y Emociones
- **Emociones dominantes:** Analiza las micro-expresiones de los clientes. Si hay un porcentaje muy alto de "Sad" (Tristeza) o "Angry" (Enojo), puede haber problemas con largas filas de espera o falta de atención en piso.
- **Dwell Time por Zona (Barras horizontales):** Permite comparar rápidamente qué pasillo o estante retiene más tiempo la atención.

### 📦 2.5 Objetos Detectados
- Muestra una lista y conteo histórico de objetos (Bolsos, mochilas, celulares, laptops, botellas) y en qué zona se detectaron, cruzado con el nivel de seguridad (confianza) de la Inteligencia Artificial.

---

## 💻 Parte 3: Documentación Técnica y de Ingeniería

### 🏗️ 3.1 Arquitectura del Sistema (Diagrama de Flujo de Datos)
El sistema opera bajo una arquitectura de canalización de datos (Data Pipeline) en tiempo real:

1. **Captura IoT:** `OpenCV` toma la transmisión en vivo de la cámara frame por frame.
2. **Inferencia Primaria (YOLOv8s):** El modelo detecta a las personas y a los objetos. Al mismo tiempo, el tracker **BoT-SORT** asocia un ID matemático (ej. ID #5) al movimiento del cuerpo.
3. **Crops y Extracción Facial:** Cuando se detecta una persona nueva, se hace un recorte (`crop`) de la imagen de su cuerpo y se pasa por **MediaPipe** (para encontrar la ubicación exacta del rostro).
4. **Análisis Demográfico y Re-ID (DeepFace):** En un hilo secundario (`ThreadPoolExecutor`), se ejecuta el análisis para sacar edad, género, emoción y el **Embedding de 128/512 dimensiones**.
5. **Geofencing:** Evaluaciones matemáticas simples comprueban si las coordenadas de los pies de la persona cruzan una línea (Trip-wire) o entran en un polígono de zona.
6. **Persistencia SQL:** Todo se guarda de inmediato en bases de datos a través de hilos seguros usando el módulo `mysql.connector`.
7. **Visualización Frontend:** `Streamlit` consulta la base de datos de forma asíncrona cada 5 segundos para actualizar los gráficos.

### 🧠 3.2 El Motor de IA (`main.py`) a Profundidad

#### Detección Asíncrona (Subprocesamiento)
El análisis facial es la tarea computacional más pesada. Si se hiciera en el hilo principal de la cámara, el video se congelaría (lag). Por ello, se usa la librería `concurrent.futures.ThreadPoolExecutor`. 
Cuando una persona es detectada, el sistema despacha la imagen a un hilo en segundo plano (background worker). El sistema principal sigue corriendo y dibujando las cajas delimitadoras. Una vez que el hilo termina su cálculo (después de 0.5 a 1.5 segundos), devuelve los datos (Edad: 24, Emoción: Feliz) y se adhieren a la metadata del `track_id` en vivo.

#### Re-Identificación (Re-ID) Activa
Problema: Una persona sale por la derecha de la cámara y vuelve a entrar por la izquierda 1 minuto después. BoT-SORT le dará un ID nuevo. 
Solución del sistema:
- Se tiene una `reid_gallery` (Lista en memoria RAM).
- Cuando entra un "nuevo" ID, el hilo de DeepFace saca su huella dactilar facial (Embedding).
- Antes de ingresarlo a la Base de Datos como alguien nuevo, se compara con la galería usando matemática de tensores (Similitud del Coseno: `cosine_d`).
- Si la similitud supera el umbral (`REID_THR = 0.45`), el sistema se da cuenta que es la misma persona, descarta el ID nuevo, le devuelve su ID original y el "Dwell Time" sigue sumando sin interrupciones.

#### Trip-Wire Mejorado
La línea de puerta evalúa la coordenada `y2` (La base de la caja delimitadora, es decir, los pies de la persona). La lógica almacena el `prev_cy` (posición Y anterior). 
- Si `prev_cy` estaba arriba de la línea y ahora está abajo, es Salida.
- Posee un mecanismo de "Cooldown" (`DOOR_COOLDOWN = 3.0`) para evitar que si una persona se queda bailando encima de la línea, genere 50 eventos de entrada/salida falsos.

### 🗄️ 3.3 Diccionario de Base de Datos (`analitica_tienda`)

#### Tablas Dimensionales (Catálogos estáticos)
- **`dim_zonas`**: `id_zona` (PK), `nombre_zona` (Gaming, Chilled).
- **`dim_empleados`**: Preparado para el futuro, para que el sistema ignore a los empleados del piso y no contamine las métricas de clientes.
- **`dim_productos`**: Catálogo de productos interactivos de la tienda.

#### Tablas de Hechos (Datos Transaccionales)
- **`fact_visitas_ia`**:
  - `track_id`: ID único generado por uuid.
  - `genero`, `edad_estimada`, `emocion_dominante`: Actualizados por DeepFace.
- **`fact_movimientos_ia`**:
  - `id_visita` (FK), `id_zona` (FK).
  - `fecha_ingreso` / `fecha_salida`: Vitales para calcular la resta de tiempos y obtener el Dwell Time por cada pasillo.
- **`fact_entradas_salidas`**:
  - `track_id` (FK lógico), `tipo` (ENUM: ENTRADA/SALIDA). Usada puramente para contar flujo de tienda.
- **`fact_objetos_detectados`**:
  - `clase_objeto` (String), `confianza` (Porcentaje numérico), `zona_detectada`.

#### Vistas Analíticas
- **`vw_metricas_dashboard`**: Es el verdadero motor del dashboard. Une Visitas, Zonas y Movimientos usando SQL JOINs, y calcula al vuelo el `dwell_time_segundos` usando la función matemática `timestampdiff(SECOND, fecha_ingreso, fecha_salida)`.

### 🔧 3.4 Guía de Calibración y Ajustes de Instalación

#### Modificando las Zonas
En `main.py`, línea ~66 encontrarás:
```python
ZONAS = {
    "#1 Gaming": {"id_db": 1, "coords": (0, 0, 640, 720)},
    "#6 Chilled": {"id_db": 2, "coords": (640, 0, 1280, 720)},
}
```
Debes ajustar las coordenadas `(X_inicio, Y_inicio, X_fin, Y_fin)`. 
1. `(0,0)` es la esquina superior izquierda de la cámara.
2. `(1280, 720)` es la esquina inferior derecha.
3. Puedes agregar tantas zonas como tu Base de Datos (`dim_zonas`) tenga registradas.

### ⚠️ 3.5 Troubleshooting y Solución de Problemas Frecuentes

1. **Error: `Failed to open NBX hive` o la cámara no enciende.**
   - Causa: Problema de controladores de video en Windows.
   - Solución: Cambiar el índice en la GUI de cámara a otra webcam disponible, o cerrar software de terceros (OBS, Zoom) que pueda tener secuestrada la cámara.

2. **Error de conexión DB o Dashboard no actualiza los datos.**
   - Causa: XAMPP / MySQL está apagado.
   - Solución: Abrir XAMPP Control Panel y darle a "Start" en MySQL. Verificar que el puerto sea el 3306.

3. **Demasiado "Lag" o cuadros por segundo bajos (Bajo FPS).**
   - Causa: Procesador de bajo rendimiento intentando procesar muchos rostros simultáneamente.
   - Solución: Cambiar el modelo `yolov8s.pt` (Small) a `yolov8n.pt` (Nano) en la línea `modelo_yolo = YOLO("yolov8s.pt")`. El modelo Nano es mucho más ligero y corre sin problemas en CPU antiguas.

4. **El Dashboard muestra "Pandas only supports SQLAlchemy connectable...".**
   - Causa: Alerta de compatibilidad temporal en la nueva versión de pandas.
   - Solución: Es un Warning, no un error que bloquee el sistema. El sistema seguirá funcionando de manera normal. Se solucionará en futuras actualizaciones migrando las conexiones a SQLAlchemy en `dashboard.py`.

5. **El sistema detecta personas pero no calcula la edad ni la emoción (Dice "--").**
   - Causa: Iluminación deficiente. DeepFace requiere que el rostro esté iluminado y no en penumbras.
   - Solución: Mejorar la luz artificial en la tienda o cambiar el ángulo de la cámara (Evitar contraluz apuntando hacia ventanas).
