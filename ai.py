import json
import streamlit as st

from openai import OpenAI


# --------------------------------------------------
# OPENAI CLIENT
# --------------------------------------------------

def get_openai_client():
    return OpenAI(
        api_key=st.secrets["OPENAI_API_KEY"]
    )


# --------------------------------------------------
# BEŽNÁ AI ANALÝZA PROJEKTU
# --------------------------------------------------

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

ZDROJE:

1. REFERENČNÝ KSP
- je záväzný zdroj pre názvy procesov,
  kontroly, skúšky, spôsob kontroly,
  normy, početnosť a tolerancie
- nevytváraj skúšky ani kontroly,
  ktoré v referenčnom KSP nie sú

2. KSP ŠABLÓNA / MUSTRA
- určuje iba štruktúru a formát výsledného dokumentu
- údaje o starej stavbe alebo starej firme ignoruj

3. TECHNICKÁ SPRÁVA, ROZPOČET A VÝKRESY
- určujú konkrétny rozsah prác projektu
- používaj ich na materiály, množstvá,
  objekty a technologické údaje

PRAVIDLÁ:

- Nevymýšľaj nové skúšky.
- Nevymýšľaj nové normy.
- Nevymýšľaj nové sekcie.
- Ak údaj nie je možné určiť,
  označ ho ako OVERIŤ.

Nevytváraj sekcie ako:
- Záverečné skúšky
- Odovzdanie stavby
- Súhrnné skúšky

ak sa nenachádzajú v referenčnom KSP.

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


# --------------------------------------------------
# RIADKY PRE KSP EXCEL
# --------------------------------------------------

def generate_ksp_rows(text):
    client = get_openai_client()

    response = client.responses.create(
        model="gpt-5.6-terra",

        instructions="""
Si AI systém na tvorbu KSP v stavebníctve.

Tvojou úlohou je vytvoriť RIADKY KSP
zo zadaných projektových podkladov.

PRIORITA ZDROJOV:

1. REFERENČNÝ KSP

Použi ho ako záväzný zdroj pre:
- kontroly
- skúšky
- spôsob kontroly
- kritériá
- normy
- početnosť
- tolerancie
- dokumentovanie

2. TECHNICKÁ SPRÁVA, ROZPOČET A VÝKRESY

Použi ich na:
- určenie realizovaných prác
- materiály
- množstvá
- konštrukcie
- konkrétny rozsah projektu

3. KSP MUSTRA

Použi ju iba ako vzor štruktúry dokumentu.

PRAVIDLÁ:

- Nevymýšľaj nové skúšky.
- Nevymýšľaj nové normy.
- Nevymýšľaj nové procesy.
- Použi iba položky relevantné pre projekt.
- Ak údaj nie je možné bezpečne určiť,
  použi "OVERIŤ".

Výstup musí byť iba validný JSON.

Každý riadok musí obsahovať:

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

Nevkladaj žiadny text mimo JSON.
""",

        input=text
    )

    raw_result = (
        response.output_text
        .strip()
    )

    if raw_result.startswith("```json"):
        raw_result = raw_result[7:]

    if raw_result.startswith("```"):
        raw_result = raw_result[3:]

    if raw_result.endswith("```"):
        raw_result = raw_result[:-3]

    return json.loads(
        raw_result.strip()
    )


# --------------------------------------------------
# KONTROLA HLAVIČKY PROJEKTU
# --------------------------------------------------

