# Signalink API

API REST desarrollada en Python con Flask para dar servicio a la aplicación React Native de Signalink.

## Características

- ✅ API REST con Flask
- ✅ **Documentación Swagger/OpenAPI automática**
- ✅ Conexión a MySQL con stored procedures
- ✅ Autenticación de usuarios
- ✅ Registro de nuevos usuarios
- ✅ Validación de datos
- ✅ Configuración para Cloud Run
- ✅ CORS habilitado para React Native
- ✅ Hash de contraseñas con SHA256
- ✅ Variables de entorno para configuración
- ✅ **Sistema híbrido de transcripción con Whisper**
- ✅ WebSocket para tiempo real
- ✅ TTS (Text-to-Speech) con Hume AI

## 📚 Documentación Swagger

Una vez que la API esté ejecutándose, puedes acceder a la documentación interactiva en:

**🌐 http://localhost:8080/docs/**

La documentación Swagger incluye:

- 📖 Descripción detallada de todos los endpoints
- 🧪 Interfaz para probar la API directamente desde el navegador
- 📋 Esquemas de request y response
- 📝 Ejemplos de uso
- ⚡ Códigos de estado HTTP

## 🎙️ Sistema Híbrido de Transcripción Whisper

El proyecto incluye un sistema híbrido que permite alternar entre tu servicio personalizado de Whisper y OpenAI Whisper mediante variables de entorno.

### ⚙️ Configuración

En el archivo `.env`:

```env
# Para usar TU servicio personalizado (recomendado)
USE_CUSTOM_WHISPER=true
CUSTOM_WHISPER_URL=https://<tu-servicio-whisper>/transcribe

# Para usar OpenAI Whisper como alternativa
USE_CUSTOM_WHISPER=false
OPENAI_API_KEY=tu_api_key_de_openai
```

### 🔄 Funcionamiento

- **TU SERVICIO**: Rápido, GPU-powered, sin costos por uso
- **OPENAI**: Backup confiable cuando sea necesario
- **Switch automático**: Solo cambiar la variable `USE_CUSTOM_WHISPER`

### 📡 Comunicación

- **WebSocket**: Transmisión de audio en tiempo real
- **HTTP POST**: Envío a servicios de transcripción
- **SocketIO**: Respuestas asíncronas al frontend

## Estructura del Proyecto

```
python-api-project/
├── src/
│   ├── app.py                 # Aplicación principal Flask con Swagger
│   ├── schemas/               # Esquemas para validación y documentación
│   │   └── __init__.py        # Modelos Marshmallow
│   ├── config/
│   │   └── database.py        # Configuración de base de datos
│   ├── controllers/
│   │   └── auth_controller.py # Controlador de autenticación
│   ├── routes/
│   │   └── auth_routes.py     # Rutas con decoradores Swagger
│   ├── services/
│   │   └── auth_service.py    # Servicios de autenticación
│   └── utils/
│       └── validators.py      # Validadores de datos
├── database/
│   └── stored_procedures/
│       └── validate_user_credentials.sql
├── tests/
│   └── test_auth.py          # Tests unitarios
├── .env                      # Variables de entorno (NO incluido en Git)
├── .env.example             # Plantilla de variables de entorno
├── .gitignore               # Archivos excluidos del control de versiones
├── requirements.txt          # Dependencias Python
├── Dockerfile               # Para despliegue en Cloud Run
├── run.py                   # Archivo principal para ejecutar
├── debug_auth.py            # Script para debug de autenticación
└── test_api.py             # Script para probar la API
```

## Configuración de Base de Datos

### Información de conexión:

- **Host:** <DB_HOST>:3306
- **Usuario:** <DB_USER>
- **Contraseña:** <DB_PASSWORD>
- **Base de datos:** signalink

### Tabla de usuarios:

```sql
CREATE TABLE `user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(30) NOT NULL,
  `surname` varchar(30) NOT NULL,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `status` enum('active','inactive') DEFAULT 'active',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

### Stored Procedure requerido:

Ejecutar el archivo `database/stored_procedures/validate_user_credentials.sql` en MySQL.

## Instalación y Configuración

### 1. Instalar dependencias:

