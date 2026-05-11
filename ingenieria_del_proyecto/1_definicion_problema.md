# 1. Definición del Problema de Negocio y Casos de Uso

## 1.1 Narrativa del Problema de Negocio
Una compañía del sector retail enfrenta el desafío de no conocer a profundidad cómo interactúan sus clientes con el espacio físico de sus tiendas. Necesitan una **solución de sistemas que les permita optimizar el uso de sus Recursos Humanos (Staffing)** y mejorar la atención al cliente. 

Actualmente, operan a ciegas en términos de métricas clave que el *e-commerce* domina. El requerimiento de negocio es claro: pretenden desplegar una serie de cámaras estratégicas para monitorear el comportamiento de los clientes que entran y salen del local en un período de prueba de una semana. Las preguntas de negocio que necesitan responder son:
* ¿Cuál es la afluencia de público en la tienda (cuántos clientes ingresan)?
* ¿En qué horarios ocurren los picos de visitas?
* ¿Cuál es el perfil demográfico de estos clientes?
* ¿Los clientes llegan solos o acompañados en familia/grupo?
* ¿Cuánto tiempo permanecen en el negocio (por día y por hora)?
* ¿Cuánto tiempo le presta atención una persona a un producto o zona específica (mapas de calor)?
* ¿En qué puntos de la tienda se detienen los clientes cuando ingresan?

Esta información servirá para determinar si el nivel de atención ofrecido es el adecuado, si el cliente pide o requiere información, y para proyectar cómo una buena atención puede influir en *n* cantidad de ventas.

## 1.2 Alcances, Restricciones y Tiempos
* **Tiempo:** El objetivo de la empresa es que el desarrollo del sistema **no exceda los 3 meses**.
* **Infraestructura:** El negocio **no pretende invertir en hardware especializado** (como cámaras estereoscópicas 3D o servidores costosos). 
* **Modelo Financiero:** Se espera que el cliente acepte el pago por el uso del sistema como un servicio (SaaS / Licenciamiento), apalancándose en las cámaras de seguridad estándar (CCTV) que ya poseen o en cámaras IP genéricas.
* **Consumo de Información:** La información recopilada debe estar formateada específicamente para un **usuario de perfil gerencial**. Se entregará a través de una estructura de Dashboard seguro (con credenciales), el cual debe actualizarse y estar disponible para cortes de evaluación cada 72 horas (o en tiempo real), mostrando parámetros precisos de afluencia, tipo de cliente, mapas de calor, y retención por producto.

## 1.3 Casos de Uso (DCU)
1. **Gerencia de Tienda (Usuario de Negocio):** Accede al Dashboard gerencial para consultar las métricas de afluencia, observar los mapas de calor, conocer las demografías (edad/género), descargar los reportes consolidados en CSV, y ajustar la rotación de su personal de piso (Staffing) en base a los datos.
2. **Sistema Automatizado IA (Actor Inteligente):** Monitorea el comportamiento del cliente a través del hardware disponible, extrae las métricas (género, edad, emociones, tiempo de permanencia), clasifica los eventos (entrada/salida, acompañantes) y envía de forma ininterrumpida estos datos hacia la base de datos analítica.
