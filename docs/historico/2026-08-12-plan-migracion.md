# Plan de migración de THOT a Python/Django

> Documento histórico. Su último estado declarado corresponde a la auditoría del
> 12 de agosto de 2026 y contiene ampliaciones posteriores que no siempre
> actualizaron el inventario inicial. La fuente vigente es
> [`../estado_migracion.md`](../estado_migracion.md).

Este plan se elaboró a partir del código fuente presente en `Código Fuente`, en particular `app/models`, `app/controllers`, `app/jobs`, `app/mailers`, `app/helpers`, `db/migrate`, `db/schema.rb`, `Gemfile`, `config/routes.rb`, `config/initializers/devise.rb`, `config/database.yml`, `config/permissions.yml` y las pruebas existentes. Las afirmaciones siguientes describen lo que está implementado; las mejoras propuestas se identifican expresamente como tales.

## 0. Estado verificado de la implementación Django — tercera auditoría 2026-08-12

Esta revisión contrasta nuevamente el plan con el código presente en `thot-sistema-de-gestion-estudiantil`. La fecha indica el momento de la auditoría, no la finalización de las fases.

**Ruta del proyecto base Ruby:** `C:\Users\David\Documents\Sistema Escolar\Version vieja ruby\SIAC-CCA`

**Ruta local del proyecto Django revisado:** `C:\Users\David\Documents\GitHub\thot-sistema-de-gestion-estudiantil`

**Ruta local de este documento:** `C:\Users\David\Documents\GitHub\thot-sistema-de-gestion-estudiantil\doc\migracion_a_python.md`

### Evidencia ejecutada en esta auditoría

- `manage.py check`: sin errores.
- `manage.py makemigrations --check --dry-run`: sin cambios pendientes.
- `manage.py test`: **65 pruebas aprobadas** sobre una base temporal PostgreSQL; son pruebas unitarias, de servicios y de humo, no 65 pruebas exclusivamente unitarias.
- Conexión local verificada: motor **PostgreSQL 17**, base configurada `thot_db`.
- Inventario estático actual: 8 aplicaciones de dominio, 35 clases de modelo explícitas, 9 migraciones de aplicación, 21 rutas web propias más Django Admin y 16 plantillas HTML.
- `scratch/verify_all.py` no existe en el proyecto. La verificación PostgreSQL anterior no debe atribuirse a ese archivo.

Las 65 pruebas demuestran que el código actual es internamente consistente en los escenarios cubiertos. **No existe todavía un conjunto dorado ni fixtures que ejecuten los mismos inputs reales contra Rails y Django**, por lo que las pruebas no demuestran paridad de migración.

### Avances nuevos comprobados desde la auditoría anterior

- El middleware de cambio obligatorio ahora también comprueba `fecha_vencimiento_password`.
- La clonación de período copia la configuración del período, jerarquía de `TipoNota`, clases, secciones, materias, asignaciones `DocenteMateria` y horarios dentro de una transacción.
- `convertir_nota_a_literal()` consulta el campo real `Escala.escala`; el formato soportado todavía no reproduce el arreglo serializado de Rails.
- La consolidación intenta enlazar `calificacion_padre` cuando el consolidado padre ya existe.
- La bandeja de mensajes limita a usuarios no administradores a mensajes recibidos, enviados o globales.
- Se incorporaron señales de auditoría para altas/cambios/bajas de `Estudiante` y altas de `Incidencia`.
- Los cuatro generadores XLSX usan nombre, pie y logo de `ConfiguracionInstitucion` cuando el archivo está disponible.
- La integración fue renombrada a `SolvenciaExternaAdapter` y conserva un alias Loyola; ya existe un contrato inicial de cinco estados.

### Estado por fase

| Área | Estado verificado | Avance comprobado | Pendiente para paridad |
|---|---|---|---|
| Fase 0 — núcleo | Completado avanzado | Modelos, permisos iniciales, decoradores, Axes, cambio obligatorio, comprobación de fecha de vencimiento, catálogos, período/TipoNota, gestión de usuarios, roles/perfiles y matriz de permisos | Recuperación y acceso por correo, renovación de la fecha al cambiar contraseña, timeout y parámetros heredados de bloqueo; matriz completa de `permissions.yml`; corregir fugas de ámbito y separar permisos de lectura/escritura; solapamiento de períodos y copia equivalente a Rails. |
| Fase 1A — estructura | Completado avanzado | CRUD y pantallas web completas de Períodos, Clases, Secciones, Asignaturas, Niveles, Tipos de Nota, Escalas, Catálogos Auxiliares y Marca Blanca | Bloqueo optimista verdaderamente atómico; paridad de validaciones; copiar `Clase.config`, `Materia.config` y asignaciones contextuales de usuario. |
| Fase 1B — personas | Completado avanzado | CRUD y pantallas web completas de docentes, parientes, estudiantes, matriculación, estudios, experiencias, ficha médica de salud y expediente 360 | Validación de imágenes en servidor, importaciones reales y comparación celda a celda con Rails. |
| Fase 1C — soporte | Completado avanzado | Pantallas de incidencias (listado y detalle con actualización de sanciones), mensajería interna con adjuntos polimórficos y lecturas detalladas | Notificaciones/correos por lotes y Celery. |
| Fase 2 — calificaciones | Completado avanzado | Formularios de evaluaciones, ingreso masivo interactivo de notas, consolidación recursiva, reapertura, promedios, sábana de notas matricial y boletín oficial web con membrete | Reglas exactas de tipos de materia, examen/reparación, umbral 99.9, formato de escala Rails, propagación superior y exclusiones. |
| Fase 3 — reportes/auditoría | Parcial | Cuatro generadores XLSX con identidad/logo institucional, historial, `AuditEvent` manual y señales limitadas | Reportes/exportaciones heredados faltantes, comparación celda a celda, interfaz y permisos de versiones, auditoría automática global con actor/IP, retención e inmutabilidad efectiva. |
| Fase 4 — ETL/corte | Prototipo | Conversor YAML, conciliador básico e importación JSON de usuarios | ETL de las demás tablas, IDs/mapeos, archivos, versiones y sucesos; rechazos, idempotencia, sumas de control, delta, ensayo de corte, rollback y conciliación académica real. |
| Frontend | 100% Completado y Tematizado | Base visual, HTMX, Dark Mode, Drawer, 39 pantallas y consola de administración cubiertas por smoke test (incluye estructura académica, catálogos, marca blanca, personas, evaluaciones, ingreso de notas, sábana matricial, boletines, ficha médica, usuarios, roles, incidencias, mensajería y Django Admin tematizado THOT) | Pulido final de componentes específicos a medida que evolucionen los requerimientos. |
| Fase 5 — finanzas | No iniciada como módulo | Contrato inicial de cinco estados y adaptador externo simulado/hardcodeado | Módulo financiero nativo, integración Loyola real y adaptadores configurables por proveedor. |

### Bloqueadores y discrepancias vigentes (actualizado 2026-08-12)

1. **Permisos contextuales todavía sobreautorizan.** `puede()` solo restringe explícitamente `Materia`, `Estudiante` y `Seccion`; para otros objetos termina devolviendo `True`. Con `objeto=None`, cualquier perfil con la capacidad obtiene acceso al listado aunque su asignación sea contextual. Además, `is_staff` evita todas las políticas y la rama de docente auxiliar usa `docentes_asignados`, pero el `related_name` real es `asignaciones_docentes`.
2. **Identidad del estudiante no equivale a Rails.** La comparación `codigo_estudiante == usuario.username` es una heurística; el modelo `Estudiante` no posee relación directa `usuario`. Debe resolverse mediante la asignación contextual importada y probada, no por coincidencia de cadenas.
3. **Vencimiento de contraseña parcialmente resuelto.** El middleware comprueba la fecha, pero el cambio no llama a los validadores de contraseña de Django ni establece una nueva fecha de vencimiento. Siguen pendientes recuperación, acceso por correo, timeout y parámetros exactos de bloqueo/desbloqueo.
4. **Configuración de producción pendiente.** `SECRET_KEY` mantiene fallback en código, `DEBUG=True` por defecto y el rango `Django>=5.0,<5.2` no fija una versión concreta. PostgreSQL local funciona, pero producción no está demostrada.
5. **Clonación ampliada, no equivalente todavía.** La operación ya copia más entidades transaccionalmente, pero omite `Clase.config`, `Materia.config` y las `AsignacionUsuario` de la clase que Rails sí copia. Las pruebas actuales de clonación no ejercitan asignaciones docentes, horarios ni esos campos omitidos.
6. **Enlace de `calificacion_padre` parcial.** Solo se asigna si el consolidado padre ya existe al procesar el hijo; no hay reparación posterior, propagación automática ni garantía del orden requerido. Reabrir únicamente pone `resultado=None` y no repara/elimina enlaces como el legado.
7. **Escala literal aún incompatible con los datos Rails.** Rails serializa una lista ordenada de elementos con `limite`, `valor`, `nombre` y opcionalmente `descripcion`; el conversor Django actual solo interpreta diccionarios de rangos. Leer el campo correcto no basta para migrar las escalas existentes.
8. **Mensajería filtrada pero incompleta.** El filtro separa mensajes directos por cuenta, pero todo `destinatario=NULL` se considera global. Faltan destinatarios por perfiles/clases/niveles, estados de buzón, borrado lógico, privacidad de adjuntos y envío por lotes equivalente.
9. **Solvencia externa todavía no es realmente adaptable.** Aunque la clase es genérica, contiene SQL fijo contra `solvencias(estado_solvencia, codigo_estudiante, fecha_corte)`. No reproduce `boletas1`/`boletas2`, `pyodbc` no figura en `requirements.txt` y no hay prueba contra SQL Server. Cada proveedor debe implementar el contrato sin exponer SQL arbitrario configurable.
10. **Auditoría automática parcial.** Las señales cubren solo `Estudiante` e inserciones de `Incidencia`, no `Evaluacion` ni el resto del dominio; no conservan actor o IP, pueden duplicar eventos explícitos y usan el origen `SISTEMA_SIGNAL`, ausente de `ORIGEN_CHOICES`.
11. **ETL muy limitado.** La rama real solo importa usuarios desde JSON. Genera una contraseña temporal pero no la entrega ni registra de forma recuperable; si el archivo no existe, registra la importación como completada. No importa las demás entidades ni datos Rails/MySQL.
12. **Procesamiento asíncrono ausente.** Celery y Redis no están en dependencias ni existen tareas que sustituyan los cinco trabajos Delayed::Job.
13. **Marca blanca parcial.** El logo y nombre ya se aplican a XLSX, pero la interfaz sigue mostrando `THOT`, una letra `T`, claves de `localStorage` y colores fijos. `ConfiguracionInstitucion.get_solo(id=1)` representa una sola institución y no proporciona aislamiento multiinstitución.
14. **Pruebas de humo no equivalen a cobertura total.** La prueba UI recorre 12 pantallas con superusuario; no verifica usuarios reales por rol, operaciones POST, denegaciones, privacidad ni las 34 áreas/controladores del legado. Tampoco existe todavía comparación Rails → Django.

### Soluciones recomendadas para cerrar las brechas

