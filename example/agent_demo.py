"""
Worker Validador de Documentos-- Ejemplo del Hackathon.

Demuestra un Agente Autonomo de Cumplimiento que recibe documentos de proveedores,
los procesa y valida sin intervencion humana.

Flujo autonomo que ejecuta el agente:
    1. Recibe la ruta local del documento que el proveedor "envio".
    2. Sube el documento a AWS S3 para persistencia y trazabilidad.
    3. Extrae el texto del documento con OCR (AWS Textract).
    4. Valida: el tipo de documento correcto y que los datos coincidan.
    5. Decision:
        APROBADO  -> Emite reporte de validacion positiva.
        RECHAZADO -> Envia WhatsApp empatico al proveedor pidiendo nuevo documento.


![TIP]: En un entorno real, los archivos deberian de llegar desde algun canal de comunicación
       y luego ejecutar todo el flujo :)

Ejecucion:
    uv run python example/agent_demo.py
"""

import asyncio
import os
import sys
import uuid
from dataclasses import dataclass
from typing import Optional

# Asegurar que el directorio raiz esta en el PATH para importaciones relativas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.config import settings
from core.engine import create_deep_agent, run_agent
from prompts.validator import VALIDATOR_SYSTEM_PROMPT
from tools import ALL_TOOLS


# =============================================================================
# MODELO DE EVENTO -- "Documento Recibido de Proveedor"
# =============================================================================
@dataclass
class DocumentoRecibido:
    """
    Representa un documento que llega del proveedor al sistema.

    Attributes:
        archivo_local: Ruta al archivo en el sistema local (simulando la recepcion).
        tipo_esperado: Tipo de documento que el proceso KYC/KYB requiere.
        telefono_proveedor: Numero del proveedor para notificacion por WhatsApp.
        nombre_proveedor: Nombre del proveedor para personalizar la comunicacion.
        datos_esperados: Datos clave que el documento debe contener/coincidir.
    """

    archivo_local: str
    tipo_esperado: str
    telefono_proveedor: str
    nombre_proveedor: str
    datos_esperados: Optional[dict] = None


# =============================================================================
# WORKER PRINCIPAL
# =============================================================================
async def procesar_documento(
    evento: DocumentoRecibido,
    db_path: str = "./validator_checkpoints.db",
) -> str:
    """
    Ejecuta el flujo completo de validacion documental de forma autonoma.

    El agente recibe la ruta local del archivo, lo sube a S3, hace OCR,
    valida tipo y datos, y notifica por WhatsApp en caso de rechazo.

    Args:
        evento: El evento con los datos del documento recibido.
        db_path: Ruta del archivo SQLite para checkpointing del agente.

    Returns:
        El reporte final emitido por el agente (str).
    """
    thread_id: str = str(uuid.uuid4())
    nombre_archivo: str = os.path.basename(evento.archivo_local)

    print("=" * 68)
    print("AGENTE VALIDADOR DE DOCUMENTOS")
    print(f"Documento recibido  : {nombre_archivo}")
    print(f"Ruta local          : {evento.archivo_local}")
    print(f"Tipo esperado       : {evento.tipo_esperado}")
    print(f"Proveedor           : {evento.nombre_proveedor}")
    print(f"Telefono            : {evento.telefono_proveedor}")
    if evento.datos_esperados:
        print(f"Datos a verificar   : {evento.datos_esperados}")
    print(f"Thread ID           : {thread_id}")
    print(f"SQLite DB           : {db_path}")
    print("-" * 68)

    # Verificar que el archivo realmente existe antes de enviar al agente
    if not os.path.exists(evento.archivo_local):
        print(f"ERROR: El archivo '{evento.archivo_local}' no existe localmente.")
        return "Error: Archivo no encontrado."

    print("\nCompilando el Agente Validador ARIA...")
    agent, db_conn = await create_deep_agent(
        system_prompt=VALIDATOR_SYSTEM_PROMPT,
        tools=ALL_TOOLS,
        provider=settings.LLM_PROVIDER,
        model_name=settings.LLM_MODEL,
        db_path=db_path,
    )

    # Construir la orden de trabajo con todos los datos del evento
    datos_str = ""
    if evento.datos_esperados:
        datos_str = "\nDatos clave a verificar en el documento:\n" + "\n".join(
            f"  - {k}: {v}" for k, v in evento.datos_esperados.items()
        )

    orden_de_trabajo: str = (
        f"NUEVO DOCUMENTO RECIBIDO DE PROVEEDOR:\n"
        f"- Nombre del proveedor : {evento.nombre_proveedor}\n"
        f"- Telefono del proveedor: {evento.telefono_proveedor}\n"
        f"- Archivo local recibido: {evento.archivo_local}\n"
        f"- Tipo de documento esperado: {evento.tipo_esperado}\n"
        f"{datos_str}\n\n"
        f"Ejecuta el flujo de validacion completo de forma autonoma:\n"
        f"1. Sube el archivo a S3 usando object_name='kyc/{nombre_archivo}'\n"
        f"2. Extrae el texto con OCR desde la ruta local '{evento.archivo_local}'\n"
        f"3. Valida si el documento es un '{evento.tipo_esperado}' valido\n"
        f"4. Verifica que los datos del documento coincidan con los datos esperados\n"
        f"5. Si esta APROBADO: emite el reporte de aprobacion\n"
        f"6. Si esta RECHAZADO: envia un WhatsApp a {evento.telefono_proveedor} "
        f"explicando el motivo del rechazo y solicitando que envie el documento correcto, "
        f"luego emite el reporte de rechazo.\n\n"
        f"Finaliza SIEMPRE emitiendo el REPORTE DE VALIDACION ARIA completo."
    )

    try:
        print("\nAgente en ejecucion autonoma...\n")
        reporte_final: str = await run_agent(
            agent=agent,
            task=orden_de_trabajo,
            thread_id=thread_id,
        )

        print("\n" + "=" * 68)
        print("RESULTADO FINAL DEL AGENTE:")
        print("=" * 68)
        print(reporte_final)
        print("=" * 68)
        return reporte_final

    finally:
        await db_conn.close()
        print("\nConexion de persistencia cerrada correctamente.")
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print("Base de datos temporal eliminada.")
            except Exception:
                pass


