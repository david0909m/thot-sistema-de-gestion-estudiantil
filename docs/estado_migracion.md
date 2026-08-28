# Estado actual de la migración SIAC → THOT

**Corte de auditoría:** 25 de agosto de 2026  
**Estado del documento:** vigente  
**Proyecto legado:** `C:\Users\David\Documents\Sistema Escolar\Version vieja ruby\SIAC-CCA`  
**Proyecto Django:** `C:\Users\David\Documents\GitHub\thot-sistema-de-gestion-estudiantil`

## Conclusión ejecutiva

THOT es hoy un **prototipo Django funcional y de cobertura visual amplia**. La
aplicación arranca, sus migraciones están sincronizadas y las 126 pruebas actuales
pasan en PostgreSQL. Eso demuestra consistencia interna para los escenarios
cubiertos.

No es todavía una migración equivalente ni está lista para producción. Ninguna
fase puede declararse cerrada mientras falten:

- ~~autorización segura por acción y ámbito~~ **corregida en la Fase 1 del
  2026-08-25** (ver hallazgo 1);
- ~~clonación íntegra de período lectivo y bloqueo optimista atómico~~
  **corregidos en la Fase 2 del 2026-08-26** (ver hallazgo 4);
- ~~flujos heredados de cuenta y endurecimiento de parámetros~~ **resueltos en
  la Fase 3 del 2026-08-27** (ver hallazgo 6; `check --deploy` sin avisos con
  `DEBUG=False`);
- ~~bitácora de auditoría con origen válido, actor/IP, sin duplicados e
  inmutable~~ **corregido en la Fase 4 del 2026-08-27** (ver hallazgo 7);
- ~~expediente médico duplicado~~ **unificado en la Fase 5 del 2026-08-27**
  (ver hallazgo 5);
- un conjunto dorado Rails → Django para calificaciones y reportes;
- migración repetible de datos e históricos reales;
- conciliación contra una base y archivos del colegio;
- ensayo de corte/reversión y simulacro de restauración de respaldo.

La prioridad inmediata no es agregar más pantallas. Es cerrar autorización,
integridad académica y estrategia de datos sobre una línea base versionada.

## Evidencia verificada

### Ejecución

| Comprobación | Resultado del 2026-08-25 | Resultado tras Fase 1 de corrección (2026-08-25) | Resultado tras Fase 2 de corrección (2026-08-26) | Resultado tras Fase 3 de corrección (2026-08-27) | Resultado tras Fase 4 de corrección (2026-08-27) | Resultado tras Fase 5 de corrección (2026-08-27) | Resultado tras Fase 6 de corrección (2026-08-27) |
|---|---|---|---|---|---|---|---|
| `manage.py check` | Sin problemas. | Sin problemas. | Sin problemas. | Sin problemas. | Sin problemas. | Sin problemas. | Sin problemas. |
| `manage.py makemigrations --check --dry-run` | Sin cambios pendientes. | Sin cambios pendientes (nuevas migraciones ya aplicadas al esquema de pruebas). | Sin cambios pendientes (la Fase 2 no requiere migración nueva). | Sin cambios pendientes (la Fase 3 no requiere migración nueva). | Sin cambios pendientes (el nuevo origen `SISTEMA` es sólo de `choices`, sin cambios de esquema). | Sin cambios pendientes tras generar `support.0002_delete_registromedico` (copia de datos + borrado del modelo) y `audit.0002_alter_auditevent_origen` (normalización del origen). | Sin cambios pendientes tras generar `support.0003_mensajeusuario` (nuevo modelo `MensajeUsuario`). |
| `manage.py migrate --plan` | Ninguna operación pendiente. | — | Ninguna operación pendiente. | — | — | — | — |
| `manage.py test --noinput` | **86 pruebas aprobadas** en 24.583 s sobre una base temporal PostgreSQL. | **99 pruebas aprobadas** en 39.411 s sobre una base temporal PostgreSQL (13 pruebas nuevas de matriz de permisos). | **102 pruebas aprobadas** en 40.820 s sobre una base temporal PostgreSQL (3 pruebas nuevas: paridad integral de clonación, traslape de períodos e incremento atómico de versión). | **111 pruebas aprobadas** en 45.821 s sobre una base temporal PostgreSQL (9 pruebas nuevas: login por correo, validadores de contraseña, renovación de vencimiento y flujo completo de recuperación). | **120 pruebas aprobadas** en 50.473 s sobre una base temporal PostgreSQL (9 pruebas nuevas: inmutabilidad de la bitácora, actor/IP por contexto, explícito gana sobre contexto y deduplicación señal-vista). | **120 pruebas aprobadas** en 48.902 s sobre una base temporal PostgreSQL (reemplazo 1:1 de la prueba de `RegistroMedico` por una de unicidad y render de `FichaMedica`; sin cambio en el total). | **126 pruebas aprobadas** en 53.206 s sobre una base temporal PostgreSQL (6 pruebas nuevas de `MensajeUsuario`: creación de fila, lectura por destinatario/remitente/tercero, bandeja y GLOBAL sin filas). |
| `manage.py check --deploy` | 5 advertencias: HSTS, redirección HTTPS, cookies de sesión seguras, cookie CSRF segura y `DEBUG=True`. | Sin cambios (pendiente Fase 3). | Sin cambios (pendiente Fase 3). | **Sin advertencias** con `DEBUG=False`: HSTS (con preload), SSL redirect, cookies de sesión/CSRF seguras y `DEBUG` resueltos; el modo desarrollo permanece funcional. | Sin cambios. | Sin cambios. | Sin cambios. |
| Entorno observado | Python 3.12.10, Django 5.1.15 y PostgreSQL 17.10. | Igual. | Igual. | Igual. | Igual. | Igual. | Igual. |

