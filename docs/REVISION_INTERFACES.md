# Revisión de interfaces locales

## Fallos encontrados y corregidos

1. **Consulta de información de docentes:** `/api/modelo-info/` devolvía HTTP 500
   porque intentaba convertir el objeto de la fotografía directamente a JSON.
   Ahora devuelve su URL, o una cadena vacía cuando no hay foto. Los identificadores
   inválidos devuelven HTTP 400. Esta consulta se utiliza para autocompletar formularios.
2. **Asignaturas con permisos de consulta:** el listado mostraba Crear, Editar y
   Eliminar incluso para coordinadores sin permisos de modificación. Ahora las
   acciones respetan `can_change_records`, también cuando el listado está vacío.
3. **Catálogo de actividades:** el menú ofrecía este enlace a coordinadores, pero
   la vista está reservada a administradores. El menú ahora respeta esa restricción.
4. **Administración de firmantes:** el formulario y el resumen de certificados
   ofrecían el enlace a coordinadores que no pueden administrar firmantes.
   Se unificó la comprobación del acceso para el menú, el resumen y el formulario.
5. **Tamaño de página en asignaturas:** la opción de 20 registros no coincidía con
   los tamaños admitidos por la vista. Se reemplazó por la opción válida de 25.

Los permisos del servidor no se ampliaron para resolver los errores de navegación.

## Verificaciones

- Compilación de 71 plantillas, sin errores de sintaxis.
- Recorrido de las rutas GET y de una muestra de enlaces y registros con cuentas
  existentes de Administrador, Coordinador y Docente.
- Cliente de pruebas de Django con middleware y autenticación simulada como esas
  cuentas. Las consultas se ejecutan en transacciones PostgreSQL de solo lectura.
- Comprobación de filtros, búsquedas y consultas de datos con parámetros válidos.
- Comprobación de disponibilidad de los recursos estáticos locales referenciados.
- Suite de 101 pruebas aprobada, incluidas las regresiones para la fotografía y
  los enlaces de modificación en asignaturas.

Los informes JSON guardan los resultados por ruta y distinguen los errores de los
enlaces visibles (`navigation_errors`) de los accesos directos a rutas protegidas.
Un 403 al solicitar directamente una acción restringida, un 404 para un registro
fuera del alcance de la cuenta y un 400 en una API sin parámetros pueden ser
respuestas esperadas, no errores de carga.

## Repetir la revisión

Desde la carpeta `Proyecto_Practica`:

```powershell
.\venv\Scripts\python.exe manage.py test
.\venv\Scripts\python.exe scripts/auditar_interfaces.py --follow-links --http
.\venv\Scripts\python.exe scripts/auditar_interfaces.py --role Coordinador --follow-links --http
.\venv\Scripts\python.exe scripts/auditar_interfaces.py --role Docente --follow-links --http
.\venv\Scripts\python.exe scripts/auditar_interfaces.py --filters-only
```

## Alcance pendiente de reproducción

Esta revisión corresponde al proyecto y a la base locales. No despliega cambios
ni comprueba el servidor de la captura. No envía formularios de modificación,
no crea certificados ni elimina registros. Los formularios de edición sin datos
de ejemplo quedan identificados como omitidos en los informes.

El cliente de Django verifica las respuestas y el HTML, pero no ejecuta JavaScript
en un navegador ni valida servicios externos. Para reproducir otro error reportado
se necesita la ruta concreta, el rol utilizado y el mensaje que aparece.