# =============================================================================
# PUNTO DE ENTRADA -- SIMULACION DE EVENTOS ENTRANTES
# =============================================================================
async def main() -> None:
    """
    Simula la llegada de documentos de proveedores al sistema de validacion.

    Los archivos en example/assets/ representan los documentos que los
    proveedores "envian" a la plataforma

    Escenario A: El proveedor envia una Acta de Nacimiento -> debe ser validada.
    Escenario B: El mismo documento se evalua como Factura Comercial -> debe ser rechazado
                 porque el tipo de documento no coincide con lo solicitado.
    """
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")

    # ------------------------------------------------------------------
    # ESCENARIO A: Proveedor envia Acta de Nacimiento (documento correcto)
    # El agente debe: subir a S3 -> OCR -> validar -> APROBAR
    # ------------------------------------------------------------------
    print("\nESCENARIO A -- Proveedor envia Acta de Nacimiento\n")

    evento_a = DocumentoRecibido(
        archivo_local=os.path.join(assets_dir, "acta_nacimiento.png"),
        tipo_esperado="Acta de Nacimiento",
        telefono_proveedor="+526611223344",
        nombre_proveedor="Alejandro Gastelum",
        datos_esperados={
            "Nombre del titular": "Alejandro Gastelum",
            "Pais de emision": "Mexico",
        },
    )
    await procesar_documento(evento_a)

    print("\n\n" + "-" * 68 + "\n")

    # ------------------------------------------------------------------
    # ESCENARIO B: El sistema solicita una Factura Comercial pero el
    # proveedor vuelve a subir el Acta de Nacimiento (error del proveedor)
    # El agente debe: subir -> OCR -> detectar tipo incorrecto -> RECHAZAR + WhatsApp
    # ------------------------------------------------------------------
    print("ESCENARIO B -- Proveedor envia documento incorrecto (tipo no coincide)\n")

    evento_b = DocumentoRecibido(
        archivo_local=os.path.join(assets_dir, "acta_nacimiento.png"),
        tipo_esperado="Factura Comercial",
        telefono_proveedor="+526611223344",
        nombre_proveedor="Alejandro Gastelum",
        datos_esperados={
            "RFC del emisor": "MARC850101XYZ",
            "Monto minimo": "$1,000 MXN",
        },
    )
    await procesar_documento(evento_b)


if __name__ == "__main__":
    # Validar que al menos existan credenciales basicas de LLM
    if (
        not settings.OPENAI_API_KEY
        and not settings.GEMINI_API_KEY
        and not settings.ANTHROPIC_API_KEY
    ):
        print("Error: No se detecto ninguna API Key de LLM en el archivo .env")
        print(
            "Configura OPENAI_API_KEY, GEMINI_API_KEY o ANTHROPIC_API_KEY antes de ejecutar."
        )
        sys.exit(1)

    asyncio.run(main())