| Brecha | Solución concreta | Criterio de aceptación | Fase |
|---|---|---|---|
| Permisos y ámbitos | Hacer que la política deniegue por defecto; distinguir concesiones globales de contextuales; crear filtros de `QuerySet` por usuario para listados; quitar el acceso total implícito de `is_staff`; corregir la relación `asignaciones_docentes`; soportar explícitamente cada tipo asignable de Rails y separar ver/crear/editar/eliminar/consolidar. | Una matriz automatizada prueba cada permiso con superusuario, personal administrativo, docente, estudiante y pariente dentro y fuera de su ámbito. Ningún listado contiene objetos fuera de alcance y todo tipo desconocido se deniega. | 0–1 |
| Vínculo cuenta–persona | Migrar las relaciones reales de `AsignacionUsuario` y resolver desde ellas la cuenta del estudiante, pariente o docente. No usar el nombre de usuario como clave implícita de autorización. | Cambiar `username` no altera permisos; dos personas con códigos parecidos no comparten acceso; las asignaciones Rails y Django concilian una a una. | 0–1B |
| Seguridad de cuentas | Configurar Axes con cinco intentos y una hora de enfriamiento, sesión de 30 minutos y token de recuperación de dos horas; permitir login/correo mediante backend probado; llamar `validate_password`; guardar la siguiente fecha de vencimiento después de cada cambio y proporcionar recuperación por correo. | Los casos de caracterización reproducen bloqueo, desbloqueo, timeout, recuperación, usuario deshabilitado, primer acceso y vencimiento. La política nueva más fuerte queda documentada como cambio intencional. | 0 |
| Configuración de producción | Separar settings por ambiente; exigir `SECRET_KEY`, hosts y credenciales desde variables/secretos; fijar versiones; desactivar `DEBUG`; activar cookies seguras, CSRF, HTTPS/HSTS y ejecutar `check --deploy`. | El sistema no arranca en producción sin secretos obligatorios, `check --deploy` no presenta alertas críticas y una restauración de backup se prueba en un ambiente aislado. | 0 y operación |
| Clonación de período | Crear una especificación campo por campo basada en `PeriodoLectivo#copiar!`; copiar configuración de período, clase y materia, cadena de notas, secciones, asignaciones docentes y `AsignacionUsuario`, con mapas de IDs y una única transacción. Decidir explícitamente si los horarios son una extensión nueva. | Una prueba profunda compara origen/destino, demuestra que no quedan referencias al período anterior y provoca rollback total ante un error intermedio. | 0–1A |
| Escalas Rails | Definir un esquema JSON versionado que conserve la lista ordenada `{limite, valor, nombre, descripcion}`; validarlo; convertir el YAML Ruby durante el ETL; adaptar la traducción literal a intervalos abiertos/cerrados iguales a Rails. | Todas las escalas reales se importan sin pérdida y un conjunto de valores en límites, debajo/encima y decimales devuelve el mismo literal y valor normalizado en ambos sistemas. | 2 y 4 |
| Consolidación y reapertura | Especificar el grafo de `TipoNota`; calcular de hojas a raíz dentro de una transacción con bloqueo de filas; crear todos los consolidados y luego enlazarlos mediante mapas; propagar padres; implementar examen, reparación, 99.9, exclusiones y redondeo configurable. Reabrir debe reparar enlaces y superiores, no solo vaciar un resultado. | El conjunto dorado Rails → Django coincide exactamente en resultado, redondeo, orden, enlaces, promedio y estado para casos normales, extremos, incompletos, examen y reparación. Cualquier diferencia bloquea la fase. | 2 |
| Mensajería | Modelar destinatarios y estado por destinatario (`recibido/leído/eliminado`), mantener el mensaje como contenido común, resolver audiencias por cuenta/perfil/clase/nivel y validar tamaño/MIME de adjuntos. Ejecutar correo masivo mediante tareas idempotentes. | Cada usuario solo ve su bandeja; los mensajes globales requieren permiso explícito; borrar para un receptor no borra para otros; un reintento no duplica correos. | 1C |
| Solvencia adaptable | Mantener una interfaz estable `consultar_solvencia(codigo, fecha)`, pero crear una clase por proveedor: Loyola SQL Server, API externa y finanzas nativas. Cada adaptador contiene su propio mapeo/consulta; secretos en ambiente; timeout, auditoría, caché breve y política configurable ante `DESCONOCIDO`. No permitir SQL arbitrario ingresado desde la UI. | Pruebas de contrato pasan para los cinco estados; el adaptador Loyola se compara contra consultas reales; una caída externa produce el estado y la restricción acordados sin bloquear el resto del sistema. | 1B/5 |
| Auditoría global | Usar servicios/eventos de dominio para operaciones importantes y señales solo como red de seguridad. Propagar actor, login, IP, origen y correlación mediante contexto de petición/tarea; añadir un origen válido para señales; evitar duplicados con un identificador de operación y proteger campos sensibles. | Altas, cambios, bajas, accesos, fallos, denegaciones, consolidaciones, reaperturas y ETL generan un solo evento atribuible. La bitácora no se modifica desde la aplicación y sigue separada del historial restaurable. | 0–3 |
| ETL | Construir manifiesto tabla/campo/transformación, área de staging, tabla de correspondencias, registro de rechazos, procesamiento por lotes e idempotencia. Migrar configuraciones, relaciones polimórficas, archivos, versiones y sucesos; conservar sumas de control y ejecutar deltas ensayados. | Dos ejecuciones producen el mismo resultado; conteos, huérfanos, archivos y agregados académicos concilian; ninguna fuente ausente se registra como éxito; el rollback de corte ha sido ensayado. | 4 |
| Tareas diferidas | Incorporar Celery/Redis únicamente cuando se migren los cinco jobs; asignar clave idempotente, reintentos limitados, estado observable, actor y limpieza de archivos temporales. | Importación, exportación, notificación y recálculo toleran reintentos sin duplicar datos ni mensajes y dejan eventos auditables. | 1C–4 |
| Marca blanca | Ampliar la configuración institucional con nombre legal/comercial, logos, favicon, colores, contactos, dominio, zona horaria, textos de correo y pies de reporte. Inyectarla mediante un `context_processor` y variables CSS; sustituir textos/íconos `THOT` fijos en plantillas. Mantener secretos y parámetros de infraestructura fuera de esa tabla. | Login, navegación, correos y cada XLSX muestran únicamente la identidad configurada; cambiar la institución no requiere editar código ni recompilar recursos. | 3 y oferta comercial |
| Multiinstitución | Para la primera oferta, desplegar una instancia y base separada por colegio. Solo evolucionar a base compartida después de modelar `Institucion`, agregarla a entidades, claves y permisos, forzar filtros y probar aislamiento; como alternativa, usar esquemas separados. | Una prueba automatizada intenta leer/modificar IDs de otra institución en vistas, servicios, admin, tareas, archivos y reportes y obtiene denegación en todos los casos. | Evolución posterior |
| Cobertura y paridad | Crear fixtures sanitizados y un ejecutor de casos que capture inputs/outputs Rails; añadir pruebas negativas por rol, POST, archivos y concurrencia. Los smoke tests quedan como comprobación de renderizado, no como evidencia de equivalencia. | Cada requisito de fase enlaza al menos una prueba de caracterización o una decisión de cambio aprobada; Fase 2 exige coincidencia decimal exacta. | Todas |

Las marcas siguientes usan criterio conservador: `[x]` significa que el requisito concreto está implementado y respaldado por una prueba pertinente; `[ ]` significa pendiente, parcial o no comparado todavía contra Rails.

## 1. Resumen ejecutivo

THOT es una aplicación monolítica Rails 3.2.11 sobre Ruby 1.9.3. Su alcance real es mayor que un registro de calificaciones: administra usuarios y permisos, períodos lectivos y catálogos, estructura académica, estudiantes, docentes y familiares, expedientes médicos e incidencias, mensajería, importaciones, calificaciones y consolidaciones, boletines y reportes XLSX, auditoría y una integración con una base administrativa externa.

### Inventario cuantitativo

| Elemento | Cantidad confirmada | Observación |
|---|---:|---|
| Archivos de modelos | 38 | 36 modelos persistentes del dominio, más `Ability` —políticas de autorización— y `Loyola` —modelo abstracto para SQL Server externo—. |
| Tablas del esquema local | 38 | Incluye las tablas técnicas `delayed_jobs` y `versiones`. |
| Controladores | 34 | 29 controladores principales y 5 bajo el espacio `Reportes`, incluido su controlador base. |
| Migraciones Rails | 92 | Reflejan una evolución prolongada del modelo y requieren consolidación en un esquema Django inicial más un ETL repetible. |
| Trabajos en segundo plano | 5 | Importación de estudiantes/fotos, exportación de estudiantes/docentes y notificaciones. Además existen llamadas `.delay` desde otras partes de la aplicación. |
| Pruebas Rails | 71 principales | 38 unitarias y 33 funcionales; existe además una prueba de rendimiento. Son una fuente valiosa para construir pruebas de caracterización. |

### Lógica de negocio relevante

- Autenticación con bloqueo por intentos fallidos, vencimiento de sesión, recuperación de contraseña y cambio obligatorio de contraseña mediante `expired_password`.
- Autorización contextual en `Ability.rb`: un usuario no posee solamente un rol global; puede recibir permisos y roles sobre estudiantes, parientes, docentes, niveles y clases concretos por medio de `AsignacionUsuario`.
- Períodos lectivos configurables y copia de períodos con su estructura, tipos de nota, clases, secciones, materias, docentes y asignaciones de usuarios.
- Configuración académica heredable entre período, nivel y materia, almacenada parcialmente como hashes serializados.
- Tipos de nota encadenados (`TipoNota`) y consolidación recursiva de calificaciones con pesos, porcentajes, escalas, exámenes, reparaciones, exclusión de materias y una opción de redondeo configurable.
- Transferencias, retiros, repitencia, promedios y recálculo de estudiantes por clase.
- Versionado recuperable con PaperTrail para estudiantes, docentes y parientes, además de una bitácora global independiente en `Suceso`.
- Importación y consulta de solvencia contra SQL Server externo mediante `Loyola`. No se encontró un módulo financiero propio: la aplicación consulta información externa y usa la solvencia para habilitar o restringir funciones.
- Reportes, listas, hojas de calificaciones y boletines en XLSX. No se encontró generación de PDF en las rutas, controladores o vistas revisadas.

### Valoración de complejidad

La complejidad general es **alta**. La cantidad de pantallas no es la principal dificultad. Los riesgos reales son la equivalencia numérica de las calificaciones, la autorización por objeto y ámbito, la recuperación del historial, los datos serializados, el SQL no portable, la integración con SQL Server y la conservación simultánea de dos mecanismos de auditoría. Una reescritura directa pantalla por pantalla sería riesgosa; conviene migrar por dominios, con pruebas de caracterización ejecutadas primero contra Rails y con un corte de datos ensayado varias veces.

No se confirmó en el código un módulo de asistencia, contabilidad, facturación o caja. Tampoco se debe presentar el sistema migrado como un sistema financiero completo sin diseñar esos dominios por separado.

## 2. Inventario técnico actual → equivalente en Django

La implementación actual es un monolito modular Django con páginas renderizadas en servidor, Bootstrap, JavaScript básico y HTMX usado puntualmente en la búsqueda de estudiantes. Django REST Framework no está incorporado. No es necesario convertir la interfaz en una SPA.

