import json
import math
import re

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
# POMOCNÉ FUNKCIE - VÝPOČET CELKOVÉHO POČTU SKÚŠOK/KONTROL
# ==========================================================

def _normalize_number(value):
    """Prevedie slovenský zápis čísla na float."""
    if value is None:
        return None

    normalized = (
        str(value)
        .replace("\xa0", "")
        .replace(" ", "")
        .replace(",", ".")
        .strip()
    )

    try:
        return float(normalized)
    except ValueError:
        return None


def _normalize_unit(unit):
    """Zjednotí zápis MJ, napr. m³ -> m3 a m² -> m2."""
    if not unit:
        return ""

    return (
        str(unit)
        .strip()
        .lower()
        .replace("³", "3")
        .replace("²", "2")
        .replace(" ", "")
    )


def calculate_total_count(quantity_text, frequency_text):
    """
    Vypočíta celkový počet skúšok/kontrol z množstva a početnosti.

    Podporované príklady:
        16585,708 m3 + 1 skúška / 5000 m3 -> 4
        9703,5 m2 + 1 skúška na 1000 m2 -> 10
        127 ks + 1x / 50 ks -> 3
        2100 m3 + min. 1 skúška na každých 500 m3 -> 5
        3000 m2 + 2 skúšky / 1000 m2 -> 6
        3000 m2 + 2x na každých 1000 m2 -> 6

    Automaticky sa počítajú iba jednoznačné matematické pravidlá.
    Slovné alebo podmienené pravidlá sa nechávajú bez výpočtu.
    """
    if not quantity_text or not frequency_text:
        return None

    quantity_match = re.search(
        r"([0-9][0-9\s\xa0.,]*)\s*(m(?:2|3|²|³)?|ks|t|kg|hod|l)?\b",
        str(quantity_text),
        re.IGNORECASE,
    )
    if not quantity_match:
        return None

    frequency = (
        str(frequency_text)
        .strip()
        .lower()
        .replace("×", "x")
    )

    blocked_phrases = (
        "každá dodávka",
        "kazda dodavka",
        "každej dodávke",
        "kazdej dodavke",
        "každý domiešavač",
        "kazdy domiesavac",
        "každá zmena",
        "kazda zmena",
        "priebežne",
        "priebezne",
        "podľa potreby",
        "podla potreby",
        "100 %",
        "100%",
        "na začiatku",
        "na zaciatku",
        "pri zmene",
        "pri každej",
        "pri kazdej",
        "podľa pd",
        "podla pd",
        "podľa tkp",
        "podla tkp",
    )
    if any(phrase in frequency for phrase in blocked_phrases):
        return None

    # "min. 1 skúška..." je stále matematicky jednoznačné minimum.
    frequency = re.sub(r"\bmin(?:imálne|imalne)?\.?\s*", "", frequency)
    frequency = re.sub(r"\bmin\.\s*", "", frequency)

    unit_pattern = r"(m(?:2|3|²|³)?|ks|t|kg|hod|l)?"
    interval_pattern = r"([0-9][0-9\s\xa0.,]*)"

    patterns = [
        rf"(\d+)\s*(?:x|ks|skúšky|skusky|skúška|skuska|kontroly|kontrola|merania|meranie|odbery|odber)?"
        rf"\s*/\s*{interval_pattern}\s*{unit_pattern}\b",

        rf"(\d+)\s*(?:x|ks|skúšky|skusky|skúška|skuska|kontroly|kontrola|merania|meranie|odbery|odber)?"
        rf"\s+na\s+(?:každých\s+|kazdych\s+)?{interval_pattern}\s*{unit_pattern}\b",

        rf"(\d+)\s*x?\s+(?:každých|kazdych)\s+{interval_pattern}\s*{unit_pattern}\b",

        rf"(\d+)\s*/\s*{interval_pattern}\s*{unit_pattern}\b",
    ]

    match = None
    for pattern in patterns:
        match = re.search(pattern, frequency, re.IGNORECASE)
        if match:
            break

    if not match:
        return None

    tests_per_interval = _normalize_number(match.group(1))
    interval = _normalize_number(match.group(2))
    quantity = _normalize_number(quantity_match.group(1))

    if (
        tests_per_interval is None
        or interval is None
        or quantity is None
        or tests_per_interval <= 0
        or interval <= 0
    ):
        return None

    quantity_unit = _normalize_unit(quantity_match.group(2) or "")
    frequency_unit = _normalize_unit(match.group(3) or "")

    if quantity_unit and frequency_unit and quantity_unit != frequency_unit:
        return None

    intervals = math.ceil(quantity / interval)
    total = intervals * tests_per_interval

    if float(total).is_integer():
        return str(int(total))

    return str(math.ceil(total))


