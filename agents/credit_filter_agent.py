import json
import asyncio
import httpx
from datetime import datetime, timezone
from functools import partial

from langchain_groq import ChatGroq

from config.config import settings
from prompts.fira_evaluator import build_evaluation_prompt
from tools.hubspot import get_pending_contacts, update_contact_verdict
from lib.whatsapp.twillio.twilio_service import TwilioService


# ── Mensajes WhatsApp ────────────────────────────────────────────────────────

def _msg_rechazo(nombre: str, motivo: str, score: int) -> str:
    return (
        f"Estimado/a *{nombre}*,\n\n"
        f"Hemos analizado su solicitud de crédito con Agrocapital.\n\n"
        f"Lamentablemente, su solicitud *no cumple* con los criterios de elegibilidad "
        f"del programa FIRA en este momento.\n\n"
        f"*Motivo:* {motivo or 'No cumple con los requisitos mínimos del programa.'}\n"
        f"*Score de cumplimiento:* {score}%\n\n"
        f"Si desea más información o cree que hay un error, comuníquese con "
        f"Agrocapital al número de atención a clientes.\n\n"
        f"_Mensaje generado automáticamente por el sistema FIRA de Agrocapital._"
    )

def _msg_viable_equipo(nombre: str, score: int, revision: bool, contact_id: str) -> str:
    revision_tag = " ⚠️ *REQUIERE REVISIÓN HUMANA*" if revision else ""
    return (
        f"🟢 *Nuevo solicitante VIABLE*{revision_tag}\n\n"
        f"*Nombre:* {nombre}\n"
        f"*ID HubSpot:* {contact_id}\n"
        f"*Score FIRA:* {score}%\n\n"
        f"Por favor, revisar expediente en HubSpot para continuar el proceso."
    )


# ── Envío async de WhatsApp (TwilioService es síncrono → executor) ───────────

async def _send_whatsapp_async(twilio: TwilioService, to: str, body: str) -> bool:
    """
    TwilioService.send_whatsapp_message es bloqueante (HTTP síncrono).
    Lo corremos en un thread executor para no bloquear el event loop.
    """
    loop = asyncio.get_event_loop()
    fn = partial(twilio.send_whatsapp_message, to_number=to, body=body)
    return await loop.run_in_executor(None, fn)


# ── Helpers internos ─────────────────────────────────────────────────────────

def _normalize_contact(raw: dict) -> dict:
    """Mapea el payload crudo de HubSpot al esquema que espera el prompt FIRA."""
    p = raw.get("properties", {})
    return {
        "hubspot_contact_id": raw.get("id"),
        "nombre": f"{p.get('firstname', '')} {p.get('lastname', '')}".strip(),
        "email": p.get("email"),
        "telefono": p.get("phone"),
        "fuente_origen": p.get("hs_lead_source", "Social Media"),
        "edad": p.get("edad"),
        "actividad_economica": p.get("actividad_economica"),
        "cartera_vencida": p.get("cartera_vencida"),
        "zona": p.get("zona"),
        "destino_credito": p.get("destino_credito"),
        "monto_solicitado_mxn": p.get("monto_solicitado_mxn"),
        "tenencia_tierra": p.get("tenencia_tierra"),
    }


def _parse_llm_response(raw_text: str) -> dict:
    """
    Extrae JSON limpio aunque el modelo haya envuelto la respuesta en markdown.
    Guard defensivo: no debería ocurrir con temperature=0, pero es real.
    """
    text = raw_text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1].lstrip("json").strip()
    return json.loads(text)


async def _evaluate_single(llm: ChatGroq, applicant: dict) -> dict:
    prompt = build_evaluation_prompt(applicant)
    response = await llm.ainvoke(prompt)
    return _parse_llm_response(response.content)


# ── Pipeline principal ───────────────────────────────────────────────────────