Las dependencias instaladas tienen versiones concretas, pero `requirements.txt`
mantiene rangos abiertos; por tanto, el entorno aún no es reproducible a partir del
repositorio.

### Inventario Django

| Elemento | Cantidad verificada | Aclaración |
|---|---:|---|
| Aplicaciones de dominio | 8 | `accounts`, `academic_core`, `people`, `grading`, `support`, `integrations`, `reporting`, `audit`. |
| Modelos explícitos | 35 | No incluye modelos históricos generados por `django-simple-history`. La Fase 5 eliminó `support.RegistroMedico` y la Fase 6 añadió `support.MensajeUsuario`. |
| Migraciones de aplicación | 15 | Fase 1 añadió `academic_core.0003_seccion_docente` y `accounts.0002_permisos_soporte`; la Fase 5 añadió `support.0002_delete_registromedico` y `audit.0002_alter_auditevent_origen`; la Fase 6 añadió `support.0003_mensajeusuario`. |
| Declaraciones `path()` | 71 | 70 rutas de la aplicación y una entrada para Django Admin. |
| Plantillas HTML | 53 | Incluye personalización de Admin, pantallas de soporte y flujo de recuperación de contraseña. |
| Métodos de prueba | 126 | En 30 archivos; predominan unitarias, servicios, vistas, humo con superusuario, matriz de permisos por ámbito, paridad de clonación, seguridad operativa de cuentas, inmutabilidad/atribución de auditoría y mensajería por destinatario. |

### Estado de la base local

La base configurada no contiene un corte del sistema legado: hay cero períodos,
clases, secciones, materias, estudiantes, matrículas, evaluaciones y
calificaciones. Conserva una cuenta local, 17 parientes y 203 eventos de auditoría
de actividad de desarrollo. Estos registros no constituyen evidencia de migración.

En la ruta del sistema Ruby sólo se encontraron código, `schema.rb`, `seeds.rb`,
migraciones y activos del manual. No se encontró un dump de la base productiva ni
el repositorio de fotografías/documentos de estudiantes. Sin esas fuentes no se
puede ensayar ni conciliar el corte real.

## Evolución de los documentos anteriores

