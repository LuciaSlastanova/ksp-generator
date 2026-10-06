import io
import re
import math
import unicodedata
from collections import Counter
from difflib import SequenceMatcher

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

    text = text.replace("×", "x")
    text = text.replace("–", "-")
    text = text.replace("—", "-")

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


def _normalize_code(value):
    """
    Zjednotí napr.:
    631362442.S
    631362442.s
    631362442
    """

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
        if isinstance(
            value,
            float
        ) and math.isnan(value):
            return None

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


def _normalize_unit(value):
    text = _normalize_text(
        value
    )

    unit_map = {
        "m²": "m2",
        "m2": "m2",

        "m³": "m3",
        "m3": "m3",

        "ks": "ks",
        "kus": "ks",
        "kusy": "ks",

        "kompl": "kompl",
        "komplet": "kompl",

        "súbor": "subor",
        "subor": "subor",

        "t": "t",
        "kg": "kg",
        "m": "m",
        "l": "l",
        "hod": "hod",
    }

    return unit_map.get(
        text,
        text
    )


def _cell_text(value):
    if value is None:
        return ""

    if pd.isna(value):
        return ""

    return str(
        value
    ).strip()


# ==========================================================
# IDENTIFIKÁCIA PROJEKTU / FILTROVANIE CUDZÍCH HÁRKOV
# ==========================================================

_PROJECT_LABELS = {
    "stavba",
    "nazov stavby",
    "názov stavby",
    "akcia",
    "nazov akcie",
    "názov akcie",
}


_PROJECT_GENERIC_WORDS = {
    "stavba",
    "nazov",
    "akcia",
    "projekt",
    "projektova",
    "projektovej",
    "dokumentacia",
    "realizacia",
    "zmena",
    "dodatok",
    "dod",
    "komplet",

    "kanalizacia",
    "kanalizacna",
    "kanalizacne",
    "splaskova",
    "stokova",
    "siet",
    "siete",

    "cs",
    "cerpacia",
    "cerpacej",
    "stanica",
    "stanice",

    "vodovod",
    "vodovodna",
    "pripojka",
    "pripojky",

    "vytlak",
    "vytlacne",
    "potrubie",

    "odvedenie",
    "odpadovych",
    "vod",

    "etapa",
    "dokoncienie",
    "dokonceni",

    "objekt",
    "stavebny",
    "so",
    "cast",

    "rekonstrukcia",
    "rekonstrukcie",
    "budovanie",
    "vystavba",
    "realizacny",
}


def _project_tokens(value):
    """
    Z názvu projektu vyberie výrazné tokeny.

    Napríklad:

    Abrahám - splašková kanalizácia a ČS,
    zmena č. 2

    -> {"abraham"}

    Všeobecné slová ako kanalizácia,
    ČS, stavba, zmena atď. ignorujeme.
    """

    text = _normalize_text(
        value
    )

    words = re.findall(
        r"[a-z0-9]+",
        text
    )

    tokens = []

    for word in words:

        if len(word) < 3:
            continue

        if word.isdigit():
            continue

        if word in _PROJECT_GENERIC_WORDS:
            continue

        tokens.append(
            word
        )

    return set(
        tokens
    )


def _extract_project_labels_from_sheet(
    dataframe,
    max_rows=45,
    max_cols=14
):
    """
    Hľadá názov stavby iba v hornej časti hárku.

    Podporuje napr.:

    Stavba | Abrahám - splašková kanalizácia

    Stavba: Abrahám - splašková kanalizácia

    Názov stavby | ...
    """

    found = []

    row_limit = min(
        len(dataframe),
        max_rows
    )

    col_limit = min(
        len(dataframe.columns),
        max_cols
    )

    normalized_project_labels = {
        _normalize_text(label)
        for label in _PROJECT_LABELS
    }

    for row_index in range(
        row_limit
    ):

        raw_values = [
            _cell_text(
                dataframe.iloc[
                    row_index,
                    col_index
                ]
            )
            for col_index in range(
                col_limit
            )
        ]

        normalized_values = [
            _normalize_text(value)
            for value in raw_values
        ]

        for col_index, normalized in enumerate(
            normalized_values
        ):

            if not normalized:
                continue

            same_cell_match = re.match(
                (
                    r"^(stavba|nazov stavby|akcia|nazov akcie)"
                    r"\s*[:\-]\s*(.+)$"
                ),
                normalized,
                flags=re.IGNORECASE
            )

            if same_cell_match:

                value = (
                    same_cell_match
                    .group(2)
                    .strip()
                )

                if value:
                    found.append(
                        value
                    )

                continue

            if normalized in normalized_project_labels:

                for next_col in range(
                    col_index + 1,
                    col_limit
                ):

                    candidate = (
                        raw_values[
                            next_col
                        ]
                        .strip()
                    )

                    if candidate:
                        found.append(
                            candidate
                        )
                        break

    unique = []
    seen = set()

    for value in found:

        normalized = (
            _normalize_text(
                value
            )
        )

        if (
            normalized
            and normalized not in seen
        ):
            seen.add(
                normalized
            )

            unique.append(
                value
            )

    return unique


