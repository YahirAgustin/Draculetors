import asyncio
import httpx
from config.config import settings

async def debug():
    headers = {
        "Authorization": f"Bearer {settings.HUBSPOT_TOKEN}",
        "Content-Type": "application/json",
    }
    props = "firstname,lastname,hs_lead_status,edad,actividad_economica"
    url = f"https://api.hubapi.com/crm/v3/objects/contacts?limit=10&properties={props}"

    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers)
        data = r.json()
        for c in data.get("results", []):
            p = c.get("properties", {})
            print(f"  id: {c['id']} | {p.get('firstname')} | lead_status: {repr(p.get('hs_lead_status'))} | edad: {p.get('edad')}")

asyncio.run(debug())