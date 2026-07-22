# Proyecto_Practica
Proyecto grupal

## Ejecutar en la red local

Con el entorno virtual activo y desde la carpeta del proyecto:

```powershell
python manage.py migrate
python manage.py runlan
```

El comando muestra la dirección local del servidor y la dirección IP que deben
abrir los demás equipos conectados a la misma red, por ejemplo
`http://192.168.1.20:8000/`. Si Windows solicita permiso, se debe permitir el
acceso en redes privadas. `runlan` habilita los hosts y archivos estáticos solo
para este servidor de desarrollo, sin relajar la configuración de producción.

Para utilizar otro puerto:

```powershell
python manage.py runlan 8080
```

## Cargar los datos FCACC desde Excel

Los libros deben permanecer en `_excel_input/PLANIFICACION Copiar3`. Primero
se valida todo dentro de una transacción que se revierte:

```powershell
python manage.py migrate
python manage.py backup_fcacc_data --output backups/pre_importacion.json
python manage.py import_complete_fcacc --dry-run
```

Si la simulación termina sin errores, se ejecuta la carga definitiva:

```powershell
python manage.py import_complete_fcacc
```

El proceso es repetible: usa cédula, códigos de catálogo y la combinación
carrera–asignatura–período–paralelo para actualizar sin duplicar. Las
actividades se guardan en su catálogo independiente y los archivos de
planificación raíz incompletos no se usan como fuente de asignaciones.