def _detect_primary_project_tokens(
    sheets,
    project_hint=None
):
    """
    Určí hlavný projekt workbooku.
    """

    if project_hint:

        hint_tokens = (
            _project_tokens(
                project_hint
            )
        )

        if hint_tokens:
            return hint_tokens

    counter = Counter()

    sheets_with_project_label = 0

    for dataframe in sheets.values():

        labels = (
            _extract_project_labels_from_sheet(
                dataframe
            )
        )

        if not labels:
            continue

        sheets_with_project_label += 1

        sheet_tokens = set()

        for label in labels:

            sheet_tokens.update(
                _project_tokens(
                    label
                )
            )

        for token in sheet_tokens:

            counter[
                token
            ] += 1

    if not counter:
        return set()

    ranked = (
        counter.most_common()
    )

    top_token, top_count = (
        ranked[0]
    )

    second_count = (
        ranked[1][1]
        if len(ranked) > 1
        else 0
    )

    if top_count < 2:
        return set()

    if top_count == second_count:
        return set()

    if sheets_with_project_label < 2:
        return set()

    return {
        top_token
    }


def _sheet_project_status(
    dataframe,
    primary_project_tokens
):
    """
    Výstup:
    relevant / foreign / unknown
    """

    labels = (
        _extract_project_labels_from_sheet(
            dataframe
        )
    )

    if (
        not labels
        or not primary_project_tokens
    ):
        return (
            "unknown",
            labels
        )

    tokens = set()

    for label in labels:

        tokens.update(
            _project_tokens(
                label
            )
        )

    if not tokens:
        return (
            "unknown",
            labels
        )

    if tokens.intersection(
        primary_project_tokens
    ):
        return (
            "relevant",
            labels
        )

    return (
        "foreign",
        labels
    )


def inspect_budget_sheets_python(
    file_bytes,
    project_hint=None
):
    """
    Diagnostická funkcia.
    """

    sheets = pd.read_excel(
        io.BytesIO(
            file_bytes
        ),
        sheet_name=None,
        header=None,
        dtype=object
    )

    primary_tokens = (
        _detect_primary_project_tokens(
            sheets,
            project_hint=project_hint
        )
    )

    result = []

    for sheet_name, dataframe in sheets.items():

        normalized_sheet_name = (
            _normalize_text(
                sheet_name
            )
        )

        if "rekapitul" in normalized_sheet_name:

            result.append(
                {
                    "sheet":
                        str(
                            sheet_name
                        ),

                    "status":
                        "skip_recap",

                    "project_labels":
                        []
                }
            )

            continue

        status, labels = (
            _sheet_project_status(
                dataframe,
                primary_tokens
            )
        )

        result.append(
            {
                "sheet":
                    str(
                        sheet_name
                    ),

                "status":
                    status,

                "project_labels":
                    labels
            }
        )

    return {
        "primary_project_tokens":
            sorted(
                primary_tokens
            ),

        "sheets":
            result
    }


# ==========================================================
# ČÍTANIE PDF / DOCX / EXCEL
# ==========================================================

