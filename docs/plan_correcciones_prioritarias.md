# Plan priorizado de correcciones críticas y altas

**Fecha:** 27 de agosto de 2026

**Estado:** plan aprobado para implementación futura; no ejecutado

**Base revisada:** commit `d127d87439fec07638ff85f2a841eab229602c46`

**Documento de estado:** [`estado_migracion.md`](estado_migracion.md)

## Objetivo

Eliminar los hallazgos críticos y altos antes de usar datos reales o
calificaciones oficiales, manteniendo paridad de comportamiento segura con SIAC y
demostrando que cualquier transformación destructiva de datos es conciliable y
reversible.

Este documento define orden, límites y pruebas de aceptación. No autoriza por sí
solo el despliegue, la aplicación de migraciones en producción ni la carga de datos
del colegio.

## Decisiones rectoras

| Decisión | Criterio acordado |
|---|---|
| Paridad | Reproducir el comportamiento útil de Rails, endurecer sus fallos y documentar desviaciones. |
| Autorización | Denegar por defecto; toda operación debe comprobar capacidad y ámbito del objeto real. |
| Datos médicos | Migración reversible y conciliada antes de eliminar el modelo origen. |
| Calificaciones | Ningún ID enviado por el cliente se considera autorizado por haber aparecido en un formulario. |
| Evidencia | Pruebas felices, negativas, manipulación directa, comparación Rails y reversión cuando corresponda. |
| Migraciones locales | No aplicar `support.0002` hasta sustituir o asegurar su política de datos. |

## Secuencia y puertas

| Prioridad | Paquete | Hallazgos | Puerta de salida |
|---:|---|---|---|
| P0 | Congelar contratos y fixtures de seguridad | Todos | Casos de abuso reproducidos como pruebas que fallan antes de corregir. |
| P1 | Integridad de calificaciones | C-01 | Ninguna calificación fuera del queryset autorizado puede modificarse. |
| P1 | Alcance institucional y privacidad global | C-02 | Una cuenta sin concesión explícita no ve reportes ni bitácora global. |
| P2 | Motor de ámbitos y vigencia | H-01 | Matriz completa positiva/negativa para identidades y ámbitos heredados. |
| P3 | Clonación segura del período | H-02 | Precondiciones, fechas y estructura contrastadas con Rails; rollback atómico. |
| P3 | Migración médica reversible | H-03 y H-04 | Ida, conciliación y vuelta probadas antes de aplicar migraciones pendientes. |

Los dos paquetes P1 pueden desarrollarse de forma independiente, pero ambos deben
cerrarse antes de P2. P3 no bloquea las correcciones de autorización, aunque sí
bloquea cualquier ensayo de datos reales.

## P0 — contratos de seguridad y datos

### Trabajo

- Convertir cada vulnerabilidad crítica y alta en una prueba de regresión que falle
  sobre la línea base actual.
- Crear fixtures mínimos con dos ámbitos incompatibles: dos docentes, dos materias,
  dos secciones, estudiantes distintos y perfiles global/contextual/inactivo.
- Documentar la correspondencia entre `Nivel`, `Clase`, `Seccion`, `Materia`,
  `Estudiante`, `Docente`, `Pariente` y mensajes en Rails y Django.
- Preparar fixtures médicos con destino inexistente, destino coincidente, conflicto,
  valores vacíos y múltiples registros anómalos.

### Pruebas requeridas

- Confirmación explícita de que cada caso C-01, C-02, H-01, H-02 y H-03 falla antes
  de su corrección.
- Los fixtures no deben usar superusuario para demostrar permisos ordinarios.
- Cada prueba debe verificar estado persistido, no sólo código HTTP o texto de una
  respuesta.

### Salida

Existe una línea roja reproducible: si una corrección se revierte, al menos una
prueba negativa vuelve a fallar.

## P1A — proteger la escritura de calificaciones

### Diseño

- Construir el conjunto de calificaciones editable desde la materia, tipo de nota,
  período y ámbito ya autorizados.
- Resolver cada `calif_<id>` únicamente dentro de ese conjunto; un ID desconocido o
  ajeno invalida el lote completo.
- Validar el valor con las mismas reglas de dominio que cualquier formulario o
  servicio de calificación: decimal válido, rango permitido, estado editable y
  período abierto.
- Ejecutar la operación en una transacción atómica y registrar actor, materia y
  resultado sin duplicar eventos.
