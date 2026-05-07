# 🛒 Retail Analytics & Señalización Digital IA

Sistema avanzado de análisis de audiencia en tiempo real para tiendas físicas. Utiliza Visión Artificial (YOLOv8n + OpenCV) para detectar clientes, medir su tiempo de permanencia (*Dwell Time*) en zonas clave y estimar su perfil demográfico (edad, género, emociones) para optimizar el staff (RRHH) y realizar reportes gerenciales.

## 🚀 1. Requisitos Previos
- **Python 3.11 o 3.12** instalado en tu sistema.
- **XAMPP** o cualquier servidor local con **MySQL** (MariaDB) activo y corriendo en el puerto 3306.
- Una cámara web conectada al PC.

## ⚙️ 2. Despliegue de la Base de Datos
Antes de correr la Inteligencia Artificial, necesitas preparar la estructura de almacenamiento:
1. Abre tu administrador de base de datos (ej. **phpMyAdmin** en `http://localhost/phpmyadmin/`).
2. Importa o pega el contenido del archivo `setup_db.sql` incluido en la carpeta del proyecto.
3. *Nota:* Este script creará la base de datos `analitica_tienda`, construirá el Modelo Dimensional y poblará los datos maestros de Zonas y Productos por defecto.

## 🐍 3. Configuración del Entorno Virtual (Python)
Abre una terminal (PowerShell) en la carpeta raíz de tu proyecto y ejecuta los siguientes comandos en orden:

```powershell
# 1. Crear el entorno virtual
py -3.12 -m venv entorno_ia

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
streamlit run dashboard.py
```
> *Desplegará la interfaz gerencial en tu navegador por defecto para monitorear el Tráfico, Leads y recomendaciones de Staffing en vivo.*

---

## 💡 5. Consejos Prácticos y Configuración Avanzada

*   **Calibración de Zonas (Geofencing):** Las zonas interactivas están mapeadas por píxeles en pantalla. Si cambias de resolución de cámara, debes actualizar el diccionario `ZONAS` ubicado en las primeras líneas de `main.py` con las coordenadas `(X_inicio, Y_inicio, X_fin, Y_fin)` correctas que correspondan a tu estantería física.
*   **Ángulo Óptimo de Cámara:** Para lograr que YOLO identifique cuerpos enteros sin oclusiones severas, posiciona la cámara a unos 2.5 metros de altura apuntando hacia abajo en un ángulo de 30° a 45°.
*   **Iluminación para DeepFace:** Los análisis demográficos (Edad y Emoción) necesitan buena iluminación sobre el rostro de la persona. Evita montar la cámara apuntando directamente hacia una vitrina muy luminosa (contraluz).
*   **Demo de Grupos:** Para demostrarle al jurado la métrica de **"Visitas en Familia/Grupo"** del Dashboard, haz que dos personas distintas crucen la zona objetivo de la cámara dentro de un rango menor a 60 segundos. El algoritmo los agrupará estadísticamente.