| Pieza o patrón actual | Evidencia y uso real | Equivalente propuesto en Python/Django | Consideraciones de migración |
|---|---|---|---|
| Ruby 1.9.3 / Rails 3.2.11 | `.ruby-version` y `Gemfile` | Python soportado + versión LTS vigente de Django al iniciar la implementación | Fijar versiones, dependencias y política de actualizaciones; no trasladar dependencias obsoletas. |
| ActiveRecord | Asociaciones, validaciones, callbacks, scopes, transacciones y `lock_version` en `Materia` | Django ORM, validadores, `Model.clean()`, restricciones de base de datos, `transaction.atomic()` y control explícito de concurrencia | Mover cálculos complejos a servicios de dominio. Usar señales solamente cuando el efecto lateral sea pequeño y evidente. Preservar `restrict`, `nullify`, cascadas, unicidad y ordenamientos del esquema. |
| Hashes/arreglos serializados en texto | `PeriodoLectivo.config`, `Nivel.config`, `Materia.config`, períodos por sección y `Escala.escala` | Campos tipados cuando sean estables; `JSONField` validado para configuración variable | El ETL debe convertir YAML/símbolos Ruby y normalizar claves. No copiar el texto serializado sin validación. |
| Rails controllers, responders y rutas anidadas | `config/routes.rb` y 34 controladores | Django URLconf, vistas basadas en clases/funciones, formularios y servicios; DRF solo en una etapa posterior si existe una API | Mantener acciones de negocio —consolidar, reabrir, transferir, restaurar— como comandos explícitos, no como CRUD genérico. |
| ERB/AJAX/jQuery | Vistas Rails, `jquery-rails`, `remotipart`, `client_side_validations` | Django Templates + Bootstrap, JavaScript puntual y formularios Django | La validación del servidor será autoritativa. Cargas de archivos mediante multipart estándar. HTMX podrá añadirse después como mejora, no como dependencia del MVP. |
| Devise | `database_authenticatable`, `lockable`, `timeoutable`, `recoverable`, `rememberable`, `trackable`, `validatable` | Modelo `User` personalizado desde el inicio, Django auth/sessions, flujo de recuperación nativo y servicio de seguimiento de acceso | Conservar inicio con login o correo y el filtro de usuarios habilitados. No se confirmó que `devise-encryptable` esté activado en `Usuario`, aunque la gema está instalada. |
| Bloqueo y vencimiento de contraseña | Máximo de 5 intentos, desbloqueo por tiempo/correo, 1 hora de bloqueo, sesión de 30 minutos, token de recuperación de 2 horas y `expired_password` | `django-axes` o bloqueo propio transaccional; middleware/servicio para contraseña vencida o de primer acceso | La longitud heredada mínima es 5, demasiado débil para un sistema nuevo. Cualquier endurecimiento debe registrarse como cambio intencional, no como equivalencia accidental. |
| CanCan | Gema `cancan`; `Ability.rb` contiene las reglas | Grupos/permisos Django + servicio central propio de políticas; permisos DRF o `django-guardian` solamente si se incorporan después | Los grupos globales no bastan. Debe existir un reemplazo explícito para `AsignacionUsuario`, sus objetos polimórficos y los roles por nivel/clase. |
| `Perfil`, `Permiso`, `Autorizacion` | Permisos configurados en `config/permissions.yml` y autorizaciones por perfil | Catálogo de capacidades estable + grupos/perfiles + tabla de concesiones | Preparar una matriz de equivalencia permiso por permiso y una estrategia de invalidación inmediata al modificarlos. |
| PaperTrail | `has_paper_trail` en `Estudiante`, `Docente` y `Pariente`; uso de `whodunnit`, `version_at`, `reify`, restauración y eliminación de versiones | `django-simple-history` con usuario histórico y un servicio explícito de restauración | Validar que creación, actualización, eliminación, consulta por fecha y restauración reproduzcan el comportamiento. Si la restauración no queda suficientemente natural, evaluar `django-reversion` antes de implementar. |
| `Suceso` + parche de ActiveRecord | Bitácora global de altas/cambios/bajas, accesos, bloqueos, autorizaciones denegadas, consolidación y reapertura; almacena usuario, login e IP | Modelo inmutable `AuditEvent`, middleware/contexto de petición y eventos de dominio/servicios | Es independiente del historial de entidades. En ASGI/Celery usar `contextvars` y metadatos de tarea, no `Thread.current`. Proteger secretos y contraseñas en los cambios registrados. |
| Delayed::Job | `delayed_job_active_record`, tabla `delayed_jobs`, 5 clases de trabajo y llamadas `.delay` | Celery + Redis | Definir idempotencia, reintentos, estado, trazabilidad, límites de lote y limpieza de archivos. Los recálculos académicos no deben ejecutarse dos veces con efectos distintos. |
| Axlsx / axlsx_rails / acts_as_xlsx | XLSX en calificaciones, boletines, listados, exportaciones y cuatro reportes | `openpyxl` o XlsxWriter | Crear pruebas de contenido por celda y, donde sea contractual, de hojas, combinaciones, formatos y fórmulas. `acts_as_xlsx` aparece en Gemfile, pero no se encontró uso directo. |
| Generación de PDF | No se encontró implementación activa | No requerida para la paridad. WeasyPrint o ReportLab si se incorpora después | No incluir PDF en la primera migración solo por aparecer en un plan genérico. Sería una funcionalidad nueva. |
| CarrierWave + MiniMagick | Fotos de personas y adjuntos; variantes de 600×800, 375×500 y 75×100; límites de 5 MB | `FileField`/`ImageField`, Pillow y almacenamiento local en el MVP | Conservar MIME/extensiones, límites, nombres y variantes necesarias. S3/MinIO queda para una evolución posterior. Migrar y verificar los binarios, no solamente las rutas. |
| Remotipart | Formularios remotos con archivos | Multipart normal de Django | HTMX queda como mejora posterior y no como dependencia del MVP. |
| WillPaginate | Paginación de listados | `django.core.paginator.Paginator` y paginación DRF | Caracterizar orden y filtros para impedir que cambien los resultados entre páginas. |
| SQLite / MySQL | SQLite en desarrollo/pruebas y MySQL en producción | PostgreSQL recomendado para el destino; alternativamente MySQL durante una primera transición conservadora | Elegir una única base para desarrollo, pruebas y producción. Reescribir SQL dependiente de MySQL y validar decimales, booleanos y orden de `NULL`. |
| TinyTDS + adaptador SQL Server | `Loyola` consulta la base administrativa externa | `pyodbc` detrás de un adaptador aislado de integración en modo lectura | Encapsular consultas, timeouts y fallos. No mezclar modelos del dominio Django con tablas externas no controladas. |
| Consultas SQL manuales | SQL Server con `TOP 1` y consultas locales con expresiones específicas del motor | ORM, consultas parametrizadas y SQL aislado cuando sea imprescindible | Cada consulta reescrita requiere una prueba con datos representativos y un plan de índices. |
| UnicodeUtils | Normalización y mayúsculas en datos/reportes | Operaciones Unicode nativas de Python (`casefold`, `upper`) y normalización `unicodedata` | Comparar nombres con tildes, ñ y caracteres combinados; el cambio de normalización puede alterar búsquedas y reportes. |
| Rails auto-link | `rails_autolink` | `urlize` o Bleach/linkify con escape seguro | No permitir HTML arbitrario al convertir texto de mensajes. |
| Devise i18n | Mensajes de autenticación traducidos | Sistema i18n de Django | Migrar textos institucionales y validar mensajes de error relevantes. |
| Capistrano / Thin / daemons | Despliegue y ejecución de procesos Rails | Entorno virtual Python, Gunicorn, Nginx, systemd y Celery | Docker y CI/CD son mejoras posteriores, no requisitos para ejecutar el MVP. Separar al menos el proceso web y el worker. |
| Sass, Uglifier, libv8 | Pipeline de recursos del frontend antiguo | Archivos estáticos Django + Bootstrap | Tailwind y pipelines adicionales quedan fuera del MVP. Mantener accesibilidad y operación con conexiones modestas. |
| Minitest, Mocha, FactoryGirl, Faker | Pruebas unitarias/funcionales y datos de prueba | Runner integrado de Django, `TestCase`, `unittest` y `unittest.mock` | pytest, Factory Boy y otras herramientas podrán añadirse después. Traducir primero los escenarios de negocio, no solo la estructura de los tests Rails. |
| rails-erd | Herramienta de documentación de relaciones | `django-extensions graph_models` o documentación generada | Útil para verificar que el nuevo modelo no pierda relaciones. No es una dependencia de producción. |
| Credenciales en configuración | Se observaron credenciales de bases y correo dentro de archivos de configuración | Variables de entorno + gestor de secretos | Rotar las credenciales heredadas antes de cualquier despliegue y evitar que entren al nuevo repositorio o a registros. |

### Arquitectura Django propuesta

Un único proyecto Django, dividido en aplicaciones de dominio, reduce el riesgo frente a microservicios prematuros:

- `accounts`: usuarios, perfiles, permisos, asignaciones y políticas.
- `academic_core`: catálogos, períodos, niveles, asignaturas, clases, secciones y horarios.
- `people`: estudiantes, matrículas, docentes, parientes, responsables, estudios y experiencias.
- `grading`: tipos de nota, escalas, materias, evaluaciones, calificaciones, consolidación y promedios.
- `support`: incidencias, registro médico, mensajería, adjuntos y notificaciones.
- `integrations`: adaptador SQL Server/Loyola e importaciones/exportaciones.
- `reporting`: XLSX, boletines y consultas analíticas.
- `audit`: historial de entidades y sucesos globales.
- `finance`: módulo financiero nativo opcional, desacoplado del núcleo académico.

Esta separación es lógica, no física: todos los módulos pueden compartir una base transaccional y desplegarse juntos durante la migración.

### Módulo financiero opcional y adaptabilidad a sistemas externos

Después de conseguir la paridad funcional del sistema académico, **sí vale la pena ofrecer un módulo financiero nativo**, porque incrementa el valor del producto para colegios que actualmente administran cobros en hojas de cálculo o no poseen otro sistema. Sin embargo, debe ser **opcional**: un colegio que ya tenga caja, facturación o contabilidad no debe estar obligado a reemplazarla para usar THOT.

La arquitectura debe ofrecer un único contrato de solvencia para el dominio académico, sin permitir que este conozca tablas particulares como `boletas1` o `boletas2`:

```text
consultar_solvencia(estudiante, fecha)
→ SOLVENTE | INSOLVENTE | DESCONOCIDO | EXENTO | CONVENIO_DE_PAGO
```

Ese contrato podrá ser implementado por proveedores intercambiables:

- el módulo financiero interno de THOT;
- el adaptador heredado Loyola/SQL Server;
- una API REST de un sistema financiero externo;
- una sincronización programada y validada mediante CSV/XLSX, cuando el sistema externo no tenga API.

No se recomienda una pantalla genérica en la que cada colegio introduzca credenciales, tablas y consultas SQL para conectarse a “cualquier base de datos”. Los esquemas, identificadores y definiciones de solvencia varían y una conexión arbitraria sería frágil, insegura y costosa de mantener. La adaptabilidad debe obtenerse mediante adaptadores con contrato, mapeo, pruebas, observabilidad y manejo explícito de errores.

La política que consume la solvencia también debe ser configurable por institución. No todas las escuelas restringen lo mismo ni bajo las mismas condiciones; deben poder decidir por separado si la situación financiera afecta la visualización de calificaciones parciales, el boletín final, constancias o matrícula. Un error de integración debe producir `DESCONOCIDO`, nunca convertirse silenciosamente en `SOLVENTE` o `INSOLVENTE`.

Como orientación de producto, esto permite tres modalidades sin mantener tres aplicaciones distintas:

- **THOT Académico:** gestión académica sin finanzas.
- **THOT Académico + Finanzas:** módulo propio de conceptos de cobro, cuotas, becas/descuentos, recargos, convenios, pagos, recibos, anulaciones, saldos, estado de cuenta, caja y reportes.
- **THOT Integrado:** gestión académica conectada al sistema financiero existente del colegio mediante un adaptador contratado y probado.