| Corte documental | Evidencia declarada | Qué cambió o se corrigió ahora |
|---|---|---|
| 2026-08-12, plan del repositorio Django | 65 pruebas ejecutadas, 9 migraciones, 21 rutas y 16 plantillas; en otra sección declaraba 39 pantallas y “Frontend 100%”. | El documento mezclaba inventarios de momentos distintos y “100%” sólo significaba renderizado, no paridad funcional. Queda archivado. |
| 2026-08-22, plan junto al proyecto Ruby | 86 pruebas encontradas estáticamente, 10 migraciones, 71 rutas y 49 plantillas. No pudo ejecutar el entorno. | El inventario estático era correcto. Ahora las 86 pruebas sí fueron ejecutadas y pasaron en PostgreSQL. |
| 2026-08-25, auditoría vigente | Mismo inventario que el 22 de agosto. | No se observan archivos de aplicación modificados después del 22 de agosto según sus marcas de tiempo. El avance nuevo es evidencia ejecutada y una revisión más profunda de seguridad y datos, no funcionalidad adicional. |

Como casi toda la implementación continúa sin seguimiento en Git, las fechas de
archivo son una señal débil. No sustituyen una línea base con commit.

## Estado conservador por área

“Construido” describe presencia de modelos, servicios o interfaz. “Paridad” exige
comparación con Rails y datos reales; no se infiere por cantidad de pantallas o
pruebas internas.

| Área | Construcción actual | Paridad con Rails | Motivo para no cerrar |
|---|---|---|---|
| Fase 0 — identidad, permisos, catálogos y períodos | Parcial y utilizable por superusuario | No demostrada | Política de permisos **corregida en Fase 1** y flujos heredados de cuenta **resueltos en Fase 3** (login por correo, recuperación, vencimiento, timeout y validadores). Falta simulacro de restauración. |
| Fase 1A — estructura académica | Amplia en modelos y pantallas | No demostrada | Clonación íntegra y bloqueo optimista atómico **corregidos en Fase 2**. La paridad con datos legados sigue sin demostrar (sin conjunto dorado). |
| Fase 1B — personas | Amplia en expedientes y pantallas | No demostrada | Mapeos heredados, importaciones, archivos e historial no conciliados. El expediente médico quedó unificado en `FichaMedica` (Fase 5). |
| Fase 1C — soporte | Parcial | No demostrada | Mensajería sin destinatarios/estado por receptor, controles de privacidad incompletos y trabajos diferidos ausentes. |
| Fase 2 — calificaciones | Prototipo funcional | No demostrada; riesgo alto | Algoritmo simplificado, reglas heredadas faltantes y ausencia total de conjunto dorado. |
| Fase 3 — reportes e historial/auditoría | Parcial | No demostrada | 4 generadores XLSX frente a 14 plantillas AXLSX legadas, sin comparación celda a celda; auditoría global parcial. |
| Fase 4 — ETL, operación paralela y corte | Boceto técnico | No iniciada con datos reales | Sólo importa usuarios desde JSON; no existe origen de datos real, reconciliación completa, delta, rollback ni ensayo de corte. |
| Operación/producción | Desarrollo local funcional | No preparada | Avisos de `check --deploy` resueltos en Fase 3 (condicionados a `DEBUG=False`); siguen pendientes dependencias no fijadas, CI y backup/restauración probada. |
| Finanzas nativas | No iniciada | No aplica al legado | Rails consulta solvencia externa; no contiene caja, facturación o contabilidad propia. |

## Hallazgos prioritarios

### 1. Autorización y privacidad — bloqueador crítico

> **CORREGIDO en Fase 1 (2026-08-25).** Evidencia: suite de 99 pruebas verdes,
> incluye matriz negativa/positiva `apps/accounts/tests_permissions.py`
> (`PermissionsScopeMatrixTests`). Cambios aplicados:

- `puede()` ahora **deniega por defecto**: sólo `is_superuser` omite reglas
  (`is_staff` ya no concede capacidades), se exige `Autorizacion` vigente de
  perfil, los tipos de objeto no contemplados devuelven `False` y las reglas por
  objeto reproducen `Ability.rb`: materia propia/titular (`Materia.docente`),
  guía vía nueva FK `Seccion.docente`, auxiliar vía `DocenteMateria`,
  estudiante propio/pariente/docente de sección/contextual, sección del docente
  y docente propio o institucional.
- Corregida la relación rota (`docentes_asignados` → `asignaciones_docentes`) y
  eliminadas las referencias a atributos inexistentes de `Seccion`.
