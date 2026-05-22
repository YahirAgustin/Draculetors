import asyncio
import httpx
from config.config import settings

contacts = [
    {
        "firstname": "Carlos", "lastname": "Mendoza", "email": "carlos@ejido.mx",
        "hs_lead_status": "NEW", "edad": "34", "actividad_economica": "agricola",
        "cartera_vencida": "no", "zona": "rural", "destino_credito": "semilla",
        "monto_solicitado_mxn": "150000", "tenencia_tierra": "ejidatario",
    },
    {
        "firstname": "Rosa", "lastname": "Juarez", "email": "rosa@gmail.com",
        "hs_lead_status": "NEW", "edad": "22", "actividad_economica": "comercio",
        "cartera_vencida": "si", "zona": "urbana", "destino_credito": "consumo",
        "monto_solicitado_mxn": "50000", "tenencia_tierra": "",
    },
    {
        "firstname": "Juan", "lastname": "Torres", "email": "juan@rancho.mx",
        "hs_lead_status": "NEW", "edad": "45", "actividad_economica": "pecuaria",
        "cartera_vencida": "no", "zona": "ejido", "destino_credito": "ganado",
        "monto_solicitado_mxn": "800000", "tenencia_tierra": "pequeño_propietario",
    },
]

async def create_contacts():
    headers = {
        "Authorization": f"Bearer {settings.HUBSPOT_TOKEN}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        for c in contacts:
            r = await client.post(
                "https://api.hubapi.com/crm/v3/objects/contacts",
                json={"properties": c},
                headers=headers,
            )
            data = r.json()
            nombre = f"{c['firstname']} {c['lastname']}"
            print(f"  {nombre}: {r.status_code} | id: {data.get('id', data.get('message'))}")

asyncio.run(create_contacts())