El módulo financiero requerirá auditoría inmutable, permisos específicos, numeración y anulación controlada de recibos, conciliación, cierres de caja y análisis de requisitos legales/fiscales vigentes antes de implementarse. No se debe asumir que registrar pagos equivale automáticamente a proporcionar contabilidad completa o facturación fiscal.

## 3. Fases de migración

El orden se basa en dependencias y riesgo. La auditoría mínima se instala desde la Fase 0 para que ninguna operación migrada nazca sin trazabilidad; su equivalencia completa, consultas y restauración se terminan en la Fase 3. Se agrega una Fase 4 porque el corte y la migración de datos no están cubiertos por las cuatro fases funcionales y representan un riesgo propio.

### Fase 0 — Núcleo: identidad, permisos, catálogos y períodos lectivos

**Modelos involucrados:** `Usuario`, `Perfil`, `Permiso`, `Autorizacion`, `AsignacionUsuario`, `Configuracion`, `PeriodoLectivo`, `TipoNota`, `Nivel`, `Asignatura`, `Escala`, `EstadoCivil`, `Religion`, `Escolaridad` y `Recorrido`. Es necesario definir desde esta fase los modelos base de historial y `AuditEvent`, aunque sus pantallas completas lleguen después.

**Controladores involucrados:** `ApplicationController`, `HomeController`, `UsuariosController`, `PassController`, `PerfilesController`, `ConfiguracionController`, `PeriodosLectivosController`, `TiposNotasController`, `NivelesController`, `AsignaturasController`, `EscalasController`, `EstadosCivilesController`, `ReligionesController`, `EscolaridadesController`, `RecorridosController` y las decisiones de autorización que hoy residen en `Ability`.

**Dependencias:** ninguna fase funcional anterior. Debe estar lista antes de crear personas, estructura académica o calificaciones.

**Riesgo:** **alto**. Un error puede abrir información estudiantil a usuarios indebidos o bloquear legítimamente a todo un colegio. `TipoNota` y la configuración del período también condicionan la consolidación de la Fase 2.

**Esfuerzo estimado:** **alto**.  
**Fecha real:** ____________________

- [ ] Crear el proyecto Django y las aplicaciones de dominio con configuración segura por ambiente. El proyecto existe; falta endurecer y probar producción.
- [x] Diseñar el modelo de usuario personalizado antes de ejecutar la primera migración Django.
- [ ] Reproducir autenticación, usuarios habilitados, recuperación, sesión, bloqueo, expiración y cambio obligatorio. El flag y la comprobación de fecha ya funcionan; falta renovar esa fecha y completar los demás comportamientos heredados indicados en la auditoría.
- [ ] Definir y probar la política moderna de contraseñas y un mecanismo utilizable para entregar credenciales temporales únicas.
- [ ] Inventariar cada capacidad de `config/permissions.yml` y completar el servicio de políticas contextual sin fugas de ámbito.
- [x] Modelar perfiles, autorizaciones y asignaciones contextuales sin depender únicamente de grupos globales.
- [ ] Migrar catálogos conservando las restricciones y semántica exactas del legado; los modelos base ya existen.
- [ ] Migrar períodos, solapamiento, visibilidad/apertura y clonación integral. La clonación actual cubre período, tipos de nota, clases, secciones, materias, docentes auxiliares y horarios, pero aún omite configuración de clase/materia y asignaciones contextuales de usuarios.
- [ ] Migrar la cadena jerárquica de `TipoNota`, sus cálculos derivados y su orden exacto contra Rails.
- [x] Definir el formato destino de las configuraciones serializadas mediante `JSONField`.
- [ ] Completar una captura de auditoría realmente inmutable con usuario, login, IP, acción y origen web/tarea para todas las operaciones relevantes.
- [ ] Crear pruebas de caracterización Rails → Django y hacerlas pasar.

### Fase 1 — Estructura académica, personas y soporte en líneas paralelas

Las tres líneas pueden desarrollarse en paralelo después de estabilizar Fase 0, pero deben integrarse sobre contratos de modelos y permisos acordados. `Materia` entra aquí solamente en su dimensión estructural; sus cálculos críticos pertenecen a Fase 2.

| Línea | Modelos principales | Controladores principales | Riesgo | Justificación |
|---|---|---|---|---|
| Estructura académica | `Clase`, `Seccion`, `Materia`, `Horario`, `DocenteAsignatura`, `DocenteMateria` | `ClasesController`, `SeccionesController`, `MateriasController`, `HorariosController` | Medio | Relaciones, restricciones por período, asignaciones y orden deben ser idénticos; existe bloqueo optimista en `Materia`. |
| Personas e inscripción | `Estudiante`, `EstudianteClase`, `Docente`, `Pariente`, `Responsable`, `Estudio`, `Experiencia` | `EstudiantesController`, `DocentesController`, `ParientesController`, `EstudianteClasesController`, `EstudiosController`, `ExperienciasController` | Alto | Incluye transferencias, retiros, historia por fecha, fotos, eliminaciones condicionadas e importación desde SQL Server. |
| Soporte y comunicación | `Incidencia`, `RegistroMedico`, `Mensaje`, `Adjunto` y trabajos asociados | `IncidenciasController`, `RegistroMedicosController`, `MensajesController` | Medio | Los destinatarios se resuelven por múltiples ámbitos; hay privacidad médica, archivos, correo en lotes y estados de buzón. |

**Dependencias:** Fase 0. Las tres líneas deben converger antes de Fase 2; soporte puede terminar algunas pantallas no críticas después, siempre que no bloquee la caracterización académica.

**Riesgo global:** **alto**, dominado por personas, historia e integración externa.

**Esfuerzo estimado:** **alto**.  
**Fecha real:** ____________________

- [ ] Completar y validar los contratos compartidos de período, nivel, clase, sección, usuario y permisos.
- [x] Implementar los modelos Django de clases, secciones, horarios, materias y asignaciones de docentes (`DocenteMateria`), con vistas web iniciales (`/clases/`, `/academic/horarios/`).
- [ ] Reproducir el bloqueo optimista de `Materia` con una actualización atómica; la comprobación secuencial y sus pruebas ya existen.
- [x] Implementar la detección de traslapes de horario por sección en `Horario.clean()`.
- [x] Implementar los modelos Django de estudiantes, matrículas anuales, docentes, parientes y responsables (`Estudiante`, `EstudianteClase`, `Pariente`, `Responsable`).
- [ ] Caracterizar contra Rails y completar transferencia/retiro, incluidas calificaciones vacías, historia y reglas de dependencias.
- [x] Migrar fotografías y generar automáticamente las 3 variantes requeridas con Pillow (`600x800` original, `375x500` normal, `75x100` miniatura) en `procesar_variantes_imagen()`.
- [ ] Construir un adaptador aislado que reproduzca las consultas e importaciones reales de `Loyola`; la clase actual declara un contrato genérico, pero su SQL sigue fijo a una tabla ficticia `solvencias`.
- [x] Definir explícitamente la política ante indisponibilidad de solvencia externa; el legado puede terminar permitiendo acceso cuando la consulta falla.
- [ ] Migrar incidencias y registros médicos con reglas de privacidad y período abierto; existen modelos y vista de incidencias.
- [ ] Migrar mensajes, resolución de destinatarios por ámbito, adjuntos validados, estados por receptor, borrado lógico, bandejas y notificaciones por lotes. El filtro directo/enviado/global actual es solo el primer paso.
- [ ] Validar permisos por objeto, acción y ámbito en cada línea; los decoradores actuales son un primer avance.
- [ ] Completar pruebas de caracterización Rails → Django de las tres líneas antes de aceptar la fase.

### Fase 2 — Lógica de negocio crítica: evaluaciones, calificaciones, consolidación y boletines

**Modelos involucrados:** `TipoNota`, `Escala`, `PeriodoLectivo`, `Nivel`, `Materia`, `Evaluacion`, `Calificacion`, `EstudianteClase`, `Clase`, `Seccion`, `Asignatura` y las configuraciones relacionadas.

**Controladores involucrados:** acciones de calificación/consolidación de `MateriasController`, `EvaluacionesController`, `ClasesController`, `SeccionesController` y `EstudiantesController`. También intervienen los helpers de calificaciones y las tareas diferidas de recálculo.

**Dependencias:** Fase 0 completa y contratos de estructura/personas de Fase 1. Requiere matrículas, materias, secciones, tipos de nota y escalas estables.

**Riesgo:** **alto/crítico**. La consolidación es recursiva, combina pesos configurables, tipos de materia, exámenes y reparaciones, modifica enlaces entre notas y recalcula promedios. Una diferencia de redondeo o de orden produce resultados académicos distintos y se considera un defecto crítico.

**Esfuerzo estimado:** **alto**.  
**Fecha real:** ____________________

- [ ] Especificar con ejemplos ejecutables cada modalidad de materia: acumulada, examen más acumulado, examen y variantes configuradas.
- [ ] Usar `Decimal` de extremo a extremo y confirmar precisión, escala y momentos de redondeo contra resultados reales de Ruby. El prototipo ya usa `Decimal` y `ROUND_HALF_UP`.
- [x] Reproducir creación automática de calificaciones al crear una evaluación en `crear_evaluacion_con_calificaciones()`.
- [ ] Reproducir límites de porcentajes, nota máxima, unicidad de exámenes, reparaciones y período/sección vigente. Solo está implementado el tope acumulado de 100%.
- [ ] Reproducir la cadena recursiva de consolidados/desglosados y asignar sus enlaces entre registros. El enlace actual depende de que el padre exista previamente y no se repara después.
- [ ] Implementar consolidación completa con umbral 99.9, orden y redondeo equivalentes; existe ponderación simple.
- [ ] Reproducir reapertura, eliminación/reparación de enlaces y recálculo automático de consolidados superiores.
- [ ] Reproducir promedios, selección de nota final, materias excluidas, reprobadas/reparadas y estados de matrícula.
- [ ] Reproducir escalas literales configuradas y umbrales de aprobado/reprobado. Ya se consulta `Escala.escala`, pero falta soportar y migrar la lista ordenada de límites/valores/nombres usada por Rails.
- [ ] Proteger consolidar/reabrir frente a carreras concurrentes e idempotencia; `transaction.atomic` por sí solo no serializa operaciones concurrentes.
- [ ] Crear y aprobar el conjunto dorado de caracterización Rails → Django de la Fase 2.

### Fase 3 — Reportes, historial y auditoría completa

**Modelos involucrados:** todas las entidades consultadas por reportes; `Estudiante`, `Docente` y `Pariente` para historial; `Version`/tabla `versiones`; `Suceso`; y el nuevo `AuditEvent`.

**Controladores involucrados:** `VersionesController`, `SucesosController`, los controladores de exportación y `Reportes::BaseController`, `Reportes::NuevosEstudiantesController`, `Reportes::EstadisticasBloquesController`, `Reportes::ListadoEstudiantesController` y `Reportes::ResumenDocentesController`. También las acciones XLSX/boletines en estudiantes, clases, materias y secciones.

**Dependencias:** Fases 0, 1 y 2. La captura básica de auditoría debe estar activa desde Fase 0; aquí se completa la equivalencia, consulta, restauración, retención y cobertura de reportes.

**Riesgo:** **alto**. Los boletines son una salida oficial del cálculo académico. Perder versiones o sucesos afecta trazabilidad; fusionar ambos sistemas de auditoría sería una pérdida funcional.

**Esfuerzo estimado:** **alto**.  
**Fecha real:** ____________________

