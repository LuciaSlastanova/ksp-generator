import io
import pandas as pd
from pypdf import PdfReader
from docx import Document


def extract_text_from_pdf(file_bytes):
    reader = PdfReader(io.BytesIO(file_bytes))

    text_parts = []

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text_parts.append(page_text)

    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes):
    document = Document(io.BytesIO(file_bytes))

    paragraphs = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(paragraph.text)

    return "\n".join(paragraphs)


def extract_text_from_excel(file_bytes):
    excel_file = io.BytesIO(file_bytes)

    sheets = pd.read_excel(
        excel_file,
        sheet_name=None,
        header=None
    )

    text_parts = []

    for sheet_name, dataframe in sheets.items():
        text_parts.append(
            f"\n--- LIST: {sheet_name} ---\n"
        )

        dataframe = dataframe.fillna("")

        for row in dataframe.itertuples(
            index=False,
            name=None
        ):
            values = [
                str(value).strip()
                for value in row
                if str(value).strip()
            ]

            if values:
                text_parts.append(" | ".join(values))

    return "\n".join(text_parts)


def extract_text_from_file(file_name, file_bytes):
    extension = (
        file_name
        .lower()
        .split(".")[-1]
    )

    if extension == "pdf":
        return extract_text_from_pdf(file_bytes)

    if extension == "docx":
        return extract_text_from_docx(file_bytes)

    if extension in ["xlsx", "xls"]:
        return extract_text_from_excel(file_bytes)

    if extension == "doc":
        return (
            "Formát .doc zatiaľ nie je možné automaticky "
            "spracovať. Použi .docx alebo PDF."
        )

    return (
        f"Nepodporovaný formát súboru: {extension}"
    )
