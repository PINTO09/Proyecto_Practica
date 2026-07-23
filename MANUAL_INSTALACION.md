# Manual de Instalación — Sistema de Gestión Docente ULEAM

## Requisitos Previos

Antes de instalar el proyecto, asegúrese de tener instalados los siguientes programas:

### 1. Python 3.10 o superior
- Descargar desde: https://www.python.org/downloads/
- Durante la instalación, marque la casilla **"Add Python to PATH"**
- Verificar la instalación abriendo una terminal (CMD o PowerShell) y ejecutando:
  ```
  python --version
  ```

### 2. Git
- Descargar desde: https://git-scm.com/downloads
- Verificar la instalación:
  ```
  git --version
  ```

### 3. PostgreSQL
- Descargar desde: https://www.postgresql.org/download/windows/
- Durante la instalación, anote la contraseña que configure para el usuario `postgres`
- Verificar la instalación:
  ```
  psql --version
  ```

### 4. pgAdmin (opcional pero recomendado)
- Se instala junto con PostgreSQL
- Sirve para visualizar y gestionar las bases de datos

---

## Paso 1: Clonar el Repositorio

Abra una terminal (CMD o PowerShell) en la carpeta donde desea guardar el proyecto y ejecute:

```powershell
git clone https://github.com/PINTO09/Proyecto_Practica.git
cd Proyecto_Practica
```

---

## Paso 2: Crear el Entorno Virtual

El entorno virtual aísla las dependencias del proyecto para que no interfieran con otros programas de su computadora.

```powershell
python -m venv venv
.\venv\Scripts\activate
```

Después de ejecutar esto, verá que al inicio de la línea de la terminal aparece `(venv)`. Eso indica que el entorno virtual está activo.

---

## Paso 3: Instalar Dependencias

Con el entorno virtual activo, ejecute:

```powershell
pip install -r requirements.txt
```

Este comando instala automáticamente todas las librerías que necesita el proyecto (Django, psycopg2, pillow, python-decouple, etc.).

---

## Paso 4: Configurar el Archivo `.env`

Cree un archivo llamado `.env` en la carpeta raíz del proyecto (al mismo nivel que `manage.py`). Copie el siguiente contenido:

```ini
DEBUG=True
SECRET_KEY=django-insecure-clave-para-desarrollo
DB_NAME=gestion_docente
DB_USER=postgres
DB_PASSWORD=SuContraseñaDePostgreSQL
DB_HOST=localhost
DB_PORT=5432
```

**Importante:** Reemplace `SuContraseñaDePostgreSQL` con la contraseña real que configuró al instalar PostgreSQL.

---

## Paso 5: Crear la Base de Datos

Abra una terminal o pgAdmin y cree la base de datos:

**Opción A — Desde la terminal:**
```powershell
psql -U postgres -c "CREATE DATABASE gestion_docente;"
```

**Opción B — Desde pgAdmin:**
1. Abra pgAdmin
2. Haga clic derecho sobre "Databases" → "Create" → "Database..."
3. Escriba `gestion_docente` como nombre
4. Haga clic en "Save"

---

## Paso 6: Ejecutar las Migraciones

Con el entorno virtual activo y la base de datos creada, ejecute:

```powershell
python manage.py migrate
```

Este comando crea todas las tablas necesarias en la base de datos.

---

## Paso 7: Crear un Usuario de Prueba

Ejecute el siguiente comando para crear un usuario administrador:

```powershell
python manage.py create_demo_user --cedula 1712345678 --password 12345678 --superuser
```

Esto creará un usuario con:
- **Cédula:** `1712345678`
- **Contraseña:** `12345678`
- **Rol:** Superusuario (acceso total)

Para crear usuarios con otros roles:
```powershell
python manage.py create_demo_user --cedula 1799999999 --password 12345678 --group "Coordinador"
```

Roles disponibles: `Administrador`, `Autoridad`, `Coordinador`, `Usuario`, `Funcionario`

---

## Paso 8: Ejecutar el Servidor

```powershell
python manage.py runserver
```

Abra su navegador y vaya a:
```
http://127.0.0.1:8000/
```

---

## Resumen de Comandos

| Paso | Comando |
|------|---------|
| Clonar repositorio | `git clone https://github.com/PINTO09/Proyecto_Practica.git` |
| Entrar a la carpeta | `cd Proyecto_Practica` |
| Crear entorno virtual | `python -m venv venv` |
| Activar entorno virtual | `.\venv\Scripts\activate` |
| Instalar dependencias | `pip install -r requirements.txt` |
| Ejecutar migraciones | `python manage.py migrate` |
| Crear usuario admin | `python manage.py create_demo_user --cedula 1712345678 --password 12345678 --superuser` |
| Iniciar servidor | `python manage.py runserver` |

---

## Credenciales de Prueba

Una vez ejecutados todos los pasos, puede iniciar sesión con:

| Campo | Valor |
|-------|-------|
| Usuario (Cédula) | `1712345678` |
| Contraseña | `12345678` |

---

## Solución de Problemas

### Error: `No module named 'decouple'`
Verifique que el entorno virtual esté activo (debe ver `(venv)` al inicio de la línea) y que haya ejecutado `pip install -r requirements.txt`.

### Error: `could not connect to server`
Verifique que PostgreSQL esté ejecutándose. Puede verificar desde el Servicios de Windows o desde pgAdmin.

### Error: `database "gestion_docente" does not exist`
Cree la base de datos siguiendo el Paso 5.

### Error: `password authentication failed`
Verifique que la contraseña en el archivo `.env` sea la correcta.

### Las migraciones fallan
Asegúrese de que PostgreSQL esté corriendo y que la base de datos `gestion_docente` exista.

---

## Estructura del Proyecto

```
Proyecto_Practica/
├── core/                    # Módulo principal (login, dashboard, roles)
├── accounts/                # Backend de autenticación
├── docentes/                # Gestión de docentes
├── catalogos/               # Catálogos del sistema
├── planificacion/           # Planificación académica
├── curriculo/               # Currículo y asignaturas
├── reportes/                # Generación de reportes
├── restricciones/           # Restricciones horarias
├── seguridad/               # Auditoría y seguridad
├── gestion_docente/         # Configuración del proyecto Django
├── templates/               # Templates globales
├── staticfiles/             # Archivos estáticos
├── manage.py                # Script de administración de Django
├── requirements.txt         # Dependencias del proyecto
├── .env.example             # Plantilla de variables de entorno
└── schema_fcacc.sql         # Esquema de base de datos
```