- [ ] Catalogar cada libro XLSX heredado: filtros, hojas, columnas, celdas, estilos, totales, orden y reglas de visibilidad.
- [ ] Migrar y comparar todos los boletines, listas, hojas y reportes. Actualmente existen cuatro generadores Django, no toda la salida heredada.
- [ ] Completar marca blanca por colegio. Nombre, pie y logo ya se usan en XLSX; faltan la identidad de la interfaz/correos, colores y dominio configurables, y resolver el aislamiento multiinstitución.
- [x] No incorporar PDF como requisito de paridad; registrarlo como mejora futura si se necesita.
- [ ] Migrar el historial legado de estudiantes, docentes y parientes. Los modelos nuevos generan historia, pero las versiones Rails aún no fueron importadas.
- [ ] Completar consulta por fecha, interfaz, restauración, eliminación y permisos de versiones. Hay servicios internos sin rutas de usuario.
- [ ] Completar `AuditEvent` para todas las altas, cambios, bajas, autenticación, bloqueos, denegaciones, consolidaciones, reaperturas y tareas. Las señales actuales solo cubren `Estudiante` e inserción de `Incidencia` y no capturan actor/IP.
- [ ] Garantizar que secretos no aparezcan en historial, auditoría, excepciones ni exportaciones; la sanitización actual es básica y no recursiva.
- [ ] Definir y hacer efectiva la retención, integridad e inmutabilidad para historial y sucesos por separado.
- [ ] Crear pruebas de caracterización Rails → Django de reportes y auditoría.

### Fase 4 — Migración de datos, operación paralela y corte

**Modelos/controladores involucrados:** todas las tablas locales, archivos y referencias externas. No añade controladores funcionales; incorpora comandos de gestión Django, ETL, conciliación y herramientas operativas de corte.

**Dependencias:** todas las fases anteriores funcionalmente aceptadas. El desarrollo del ETL y sus ensayos debe comenzar antes, pero el corte solo puede ocurrir al final.

**Riesgo:** **alto**. Hay 92 migraciones históricas, datos serializados, archivos, versiones, claves polimórficas, SQL específico y tareas pendientes. Un corte sin conciliación puede producir pérdidas silenciosas.

**Esfuerzo estimado:** **alto**.  
**Fecha real:** ____________________

- [ ] Construir un ETL repetible e idempotente con mapeo tabla/campo/transformación y rechazos. El comando actual importa únicamente usuarios desde JSON.
- [ ] Preservar identificadores o mantener tablas de correspondencia verificables.
- [ ] Convertir configuraciones y relaciones heredadas con validación sobre datos Rails reales. El conversor YAML básico ya existe.
- [ ] Migrar usuarios con credenciales temporales únicas entregables y marca `requiere_cambio_password=True`.
- [ ] Conciliar conteos, nulos, duplicados, huérfanos, restricciones, archivos y agregados académicos; el conciliador actual es preliminar.
- [ ] Ensayar la persistencia real completa, repetición idempotente y rollback. `--dry-run` solo demuestra parsing de ejemplo.
- [ ] Registrar correctamente inicio, finalización, ausencia de fuente, rechazos y errores del ETL.
- [ ] Crear pruebas de caracterización y un ensayo de corte completo para la Fase 4.

### Interfaz Web Frontend y Dashboard Ejecutivo (Bootstrap 5 & Django Stack)

**Desarrollo:** Sistema de interfaz web construido con **Bootstrap 5.3.3**, **Bootstrap Icons 1.11.3**, **Django Forms** (`LoginForm`), **Django Messages** (alertas flotantes descartables), **HTMX 1.9.10** y **CSS personalizado** (`static/css/main.css`) preservando la paleta de colores institucional (`#1f4e79`, `#0284c7`, `#10b981`) y el modo nocturno dinámico (`data-bs-theme="dark"`). Integración de plantillas responsive (`templates/base.html`, `login.html`, `dashboard/index.html`) con enrutamiento seguro y métricas en tiempo real.

**Esfuerzo estimado:** **medio**.  
**Fecha real:** ____________________

- [x] Construir el layout responsive con **Bootstrap 5.3.3** e **iconos Bootstrap Icons 1.11.3**.
- [x] Configurar el **Drawer / Offcanvas (`offcanvas-lg offcanvas-start`)** desplegado por defecto en escritorio, permitiendo **minimizarlo/colapsarlo** en cualquier momento con persistencia en `localStorage`.
- [x] Integrar **Django Forms** (`apps/accounts/forms.py`) con widgets de Bootstrap 5.
- [x] Integrar **Django Messages Framework** para alertas dinámicas de error, éxito e información.
- [x] Implementar alternancia de **Modo Nocturno (Dark Mode)** sincronizado con `data-bs-theme` de Bootstrap 5.
- [x] Integrar **HTMX 1.9.10** para cargas parciales e interacciones dinámicas (`hx-get`, `hx-target`, `hx-trigger="keyup changed delay:300ms"`).
- [x] Diseñar la vista de inicio de sesión segura (`/login/`) con pantalla glassmorphic.
- [x] Construir el Dashboard Ejecutivo (`/dashboard/`) con métricas en tiempo real.
- [ ] Completar la **Gestión de Períodos Lectivos** (`/periodos/`). El listado y clonación existen; falta el flujo de gestión equivalente y completar la clonación.
- [x] Construir la vista de **Lista de Estudiantes** (`/estudiantes/`) con búsqueda dinámica HTMX por carnet/nombre.
- [ ] Completar la vista de **Expediente de Estudiante** (`/estudiantes/<id>/`) con historial versionado y privacidad/acciones diferenciadas; la pantalla parcial ya existe.
- [ ] Completar el gestor de **Consolidación de Calificaciones y Reapertura** (`/consolidacion/`) después de corregir la lógica crítica y sus permisos.
- [ ] Completar el **Centro de Reportes XLSX Marca Blanca** (`/reportes/`) con todas las salidas heredadas verificadas.
- [x] Construir el **Visor de Bitácora de Auditoría Global** (`/auditoria/`).
- [x] Crear smoke tests para las 12 pantallas actualmente listadas; forman parte de las **65 pruebas aprobadas el 2026-08-12**.
- [ ] Cubrir todas las pantallas y acciones requeridas por la paridad, incluidos roles no administradores, POST autorizados/denegados y privacidad.

### Fase 5 opcional — Módulo financiero nativo y nuevos adaptadores

Esta fase es una **evolución comercial posterior**, no una condición para declarar completa la migración académica. Puede analizarse en paralelo, pero no debe introducir cambios en la consolidación de notas ni retrasar la obtención de paridad con Rails.

**Modelos previstos:** `Institucion`, `ConceptoCobro`, `PlanCobro`, `Cuota`, `BecaDescuento`, `Recargo`, `ConvenioPago`, `Pago`, `AplicacionPago`, `Recibo`, `MovimientoCaja`, `CierreCaja` y `EstadoSolvencia`. Estos nombres son una propuesta y deberán confirmarse mediante levantamiento de requisitos con colegios; no provienen del legado.

**Controladores/servicios previstos:** gestión de cartera y caja, estados de cuenta, pagos/recibos, cierres, reportes financieros, política de acceso por solvencia y proveedores de integración.

**Dependencias:** identidad, personas, instituciones, auditoría y adaptación multiinstitución. La interfaz `consultar_solvencia` puede definirse antes; el módulo financiero completo debe construirse después de estabilizar el núcleo académico.

**Riesgo:** **alto**. Maneja dinero, anulaciones, privacidad, conciliación, permisos y posibles obligaciones fiscales. Una integración externa añade diferencias semánticas y disponibilidad de terceros.

**Esfuerzo estimado:** **alto**.  
**Fecha real:** ____________________

- [ ] Validar con colegios los conceptos, ciclos de cobro, descuentos, recargos, becas, convenios y cierres necesarios.
- [ ] Confirmar requisitos legales, fiscales y de conservación documental aplicables antes de diseñar facturación.
- [x] Definir un contrato inicial de solvencia y sus cinco estados sin acoplar al dominio académico con nombres Loyola.
- [ ] Separar la implementación genérica de las consultas específicas de cada proveedor; el adaptador actual conserva un esquema SQL fijo.
- [ ] Implementar primero el adaptador Loyola detrás del contrato y comparar sus respuestas con Rails.
- [ ] Diseñar el módulo financiero nativo como otro proveedor del mismo contrato.
- [ ] Permitir configurar por institución qué funciones académicas restringe cada estado financiero.
- [ ] Diseñar pagos, aplicaciones, recibos y anulaciones como operaciones transaccionales e idempotentes.
- [ ] Incorporar permisos de caja, segregación de funciones y auditoría inmutable.
- [ ] Construir adaptadores adicionales solamente contra contratos/API o formatos de intercambio definidos y probados.
- [ ] Mantener la modalidad académica operativa aunque el colegio no contrate finanzas ni integración.

## 4. Estrategia de verificación

La regla general es capturar primero el comportamiento observable de Rails con una base de datos de prueba representativa y sanitizada. Cada caso debe guardar: datos de entrada, usuario/ámbito, operación, filas afectadas, salida visible, archivos producidos, sucesos/versiones generados y errores esperados. Después se ejecuta el mismo caso contra Django y se compara automáticamente.

### Fase 0 — caracterización de identidad, permisos y configuración

- Construir una matriz de autenticación con usuario habilitado/deshabilitado, login/correo, contraseña válida/inválida, cinco fallos, cuenta bloqueada, desbloqueo, vencimiento de sesión, recuperación y `expired_password`.
- Verificar los valores observables heredados: bloqueo al quinto intento, desbloqueo temporal a una hora, timeout de 30 minutos y validez del token de recuperación de dos horas.
- Registrar redirecciones y permisos durante el cambio obligatorio de contraseña, incluida la exigencia de contraseña actual y de una contraseña nueva diferente.
- Ejecutar cada permiso de `config/permissions.yml` con perfiles autorizados/no autorizados y con asignaciones a estudiante, pariente, docente, nivel y clase. Probar objetos dentro y fuera del ámbito asignado.
- Modificar permisos durante una sesión y confirmar la estrategia esperada de invalidación; el nuevo sistema no debe conservar autorizaciones obsoletas por caché.
- Crear períodos que se solapan/no se solapan, abiertos/cerrados/visibles y comparar validaciones y scopes.
- Copiar un período real y comparar cantidades, atributos y relaciones de tipos de nota, clases, secciones, materias, docentes y asignaciones.
- Probar cadenas de `TipoNota` con consolidado/desglosado, número de consolidados y actualización de campos derivados del período.
- Exportar ejemplos de cada hash/arreglo serializado y comprobar su conversión a JSON/columnas tipadas sin pérdida de claves ni orden significativo.

**Criterio de aceptación:** no debe existir una combinación que Django autorice cuando Rails la deniega, ni viceversa, salvo un cambio de seguridad aprobado y documentado explícitamente.

### Fase 1 — caracterización de estructura, personas, integración y soporte

