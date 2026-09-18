# Valoración y selección de actividades

El certificado de funciones y comisiones aplica estas reglas:

- Las actividades complementarias se incluyen cuando su peso es `1`.
- Las asignaturas y actividades de currículo se incluyen cuando está marcada
  «Incluir en funciones y comisiones», en los formularios de creación y edición.
- «Solo actividades» reúne las complementarias y los registros de currículo
  marcados como actividad. «Solo asignaciones» reúne las asignaturas restantes.
- Al elegir docente se muestran las actividades habilitadas que tiene asignadas
  dentro del período seleccionado. Marcar opciones limita la emisión a esas
  actividades. Sin opciones marcadas se incluyen todas las habilitadas.
- La selección de actividades no limita las asignaciones o comisiones si se
  seleccionó el contenido «Actividades, asignaciones y comisiones».
- «Todos los períodos» incluye el historial disponible y conserva la valoración.
- Los certificados emitidos conservan los datos guardados al generarse.

La valoración no cambia las horas de planificación, los reportes de carga,
el certificado de cátedras ni las comisiones de servicio, que son información
independiente de la valoración de la asignatura asociada.

## Configuración y actualización

Aplicar `python manage.py migrate` al actualizar otra instalación. La migración
`curriculo.0007_importante_certificado` añade la columna a la tabla heredada de
asignaturas (modelo no administrado por Django).

La inclusión se conserva por defecto para registros existentes. Para excluir
«Clase de docencia», editar el registro correspondiente y desmarcar la casilla
o establecer peso `0` si pertenece al catálogo de actividades complementarias.
No se clasifican registros automáticamente por su nombre.

## Verificación

```powershell
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py test certificados curriculo
.\venv\Scripts\python.exe scripts/verificar_filtros_certificados.py
```

La última orden utiliza SQLite en memoria y el ORM real para verificar
exclusión, selección entre ambas fuentes, períodos, validación del formulario
y conservación de cátedras y comisiones. No modifica la base del proyecto.
