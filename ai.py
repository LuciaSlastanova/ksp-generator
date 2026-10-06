1. cenová ponuka / rozpočet
2. technická správa
3. ZoD

Časť musí byť odlišná
od názvu celej stavby.

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

        input=metadata_text
    )

    raw_result = clean_json_response(
        response.output_text
    )

    return json.loads(
        raw_result
    )
