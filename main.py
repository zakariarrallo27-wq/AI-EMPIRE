import os
from openai import OpenAI

MODEL = os.getenv("AI_EMPIRE_MODEL", "gpt-4.1-mini")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

AGENTS = [
    ("Estratega", "Analiza el problema, el mercado y las oportunidades. Distingue hechos, hipótesis y dudas. Propón una dirección concreta."),
    ("Creadora", "A partir del análisis anterior, diseña una oferta o producto sencillo. Explica para quién es, qué problema resuelve y cómo validarlo."),
    ("Ejecutora", "Convierte las propuestas anteriores en un plan práctico de 3 pasos. Señala dependencias, riesgos y la primera acción medible.")
]

def ask_agent(name, role, shared_context):
    prompt = (
        f"Eres el agente {name} de AI-EMPIRE. Tu función: {role}\n\n"
        "Colabora con los otros agentes. No inventes datos ni afirmes haber ejecutado acciones. "
        "Si falta información, dilo y formula supuestos explícitos. Responde en español.\n\n"
        f"Contexto compartido hasta ahora:\n{shared_context or 'Todavía no hay mensajes.'}"
    )
    response = client.responses.create(model=MODEL, input=prompt)
    return response.output_text.strip()

def main():
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Falta OPENAI_API_KEY. Configúrala como variable de entorno; nunca la guardes en GitHub.")
    topic = input("¿Qué problema u oportunidad deben trabajar los tres agentes? ").strip()
    if not topic:
        raise SystemExit("Escribe un tema para iniciar la colaboración.")
    transcript = f"Reto inicial del usuario: {topic}\n"
    for name, role in AGENTS:
        print(f"\n--- {name} está trabajando ---\n")
        answer = ask_agent(name, role, transcript)
        transcript += f"\n\n## {name}\n{answer}\n"
        print(answer)
    print("\n--- Fin de la primera ronda de AI-EMPIRE ---")

if __name__ == "__main__":
    main()
