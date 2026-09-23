# Estado vigente de la migración SIAC → THOT

**Corte de auditoría:** 27 de agosto de 2026

**Estado del documento:** vigente

**Commit revisado:** `d127d87439fec07638ff85f2a841eab229602c46`

**Proyecto legado:** `C:\Users\David\Documents\Sistema Escolar\Version vieja ruby\SIAC-CCA`

**Proyecto Django:** `C:\Users\David\Documents\GitHub\thot-sistema-de-gestion-estudiantil`

## Dictamen ejecutivo

THOT es un **prototipo Django avanzado, ejecutable y con cobertura visual amplia**.
El árbol Git está limpio, la línea base contiene 191 archivos versionados, Django
arranca y las 126 pruebas actuales pasan en PostgreSQL. Es evidencia útil de
consistencia interna para los escenarios cubiertos.

No es todavía una migración equivalente ni está preparada para producción. La
autorización y la integridad de calificaciones conservan vulnerabilidades críticas;
la clonación de períodos, la consolidación médica y los ámbitos heredados no
alcanzan paridad segura; tampoco existe una migración ensayada de datos reales.

**No deben cargarse datos reales ni registrarse calificaciones oficiales** hasta
resolver los hallazgos críticos y altos del
[`plan_correcciones_prioritarias.md`](plan_correcciones_prioritarias.md).

## Evidencia reproducida

| Comprobación | Resultado del corte | Interpretación conservadora |
|---|---|---|
| `git status --short` | Limpio | No hay cambios locales sin registrar al cerrar la auditoría. |
| Archivos seguidos por Git | 191 | Ya existe una línea base; no hay historial granular para atribuir cada fase anterior. |
| `manage.py check` | Sin problemas | La configuración cargada y el registro de aplicaciones son coherentes. |
| `manage.py makemigrations --check --dry-run` | Sin cambios | No hay diferencias de modelos que requieran generar otra migración. |
| `manage.py migrate --plan` | **5 operaciones de aplicación pendientes** | La base local no está sincronizada con todas las migraciones versionadas. |
| `manage.py test` | **126/126 aprobadas** en PostgreSQL | La suite no cubre varios casos negativos descritos abajo. |
| `manage.py check --deploy` con `DEBUG=False` y clave válida | Sin advertencias | Depende de suministrar valores de producción correctos mediante entorno. |

### Migraciones pendientes en la base local

- `academic_core.0003_seccion_docente`
- `accounts.0002_permisos_soporte`
- `audit.0002_alter_auditevent_origen`
- `support.0002_delete_registromedico`
- `support.0003_mensajeusuario`

`makemigrations --check` y `migrate --plan` responden preguntas distintas: el
primero confirma que no falta generar archivos; el segundo demuestra que los cinco
archivos anteriores todavía no están aplicados en la base configurada. No debe
aplicarse `support.0002` sobre datos reales antes de definir y probar su política de
conflictos y reversión.

### Base local observada

La base contiene una cuenta, 17 parientes y 203 eventos de auditoría. Contiene cero
períodos, clases, secciones, materias, estudiantes, matrículas, evaluaciones y
calificaciones. Es actividad de desarrollo, no evidencia de migración de SIAC.

En el proyecto Ruby no se encontró un dump productivo ni el repositorio real de
fotografías y documentos. Sin esas fuentes no es posible ensayar ni conciliar el
corte de datos.

## Avances confirmados

- Línea base completa incorporada a Git y árbol de trabajo limpio.
- Arquitectura modular de ocho aplicaciones y modelo de usuario personalizado.
- Arranque, comprobaciones de modelos y suite de 126 pruebas funcionales.
- Denegación de `is_staff` como superpoder implícito y controles por objeto para
  varios expedientes, materias, secciones y mensajes.
- Clonación más completa que el primer prototipo: tipos de nota, clases, secciones,
  materias, docentes, horarios y asignaciones de clase.
- Flujo de recuperación de contraseña, validadores y endurecimiento condicionado a
  variables de producción.
- Modelo canónico `FichaMedica`, relación `MensajeUsuario` y contexto de actor/IP
  para parte de la auditoría.
- Separación documental entre estado vigente, plan técnico y cortes históricos.

Estos avances reducen trabajo de construcción. No prueban por sí solos equivalencia
con Rails, seguridad por ámbito, reversibilidad de datos ni preparación operativa.

## Hallazgos abiertos

### Críticos

#### C-01 — modificación de calificaciones ajenas por ID

La consolidación acepta claves `calif_<id>` y busca la calificación únicamente por
clave primaria. No restringe la fila a la materia y tipo de nota seleccionados ni
revalida el ámbito real del objeto. Un usuario autorizado en una materia puede
intentar modificar una calificación perteneciente a otra materia o sección.

#### C-02 — alcance institucional implícito y exposición global de auditoría

Una cuenta habilitada sin asignaciones puede ser considerada de alcance global. El
reporte de docentes se apoya en ese predicado sin exigir un permiso dedicado. El
dashboard, protegido sólo por inicio de sesión, expone conteos globales y los diez
eventos de auditoría más recientes a cualquier cuenta autenticada.

### Altos