- Listados filtrados por ámbito: estudiantes (`estudiantes_list_view`),
  docentes (propio expediente si es docente), incidencias
  (`_incidencias_visibles`), evaluaciones/consolidación (`materias_visibles`),
  sábana de notas y reportes (`secciones_visibles`), índice de reportes y
  boletines XLSX.
- POST protegidos con permiso de gestión sobre el objeto:
  `estudiante_detail_view` (foto/traslado/retiro exige
  `people.estudiantes_gestionar` object-level), `ficha_medica_view`, crear y
  sancionar incidencias (nuevo permiso `support.incidencias_gestionar`),
  enviar mensajes (nuevo permiso `support.mensajes_enviar`, creado mediante la
  migración de datos `accounts.0002_permisos_soporte`) y crear/editar
  evaluaciones e ingreso de notas sobre materias propias.
- `mensaje_detail_view` aplica `puede_leer_mensaje()` (remitente, destinatario
  directo o audiencia GLOBAL) y registra `ACCESO_MENSAJE_DENEGADO` con
  `exito=False`; el boletín web valida alcance sobre el estudiante.
- Pruebas previas que usaban `is_staff` como administrador fueron migradas a
  `is_superuser`; se añadieron 13 pruebas de matriz (staff sin perfil denegado,
  pariente lee sólo a su hijo incluida denegación de POST con lectura,
  docente guía/auxiliar, tipo desconocido, usuario inhabilitado y privacidad de
  mensajes).

Pendiente para cierre total de Puerta 1: adjuntos genéricos sin control propio
y revisión de `reporting.descargar_boletin` frente al catálogo real de roles.

### 2. Calificaciones — lógica crítica aún no equivalente

- La consolidación Django suma hijos/evaluaciones directos, pero no reproduce el
  grafo, períodos internos, examen, reparación, umbral 99.9, exclusiones,
  configuración por nivel/materia ni propagación recursiva del legado.
- `calificacion_padre` sólo se asigna si el padre ya existe; reabrir sólo pone el
  resultado en `NULL`.
- `convertir_nota_a_literal()` no interpreta la lista ordenada
  `{limite, valor, nombre, descripcion}` serializada por Rails.
- El modelo Django no contiene las restricciones de unicidad equivalentes para
  impedir duplicados por evaluación o por consolidado. Tampoco se encontró una
  validación de rango 0–100 equivalente en el modelo.
- Las pruebas cubren ejemplos simples creados para Django. No ejecutan los mismos
  inputs y resultados en ambos sistemas.

La Fase 2 sólo puede avanzar mediante un conjunto dorado extraído del legado, no
sumando más pruebas autocontenidas con expectativas inventadas para Django.

### 3. Migración de datos — no existe todavía un ETL de corte

- `import_legacy_data` sólo procesa `usuarios` de un JSON.
- Si el archivo no existe, continúa y registra la importación como completada.
- No migra IDs, personas, estructura, matrículas, calificaciones, mensajes,
  versiones, sucesos, adjuntos ni fotografías.
- El conciliador compara conteos de la base Django consigo misma; no recibe
  conteos, sumas de control o reglas de la fuente Rails/MySQL.
- Las contraseñas temporales generadas no tienen un canal de entrega recuperable.

La Fase 4 está en estado de diseño/prototipo, no “en progreso” sobre datos reales.

### 4. Clonación y consistencia académica

> **CORREGIDO en Fase 2 (2026-08-26).** Evidencia: suite de 102 pruebas verdes
> (40.820 s), con las clases nuevas `CopiarEstructuraParidadTests` y
> `TraslapePeriodosTests` (`apps/academic_core/tests_clonacion.py`) y aserción de
> versión agregada a `test_materia_lock_version_concurrency`. Cambios aplicados:

- `copiar_estructura()` ya no lee el campo inexistente `dm.rol`: replica las
  asignaciones auxiliares conservando su bandera real `es_titular`.
- La clonación copia ahora los datos que Rails sí copiaba: `Clase.config`,
  la guía de sección (`Seccion.docente`) y `Materia.config` eliminando la clave
  efímera `periodo_actual_hash`, igual que el `copiar!` original.
