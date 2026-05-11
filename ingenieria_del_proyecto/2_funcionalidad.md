# 2. Funcionalidad del Sistema

El sistema "Retail Analytics IA" funciona como un motor inteligente dual: por un lado extrae los datos del espacio físico mediante Visión Computacional, y por el otro, renderiza dichos datos en un panel de gerencia interactivo.

## 2.1 Módulo de Detección e Inferencia IA (Visión Artificial)
El sistema captura la señal de video de las cámaras en tiempo real y ejecuta las siguientes funcionalidades clave, cumpliendo con regulaciones de privacidad (no guarda fotografías, solo vectores matemáticos):

* **Tracking de Personas (Flujo y Afluencia):** Utiliza un modelo de Inteligencia Artificial (YOLOv8) acoplado a un algoritmo de rastreo (BoT-SORT) que asocia un identificador único numérico (Track ID) al movimiento del cuerpo de cada cliente.
* **Línea de Puerta Virtual (Trip-Wire):** Mide dinámicamente si los píxeles de una persona cruzan una línea virtual establecida, lo que permite contabilizar con precisión matemática las Entradas y Salidas reales del establecimiento.
* **Extracción Demográfica y de Emociones:** Cuando el sistema detecta a un individuo nuevo, realiza un recorte (*crop*) hacia la zona del rostro usando algoritmos como MediaPipe. Este recorte se envía de manera asíncrona a un segundo motor de IA (DeepFace), el cual es capaz de estimar en milisegundos:
  * El **Género** de la persona (Male/Female).
  * La **Edad** aproximada.
  * La **Emoción Dominante** (Feliz, Neutral, Enojado, Triste).
* **Agrupación y Perfiles (Llegan solos o acompañados):** A través de marcas temporales (timestamps), el sistema puede realizar heurística para saber si grupos de personas ingresan de forma simultánea, estimando si son unidades familiares o visitantes individuales.
* **Geofencing y Dwell Time (Tiempo de Permanencia):** Divide la vista de la cámara en 3 zonas poligonales interactuables estratégicas ("Escolar", "Tecno", "Papelería"). El sistema cronometra el segundo exacto en que un individuo entra a la zona y el momento en que sale, calculando el *Dwell Time* (tiempo de retención).
* **Interacción Espacial Físico-Digital (Personas ↔ Objetos):** El sistema va un paso más allá de detectar mochilas o celulares. A través de algoritmos de intersección de *bounding boxes* (cajas delimitadoras), el sistema detecta si el recuadro de un objeto se superpone con el recuadro de una persona. Si esto ocurre, deduce una interacción física, captura la emoción de la persona en ese preciso milisegundo y lo registra en la base de datos.

## 2.2 Módulo de Analítica Gerencial (Dashboard)
El usuario gerencial consume estos datos a través de un Dashboard web en vivo, el cual le brinda las siguientes funcionalidades:

* **Panel de Flujo Activo:** Muestra el total de Entradas de Hoy, Salidas de Hoy, y el número preciso de clientes que están "En tienda ahora". 
* **KPIs Generales:** Visitantes únicos del día, Dwell Time Promedio global, Zona de mayor interés y Porcentaje de clientes en grupo.
* **Segmentación Gender & Age:** Gráficos de barras que cruzan los segmentos de edades (ej. 20-29, 30-45) con el género, para establecer el Perfil de Cliente de manera estadística.
* **Engaged Visitors:** Una métrica en forma de torta que segmenta a los visitantes en rangos según su nivel de permanencia (menor a 5 seg, mayor a 15 seg), demostrando el "enganche" con los productos.
* **Mapas y Zonas de Interés (Heatmaps lógicos):** Desglose del tiempo promedio de permanencia por zona para responder "¿En qué área se detienen más los clientes?".
* **Exportación de Datos Crudos:** Permite la descarga instantánea de las métricas puras a archivos `.CSV` para cruce de datos financieros (RP/ERP), con el fin de proyectar conversiones de ventas a nivel gerencial.
