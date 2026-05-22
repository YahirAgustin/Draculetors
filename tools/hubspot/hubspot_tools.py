import httpx
from config.config import settings

HUBSPOT_BASE = "https://api.hubapi.com"

FETCH_PROPS = [
    "firstname", "lastname", "email", "phone", "hs_lead_source",
    "hs_lead_status",
    "edad", "actividad_economica", "cartera_vencida",
    "zona", "destino_credito", "monto_solicitado_mxn", "tenencia_tierra",
]

def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.HUBSPOT_TOKEN}",
        "Content-Type": "application/json",
    }

async def get_pending_contacts(limit: int = 10) -> list[dict]:
    """Obtiene contactos desde HubSpot con hs_lead_status == NEW."""
    props = ",".join(FETCH_PROPS)
    url = f"{HUBSPOT_BASE}/crm/v3/objects/contacts?limit={limit}&properties={props}"

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url, headers=_headers())
        r.raise_for_status()
        results = r.json().get("results", [])
        return [
            c for c in results
            if c.get("properties", {}).get("hs_lead_status") == "NEW"
        ]

async def update_contact_verdict(contact_id: str, evaluation: dict) -> bool:
    """
    Actualiza el veredicto FIRA en HubSpot.

    Estrategia de fallback en dos pasos:
    1. Intenta escribir todas las propiedades custom FIRA + hs_lead_status.
    2. Si HubSpot rechaza con 400 (propiedades custom no existen en el portal),
       hace un segundo PATCH solo con hs_lead_status — que siempre existe.
    Esto garantiza que al menos el estado del lead se actualice en cualquier portal.
    """
    # BUG FIX: la URL correcta incluye /objects/ antes de /contacts/
    url = f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{contact_id}"
    veredicto = evaluation.get("veredicto", "RECHAZADO")

    payload_full = {
        "properties": {
            "fira_veredicto":          veredicto,
            "fira_score":              str(evaluation.get("score_cumplimiento", 0)),
            "fira_motivo_rechazo":     evaluation.get("motivo_rechazo") or "",
            "fira_requiere_revision":  str(evaluation.get("requiere_revision_humana", False)),
            "fira_timestamp":          evaluation.get("timestamp_evaluacion", ""),
            "hs_lead_status":          "IN_PROGRESS" if veredicto == "VIABLE" else "UNQUALIFIED",
        }
    }

    payload_minimal = {
        "properties": {
            "hs_lead_status": "IN_PROGRESS" if veredicto == "VIABLE" else "UNQUALIFIED",
        }
    }

    async with httpx.AsyncClient(timeout=15) as client:
        # Intento 1: payload completo con campos FIRA custom
        r = await client.patch(url, json=payload_full, headers=_headers())

        if r.status_code == 200:
            return True

        # Intento 2 (fallback): HubSpot devolvió 400 porque las propiedades custom
        # no existen en este portal. Actualizamos solo hs_lead_status.
        if r.status_code == 400:
            print(f"    ⚠ Propiedades FIRA custom no encontradas en el portal. "
                  f"Fallback: actualizando solo hs_lead_status.")
            r2 = await client.patch(url, json=payload_minimal, headers=_headers())
            if r2.status_code == 200:
                return True
            r2.raise_for_status()

        # Cualquier otro error (401, 403, 404, 5xx) — lanzar para que el agente lo loguee
        r.raise_for_status()
        return False