- Copia también las `AsignacionUsuario` activas cuyo ámbito es cada clase,
  reasignadas al objeto Clase del nuevo período dentro de la misma transacción.
- Se corrigió además la creación de horarios, que fallaba al pasar `seccion`
  (atributo inexistente del modelo `Horario`) — caso no cubierto por pruebas.
- `PeriodoLectivo.clean()` detecta traslapes de fechas contra otros períodos,
  excluye su propio identificador y nombra al período en conflicto; los
  formularios web de creación/edición aplican esta validación automáticamente.
- `Materia.save()` hace el bloqueo optimista atómico: lectura con
  `select_for_update()` dentro de `transaction.atomic()`, comparación de versión
  bajo candado de fila e incremento único de `lock_version`. La prueba confirma
  incremento secuencial y rechazo ante una versión obsoleta.

### 5. Expediente médico dividido

> **CORREGIDO en Fase 5 (2026-08-27).** Evidencia: suite de 120 pruebas verdes
> (48.902 s) y `makemigrations --check` limpio tras aplicar las dos migraciones
> nuevas. Cambios aplicados:

- Se eligió `people.FichaMedica` como modelo canónico del expediente clínico.
- La migración `support.0002_delete_registromedico` copia campo a campo
  (`grupo_sanguineo→tipo_sangre`, `padecimientos→padecimientos_cronicos`,
  `medicamentos→medicamentos_permanentes`,
  `contacto_emergencia→contacto_emergencia_nombre`,
  `telefono_emergencia→contacto_emergencia_telefono`, además de alergias y
  observaciones) mediante `update_or_create` idempotente antes de borrar
  `RegistroMedico`.
- El expediente 360 (`estudiante_detail_view` y su plantilla) renderiza ahora
  `FichaMedica` con campos existentes; se eliminó el campo inexistente
  `condiciones_especiales`.
- `ficha_medica_view` ya editaba `FichaMedica`; admin, servicios, ETL y pruebas
  quedaron sin referencias al modelo eliminado.
- Nueva prueba de unicidad y render (`support/tests.py`): la ficha es única por
  estudiante y sus datos aparecen en el detalle web.

### 6. Cuentas y seguridad operativa

> **CORREGIDO en Fase 3 (2026-08-27).** Evidencia: suite de 111 pruebas verdes y
> `check --deploy` sin advertencias con `DEBUG=False` (`tests_fase3.py`). Cambios:

- **Login por correo**: `login_view` re-autentica mediante `email__iexact`
  cuando falla la autenticación por nombre de usuario.
- **Recuperación de contraseña**: flujo nativo de Django
  (`PasswordResetView/Done/Confirm/Complete`) con tokens firmados, plantillas
  propias del mismo estilo visual, envío vía `EMAIL_BACKEND` de consola
  (configurable por `.env`) y enlace «¿Olvidó su contraseña?» en el login.
- **Timeout de sesión**: `SESSION_COOKIE_AGE=3600` (1 hora) y
  `SESSION_EXPIRE_AT_BROWSER_CLOSE=True`, ambos configurables por `.env`.
- **Renovación del vencimiento**: al cambiar la contraseña,
  `fecha_vencimiento_password` se renueva a `now + PASSWORD_EXPIRATION_DAYS`
  (180 días por defecto) y se limpia `requiere_cambio_password`.
- **Validadores de Django**: `validate_password` se aplica en
  `CambiarPasswordForm`, en la vista de cambio obligatorio y en
  `UserAccountForm` (cambio administrativo de contraseña).
- **Endurecimiento**: `DEBUG` es `False` por defecto; `SECRET_KEY` sin fallback
  fijo (se exige en `.env` cuando `DEBUG=False`, clave aleatoria sólo en
  desarrollo) y, en producción, HSTS con preload, redirección HTTPS y cookies
  de sesión/CSRF seguras activadas automáticamente.

Pendiente para cierre total: simulacro de restauración de respaldo y parámetros
heredados de bloqueo (`lock_strategy` de Axes queda con valores por defecto).

### 7. Auditoría e historial

> **CORREGIDO en Fase 4 (2026-08-27).** Evidencia: suite de 120 pruebas verdes,
> archivo nuevo `apps/audit/tests_fase4.py`. Cambios aplicados:

- `ORIGEN_CHOICES` incorpora `("SISTEMA", "Sistema / Señales Internas")` y las
  señales usan ese valor en lugar del inválido `SISTEMA_SIGNAL`.
- Nuevo `apps/audit/context.py` (actor e IP en thread-local) y
  `apps/audit/middleware.py` (`ActorAuditMiddleware`, instalado tras
  `AuthenticationMiddleware`). `registrar_evento()` completa actor/IP desde el
  contexto cuando la llamada no los trae explícitos; el valor explícito siempre
  gana. Así las señales registran quién y desde dónde sin duplicar parámetros.
- Cobertura ampliada: `Evaluacion` emite `CREAR_EVALUACION`,
  `ACTUALIZAR_EVALUACION` y `ELIMINAR_EVALUACION`; `Estudiante` conserva
  crear/actualizar/eliminar; `Incidencia` registra `CREAR_INCIDENCIA`.
- Deduplicación señal-vista: se eliminaron los eventos redundantes
  `CREAR_ESTUDIANTE_WEB`, `EDITAR_ESTUDIANTE_WEB`, `CREAR_INCIDENCIA` de la
  vista de listado y `CREAR_EVALUACION` de vista y servicio (la señal es la
  única fuente para esas acciones).
- Inmutabilidad impuesta en el modelo: `AuditEvent.save()` rechaza
  actualizaciones de eventos existentes, `delete()` y
  `AuditEvent.objects.all().delete()` levantan `RuntimeError`.
- Pendiente: el flujo web de restauración histórica (matriz equivalente a
  `versiones` en Rails); `django-simple-history` cubre parcialmente el
  expediente por modelo.

### 8. Mensajería, trabajos y reportes

> **PARCIALMENTE CORREGIDO en Fase 6 (2026-08-27).** Evidencia: suite de 126
> pruebas verdes (`apps/support/tests_fase6.py`).

- Implementado el modelo `support.MensajeUsuario` (equivalente de
  `mensaje_usuarios` de Rails): relación mensaje-usuario con
  `unique_together`, bandera `leido` y `fecha_leido`; migración
  `support.0003_mensajeusuario`.
- `enviar_mensaje_interno()` ahora registra la fila `MensajeUsuario` cuando el
  destinatario es un usuario concreto; los ámbitos (GLOBAL, PERIODO, NIVEL,
  CLASE, SECCION) conservan el GenericFK existente y no crean filas.
- La bandeja incluye mensajes donde el usuario es destinatario vía
  `Q(destinatarios__usuario=request.user)` con `distinct()` y
  `puede_leer_mensaje()` acepta la relación por destinatario, manteniendo la
  denegación para terceros.
- Pruebas nuevas: creación de la fila, destinatario/remitente pueden leer y
  tercero no, visibilidad del mensaje en la bandeja con permiso
  `support.mensajes_ver`, GLOBAL visible sin filas, entrega canónica sin
  depender del correo.

Quedan pendientes para paridad total: Celery/Redis y sustitutos de los cinco
jobs legados, y el golden master de los cuatro generadores XLSX frente a las 14
plantillas AXLSX de Rails.

### 9. Trazabilidad del repositorio

Git sólo sigue `.gitattributes` y `README.md`; la implementación, configuración,
plantillas, pruebas y documentación aparecen como archivos sin seguimiento. Hasta
crear una línea base revisable no se puede atribuir con seguridad un avance a un
commit ni reproducir un hito.

### 10. Documentación y secretos

El documento anterior de acceso contenía contraseñas locales en texto plano. Fue
retirado durante esta reorganización y sustituido por
[`configuracion_local.md`](configuracion_local.md). Si esas credenciales se
reutilizaron fuera del entorno local, deben rotarse.

## Avances reales que sí deben conservarse

- Arquitectura modular de 8 aplicaciones y modelo de usuario personalizado.
- PostgreSQL operativo y migraciones coherentes con los modelos actuales.
- 126 pruebas internas ejecutables y verdes (incluye matriz de permisos por
  ámbito y paridad de clonación).
- Cobertura visual amplia para estructura, personas, calificaciones, soporte,
  reportes, auditoría y administración.