- No confiar en campos ocultos, parámetros GET ni IDs procedentes del cliente para
  establecer el ámbito.

### Pruebas requeridas

1. Docente A modifica una calificación de su materia: permitido.
2. Docente A envía el ID de una calificación de la materia del docente B: denegado y
   ninguna fila cambia.
3. Lote con una fila propia y una ajena: rollback completo.
4. ID inexistente, valor no decimal, valor fuera de rango y tipo de nota ajeno:
   rechazo sin persistencia parcial.
5. Materia o período cerrado: rechazo.
6. Dos solicitudes concurrentes sobre la misma fila: comportamiento definido, sin
   pérdida silenciosa de actualización.
7. Superusuario conserva la capacidad esperada, pero bajo las mismas validaciones de
   dominio.

### Salida

La única ruta de escritura masiva usa un queryset autorizado y validado; la prueba
de ID foráneo demuestra que C-01 quedó cerrado.

## P1B — alcance institucional explícito y dashboard privado

### Diseño

- Redefinir alcance global como una concesión global, activa y vigente; la ausencia
  de asignaciones nunca concede privilegios.
- Exigir un permiso específico para descargar el reporte institucional de docentes.
- Separar las métricas públicas al usuario de la bitácora global. La bitácora sólo
  debe entregarse con `audit.ver_bitacora` o filtrarse a eventos del propio ámbito.
- Asegurar que los usuarios creados por ETL queden inhabilitados o sin acceso hasta
  recibir perfil y asignación explícitos.

### Pruebas requeridas

1. Cuenta habilitada sin perfil ni asignaciones: no es global y no descarga el XLSX.
2. Estudiante y pariente autenticados: no reciben eventos globales ni datos de la
   planta docente.
3. Perfil contextual con permiso nominal pero sin concesión global: denegado.
4. Perfil institucional activo, vigente y con permiso dedicado: permitido.
5. Perfil institucional inactivo, futuro o vencido: denegado.
6. Acceso directo a la URL y seguimiento de redirecciones no filtran el archivo ni
   la bitácora en el cuerpo de respuesta.
7. Usuario recién importado por ETL: no adquiere acceso institucional implícito.

### Salida

No existe camino autenticado hacia reportes o auditoría global sin concesión y
permiso explícitos; C-02 queda cubierto por matriz negativa.

## P2 — completar el motor de autorización contextual

### Diseño

- Centralizar la vigencia de asignaciones: `activo`, `perfil.activo`, fecha de
  inicio inclusiva y fecha de fin inclusiva.
- Diferenciar operaciones sin objeto real de operaciones sobre colecciones. Crear no
  equivale a gestionar cualquier objeto; los formularios y servicios deben limitar
  relaciones seleccionables al ámbito autorizado.
- Definir filtros canónicos para listados y comprobaciones canónicas para detalle,
  edición, eliminación y POST.
- Implementar la propagación de Nivel y Clase observada en `Ability.rb` sin portar
  literalmente CanCan: Nivel → clases → secciones/materias/estudiantes; Clase →
  secciones/materias/estudiantes. Cada acción conserva su permiso específico.
- Completar el ámbito docente incluyendo docente guía, docente primario de
  `Materia`, asignaciones auxiliares y jefatura de asignatura cuando corresponda.
- Tratar tipos no soportados como denegados y evitar que `objeto=None` sea un atajo
  de ámbito.

### Pruebas requeridas

- Límites temporales: comienza hoy, termina hoy, futura, vencida y sin fechas.
- Perfil activo/inactivo combinado con asignación activa/inactiva.
- Matriz para administrador institucional, personal contextual, docente guía,
  docente de materia, estudiante y pariente.
- Ámbitos Nivel y Clase dentro/fuera para listado, detalle, edición y POST directo.
- Matrícula: un usuario contextual no puede seleccionar ni matricular un estudiante
  ajeno aunque manipule `estudiante_id`.
- Responsables y parientes: las opciones y los IDs enviados permanecen dentro del
  ámbito.
- Materia primaria, auxiliar y ajena; sección guía y ajena.
- Mensajes, adjuntos, incidencias, ficha médica, boletín y reportes por acceso directo.
- Todas las pruebas negativas verifican que no se creó, modificó ni eliminó ninguna
  fila.

### Salida

La matriz demuestra capacidad **y** ámbito en cada operación; H-01 no se cierra con
una prueba únicamente de lectura.

## P3A — clonación de período con paridad segura

### Diseño

