import io
import re
import unicodedata
import pandas as pd


# ==========================================================
# VŠEOBECNÉ POMOCNÉ FUNKCIE
# ==========================================================

def _normalize_text(value):
    if value is None:
        return ""

    text = str(value).strip().lower()

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


def _normalize_code(value):
    text = _normalize_text(
        value
    )

    text = re.sub(
        r"\.s$",
        "",
        text
    )

    return text


def _to_number(value):
    if value is None:
        return None

    if isinstance(
        value,
        bool
    ):
        return None

    if isinstance(
        value,
        (int, float)
    ):
        return float(value)

    text = str(
        value
    ).strip()

    if not text:
        return None

    text = (
        text
        .replace("\xa0", "")
        .replace(" ", "")
        .replace(",", ".")
    )

    try:
        return float(text)

    except Exception:
        return None


# ==========================================================
# PDF
# ==========================================================

def extract_text_from_pdf(file_bytes):
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader

    reader = PdfReader(
        io.BytesIO(file_bytes)
    )

    parts = []

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):
        text = (
            page.extract_text()
            or ""
        )

        parts.append(
            f"\n--- STRANA {page_number} ---\n{text}"
        )

    return "\n".join(
        parts
    )


# ==========================================================
# DOCX
# ==========================================================

def extract_text_from_docx(file_bytes):
    from docx import Document

    document = Document(
        io.BytesIO(file_bytes)
    )

    parts = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()

        if text:
            parts.append(
                text
            )

    for table_number, table in enumerate(
        document.tables,
        start=1
    ):
        parts.append(
            f"\n--- TABUĽKA {table_number} ---"
        )

        for row in table.rows:
            values = [
                cell.text.strip()
                for cell in row.cells
            ]

            if any(values):
                parts.append(
                    " | ".join(values)
                )

    return "\n".join(
        parts
    )


# ==========================================================
# EXCEL - TEXT PRE AI
# ==========================================================

def extract_excel_rows(file_bytes):
    sheets = pd.read_excel(
        io.BytesIO(file_bytes),
        sheet_name=None,
        header=None,
        dtype=object
    )

    result = []

    for sheet_name, dataframe in sheets.items():

        for dataframe_index, row in dataframe.iterrows():

            values = []

            for value in row.tolist():

                if pd.isna(value):
                    values.append("")
                else:
                    values.append(
                        str(value).strip()
                    )

            if not any(
                value != ""
                for value in values
            ):
                continue

            result.append(
                {
                    "sheet": str(
                        sheet_name
                    ),
                    "row_number": int(
                        dataframe_index
                    ) + 1,
                    "values": values
                }
            )

    return result


def extract_text_from_excel(file_bytes):
    rows = extract_excel_rows(
        file_bytes
    )

    if not rows:
        return ""

    parts = []
    current_sheet = None

    for row in rows:

        sheet = row.get(
            "sheet",
            ""
        )

        if sheet != current_sheet:
            current_sheet = sheet

            parts.append(
                f"\n--- LIST: {sheet} ---"
            )

        parts.append(
            "RIADOK "
            + str(
                row.get(
                    "row_number",
                    ""
                )
            )
            + ": "
            + " | ".join(
                row.get(
                    "values",
                    []
                )
            )
        )

    return "\n".join(
        parts
    )


# ==========================================================
# ROZPOČET - 100 % PYTHON, BEZ AI
# ==========================================================

