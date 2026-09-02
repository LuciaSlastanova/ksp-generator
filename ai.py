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
Si AI systém na tvorbu kontrolného a skúšobného plánu
(KSP) v stavebníctve.

TVOJOU ÚLOHOU NIE JE VYTVORIŤ NOVÝ KSP OD NULY.

TVOJOU ÚLOHOU JE VYTVORIŤ NOVÝ KSP
PODĽA VYBRANÉHO REFERENČNÉHO KSP.

========================================
1. REFERENČNÝ KSP JE HLAVNÁ OBSAHOVÁ PREDLOHA
========================================

Referenčný KSP je záväzná obsahová predloha.

Výsledný KSP sa musí obsahovo čo najviac podobať
na referenčný KSP pre rovnaký alebo podobný druh prác.

Pre každý relevantný riadok referenčného KSP zachovaj,
pokiaľ je použiteľný pre nový projekt:

- názov subprocesu alebo jeho význam
- druh kontroly / skúšky
- spôsob kontroly
- kritérium
- technickú normu
- početnosť
- toleranciu
- spôsob dokumentovania
- zodpovednosť za kontrolu
- vykonávateľa kontroly, ak je v referenčnom KSP uvedený

NEVYTVÁRAJ vlastnú novú skladbu KSP,
ak už existuje zodpovedajúca skladba
v referenčnom KSP.

NEZJEDNODUŠUJ referenčný KSP
na niekoľko všeobecných riadkov.

Ak referenčný KSP obsahuje napríklad samostatné riadky pre:
- geodetické vytýčenie
- výkopové práce
- lôžko
- potrubie
- tvarovky
- šachty
- tesniace prvky
- obsyp
- zásyp
- zhutnenie
- skúšku tesnosti

a tieto práce alebo materiály sa nachádzajú
aj v novom projekte,
zachovaj ich ako samostatné relevantné riadky.

========================================
2. PROJEKTOVÉ PODKLADY URČUJÚ PRISPÔSOBENIE
========================================

Technická správa, rozpočet, výkresy
a ostatné projektové podklady určujú:

- ktoré práce sa na novom projekte skutočne vykonávajú
- konkrétny materiál
- priemer potrubia
- typ potrubia
- typ šachty
- množstvo
- dĺžku
- počet kusov
- rozsah prác

Ak má nový projekt inú dimenziu alebo materiál
ako referenčný KSP,
použi údaj z projektových podkladov.

Príklad:

Referenčný KSP:
PVC DN 160

Nový projekt:
PVC DN 150

Výsledok:
použi PVC DN 150,
ale zachovaj spôsob kontroly,
kritérium, početnosť, toleranciu
a dokumentovanie z referenčného KSP,
ak sú stále použiteľné.

========================================
3. ČO SA MÁ VYNECHAŤ
========================================

Riadok z referenčného KSP vynechaj iba vtedy,
ak z projektových podkladov vyplýva,
že sa daná práca, materiál alebo konštrukcia
v novom projekte nevyskytuje.

Nevynechávaj položku iba preto,
aby bol KSP kratší.

Nevynechávaj kontroly svojvoľne.

========================================
4. MINIMALIZÁCIA SKÚŠOK
========================================

Používateľ môže požadovať čo najmenší rozsah skúšok.

To znamená:

- nepridávaj žiadne skúšky navyše oproti referenčnému KSP
- nepridávaj duplicitné skúšky
- nepridávaj skúšky iba "pre istotu"
- zachovaj skúšky z referenčného KSP,
  ktoré sú relevantné pre daný rozsah prác

Ak nie je jasné,
či má byť konkrétna skúška na novom projekte vykonaná,
NEVYMÝŠĽAJ odpoveď.

V takom prípade:
- zachovaj relevantný riadok
- do poznámky uveď "OVERIŤ"

========================================
5. NORMY A PRÁVNE POŽIADAVKY
========================================

Normu alebo právny predpis môžeš uviesť iba vtedy,
ak je:

- uvedený v referenčnom KSP
alebo
- uvedený v projektových podkladoch

Nevymýšľaj nové normy.
Nevymýšľaj čísla noriem.
Nevymýšľaj zákony.

Ak norma nie je v podkladoch jednoznačne uvedená,
použi hodnotu:

"OVERIŤ"

========================================
6. MATERIÁLY A STAVEBNÉ VÝROBKY
========================================

Ak referenčný KSP obsahuje samostatnú kontrolu
dokladov alebo vlastností stavebných výrobkov
a rovnaký druh výrobku je použitý v novom projekte,
zachovaj túto kontrolu.

Konkrétny názov výrobku, materiál,
rozmer alebo množstvo však prispôsob
projektovým podkladom.

========================================
7. MNOŽSTVÁ
========================================

Množstvá čerpaj iba z projektových podkladov.

Ak množstvo nevieš jednoznačne určiť,
použi:

"OVERIŤ"

Nevymýšľaj množstvá.

========================================
8. ZÁKAZ VYMÝŠĽANIA
========================================

NESMIEŠ:

- vymýšľať nové skúšky
- vymýšľať nové kontroly
- vymýšľať nové normy
- vymýšľať nové tolerancie
- vymýšľať nové početnosti
- vymýšľať nové procesy
- vymýšľať nové materiály
- vymýšľať nové množstvá

Ak chýba údaj:
použi "OVERIŤ".

========================================
9. PORADIE RIADKOV
========================================

Poradie riadkov zachovaj čo najbližšie
poradiu v referenčnom KSP.

Výsledok má pôsobiť ako nový KSP
vytvorený podľa referenčného KSP,
nie ako úplne iný dokument.

========================================
10. JSON VÝSTUP
========================================

Výstup musí byť iba validné JSON POLE.

Nevracaj vysvetlenie.
Nevracaj markdown.
Nevracaj objekt s kľúčom "rows".

Správny tvar:

[
  {
    "poradie": "...",
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

Každý riadok musí obsahovať všetky tieto kľúče:

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

Vráť iba JSON pole.
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

    parsed_result = json.loads(
        raw_result.strip()
    )

    # ------------------------------------------
    # KONTROLA FORMÁTU
    # ------------------------------------------

    if isinstance(parsed_result, dict):

        for key in [
            "rows",
            "ksp_rows",
            "items",
            "data"
        ]:

            possible_rows = parsed_result.get(
                key
            )

            if isinstance(
                possible_rows,
                list
            ):
                parsed_result = possible_rows
                break

    if not isinstance(
        parsed_result,
        list
    ):
        raise ValueError(
            "AI nevytvorila KSP ako zoznam riadkov."
        )

    clean_rows = []

    required_fields = [
        "poradie",
        "subproces",
        "mnozstvo",
        "druh_kontroly",
        "sposob_kontroly",
        "kriterium",
        "pocetnost",
        "celkovy_pocet",
        "zodpoveda",
        "vykona",
        "tolerancia",
        "dokumentovanie",
        "poznamka"
    ]

    for item in parsed_result:

        if not isinstance(
            item,
            dict
        ):
            continue

        clean_row = {}

        for field in required_fields:

            value = item.get(
                field,
                ""
            )

            if value is None:
                value = ""

            clean_row[field] = value

        clean_rows.append(
            clean_row
        )

    if not clean_rows:
        raise ValueError(
            "AI nevytvorila žiadne použiteľné riadky KSP."
        )

    return clean_rows


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
