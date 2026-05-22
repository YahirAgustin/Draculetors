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
    """Obtiene contactos desde HubSpot vía GET simple."""
    props = ",".join(FETCH_PROPS)
    url = f"{HUBSPOT_BASE}/crm/v3/objects/contacts?limit={limit}&properties={props}"

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url, headers=_headers())
        r.raise_for_status()
        results = r.json().get("results", [])
        # Filtra solo los que tienen lead_status NEW
        return [
            c for c in results
            if c.get("properties", {}).get("hs_lead_status") == "NEW"
        ]

async def update_contact_verdict(contact_id: str, evaluation: dict) -> bool:
    url = f"{HUBSPOT_BASE}/crm/v3/contacts/{contact_id}"
    veredicto = evaluation.get("veredicto", "RECHAZADO")
    payload = {
        "properties": {
            "fira_veredicto": veredicto,
            "fira_score": str(evaluation.get("score_cumplimiento", 0)),
            "fira_motivo_rechazo": evaluation.get("motivo_rechazo") or "",
            "fira_requiere_revision": str(evaluation.get("requiere_revision_humana", False)),
            "fira_timestamp": evaluation.get("timestamp_evaluacion", ""),
            "hs_lead_status": "IN_PROGRESS" if veredicto == "VIABLE" else "UNQUALIFIED",
        }
    }
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.patch(url, json=payload, headers=_headers())
        return r.status_code == 200