def extract_budget_items_python(file_bytes):
    """
    Nájde v každom detailnom hárku tabuľku:
    Kód | Popis | MJ | Množstvo

    Rekapitulačné hárky zámerne preskočí,
    aby sa množstvá nespočítali dvakrát.

    Táto funkcia NEVOLÁ AI.
    """

    sheets = pd.read_excel(
        io.BytesIO(file_bytes),
        sheet_name=None,
        header=None,
        dtype=object
    )

    items = []

    for sheet_name, dataframe in sheets.items():

        normalized_sheet_name = (
            _normalize_text(
                sheet_name
            )
        )

        if (
            "rekapitul" in normalized_sheet_name
            or "kryci list" in normalized_sheet_name
        ):
            continue

        header_row_index = None
        header_columns = None

        # Nájdeme riadok, kde sú všetky štyri hlavičky.
        for dataframe_index, row in dataframe.iterrows():

            normalized_values = [
                _normalize_text(value)
                for value in row.tolist()
            ]

            positions = {}

            for target in [
                "kod",
                "popis",
                "mj",
                "mnozstvo"
            ]:

                if target in normalized_values:
                    positions[target] = (
                        normalized_values.index(
                            target
                        )
                    )

            if len(positions) == 4:
                header_row_index = int(
                    dataframe_index
                )
                header_columns = positions
                break

        if (
            header_row_index is None
            or header_columns is None
        ):
            continue

        for dataframe_index in range(
            header_row_index + 1,
            len(dataframe)
        ):

            row = dataframe.iloc[
                dataframe_index
            ]

            code = row.iloc[
                header_columns["kod"]
            ]

            description = row.iloc[
                header_columns["popis"]
            ]

            unit = row.iloc[
                header_columns["mj"]
            ]

            quantity_raw = row.iloc[
                header_columns["mnozstvo"]
            ]

            quantity = _to_number(
                quantity_raw
            )

            if quantity is None:
                continue

            if pd.isna(code) or pd.isna(
                description
            ) or pd.isna(unit):
                continue

            code = str(
                code
            ).strip()

            description = str(
                description
            ).strip()

            unit = str(
                unit
            ).strip()

            if (
                not code
                or not description
                or not unit
            ):
                continue

            items.append(
                {
                    "sheet": str(
                        sheet_name
                    ),
                    "row_number": (
                        int(
                            dataframe_index
                        )
                        + 1
                    ),
                    "code": code,
                    "description": description,
                    "unit": unit,
                    "quantity": quantity
                }
            )

    return items


def _extract_dn(description):
    text = _normalize_text(
        description
    )

    match = re.search(
        r"\bdn\s*([0-9]+)",
        text
    )

    if not match:
        return ""

    return (
        "DN"
        + match.group(1)
    )


def _extract_concrete_class(description):
    text = str(
        description
    )

    match = re.search(
        r"\bC\s*([0-9]+)\s*/\s*([0-9]+)\b",
        text,
        flags=re.IGNORECASE
    )

    if not match:
        return ""

    return (
        f"C{match.group(1)}/"
        f"{match.group(2)}"
    )


def _extract_thickness_mm(description):
    text = _normalize_text(
        description
    )

    match = re.search(
        r"\bhr\.?\s*([0-9]+(?:[.,][0-9]+)?)\s*mm\b",
        text
    )

    if not match:
        return None

    return float(
        match.group(1).replace(
            ",",
            "."
        )
    )


