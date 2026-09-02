import json
import streamlit as st

from openai import OpenAI


def get_openai_client():
    return OpenAI(
        api_key=st.secrets["OPENAI_API_KEY"]
    )


# ==========================================================
# POMOCNÁ FUNKCIA - ČISTENIE JSON ODPOVEDE
# ==========================================================

def clean_json_response(raw_result):
    raw_result = raw_result.strip()

    if raw_result.startswith("```json"):
        raw_result = raw_result[7:]

    if raw_result.startswith("```"):
        raw_result = raw_result[3:]

    if raw_result.endswith("```"):
        raw_result = raw_result[:-3]

    return raw_result.strip()


# ==========================================================
# AI ANALÝZA / TECHNICKÝ POSTUP
# ==========================================================

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
- je hlavný obsahový vzor
- je zdroj kontrol, skúšok, spôsobov kontroly,
  kritérií, noriem, početnosti, tolerancií
  a dokumentovania

KSP MUSTRA:
- určuje iba formát a štruktúru výsledného dokumentu
- staré údaje o stavbe a firmách ignoruj

TECHNICKÁ SPRÁVA, ROZPOČET A VÝKRESY:
- určujú konkrétny rozsah nového projektu
- určujú materiály
- určujú rozmery
- určujú množstvá

PRAVIDLÁ:
- nevymýšľaj nové skúšky
- nevymýšľaj nové normy
- nevymýšľaj nové sekcie
- údaje existujúce v referenčnom KSP
  nenahrádzaj slovom OVERIŤ

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


# ==========================================================
# GENEROVANIE RIADKOV KSP
# ==========================================================

