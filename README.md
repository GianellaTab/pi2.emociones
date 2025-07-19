# PI2 Emociones

## Descripción

PI2 Emociones es una aplicación de escritorio para la detección y registro de emociones faciales en tiempo real, utilizando los modelos FER y DeepFace. Permite:

- Detectar emociones básicas (feliz, tristeza, miedo, enojo, sorpresa, neutral, desprecio).
- Registrar los resultados (emociones y porcentaje) en una base de datos SQLite.
- Guardar imágenes de emociones negativas para su análisis.
- Generar reportes en Excel y enviarlos por correo electrónico cada intervalo configurado o a solicitud.
- Buscar y visualizar el historial de emociones por rango de fechas.
- Registrar nuevos rostros y reconocer personas usando embeddings de DeepFace.

## Características

- Interfaz gráfica principal con PyQt5 para la visualización de video y estadísticas.
- Panel de búsqueda y generación de reportes con Tkinter.
- Integración con SQLite para almacenamiento local.
- Generación automática de base de datos y tablas al primer arranque.
- Configuración de intervalos de reporte y lista de destinatarios.

## Requisitos

- **Python 3.10** o superior
- Cámara web o video (para pruebas)
- Las dependencias listadas en `requirements.txt`

## Instalación

1. Clona este repositorio:
   ```bash
   git clone <https://github.com/GianellaTab/pi2.emociones.git 
   cd pi2.emociones
   ```
2. Crea y activa un entorno virtual:
   - En Windows:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\activate
     ```
   - En macOS/Linux:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Configuración

- El primer arranque crea la base de datos `emociones.db` y la tabla de usuarios con credenciales por defecto:
  - **Usuario:** `admin`
  - **Contraseña:** `admin123`
- Para cambiar las credenciales de correo (envío de reportes), edita en `main.py` las variables `from_email`, `password` y `recipients`, o utiliza variables de entorno.

## Uso

Ejecuta la aplicación con:

```bash
python main.py
```

1. **Inicio de sesión:** ingresa con el usuario `admin`.
2. **Interfaz principal:**
   - Selecciona el modelo de detección (FER o DeepFace).
   - Haz clic en "Iniciar Detección" para arrancar la cámara.
   - Los resultados se muestran en tiempo real y se registran automáticamente.
   - Usa "Registrar Rostro" para capturar imágenes de un nuevo usuario y entrenar el reconocimiento.
   - Los botones "Enviar reporte diario" y los reportes automáticos cada intervalo enviarán un correo con Excel y un ZIP de imágenes.
   - "Buscar por Fecha" abre un diálogo para filtrar y exportar historiales.

## Estructura de carpetas

```
pi2.emociones/
├── .gitignore
├── .python-version
├── conductas.bat
├── emociones.db            # Base de datos SQLite
├── main.py                 # Script principal
├── requirements.txt        # Dependencias del proyecto
├── capturas_tristeza/      # Imágenes automáticas de tristeza
├── debug_faces/            # Capturas de depuración
├── emociones_negativas/    # Carpeta genérica de emociones negativas
├── rostros_registrados/    # Imágenes usadas para reconocimiento de personas
└── .venv/                  # Entorno virtual (no versionar)
```


