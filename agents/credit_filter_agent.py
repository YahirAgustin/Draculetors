import json
import asyncio
import httpx
from datetime import datetime, timezone

from langchain_groq import ChatGroq

from config.config import settings
from prompts.fira_evaluator import build_evaluation_prompt
from tools.hubspot import get_pending_contacts, update_contact_verdict


def _normalize_contact(raw: dict) -> dict:
    """Mapea el payload crudo de HubSpot al esquema que espera el prompt FIRA."""
    p = raw.get("properties", {})
    return {
        "hubspot_contact_id": raw.get("id"),
        "nombre": f"{p.get('firstname', '')} {p.get('lastname', '')}".strip(),
        "email": p.get("email"),
        "telefono": p.get("phone"),
        "fuente_origen": p.get("hs_lead_source", "Social Media"),
        # Campos custom FIRA — vendrán null si no fueron capturados en el CRM
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
    Esto no debería ocurrir con temperature=0, pero es un guard real.
    """
    text = raw_text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        # parts[1] contiene el bloque de código
        text = parts[1].lstrip("json").strip()
    return json.loads(text)


async def _evaluate_single(
    llm: ChatGroq, applicant: dict
) -> dict:
    prompt = build_evaluation_prompt(applicant)
    response = await llm.ainvoke(prompt)
    return _parse_llm_response(response.content)


async def run_credit_filter(batch_size: int = 10) -> dict:
    """
    Pipeline principal:
    1. Obtiene contactos pendientes de HubSpot
    2. Evalúa cada uno con Gemini + reglas FIRA
    3. Escribe el veredicto de vuelta en HubSpot
    4. Retorna resumen para logging/monitoreo
    """
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.GROQ_API_KEY,
        temperature=0,
    )

    run_ts = datetime.now(timezone.utc).isoformat()
    print(f"[{run_ts}] Agente Agrocapital iniciado | batch={batch_size}")

    contacts_raw = await get_pending_contacts(limit=batch_size)
    print(f"→ {len(contacts_raw)} contactos obtenidos de HubSpot\n")

    summary = {"run_timestamp": run_ts, "viables": [], "rechazados": [], "errores": []}

    for raw in contacts_raw:
        applicant = _normalize_contact(raw)
        cid = applicant["hubspot_contact_id"]
        nombre = applicant["nombre"] or cid

        try:
            evaluation = await _evaluate_single(llm, applicant)
            crm_updated = await update_contact_verdict(cid, evaluation)

            veredicto = evaluation["veredicto"]
            score = evaluation["score_cumplimiento"]
            revision = evaluation["requiere_revision_humana"]

            entry = {"id": cid, "nombre": nombre, "score": score, "revision_humana": revision}

            if veredicto == "VIABLE":
                summary["viables"].append(entry)
            else:
                entry["motivo"] = evaluation.get("motivo_rechazo")
                summary["rechazados"].append(entry)

            status_icon = "✓" if veredicto == "VIABLE" else "✗"
            revision_tag = " [REVISIÓN HUMANA]" if revision else ""
            print(
                f"  {status_icon} {nombre} → {veredicto} "
                f"(score: {score}%){revision_tag} | CRM: {'OK' if crm_updated else 'FALLO'}"
            )

        except json.JSONDecodeError:
            print(f"  ✗ {nombre} → ERROR: respuesta LLM no es JSON válido")
            summary["errores"].append({"id": cid, "error": "json_parse_error"})
        except httpx.HTTPStatusError as e:
            print(f"  ✗ {nombre} → ERROR HubSpot HTTP {e.response.status_code}")
            summary["errores"].append({"id": cid, "error": f"hubspot_{e.response.status_code}"})
        except Exception as e:
            print(f"  ✗ {nombre} → ERROR inesperado: {e}")
            summary["errores"].append({"id": cid, "error": str(e)})

    print(f"\n{'='*55}")
    print(f"  Viables:    {len(summary['viables'])}")
    print(f"  Rechazados: {len(summary['rechazados'])}")
    print(f"  Errores:    {len(summary['errores'])}")
    print(f"{'='*55}\n")

    return summary
