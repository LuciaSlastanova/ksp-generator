
Načítavajú sa staršie správy…

Prilepený text(20261002-132521).txt
Dokument
Áno, našla som presne problém.

Funkcia extract_project_metadata(text) síce potrebuje iba 5 údajov do hlavičky, ale na riadku 1810 posiela do modelu celý text, ktorý jej príde:

input=text


To znamená, že ak text obsahuje naraz technickú správu, rozpočet, referenčný KSP, mustru, prípadne ďalšie podklady, tak sa všetko odošle len kvôli zisteniu:

stavby
objektu
časti
zhotoviteľa
objednávateľa
A preto ti to vystrelilo na viac než 600-tisíc tokenov.

Najjednoduchšia oprava je pred odoslaním text skrátiť.

V tejto funkcii:

def extract_project_metadata(text):

hneď pod:

client = get_openai_client()

pridaj:

    max_chars = 120000

    if len(text) > max_chars:
        text = text[:max_chars]

Čiže začiatok bude:

def extract_project_metadata(text):
    """
    Zistí údaje pre hlavičku KSP.
    Vracia value, status a source.
    """

    client = get_openai_client()

    max_chars = 120000

    if len(text) > max_chars:
        text = text[:max_chars]

    response = client.responses.create(

Tým hneď zabrániš tomu, aby sa do jednej požiadavky poslalo obrovské množstvo dát.

Ale toto je zatiaľ bezpečnostná brzda, nie ideálne finálne riešenie.

Lepšie bude potom spraviť to, aby sa do extract_project_metadata() vôbec neposielal napríklad celý referenčný KSP, pretože v tvojom vlastnom promte máš napísané, že referenčný KSP ani KSP mustra sa nesmú použiť ako zdroj údajov hlavičky. 

Čiže ďalší krok by som spravila takto:

najprv pridaj ten limit 120000 znakov, commitni a otestuj.

Ak to prejde, potom sa pozrieme do kódu, odkiaľ sa extract_project_metadata(text) volá, a vyhodíme z toho vstupu referenčný KSP a mustru úplne. To je správne riešenie.

a je to otrebné aby hlavičku takto zbytočne kontrolovala?
Nie, podľa toho kódu nie je potrebné, aby hlavičku kontrolovala takto draho.

Tá funkcia extract_project_metadata() hľadá iba 5 údajov: stavba, objekt, časť, zhotoviteľ, objednávateľ. Zároveň máš v prompt-e výslovne napísané, že referenčný KSP a KSP mustra nesmú určovať tieto údaje. 
 

Čiže posielať tam celý obrovský balík podkladov je zbytočné.

Ja by som to prerobila tak, aby hlavička čítala iba:

ZoD, ak je nahratá,
technickú správu,
prípadne cenovú ponuku/rozpočet.
A aj z týchto dokumentov netreba celé tisíce riadkov. Stačia časti, kde sa typicky vyskytujú názvy projektu a zmluvné strany.

Takže odpoveď je: áno, túto kontrolu hlavičky treba zjednodušiť. Limit 120 000 znakov, ktorý som navrhla, je len poistka proti pádu. Lepšie je opraviť vstup tak, aby sa tam neposielal celý projekt.

Ak chceš, ďalší krok spravíme správne: nájdeme, kde sa volá extract_project_metadata(...), a upravíme, aký text jej odovzdáva.

ok tak to zjednodušne

Trvalo to 13s
Áno. Najjednoduchšie je to upraviť priamo v extract_project_metadata(), takže teraz nemusíme prerábať zvyšok aplikácie.

Tvoja hlavička potrebuje iba 5 údajov a podľa vlastných pravidiel sa referenčný KSP ani mustra nesmú použiť ako zdroj hlavičky. 
 

Spravme teda toto.

1. Nájdeš v ai.py
def extract_project_metadata(text):

A hneď za:

client = get_openai_client()

vlož:

    # Pre hlavičku nepotrebujeme celý projekt.
    # Stačí začiatok podkladov, kde bývajú názvy stavby,
    # objektu, objednávateľa a zhotoviteľa.
    text = text[:80000]

Čiže začiatok bude:

def extract_project_metadata(text):
    """
    Zistí údaje pre hlavičku KSP.
    Vracia value, status a source.
    """

    client = get_openai_client()

    # Pre kontrolu hlavičky neposielame celý projekt do AI
    text = text[:80000]

    response = client.responses.create(
        model="gpt-5.6-terra",

A dole necháš normálne:

input=text

Prečo 80 000?
Je to rádovo oveľa menej než tých 615-tisíc tokenov, ktoré sa aplikácia snažila poslať teraz. Zároveň je to stále dosť textu na to, aby AI našla základné údaje.

Ale ešte by som spravila jednu malú zmenu v texte pokynov.

Teraz tam máš prioritu:

ZoD
technická správa
cenová ponuka / rozpočet 
To je správne.

Takže zatiaľ nič iné nemeníme.

Po commite skús znova:

Detail projektu → Skontrolovať údaje hlavičky

Ak to prejde, až potom môžeme urobiť ešte lepšiu verziu, kde aplikácia pre hlavičku automaticky úplne vyhodí reference_ksp a ďalšie nepotrebné dokumenty. Teraz by som to zbytočne nekomplikovala.

oprav mi celý tento subor a daj do chatu

Trvalo to 1m 34s
Áno. Opravila som celý ai.py tak, aby kontrola hlavičky neposielala do AI celý obrovský projekt. Pôvodne funkcia extract_project_metadata() posielala celý text, hoci kontroluje iba stavbu, objekt, časť, zhotoviteľa a objednávateľa. 

Urobila som dve zmeny:

pridala som funkciu _prepare_project_metadata_text(), ktorá vyhodí referenčný KSP a mustru, ak sú označené typom dokumentu,
pri veľmi veľkých podkladoch vyberie hlavne úseky súvisiace s hlavičkou a maximálne približne 80 000 znakov.
Tiež som skontrolovala syntax cez Python a súbor je syntakticky v poriadku.

Celý opravený súbor máš tu:

A toto je presne nová časť, ktorú som doň pridala:

# ==========================================================
# POMOCNÁ FUNKCIA - ZJEDNODUŠENIE PODKLADOV PRE HLAVIČKU
# ==========================================================

def _prepare_project_metadata_text(text, max_chars=80000):
    """
    Pripraví menší vstup iba pre kontrolu hlavičky projektu.

    - odstráni sekcie referenčného KSP a KSP mustry, ak sú označené
      markerom "--- TYP DOKUMENTU: ... ---"
    - pri veľmi veľkom vstupe vyberie začiatok dokumentov a riadky
      okolo výrazov dôležitých pre hlavičku
    - výsledok obmedzí na max_chars znakov
    """
    text = str(text or "")

    if not text:
        return ""

    marker_pattern = re.compile(
        r"---\s*TYP DOKUMENTU:\s*([^\n-]+?)\s*---",
        re.IGNORECASE,
    )

    matches = list(marker_pattern.finditer(text))

    if matches:
        kept_sections = []

        for index, match in enumerate(matches):
            start = match.start()
            end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(text)
            )

A funkcia hlavičky teraz začína takto:

def extract_project_metadata(text):
    """
    Zistí údaje pre hlavičku KSP.
    Vracia value, status a source.
    """

    client = get_openai_client()

    metadata_text = _prepare_project_metadata_text(text)

    response = client.responses.create(
        model="gpt-5.6-terra",

a hlavne dole už nie je:

input=text

ale:

input=metadata_text

Čiže na GitHube môžeš pokojne celý obsah ai.py nahradiť týmto opraveným súborom. Ostatnú logiku generovania KSP som nemenila.


ai.py
Kód



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
