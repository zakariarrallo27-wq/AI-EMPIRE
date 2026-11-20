# AI-EMPIRE / JARVIS

Orquestador local inicial para AI-EMPIRE, ejecutable en Python desde Termux (Android).

## Estado actual (20-11-2026)

- `main.py`: ronda local secuencial CEO → Estratega → Creadora → Ejecutora.
- `memory.py`: memoria persistente SQLite en `data/jarvis_memory.db`.
- La lectura de recuerdos usa SQLite en modo solo lectura.
- No requiere dependencias externas: utiliza la biblioteca estándar de Python.
- El flujo guarda objetivo, misión, estrategia, creación, ejecución y resumen.
- Las respuestas de los agentes son actualmente reglas/plantillas locales predeterminadas. **No son agentes autónomos ni llaman todavía a un modelo de IA.**
- No incluye aún servicio 24/7, acceso web, publicación, automatización externa ni sincronización automática con Notion.

## Requisitos

- Python 3.10 o posterior.
- No se necesita instalar paquetes con pip para esta versión.

## Ejecutar en Termux

    cd ~/AI-EMPIRE
    python -B main.py

La primera escritura inicializa la base de datos y crea la tabla de recuerdos. La consulta de recuerdos no crea ni modifica la base de datos.

## Seguridad y límites

- Presupuesto objetivo: 0 €.
- No publicar, enviar mensajes, realizar compras ni ejecutar acciones externas sin aprobación humana explícita.
- No guardar claves API en GitHub ni en el código.
- Antes de modificar datos o código, crear copia de seguridad y verificarla.
- La disponibilidad 24/7 no está implementada ni garantizada.

## Próximas fases

1. Pruebas aisladas y de aceptación.
2. Proveedor de modelo con nivel gratuito y límites verificados; nunca asumir uso ilimitado.
3. Orquestación real con contexto compartido y memoria.
4. Cola de tareas, reintentos, auditoría y aprobaciones.
5. Integración opcional con Notion y GitHub.
6. Servicio remoto/event-driven y monitorización, sin prometer disponibilidad gratuita ilimitada.

## Contexto operativo del usuario

El usuario trabaja desde ChatGPT Free en Android. Sus conversaciones pueden alcanzar límites de uso y quedar temporalmente bloqueadas hasta que se restablezca la cuota indicada por ChatGPT (en su experiencia, a veces hasta 24 horas). Por ello, **no debe pedírsele que vuelva a explicar el proyecto, sus preferencias o decisiones ya documentadas**.

Antes de pedir contexto:
1. Leer este README y `docs/USER_CONTEXT.md`.
2. Consultar la continuidad y Memoria Maestra en Notion.
3. Revisar el estado de GitHub y los últimos commits.
4. Preguntar únicamente por datos que realmente falten o hayan cambiado.

Esta nota describe la experiencia y restricción operativa comunicada por el usuario; no afirma que todos los usuarios de ChatGPT Free tengan exactamente el mismo límite.
