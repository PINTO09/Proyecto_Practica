# Análisis del sistema y hoja de ruta

Fecha de revisión: 22 de julio de 2026.

## 1. Resumen ejecutivo

El proyecto ya cubre el núcleo de una planificación docente: catálogos,
docentes, currículo, afinidad, demanda, asignaciones por paralelo, actividades,
Matriz F4, consolidación de carga, restricciones, auditoría y exportaciones. Su
principal reto ya no es agregar pantallas aisladas, sino convertir esas piezas
en un único procedimiento controlado, trazable y fácil de operar.

El repositorio tiene aproximadamente 53 modelos, 219 rutas y 11 pruebas. Esta
relación muestra que la cobertura automatizada todavía es baja para el tamaño
del sistema. Además, varios modelos representan tablas externas no administradas
por Django, por lo que la sincronización entre modelo, esquema y migraciones debe
tratarse como un riesgo prioritario.

## 2. Proceso reconstruido desde la integración de Excel

Los importadores y validadores evidencian que los libros suministran, al menos,
los siguientes pasos funcionales:

1. Carreras y períodos.
2. Modalidades y dedicaciones docentes.
3. Campos de conocimiento.
4. Asignaturas, niveles y horas semanales.
5. Relación asignatura–campo.
6. Docentes y datos personales.
7. Títulos y formación de los docentes.
8. Afinidad docente–campo.
9. Demanda académica y número de paralelos.
10. Asignaciones por docente, asignatura, nivel y paralelo.
11. Horas adicionales, investigación y Matriz F4.
12. Consolidación y comparación del total de horas por docente.

Los archivos disponibles incluyen libros maestros, detallados, malla, docentes,
nivel docente y planificaciones por carrera. El código reconoce hojas como
`MAE_CARRERA`, `MAE_ASIGNATURA`, `MAE_CONOCIMIENTO`, `MDOCENTES`,
`DET_DOCENTE`, `ASIGNACION` y `CARRERAS_FCACC`.

Esta reconstrucción proviene del código de importación. Las fórmulas y el diseño
celda por celda de los libros deben verificarse directamente antes de declarar
paridad total con Excel.

## 3. Fortalezas actuales

- Separación por dominios mediante aplicaciones Django.
- Reglas de afinidad desde nivel 4 y asignación libre en niveles 1–3.
- Validación de límites por modalidad y carga docente.
- Selección de paralelos y vistas operativa, consolidada y detallada.
- Importación transaccional con modo de simulación en los comandos principales.
- Historial de cargas y auditoría de cambios.
- Exportación general y detallada en Excel.
- Acceso por IP local y configuración por variables de entorno.
- Interfaz adaptable, modo oscuro y controles de accesibilidad.

## 4. Riesgos y mejoras prioritarias

### Prioridad crítica

1. **Flujo de aprobación por período.** Incorporar estados `BORRADOR`,
   `EN_REVISIÓN`, `APROBADO` y `CERRADO`. Un período aprobado debe bloquear
   cambios ordinarios y requerir reapertura auditada.
2. **Permisos por acción.** Los CRUD genéricos solo exigen autenticación. Deben
   diferenciar lectura, creación, edición, eliminación, importación, aprobación y
   exportación según rol.
3. **Unificar identidades.** Actualmente conviven usuarios y docentes en modelos
   locales y tablas FCACC. Definir una fuente principal y sincronizaciones
   explícitas evitará perfiles duplicados o divergentes.
4. **Servicio único de carga docente.** El cálculo de clase, complementarias,
   investigación, F4, límite y porcentaje debe residir en un servicio de dominio,
   no dentro de vistas. Todas las pantallas y exportaciones deben consumirlo.
5. **Restricciones de base de datos.** Añadir unicidad para asignatura, carrera,
   período y paralelo; impedir horas negativas; y proteger períodos cerrados.

### Prioridad alta

1. **Centro de importaciones web.** Permitir subir un libro, detectar su versión,
   previsualizar cambios, mostrar filas inválidas y confirmar la importación. No
   depender de rutas absolutas ni de índices fijos de columna.
2. **Mapeo por encabezados.** Sustituir posiciones como columna 11 o 22 por
   nombres normalizados y un perfil versionado para cada formato de Excel.
3. **Eliminar importadores duplicados.** Consolidar `import_planificacion_excel`
   e `import_complete_fcacc` en una canalización reutilizable por etapas.
4. **Actividades sin pseudo-carreras.** El Excel representa algunas actividades
   como carreras especiales. El sistema debe traducirlas al catálogo de
   actividades y conservar la carrera solo cuando sea un dato académico real.
5. **Conciliación visible.** Mostrar por docente: total Excel, total sistema,
   diferencia, origen de la diferencia y acción recomendada.
6. **Copiar planificación anterior.** Crear un nuevo período a partir del anterior,
   marcando docentes inactivos, asignaturas cambiadas y paralelos pendientes.

### Prioridad media

1. Búsquedas por nombre, cédula, asignatura, nivel y paralelo desde una barra
   global.
2. Filtros persistentes y vistas guardadas por coordinador.
3. Edición masiva tipo matriz con teclado, validación inmediata y guardado por
   lote.
4. Notificaciones de sobrecarga, falta de afinidad y asignaturas sin docente.
5. Panel de calidad de datos: cédulas repetidas, docentes sin modalidad,
   asignaturas sin campo, límites faltantes y períodos inconsistentes.
6. Exportaciones con portada de filtros, fecha, usuario responsable y versión del
   período.

## 5. Mejoras de interfaz aplicadas

