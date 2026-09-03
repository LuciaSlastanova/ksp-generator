import io
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document


# ==========================================================
# PDF
# ==========================================================

def extract_text_from_pdf(file_bytes):
    """
    Prečíta text zo všetkých strán PDF.
    """

    reader = PdfReader(
        io.BytesIO(file_bytes)
    )

    parts = []

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):
        text = page.extract_text() or ""

        parts.append(
            f"\n--- STRANA {page_number} ---\n{text}"
        )

    return "\n".join(parts)


# ==========================================================
# DOCX
# ==========================================================

def extract_text_from_docx(file_bytes):
    """
    Prečíta odseky aj tabuľky zo súboru DOCX.
    """

    document = Document(
        io.BytesIO(file_bytes)
    )

    parts = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()

        if text:
            parts.append(text)

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

    return "\n".join(parts)


# ==========================================================
# EXCEL - VŠETKY HÁRKY
# ==========================================================

def extract_excel_rows(file_bytes):
    """
    Prečíta všetky hárky Excelu.

    Vracia zoznam:
    {
        "sheet": názov hárku,
        "row_number": číslo riadku,
        "values": hodnoty buniek
    }
    """

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
                    "sheet": str(sheet_name),
                    "row_number": int(
                        dataframe_index
                    ) + 1,
                    "values": values
                }
            )

    return result


def extract_text_from_excel(file_bytes):
    """
    Prevedie všetky hárky Excelu na text pre AI.
    """

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

        # Prázdne bunky medzi hodnotami zachováme
        # aspoň vo forme oddelovačov.
        values = row.get(
            "values",
            []
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
            + " | ".join(values)
        )

    return "\n".join(parts)


# ==========================================================
# SČÍTANIE ROZPOČTU PO AI KLASIFIKÁCII
# ==========================================================

def aggregate_budget_rows(classified_rows):
    """
    Sčíta položky rozpočtu, ktoré AI predtým
    semanticky zaradila cez group_key.

    AI rozhoduje, ktoré položky patria spolu.
    Python robí iba matematiku.

    Pravidlá:
    - spracujú sa iba include=True položky,
    - sčítava sa podľa (group_key, unit),
    - bez group_key alebo bez číselného množstva
      zostane položka samostatná,
    - zdrojové riadky sa zachovajú v source_rows.
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

        # Ak by AI vrátila text namiesto JSON boolean.
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
                    "ano",
                    "áno"
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
            "sheet": item.get(
                "sheet",
                ""
            ),
            "row_number": item.get(
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
                    "group_key": group_key,
                    "item_name": item.get(
                        "item_name",
                        ""
                    ),
                    "category": item.get(
                        "category",
                        ""
                    ),
                    "unit": unit,
                    "quantity": 0.0,
                    "dimension": item.get(
                        "dimension",
                        ""
                    ),
                    "material": item.get(
                        "material",
                        ""
                    ),
                    "source_rows": []
                }

            grouped[key][
                "quantity"
            ] += float(quantity)

            grouped[key][
                "source_rows"
            ].append(
                source_row
            )

        else:
            standalone.append(
                {
                    "group_key": group_key,
                    "item_name": item.get(
                        "item_name",
                        ""
                    ),
                    "category": item.get(
                        "category",
                        ""
                    ),
                    "unit": unit,
                    "quantity": quantity,
                    "dimension": item.get(
                        "dimension",
                        ""
                    ),
                    "material": item.get(
                        "material",
                        ""
                    ),
                    "source_rows": [
                        source_row
                    ]
                }
            )

    result = (
        list(
            grouped.values()
        )
        + standalone
    )

    def sort_key(item):

        source_rows = item.get(
            "source_rows",
            []
        )

        if not source_rows:
            return (
                "",
                999999999
            )

        first = source_rows[0]

        row_number = first.get(
            "row_number",
            999999999
        )

        try:
            row_number = int(
                row_number
            )
        except Exception:
            row_number = 999999999

        return (
            str(
                first.get(
                    "sheet",
                    ""
                )
            ),
            row_number
        )

    result.sort(
        key=sort_key
    )

    return result


# ==========================================================
# HLAVNÝ DISPEČER
# ==========================================================

def extract_text_from_file(arg1, arg2):
    """
    Prečíta podporovaný súbor.

    Funkcia zámerne podporuje OBE poradia argumentov:

        extract_text_from_file(file_bytes, file_name)

    aj:

        extract_text_from_file(file_name, file_bytes)

    aby bola kompatibilná s existujúcim kódom appky.
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

    file_name = str(file_name)

    extension = (
        file_name
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
            "Starý formát .doc nie je možné spoľahlivo čítať "
            "cez python-docx. Ulož dokument ako .docx."
        )

    raise ValueError(
        f"Nepodporovaný typ súboru: {file_name}"
    )
