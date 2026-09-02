import io
from copy import copy

from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell


KSP_SHEET_NAME = "KSP_SO 202-300"

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
    Skopíruje vzhľad bunky zo šablóny.
    """

    if isinstance(
        source_cell,
        MergedCell
    ):
        return

    if isinstance(
        target_cell,
        MergedCell
    ):
        return

    if source_cell.has_style:
        target_cell._style = copy(
            source_cell._style
        )

    target_cell.font = copy(
        source_cell.font
    )

    target_cell.fill = copy(
        source_cell.fill
    )

    target_cell.border = copy(
        source_cell.border
    )

    target_cell.alignment = copy(
        source_cell.alignment
    )

    target_cell.protection = copy(
        source_cell.protection
    )

    target_cell.number_format = (
        source_cell.number_format
    )


def get_real_cell(
    worksheet,
    row,
    column
):
    """
    Ak bunka patrí do zlúčenej oblasti,
    vráti ľavú hornú bunku tejto oblasti.

    Inak vráti pôvodnú bunku.
    """

    cell = worksheet.cell(
        row=row,
        column=column
    )

    if not isinstance(
        cell,
        MergedCell
    ):
        return cell

    for merged_range in worksheet.merged_cells.ranges:

        if cell.coordinate in merged_range:

            return worksheet.cell(
                row=merged_range.min_row,
                column=merged_range.min_col
            )

    return None


def clear_existing_ksp_rows(
    worksheet,
    start_row
):
    """
    Vymaže pôvodné hodnoty KSP,
    ale nezasahuje do zlúčených buniek.
    """

    for row in range(
        start_row,
        worksheet.max_row + 1
    ):

        for column in COLUMN_MAP.values():

            cell = worksheet.cell(
                row=row,
                column=column
            )

            if isinstance(
                cell,
                MergedCell
            ):
                continue

            cell.value = None


def create_ksp_excel(
    template_bytes,
    ksp_rows
):
    """
    Vytvorí KSP Excel podľa pôvodnej mustry.
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

    style_source_row = START_ROW

    # --------------------------------------------------
    # VYČISTENIE STARÉHO OBSAHU
    # --------------------------------------------------

    clear_existing_ksp_rows(
        worksheet,
        START_ROW
    )

    # --------------------------------------------------
    # ZÁPIS AI RIADKOV
    # --------------------------------------------------

    for index, item in enumerate(
        ksp_rows
    ):

        target_row = (
            START_ROW + index
        )

        for (
            field_name,
            column_number
        ) in COLUMN_MAP.items():

            source_cell = get_real_cell(
                worksheet,
                style_source_row,
                column_number
            )

            target_cell = get_real_cell(
                worksheet,
                target_row,
                column_number
            )

            if target_cell is None:
                continue

            if source_cell is not None:
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
    # ULOŽENIE
    # --------------------------------------------------

    output = io.BytesIO()

    workbook.save(
        output
    )

    output.seek(0)

    return output.getvalue()