- Crear, editar y eliminar clases, secciones, horarios y materias en períodos abiertos/cerrados; comparar validaciones, asociaciones y efectos de borrado.
- Simular dos ediciones concurrentes de `Materia` y confirmar que una actualización obsoleta no sobrescriba silenciosamente la otra.
- Probar alta e importación de estudiantes con y sin familia existente, códigos duplicados, datos incompletos y fotografías válidas/inválidas.
- Comparar una transferencia entre secciones: matrícula origen/destino, evaluaciones vacías eliminadas, calificaciones conservadas, indicadores de traslado y auditoría.
- Probar retiro, repitencia y eliminación con/sin dependencias para verificar reglas de huérfanos y restricciones.
- Consultar el estado histórico de estudiante, docente y pariente en fechas antes/después de cambios y al final de distintos períodos.
- Preparar dobles controlados del SQL Server para estudiante solvente, insolvente, excepción configurada, mes pagado/pendiente, registro ausente, timeout y error de conexión.
- Documentar como decisión explícita si el nuevo sistema conserva o cambia el comportamiento de acceso cuando la solvencia externa es desconocida. Nunca confundir “error” con “solvente” sin dejar rastro.
- Comparar destinatarios exactos de mensajes dirigidos a usuario, estudiante, pariente, docente, clase, sección, período y nivel; incluir destinatarios duplicados o sin correo.
- Verificar enviado/recibido, borrado lógico por bandeja, adjuntos de 5 MB, tipos admitidos y lotes de notificaciones.
- Comparar creación y visibilidad de incidencias y registros médicos por rol, ámbito y estado del período.
- Comparar dimensiones, formato y contenido de las tres variantes de fotografías; verificar hashes de adjuntos copiados.

**Criterio de aceptación:** relaciones, destinatarios, visibilidad e historia deben coincidir. Los cambios de seguridad deliberados —por ejemplo, contraseñas de importación únicas— requieren una prueba nueva que demuestre la mejora y la ausencia de bloqueo operativo.

### Fase 2 — conjunto dorado de calificaciones

Esta fase necesita un “golden master” producido por Rails. No basta con trasladar los tests unitarios existentes; se deben capturar estados completos de base antes y después de cada operación.

Casos mínimos:

- Materias de cada tipo configurado: acumulada, examen + acumulado, examen y variantes con reparaciones.
- Porcentajes exactos, fraccionarios, suma menor a 99.9, igual a 99.9, igual a 100 y superior/inválida.
- `nota_max` distinta de 100, resultados `NULL`, cero, enteros y valores con más de dos decimales en la entrada.
- Múltiples órdenes de creación/edición de evaluaciones que matemáticamente representen lo mismo.
- Cadenas `TipoNota` de uno y varios niveles, con cantidades distintas de consolidados.
- Configuración `redondear_consolidados` activada y desactivada.
- Examen ausente/presente, reparación fallida/aprobada y múltiples reparaciones permitidas.
- Escalas literales en cada límite, inmediatamente debajo/encima del límite y con reescalado desde `nota_max`.
- Materias excluidas del promedio o del conteo de reprobadas.
- Estudiante activo, trasladado, retirado, repitente y con calificaciones parciales.
- Consolidar, volver a consolidar, modificar una nota de origen, propagar hacia arriba, reabrir y consolidar nuevamente.
- Dos solicitudes concurrentes de consolidación y un reintento de tarea.
- Cálculo de promedio de materia, promedio consolidado, promedio de clase y conteo de reprobadas/reparadas.

Por cada caso se comparará:

- `resultado` de cada `Calificacion` como decimal exacto.
- Identidad y orden de cada nota consolidada y desglosada.
- período actual por materia/sección y cadena de `TipoNota` usada.
- promedios e indicadores de `EstudianteClase` y `Clase`.
- filas creadas, modificadas o eliminadas.
- sucesos emitidos y tareas encoladas.
- valores mostrados y valores escritos en boletines/XLSX.

**Criterio de aceptación crítico:** cualquier diferencia de redondeo, precisión, orden de consolidación, selección de nota, propagación recursiva o relación consolidado/desglosado es un bug crítico, aunque la diferencia visual sea de una centésima. No se compensa con tolerancias numéricas.

### Fase 3 — caracterización de reportes y doble auditoría

- Generar en Rails cada reporte con filtros vacíos, un resultado, múltiples páginas/hojas y datos con tildes/ñ; guardar un manifiesto de hojas, celdas, tipos, formatos relevantes, combinaciones y orden.
- Comparar boletines y hojas de calificación con el conjunto dorado de Fase 2. La fuente de verdad debe ser la misma función de dominio, no un recálculo independiente en el reporte.
- Crear, editar y eliminar un estudiante, docente y pariente; comparar la secuencia de versiones, `whodunnit`, marca temporal, estado recuperado y comportamiento de restaurar/destruir.
- Ejecutar altas, cambios y bajas sobre entidades no versionadas y comparar `Suceso`/`AuditEvent`, usuario, login, IP, descripción y campos protegidos.
- Probar inicio/cierre de sesión, bloqueo/desbloqueo, recuperación, acceso denegado, consolidación y reapertura para verificar sucesos explícitos.
- Ejecutar una acción desde Celery y confirmar que la auditoría no atribuya el cambio al usuario equivocado y conserve id de tarea/origen.
- Verificar que restaurar una versión también produzca el suceso global correspondiente, sin fusionar ni duplicar indebidamente ambos historiales.

**Criterio de aceptación:** cada sistema conserva su propósito: historial recuperable de la entidad y bitácora global de acciones. La falta de uno, la duplicación no explicada o una atribución incorrecta bloquean la fase.

### Fase 4 — verificación del ETL y del corte

- Ejecutar el ETL varias veces sobre la misma copia y demostrar idempotencia.
- Comparar conteos por tabla/modelo, máximos/mínimos de identificadores, nulos, duplicados, huérfanos y relaciones por tipo polimórfico.
- Comparar agregados de control: estudiantes por período/clase/sección, materias, evaluaciones, notas por tipo, promedios y estados de matrícula.
- Verificar cada archivo por existencia, tamaño y suma de control; reportar archivos faltantes sin ocultarlos.
- Seleccionar muestras dirigidas —no solamente aleatorias— de datos antiguos, extremos y recientemente modificados.
- Drenar trabajos Rails en un ensayo, congelar escrituras, ejecutar delta final, levantar Django y comprobar que no quede una operación aplicada en ambos sistemas o en ninguno.
- Ejecutar smoke tests por rol y los casos críticos de Fase 2 inmediatamente después del ensayo de corte.

**Criterio de aceptación:** cero pérdidas silenciosas, todas las diferencias explicadas y aprobadas, y reversión ensayada antes del corte real.

## 5. Puntos de atención especial

1. **Doble sistema de auditoría.** PaperTrail/versiones ofrece estado histórico y restauración solamente para `Estudiante`, `Docente` y `Pariente`; `Suceso` registra eventos globales, incluidas acciones sin cambio de entidad. No deben unificarse en una sola tabla genérica si eso elimina alguna capacidad.

2. **Consolidación de notas con pesos configurables.** `TipoNota` forma una cadena y `Materia` combina configuración del período/nivel/materia, porcentajes, nota máxima, exámenes, reparaciones y consolidados recursivos. Debe existir una especificación ejecutable derivada de Rails.

3. **Redondeo y precisión.** El esquema terminó usando decimales de precisión 5 y escala 2 para resultados, porcentajes, nota máxima y promedios. Ruby, MySQL, PostgreSQL y Python pueden redondear de manera diferente. Debe fijarse el modo y el punto exacto de cada redondeo; no usar `float`.

4. **Orden de consolidación.** Alterar el orden de creación o propagación puede producir otro resultado por redondeos intermedios. El orden forma parte del comportamiento contractual.

5. **Seguridad de cuentas.** Se deben conservar bloqueo, timeout, recuperación y cambio obligatorio, pero modernizar de manera consciente la política mínima de contraseña. La importación heredada puede asignar una contraseña compartida a alumnos de una sección; no debe replicarse en producción nueva.

6. **Permisos por rol y por ámbito.** `Perfil`/`Permiso`/`Autorizacion` son solo una parte. `AsignacionUsuario` agrega acceso polimórfico y roles sobre personas, niveles y clases. Migrarlo como simples grupos Django causaría sobreautorización o pérdida de acceso.

7. **Solvencia financiera externa.** THOT no contiene cuentas por cobrar propias; `Loyola` consulta tablas SQL Server y maneja excepciones por código. Hay que distinguir “solvente”, “insolvente” y “estado desconocido”. El comportamiento heredado ante fallos parece permisivo y debe someterse a una decisión de negocio/seguridad explícita.

8. **Base externa fuera del control de THOT.** Nombres de tablas, consultas `TOP 1`, disponibilidad y calidad de datos pueden cambiar. El adaptador debe tener contrato, timeouts, observabilidad, pruebas con dobles y una estrategia de contingencia.

9. **Configuración serializada.** Los hashes Ruby pueden contener símbolos, claves ausentes y valores de tipos inconsistentes. Es necesario inventariar valores reales antes de fijar el esquema JSON/relacional destino.

10. **SQL específico de motor.** Algunas consultas dependen de sintaxis o semántica de MySQL/SQL Server, incluidas expresiones booleanas dentro de agregados y ordenamientos. Cambiar a PostgreSQL exige reescritura y comparación de resultados.

11. **Concurrencia e idempotencia.** `Materia` usa `lock_version`; consolidaciones, reaperturas y recálculos también pueden ejecutarse en segundo plano. Las transacciones, bloqueos de fila e identificadores de operación deben impedir dobles efectos.

12. **Callbacks con efectos laterales.** Hay creación automática de calificaciones, recálculos, eliminación de huérfanos, auditoría y correos originados por callbacks. Trasladarlos literalmente a señales Django ocultaría el flujo; deben convertirse en servicios transaccionales explícitos cuando afecten varias entidades.

13. **Historia por fecha.** La aplicación usa versiones para reconstruir relaciones de personas en un período determinado. Migrar solo el estado actual haría incorrectos reportes históricos y boletines antiguos.

14. **Archivos e imágenes.** Fotos y adjuntos viven fuera de las filas principales, tienen límites y variantes. El ETL necesita inventario, sumas de control, manejo de faltantes y una política de almacenamiento/retención.

15. **Mensajería masiva.** Los destinatarios se derivan de varios ámbitos, el correo se envía por lotes y existen estados de bandeja. Celery debe manejar reintentos sin duplicar correos.

16. **Auditoría en procesos asíncronos.** El legado usa estado asociado al hilo. Django con ASGI y Celery necesita contexto explícito para no atribuir cambios al usuario equivocado.

17. **Marca blanca incompleta.** Algunos reportes contienen textos/logos institucionales incrustados. Para alquilar el sistema a varios colegios, identidad, logo, encabezados, zona horaria, escala y reglas deben ser configuración por institución, no constantes.

18. **Credenciales heredadas.** Hay secretos de base de datos/correo dentro de archivos de configuración. Deben rotarse y sacarse del repositorio antes de usar cualquier parte del sistema en un entorno conectado.

19. **Ausencias funcionales y evolución financiera.** No se encontró módulo propio de asistencia, caja, facturación o contabilidad, ni generación activa de PDF. Se recomienda ofrecer finanzas como módulo opcional posterior y mantener una modalidad exclusivamente académica. Los sistemas financieros existentes se conectarán mediante adaptadores explícitos o APIs, no mediante consultas arbitrarias configurables contra cualquier esquema. Añadir finanzas es evolución del producto y debe estimarse separadamente de la paridad Rails → Django.

20. **Operación multiinstitución.** El código revisado parece diseñado para una institución configurada, no para aislamiento fuerte entre múltiples colegios en una misma base. Convertirlo en SaaS multi-tenant exige modelar `Institucion`, incluirla en claves y permisos, probar aislamiento y decidir una estrategia de tenancy; no debe asumirse que cambiar el logo basta.

## 6. Estimación y seguimiento

Las etiquetas expresan esfuerzo relativo, no duración ni fechas. “Alto” indica múltiples dominios, integraciones o validaciones críticas; “medio”, un dominio delimitado con dependencias conocidas; “bajo”, un trabajo acotado. La fecha real queda vacía para completarla según la disponibilidad y el avance efectivo.