def extract_project_metadata(text):
    """
    Zistí údaje pre hlavičku KSP.
    Každý údaj vracia:
    - value
    - status
    - source
    """

    client = get_openai_client()

    response = client.responses.create(
        model="gpt-5.6-terra",

        instructions="""
Si AI systém na kontrolu hlavičky
stavebného KSP.

Tvojou úlohou je z poskytnutých dokumentov
zistiť iba tieto údaje:

- STAVBA
- OBJEKT / SO
- ČASŤ
- ZHOTOVITEĽ
- OBJEDNÁVATEĽ / INVESTOR

Pri každom údaji musíš uviesť aj ZDROJ.


========================================
VŠEOBECNÉ PRAVIDLO
========================================

Použi iba údaje,
ktoré sú v dokumentoch výslovne uvedené.

Nedomýšľaj význam
z bežného technického alebo opisného textu.

Ak si nie si istý,
použi:

value = "OVERIŤ"
status = "OVERIŤ"
source = "nenájdené"


========================================
STAVBA
========================================

STAVBA znamená názov celej stavby.

Primárny zdroj je ZoD.

Hľadaj najmä označenia:

- Názov stavby
- Stavba
- Názov diela
- Predmet stavby

PRIORITA:

1. ZoD
2. technická správa
3. cenová ponuka / rozpočet

Ak sa v ZoD nachádza napríklad:

"Názov stavby: Jahodná - kanalizácia II. etapa"

použi presne tento údaj ako STAVBU.

Ak sa rovnaký alebo významovo rovnaký názov
nachádza aj v ďalších dokumentoch,
status = ZHODA
source = "viac zdrojov"

Ak je jasne uvedený iba v ZoD
a nič mu neodporuje,
status = ZHODA
source = "ZoD"


========================================
OBJEKT / SO
========================================

OBJEKT znamená konkrétny stavebný objekt.

Použi iba údaj,
ktorý je výslovne označený napríklad ako:

- Objekt
- Stavebný objekt
- SO
- Číslo a názov objektu
- Objekt stavby

Príklady správnych objektov:

"SO 01 Kanalizácia"
"SO 02 Čerpacia stanica"
"Objekt: SO 03 Prípojky"

NEPOUŽÍVAJ ako objekt
iba všeobecný opis prác alebo technológie.

Tieto výrazy NESMÚ byť automaticky objekt:

- stoková sieť
- gravitačná kanalizácia
- kanalizačné prípojky
- výtlačné potrubie
- čerpacia stanica

Tieto výrazy môžeš použiť ako objekt iba vtedy,
ak dokument výslovne uvádza napríklad:

"Objekt: Stoková sieť"

alebo:

"SO 01 Stoková sieť"

Ak explicitný objekt alebo SO
v dokumentoch nenájdeš:

value = "OVERIŤ"
status = "OVERIŤ"
source = "nenájdené"


========================================
ČASŤ
========================================

ČASŤ znamená konkrétnu časť stavby alebo zákazky.

Primárny zdroj pre ČASŤ je:

1. cenová ponuka
2. rozpočet
3. technická správa
4. ZoD

Hľadaj údaje označené napríklad ako:

- Časť
- Časť stavby
- Časť zákazky
- Etapa
- Predmet cenovej ponuky
- Názov časti
- časť objektu

DÔLEŽITÉ:

Ak cenová ponuka alebo rozpočet
má názov alebo nadpis,
ktorý jednoznačne označuje konkrétnu časť
realizovaných prác,
môžeš ho použiť ako ČASŤ.

Ale nesmieš použiť všeobecný technický opis,
ak nie je zrejmé, že ide o názov časti.

Príklad:

Ak cenová ponuka jasne uvádza napríklad:

"Časť: Kanalizácia - stoková sieť"

použi túto hodnotu.

Ak je v cenovej ponuke iba zoznam položiek,
bez jednoznačného názvu časti:

value = "OVERIŤ"
status = "OVERIŤ"
source = "nenájdené"

Nikdy nepouži starú hodnotu
zo vzorovej KSP mustry.


========================================
ZHOTOVITEĽ
========================================

Primárny zdroj je ZoD.

Hľadaj výslovne označenia:

- Zhotoviteľ
- Dodávateľ
- Zhotoviteľ diela
- Zmluvná strana - zhotoviteľ

PRIORITA:

1. ZoD
2. cenová ponuka
3. rozpočet

Ak ZoD jasne uvádza:

"Zhotoviteľ: AVA-stav, s.r.o."

použi presne tento údaj.

Ak nič tomuto údaju neodporuje:

status = ZHODA
source = "ZoD"

NIKDY nepouži firmu
z KSP mustry alebo referenčného KSP.


========================================
OBJEDNÁVATEĽ / INVESTOR
========================================

Primárny zdroj je ZoD.

Hľadaj výslovne:

- Objednávateľ
- Investor
- Stavebník
- Objednávateľ diela
- Zmluvná strana - objednávateľ

PRIORITA:

1. ZoD
2. cenová ponuka
3. rozpočet
4. technická správa

Ak ZoD jasne uvádza napríklad:

"Objednávateľ: Obec Jahodná"

použi presne tento údaj.

Ak nič tomuto údaju neodporuje:

status = ZHODA
source = "ZoD"


========================================
ZDROJ
========================================

Pole "source" musí byť jedna z hodnôt:

- "ZoD"
- "technická správa"
- "cenová ponuka / rozpočet"
- "výkres"
- "viac zdrojov"
- "nenájdené"

Ak je údaj nájdený iba v jednom dokumente,
uveď tento konkrétny zdroj.

Ak sa rovnaký údaj zhoduje
vo viacerých zdrojoch:

source = "viac zdrojov"


========================================
STATUS
========================================

ZHODA
- údaj je explicitne uvedený
- nič mu neodporuje

NEZHODA
- dva dôveryhodné dokumenty
  uvádzajú rozdielne údaje

OVERIŤ
- údaj nie je explicitne uvedený
- údaj je nejednoznačný
- alebo by si ho musel domyslieť


========================================
ZAKÁZANÉ ZDROJE PRE HLAVIČKU
========================================

Údaje z:

- KSP mustry
- vzorového KSP
- referenčného KSP

nesmú určovať:

- stavbu
- objekt
- časť
- objednávateľa
- zhotoviteľa

Tieto staré údaje ignoruj.


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
    "value": "...",
    "status": "OVERIŤ",
    "source": "nenájdené"
  },

  "cast": {
    "value": "...",
    "status": "OVERIŤ",
    "source": "cenová ponuka / rozpočet"
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

Povolené statusy sú iba:

ZHODA
NEZHODA
OVERIŤ

Nevkladaj žiadny text mimo JSON.
""",

        input=text
    )

    raw_result = (
        response.output_text
        .strip()
    )

    if raw_result.startswith("```json"):
        raw_result = raw_result[7:]

    if raw_result.startswith("```"):
        raw_result = raw_result[3:]

    if raw_result.endswith("```"):
        raw_result = raw_result[:-3]

    return json.loads(
        raw_result.strip()
    )
