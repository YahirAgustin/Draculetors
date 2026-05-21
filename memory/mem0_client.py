"""
Módulo de Integración Externa con Mem0 (Memoria Semántica de Largo Plazo).

Este módulo está desacoplado del motor principal. Permite guardar y recuperar
hechos contextuales sobre leads o procesos de venta usando Mem0.
"""

from typing import Any, Dict, List, Optional
from config.config import settings


class Mem0Client:
    """
    Cliente wrapper para Mem0.
    Permite encapsular la lógica de persistencia de hechos de largo plazo.
    """
    
    def __init__(self) -> None:
        try:
            from mem0 import MemoryClient
        except ImportError:
            raise ImportError(
                "La librería 'mem0ai' no está instalada. "
                "Ejecuta 'uv sync' o 'pip install mem0ai' para poder utilizar la memoria semántica."
            )
            
        api_key = settings.MEM0_API_KEY
        if not api_key:
            raise ValueError(
                "MEM0_API_KEY no configurada en las variables de entorno. "
                "Agrega MEM0_API_KEY en tu archivo .env"
            )
            
        self._client = MemoryClient(api_key=api_key)
        
    def add_memory(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Envía un conjunto de mensajes a Mem0 para extraer y almacenar hechos.
        
        Args:
            messages: Lista de mensajes, ej: [{"role": "user", "content": "Me llamo Carlos"}]
            user_id: ID único del cliente/lead
            metadata: Diccionario opcional con metadatos como process_id
        """
        try:
            self._client.add(
                messages=messages,
                user_id=user_id,
                metadata=metadata or {}
            )
        except Exception as e:
            print(f"[Mem0] Error al guardar memoria para el usuario {user_id}: {e}")
            
    def get_context(
        self,
        query: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> str:
        """
        Realiza una búsqueda semántica de recuerdos relevantes de un usuario.
        
        Args:
            query: La consulta o mensaje actual del usuario
            user_id: ID único del cliente/lead
            metadata: Filtros de metadatos opcionales (ej: {"process_id": "abc"})
            limit: Número máximo de memorias a recuperar
            
        Returns:
            Una cadena de texto formateada con viñetas conteniendo las memorias encontradas.
        """
        try:
            filters = {"user_id": user_id}
            if metadata:
                filters.update(metadata)
                
            results = self._client.search(
                query=query,
                filters=filters,
                limit=limit
            )
            
            if results and isinstance(results, dict) and "results" in results:
                memories = results["results"]
                if memories:
                    return "\n".join(f"- {m['memory']}" for m in memories)
                    
            elif isinstance(results, list):
                # Caso en que la respuesta del SDK sea directamente una lista
                if results:
                    return "\n".join(f"- {m['memory']}" for m in results if isinstance(m, dict) and "memory" in m)
                    
            return ""
        except Exception as e:
            print(f"[Mem0] Error al recuperar memoria para el usuario {user_id}: {e}")
            return ""