def _slugify_group_part(value):
    """Normalizuje časť group_key bez diakritiky a medzier."""
    value = str(value or "").strip().lower()

    replacements = {
        "á": "a", "ä": "a", "č": "c", "ď": "d", "é": "e",
        "í": "i", "ĺ": "l", "ľ": "l", "ň": "n", "ó": "o",
        "ô": "o", "ŕ": "r", "š": "s", "ť": "t", "ú": "u",
        "ý": "y", "ž": "z",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)

    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def stabilize_group_key(item_name, group_key):
    """
    Python poistka proti zlúčeniu technicky rozdielnych položiek.

    AI vytvorí základný group_key.
    Python doplní rozlišovací znak, ak názov obsahuje jasný technický
    variant, ktorý sa nesmie agregovať s opačným variantom.
    """
    name = str(item_name or "").strip().lower()
    key = _slugify_group_part(group_key)

    if not key:
        return key

    qualifier_rules = [
        (("bez zhutnenia", "nezhutnen"), "bez_zhutnenia"),
        (("so zhutnením", "so zhutnenim", "s hutnením", "s hutnenim"), "so_zhutnenim"),

        (("bez paženia", "bez pazenia", "nepažen", "nepazen"), "bez_pazenia"),
        (("s pažením", "s pazenim"), "s_pazenim"),

        (("bez odvozu",), "bez_odvozu"),
        (("s odvozom", "so odvozom"), "s_odvozom"),

        (("bez dodávky", "bez dodavky"), "bez_dodavky"),
        (("s dodávkou", "s dodavkou", "so dodávkou", "so dodavkou"), "s_dodavkou"),

        (("bez montáže", "bez montaze"), "bez_montaze"),
        (("s montážou", "s montazou", "so montážou", "so montazou"), "s_montazou"),
    ]

    detected = []

    for phrases, qualifier in qualifier_rules:
        if any(phrase in name for phrase in phrases):
            detected.append(qualifier)

    # Bežné technické parametre, ktoré často odlišujú výrobok alebo skúšky.
    technical_patterns = [
        (r"\bsn\s*[- ]?(\d+)\b", "sn"),
        (r"\bdn\s*[- ]?(\d+)\b", "dn"),
        (r"\bc\s*(\d+)\s*/\s*(\d+)\b", "c"),
        (r"\bs\s*([1-5])\b", "s"),
        (r"\bpn\s*[- ]?(\d+(?:[.,]\d+)?)\b", "pn"),
    ]

    for pattern, prefix in technical_patterns:
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            suffix = "_".join(g.replace(",", "_") for g in match.groups())
            detected.append(f"{prefix}_{suffix}")

    for qualifier in detected:
        if qualifier and qualifier not in key:
            key = f"{key}_{qualifier}"

    return key


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
# AI KLASIFIKÁCIA RIADKOV CENOVEJ PONUKY
# ==========================================================