def _budget_group_info(item):
    """
    Deterministicky vytvorí group_key.

    Pri známych stavebných položkách zjednotí
    iba rozdiely, ktoré nemajú meniť KSP položku.
    Technicky rozdielne DN, materiály a triedy betónu
    zostávajú oddelené.
    """

    description = item[
        "description"
    ]

    unit = item[
        "unit"
    ]

    quantity = float(
        item["quantity"]
    )

    normalized_description = (
        _normalize_text(
            description
        )
    )

    normalized_code = (
        _normalize_code(
            item["code"]
        )
    )

    result = {
        "group_key": "",
        "item_name": description,
        "category": "praca",
        "unit": unit,
        "quantity": quantity,
        "dimension": "",
        "material": "",
        "original_quantity": quantity,
        "original_unit": unit
    }

    # ------------------------------------------------------
    # ZEMNÉ PRÁCE
    # ------------------------------------------------------

    if (
        "lozko pod potrubie" in normalized_description
        and (
            "piesku" in normalized_description
            or "strkopiesku" in normalized_description
        )
    ):
        result.update(
            {
                "group_key":
                    "lozko_pod_potrubie_piesok_strkopiesok",
                "item_name":
                    "Lôžko pod potrubie, stoky a drobné objekty – piesok / štrkopiesok",
                "material":
                    "piesok / štrkopiesok"
            }
        )

        return result

    if (
        normalized_description.startswith(
            "obsyp potrubia"
        )
    ):
        result.update(
            {
                "group_key":
                    "obsyp_potrubia_sypanina",
                "item_name":
                    "Obsyp potrubia sypaninou z vhodných hornín",
                "material":
                    "sypanina"
            }
        )

        return result

    if (
        normalized_description.startswith(
            "zasyp sypaninou so zhutnenim"
        )
    ):
        result.update(
            {
                "group_key":
                    "zasyp_sypaninou_so_zhutnenim",
                "item_name":
                    "Zásyp sypaninou so zhutnením",
                "material":
                    "sypanina"
            }
        )

        return result

    # ------------------------------------------------------
    # ARMOVANIE
    # ------------------------------------------------------

    if (
        "kari" in normalized_description
        and "8/8" in normalized_description
        and "150x150" in normalized_description.replace(
            " ",
            ""
        )
    ):
        result.update(
            {
                "group_key":
                    "kari_8_8_150x150",
                "item_name":
                    "Výstuž mazanín zo sietí KARI 8/8 mm, oko 150×150 mm",
                "material":
                    "oceľová KARI sieť",
                "dimension":
                    "8/8 mm; 150×150 mm"
            }
        )

        return result

    # ------------------------------------------------------
    # KOMUNIKÁCIE
    # ------------------------------------------------------

    if (
        normalized_description.startswith(
            "postrek asfaltovy spojovaci"
        )
    ):
        result.update(
            {
                "group_key":
                    "postrek_asfaltovy_spojovaci",
                "item_name":
                    "Postrek asfaltový spojovací bez posypu"
            }
        )

        return result

    if (
        "asfaltovy beton" in normalized_description
        and "ac 11 o" in normalized_description
    ):
        result.update(
            {
                "group_key":
                    "asfalt_ac11o_obrusna_60mm",
                "item_name":
                    "Asfaltová zmes AC 11 O, obrusná vrstva po zhutnení hr. 60 mm",
                "material":
                    "asfaltový betón AC 11 O",
                "dimension":
                    "60 mm"
            }
        )

        return result

    # Podkladový betón - rovnaký cenníkový kód môže mať
    # rôzne triedy betónu, preto rozhoduje aj popis.
    if (
        "podklad z podkladoveho betonu"
        in normalized_description
    ):
        concrete_class = (
            _extract_concrete_class(
                description
            )
        )

        thickness_mm = (
            _extract_thickness_mm(
                description
            )
        )

        group_key = (
            "podkladovy_beton_"
            + (
                concrete_class
                .lower()
                .replace("/", "_")
                if concrete_class
                else "bez_triedy"
            )
        )

        if thickness_mm is not None:
            group_key += (
                f"_{thickness_mm:g}mm"
            )

        result.update(
            {
                "group_key":
                    group_key,
                "item_name":
                    (
                        "Podkladový betón "
                        + (
                            concrete_class
                            if concrete_class
                            else ""
                        )
                        + (
                            f", hr. {thickness_mm:g} mm"
                            if thickness_mm is not None
                            else ""
                        )
                    ).strip(
                        ", "
                    ),
                "material":
                    concrete_class,
                "dimension":
                    (
                        f"{thickness_mm:g} mm"
                        if thickness_mm is not None
                        else ""
                    )
            }
        )

        # Pre KSP podkladový betón vyjadrujeme objemom,
        # ak rozpočet uvádza plochu a hrúbku.
        if (
            _normalize_text(
                unit
            ) == "m2"
            and thickness_mm is not None
        ):
            result[
                "quantity"
            ] = (
                quantity
                * thickness_mm
                / 1000.0
            )

            result[
                "unit"
            ] = "m3"

        return result

    # ------------------------------------------------------
    # POTRUBIA
    # ------------------------------------------------------

    if (
        "potrubie kanalizacne pvc-u"
        in normalized_description
        and "grav" in normalized_description
    ):
        dn = _extract_dn(
            description
        )

        result.update(
            {
                "group_key":
                    (
                        "potrubie_pvcu_gravitacne_"
                        + (
                            dn.lower()
                            if dn
                            else normalized_code
                        )
                    ),
                "item_name":
                    (
                        "Gravitačné kanalizačné potrubie PVC-U "
                        + dn
                    ).strip(),
                "material":
                    "PVC-U",
                "dimension":
                    dn
            }
        )

        return result

    if (
        (
            "pe100" in normalized_description
            or "hdpe" in normalized_description
        )
        and "potrub" in normalized_description
    ):
        dn = _extract_dn(
            description
        )

        result.update(
            {
                "group_key":
                    (
                        "potrubie_hdpe_pe100_"
                        + (
                            dn.lower()
                            if dn
                            else normalized_code
                        )
                    ),
                "item_name":
                    (
                        "Výtlačné potrubie HDPE PE100 "
                        + dn
                    ).strip(),
                "material":
                    "HDPE PE100",
                "dimension":
                    dn
            }
        )

        return result

    # ------------------------------------------------------
    # DEFAULT - PRESNÁ TECHNICKÁ POLOŽKA
    # ------------------------------------------------------

    # Tu zámerne kombinujeme normalizovaný kód AJ popis.
    # Rovnaký kód s rozdielnou triedou/materiálom sa nespojí.
    technical_description = re.sub(
        r"\s+",
        "_",
        normalized_description
    )

    technical_description = re.sub(
        r"[^a-z0-9_/-]",
        "",
        technical_description
    )

    technical_description = (
        technical_description[:120]
    )

    result[
        "group_key"
    ] = (
        f"{normalized_code}__"
        f"{technical_description}"
    )

    return result