def extract_text_from_pdf(
    file_bytes
):
    try:
        from pypdf import PdfReader

    except ImportError:
        from PyPDF2 import PdfReader

    reader = PdfReader(
        io.BytesIO(
            file_bytes
        )
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


def extract_text_from_docx(
    file_bytes
):
    from docx import Document

    document = Document(
        io.BytesIO(
            file_bytes
        )
    )

    parts = []

    for paragraph in document.paragraphs:

        text = (
            paragraph.text
            .strip()
        )

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

            if any(
                values
            ):
                parts.append(
                    " | ".join(
                        values
                    )
                )

    return "\n".join(
        parts
    )


def extract_excel_rows(
    file_bytes
):
    sheets = pd.read_excel(
        io.BytesIO(
            file_bytes
        ),
        sheet_name=None,
        header=None,
        dtype=object
    )

    result = []

    for sheet_name, dataframe in sheets.items():

        for dataframe_index, row in dataframe.iterrows():

            values = []

            for value in row.tolist():

                if pd.isna(
                    value
                ):
                    values.append(
                        ""
                    )

                else:
                    values.append(
                        str(
                            value
                        ).strip()
                    )

            if not any(
                value != ""
                for value in values
            ):
                continue

            result.append(
                {
                    "sheet":
                        str(
                            sheet_name
                        ),

                    "row_number":
                        int(
                            dataframe_index
                        )
                        + 1,

                    "values":
                        values
                }
            )

    return result


def extract_text_from_excel(
    file_bytes
):
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

            current_sheet = (
                sheet
            )

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
# KATEGORIZÁCIA POLOŽIEK
# ==========================================================

def _infer_budget_category(
    description
):
    text = (
        _normalize_text(
            description
        )
    )

    if any(
        token in text
        for token in [
            "skuska",
            "meranie",
            "revizia",
            "prehliadka",
            "monitoring",
            "kamerov",
            "tlakova skuska",
            "tesnost",
        ]
    ):
        return "skuska"

    if any(
        token in text
        for token in [
            "montaz",
            "osadenie",
            "ulozenie",
            "zriadenie",
        ]
    ):
        return "montaz"

    if any(
        token in text
        for token in [
            "dodavka",
            "material",
            "piesok",
            "strkodrv",
            "strkopiesok",
            "kamenivo",
            "poklop",
            "skruz",
            "sachtove dno",
            "rura",
            "potrubie",
            "kabel",
            "pas fezn",
            "kari siet",
            "vystuz",
        ]
    ):

        work_tokens = [
            "obsyp",
            "zasyp",
            "vykop",
            "hlbenie",
            "hutnenie",
            "betonaz",
            "zhotovenie",
            "rezanie",
            "buranie",
        ]

        if not any(
            token in text
            for token in work_tokens
        ):
            return "material"

    return "praca"


# ==========================================================
# 1. VŠEOBECNÉ NAČÍTANIE ROZPOČTU
# ==========================================================

def extract_budget_items_python(
    file_bytes,
    project_hint=None,
    include_unknown_sheets=True
):
    """
    V každom hárku hľadá tabuľku:
    Kód | Popis | MJ | Množstvo

    NEVOLÁ AI.
    """

    sheets = pd.read_excel(
        io.BytesIO(
            file_bytes
        ),
        sheet_name=None,
        header=None,
        dtype=object
    )

    primary_project_tokens = (
        _detect_primary_project_tokens(
            sheets,
            project_hint=project_hint
        )
    )

    items = []

    aliases = {
        "kod": {
            "kod",
            "kód"
        },

        "popis": {
            "popis",
            "nazov",
            "názov",
            "popis polozky",
            "nazov polozky"
        },

        "mj": {
            "mj",
            "m.j.",
            "merna jednotka",
            "merná jednotka"
        },

        "mnozstvo": {
            "mnozstvo",
            "množstvo"
        }
    }

    normalized_aliases = {
        key: {
            _normalize_text(
                value
            )
            for value in values
        }
        for key, values
        in aliases.items()
    }

    for sheet_name, dataframe in sheets.items():

        normalized_sheet_name = (
            _normalize_text(
                sheet_name
            )
        )

        if "rekapitul" in normalized_sheet_name:
            continue

        project_status, project_labels = (
            _sheet_project_status(
                dataframe,
                primary_project_tokens
            )
        )

        if (
            project_status == "unknown"
            and not include_unknown_sheets
        ):
            continue

        header_row_index = None
        header_columns = None

        for dataframe_index, row in dataframe.iterrows():

            normalized_values = [
                _normalize_text(
                    value
                )
                for value
                in row.tolist()
            ]

            positions = {}

            for target, accepted in normalized_aliases.items():

                for index, cell_text in enumerate(
                    normalized_values
                ):

                    if cell_text in accepted:

                        positions[
                            target
                        ] = index

                        break

            if len(
                positions
            ) == 4:

                header_row_index = int(
                    dataframe_index
                )

                header_columns = (
                    positions
                )

                break

        if (
            header_row_index is None
            or header_columns is None
        ):
            continue

        for dataframe_index in range(
            header_row_index + 1,
            len(
                dataframe
            )
        ):

            row = dataframe.iloc[
                dataframe_index
            ]

            code = row.iloc[
                header_columns[
                    "kod"
                ]
            ]

            description = row.iloc[
                header_columns[
                    "popis"
                ]
            ]

            unit = row.iloc[
                header_columns[
                    "mj"
                ]
            ]

            quantity_raw = row.iloc[
                header_columns[
                    "mnozstvo"
                ]
            ]

            quantity = _to_number(
                quantity_raw
            )

            if quantity is None:
                continue

            if (
                pd.isna(
                    description
                )
                or pd.isna(
                    unit
                )
            ):
                continue

            description = str(
                description
            ).strip()

            unit = str(
                unit
            ).strip()

            if pd.isna(
                code
            ):
                code = ""

            else:
                code = str(
                    code
                ).strip()

            if (
                not description
                or not unit
            ):
                continue

            normalized_description = (
                _normalize_text(
                    description
                )
            )

            if any(
                token in normalized_description
                for token in [
                    "medzisucet",
                    "sucet",
                    "spolu",
                    "rekapitulacia",
                    "dph",
                ]
            ):
                continue

            items.append(
                {
                    "sheet":
                        str(
                            sheet_name
                        ),

                    "row_number":
                        int(
                            dataframe_index
                        )
                        + 1,

                    "code":
                        code,

                    "description":
                        description,

                    "unit":
                        _normalize_unit(
                            unit
                        ),

                    "quantity":
                        quantity,

                    "category":
                        _infer_budget_category(
                            description
                        ),

                    "sheet_project_status":
                        project_status,

                    "sheet_project_labels":
                        project_labels,

                    "warnings":
                        []
                }
            )

    _attach_suspicious_quantity_warnings(
        items
    )

    return items


# ==========================================================
# KONTROLA PODOZRIVÝCH MNOŽSTIEV
# ==========================================================

def _is_obsyp_work(
    item
):
    text = _normalize_text(
        item.get(
            "description",
            ""
        )
    )

    return (
        "obsyp" in text
        and "potrub" in text
        and "dodavka" not in text
        and item.get(
            "category"
        ) != "material"
    )


def _is_obsyp_material(
    item
):
    text = _normalize_text(
        item.get(
            "description",
            ""
        )
    )

    return (
        "obsyp" in text
        and any(
            token in text
            for token in [
                "piesok",
                "strkopiesok",
                "kamenivo",
            ]
        )
        and (
            "dodavka" in text
            or item.get(
                "category"
            ) == "material"
        )
    )


def _is_zasyp_work(
    item
):
    text = _normalize_text(
        item.get(
            "description",
            ""
        )
    )

    return (
        "zasyp" in text
        and "obsyp" not in text
        and item.get(
            "category"
        ) != "material"
    )


def _append_item_warning(
    item,
    message
):
    warnings = item.setdefault(
        "warnings",
        []
    )

    if message not in warnings:

        warnings.append(
            message
        )


def _attach_suspicious_quantity_warnings(
    items
):
    by_sheet = {}

    for item in items:

        by_sheet.setdefault(
            item.get(
                "sheet",
                ""
            ),
            []
        ).append(
            item
        )

    for sheet_name, sheet_items in by_sheet.items():

        obsyp_work = [
            item
            for item in sheet_items
            if _is_obsyp_work(
                item
            )
        ]

        obsyp_material = [
            item
            for item in sheet_items
            if _is_obsyp_material(
                item
            )
        ]

        zasyp_work = [
            item
            for item in sheet_items
            if _is_zasyp_work(
                item
            )
        ]

        if (
            not obsyp_work
            or not obsyp_material
        ):
            continue

        obsyp_work_total = sum(
            float(
                item.get(
                    "quantity",
                    0
                )
                or 0
            )
            for item in obsyp_work
        )

        obsyp_material_total = sum(
            float(
                item.get(
                    "quantity",
                    0
                )
                or 0
            )
            for item in obsyp_material
        )

        zasyp_total = sum(
            float(
                item.get(
                    "quantity",
                    0
                )
                or 0
            )
            for item in zasyp_work
        )

        if (
            obsyp_work_total <= 0
            or obsyp_material_total <= 0
        ):
            continue

        ratio = (
            obsyp_material_total
            /
            obsyp_work_total
        )

        if (
            ratio < 0.75
            or ratio > 1.25
        ):

            message = (
                f"PODOZRIVÉ MNOŽSTVO na hárku "
                f"{sheet_name}: "
                f"materiál na obsyp = "
                f"{round(obsyp_material_total, 3)} m3, "
                f"obsyp potrubia = "
                f"{round(obsyp_work_total, 3)} m3. "
                f"Skontrolovať CP; "
                f"automaticky sa neopravuje."
            )

            for item in (
                obsyp_work
                + obsyp_material
            ):

                _append_item_warning(
                    item,
                    message
                )

        if (
            zasyp_total > 0
            and abs(
                obsyp_material_total
                -
                zasyp_total
            )
            <= max(
                0.01,
                abs(
                    zasyp_total
                ) * 0.005
            )
            and abs(
                obsyp_material_total
                -
                obsyp_work_total
            )
            >
            max(
                0.01,
                abs(
                    obsyp_work_total
                ) * 0.25
            )
        ):

            message = (
                f"MOŽNÉ KOPÍROVANIE MNOŽSTVA "
                f"na hárku {sheet_name}: "
                f"materiál na obsyp "
                f"({round(obsyp_material_total, 3)} m3) "
                f"sa zhoduje so zásypom "
                f"({round(zasyp_total, 3)} m3), "
                f"ale nie s obsypom "
                f"({round(obsyp_work_total, 3)} m3)."
            )

            for item in obsyp_material:

                _append_item_warning(
                    item,
                    message
                )


# ==========================================================
# 2. TECHNICKÝ PODPIS POLOŽKY
# ==========================================================

def _remove_pricing_bands(
    text
):
    """
    Odstraňuje iba typické cenové pásma,
    ktoré nemenia technický význam práce.
    """

    result = (
        _normalize_text(
            text
        )
    )

    patterns = [

        (
            r"\bnad\s+\d+(?:[.,]\d+)?"
            r"\s+do\s+\d+(?:[.,]\d+)?"
            r"\s*(?:m3|m2|m|t|kg|ks)\b"
        ),

        (
            r"\bod\s+\d+(?:[.,]\d+)?"
            r"\s+do\s+\d+(?:[.,]\d+)?"
            r"\s*(?:m3|m2|m|t|kg|ks)\b"
        ),

        (
            r"\bdo\s+\d+(?:[.,]\d+)?"
            r"\s*(?:m3|m2|t|kg|ks)\b"
        ),

        (
            r"\bnad\s+\d+(?:[.,]\d+)?"
            r"\s*(?:m3|m2|t|kg|ks)\b"
        ),

        (
            r"\bna vzdialenost do\s+"
            r"\d+(?:[.,]\d+)?\s*m\b"
        ),

        (
            r"\bna vzdialenost nad\s+"
            r"\d+(?:[.,]\d+)?"
            r"\s+do\s+"
            r"\d+(?:[.,]\d+)?"
            r"\s*m\b"
        ),

        (
            r"\bza kazdych dalsich "
            r"a zacatych\s+"
            r"\d+(?:[.,]\d+)?"
            r"\s*m\b"
        ),

        (
            r"\bplochy do\s+"
            r"\d+(?:[.,]\d+)?"
            r"\s*m2\b"
        ),

        (
            r"\bplochy nad\s+"
            r"\d+(?:[.,]\d+)?"
            r"\s+do\s+"
            r"\d+(?:[.,]\d+)?"
            r"\s*m2\b"
        ),
    ]

    for pattern in patterns:

        result = re.sub(
            pattern,
            "",
            result,
            flags=re.IGNORECASE
        )

    result = re.sub(
        r"\s+",
        " ",
        result
    ).strip(
        " ,;-"
    )

    return result


def _extract_critical_parameters(
    description
):
    """
    Všeobecný technický podpis.
    """

    text = (
        _normalize_text(
            description
        )
    )

    parameters = []

    regexes = [

        (
            "dn",
            r"\bdn\s*([0-9]+)\b"
        ),

        (
            "sn",
            r"\bsn\s*([0-9]+)\b"
        ),

        (
            "pn",
            (
                r"\bpn\s*"
                r"([0-9]+(?:[.,][0-9]+)?)\b"
            )
        ),

        (
            "beton",
            (
                r"\bc\s*"
                r"([0-9]+)"
                r"\s*/\s*"
                r"([0-9]+)\b"
            )
        ),

        (
            "hr",
            (
                r"\bhr\.?\s*"
                r"([0-9]+(?:[.,][0-9]+)?)"
                r"\s*(mm|cm|m)\b"
            )
        ),

        (
            "priemer",
            (
                r"\bpriemer(?:u)?\s*"
                r"([0-9]+(?:[.,][0-9]+)?)"
                r"\s*(mm|cm|m)?\b"
            )
        ),

        (
            "rozmer",
            (
                r"\b("
                r"[0-9]+(?:[.,][0-9]+)?"
                r"x"
                r"[0-9]+(?:[.,][0-9]+)?"
                r"(?:x"
                r"[0-9]+(?:[.,][0-9]+)?"
                r")?"
                r")"
                r"\s*(mm|cm|m)?\b"
            )
        ),

        (
            "xc",
            (
                r"\b("
                r"xc[0-9]+"
                r"|xf[0-9]+"
                r"|xd[0-9]+"
                r"|xa[0-9]+"
                r")\b"
            )
        ),
    ]

    for name, pattern in regexes:

        for match in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE
        ):

            value = "|".join(
                part
                for part
                in match.groups()
                if part is not None
            )

            parameters.append(
                f"{name}:{value}"
            )

    material_tokens = [
        "pvc-u",
        "pvc",
        "hdpe",
        "pe100",
        "pe80",
        "pp",
        "beton",
        "zelezo",
        "ocel",
        "nerez",
        "kari",
        "eps",
        "xps",
        "mineralna vlna",
        "sklenena vlna",
        "tehla",
        "porotherm",
        "ytong",
        "sadrokarton",
        "asfalt",
        "strkopiesok",
        "piesok",
        "kamenivo",
        "makadam",
        "drevo",
        "hlinik",
        "med",
    ]

    for token in material_tokens:

        if token in text:

            parameters.append(
                f"mat:{token}"
            )

    return tuple(
        sorted(
            set(
                parameters
            )
        )
    )