def classify_budget_rows(text):
    """
    AI prečíta surové riadky zo všetkých hárkov cenovej ponuky
    a určí, ktoré riadky sú skutočné položky a čo znamenajú.

    Táto funkcia NESČÍTAVA množstvá.
    Sčítanie spraví neskôr Python až podľa group_key + MJ.
    """

    client = get_openai_client()

    response = client.responses.create(
        model="gpt-5.6-terra",
        instructions="""
Si AI systém na analýzu stavebných cenových ponúk a rozpočtov.

Dostaneš text vytvorený z Excelu.
Text obsahuje všetky hárky a pôvodné riadky napríklad:

--- LIST: SO 01 ---
RIADOK 12: 1 | Výkop ryhy | m3 | 120,50 | 15,20 | 1831,00

TVOJOU ÚLOHOU JE IBA POCHOPIŤ RIADKY.
NESMIEŠ TVORIŤ KSP.
NESMIEŠ SČÍTAVAŤ MNOŽSTVÁ.

========================================
1. ROZPOZNAJ SKUTOČNÚ POLOŽKU
========================================

Každý riadok označ:

include = true

iba ak ide o skutočnú položku práce, materiálu,
výrobku, montáže, skúšky alebo inej vecnej položky
relevantnej pre realizáciu stavby.

Riadky ako:
- názov stavby
- názov objektu
- nadpis
- medzisúčet
- súčet
- cena spolu
- DPH
- rekapitulácia
- poznámka
- prázdny technický riadok
- hlavička tabuľky

označ:

include = false

========================================
2. NÁZOV POLOŽKY
========================================

Do item_name daj technický názov položky bez ceny.

Nevkladaj:
- jednotkovú cenu
- cenu spolu
- DPH
- poradové číslo
- kód položky, ak nie je súčasťou technického významu

Zachovaj však technicky dôležité údaje:
- materiál
- DN
- priemer
- rozmer
- triedu
- SN
- typ
- hrúbku
- druh konštrukcie

========================================
3. KATEGÓRIA
========================================

category musí byť jedna z hodnôt:

- "praca"
- "material"
- "vyrobok"
- "montaz"
- "skuska"
- "ine"

Vyber podľa významu položky.

========================================
4. MNOŽSTVO A MJ
========================================

Zisti:

unit
quantity

quantity musí obsahovať iba množstvo,
nie cenu.

Ak je množstvo napríklad:

"120,50"

vráť:

120.5

ako číslo.

Ak množstvo nemožno jednoznačne určiť:
quantity = null

unit je napríklad:
- m
- m2
- m3
- ks
- t
- kg
- hod
- súbor
- komplet

Ak MJ nemožno jednoznačne určiť:
unit = ""

NEZAMEŇ cenu za množstvo.

Ak je v riadku viac čísel,
využi názvy stĺpcov, susedné riadky,
kontext hárku a typické členenie rozpočtu.

========================================
5. DN / ROZMER
========================================

Do dimension daj iba technicky relevantný rozmer,
napríklad:

"DN160"
"DN300"
"400x400"
"hr. 150 mm"
"SN8"

Ak relevantný rozmer nie je:
dimension = ""

========================================
6. MATERIÁL
========================================

Do material daj základný materiál alebo typ výrobku,
ak ho možno určiť, napríklad:

"PVC-U"
"PP"
"PE100"
"betón"
"štrkopiesok"
"drvené kamenivo"

Ak ho nemožno určiť:
material = ""

========================================
7. GROUP_KEY - NA SČÍTANIE
========================================

group_key je veľmi dôležitý.

Má označovať významovo rovnakú položku,
ktorú bude možné neskôr sčítať s rovnakými položkami
z iných hárkov.

group_key musí byť krátky, stabilný a technický.

Príklady:

"potrubie_pvc_dn160"
"potrubie_pvc_dn300"
"lozko_strkopiesok"
"obsyp_potrubia"
"vykop_ryhy"
"zasyp_ryhy_so_zhutnenim"
"zasyp_ryhy_bez_zhutnenia"
"revizna_sachta_dn400"
"tlakova_skuska_pe_dn90"

Rovnaké významové položky pomenované rozdielne
majú dostať rovnaký group_key.

ALE NESMIEŠ spojiť položky, ktoré sa technicky líšia.

NESMIEŠ dať rovnaký group_key pre položky, ktoré sa technicky líšia.

Rozlišuj najmä:
- odlišné DN, priemery a rozmery
- odlišné MJ
- odlišný materiál alebo typ výrobku
- odlišné triedy a parametre, napr. SN, PN, C25/30, C30/37, S4, S5
- prácu a materiál, ak sú samostatnými položkami
- montáž a dodávku, ak sú samostatnými položkami
- výkop a zásyp
- materiál a skúšku
- variant "so zhutnením" a "bez zhutnenia"
- variant "s pažením" a "bez paženia"
- variant "s odvozom" a "bez odvozu"
- variant "s dodávkou" a "bez dodávky"
- variant "s montážou" a "bez montáže"
- akúkoľvek inú vlastnosť, ktorá mení technológiu, skúšku,
  normu, početnosť, kvalitatívnu požiadavku alebo spôsob realizácie

VŠEOBECNÉ PRAVIDLO:
Ak by zlúčenie dvoch položiek mohlo spôsobiť nesprávne množstvo
pre inú skúšku, inú technológiu alebo inú požiadavku,
musia mať rozdielny group_key.

Nerozdeľuj však položky len kvôli nepodstatnému rozdielu v slovoslede
alebo pravopise. Významovo rovnaké položky z rôznych hárkov majú
naďalej dostať rovnaký group_key.

Ak si nie si istý, vytvor radšej odlišný group_key.
Nesprávne sčítanie je horšie ako ponechanie dvoch skupín.

========================================
8. CENY IGNORUJ
========================================

Nevracaj:
- jednotkovú cenu
- cenu spolu
- sadzbu
- DPH
- obchodnú maržu

Ceny nie sú pre KSP potrebné.

========================================
9. PÔVOD RIADKU
========================================

Zachovaj:

sheet
row_number

presne podľa vstupného textu.

========================================
10. VÝSTUP
========================================

Vráť iba validné JSON pole.

Každý prvok musí mať presne tieto kľúče:

sheet
row_number
include
item_name
category
unit
quantity
dimension
material
group_key
reason

Príklad:

[
  {
    "sheet": "SO 01",
    "row_number": 12,
    "include": true,
    "item_name": "PVC-U kanalizačné potrubie DN160 SN8",
    "category": "material",
    "unit": "m",
    "quantity": 120.5,
    "dimension": "DN160",
    "material": "PVC-U",
    "group_key": "potrubie_pvc_dn160",
    "reason": "Skutočná materiálová položka"
  },
  {
    "sheet": "SO 01",
    "row_number": 2,
    "include": false,
    "item_name": "",
    "category": "ine",
    "unit": "",
    "quantity": null,
    "dimension": "",
    "material": "",
    "group_key": "",
    "reason": "Hlavička tabuľky"
  }
]

Vráť iba JSON.
""",
        input=text
    )

    raw_result = clean_json_response(
        response.output_text
    )

    parsed_result = json.loads(
        raw_result
    )

    if isinstance(
        parsed_result,
        dict
    ):
        for key in [
            "rows",
            "items",
            "data",
            "budget_rows"
        ]:
            value = parsed_result.get(
                key
            )

            if isinstance(
                value,
                list
            ):
                parsed_result = value
                break

    if not isinstance(
        parsed_result,
        list
    ):
        raise ValueError(
            "AI nevytvorila klasifikáciu "
            "cenovej ponuky ako zoznam riadkov."
        )

    clean_rows = []

    required_fields = [
        "sheet",
        "row_number",
        "include",
        "item_name",
        "category",
        "unit",
        "quantity",
        "dimension",
        "material",
        "group_key",
        "reason"
    ]

    for item in parsed_result:

        if not isinstance(
            item,
            dict
        ):
            continue

        clean_item = {}

        for field in required_fields:
            clean_item[field] = item.get(
                field
            )

        clean_item["sheet"] = (
            str(
                clean_item.get("sheet") or ""
            ).strip()
        )

        try:
            clean_item["row_number"] = int(
                clean_item.get("row_number")
            )

        except (
            TypeError,
            ValueError
        ):
            clean_item["row_number"] = None

        clean_item["include"] = bool(
            clean_item.get("include")
        )

        clean_item["item_name"] = (
            str(
                clean_item.get("item_name") or ""
            ).strip()
        )

        clean_item["category"] = (
            str(
                clean_item.get("category") or "ine"
            ).strip()
        )

        clean_item["unit"] = (
            str(
                clean_item.get("unit") or ""
            ).strip()
        )

        quantity = clean_item.get(
            "quantity"
        )

        if isinstance(
            quantity,
            str
        ):
            normalized_quantity = (
                quantity
                .replace(" ", "")
                .replace(",", ".")
            )

            try:
                quantity = float(
                    normalized_quantity
                )

            except ValueError:
                quantity = None

        elif not isinstance(
            quantity,
            (
                int,
                float
            )
        ):
            quantity = None

        clean_item["quantity"] = (
            quantity
        )

        clean_item["dimension"] = (
            str(
                clean_item.get("dimension") or ""
            ).strip()
        )

        clean_item["material"] = (
            str(
                clean_item.get("material") or ""
            ).strip()
        )

        clean_item["group_key"] = stabilize_group_key(
            clean_item.get("item_name", ""),
            clean_item.get("group_key", ""),
        )

        clean_item["reason"] = (
            str(
                clean_item.get("reason") or ""
            ).strip()
        )

        clean_rows.append(
            clean_item
        )

    if not clean_rows:
        raise ValueError(
            "AI nevytvorila žiadne "
            "použiteľné riadky cenovej ponuky."
        )

    return clean_rows


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
PREVEZMI z referenčného KSP CELÝ RELEVANTNÝ RIADOK:

- druh kontroly
- spôsob kontroly
- kritérium
- normu alebo predpis
- početnosť
- zodpovednosť
- kto kontrolu vykonáva
- toleranciu
- dokumentovanie
- poznámku, ak je technicky relevantná

Nesmieš prebrať iba časť riadku a ostatné polia
nechať prázdne.

Ak je napríklad v referenčnom riadku:
kriterium = "PD"
zodpoveda = "SV"
vykona = "SV"
tolerancia = "podľa PD"
dokumentovanie = "zápis v SD"

potom tieto hodnoty normálne prevezmi.

NEPÍŠ OVERIŤ a NENECHÁVAJ PRÁZDNE POLE,
ak sa údaj nachádza v relevantnom riadku
referenčného KSP.

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

Množstvo ber z AGREGOVANÝCH POLOŽIEK
CENOVEJ PONUKY, ktoré sú vložené do vstupu.

Tieto agregované množstvá už boli spočítané
Python kódom zo všetkých detailných hárkov.

Preto:

- NESČÍTAVAJ ich znova,
- NEBER množstvo z referenčného KSP,
- NEBER množstvo z technickej správy,
  ak už existuje agregovaná položka,
- NEVYMÝŠĽAJ množstvo,
- zachovaj presnú MJ.

Ak je agregovaná položka napríklad:

položka=Lôžko pod potrubie...
množstvo=504.618
MJ=m3

výsledný KSP musí mať:

mnozstvo = "504,618 m3"

Ak množstvo pre konkrétny subproces
v agregovanom zozname neexistuje,
pole môže zostať prázdne.

NEPÍŠ automaticky OVERIŤ.

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

Pri každom výslednom riadku urob kontrolu:

1. nájdi relevantný riadok v referenčnom KSP,
2. prevezmi z neho kritérium,
3. prevezmi početnosť PRESNE ako pravidlo,
4. prevezmi zodpovednosť,
5. prevezmi kto kontrolu vykoná,
6. prevezmi toleranciu,
7. prevezmi dokumentovanie.

DÔLEŽITÉ PRE CELKOVÝ POČET:

Pole "pocetnost" obsahuje pravidlo z referenčného KSP, napr.:

"1 skúška / 5000 m3"
"1 kontrola / 1000 m2"
"1 skúška na 50 m"
"1x / 50 ks"
"min. 1 skúška na každých 500 m3"
"2 skúšky / 1000 m2"
"2x na každých 1000 m2"

Ak je početnosť matematicky vypočítateľná z množstva,
CELKOVÝ POČET NEPOČÍTAJ. V takom prípade vráť:

"celkovy_pocet": ""

Výsledný počet vypočíta Python po prijatí JSON odpovede.