def generate_ksp_rows(text):
    client = get_openai_client()

    response = client.responses.create(
        model="gpt-5.6-terra",

        # Web použijeme na overenie aktuálnych
        # právnych požiadaviek a povinnosti skúšok.
        tools=[
            {
                "type": "web_search",
                "search_context_size": "low",
                "filters": {
                    "allowed_domains": [
                        "slov-lex.sk",
                        "normoff.gov.sk",
                        "mindop.sk"
                    ]
                }
            }
        ],

        instructions="""
Si AI systém na tvorbu kontrolných a skúšobných
plánov KSP pre stavebníctvo na Slovensku.

TVOJOU ÚLOHOU NIE JE VYTVORIŤ NOVÝ KSP OD NULY.

Máš vytvoriť nový KSP tak,
aby sa obsahovo čo najviac podobal
na REFERENČNÝ KSP.

===============================================
A. ROZPOZNAJ DOKUMENTY
===============================================

V texte sú dokumenty označené napríklad:

--- TYP DOKUMENTU: reference_ksp ---
--- TYP DOKUMENTU: technical_report ---
--- TYP DOKUMENTU: budget ---
--- TYP DOKUMENTU: drawing ---

Dokument typu:

reference_ksp

je REFERENČNÝ KSP.

Je to HLAVNÝ OBSAHOVÝ VZOR.

===============================================
B. REFERENČNÝ KSP JE ZÁKLAD
===============================================

Najprv si prečítaj celý referenčný KSP.

Výsledný KSP musí obsahovo vychádzať
z jeho relevantných riadkov.

Ak nový projekt obsahuje rovnaký alebo podobný
druh práce ako referenčný KSP,
PREVEZMI z referenčného KSP:

- subproces
- druh kontroly
- spôsob kontroly
- kritérium
- normu alebo predpis
- početnosť
- celkový spôsob kontroly
- zodpovednosť
- kto kontrolu vykonáva
- toleranciu
- dokumentovanie

NEPÍŠ OVERIŤ,
ak sa údaj nachádza v referenčnom KSP.

Ak napríklad referenčný KSP obsahuje:

- vizuálnu kontrolu
- kontrolu dokladov
- kontrolu rozmerov
- kontrolu lôžka
- kontrolu potrubia
- kontrolu obsypu
- kontrolu zásypu
- kontrolu zhutnenia
- kontrolu šácht

a rovnaká práca sa vykonáva aj na novom projekte,
použi príslušný riadok referenčného KSP.

===============================================
C. NEZJEDNODUŠUJ HRUBÝ ŠÚR
===============================================

Referenčný KSP môže obsahovať viac samostatných
riadkov pre jednu skupinu prác.

Tieto riadky svojvoľne nespájaj.

Ak referenčný KSP obsahuje samostatné kontroly pre:

- vytýčenie
- výkop
- lôžko
- potrubie
- tvarovky
- tesnenia
- revízne šachty
- obsyp
- zásyp
- hutnenie
- skúšku

zachovaj podobné členenie,
ak sa tieto práce nachádzajú aj v novom projekte.

Výsledný KSP sa má pri porovnaní
s referenčným KSP obsahovo podobať.

===============================================
D. NOVÝ PROJEKT MENÍ KONKRÉTNE ÚDAJE
===============================================

TECHNICKÁ SPRÁVA, ROZPOČET a VÝKRESY
určujú konkrétny nový projekt.

Z nich použi najmä:

- druh potrubia
- materiál potrubia
- DN
- rozmery
- typ šachty
- typ výrobkov
- množstvo
- metre
- kusy
- rozsah prác

Ak je napríklad v referenčnom KSP:

PVC potrubie DN 160

ale nový projekt má:

PVC potrubie DN 200

použi:

PVC potrubie DN 200

ALE kontrolu, spôsob kontroly,
kritérium, početnosť, toleranciu
a dokumentovanie prevezmi
z relevantného riadku referenčného KSP.

===============================================
E. MNOŽSTVO
===============================================

Množstvo ber z:

1. rozpočtu
2. technickej správy
3. výkresov

Ak množstvo nie je jednoznačne dostupné,
môže byť prázdne.

NEPÍŠ automaticky OVERIŤ.

Nevymýšľaj množstvo.

===============================================
F. OVERIŤ - VEĽMI DÔLEŽITÉ
===============================================

Slovo OVERIŤ používaj VÝNIMOČNE.

NESMIEŠ použiť OVERIŤ len preto,
že si nie si istý prepisom údajov.

Ak je údaj v referenčnom KSP,
normálne ho prevezmi.

Ak je údaj v projektovej dokumentácii,
normálne ho použi.

OVERIŤ použi predovšetkým v prípade,
keď nemožno spoľahlivo rozhodnúť,
či je konkrétna SKÚŠKA pre nový projekt
povinná.

===============================================
G. SKÚŠKY - MINIMÁLNY POTREBNÝ ROZSAH
===============================================

Cieľom spoločnosti je:

ČO NAJMENŠÍ POTREBNÝ ROZSAH SKÚŠOK,

ale KSP musí zostať v súlade s požiadavkami,
ktoré sa na projekt vzťahujú.

Pre každú nákladovú alebo samostatnú skúšku
z referenčného KSP posúď:

1. Je relevantná pre nový projekt?

2. Vyžaduje ju výslovne projektová dokumentácia?

3. Vyžaduje ju právny predpis?

4. Vyplýva jej povinnosť zo záväznej technickej
   požiadavky alebo normy použitej pre dané práce?

Ak potrebuješ preveriť aktuálne právne požiadavky,
použi WEB SEARCH.

Uprednostni oficiálne zdroje:

- Slov-Lex
- Úrad pre normalizáciu, metrológiu
  a skúšobníctvo SR
- Ministerstvo dopravy SR

===============================================
H. DÔLEŽITÉ - WEB NIE JE ZDROJOM NOVÉHO KSP
===============================================

Web search používaj iba na overenie,
či je konkrétna skúška alebo kontrola
povinná.

WEB NESMIEŠ používať na:

- vymýšľanie nových skúšok
- pridávanie nových položiek,
  ktoré nie sú v referenčnom KSP
- vytváranie nových procesov

Obsahový základ stále tvorí
REFERENČNÝ KSP.

===============================================
I. ROZHODOVANIE O SKÚŠKE
===============================================

Ak je skúška:

RELEVANTNÁ A POVINNÁ
→ ponechaj ju.

Ak je skúška:

RELEVANTNÁ A VYŽADUJE JU PROJEKT
→ ponechaj ju.

Ak je v referenčnom KSP,
ale nový projekt danú prácu vôbec neobsahuje
→ vynechaj ju.

Ak z dostupných zdrojov nemožno jednoznačne
rozhodnúť o jej povinnosti
→ ponechaj ju a do POZNÁMKY napíš:

OVERIŤ POVINNOSŤ SKÚŠKY

Nepíš OVERIŤ do ostatných polí.

===============================================
J. ZÁKON 133/2013 Z. Z.
===============================================

Ak referenčný KSP používa zákon č. 133/2013 Z. z.
pri kontrole stavebných výrobkov alebo dokladov
k stavebnému výrobku a na novom projekte
sa používa zodpovedajúci stavebný výrobok,
zachovaj tento typ kontroly.

Neinterpretuj však zákon automaticky
ako povinnosť vykonať každú skúšku na stavbe.

===============================================
K. NORMY
===============================================

Ak je konkrétna norma uvedená
v relevantnom riadku referenčného KSP
a ten istý typ práce je v novom projekte,
prevezmi ju.

NEPÍŠ namiesto nej OVERIŤ.

Ak projektová dokumentácia obsahuje
konkrétnejšiu alebo inú požiadavku
pre nový projekt,
použi projektovú dokumentáciu.

Nevymýšľaj číslo normy z pamäti.

===============================================
L. POČETNOSŤ, TOLERANCIE A DOKUMENTOVANIE
===============================================

Tieto údaje majú primárne pochádzať
z REFERENČNÉHO KSP.

Ak sú v relevantnom riadku uvedené,
PREVEZMI ICH.

NENAHRÁDZAJ ich textom OVERIŤ.

===============================================
M. KONTROLY MATERIÁLOV
===============================================

Ak referenčný KSP obsahuje kontroly
stavebných výrobkov, dokladov,
vyhlásení o parametroch,
certifikátov alebo dodacích dokladov
a rovnaký druh materiálu sa používa
v novom projekte,
zachovaj príslušnú kontrolu.

Konkrétny výrobok, materiál,
DN a množstvo prispôsob novému projektu.

===============================================
N. PORADIE
===============================================

Zachovaj technologické a obsahové poradie
čo najbližšie referenčnému KSP.

Výsledok má pôsobiť,
ako keby bol pôvodný referenčný KSP
upravený pre nový projekt.

Nesmie pôsobiť ako úplne nový KSP
vytvorený nezávisle od referencie.

===============================================
O. ZAKÁZANÉ
===============================================

NESMIEŠ svojvoľne:

- vymýšľať skúšky
- vymýšľať kontroly
- vymýšľať normy
- vymýšľať zákony
- vymýšľať tolerancie
- vymýšľať početnosť
- vymýšľať materiály
- vymýšľať množstvá

NEVYPĹŇAJ polovicu tabuľky slovom OVERIŤ.

===============================================
P. JSON VÝSTUP
===============================================

Výstup musí byť iba validné JSON POLE.

Nevracaj markdown.
Nevracaj vysvetlenie.
Nevracaj komentár mimo JSON.
Nevracaj objekt s kľúčom rows.

Formát:

[
  {
    "poradie": "",
    "subproces": "",
    "mnozstvo": "",
    "druh_kontroly": "",
    "sposob_kontroly": "",
    "kriterium": "",
    "pocetnost": "",
    "celkovy_pocet": "",
    "zodpoveda": "",
    "vykona": "",
    "tolerancia": "",
    "dokumentovanie": "",
    "poznamka": ""
  }
]

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
""",

        input=text
    )

    raw_result = clean_json_response(
        response.output_text
    )

    parsed_result = json.loads(
        raw_result
    )

    # ------------------------------------------
    # AK AI PREDSA VRÁTI OBJEKT
    # ------------------------------------------

    if isinstance(
        parsed_result,
        dict
    ):

        for key in [
            "rows",
            "ksp_rows",
            "items",
            "data"
        ]:

            possible_rows = (
                parsed_result.get(key)
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
            "AI nevytvorila KSP "
            "ako zoznam riadkov."
        )

    # ------------------------------------------
    # POVINNÉ STĹPCE
    # ------------------------------------------

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

    clean_rows = []

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
            "AI nevytvorila žiadne "
            "použiteľné riadky KSP."
        )

    return clean_rows


# ==========================================================
# HLAVIČKA PROJEKTU
# ==========================================================

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

Ak údaj, ktorý by si chcel použiť ako ČASŤ,
je rovnaký alebo veľmi podobný hodnote STAVBA,
NESMIEŠ ho použiť ako ČASŤ.

Ak samostatnú časť nenájdeš:

value = "OVERIŤ"
status = "OVERIŤ"
source = "nenájdené"


========================================
ZHOTOVITEĽ
========================================

Primárny zdroj je ZoD.

Hľadaj:
- Zhotoviteľ
- Dodávateľ
- Zhotoviteľ diela

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
    "source": "..."
  },

  "objekt": {
    "value": "...",
    "status": "...",
    "source": "..."
  },

  "cast": {
    "value": "...",
    "status": "...",
    "source": "..."
  },

  "zhotovitel": {
    "value": "...",
    "status": "...",
    "source": "..."
  },

  "objednavatel": {
    "value": "...",
    "status": "...",
    "source": "..."
  }
}

Vráť iba JSON.
""",

        input=text
    )

    raw_result = clean_json_response(
        response.output_text
    )

    return json.loads(
        raw_result
    )
