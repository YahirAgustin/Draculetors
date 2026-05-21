"""
Herramientas (Tools) del Agente.

Aquí es donde los participantes del Hackathon registran sus herramientas.

╔══════════════════════════════════════════════════════════════════╗
║  🔧 PARTICIPANTES:                                               ║
║  Para agregar tu propia herramienta al agente:                   ║
║  1. Crea una función en un archivo dentro de tools/              ║
║  2. Decórala con @tool de langchain_core.tools                   ║
║  3. Impórtala en este archivo y agrégala a la lista `ALL_TOOLS`  ║
╚══════════════════════════════════════════════════════════════════╝
"""

from tools.cloud.aws.aws_tools import (
    upload_file_to_s3,
    download_file_from_s3,
    extract_text_with_ocr,
)
from tools.whatsapp.whatsapp_tools import send_whatsapp_message

# =================================================================
# 📋 LISTA MAESTRA DE HERRAMIENTAS
# El motor del agente consumirá esta lista automáticamente.
# =================================================================
ALL_TOOLS = [
    upload_file_to_s3,
    download_file_from_s3,
    extract_text_with_ocr,
    send_whatsapp_message,
]

__all__ = [
    "ALL_TOOLS",
    "upload_file_to_s3",
    "download_file_from_s3",
    "extract_text_with_ocr",
    "send_whatsapp_message",
]
