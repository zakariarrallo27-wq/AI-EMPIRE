# AI-EMPIRE

Prototipo inicial de tres agentes que colaboran en una ronda compartida.

## Agentes
- Estratega: analiza oportunidades y supuestos.
- Creadora: convierte el análisis en una oferta o producto.
- Ejecutora: propone pasos concretos y medibles.

## Requisitos
Python 3.10+ y una clave de API de OpenAI.

## Ejecutar
1. Instala dependencias: `pip install -r requirements.txt`
2. Configura `OPENAI_API_KEY` como variable de entorno. No publiques la clave en GitHub.
3. Ejecuta: `python main.py`

El prototipo hace una ronda secuencial: cada agente recibe los mensajes anteriores. Todavía no es un servicio automático permanente ni tiene acceso web o memoria persistente.
