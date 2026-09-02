import io
from copy import copy

from openpyxl import load_workbook


KSP_SHEET_NAME = "KSP_SO 202-300"

# V tvojej šablóne začínajú dátové riadky od riadku 11
START_ROW = 11


COLUMN_MAP = {
    "poradie": 1,            # A
    "subproces": 2,          # B
    "mnozstvo": 4,           # D
    "druh_kontroly": 5,      # E
    "sposob_kontroly": 6,    # F
    "kriterium": 7,          # G
    "pocetnost": 8,          # H
    "celkovy_pocet": 9,      # I
    "zodpoveda": 10,         # J
    "vykona": 11,            # K
    "tolerancia": 12,        # L
    "dokumentovanie": 13,    # M
    "poznamka": 14           # N
}


def copy_cell_style(source_cell, target_cell):
    """
    Skopíruje formátovanie zo vzorového riadku šablóny.
    """

    if source_cell.has_style:
        target_cell._style = copy(source_cell._style)

    if source_cell.number_format:
        target_cell.number_format = source_cell.number_format

    if source_cell.font:
        target_cell.font = copy(source_cell.font)

    if source_cell.fill:
        target_cell.fill = copy(source_cell.fill)

    if source_cell.border:
        target_cell.border = copy(source_cell.border)

    if source_cell.alignment:
        target_cell.alignment = copy(source_cell.alignment)

    if source_cell.protection:
        target_cell.protection = copy(source_cell.protection)


def clear_existing_ksp_rows(worksheet, start_row):
    """
    Vymaže starý obsah dátových riadkov,
    ale ponechá štruktúru a formát šablóny.
    """

    max_row = worksheet.max_row

    for row in range(start_row, max_row + 1):
        for column in COLUMN_MAP.values():
            worksheet.cell(
                row=row,
                column=column
            ).value = None


def create_ksp_excel(
    template_bytes,
    ksp_rows
):
    """
    Vytvorí nový KSP Excel podľa nahranej mustry.

    template_bytes:
        binárny obsah KSP šablóny

    ksp_rows:
        JSON riadky vytvorené AI
    """

    template_file = io.BytesIO(
        template_bytes
    )

    workbook = load_workbook(
        template_file
    )

    if KSP_SHEET_NAME not in workbook.sheetnames:
        raise ValueError(
            f"V šablóne sa nenašiel list "
            f"'{KSP_SHEET_NAME}'."
        )

    worksheet = workbook[
        KSP_SHEET_NAME
    ]

    # --------------------------------------------------
    # VZOROVÝ RIADOK PRE FORMÁTOVANIE
    # --------------------------------------------------

    style_source_row = START_ROW

    # --------------------------------------------------
    # VYČISTENIE STARÉHO OBSAHU
    # --------------------------------------------------

    clear_existing_ksp_rows(
        worksheet,
        START_ROW
    )

    # --------------------------------------------------
    # ZÁPIS NOVÝCH KSP RIADKOV
    # --------------------------------------------------

    for index, item in enumerate(
        ksp_rows
    ):
        target_row = (
            START_ROW + index
        )

        # Ak potrebujeme viac riadkov, než mala šablóna,
        # vložíme nový riadok.
        if target_row > worksheet.max_row:
            worksheet.insert_rows(
                target_row
            )

        for field_name, column_number in COLUMN_MAP.items():

            source_cell = worksheet.cell(
                row=style_source_row,
                column=column_number
            )

            target_cell = worksheet.cell(
                row=target_row,
                column=column_number
            )

            # zachovanie vzhľadu šablóny
            copy_cell_style(
                source_cell,
                target_cell
            )

            value = item.get(
                field_name,
                ""
            )

            target_cell.value = value

    # --------------------------------------------------
    # ULOŽENIE DO PAMÄTE
    # --------------------------------------------------

    output = io.BytesIO()

    workbook.save(
        output
    )

    output.seek(0)

    return output.getvalue()
