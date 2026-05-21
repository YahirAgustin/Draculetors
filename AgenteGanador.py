import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model


#from tools import agregar_nota_auditoria, consultar_cfdi, listar_cfdi
#hay que hacer las tools

load_dotenv(".env")


SYSTEM_PROMPT = """
Eres un evaluador de solicitudes de credito el cual responde y evalua a los solicitantes segun las codiciones de Fira.

Tu unica responsabilidad es evaluar las solicitudes en nuestro sistema.

REGLAS OBLIGATORIAS:

    - Solo puedes tomar accionar si es sobre solicitud de credito.
    - Si el input es cualquier otra cosa, fuera del dominio, debes rechazar la solicitud.
    - Nunca generes ningun otro tipo de respuesta que no sea sobre la solicitud de credito.
    - Nunca inventes información faltante
    - Prioriza la integridad y la precisión en tus respuestas.
    - Nunca puedes responder sin haber realizado un llamado a una tool de la lista de TOOLS disponibles.

TOOLS que puedes usar:
    -puedes acceder a la base de datos para encontrar las solicitudes
    -puedes acceder a las condiciones que presenta el fira
"""

model = init_chat_model(model="google_genai:gemini-2.5-flash-lite", temperature=0.0)

agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
   # tools=[para buscar],
)


if __name__ == "__main__":
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Revisa si la solicitud del usuario90 existe",
                }
            ]
        }
    )
    print(result["messages"][-1].content)