def _remove_ksp_irrelevant_classifiers(
    text
):
    """
    Odstráni klasifikátory,
    ktoré menia cenu,
    ale obvykle nemenia KSP kontrolu.
    """

    result = (
        _normalize_text(
            text
        )
    )

    is_earth_excavation = any(
        token in result
        for token in [
            "vykop",
            "hlbenie",
            "hlbenia",
            "ryhy",
            "jamy",
            "jám",
            "zarezov",
        ]
    )

    if not is_earth_excavation:
        return result

    patterns = [
        r"\bhorn\.?\s*\d+\b",
        r"\bhor\s*\d+\b",

        (
            r"\bhornina\s*"
            r"(?:tr\.?|triedy)?"
            r"\s*\d+\b"
        ),

        (
            r"\bhornine\s*"
            r"(?:tr\.?|triedy)?"
            r"\s*\d+\b"
        ),

        (
            r"\bz\s*horniny\s*"
            r"(?:tr\.?|triedy)?"
            r"\s*\d+\b"
        ),

        (
            r"\bv\s*hornine\s*"
            r"(?:tr\.?|triedy)?"
            r"\s*\d+\b"
        ),
    ]

    for pattern in patterns:

        result = re.sub(
            pattern,
            "",
            result,
            flags=re.IGNORECASE
        )

    result = re.sub(
        r"\s+",
        " ",
        result
    ).strip(
        " ,;-"
    )

    return result