- Exigir las precondiciones Rails: origen abierto y período actual, salvo desviación
  explícita aprobada y documentada.
- Calcular inicio y fin desplazando exactamente un año, preservando fechas válidas
  y definiendo el caso del 29 de febrero.
- Ejecutar validaciones completas antes de crear el destino, incluida la detección
  de traslape.
- Mantener toda la clonación en una transacción atómica; cualquier relación inválida
  revierte el período y todos sus hijos.
- Comparar campo por campo tipos de nota, configuración, clases, secciones, docentes,
  materias, horarios y asignaciones. Toda omisión intencional debe quedar documentada.

### Pruebas requeridas

1. Período abierto y actual: clona fechas originales +1 año.
2. Período cerrado o no actual: rechazo sin crear destino.
3. Destino traslapado: rechazo y cero filas parciales.
4. Fecha que incluye 29 de febrero: regla documentada y estable.
5. Error al crear una relación hija: rollback completo.
6. Comparación estructural Rails → Django mediante fixture dorado, incluidos roles y
   relaciones de docentes/horarios.
7. La versión y configuración del origen no cambian durante la copia.

### Salida

Un fixture dorado y las pruebas de fallo demuestran paridad estructural y atomicidad;
H-02 queda cerrado.

## P3B — consolidación médica reversible y aplicación controlada

### Diseño

- No usar sobrescritura ciega. Clasificar cada estudiante como: sólo origen, sólo
  destino, coincidencia, complemento no conflictivo o conflicto.
- Definir precedencia por campo. Los conflictos no resueltos se registran y bloquean
  la eliminación de la tabla origen.
- Generar conteos antes/después y una salida conciliable con identificadores, sin
  exponer datos médicos sensibles en logs generales.
- Conservar un respaldo restaurable y una reversa que reconstruya los registros
  requeridos por el estado anterior.
- Ejecutar la migración dentro de un ensayo sobre copia anonimizada antes de la base
  real.
- Sólo después de cerrar H-03 aplicar, en orden, las cinco migraciones pendientes y
  confirmar que el plan queda vacío.

### Pruebas requeridas

1. Registro sólo en `RegistroMedico`: copia completa a `FichaMedica`.
2. Ficha existente idéntica: operación idempotente.
3. Campos complementarios: combinación según regla documentada.
4. Conflicto y campos vacíos: no sobrescritura silenciosa; migración bloqueada o
   conflicto registrado según contrato.
5. Dos ejecuciones de ida producen el mismo resultado.
6. Ida → reversa restaura cantidades y valores relevantes del estado anterior.
7. Fallo a mitad de lote: rollback o reanudación segura, sin pérdida parcial.
8. Conteos y checksums antes/después coinciden con la conciliación esperada.
9. `showmigrations` marca las cinco migraciones aplicadas y `migrate --plan` no
   presenta operaciones pendientes al terminar el ensayo aprobado.

### Salida

Existe evidencia de ida, vuelta, conflictos y conciliación. Sólo entonces pueden
aplicarse `support.0002` y las demás migraciones a un entorno con datos.

## Regresión obligatoria al cerrar cada paquete

- `manage.py check`
- `manage.py makemigrations --check --dry-run`
- pruebas dirigidas del paquete
- suite completa en PostgreSQL
- `manage.py check --deploy` con configuración de producción de prueba
- `migrate --plan` documentado contra una base controlada
- revisión de acceso directo y POST manipulado para cambios de autorización
- actualización de [`estado_migracion.md`](estado_migracion.md) con evidencia real,
  sin tachar un hallazgo antes de cumplir su puerta de salida

## Fuera de alcance de este plan

Los hallazgos medios —mensajería por audiencia y lectura, inmutabilidad completa de
auditoría, contexto ASGI, parámetros exactos de cuenta y jobs asíncronos— permanecen
abiertos y deberán planificarse después de P3. Tampoco se incluye todavía el ETL
completo, golden master de calificaciones/reportes, despliegue, corte productivo ni
restauración general del sistema.

## Orden recomendado de implementación

1. P0: fijar pruebas que reproduzcan los fallos.
2. P1A y P1B: cerrar ambos críticos.
3. P2: reconstruir la matriz de ámbitos sobre las garantías de P1.
4. P3A: cerrar la clonación y su fixture dorado.
5. P3B: reemplazar la política médica, ensayar reversión y aplicar migraciones en
   entorno controlado.
6. Reauditar el estado completo antes de autorizar datos reales.