#### H-01 — autorización contextual incompleta

- La vigencia de asignaciones sólo considera `activo=True`; ignora fecha de inicio,
  fecha de fin y perfil inactivo.
- `puede(..., objeto=None)` concede el permiso de perfil sin comprobar ámbito. Varias
  vistas de creación, matrícula, familiares y estructura académica usan esa ruta.
- Persisten listados y opciones de formulario sin filtrar por ámbito.
- No se reproduce la propagación heredada de asignaciones de Nivel y Clase hacia
  secciones, materias, estudiantes, incidencias y expedientes.
- Las pruebas actuales validan varios objetos directos, pero no una matriz completa
  de acceso directo, POST manipulado y ámbito heredado.

#### H-02 — clonación de período no equivalente

Rails sólo clonaba el período abierto y actual y desplazaba inicio y fin exactamente
un año. El flujo Django no verifica esas precondiciones, fija 15 de enero y 30 de
noviembre y crea el destino sin ejecutar necesariamente `full_clean()`. Por ello
puede saltarse la validación de traslape y producir fechas distintas del legado.

#### H-03 — consolidación médica destructiva y sin reversa de datos

La migración usa `update_or_create()` y puede sobrescribir una `FichaMedica`
existente con valores vacíos o divergentes del registro antiguo. Su función inversa
no restaura filas. La política acordada para corregirla es **reversible y
conciliada**: respaldo, detección de conflictos, conteos, reglas de precedencia y
prueba de ida y vuelta antes de eliminar el origen.

#### H-04 — base local con migraciones de corrección sin aplicar

Las cinco migraciones de las fases 1, 5 y 6 existen en Git pero no están aplicadas a
la base local. Aplicarlas a ciegas ocultaría el riesgo de `support.0002`; primero
debe aprobarse y probarse el procedimiento de datos.

### Medios que permanecen abiertos

- `MensajeUsuario` no se marca leído al abrir un mensaje y los ámbitos Nivel, Clase,
  Sección y Período no se expanden como en Rails.
- La inmutabilidad de `AuditEvent` cubre `save()` y `delete()` ordinarios, pero no
  escrituras por `QuerySet.update()`, `bulk_update()` o SQL directo.
- El contexto de auditoría usa almacenamiento por hilo, no una estrategia segura
  para concurrencia ASGI ni ejecución asíncrona.
- Las políticas observadas difieren del legado: sesión de 60 frente a 30 minutos,
  recuperación por 3 días frente a 2 horas y bloqueo de acceso con parámetros
  distintos.
- El ETL sólo importa usuarios desde JSON, no asigna perfiles y puede registrar la
  operación como completada aunque la fuente no exista.

## Estado conservador por área

| Área | Construcción actual | Paridad segura | Estado |
|---|---|---|---|
| Identidad y cuentas | Funcional en desarrollo | Parcial | Políticas temporales y operación de correo/bloqueo por cerrar. |
| Autorización y privacidad | Parcial | No demostrada | **Bloqueada por C-02 y H-01.** |
| Estructura académica | Amplia | No demostrada | Clonación bloqueada por H-02. |
| Personas y expediente médico | Amplia | No demostrada | Consolidación de datos bloqueada por H-03. |
| Calificaciones | Prototipo funcional | No demostrada | **Bloqueada por C-01 y ausencia de conjunto dorado.** |
| Mensajería | Directos básicos | Parcial | Estado de lectura y audiencias heredadas pendientes. |
| Reportes | Cuatro generadores XLSX | No demostrada | Sin comparación contra las 14 plantillas AXLSX legadas. |
| Auditoría | Cobertura parcial | Parcial | No es global ni inmutable en todas las rutas de escritura. |
| ETL y corte | Boceto | No iniciada con datos reales | Sin dump, staging, conciliación, delta ni reversión ensayada. |
| Operación | Desarrollo local funcional | No preparada | Migraciones locales pendientes, dependencias abiertas y restauración sin probar. |

## Criterio de paridad acordado

Se usará **paridad de comportamiento segura**:

1. Conservar resultados, ámbitos y flujos observables necesarios del sistema Rails.
2. No copiar vulnerabilidades o limitaciones técnicas del legado.
3. Documentar toda desviación intencional y su razón.
4. Exigir pruebas comparativas o fixtures dorados para declarar paridad.
5. Mantener una política de denegación por defecto en accesos y una reversión
   demostrable en transformaciones destructivas de datos.

## Regla de cierre

Un hallazgo no se cierra porque exista código o una prueba feliz. Se cierra cuando:

- existe una especificación de comportamiento y ámbito;
- pasan pruebas positivas, negativas y de manipulación directa;
- la implementación se contrasta con Rails cuando aplica;
- las migraciones se prueban hacia adelante y hacia atrás con conflictos;
- la documentación y el estado de la base coinciden con la evidencia ejecutada.

El orden y las pruebas requeridas están definidos en
[`plan_correcciones_prioritarias.md`](plan_correcciones_prioritarias.md). El corte
anterior se conserva como documento histórico en
[`historico/2026-08-27-estado-migracion-fases-1-6.md`](historico/2026-08-27-estado-migracion-fases-1-6.md).
