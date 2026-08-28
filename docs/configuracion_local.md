# Configuración local

Este repositorio no debe contener credenciales reales. El archivo `.env` está
excluido por `.gitignore`; `.env.example` sólo sirve como plantilla.

## Preparación

1. Copiar `.env.example` como `.env`.
2. Sustituir todos los valores de ejemplo por valores locales únicos, en
   particular `SECRET_KEY` y `DB_PASSWORD`.
3. En desarrollo local fijar `DEBUG=True` en el `.env` (el valor por defecto
   del sistema es `False` y, sin `SECRET_KEY` definida, la aplicación no
   arranca en producción).
4. Crear la base PostgreSQL indicada en el `.env`.
5. Aplicar migraciones y crear una cuenta administrativa local:

   ```powershell
   .\.venv\Scripts\python.exe manage.py migrate
   .\.venv\Scripts\python.exe manage.py createsuperuser
   ```

6. Iniciar el servidor de desarrollo y abrir `/admin/` en la dirección local
   configurada.

## Seguridad

- No copiar usuarios ni contraseñas a este documento, incidencias o capturas.
- No reutilizar en producción credenciales que alguna vez aparecieron en la
  documentación anterior; deben considerarse expuestas y rotarse.
- `DEBUG=True` es exclusivamente para desarrollo.
- Antes de desplegar, ejecutar `manage.py check --deploy` y resolver todas las
  advertencias.