Ak celkový počet nie je matematicky odvoditeľný z množstva
(napr. "priebežne", "každá dodávka", "100 %", "podľa potreby",
"na začiatku a potom pri zmene" alebo iné textové pravidlo),
môžeš prevziať z referenčného KSP relevantný textový spôsob kontroly,
ak tam je uvedený.

Ak je niektorá z hodnôt kritérium, početnosť, zodpovednosť,
vykoná, tolerancia alebo dokumentovanie v referenčnom riadku
vyplnená, NESMIE zostať vo výsledku prázdna.

Prázdne pole je prípustné iba vtedy,
ak je prázdne aj v relevantnom referenčnom riadku
a projekt neposkytuje konkrétnejšiu hodnotu.

NENAHRÁDZAJ tieto údaje textom OVERIŤ.

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
N2. KONTROLA ÚPLNOSTI PRED VÝSTUPOM
===============================================

Pred vytvorením JSON výstupu urob ešte jednu
vnútornú kontrolu úplnosti.

A. KONTROLA AGREGOVANÉHO ROZPOČTU

Prejdi všetky AGREGOVANÉ POLOŽKY CENOVEJ PONUKY.

Ak položka predstavuje prácu, materiál alebo výrobok,
pre ktorý existuje relevantná kontrola alebo skúška
v referenčnom KSP, musí byť v novom KSP zastúpená.

Nesmieš relevantnú agregovanú položku potichu vynechať.

Ak je jedna kontrola spoločná pre viac agregovaných
položiek rovnakého technického typu, môžeš ich zlúčiť
iba ak tým nestratíš rozdielne:
- materiály,
- DN,
- triedy,
- rozmery,
- MJ,
- požiadavky na kontrolu.

B. KONTROLA VYPLNENIA RIADKOV

Pre každý výsledný riadok skontroluj tieto polia:

- druh_kontroly
- sposob_kontroly
- kriterium
- pocetnost
- zodpoveda
- vykona
- tolerancia
- dokumentovanie

Ak je hodnota v relevantnom referenčnom riadku,
musí byť aj vo výslednom riadku.

Výnimka je pole "celkovy_pocet": pri číselnej intervalovej
početnosti ho nechaj prázdne, pretože ho vypočíta Python.

Nevytváraj riadky, kde zostane väčšina týchto polí
prázdna, ak ich referenčný KSP obsahuje.

C. KONTROLA MNOŽSTIEV

Ak má výsledný subproces zodpovedajúcu
agregovanú položku cenovej ponuky,
použi presné agregované množstvo a MJ.

Nesmieš použiť čiastkové množstvo len z jedného hárku.

D. KONTROLA REFERENCIE

Výsledok má byť adaptáciou referenčného KSP,
nie jeho zjednodušenou skrátenou verziou.

Ak má relevantný referenčný subproces viac kontrolných
riadkov, zachovaj všetky relevantné riadky,
pokiaľ ich vedome neoznačíš ako REMOVE_CANDIDATE
alebo VERIFY podľa pravidiel vyššie.

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
PROCES / SKUPINA PRÁC
===============================================

Každý riadok musí mať aj pole "proces".

Pole "proces" je nadradená skupina prác použitá
ako samostatný deliaci riadok KSP.

Pre kanalizačné stavby používaj podľa obsahu napríklad:

- "Prípravné práce"
- "Zemné práce"
- "Armovacie práce"
- "Konštrukčné vrstvy"
- "Rúrové vedenie a ostatné konštrukcie"
- "Skúšky a preberanie"

Nevytváraj proces pre každý jednotlivý riadok.
Viac po sebe idúcich subprocesov má patriť
pod jeden spoločný proces.

Ak referenčný KSP používa vlastné pomenovanie procesov,
uprednostni pomenovanie z referenčného KSP.


===============================================
Q. STAV RIADKU PRE ODBORNÚ KONTROLU
===============================================

Každý výsledný riadok musí mať aj:

- "status"
- "status_reason"
- "legal_basis"

Povolené hodnoty "status":

KEEP
REMOVE_CANDIDATE
VERIFY