def aggregate_budget_items_python(items):
    """
    Sčíta položky, ktoré boli deterministicky
    zaradené cez _budget_group_info().

    Žiadne AI volanie.
    """

    grouped = {}

    for item in items:

        group_info = (
            _budget_group_info(
                item
            )
        )

        group_key = (
            group_info[
                "group_key"
            ]
        )

        unit = group_info[
            "unit"
        ]

        key = (
            group_key,
            _normalize_text(
                unit
            )
        )

        if key not in grouped:

            grouped[key] = {
                "group_key":
                    group_key,
                "item_name":
                    group_info[
                        "item_name"
                    ],
                "category":
                    group_info[
                        "category"
                    ],
                "unit":
                    unit,
                "quantity":
                    0.0,
                "dimension":
                    group_info[
                        "dimension"
                    ],
                "material":
                    group_info[
                        "material"
                    ],
                "source_rows":
                    []
            }

        grouped[key][
            "quantity"
        ] += float(
            group_info[
                "quantity"
            ]
        )

        grouped[key][
            "source_rows"
        ].append(
            {
                "sheet":
                    item[
                        "sheet"
                    ],
                "row_number":
                    item[
                        "row_number"
                    ],
                "code":
                    item[
                        "code"
                    ],
                "description":
                    item[
                        "description"
                    ],
                "original_quantity":
                    item[
                        "quantity"
                    ],
                "original_unit":
                    item[
                        "unit"
                    ]
            }
        )

    result = list(
        grouped.values()
    )

    result.sort(
        key=lambda item: (
            str(
                item.get(
                    "source_rows",
                    [{}]
                )[0].get(
                    "sheet",
                    ""
                )
            ),
            int(
                item.get(
                    "source_rows",
                    [{}]
                )[0].get(
                    "row_number",
                    999999
                )
            )
        )
    )

    # Zaokrúhlenie iba na odstránenie floating-point šumu.
    for item in result:
        item["quantity"] = round(
            float(
                item["quantity"]
            ),
            6
        )

    return result


def process_budget_python(file_bytes):
    """
    Hlavná funkcia prvého kroku.

    1. prečíta všetky detailné hárky,
    2. nájde Kód/Popis/MJ/Množstvo,
    3. zoskupí položky,
    4. presne sčíta množstvá.

    NEVOLÁ OPENAI API.
    """

    items = extract_budget_items_python(
        file_bytes
    )

    return aggregate_budget_items_python(
        items
    )


def merge_aggregated_budget_rows(
    aggregated_lists
):
    """
    Ak je v projekte viac rozpočtových Excelov,
    spojí už spočítané výsledky bez AI.
    """

    grouped = {}

    for aggregated_rows in aggregated_lists:

        for item in aggregated_rows:

            key = (
                str(
                    item.get(
                        "group_key",
                        ""
                    )
                ),
                _normalize_text(
                    item.get(
                        "unit",
                        ""
                    )
                )
            )

            if key not in grouped:
                grouped[key] = {
                    "group_key":
                        item.get(
                            "group_key",
                            ""
                        ),
                    "item_name":
                        item.get(
                            "item_name",
                            ""
                        ),
                    "category":
                        item.get(
                            "category",
                            ""
                        ),
                    "unit":
                        item.get(
                            "unit",
                            ""
                        ),
                    "quantity":
                        0.0,
                    "dimension":
                        item.get(
                            "dimension",
                            ""
                        ),
                    "material":
                        item.get(
                            "material",
                            ""
                        ),
                    "source_rows":
                        []
                }

            grouped[key][
                "quantity"
            ] += float(
                item.get(
                    "quantity",
                    0
                )
                or 0
            )

            grouped[key][
                "source_rows"
            ].extend(
                item.get(
                    "source_rows",
                    []
                )
            )

    result = list(
        grouped.values()
    )

    for item in result:
        item["quantity"] = round(
            item["quantity"],
            6
        )

    return result