- Azul `#2563EB` como color primario y navegación en azul marino.
- Colores semánticos reservados para éxito, advertencia y error.
- Identidad visual unificada en botones, enlaces, foco, tablas y formularios.
- Tarjetas de indicadores y módulos con jerarquía y estados de interacción.
- Marca con logotipo en la barra lateral y mejor agrupación de módulos.
- Enlace “Saltar al contenido”, foco visible y respeto a movimiento reducido.
- Mejor presentación de período activo, estados vacíos y navegación de
  planificación.
- Una sola fuente canónica para archivos estáticos, evitando que Django sirva
  estilos antiguos.

## 6. Procedimiento objetivo recomendado

1. El administrador configura catálogos, período y límites.
2. El coordinador importa o registra demanda y malla.
3. El sistema valida campos de conocimiento, docentes y afinidad.
4. El coordinador genera o ajusta asignaciones por paralelo.
5. Registra actividades complementarias independientes de carrera.
6. Revisa carga, conflictos y diferencias frente al Excel.
7. Envía la planificación a revisión.
8. La autoridad aprueba y cierra el período.
9. Se generan exportaciones general y detallada con la versión aprobada.
10. Toda reapertura o modificación posterior queda auditada.

## 7. Estrategia de pruebas

La siguiente meta debe ser cubrir primero reglas de negocio, no solo páginas:

- límites de horas y estados de carga;
- afinidad obligatoria desde nivel 4;
- unicidad por paralelo;
- actividades sin carrera;
- importación idempotente y modo simulación;
- permisos por rol;
- cierre y reapertura de período;
- conciliación Excel–sistema;
- contenido y filtros de las exportaciones.

Una meta razonable es superar 50 pruebas antes de ampliar significativamente el
número de funciones de planificación.

## 8. Integración ejecutada el 22 de julio de 2026

Se aplicó una carga transaccional e idempotente usando los libros consolidados
de catálogos y los tres libros de coordinación. Antes de la carga se creó un
respaldo local de 30 tablas. Los archivos `PLANIFICACION_ADMINISTRACION.xlsx`,
`PLANIFICACION_COMERCIO.xlsx`, `PLANIFICACION_CONTABILIDAD.xlsx`,
`PLANIFICACION_FCACC.xlsx` y `MALLA.xlsx` quedaron fuera de las asignaciones por
ser plantillas parciales, contener fórmulas rotas o clasificaciones incorrectas.

Resultado verificado en PostgreSQL:

- 135 docentes preservados y actualizados; ninguno fue eliminado.
- 136 títulos académicos, todos vinculados con su posgrado del catálogo.
- 35 campos y 444 relaciones asignatura–campo.
- 90 posgrados únicos y 131 relaciones posgrado–campo.
- 378 asignaturas académicas.
- 187 demandas, 255 asignaciones válidas y 23 actividades docentes.
- cero duplicados por carrera–asignatura–período–paralelo.
- cero asignaciones sin afinidad desde cuarto nivel en el período 2026-2; las
  detectadas quedaron como demandas pendientes y registradas en el historial.

También se corrigió el historial de carga, se agregó una restricción única en
PostgreSQL, se separaron las actividades de las pseudo-carreras, se corrigió la
normalización de correo y teléfono, y se eliminó la restricción incorrecta que
impedía a un docente impartir materias distintas dentro del mismo período.

Permanecen como trabajo futuro los cambios estructurales que requieren una
decisión institucional: flujo formal de aprobación/cierre del período,
unificación definitiva entre usuarios y docentes, y el centro web de
importaciones con aprobación fila por fila.

## 9. Navegación e interfaces revisadas el 22 de julio de 2026

- La barra lateral se organizó como un acordeón de siete módulos. Solo se
  despliega el módulo elegido y Planificación ya no presenta todas sus opciones
  al mismo tiempo.
- La sección y la opción actuales quedan destacadas. El navegador conserva el
  módulo abierto y la posición vertical del menú al cambiar de pantalla.
- Se incorporó un buscador de opciones en la propia barra lateral y accesos
  directos a demanda, paralelos, actividades, control de horas y exportaciones.
- Los listados compartidos ahora tienen búsqueda más clara, tamaños de página
  limitados, paginación abreviada y estados vacíos distintos para “sin datos” y
  “sin coincidencias”.
- Los formularios identifican campos obligatorios, anuncian errores y advierten
  si se intenta salir con cambios pendientes. Las confirmaciones de eliminación
  muestran el registro afectado.
- Se eliminó la conversión automática indiscriminada a mayúsculas, que podía
  alterar contraseñas y textos libres. En adelante solo se transforma un campo
  marcado explícitamente con `data-uppercase="true"`.
- La navegación es utilizable con teclado, tiene foco visible y mantiene su
  comportamiento en escritorio y dispositivos móviles.

### Correcciones de regresión

- Se corrigió el error HTTP 500 del listado de períodos: los campos `DateField`
  y `DateTimeField` ahora utilizan formatos distintos.
- Se agregó `python manage.py audit_interfaces`, que recorre las páginas y sus
  enlaces representativos para detectar errores HTTP, textos mal codificados e
  identificadores HTML duplicados.
- Bootstrap, Font Awesome y Bootstrap Icons se sirven desde el proyecto. La
  interfaz ya no depende de Internet cuando se abre mediante la IP de la red
  local.
- Resultado de verificación: 143 interfaces sin errores ni advertencias, 18
  pruebas automatizadas aprobadas y todos los recursos visuales con HTTP 200.
