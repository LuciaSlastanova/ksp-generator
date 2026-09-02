import json
import streamlit as st

from openai import OpenAI


def get_openai_client():
    return OpenAI(
        api_key=st.secrets["OPENAI_API_KEY"]
    )


def improve_technical_procedure(
    text,
    instruction
):
    client = get_openai_client()

    response = client.responses.create(
        model="gpt-5.6-terra",
        instructions="""
Si AI asistent pre kontrolné a skúšobné plány (KSP)
v stavebníctve.

REFERENČNÝ KSP:
- je záväzný zdroj kontrol, skúšok, spôsobov kontroly,
  noriem, početnosti, tolerancií a dokumentovania

KSP MUSTRA:
- určuje iba formát a štruktúru výsledného dokumentu
- staré údaje o stavbe a firmách ignoruj

TECHNICKÁ SPRÁVA, ROZPOČET A VÝKRESY:
- určujú konkrétny rozsah projektu

PRAVIDLÁ:
- nevymýšľaj nové skúšky
- nevymýšľaj nové normy
- nevymýšľaj nové sekcie
- ak údaj nie je možné určiť, označ OVERIŤ

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

PRIORITA ZDROJOV:

1. REFERENČNÝ KSP
- kontroly
- skúšky
- spôsob kontroly
- kritériá
- normy
- početnosť
- tolerancie
- dokumentovanie

2. TECHNICKÁ SPRÁVA, ROZPOČET A VÝKRESY
- rozsah prác
- materiály
- množstvá
- konštrukcie

3. KSP MUSTRA
- iba formát výsledného dokumentu

PRAVIDLÁ:
- nevymýšľaj skúšky
- nevymýšľaj normy
- nevymýšľaj procesy
- použi iba položky relevantné pre projekt
- ak údaj nie je možné určiť, použi "OVERIŤ"

Výstup musí byť iba validný JSON.

Každý riadok musí mať:

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

    return json.loads(
        raw_result.strip()
    )


def extract_project_metadata(text):
    """
    Zistí údaje pre hlavičku KSP.
    Vracia value, status a source.
    """

    client = get_openai_client()

    response = client.responses.create(
        model="gpt-5.6-terra",
        instructions="""
Si AI systém na kontrolu hlavičky stavebného KSP.

Zisti iba:

- STAVBA
- OBJEKT / SO
- ČASŤ
- ZHOTOVITEĽ
- OBJEDNÁVATEĽ / INVESTOR


========================================
STAVBA
========================================

STAVBA je názov celej stavby.

Primárne hľadaj v ZoD.

Hľadaj označenia:
- Názov stavby
- Stavba
- Názov diela
- Predmet stavby

Priorita:
1. ZoD
2. technická správa
3. cenová ponuka / rozpočet

Ak je názov jasne uvedený:
status = ZHODA


========================================
OBJEKT / SO
========================================

Použi iba výslovne označený objekt:

- Objekt
- Stavebný objekt
- SO
- Číslo a názov objektu
- Objekt stavby

NEPOUŽÍVAJ všeobecný technický opis ako objekt.

Napríklad tieto výrazy NIE SÚ automaticky objekt:
- stoková sieť
- kanalizácia
- kanalizačné prípojky
- výtlačné potrubie

Ak explicitný objekt nenájdeš:
value = "OVERIŤ"
status = "OVERIŤ"
source = "nenájdené"


========================================
ČASŤ
========================================

ČASŤ je samostatná časť stavby alebo zákazky.

Primárny zdroj:
1. cenová ponuka / rozpočet
2. technická správa
3. ZoD

Časť musí byť odlišná od názvu celej stavby.

DÔLEŽITÉ:
Ak údaj, ktorý by si chcel použiť ako ČASŤ,
je rovnaký alebo veľmi podobný hodnote STAVBA,
NESMIEŠ ho použiť ako ČASŤ.

Príklad:

STAVBA:
"Jahodná - kanalizácia II. etapa"

CENOVÁ PONUKA:
"JAHODNÁ - kanalizácia II.etapa"

Toto NIE JE ČASŤ.
Je to iba rovnaký názov celej stavby.

V takom prípade nastav:

value = "OVERIŤ"
status = "OVERIŤ"
source = "nenájdené"

ČASŤ použi iba ak dokument jasne uvádza samostatnú časť,
napríklad:

"Časť: Kanalizačné prípojky"
"Časť stavby: Stoková sieť"
"Etapa: II. etapa"

Samotný názov celej stavby nesmie byť použitý ako ČASŤ.


========================================
ZHOTOVITEĽ
========================================

Primárny zdroj je ZoD.

Hľadaj:
- Zhotoviteľ
- Dodávateľ
- Zhotoviteľ diela

Ak ZoD jasne uvádza firmu:
status = ZHODA
source = "ZoD"

Nikdy nepouži firmu z mustry
ani z referenčného KSP.


========================================
OBJEDNÁVATEĽ / INVESTOR
========================================

Primárny zdroj je ZoD.

Hľadaj:
- Objednávateľ
- Investor
- Stavebník
- Objednávateľ diela

Ak ZoD jasne uvádza subjekt:
status = ZHODA
source = "ZoD"


========================================
ZDROJ
========================================

Povolené hodnoty source:

- "ZoD"
- "technická správa"
- "cenová ponuka / rozpočet"
- "výkres"
- "viac zdrojov"
- "nenájdené"


========================================
STATUS
========================================

ZHODA
- údaj je výslovne uvedený
- nič mu neodporuje

NEZHODA
- dôveryhodné dokumenty si odporujú

OVERIŤ
- údaj nie je explicitne uvedený
- alebo by sa musel domyslieť


========================================
ZAKÁZANÉ ZDROJE
========================================

KSP mustra a referenčný KSP nesmú určovať:

- stavbu
- objekt
- časť
- objednávateľa
- zhotoviteľa


========================================
VÝSTUP
========================================

Vráť iba validný JSON:

{
  "stavba": {
    "value": "...",
    "status": "ZHODA",
    "source": "ZoD"
  },

  "objekt": {
    "value": "OVERIŤ",
    "status": "OVERIŤ",
    "source": "nenájdené"
  },

  "cast": {
    "value": "OVERIŤ",
    "status": "OVERIŤ",
    "source": "nenájdené"
  },

  "zhotovitel": {
    "value": "...",
    "status": "ZHODA",
    "source": "ZoD"
  },

  "objednavatel": {
    "value": "...",
    "status": "ZHODA",
    "source": "ZoD"
  }
}

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

    return json.loads(
        raw_result.strip()
    )