async def run_credit_filter(batch_size: int = 10) -> dict:
    """
    Pipeline principal FIRA + WhatsApp:
    1. Obtiene contactos NEW desde HubSpot
    2. Evalúa cada uno con Groq llama-3.3-70b + reglas FIRA
    3. Escribe veredicto de vuelta en HubSpot
    4. Notifica por WhatsApp:
       - RECHAZADO → mensaje al solicitante explicando motivo
       - VIABLE     → alerta al equipo Agrocapital
    5. Retorna resumen para logging
    """
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.GROQ_API_KEY,
        temperature=0,
    )

    # Twilio: se inicializa aquí; si no hay credenciales, `client` queda en None
    # y send_whatsapp_message() simplemente imprime el error sin crashear el pipeline.
    twilio = TwilioService()
    whatsapp_enabled = twilio.client is not None
    if not whatsapp_enabled:
        print("⚠ WhatsApp DESHABILITADO: credenciales Twilio no configuradas en .env")

    # Número del equipo Agrocapital — debe estar en .env como AGROCAPITAL_WHATSAPP_NUMBER
    agrocapital_number = getattr(settings, "AGROCAPITAL_WHATSAPP_NUMBER", None)

    run_ts = datetime.now(timezone.utc).isoformat()
    print(f"[{run_ts}] Agente FIRA Agrocapital iniciado | batch={batch_size}")

    contacts_raw = await get_pending_contacts(limit=batch_size)
    print(f"→ {len(contacts_raw)} contactos NEW obtenidos de HubSpot\n")

    summary = {"run_timestamp": run_ts, "viables": [], "rechazados": [], "errores": []}

    for raw in contacts_raw:
        applicant = _normalize_contact(raw)
        cid      = applicant["hubspot_contact_id"]
        nombre   = applicant["nombre"] or cid
        telefono = applicant.get("telefono")

        try:
            evaluation   = await _evaluate_single(llm, applicant)
            crm_updated  = await update_contact_verdict(cid, evaluation)

            veredicto = evaluation["veredicto"]
            score     = evaluation["score_cumplimiento"]
            revision  = evaluation["requiere_revision_humana"]

            entry = {"id": cid, "nombre": nombre, "score": score, "revision_humana": revision}

            # ── Notificaciones WhatsApp ──────────────────────────────────────
            wa_status = "SKIP"

            if whatsapp_enabled:
                if veredicto == "RECHAZADO" and telefono:
                    motivo = evaluation.get("motivo_rechazo", "")
                    msg = _msg_rechazo(nombre, motivo, score)
                    sent = await _send_whatsapp_async(twilio, telefono, msg)
                    wa_status = "OK" if sent else "FALLO"
                    entry["motivo"] = motivo

                elif veredicto == "VIABLE" and agrocapital_number:
                    msg = _msg_viable_equipo(nombre, score, revision, cid)
                    sent = await _send_whatsapp_async(twilio, agrocapital_number, msg)
                    wa_status = "OK" if sent else "FALLO"

                elif veredicto == "RECHAZADO" and not telefono:
                    wa_status = "SIN_TELEFONO"
                elif veredicto == "VIABLE" and not agrocapital_number:
                    wa_status = "SIN_NUMERO_EQUIPO"

            # ── Registro en summary ──────────────────────────────────────────
            if veredicto == "VIABLE":
                summary["viables"].append(entry)
            else:
                entry.setdefault("motivo", evaluation.get("motivo_rechazo"))
                summary["rechazados"].append(entry)

            status_icon  = "✓" if veredicto == "VIABLE" else "✗"
            revision_tag = " [REVISIÓN HUMANA]" if revision else ""
            print(
                f"  {status_icon} {nombre} → {veredicto} "
                f"(score: {score}%){revision_tag} "
                f"| CRM: {'OK' if crm_updated else 'FALLO'} "
                f"| WA: {wa_status}"
            )

        except json.JSONDecodeError:
            print(f"  ✗ {nombre} → ERROR: respuesta LLM no es JSON válido")
            summary["errores"].append({"id": cid, "error": "json_parse_error"})
        except httpx.HTTPStatusError as e:
            print(f"  ✗ {nombre} → ERROR HubSpot HTTP {e.response.status_code}: {e.response.text[:200]}")
            summary["errores"].append({"id": cid, "error": f"hubspot_{e.response.status_code}"})
        except Exception as e:
            print(f"  ✗ {nombre} → ERROR inesperado: {e}")
            summary["errores"].append({"id": cid, "error": str(e)})

    print(f"\n{'='*60}")
    print(f"  Viables:    {len(summary['viables'])}")
    print(f"  Rechazados: {len(summary['rechazados'])}")
    print(f"  Errores:    {len(summary['errores'])}")
    print(f"{'='*60}\n")

    return summary
