# Documentación de THOT

Este directorio separa el estado vigente de la migración de los planes y
auditorías que ya sólo sirven como antecedentes.

## Documento vigente

- [`estado_migracion.md`](estado_migracion.md): auditoría verificada al 25 de
  agosto de 2026. Es la fuente de verdad para decidir el siguiente trabajo de
  migración.

## Operación local

- [`configuracion_local.md`](configuracion_local.md): preparación del entorno
  sin publicar usuarios, contraseñas ni secretos.

## Historial

- [`historico/`](historico/): documentos anteriores conservados para entender
  la evolución del plan, no para declarar el estado actual.

## Regla de mantenimiento

Cuando cambie la implementación, se actualiza `estado_migracion.md` con evidencia
ejecutada. Antes de sustituirlo, la versión anterior se mueve a `historico/` con
la fecha de su auditoría. No se guardan credenciales reales en Markdown.