- Uso de `Decimal`, transacciones en servicios relevantes, historial para usuario
  y personas, y bitácora separada.
- Prototipos útiles de conversión YAML Ruby, solvencia externa, XLSX y generación
  de variantes de imagen.

Estos activos reducen trabajo de construcción, pero necesitan endurecimiento y
caracterización antes de considerarse equivalentes.

## Próximo hito recomendado

### Puerta 0 — línea base auditable

- Incorporar a Git la implementación revisada, excluyendo `.env`, base local,
  medios y secretos.
- Fijar versiones exactas y documentar la creación reproducible del entorno.
- Conservar el resultado de pruebas como evidencia del commit base.

### Puerta 1 — seguridad antes de datos reales

- ~~Rediseñar la autorización para denegar por defecto y separar ver, crear, editar,
  eliminar, calificar, consolidar, trasladar y retirar.~~ **Hecho en Fase 1
  (2026-08-25).**
- ~~Filtrar todos los listados por ámbito y comprobar acceso directo a objetos.~~
  **Hecho en Fase 1 (2026-08-25).**
- ~~Crear una matriz negativa/positiva para administrador, personal, docente,
  estudiante y pariente dentro y fuera de su ámbito.~~ **Hecha en Fase 1
  (`PermissionsScopeMatrixTests`); ampliable con estudiante-autologado.**
- ~~Resolver privacidad de mensajes, adjuntos, expedientes e incidencias.~~
  **Mensajes, expedientes e incidencias resueltos en Fase 1; adjuntos genéricos
  pendientes de control propio.**

### Puerta 2 — contrato de paridad académica

- Extraer fixtures de Rails para escalas, tipos de nota, evaluaciones,
  consolidaciones, exámenes, reparaciones, redondeo y reapertura.
- Ejecutar las mismas entradas en Rails y Django; cualquier diferencia bloquea el
  cierre de Fase 2.
- Agregar restricciones de integridad derivadas de `schema.rb` y de las
  validaciones Rails.

### Puerta 3 — ETL y ensayo de corte

- Obtener dump anonimizado/representativo y archivos del legado.
- Definir mapeos de ID, staging, rechazos, reintentos idempotentes, sumas de
  control y conciliación por dominio.
- Ensayar carga completa, delta, reversión y restauración de backup.

### Puerta 4 — operación

- ~~Cerrar los cinco avisos de `check --deploy`.~~ **Cerrado en Fase 3
  (2026-08-27):** con `DEBUG=False` el chequeo no reporta advertencias; falta
  ensayar el despliegue real.
- Probar servidor de aplicación, HTTPS, tareas, correo, backups y restauración.
- Ejecutar aceptación por rol y comparación de reportes antes del corte.

## Criterio para declarar completada la migración

La migración termina cuando, sobre una versión identificable en Git:

1. la matriz de permisos no presenta fugas de ámbito ni de acción;
2. el conjunto dorado académico y los reportes coinciden con Rails o documentan
   diferencias aprobadas;
3. datos, relaciones, archivos, versiones y sucesos concilian contra la fuente;
4. el corte y la reversión se ensayan con éxito;
5. el despliegue no conserva advertencias críticas y la restauración de backups se
   demuestra;
6. usuarios representativos de cada rol completan sus recorridos sin usar acceso
   de superusuario.

Hasta entonces, el término correcto es **prototipo de reimplementación avanzado**,
no sistema migrado completo.

## Fuentes principales revisadas

- Rails: `app/models/ability.rb`, `config/permissions.yml`, `config/routes.rb`,
  `app/models/periodo_lectivo.rb`, `app/models/calificacion.rb`, `app/jobs/`,
  `db/schema.rb`, `db/migrate/`, pruebas y manual de usuario.
- Django: `config/settings.py`, `config/urls.py`, modelos, vistas, servicios,
  migraciones y pruebas de las ocho aplicaciones.
- Antecedentes: [`historico/2026-08-12-plan-migracion.md`](historico/2026-08-12-plan-migracion.md)
  y [`historico/2026-08-22-auditoria-en-proyecto-ruby.md`](historico/2026-08-22-auditoria-en-proyecto-ruby.md).