def _description_signature(
    description
):
    """
    Vráti všeobecný technický podpis položky.
    """

    text = (
        _remove_pricing_bands(
            description
        )
    )

    text = (
        _remove_ksp_irrelevant_classifiers(
            text
        )
    )

    text = re.sub(
        r"[(),.;:]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


def _description_similarity(
    first,
    second
):
    return SequenceMatcher(
        None,
        _description_signature(
            first
        ),
        _description_signature(
            second
        )
    ).ratio()


def _can_group_items(
    first,
    second
):
    """
    Konzervatívne zoskupovanie.

    Všeobecné pravidlo:
    ak obe položky majú kód a kódy sú rozdielne,
    NESMÚ sa automaticky zlúčiť.
    """

    if (
        _normalize_unit(
            first[
                "unit"
            ]
        )
        !=
        _normalize_unit(
            second[
                "unit"
            ]
        )
    ):
        return False

    first_category = (
        first.get(
            "category"
        )
        or
        _infer_budget_category(
            first[
                "description"
            ]
        )
    )

    second_category = (
        second.get(
            "category"
        )
        or
        _infer_budget_category(
            second[
                "description"
            ]
        )
    )

    if (
        first_category
        != second_category
    ):
        return False

    first_params = (
        _extract_critical_parameters(
            first[
                "description"
            ]
        )
    )

    second_params = (
        _extract_critical_parameters(
            second[
                "description"
            ]
        )
    )

    if (
        first_params
        and second_params
        and first_params != second_params
    ):
        return False

    first_code = (
        _normalize_code(
            first.get(
                "code",
                ""
            )
        )
    )

    second_code = (
        _normalize_code(
            second.get(
                "code",
                ""
            )
        )
    )

    # ------------------------------------------------------
    # KĽÚČOVÁ VŠEOBECNÁ OPRAVA
    # ------------------------------------------------------

    if (
        first_code
        and second_code
        and first_code != second_code
    ):
        return False

    first_signature = (
        _description_signature(
            first[
                "description"
            ]
        )
    )

    second_signature = (
        _description_signature(
            second[
                "description"
            ]
        )
    )

    if (
        first_code
        and second_code
        and first_code == second_code
        and first_signature == second_signature
    ):
        return True

    similarity = (
        _description_similarity(
            first[
                "description"
            ],
            second[
                "description"
            ]
        )
    )

    if (
        first_code
        and second_code
        and first_code == second_code
        and similarity >= 0.78
    ):
        return True

    if (
        not first_code
        or not second_code
    ):

        if first_signature == second_signature:
            return True

        if similarity >= 0.94:
            return True

    return False


# ==========================================================
# 3. VŠEOBECNÉ ZOSKUPOVANIE
# ==========================================================

def _make_generic_group_key(
    representative
):
    signature = (
        _description_signature(
            representative[
                "description"
            ]
        )
    )

    params = (
        _extract_critical_parameters(
            representative[
                "description"
            ]
        )
    )

    safe_signature = re.sub(
        r"[^a-z0-9]+",
        "_",
        signature
    ).strip(
        "_"
    )

    if len(
        safe_signature
    ) > 90:

        safe_signature = (
            safe_signature[
                :90
            ]
        )

    param_text = "_".join(
        re.sub(
            r"[^a-z0-9]+",
            "_",
            param
        ).strip(
            "_"
        )
        for param in params
    )

    if param_text:

        return (
            safe_signature
            + "__"
            + param_text
        )

    return safe_signature


def _convert_quantity_for_ksp(
    description,
    unit,
    quantity
):
    """
    Konzervatívny odvodený prepočet.

    Zatiaľ iba:
    BETÓN:
    m2 × explicitná hrúbka = m3
    """

    normalized = (
        _normalize_text(
            description
        )
    )

    normalized_unit = (
        _normalize_unit(
            unit
        )
    )

    if normalized_unit != "m2":

        return (
            quantity,
            normalized_unit
        )

    concrete_class = re.search(
        r"\bc\s*[0-9]+\s*/\s*[0-9]+\b",
        normalized,
        flags=re.IGNORECASE
    )

    if not concrete_class:

        return (
            quantity,
            normalized_unit
        )

    match = re.search(
        (
            r"\bhr\.?\s*"
            r"([0-9]+(?:[.,][0-9]+)?)"
            r"\s*mm\b"
        ),
        normalized
    )

    if not match:

        return (
            quantity,
            normalized_unit
        )

    thickness_mm = float(
        match.group(
            1
        ).replace(
            ",",
            "."
        )
    )

    return (
        quantity
        *
        thickness_mm
        /
        1000.0,

        "m3"
    )


def aggregate_budget_items_python(
    items
):
    """
    Všeobecné zoskupovanie bez AI.
    """

    groups = []

    for item in items:

        matching_group = None

        for group in groups:

            if _can_group_items(
                item,
                group[
                    "representative"
                ]
            ):

                matching_group = (
                    group
                )

                break

        if matching_group is None:

            matching_group = {
                "representative":
                    item,

                "members":
                    []
            }

            groups.append(
                matching_group
            )

        matching_group[
            "members"
        ].append(
            item
        )

    result = []

    for group in groups:

        representative = (
            group[
                "representative"
            ]
        )

        total_quantity = 0.0
        result_unit = None
        source_rows = []
        warnings = []

        for member in group[
            "members"
        ]:

            (
                converted_quantity,
                converted_unit
            ) = (
                _convert_quantity_for_ksp(
                    member[
                        "description"
                    ],
                    member[
                        "unit"
                    ],
                    member[
                        "quantity"
                    ]
                )
            )

            if result_unit is None:

                result_unit = (
                    converted_unit
                )

            if (
                converted_unit
                !=
                result_unit
            ):

                converted_quantity = (
                    member[
                        "quantity"
                    ]
                )

                converted_unit = (
                    _normalize_unit(
                        member[
                            "unit"
                        ]
                    )
                )

            total_quantity += float(
                converted_quantity
            )

            source_rows.append(
                {
                    "sheet":
                        member[
                            "sheet"
                        ],

                    "row_number":
                        member[
                            "row_number"
                        ],

                    "code":
                        member.get(
                            "code",
                            ""
                        ),

                    "description":
                        member[
                            "description"
                        ],

                    "original_quantity":
                        member[
                            "quantity"
                        ],

                    "original_unit":
                        member[
                            "unit"
                        ],

                    "category":
                        member.get(
                            "category",
                            ""
                        ),

                    "sheet_project_status":
                        member.get(
                            "sheet_project_status",
                            ""
                        )
                }
            )

            for warning in member.get(
                "warnings",
                []
            ):

                if warning not in warnings:

                    warnings.append(
                        warning
                    )

        params = (
            _extract_critical_parameters(
                representative[
                    "description"
                ]
            )
        )

        result.append(
            {
                "group_key":
                    _make_generic_group_key(
                        representative
                    ),

                "item_name":
                    representative[
                        "description"
                    ],

                "category":
                    representative.get(
                        "category",
                        _infer_budget_category(
                            representative[
                                "description"
                            ]
                        )
                    ),

                "unit":
                    result_unit
                    or
                    _normalize_unit(
                        representative[
                            "unit"
                        ]
                    ),

                "quantity":
                    round(
                        total_quantity,
                        6
                    ),

                "dimension":
                    "; ".join(
                        params
                    ),

                "material":
                    "",

                "source_rows":
                    source_rows,

                "grouping_method":
                    "python_generic",

                "warnings":
                    warnings
            }
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

    return result


# ==========================================================
# DIAGNOSTIKA ROZPOČTU
# ==========================================================

def _build_budget_diagnostics(
    file_bytes,
    items,
    project_hint=None
):
    sheet_info = (
        inspect_budget_sheets_python(
            file_bytes,
            project_hint=project_hint
        )
    )

    warnings = []

    for item in items:

        for warning in item.get(
            "warnings",
            []
        ):

            if warning not in warnings:

                warnings.append(
                    warning
                )

    skipped_foreign = [
        row
        for row
        in sheet_info[
            "sheets"
        ]
        if row.get(
            "status"
        )
        ==
        "foreign"
    ]

    return {
        "primary_project_tokens":
            sheet_info.get(
                "primary_project_tokens",
                []
            ),

        "skipped_foreign_sheets":
            skipped_foreign,

        "warnings":
            warnings,

        "item_count":
            len(
                items
            )
    }


# ==========================================================
# HLAVNÉ SPRACOVANIE ROZPOČTU
# ==========================================================

def process_budget_python(
    file_bytes,
    project_hint=None
):
    """
    Verejná funkcia pre appku.
    """

    items = (
        extract_budget_items_python(
            file_bytes,
            project_hint=project_hint
        )
    )

    return (
        aggregate_budget_items_python(
            items
        )
    )


def process_budget_python_with_diagnostics(
    file_bytes,
    project_hint=None
):
    items = (
        extract_budget_items_python(
            file_bytes,
            project_hint=project_hint
        )
    )

    rows = (
        aggregate_budget_items_python(
            items
        )
    )

    diagnostics = (
        _build_budget_diagnostics(
            file_bytes,
            items,
            project_hint=project_hint
        )
    )

    return {
        "rows":
            rows,

        "diagnostics":
            diagnostics
    }


# ==========================================================
# SPOJENIE VIAC ROZPOČTOV
# ==========================================================

def merge_aggregated_budget_rows(
    aggregated_lists
):
    """
    Spojí výsledky z viacerých rozpočtových Excelov.
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

                _normalize_unit(
                    item.get(
                        "unit",
                        ""
                    )
                ),

                str(
                    item.get(
                        "category",
                        ""
                    )
                )
            )

            if key not in grouped:

                grouped[
                    key
                ] = {

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
                        [],

                    "grouping_method":
                        item.get(
                            "grouping_method",
                            "python_generic"
                        ),

                    "warnings":
                        []
                }

            grouped[
                key
            ][
                "quantity"
            ] += float(
                item.get(
                    "quantity",
                    0
                )
                or 0
            )

            grouped[
                key
            ][
                "source_rows"
            ].extend(
                item.get(
                    "source_rows",
                    []
                )
            )

            for warning in item.get(
                "warnings",
                []
            ):

                if (
                    warning
                    not in
                    grouped[
                        key
                    ][
                        "warnings"
                    ]
                ):

                    grouped[
                        key
                    ][
                        "warnings"
                    ].append(
                        warning
                    )

    result = list(
        grouped.values()
    )

    for item in result:

        item[
            "quantity"
        ] = round(
            item[
                "quantity"
            ],
            6
        )

    return result


# ==========================================================
# SPÄTNÁ KOMPATIBILITA
# ==========================================================

def aggregate_budget_rows(
    classified_rows
):
    """
    Staršia funkcia ostáva iba preto,
    aby prípadný starší import appku nezrútil.
    """

    if not isinstance(
        classified_rows,
        list
    ):
        return []

    return classified_rows


# ==========================================================
# HLAVNÝ DISPEČER
# ==========================================================

def extract_text_from_file(
    arg1,
    arg2
):
    """
    Podporuje obe poradia:

    extract_text_from_file(
        file_bytes,
        file_name
    )

    extract_text_from_file(
        file_name,
        file_bytes
    )
    """

    if isinstance(
        arg1,
        (bytes, bytearray)
    ):

        file_bytes = (
            arg1
        )

        file_name = (
            arg2
        )

    else:

        file_name = (
            arg1
        )

        file_bytes = (
            arg2
        )

    extension = (
        str(
            file_name
        )
        .lower()
        .split(
            "."
        )[-1]
    )

    if extension == "pdf":

        return (
            extract_text_from_pdf(
                file_bytes
            )
        )

    if extension == "docx":

        return (
            extract_text_from_docx(
                file_bytes
            )
        )

    if extension in [
        "xlsx",
        "xls"
    ]:

        return (
            extract_text_from_excel(
                file_bytes
            )
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
