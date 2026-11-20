import sys
from datetime import datetime
from memory import save_memory, list_memories


def separator():
    print("=" * 48)


def validate_response(response, agent):
    if not isinstance(response, str) or not response.strip():
        raise RuntimeError(
            f"{agent} produjo una respuesta vacia o invalida."
        )
    return response


def save_phase(content, category, phase):
    try:
        save_memory(content, category)
    except Exception as exc:
        raise RuntimeError(
            f"No se pudo guardar la fase: {phase}."
        ) from exc


def run_agent(name, message, function, category):
    response = validate_response(function(message), name)
    save_phase(response, category, name)
    print(response)
    return response


def ceo(objective):
    return (
        f"OBJETIVO: {objective}\n"
        "MISION: Desarrollar AI-EMPIRE progresivamente, "
        "con presupuesto cero y supervision humana."
    )


def estratega(mission):
    return (
        "MISION RECIBIDA DEL CEO:\n"
        + mission
        + """

ANALISIS ESTRATEGICO

Clientes:
- Comercios y pequenos negocios.
- Profesionales independientes.
- Empresas con redes sociales poco desarrolladas.

Oportunidades:
- Gestion de redes sociales.
- Creacion de publicaciones y videos.
- Calendarios de contenido.
- Auditorias digitales.

Estrategia:
Captacion mediante contacto directo y demostraciones.
"""
    )


def creadora(strategy):
    return (
        "ANALISIS RECIBIDO DEL ESTRATEGA:\n"
        + strategy
        + """

DISENO DE SERVICIOS

1. Gestion de redes sociales.
2. Creacion de contenido digital.
3. Marketing y calendarios de publicaciones.
4. Auditorias gratuitas.

Preparar muestras antes de ofrecer servicios.
"""
    )


def ejecutora(creation):
    return (
        "PROPUESTA RECIBIDA DE LA CREADORA:\n"
        + creation
        + """

PLAN OPERATIVO

1. Preparar presentacion profesional.
2. Crear tres muestras de contenido.
3. Identificar 30 negocios potenciales.
4. Preparar contactos personalizados.
5. Ofrecer auditorias gratuitas.
6. Registrar seguimiento.

No publicar ni gastar dinero sin autorizacion.
"""
    )


def main():
    separator()
    print("       AI-EMPIRE JARVIS 2.0")
    print("       ORQUESTADOR LOCAL")
    separator()

    print("\n[JARVIS] RECUERDOS RECIENTES")

    try:
        memories = list_memories(5)
    except Exception as exc:
        raise RuntimeError(
            "No se pudieron recuperar los recuerdos."
        ) from exc

    for item in memories:
        try:
            memory_id, category, content, created_at = item
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "Se encontro un recuerdo con formato invalido."
            ) from exc

        if not isinstance(category, str) or not isinstance(content, str):
            raise RuntimeError(
                "Un recuerdo contiene campos invalidos."
            )

        print(f"- [{category}] {content[:150]}")

    objective = input(
        "\nCual es nuestro objetivo?\n> "
    ).strip()

    if not objective:
        print("Objetivo vacio.")
        return

    save_phase(objective, "objetivo", "objetivo")

    print("\n[CEO] Creando mision...")
    mission = run_agent(
        "CEO", objective, ceo, "mision"
    )

    print("\n[ESTRATEGA] Analizando...")
    strategy = run_agent(
        "ESTRATEGA", mission, estratega, "estrategia"
    )

    print("\n[CREADORA] Disenando...")
    creation = run_agent(
        "CREADORA", strategy, creadora, "creacion"
    )

    print("\n[EJECUTORA] Preparando acciones...")
    execution = run_agent(
        "EJECUTORA", creation, ejecutora, "ejecucion"
    )

    summary = (
        f"OBJETIVO:\n{objective}\n\n"
        f"MISION:\n{mission}\n\n"
        f"ESTRATEGIA:\n{strategy}\n\n"
        f"CREACION:\n{creation}\n\n"
        f"EJECUCION:\n{execution}"
    )

    save_phase(summary, "resultado", "resultado")

    separator()
    print("[JARVIS] PROCESO COMPLETADO")
    print("Todas las fases se han guardado.")
    print("Fecha:", datetime.now().strftime("%d/%m/%Y %H:%M"))
    separator()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nEjecucion interrumpida.")
        sys.exit(130)
    except Exception as exc:
        print(f"\n[JARVIS] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
