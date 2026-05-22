"""
webhook.py — Servidor de entrada para mensajes WhatsApp vía Twilio
Flujo: Cliente envía datos por WhatsApp → Twilio hace POST aquí →
       Evaluamos con FIRA → Respondemos al cliente en el mismo chat
"""
from fastapi import FastAPI, Form
from fastapi.responses import Response
from langchain_groq import ChatGroq
from config.config import settings
from agents.credit_filter_agent import _evaluate_single, _send_whatsapp_async
from lib.whatsapp.twillio.twilio_service import TwilioService

app = FastAPI()
twilio = TwilioService()

EMPTY_TWIML = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'

def _fix_mx_number(raw: str) -> str:
    """
    Twilio recibe números mexicanos como +526XXXXXXXXX (sin el 1 móvil).
    WhatsApp los tiene registrados como +5216XXXXXXXXX.
    Detectamos: +52 + exactamente 10 dígitos → insertamos el 1.
    """
    number = raw.replace("whatsapp:", "").strip()
    if number.startswith("+52") and len(number) == 13:
        number = "+521" + number[3:]
    return number

HELP_MSG = """👋 *Agente FIRA - Agrocapital*

Para evaluar tu solicitud de crédito, envía tus datos en este formato:

Nombre: [tu nombre completo]
Edad: [tu edad]
Actividad: [qué produces, ej: Maíz, Sorgo, Frijol]
Zona: [tu estado o región]
Monto: [monto solicitado en pesos]
Tierra: [Ejidal, Pequeña propiedad, o Rentada]
Cartera vencida: [Sí o No]

Ejemplo:
Nombre: Juan Pérez
Edad: 42
Actividad: Maíz de temporal
Zona: Sinaloa
Monto: 150000
Tierra: Ejidal
Cartera vencida: No"""


def _parse_message(body: str) -> dict | None:
    """
    Extrae los campos del mensaje en formato clave: valor.
    Retorna None si el mensaje no tiene el formato esperado.
    """
    lines = body.strip().splitlines()
    data = {}
    for line in lines:
        if ":" in line:
            key, _, value = line.partition(":")
            data[key.strip().lower()] = value.strip()

    # Campo mínimo requerido para intentar evaluación
    if "nombre" not in data:
        return None

    # Normalización de claves al esquema FIRA
    cartera_raw = data.get("cartera vencida", "no").lower()
    cartera = "true" if cartera_raw in ("sí", "si", "s", "yes", "true") else "false"

    return {
        "hubspot_contact_id": "whatsapp_inbound",
        "nombre":              data.get("nombre", "Solicitante"),
        "email":               None,
        "telefono":            None,
        "fuente_origen":       "WhatsApp",
        "edad":                data.get("edad"),
        "actividad_economica": data.get("actividad"),
        "cartera_vencida":     cartera,
        "zona":                data.get("zona"),
        "destino_credito":     data.get("actividad"),
        "monto_solicitado_mxn": data.get("monto"),
        "tenencia_tierra":     data.get("tierra"),
    }


def _build_reply(nombre: str, evaluation: dict) -> str:
    veredicto = evaluation["veredicto"]
    score     = evaluation["score_cumplimiento"]
    revision  = evaluation["requiere_revision_humana"]
    motivo    = evaluation.get("motivo_rechazo", "")

    if veredicto == "VIABLE":
        revision_tag = "\n\n⚠️ *Un asesor revisará tu caso personalmente.*" if revision else ""
        return (
            f"✅ *Estimado/a {nombre}, su solicitud es VIABLE*\n\n"
            f"Score de cumplimiento FIRA: *{score}%*\n\n"
            f"Un asesor de Agrocapital se pondrá en contacto contigo "
            f"para continuar el proceso de crédito.{revision_tag}"
        )
    else:
        return (
            f"❌ *Estimado/a {nombre}, su solicitud no es elegible en este momento*\n\n"
            f"Score de cumplimiento FIRA: *{score}%*\n"
            f"Motivo: {motivo or 'No cumple con los requisitos mínimos del programa FIRA.'}\n\n"
            f"Para más información comuníquese con Agrocapital."
        )


def _twiml(message: str) -> str:
    # Escapar caracteres especiales XML
    safe = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Message>{safe}</Message></Response>"
    )


@app.post("/whatsapp")
async def whatsapp_inbound(
    Body: str = Form(...),
    From: str = Form(...),
):
    """
    Endpoint que Twilio llama cuando llega un WhatsApp entrante.
    Debe responder con TwiML en < 15 segundos (límite de Twilio).
    """
    print(f"\n📩 Mensaje entrante de {From}: {Body[:80]}")

    applicant = _parse_message(Body)

    # Mensaje no reconocido → instrucciones
    if applicant is None:
        to_number = _fix_mx_number(From)
        await _send_whatsapp_async(twilio, to_number, HELP_MSG)
        return Response(content=EMPTY_TWIML, media_type="application/xml")

    # Evaluación FIRA
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.GROQ_API_KEY,
        temperature=0,
    )

    # Corregir número mexicano antes de responder
    to_number = _fix_mx_number(From)

    try:
        evaluation = await _evaluate_single(llm, applicant)
        reply = _build_reply(applicant["nombre"], evaluation)
        print(f"  → Veredicto: {evaluation['veredicto']} | score: {evaluation['score_cumplimiento']}%")
    except Exception as e:
        print(f"  → ERROR evaluación: {e}")
        reply = (
            "Lo sentimos, ocurrió un error procesando su solicitud. "
            "Por favor intente nuevamente en unos minutos."
        )

    # Enviamos activamente con número corregido en lugar de TwiML reply
    # (TwiML usa el From tal cual y falla con números MX sin el 1)
    sent = await _send_whatsapp_async(twilio, to_number, reply)
    print(f"  → WhatsApp enviado a {to_number}: {'OK' if sent else 'FALLO'}")

    return Response(content=EMPTY_TWIML, media_type="application/xml")


@app.get("/health")
def health():
    return {"status": "ok", "agent": "FIRA Agrocapital"}
