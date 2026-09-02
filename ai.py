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

    if raw_result.startswith(
        "```json"
    ):
        raw_result = raw_result[7:]

    if raw_result.startswith(
        "```"
    ):
        raw_result = raw_result[3:]

    if raw_result.endswith(
        "```"
    ):
        raw_result = raw_result[:-3]

    return json.loads(
        raw_result.strip()
    )


# --------------------------------------------------
# KONTROLA HLAVIČKY PROJEKTU
# --------------------------------------------------

def extract_project_metadata(text):
    """
    Zistí údaje pre hlavičku KSP
    a porovná ich medzi projektovými dokumentmi.
    """

    client = get_openai_client()

    response = client.responses.create(
        model="gpt-5.6-terra",

        instructions="""
Si AI systém na kontrolu údajov
stavebného projektu.

Tvojou úlohou je z poskytnutých dokumentov
zistiť údaje pre hlavičku KSP:

- STAVBA
- OBJEKT / SO
- ZHOTOVITEĽ
- OBJEDNÁVATEĽ / INVESTOR


========================================
ZDROJE
========================================

Dokument môže obsahovať:

- technickú správu
- cenovú ponuku
- rozpočet
- titulnú stranu ZoD
- časť Zmluvy o dielo

ZoD môže byť vložená priamo
na začiatku technickej správy.

Nehľadaj iba presný názov dokumentu.
Čítaj jeho obsah.


========================================
STAVBA
========================================

Primárne hľadaj názov stavby v:

1. technickej správe
2. Zmluve o dielo / ZoD
3. cenovej ponuke alebo rozpočte

Ak sa názvy významovo zhodujú,
použi najúplnejší názov.

Príklad:

"JAHODNÁ - KANALIZÁCIA"

a

"JAHODNÁ - KANALIZÁCIA - II. etapa"

sa môžu považovať za zhodné,
ak dokumenty jasne patria
k tomu istému projektu.


========================================
OBJEKT / SO
========================================

Hľadaj napríklad:

- SO
- stavebný objekt
- objekt
- časť stavby
- stoková sieť
- kanalizačné prípojky
- čerpacia stanica

Primárne používaj technickú správu.

Porovnaj s:
- rozpočtom
- ZoD
- cenovou ponukou

Ak je objektov viac,
uveď ich prehľadne.

Nevytváraj číslo SO,
ak v dokumentoch nie je uvedené.


========================================
ZHOTOVITEĽ
========================================

Hľadaj aj označenia:

- Zhotoviteľ
- Dodávateľ
- Zhotoviteľ diela
- Dodávateľ stavby
- Zmluvná strana - zhotoviteľ

Primárne používaj:

1. ZoD
2. cenovú ponuku
3. rozpočet

Ak je pri označení firmy uvedený názov spoločnosti,
IČO, sídlo alebo kontaktné údaje,
považuj to za silný dôkaz.

NIKDY nepouži ako zhotoviteľa firmu,
ktorá pochádza iba zo vzorového KSP
alebo referenčného KSP.


========================================
OBJEDNÁVATEĽ / INVESTOR
========================================

Hľadaj aj označenia:

- Objednávateľ
- Investor
- Objednávateľ diela
- Stavebník
- Zmluvná strana - objednávateľ

Primárne používaj:

1. ZoD
2. cenovú ponuku
3. rozpočet
4. technickú správu

Ak dokument jasne uvádza
objednávateľa a jeho firmu,
použi tento údaj.


========================================
KONTROLA ZHODY
========================================

Pre každý údaj nastav status.

ZHODA
- údaj bol nájdený
- dokumenty sa nebijú
- alebo sa rovnaký údaj nachádza
  vo viacerých dokumentoch

NEZHODA
- dva dôveryhodné dokumenty
  uvádzajú rozdielne údaje

OVERIŤ
- údaj sa nepodarilo nájsť
- je nejednoznačný
- alebo nie je dostatok podkladov


DÔLEŽITÉ:

Ak je údaj jasne uvedený iba v jednom
dôveryhodnom dokumente a nič mu neodporuje,
môžeš ho použiť.

Nemusíš vyžadovať,
aby bol rovnaký údaj uvedený dvakrát.

V takom prípade môže byť status ZHODA.


========================================
ZAKÁZANÉ ZDROJE PRE HLAVIČKU
========================================

Ak by sa v texte nachádzal obsah:

- KSP mustry
- vzorového KSP
- referenčného KSP

ich údaje o:

- starej stavbe
- starom objekte
- starej firme
- starom objednávateľovi
- starom zhotoviteľovi

IGNORUJ.

Tieto dokumenty nesmú určovať
hlavičku nového projektu.


========================================
ZÁKAZ DOMÝŠĽANIA
========================================

Nevymýšľaj:

- názov firmy
- objekt
- číslo SO
- objednávateľa
- zhotoviteľa
- názov stavby

Ak údaj naozaj nie je v podkladoch,
použi OVERIŤ.


========================================
VÝSTUP
========================================

Vráť iba validný JSON:

{
  "stavba": {
    "value": "...",
    "status": "ZHODA"
  },

  "objekt": {
    "value": "...",
    "status": "ZHODA"
  },

  "zhotovitel": {
    "value": "...",
    "status": "ZHODA"
  },

  "objednavatel": {
    "value": "...",
    "status": "ZHODA"
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

    if raw_result.startswith(
        "```json"
    ):
        raw_result = raw_result[7:]

    if raw_result.startswith(
        "```"
    ):
        raw_result = raw_result[3:]

    if raw_result.endswith(
        "```"
    ):
        raw_result = raw_result[:-3]

    return json.loads(
        raw_result.strip()
    )