```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno:

```bash
cp .env.example .env
# Editar .env con tu configuración
```

### 2. Configurar variables de entorno:

En Windows (PowerShell):

```powershell
Copy-Item .env.example .env
# Editar .env con tu configuración
```

En Linux/Mac o en shells compatibles con Unix:

```bash
cp .env.example .env
# Editar .env con tu configuración
```

**⚠️ Importante:** El archivo `.env` contiene credenciales sensibles y está excluido del control de versiones por el `.gitignore`.

### 3. Ejecutar la API:

```bash
python run.py
```

O usar los scripts de conveniencia:

- **Windows:** `run.bat`
- **Linux/Mac:** `run.sh`

### 4. Probar la API:

```bash
python test_api.py
```

## Endpoints de la API

### Autenticación

#### POST /api/auth/login

Autenticar usuario existente.

**Body:**

```json
{
  "username": "string", // username o email
  "password": "string"
}
```

**Respuesta exitosa (200):**

```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": 1,
    "name": "Usuario"
  }
}
```

**Respuesta error (401):**

```json
{
  "error": "Invalid credentials"
}
```

#### POST /api/auth/register

Registrar nuevo usuario.

**Body:**

```json
{
  "name": "string",
  "surname": "string",
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Respuesta exitosa (201):**

```json
{
  "success": true,
  "message": "User created successfully",
  "user_id": 1
}
```

### Health Checks

#### GET /health

Estado general de la API y conexión a base de datos.

#### GET /api/auth/health

Estado del módulo de autenticación.

## Despliegue en Cloud Run

### 1. Construir imagen Docker:

```bash
docker build -t signalink-api .
```

### 2. Subir a Google Container Registry:

```bash
docker tag signalink-api gcr.io/[PROJECT-ID]/signalink-api
docker push gcr.io/[PROJECT-ID]/signalink-api
```

### 3. Desplegar en Cloud Run:

```bash
gcloud run deploy signalink-api \
  --image gcr.io/[PROJECT-ID]/signalink-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Testing

### Ejecutar tests unitarios:

```bash
python -m pytest tests/ -v
```

### Probar API manualmente:

```bash
python test_api.py
```

## Variables de Entorno

| Variable    | Descripción         | Valor por defecto    |
| ----------- | ------------------- | -------------------- |
| DB_HOST     | Host de MySQL       | <DB_HOST>      |
| DB_PORT     | Puerto de MySQL     | 3306                 |
| DB_USER     | Usuario de MySQL    | <DB_USER>        |
| DB_PASSWORD | Contraseña de MySQL | <DB_PASSWORD>            |
| DB_NAME     | Nombre de la base   | signalink            |
| SECRET_KEY  | Clave secreta Flask | your-secret-key-here |
| DEBUG       | Modo debug          | True                 |
| PORT        | Puerto de la API    | 8080                 |
| HOST        | Host de la API      | 0.0.0.0              |

## Tecnologías Utilizadas

- **Flask 2.3.3** - Framework web
- **Flask-CORS 4.0.0** - Soporte CORS
- **mysql-connector-python 8.1.0** - Driver MySQL
- **python-dotenv 1.0.0** - Variables de entorno
- **bcrypt 4.0.1** - Hash de contraseñas
- **PyJWT 2.8.0** - Tokens JWT
- **gunicorn 21.2.0** - Servidor WSGI para producción

## Desarrollo

### Estructura del código:

- **Controllers:** Manejan las requests HTTP
- **Services:** Lógica de negocio
- **Routes:** Definición de endpoints
- **Utils:** Utilidades y validadores
- **Config:** Configuración de la aplicación

### Convenciones:

- Usar snake_case para variables y funciones
- Documentar todas las funciones públicas
- Manejar errores apropiadamente
- Validar todos los inputs de usuario

### Control de versiones:

- El archivo `.gitignore` está configurado para excluir:
  - Archivos de configuración sensibles (`.env`)
  - Cache de Python (`__pycache__/`)
  - Archivos de entornos virtuales
  - Logs y archivos temporales
  - Archivos específicos de IDE

### Configuración Git:

```bash
git init
git add .
git commit -m "Initial commit: Signalink API with Swagger"
```

## Contacto

Para preguntas sobre el proyecto, contactar al equipo de desarrollo de Signalink.

## Setup Instructions

1. **Clone the repository:**

   ```
   git clone <repository-url>
   cd python-api-project
   ```

2. **Create a virtual environment:**

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**

   ```
   pip install -r requirements.txt
   ```

4. **Set up the database:**

   - Create a MySQL database and user.
   - Run the SQL script located in `database/migrations/create_users_table.sql` to create the necessary tables.
   - Add your database configuration to the `.env` file based on the `.env.example` template.

5. **Run the application:**
   ```
   python src/app.py
   ```

## Usage

- The API provides endpoints for user authentication and user management.
- Use tools like Postman or curl to interact with the API.

## Testing

- Unit tests are located in the `tests` directory.
- Run tests using:
  ```
  python -m unittest discover -s tests
  ```

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.