Použi ich takto:

KEEP
= riadok patrí do výsledného KSP.
Použi najmä ak:
- kontrola/skúška vyplýva z projektu,
- je potrebná pre daný rozsah prác,
- alebo je jej potreba podložená právnym predpisom,
  záväznou technickou požiadavkou či relevantným
  referenčným KSP.

REMOVE_CANDIDATE
= riadok NEVYMAŽ.
Ponechaj ho vo výsledku, ale označ ako kandidáta
na vyradenie, ak:
- práca je v projekte relevantná,
- referenčný KSP túto skúšku/kontrolu obsahuje,
- ale nenašiel si dostatočný podklad, že práve táto
  samostatná skúška je pre nový projekt potrebná,
- a nejde len o chýbajúcu informáciu.

VERIFY
= riadok NEVYMAŽ.
Použi, ak sa z oficiálnych dostupných zdrojov
nedá spoľahlivo rozhodnúť, či skúška alebo kontrola
musí byť vykonaná.

DÔLEŽITÉ:
- Ak daná práca alebo materiál v novom projekte
  vôbec nie sú, riadok nevytváraj.
- REMOVE_CANDIDATE nie je právny záver.
  Je to upozornenie pre odbornú kontrolu.
- VERIFY používaj pri skutočnej neistote.
- Neoznačuj bežnú vizuálnu alebo dokladovú kontrolu
  na vyradenie len preto, že nie je nákladná skúška.

"status_reason":
napíš jednou krátkou vetou dôvod označenia.

"legal_basis":
uveď stručne podklad, ktorý si skutočne našiel
alebo použil, napríklad:
- "Zákon č. 442/2002 Z. z. § 11"
- "Vyhláška č. 684/2006 Z. z."
- "Zákon č. 133/2013 Z. z."
- "PD"
- "Referenčný KSP"

Nevymýšľaj paragraf alebo číslo normy.
Ak si právny podklad neoveril, nechaj legal_basis
prázdne alebo uveď len "Referenčný KSP".

Pri verejnej kanalizácii venuj osobitnú pozornosť
aktuálnemu zneniu:
- zákona č. 442/2002 Z. z.,
- vyhlášky č. 684/2006 Z. z.,
- zákona č. 133/2013 Z. z. pri stavebných výrobkoch.

Pred použitím právneho záveru over aktuálne znenie
v povolených oficiálnych webových zdrojoch.

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
    "proces": "",
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
    "poznamka": "",
    "status": "KEEP",
    "status_reason": "",
    "legal_basis": ""
  }
]

Pred odoslaním JSON:
- skontroluj, že relevantné agregované položky neboli vynechané,
- skontroluj, že množstvá sú z agregovaného rozpočtu,
- skontroluj, že polia kriterium, zodpoveda, vykona,
  tolerancia a dokumentovanie nie sú prázdne,
  ak ich obsahuje relevantný referenčný riadok,
- pri matematicky vypočítateľnej početnosti nechaj celkovy_pocet
  prázdny; vypočíta ho Python.

Každý riadok musí obsahovať:

proces
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
status
status_reason
legal_basis
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
        "proces",
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
        "poznamka",
        "status",
        "status_reason",
        "legal_basis"
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

        status = str(
            clean_row.get(
                "status",
                "KEEP"
            )
            or "KEEP"
        ).strip().upper()

        if status not in {
            "KEEP",
            "REMOVE_CANDIDATE",
            "VERIFY"
        }:
            status = "VERIFY"

        clean_row["status"] = status

        # --------------------------------------------------
        # CELKOVÝ POČET POČÍTA PYTHON, NIE AI
        # --------------------------------------------------
        # Ak je početnosť jednoznačný číselný interval
        # (napr. 1 skúška / 5000 m3), vypočítame počet
        # deterministicky a vždy zaokrúhlime nahor.
        calculated_count = calculate_total_count(
            clean_row.get("mnozstvo", ""),
            clean_row.get("pocetnost", ""),
        )

        if calculated_count is not None:
            clean_row["celkovy_pocet"] = calculated_count

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
