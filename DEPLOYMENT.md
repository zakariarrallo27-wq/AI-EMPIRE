# Despliegue de la API de Jarvis

## Estado
La API HTTP está implementada en `api_server.py`. Usa la misma base SQLite que
`jarvis_core.py` y `jarvis_bus.py`. El endpoint `/health` es público para
comprobaciones; todos los endpoints `/v1` requieren un token Bearer.

**El servicio aún no está publicado en Internet.** Subir el código a GitHub no
crea un servidor activo. Para conectar los teléfonos hace falta desplegarlo en
un hosting Python con HTTPS y configurar sus variables secretas.

## Variables de entorno
Configura en el panel privado del hosting:

- `JARVIS_API_TOKEN`: secreto aleatorio largo. No lo guardes en GitHub ni lo
  compartas en chats.
- `JARVIS_DB_PATH`: ruta a un disco persistente, por ejemplo
  `/var/data/jarvis.db`, si el proveedor ofrece almacenamiento persistente.
- `OPENAI_API_KEY`: necesaria solo para ejecutar los agentes con OpenAI.
- `AI_EMPIRE_MODEL`: opcional; por defecto `gpt-4.1-mini`.

No uses SQLite en un disco efímero: los datos podrían desaparecer al reiniciar
o redeplegar el servicio. Para varias réplicas o mayor concurrencia, migra a
PostgreSQL antes de escalar.

## Comando de arranque
```bash
uvicorn api_server:app --host 0.0.0.0 --port ${PORT:-8000}
```

## Comprobación
- `GET /health` debe devolver `{"status":"ok","service":"jarvis-api","version":"0.1.0"}`.
- Envía el token como `Authorization: Bearer <JARVIS_API_TOKEN>` a las rutas
  `/v1`.
- Documentación interactiva: `/docs` (protegida por la capa de red del hosting
  si no quieres exponerla públicamente).

## Rutas disponibles
- `POST /v1/projects`
- `GET /v1/projects/{project_id}/tasks`
- `POST /v1/projects/{project_id}/tasks`
- `POST /v1/tasks/{task_id}/claim`
- `POST /v1/tasks/{task_id}/complete`
- `GET /v1/projects/{project_id}/messages?agent=Nombre`
- `POST /v1/projects/{project_id}/messages`

## Seguridad y siguiente fase
Usa exclusivamente HTTPS en producción. Guarda el token como secreto del
hosting y configura el mismo valor de forma segura en cada dispositivo. No
incluyas tokens en URLs, logs, capturas ni repositorios. Antes de uso real
multiusuario habrá que añadir identidad por dispositivo/agente, rotación de
tokens, límites de peticiones, auditoría y migrar a PostgreSQL si se ejecutan
varias instancias.