# ==========================================================
# STARŠIA AI AGREGÁCIA - PONECHANÁ PRE KOMPATIBILITU
# ==========================================================

def aggregate_budget_rows(classified_rows):
    """
    Ponechané len kvôli spätnej kompatibilite.
    Nový project_detail.py túto funkciu na prvý krok
    už nepoužíva.
    """

    if not isinstance(
        classified_rows,
        list
    ):
        return []

    grouped = {}
    standalone = []

    for item in classified_rows:

        if not isinstance(
            item,
            dict
        ):
            continue

        include = item.get(
            "include",
            False
        )

        if isinstance(
            include,
            str
        ):
            include = (
                include.strip().lower()
                in {
                    "true",
                    "1",
                    "yes",
                    "áno",
                    "ano"
                }
            )

        if not include:
            continue

        group_key = str(
            item.get(
                "group_key",
                ""
            )
            or ""
        ).strip()

        unit = str(
            item.get(
                "unit",
                ""
            )
            or ""
        ).strip()

        quantity = item.get(
            "quantity"
        )

        source_row = {
            "sheet":
                item.get(
                    "sheet",
                    ""
                ),
            "row_number":
                item.get(
                    "row_number",
                    ""
                )
        }

        is_number = (
            isinstance(
                quantity,
                (int, float)
            )
            and not isinstance(
                quantity,
                bool
            )
        )

        if (
            group_key
            and is_number
        ):

            key = (
                group_key,
                unit.lower()
            )

            if key not in grouped:

                grouped[key] = {
                    "group_key":
                        group_key,
                    "item_name":
                        item.get(
                            "item_name",
                            ""
                        ),
                    "category":
                        item.get(
                            "category",
                            ""
                        ),
                    "unit":
                        unit,
                    "quantity":
                        0.0,
                    "dimension":
                        item.get(
                            "dimension",
                            ""
                        ),
                    "material":
                        item.get(
                            "material",
                            ""
                        ),
                    "source_rows":
                        []
                }

            grouped[key][
                "quantity"
            ] += float(
                quantity
            )

            grouped[key][
                "source_rows"
            ].append(
                source_row
            )

        else:

            standalone.append(
                {
                    "group_key":
                        group_key,
                    "item_name":
                        item.get(
                            "item_name",
                            ""
                        ),
                    "category":
                        item.get(
                            "category",
                            ""
                        ),
                    "unit":
                        unit,
                    "quantity":
                        quantity,
                    "dimension":
                        item.get(
                            "dimension",
                            ""
                        ),
                    "material":
                        item.get(
                            "material",
                            ""
                        ),
                    "source_rows":
                        [
                            source_row
                        ]
                }
            )

    return (
        list(
            grouped.values()
        )
        + standalone
    )


# ==========================================================
# HLAVNÝ DISPEČER
# ==========================================================

def extract_text_from_file(arg1, arg2):
    """
    Podporuje obe poradia argumentov:
    extract_text_from_file(file_bytes, file_name)
    aj
    extract_text_from_file(file_name, file_bytes)
    """

    if isinstance(
        arg1,
        (bytes, bytearray)
    ):
        file_bytes = arg1
        file_name = arg2
    else:
        file_name = arg1
        file_bytes = arg2

    extension = (
        str(
            file_name
        )
        .lower()
        .split(".")[-1]
    )

    if extension == "pdf":
        return extract_text_from_pdf(
            file_bytes
        )

    if extension == "docx":
        return extract_text_from_docx(
            file_bytes
        )

    if extension in [
        "xlsx",
        "xls"
    ]:
        return extract_text_from_excel(
            file_bytes
        )

    if extension == "doc":
        raise ValueError(
            "Starý formát .doc nie je možné "
            "spoľahlivo čítať cez python-docx. "
            "Ulož dokument ako .docx."
        )

    raise ValueError(
        f"Nepodporovaný typ súboru: "
        f"{file_name}"
    )
