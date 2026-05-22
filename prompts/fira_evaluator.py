import json

# Subconjunto de reglas FIRA para crédito agropecuario (persona física).
# Fuente: Reglas de Operación FIRA 2024, Art. 3-12.
# MODIFICA ESTE OBJETO para agregar/quitar reglas sin tocar el agente.
FIRA_RULES = {
    "version": "2024.1",
    "programa": "FIRA - Crédito Agropecuario Persona Física",
    "reglas": [
        {
            "regla_id": "FIRA-001",
            "nombre": "Edad del solicitante",
            "obligatoria": True,
            "campo_solicitante": "edad",
            "criterio": "Mayor o igual a 18 años y menor o igual a 75 años",
            "validacion": {"min": 18, "max": 75}
        },
        {
            "regla_id": "FIRA-002",
            "nombre": "Actividad económica elegible",
            "obligatoria": True,
            "campo_solicitante": "actividad_economica",
            "criterio": "Debe ser agrícola, pecuaria, forestal, pesquera o agroindustrial",
            "valores_validos": [
                "agricola", "pecuaria", "forestal",
                "pesquera", "agroindustrial", "agropecuaria"
            ]
        },
        {
            "regla_id": "FIRA-003",
            "nombre": "Sin cartera vencida activa",
            "obligatoria": True,
            "campo_solicitante": "cartera_vencida",
            "criterio": "El campo debe ser false o 'no'. Cualquier indicio de cartera vencida activa es motivo de rechazo.",
            "valor_esperado": False
        },
        {
            "regla_id": "FIRA-004",
            "nombre": "Ubicación en zona rural o agropecuaria",
            "obligatoria": True,
            "campo_solicitante": "zona",
            "criterio": "El solicitante debe operar en zona rural, semi-rural, ejido o área de producción agropecuaria",
            "valores_validos": ["rural", "semi-rural", "agropecuaria", "ejido", "campo"]
        },
        {
            "regla_id": "FIRA-005",
            "nombre": "Destino del crédito elegible",
            "obligatoria": True,
            "campo_solicitante": "destino_credito",
            "criterio": "El crédito debe destinarse a avío (insumos/operación), refaccionario (maquinaria/equipo) o capital de trabajo agrícola",
            "valores_validos": [
                "avio", "refaccionario", "capital_trabajo",
                "infraestructura", "equipo", "semilla",
                "fertilizante", "ganado", "invernadero"
            ]
        },
        {
            "regla_id": "FIRA-006",
            "nombre": "Monto dentro del límite FIRA persona física",
            "obligatoria": False,
            "campo_solicitante": "monto_solicitado_mxn",
            "criterio": "El monto no debe exceder $10,000,000 MXN para persona física",
            "validacion": {"max": 10000000}
        },
        {
            "regla_id": "FIRA-007",
            "nombre": "Tenencia de tierra o contrato vigente",
            "obligatoria": False,
            "campo_solicitante": "tenencia_tierra",
            "criterio": "Debe acreditar ser ejidatario, pequeño propietario, arrendatario o comunero",
            "valores_validos": [
                "ejidatario", "pequeño_propietario",
                "arrendatario", "comunero", "propietario"
            ]
        }
    ]
}


def build_evaluation_prompt(applicant_data: dict) -> str:
    """
    Construye el prompt completo inyectando reglas FIRA y datos del solicitante.
    Separado del agente para poder testearlo de forma aislada.
    """
    return f"""IDENTIDAD Y ROL
===============
Eres un motor de evaluación crediticia determinista para Agrocapital.
Tu ÚNICA función es evaluar solicitudes de crédito agrícola contra las
reglas FIRA inyectadas en este prompt.

NO tienes memoria de conversaciones anteriores.
NO debes inferir, asumir ni inventar reglas fuera del esquema.
Si faltan datos para evaluar una regla, márcala como "sin_datos".

REGLAS FIRA VIGENTES
====================
<FIRA_RULES_SCHEMA>
{json.dumps(FIRA_RULES, ensure_ascii=False, indent=2)}
</FIRA_RULES_SCHEMA>

DATOS DEL SOLICITANTE
=====================
<APPLICANT_DATA>
{json.dumps(applicant_data, ensure_ascii=False, indent=2)}
</APPLICANT_DATA>

PROCESO DE RAZONAMIENTO (interno, obligatorio)
==============================================
Para cada regla en FIRA_RULES_SCHEMA:
  1. Localiza el campo indicado en "campo_solicitante" dentro de APPLICANT_DATA.
  2. Compara el valor contra el criterio de la regla.
  3. Asigna: cumple | no_cumple | sin_datos

CRITERIO DE VEREDICTO
=====================
- VIABLE     → 100% de reglas con obligatoria=true en estado "cumple".
- RECHAZADO  → Una o más reglas obligatorias en "no_cumple".
- requiere_revision_humana = true si cualquier regla obligatoria tiene
  "sin_datos" O si score_cumplimiento está entre 70 y 99 inclusive.

FORMATO DE SALIDA — ESTRICTO
============================
Responde ÚNICAMENTE con JSON válido. Sin markdown, sin texto extra.

{{
  "solicitud_id": "<hubspot_contact_id del solicitante>",
  "veredicto": "VIABLE" | "RECHAZADO",
  "score_cumplimiento": <entero 0-100>,
  "reglas_evaluadas": [
    {{
      "regla_id": "<id>",
      "nombre": "<nombre>",
      "resultado": "cumple" | "no_cumple" | "sin_datos",
      "valor_solicitante": "<valor encontrado o null>",
      "criterio": "<criterio de la regla>",
      "observacion": "<máximo 20 palabras>"
    }}
  ],
  "motivo_rechazo": "<resumen si RECHAZADO, null si VIABLE>",
  "requiere_revision_humana": true | false,
  "timestamp_evaluacion": "<ISO 8601>"
}}

RESTRICCIONES ABSOLUTAS
========================
- Cero texto fuera del objeto JSON.
- Cero reglas inventadas fuera de FIRA_RULES_SCHEMA.
- VIABLE es imposible si hay una sola regla obligatoria en no_cumple.
"""
