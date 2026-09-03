import io
import pandas as pd
from pypdf import PdfReader
from docx import Document


# --------------------------------------------------
# PDF
# --------------------------------------------------

def extract_text_from_pdf(file_bytes):
    reader = PdfReader(
        io.BytesIO(file_bytes)
    )

    text_parts = []

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):
        page_text = page.extract_text()

        if page_text:
            text_parts.append(
                f"\n--- STRANA: {page_number} ---\n"
            )

            text_parts.append(
                page_text
            )

    return "\n".join(
        text_parts
    )


# --------------------------------------------------
# DOCX
# --------------------------------------------------

def extract_text_from_docx(file_bytes):
    document = Document(
        io.BytesIO(file_bytes)
    )

    paragraphs = []

    for paragraph in document.paragraphs:

        if paragraph.text.strip():
            paragraphs.append(
                paragraph.text.strip()
            )

    return "\n".join(
        paragraphs
    )


# --------------------------------------------------
# EXCEL - SUROVÉ RIADKY ZO VŠETKÝCH HÁRKOV
# --------------------------------------------------

def extract_excel_rows(file_bytes):
    """
    Načíta všetky hárky Excelu bez predpokladu,
    kde sa nachádza názov položky, MJ, množstvo
    alebo cena.

    Výsledok je zoznam riadkov:

    [
        {
            "sheet": "SO 01",
            "row_number": 12,
            "values": ["1", "Výkop ryhy...", "m3", "120,5", ...]
        },
        ...
    ]

    Táto funkcia NIČ nesčítava a NIČ neklasifikuje.
    Iba bezpečne vytiahne surové dáta.
    """

    excel_file = io.BytesIO(
        file_bytes
    )

    sheets = pd.read_excel(
        excel_file,
        sheet_name=None,
        header=None,
        dtype=object
    )

    rows = []

    for sheet_name, dataframe in sheets.items():

        dataframe = dataframe.fillna(
            ""
        )

        for row_number, row in enumerate(
            dataframe.itertuples(
                index=False,
                name=None
            ),
            start=1
        ):

            values = []

            has_value = False

            for value in row:

                if value is None:
                    text_value = ""

                else:
                    text_value = str(
                        value
                    ).strip()

                if text_value:
                    has_value = True

                values.append(
                    text_value
                )

            if not has_value:
                continue

            rows.append(
                {
                    "sheet": str(
                        sheet_name
                    ),
                    "row_number": row_number,
                    "values": values
                }
            )

    return rows


# --------------------------------------------------
# EXCEL - TEXT PRE AI
# --------------------------------------------------

def extract_text_from_excel(file_bytes):
    """
    Prevedie Excel na text tak, aby AI videla:
    - názov hárku
    - číslo pôvodného riadku
    - všetky neprázdne hodnoty riadku

    Dôležité:
    nič tu nefiltrujeme podľa cien,
    pretože rôzne cenové ponuky majú
    rôznu štruktúru.

    O tom, čo je položka, MJ, množstvo,
    cena alebo medzisúčet, rozhodne neskôr AI.
    """

    rows = extract_excel_rows(
        file_bytes
    )

    if not rows:
        return ""

    text_parts = []

    current_sheet = None

    for item in rows:

        sheet_name = item[
            "sheet"
        ]

        if sheet_name != current_sheet:

            current_sheet = sheet_name

            text_parts.append(
                f"\n--- LIST: {sheet_name} ---\n"
            )

        non_empty_values = [
            value
            for value in item["values"]
            if value
        ]

        if not non_empty_values:
            continue

        row_text = " | ".join(
            non_empty_values
        )

        text_parts.append(
            f"RIADOK {item['row_number']}: "
            f"{row_text}"
        )

    return "\n".join(
        text_parts
    )


# --------------------------------------------------
# VŠEOBECNÉ SPRACOVANIE SÚBORU
# --------------------------------------------------

def extract_text_from_file(
    file_name,
    file_bytes
):
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
        return (
            "Formát .doc zatiaľ nie je možné "
            "automaticky spracovať. "
            "Použi .docx alebo PDF."
        )

    return (
        f"Nepodporovaný formát súboru: "
        f"{extension}"
    )