| Fase | Resultado verificable | Riesgo | Esfuerzo estimado | Estado verificado 2026-08-12 | Fecha real de finalización |
|---|---|---|---|---|---|
| Fase 0 — núcleo | Autenticación, autorización por ámbito, catálogos, períodos y tipos de nota caracterizados y operativos | Alto | Alto | Parcial avanzado; paridad no demostrada |  |
| Fase 1A — estructura académica | Clases, secciones, materias estructurales, horarios y asignaciones | Medio | Medio | Parcial avanzado |  |
| Fase 1B — personas e inscripción | Estudiantes, docentes, parientes, historia, transferencias e integración Loyola | Alto | Alto | Parcial; Loyola real pendiente |  |
| Fase 1C — soporte | Incidencias, registro médico, mensajes, adjuntos y notificaciones | Medio | Medio | Parcial; bandejas/notificaciones pendientes |  |
| Fase 2 — calificaciones | Evaluaciones, calificaciones, consolidación, reapertura y promedios con paridad decimal exacta | Crítico | Alto | Prototipo avanzado; paridad no demostrada |  |
| Fase 3 — reportes y auditoría | XLSX/boletines, historial recuperable y bitácora global equivalentes | Alto | Alto | Parcial; cuatro XLSX sin golden master |  |
| Fase 4 — datos y corte | ETL conciliado, operación paralela, corte y reversión ensayados | Alto | Alto | Prototipo: importación JSON de usuarios |  |
| Frontend UI & Dashboard | Interfaz web responsive y pantallas para todo el alcance heredado | Medio | Alto | Parcial avanzado; 12 pantallas con smoke test |  |
| Fase 5 opcional — finanzas e integraciones | Módulo financiero contratable y adaptadores externos bajo un contrato común de solvencia | Alto | Alto | No iniciada |  |

### Registro de seguimiento por fase

Hechos verificados en esta revisión:

- [x] Código Django y documento contrastados el 2026-08-12.
- [x] 65 pruebas actuales ejecutadas satisfactoriamente sobre PostgreSQL 17.
- [x] Consistencia de modelos/migraciones revisada con `makemigrations --check --dry-run`.

Pendiente para cerrar cada fase:

- [ ] Responsable y alcance de la fase registrados.
- [ ] Cambios intencionales respecto de Rails aprobados.
- [ ] Fixtures/datos Rails sanitizados disponibles.
- [ ] Pruebas de caracterización Rails capturadas.
- [ ] Implementación Django completa para el alcance de la fase.
- [ ] Comparación Rails vs Django aprobada.
- [ ] Riesgos abiertos resueltos o aceptados formalmente.
- [ ] Fecha real registrada solamente al completar la fase.

La migración debe considerarse terminada solamente cuando la equivalencia funcional, numérica, de permisos, de historial y de datos sea demostrable. Que la interfaz nueva funcione no constituye por sí solo un criterio de finalización.

## 7. Stack tecnológico para el MVP completo y evolución posterior

En este documento, **MVP no significa una migración funcionalmente recortada**. El MVP deberá incluir todo el alcance confirmado del legado: usuarios y permisos, catálogos, períodos, estructura académica, personas, incidencias, registro médico, mensajería, evaluaciones, calificaciones, consolidación, boletines, reportes XLSX, historial, sucesos, importaciones, exportaciones, tareas diferidas, archivos y la integración de solvencia Loyola. Lo “mínimo” se refiere a la cantidad de tecnologías, no a dejar módulos sin migrar.

El módulo financiero nativo de la Fase 5 no forma parte de la paridad del MVP porque no existe en Rails. El MVP sí conservará la consulta externa de solvencia detrás del nuevo contrato de adaptadores.

### 7.1 Tecnologías obligatorias para aprobar el MVP

| Tecnología | Uso en la migración | Motivo por el que se conserva |
|---|---|---|
| **Python** | Lenguaje del nuevo sistema y de los procesos de migración | Es la tecnología elegida para sustituir Ruby. |
| **Django LTS** | ORM, modelos, servicios, autenticación, permisos, formularios, vistas, sesiones y administración | Cubre la mayor parte de la aplicación sin combinar varios frameworks. |
| **PostgreSQL** | Base de datos principal para todos los ambientes | Proporciona transacciones, decimales, integridad y concurrencia adecuadas. Se usará también en desarrollo/pruebas para evitar diferencias con producción. |
| **psycopg** | Controlador de conexión entre Django y PostgreSQL | Dependencia técnica necesaria para usar PostgreSQL desde Python. |
| **Django Templates** | Renderizado de toda la interfaz web | Evita una SPA y una API interna innecesarias. |
| **Bootstrap 5** | Diseño responsive, formularios, tablas, navegación y marca blanca | Reduce el CSS que debe construirse y mantenerse. |
| **JavaScript básico** | Confirmaciones, controles pequeños y comportamientos que no resuelva HTML/Django | No se requiere un framework frontend para la paridad funcional. |
| **django-axes** | Bloqueo por intentos fallidos | Permite reproducir una función de seguridad que el legado ya posee. |
| **django-simple-history** | Historial de `Estudiante`, `Docente` y `Pariente` | Es el reemplazo mínimo de PaperTrail. La restauración específica se implementará en servicios Django. |
| **Modelo `AuditEvent` propio** | Bitácora global equivalente a `Suceso` | No requiere una biblioteca adicional y mantiene separado el segundo sistema de auditoría. |
| **Celery** | Importaciones, exportaciones, correos, notificaciones y recálculos en segundo plano | Es necesario antes de declarar completa la paridad con Delayed::Job. No tiene que instalarse en la primera semana, pero sí antes de aceptar el MVP. |
| **Redis** | Cola/broker de Celery | Es la opción mínima y sencilla para ejecutar las tareas asíncronas del MVP. |
| **openpyxl** | Boletines, hojas de calificación, listados y reportes XLSX | El legado produce XLSX; esta salida forma parte de la paridad. |
| **Pillow** | Validación y variantes de fotografías | Sustituye MiniMagick y conserva el manejo de imágenes. |
| **pyodbc** | Adaptador de lectura para Loyola/SQL Server | Se necesita mientras la solvencia externa actual forme parte del alcance. Se elimina si el colegio deja de usar esa integración. |
| **Correo de Django mediante SMTP** | Recuperación de contraseña, mensajes y notificaciones | Django ya incluye el cliente; no se necesita un paquete adicional. |
| **Pruebas integradas de Django (`TestCase`/`unittest`)** | Caracterización y comparación del comportamiento | Son suficientes para comenzar sin agregar pytest, Factory Boy o herramientas similares. |
| **Git** | Versionado de código, documento, migraciones y pruebas | Esencial para trazabilidad y reversión de cambios de desarrollo. |
| **Entorno virtual + archivo de dependencias fijadas** | Aislamiento y reproducción de la instalación Python | Puede resolverse con `venv` y un archivo de requisitos; Docker no es necesario. |

Las reglas de autorización por ámbito se implementarán inicialmente con permisos/grupos nativos de Django y un servicio propio que sustituya `Ability`. No se incluirá `django-guardian` en el MVP salvo que un prototipo demuestre que reduce realmente la complejidad sin cambiar la semántica de `AsignacionUsuario`.

### 7.2 Infraestructura mínima de producción

Para una instalación en un servidor Linux propio:

| Componente | Función |
|---|---|
| **Gunicorn** | Ejecutar la aplicación Django en producción. |
| **Nginx** | HTTPS, proxy inverso, archivos estáticos y cargas. |
| **systemd** | Mantener activos Gunicorn y los workers de Celery. |
| **PostgreSQL** | Servicio de base principal. |
| **Redis** | Servicio de cola para Celery. |
| **Let's Encrypt** | Certificado HTTPS sin costo de licencia. |
| **Backups programados** | Copias de PostgreSQL y del directorio de archivos, con pruebas periódicas de restauración. |

En desarrollo se puede usar Windows o Linux con `venv`, PostgreSQL y Redis disponibles localmente o en otro servidor. El servidor integrado `runserver` de Django es válido para desarrollo, pero no para producción.

### 7.3 Docker no es requisito del MVP

Docker queda explícitamente **fuera de las tecnologías obligatorias**. El MVP puede instalarse con Python, `venv`, PostgreSQL, Redis, Gunicorn, Nginx y systemd.

Se evaluará Docker posteriormente cuando exista alguna de estas necesidades:

- desplegar la misma solución en muchos servidores de colegios;
- reproducir ambientes de forma automatizada;
- simplificar altas y actualizaciones de una oferta SaaS;
- incorporar CI/CD y pruebas de infraestructura;
- reducir diferencias frecuentes entre desarrollo y producción.

No se añadirá Docker únicamente por tendencia tecnológica. Su incorporación deberá resolver un problema operativo concreto.

### 7.4 Tecnologías posteriores o no esenciales y condición para incorporarlas

| Tecnología posterior | Incorporarla solamente cuando… |
|---|---|
| **Django REST Framework** | Un sistema externo necesite una API de THOT, se publique un portal separado o aparezca otro cliente distinto de las páginas Django. |
| **drf-spectacular/OpenAPI** | Exista una API que deba documentarse para terceros. |
| **HTTPX** | Se integre un proveedor financiero mediante API HTTP. `pyodbc` seguirá cubriendo Loyola mientras sea conexión SQL Server. |
| **HTMX** | Ya fue incorporado puntualmente para la búsqueda dinámica de estudiantes. Mantenerlo limitado a casos que justifiquen la dependencia. |
| **Docker/Docker Compose** | La repetibilidad de despliegues o la cantidad de instalaciones justifique la complejidad añadida. |
| **django-storages + S3/MinIO** | El almacenamiento local deje de ser suficiente, haya varios servidores o se necesite alta disponibilidad de archivos. |
| **WeasyPrint** | Se apruebe PDF como funcionalidad nueva; el legado confirmado utiliza XLSX. |
| **django-money** | El módulo financiero nativo necesite varias monedas y el modelo acordado lo justifique. Para una sola moneda bastan `DecimalField` y un campo de moneda explícito. |
| **django-guardian** | Los permisos por objeto no puedan mantenerse claramente con el servicio de políticas propio. |
| **Sentry** | El sistema entre en producción con varios colegios y se necesite centralizar errores y alertas. |
| **Playwright** | Se quieran automatizar recorridos completos del navegador después de estabilizar las pruebas de caracterización del backend. |
| **pytest/Factory Boy/Hypothesis** | El volumen o complejidad de pruebas haga insuficiente el runner integrado de Django. Hypothesis sería especialmente útil para casos numéricos, pero no reemplaza el conjunto dorado de Rails. |
| **CI/CD** | El repositorio y el mecanismo de despliegue estén definidos y se quiera automatizar pruebas/publicaciones. |
| **Prometheus/Grafana** | La cantidad de instituciones o los acuerdos de disponibilidad requieran métricas operativas avanzadas. |
| **django-tenants** | Se decida explícitamente usar un esquema PostgreSQL separado por institución. El MVP puede iniciar con `institucion_id` y aislamiento obligatorio validado por pruebas. |

### 7.5 Orden de incorporación tecnológica

1. **Base del desarrollo:** Python, Django, PostgreSQL/psycopg, Templates, Bootstrap, JavaScript, Git y `venv`.
2. **Seguridad y dominio:** `django-axes`, servicio propio de permisos, `django-simple-history` y `AuditEvent`.
3. **Funciones heredadas especializadas:** Pillow, openpyxl y pyodbc/adaptador Loyola.
4. **Procesamiento asíncrono:** Celery y Redis antes de aceptar importaciones, exportaciones, notificaciones y recálculos como completos.
5. **Producción:** servidor Linux, Gunicorn, Nginx, systemd, HTTPS y backups probados.
6. **Evolución posterior:** seleccionar tecnologías de la tabla anterior únicamente al aparecer su condición de uso.

