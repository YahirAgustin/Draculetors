"""
Motor de Orquestación de Agentes Profundos (Deep Agents Engine).

╔══════════════════════════════════════════════════════════════════╗
║  ⚠️  PARTICIPANTES: NO MODIFICAR ESTE ARCHIVO                  ║
║                                                                  ║
║  Este módulo contiene el motor de orquestación genérico del      ║
║  agente, el manejo de persistencia local y el binding de         ║
║  herramientas.                                                   ║
╚══════════════════════════════════════════════════════════════════╝
"""

import aiosqlite
from typing import Any, Callable, List, Optional, Sequence, Tuple

from langchain_core.messages import SystemMessage, BaseMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState

from core.llm_factory import get_llm


def _build_dynamic_prompt(
    base_system_prompt: str,
    prompt_modifier: Optional[Callable[[dict], str]] = None
) -> Callable[[dict], List[BaseMessage]]:
    """
    Construye la función inyectora para el parámetro `prompt` de create_react_agent.
    
    Args:
        base_system_prompt: Prompt de sistema base del agente.
        prompt_modifier: Callable opcional que recibe el estado actual y devuelve
                         texto adicional para concatenar al prompt de sistema.
    """
    def prompt_injector(state: dict) -> List[BaseMessage]:
        modifier_text = ""
        if prompt_modifier:
            try:
                modifier_text = prompt_modifier(state)
            except Exception as e:
                print(f"⚠️ [Core Engine] Error en prompt_modifier: {e}")
                
        full_prompt = base_system_prompt
        if modifier_text:
            full_prompt += f"\n\n{modifier_text}"
            
        return [SystemMessage(content=full_prompt)] + state.get("messages", [])
        
    return prompt_injector


async def create_deep_agent(
    system_prompt: str,
    tools: Sequence[BaseTool],
    *,
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    db_path: str = "./checkpoints.db",
    prompt_modifier: Optional[Callable[[dict], str]] = None,
    **llm_kwargs: Any
) -> Tuple[Any, aiosqlite.Connection]:
    """
    Instancia y compila un agente ReAct profundo usando create_react_agent y persistencia asíncrona con SQLite.
    
    Args:
        system_prompt: Prompt de sistema de negocio del agente.
        tools: Secuencia de tools compatibles con LangChain.
        provider: Proveedor de LLM ('openai', 'gemini', 'anthropic').
        model_name: Nombre específico del modelo.
        db_path: Ruta al archivo SQLite de base de datos de checkpoints.
        prompt_modifier: Callable para modificar dinámicamente el prompt con contexto externo.
        **llm_kwargs: Parámetros adicionales a pasar al constructor del LLM.
        
    Returns:
        Un tuple conteniendo:
        - El agente compilado ejecutable (.ainvoke, .astream)
        - La conexión a SQLite asíncrona del checkpointer (debe ser cerrada por el invocador).
    """
    # 1. Instanciar LLM usando el factory
    llm = get_llm(provider=provider, model_name=model_name, **llm_kwargs)
    
    # 2. Configurar el modificador dinámico de prompt
    dynamic_prompt = _build_dynamic_prompt(
        base_system_prompt=system_prompt,
        prompt_modifier=prompt_modifier
    )
    
    # 3. Inicializar checkpointer de persistencia asíncrono
    conn = await aiosqlite.connect(db_path)
    checkpointer = AsyncSqliteSaver(conn)
    await checkpointer.setup()
    
    # 4. Compilar el agente preconstruido
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=dynamic_prompt,
        checkpointer=checkpointer
    )
    
    return agent, conn


async def run_agent(
    agent: Any,
    task: str,
    *,
    thread_id: str,
    recursion_limit: int = 50
) -> str:
    """
    Ejecuta el agente para una tarea dada o reanuda un hilo de conversación existente.
    
    Args:
        agent: Instancia del agente compilado (retornado por create_deep_agent).
        task: Mensaje del usuario o instrucción de negocio a ejecutar.
        thread_id: ID único del hilo de ejecución para persistencia y checkpointing.
        recursion_limit: Límite máximo de pasos en el grafo para prevenir loops infinitos.
        
    Returns:
        La respuesta final en texto plano del agente.
    """
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": recursion_limit
    }
    
    # El estado inicial del agente ReAct espera una lista de mensajes
    input_state = {"messages": [("user", task)]}
    
    # Ejecución asíncrona
    response = await agent.ainvoke(input_state, config=config)
    
    # Extraer el último mensaje (que debería ser la respuesta final del agente)
    messages = response.get("messages", [])
    if messages:
        return messages[-1].content

        
    return "Error: No se recibió ninguna respuesta del agente."

