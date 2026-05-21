"""
Factory de Proveedores de LLM.
"""

import os
from typing import Any
from langchain_core.language_models.chat_models import BaseChatModel
from config.config import settings


def get_llm(
    provider: str | None = None,
    model_name: str | None = None,
    **kwargs: Any
) -> BaseChatModel:
    """
    Factory para retornar la instancia correcta de LLM basada en el provider especificado.
    Soporta: 'openai', 'gemini' (google), y 'anthropic'.
    
    Args:
        provider: El nombre del proveedor (openai, gemini, anthropic). Si es None,
                  se lee de config.LLM_PROVIDER.
        model_name: El nombre del modelo específico. Si es None, se lee de config.LLM_MODEL.
        **kwargs: Parámetros adicionales para el modelo (ej. temperature, streaming, etc.)
        
    Returns:
        Una instancia de BaseChatModel compatible con LangChain/LangGraph.
    """
    provider = (provider or settings.LLM_PROVIDER or "openai").lower()
    
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        
        # Validar credenciales
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY no configurada. "
                "Asegúrate de agregar tu key en el archivo .env"
            )
            
        return ChatOpenAI(
            model=model_name or settings.LLM_MODEL or "gpt-4o",
            api_key=api_key,
            temperature=kwargs.pop("temperature", 0),
            **kwargs
        )
        
    elif provider in ("gemini", "google"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Validar credenciales
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY no configurada. "
                "Asegúrate de agregar tu key en el archivo .env"
            )
            
        return ChatGoogleGenerativeAI(
            model=model_name or settings.LLM_MODEL or "gemini-1.5-flash",
            google_api_key=api_key,
            temperature=kwargs.pop("temperature", 0),
            **kwargs
        )
        
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        
        # Validar credenciales
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY no configurada. "
                "Asegúrate de agregar tu key en el archivo .env"
            )
            
        return ChatAnthropic(
            model=model_name or settings.LLM_MODEL or "claude-3-5-sonnet-latest",
            api_key=api_key,
            temperature=kwargs.pop("temperature", 0),
            **kwargs
        )
        
    else:
        raise ValueError(f"Provider de LLM no soportado: '{provider}'. Usar 'openai', 'gemini' o 'anthropic'.")
