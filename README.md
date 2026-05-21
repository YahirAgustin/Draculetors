# Agent Starter Kit - BuildDay: Agentes Inteligentes

¡Bienvenido al Agent Starter Kit! Este repositorio ha sido diseñado como base para el BuildDay centrado en la creación de Agentes Inteligentes. Proporciona una arquitectura robusta, modular y lista para producción utilizando LangGraph, LangChain y diversas integraciones de herramientas.

> **Tu Misión:** Analizar, comprender y extender las capacidades de este kit para desarrollar agentes autónomos que resuelvan el problema planteado. 

## Descripción General

Este starter kit permite a los desarrolladores enfocarse en la lógica de negocio y el comportamiento de sus agentes, abstrayendo la complejidad de la orquestación, la persistencia de memoria y la conexión con modelos de lenguaje (LLMs).

### Características Principales:
- Orquestación con LangGraph: Motor basado en grafos de estado para agentes ReAct.
- Multi-Provider: Soporte nativo para OpenAI, Google (Gemini) y Anthropic.
- Persistencia de Sesión: Base de datos SQLite integrada para mantener el historial de conversaciones de forma asíncrona.
- Tooling Ready: Herramientas pre-configuradas para AWS (S3) y mensajería (WhatsApp vía Twilio).

---

## Estructura del Proyecto

```text
agents-starterkit/
├── agents/             # Define aquí tus agentes personalizados
├── config/             # Configuración centralizada y variables de entorno
├── core/               # Motor de orquestación (No modificar)
├── lib/                # Librerías base y lógica compartida
├── memory/             # Gestión de memoria semántica (Mem0)
├── prompts/            # Almacén de system prompts
├── tools/              # Definición de herramientas (Tools) para los agentes
└── main.py             # Punto de entrada de la aplicación
```

---

## Configuración Inicial

1. Instalar dependencias:
   Este proyecto utiliza uv para la gestión de paquetes, instala toda las dependencias utilizando el comando:
   ```bash
   uv sync
   ```

2. Configurar variables de entorno:
   Copia el archivo de ejemplo y rellena tus credenciales:
   ```bash
   cp .env.example .env
   ```
   Asegúrate de configurar al menos una API Key de LLM (OPENAI_API_KEY, GEMINI_API_KEY o ANTHROPIC_API_KEY).

---

## Guía de Desarrollo

### 1. El Motor Core (core/)
El archivo core/engine.py contiene la función create_deep_agent. Esta función se encarga de:
- Instanciar el LLM seleccionado.
- Configurar el checkpointer de SQLite para la persistencia.
- Compilar el grafo del agente con las herramientas proporcionadas.

Nota: Se recomienda no modificar los archivos dentro de core/ para asegurar la estabilidad del motor.

### 2. Creando un Agente
Para crear un nuevo agente, debes definir su System Prompt y las Tools que podrá utilizar.

```python
from core.engine import create_deep_agent, run_agent
from tools.whatsapp.whatsapp_tools import send_message_tool

# 1. Definir el comportamiento
SYSTEM_PROMPT = "Eres un asistente experto en logística..."

# 2. Crear el agente
agent, conn = await create_deep_agent(
    system_prompt=SYSTEM_PROMPT,
    tools=[send_message_tool],
    provider="openai"
)

# 3. Ejecutar una tarea
response = await run_agent(agent, "Hola, ¿puedes enviar un mensaje?", thread_id="user_123")
```

### 3. Añadiendo Herramientas (Tools)
Puedes extender las capacidades de tu agente añadiendo funciones en el directorio tools/. Cualquier función decorada con @tool de LangChain puede ser inyectada en el motor.

---

## Integraciones Disponibles

### WhatsApp (Twilio)
Permite a los agentes enviar y recibir mensajes de WhatsApp. Configura tus credenciales de Twilio en el .env para habilitarlo.

### AWS Cloud
Incluye herramientas para interactuar con servicios de AWS como S3, permitiendo al agente persistir o leer documentos en la nube.

### Mem0 (Memoria Semántica)
A diferencia de la memoria de sesión (que se olvida al cerrar el chat), Mem0 permite que el agente "recuerde" detalles del usuario a través de diferentes sesiones. 

Nota: Esto puede tener fallos. Si decides utilizar la memoria de Mem0, asegúrate de que esto funcione correctamente. Revisa los docs: https://docs.mem0.ai/introduction

---

## BuildDay: El Reto
Utiliza este kit para construir un agente que resuelva un problema real. Enfócate en:
1. Diseñar un system_prompt efectivo en prompts/.
2. Implementar herramientas útiles en tools/.
3. Orquestar la lógica en un nuevo archivo dentro de agents/.

¡Mucha suerte y happy coding!

---

## Ejemplo: Agente Validador de Documentos

El archivo `example/agent_demo.py` muestra un flujo autónomo de cumplimiento.

### Flujo del Agente:
1. Recibe la ruta local del documento enviado por el proveedor.
2. Sube el documento a AWS S3 para persistencia y trazabilidad.
3. Extrae el texto del documento mediante OCR (AWS Textract).
4. Valida que el tipo de documento sea el correcto y que los datos coincidan con lo esperado.
5. Toma una decisión automática:
    - Si es APROBADO: Emite un reporte de validación positiva.
    - Si es RECHAZADO: Envía una notificación por WhatsApp al proveedor explicando el motivo y solicitando la corrección.

### Ejecución del Demo:
```bash
uv run python example/agent_demo.py
```

Este ejemplo demuestra cómo el agente puede tomar decisiones complejas utilizando herramientas externas y cerrar procesos de negocio de forma autónoma.
