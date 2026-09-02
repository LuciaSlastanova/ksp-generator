import json
import streamlit as st
from openai import OpenAI


def get_openai_client():
    return OpenAI(
        api_key=st.secrets["OPENAI_API_KEY"]
    )


def improve_technical_procedure(text, instruction):
    client = get_openai_client()

    response = client.responses.create(
        model="gpt-5.6-terra",
        instructions="""
Si AI asistent pre kontrolné a skúšobné plány (KSP)
v stavebníctve.

Referenčný KSP je záväzný zdroj pre:
- názvy procesov a subprocesov,
- kontroly,
- skúšky,
- spôsob kontroly,
- normy,
- početnosť,
- tolerancie a dokumentovanie.

KSP šablóna / mustra určuje iba štruktúru a formát výsledného dokumentu.

Technická správa, rozpočet a výkresy určujú konkrétny rozsah
prác daného projektu.

Nevymýšľaj nové skúšky, kontroly, normy ani sekcie,
ktoré nie sú podložené referenčným KSP.

Ak niečo nie je možné určiť, označ to ako OVERIŤ.

Nevytváraj sekcie typu:
- Záverečné skúšky
- Odovzdanie stavby
- Súhrnné skúšky

pokiaľ sa nenachádzajú v referenčnom KSP.

Odpovedaj po slovensky.
""",
        input=f"""
PODKLADY PROJEKTU:

{text}

POŽIADAVKA:

{instruction}
"""
    )

    return response.output_text


def generate_ksp_rows(text):
    client = get_openai_client()

    response = client.responses.create(
        model="gpt-5.6-terra",
        instructions="""
Si AI systém na tvorbu KSP v stavebníctve.

Tvojou úlohou je vytvoriť RIADKY KSP zo zadaných projektových podkladov.

PRIORITA ZDROJOV:

1. Referenčný KSP
   - určuje povolené kontroly a skúšky
   - určuje spôsob kontroly
   - určuje normy
   - určuje typické početnosti
   - určuje tolerancie

2. Technická správa, rozpočet a výkresy
   - určujú, ktoré práce sa v projekte skutočne realizujú
   - určujú materiály, rozmery, množstvá a konkrétny rozsah

3. KSP šablóna
   - určuje formát dokumentu
   - nie je zdrojom nových skúšok

ZÁSADY:

- Nevymýšľaj nové skúšky.
- Nevymýšľaj nové normy.
- Nevymýšľaj nové sekcie.
- Použi iba položky relevantné pre konkrétny projekt.
- Ak údaj nie je možné bezpečne určiť, použi "OVERIŤ".
- Nevkladaj vysvetľujúci text.
- Výstup musí byť iba validný JSON.

Každý riadok musí mať tieto polia:

poradie
subproces
mnozstvo
druh_kontroly
sposob_kontroly
kriterium
pocetnost
celkovy_pocet
zodpoveda
vykona
tolerancia
dokumentovanie
poznamka

Výstup:

[
  {
    "poradie": "1.",
    "subproces": "...",
    "mnozstvo": "...",
    "druh_kontroly": "...",
    "sposob_kontroly": "...",
    "kriterium": "...",
    "pocetnost": "...",
    "celkovy_pocet": "...",
    "zodpoveda": "...",
    "vykona": "...",
    "tolerancia": "...",
    "dokumentovanie": "...",
    "poznamka": "..."
  }
]

Vráť iba JSON.
""",
        input=text
    )

    raw_result = response.output_text.strip()

    if raw_result.startswith("```json"):
        raw_result = raw_result[7:]

    if raw_result.startswith("```"):
        raw_result = raw_result[3:]

    if raw_result.endswith("```"):
        raw_result = raw_result[:-3]

    return json.loads(raw_result.strip())