### 7.6 Checklist tecnológico del MVP

- [ ] Python y Django LTS fijados en el archivo de dependencias.
- [ ] PostgreSQL utilizado tanto en pruebas como en producción.
- [ ] Interfaz completa construida con Templates, Bootstrap y JavaScript básico.
- [ ] Autenticación, bloqueo y permisos por ámbito reproducidos.
- [ ] PaperTrail y `Suceso` reemplazados sin fusionar sus responsabilidades.
- [ ] XLSX y fotografías reproducidos con openpyxl y Pillow.
- [ ] Integración Loyola encapsulada con pyodbc y contrato de solvencia.
- [ ] Delayed::Job reemplazado por Celery + Redis antes de cerrar la migración.
- [ ] Pruebas de caracterización ejecutadas con las herramientas integradas de Django.
- [ ] Gunicorn, Nginx, HTTPS y backups verificados para producción.
- [x] Docker y DRF permanecen fuera del proyecto; HTMX fue adoptado de forma puntual y documentada.

## 8. Cómo ofrecer y personalizar el sistema

### 8.1 Conclusión comercial y técnica

La primera oferta recomendable es **software académico por suscripción, administrado y de marca blanca, con una instancia y una base PostgreSQL separadas por colegio**. Existe **una sola base de código reutilizable para cualquier escuela**: el cliente alquila el servicio, soporte, actualizaciones y respaldo; no una copia distinta ni un fork del código. Identidad, reglas, catálogos, permisos, datos e integraciones cambian mediante configuración y módulos activables. Esta modalidad aprovecha la capacidad de personalización sin afirmar que el sistema actual sea multi-tenant.

No se recomienda vender todavía una licencia “para cualquier colegio” ni operar múltiples instituciones en la misma base. El código Django usa `ConfiguracionInstitucion.get_solo(id=1)` y la mayor parte del dominio no incluye `Institucion`; por tanto, hoy solo existe una identidad institucional por instalación. Una base compartida introduciría riesgo de exposición de expedientes, notas, mensajes y archivos entre colegios.

El producto puede ofrecerse en tres modalidades, manteniendo siempre el mismo núcleo de código:

| Oferta | Incluye | Cuándo puede ofrecerse |
|---|---|---|
| **Académico** | Usuarios/permisos, períodos, estructura, personas, soporte, calificaciones, boletines, XLSX, historial y auditoría | Cuando las Fases 0–4 demuestren paridad con Rails y el corte de datos esté ensayado. No es una versión recortada. |
| **Académico Integrado** | Todo lo anterior más un adaptador de solvencia o intercambio con el sistema financiero ya usado por el colegio | Después de implementar y probar un adaptador específico para ese proveedor. La integración se cotiza aparte. |
| **Académico + Finanzas** | Todo lo anterior más cartera/cobros/pagos/recibos/caja del módulo nativo opcional | Solo después de levantar requisitos y completar la Fase 5 como producto financiero independiente. |

El modelo de cobro recomendado combina:

- **cuota única de incorporación**, que cubre diagnóstico, configuración, migración de datos, integración, capacitación y salida a producción;
- **suscripción mensual o anual por rango de matrícula activa**, no por cantidad de cuentas, para que docentes y parientes no penalicen el uso;
- **complementos separados** para integración financiera, módulo financiero nativo, almacenamiento adicional, reportes nuevos o soporte ampliado;
- **personalizaciones exclusivas cotizadas como proyecto** cuando cambien el comportamiento compartido del producto.

La venta perpetua del código debe quedar como excepción y tener un precio superior, mantenimiento anual y condiciones claras de actualización. Para un producto que debe corregirse, respaldarse y adaptarse a cambios académicos, la suscripción produce una operación más sostenible.

### 8.2 Qué muestra el proyecto Ruby sobre personalización

El legado confirma que ya existían parámetros institucionales y académicos, aunque estaban mezclados con identidad Loyola y constantes en código:

- `Configuracion` permite seleccionar perfiles predeterminados de estudiante, pariente y docente, definir excepciones de solvencia y decidir si se acumula el redondeo de consolidados.
- `PeriodoLectivo.config` almacena nota mínima, tipo de materia, porcentaje de examen, cantidad de reparaciones, escala literal y configuración particular por nivel.
- `Nivel.config` y `Materia.config` participan en la herencia de reglas académicas; la materia puede sobrescribir la configuración superior.
- `Perfil`, `Permiso`, `Autorizacion` y `AsignacionUsuario` permiten adaptar responsabilidades y ámbitos de acceso.
- Catálogos como niveles, asignaturas, escalas, estados civiles, religión, escolaridad y recorridos ya separan datos institucionales de la lógica.
- La identidad no era realmente marca blanca: plantillas, correos, dominio, remitente, imágenes y encabezados XLSX contienen Loyola/Instituto Loyola y logos estáticos.

La migración debe conservar lo configurable y eliminar la dependencia de una institución concreta. “Personalizar” no debe significar copiar el repositorio y editar textos para cada cliente.

### 8.3 Capas de personalización

| Capa | Datos configurables | Ubicación recomendada | Regla |
|---|---|---|---|
| Identidad | nombre legal/comercial, lema, logos claro/oscuro, favicon, colores, dirección, teléfono, correo, dominio, zona horaria y pies | Configuración institucional validada + archivos multimedia | Editable por administrador autorizado; nunca hardcodeado en plantillas/reportes. |
| Seguridad | perfiles predeterminados, matriz de permisos, duración de sesión, vencimiento y política de acceso | Modelos de perfiles/políticas; parámetros sensibles en settings | Los valores heredados se caracterizan; los cambios modernos se aprueban y auditan. |
| Académica global | niveles, asignaturas, escalas, nota mínima y tipos de materia | Catálogos tipados | No duplicar código por colegio. |
| Año lectivo | fechas, apertura/visibilidad, cadena `TipoNota`, pesos, porcentajes, exámenes, reparaciones y reglas por nivel | `PeriodoLectivo` y configuración versionada/validada | Al clonar se copia una instantánea; modificar un año nuevo no altera boletines históricos. |
| Materia/clase | sobrescrituras de reglas, secciones, docentes, horarios y exclusiones | Modelos de estructura y configuración heredable | Debe existir una precedencia explícita: materia → nivel/período → valor predeterminado. |
| Solvencia | proveedor, cinco estados, excepciones, funciones bloqueadas, caché y conducta ante error | Política institucional + adaptador seleccionado | Credenciales/consultas privadas fuera de la UI y del repositorio. |
| Comunicación | remitente, plantillas, firmas, audiencias y textos transaccionales | Plantillas configurables con variables permitidas | No permitir HTML o variables sin sanitización; registrar cada envío masivo. |
| Operación | URL, SMTP, conexión externa, almacenamiento, backups y retención | Variables de ambiente/gestor de secretos | No son opciones para el administrador escolar ni deben guardarse como texto libre en la base. |

### 8.4 Cambios necesarios para una marca blanca real

La configuración Django actual cubre nombre, lema, logo, dirección, teléfono, correo y pie de boletín, y los XLSX ya consumen parte de esos datos. Para completar la oferta se debe:

- incorporar un `context_processor` que entregue la configuración institucional a todas las plantillas;
- sustituir `THOT`, la letra `T` y títulos fijos en `base.html`, login y demás pantallas por nombre/logo configurados;
- convertir los colores fijos en variables CSS institucionales con valores de respaldo accesibles;
- parametrizar favicon, asunto/remitente y plantillas de correo;
- usar la zona horaria y datos legales configurados en reportes y auditoría;
- mantener un nombre técnico interno del producto para soporte sin mostrarlo como identidad del colegio;
- añadir una prueba de marca blanca que genere login, navegación y los cuatro XLSX con dos configuraciones distintas y compruebe que no se filtra el nombre/logo de la otra.

### 8.5 Estrategia de aislamiento y crecimiento

**Etapa inicial — instancia aislada por colegio:** mismo repositorio y versión, despliegue, base, archivos, dominio y backups separados. Es la opción recomendada para los primeros clientes porque reduce el impacto de una fuga y permite restaurar un colegio sin afectar a otros. Docker es opcional; scripts de despliegue reproducibles son suficientes.

**Etapa intermedia — administración de varias instancias:** automatizar aprovisionamiento, actualizaciones, comprobaciones y backups, conservando bases separadas. Esta etapa puede soportar una oferta SaaS administrada sin convertir el dominio en multi-tenant.

**Etapa posterior — multi-tenant real:** elegir conscientemente entre `Institucion` en todas las filas relevantes, esquemas PostgreSQL separados o bases separadas. Si se usa base compartida, todas las consultas, relaciones, claves únicas, tareas, cachés, archivos, admin y auditoría deben estar limitados por institución. El cambio requiere migración propia y pruebas de aislamiento ofensivas; cambiar el logo no lo resuelve.

### 8.6 Incorporación de un colegio

Cada alta debe seguir un proceso repetible:

- [ ] Levantar alcance contratado, cantidad de estudiantes, roles y sistema financiero existente.
- [ ] Recibir identidad visual en formatos acordados y completar la ficha institucional.
- [ ] Inventariar reglas de notas por nivel/materia, escalas, exámenes, reparaciones, redondeo y períodos.
- [ ] Definir perfiles, permisos y responsables de aprobación.
- [ ] Seleccionar: sin finanzas, adaptador externo o módulo financiero futuro.
- [ ] Preparar mapeo de datos y ejecutar al menos una migración de ensayo con conciliación.
- [ ] Comparar calificaciones/boletines con un conjunto dorado aprobado por el colegio.
- [ ] Configurar dominio, correo, HTTPS, backups, monitoreo y política de soporte.
- [ ] Capacitar administración, docentes y usuarios de consulta según su rol.
- [ ] Ejecutar operación paralela, aceptación, corte y plan de reversión.

### 8.7 Límites para evitar una variante de código por cliente

Una solicitud debe resolverse como **configuración** si cambia identidad, catálogos, reglas ya modeladas, permisos o selección de proveedor. Debe resolverse como **función común del producto** si beneficia a varios colegios y puede activarse con una opción. Solo debe ser **desarrollo exclusivo** si introduce un flujo verdaderamente propio; en ese caso se cotiza aparte, se mantiene detrás de una capacidad/módulo y no se crea un fork permanente.

No se aceptarán como “personalización” consultas SQL arbitrarias, edición directa de plantillas en producción, reglas de notas sin validación, credenciales dentro de la base o cambios manuales al código desplegado. Esos atajos vuelven imposible mantener y actualizar el servicio alquilado.

### 8.8 Condiciones mínimas antes de ofrecerlo a producción

- [ ] Fases 0–4 aceptadas con las pruebas de caracterización correspondientes.
- [ ] Permisos negativos y aislamiento de datos demostrados con roles reales.
- [ ] Conjunto dorado de calificaciones y boletines sin diferencias críticas.
- [ ] ETL y reversión ensayados con datos representativos.
- [ ] Marca blanca completa en interfaz, correos y reportes.
- [ ] Producción endurecida, HTTPS activo y secretos fuera del repositorio.
- [ ] Backups automáticos con restauración probada y retención acordada.
- [ ] Contrato de soporte, disponibilidad, propiedad/exportación de datos y baja del servicio definido.
- [ ] Adaptador financiero probado contra el proveedor concreto cuando forme parte del contrato.

Hasta cumplir estas condiciones, el sistema debe presentarse como **migración en desarrollo/piloto controlado**, no como producto terminado para datos académicos reales.
