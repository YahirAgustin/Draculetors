import httpx
from config.config import settings

HUBSPOT_BASE = "https://api.hubapi.com"

# Propiedades custom que debes crear en HubSpot antes de correr esto.
# Settings → Properties → Create property (tipo: single-line text o number)
CUSTOM_PROPS = [
    "edad", "actividad_economica", "cartera_vencida",
    "zona", "destino_credito", "monto_solicitado_mxn", "tenencia_tierra",
    "fira_veredicto", "fira_score", "fira_motivo_rechazo",
    "fira_requiere_revision", "fira_timestamp",
]

FETCH_PROPS = [
    "firstname", "lastname", "email", "phone", "hs_lead_source",
    "edad", "actividad_economica", "cartera_vencida",
    "zona", "destino_credito", "monto_solicitado_mxn", "tenencia_tierra",
]


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.HUBSPOT_TOKEN}",
        "Content-Type": "application/json",
    }


async def get_pending_contacts(limit: int = 10) -> list[dict]:
    """
    MOCK — Simula contactos entrantes desde redes sociales.
    Reemplazar con llamada real a HubSpot cuando el CRM tenga datos.
    """
    return [
        {
            "id": "mock-001",
            "properties": {
                "firstname": "Carlos", "lastname": "Mendoza",
                "email": "carlos@ejido.mx", "phone": "5512345678",
                "hs_lead_source": "Social Media",
                "edad": "34",
                "actividad_economica": "agricola",
                "cartera_vencida": "no",
                "zona": "rural",
                "destino_credito": "semilla",
                "monto_solicitado_mxn": "150000",
                "tenencia_tierra": "ejidatario",
            }
        },
        {
            "id": "mock-002",
            "properties": {
                "firstname": "Rosa", "lastname": "Juárez",
                "email": "rosa@gmail.com", "phone": "5598765432",
                "hs_lead_source": "Social Media",
                "edad": "22",
                "actividad_economica": "comercio",  # No elegible FIRA
                "cartera_vencida": "si",             # Rechazo directo
                "zona": "urbana",
                "destino_credito": "consumo",
                "monto_solicitado_mxn": "50000",
                "tenencia_tierra": None,
            }
        },
        {
            "id": "mock-003",
            "properties": {
                "firstname": "Juan", "lastname": "Torres",
                "email": "juan@rancho.mx", "phone": "5567891234",
                "hs_lead_source": "Social Media",
                "edad": "45",
                "actividad_economica": "pecuaria",
                "cartera_vencida": "no",
                "zona": "ejido",
                "destino_credito": "ganado",
                "monto_solicitado_mxn": "800000",
                "tenencia_tierra": "pequeño_propietario",
            }
        },
    ]


async def update_contact_verdict(contact_id: str, evaluation: dict) -> bool:
    """MOCK — Simula escritura de vuelta al CRM."""
    print(f"    [CRM MOCK] Contacto {contact_id} actualizado → {evaluation.get('veredicto')}")
    return True
