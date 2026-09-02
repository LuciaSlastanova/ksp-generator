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


# --------------------------------------------------
# POMOCNÉ FUNKCIE PRE ZLÚČENÉ BUNKY
# --------------------------------------------------

def get_real_cell(
    worksheet,
    row,
    column
):
    """
    Ak bunka patrí do zlúčenej oblasti,
    vráti ľavú hornú zapisovateľnú bunku.
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


def copy_cell_style(
    source_cell,
    target_cell
):
    """
    Skopíruje formátovanie bunky.
    """

    if source_cell is None:
        return

    if target_cell is None:
        return

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


# --------------------------------------------------
# HLAVIČKA KSP
# --------------------------------------------------

def normalize_text(value):
    """
    Pomocná funkcia na porovnávanie názvov buniek.
    """

    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace(":", "")
    )


def find_label_cell(
    worksheet,
    possible_labels
):
    """
    Nájde v hornej časti KSP bunku,
    ktorá obsahuje napr. Stavba, Objekt,
    Zhotoviteľ alebo Objednávateľ.
    """

    normalized_labels = [
        normalize_text(label)
        for label in possible_labels
    ]

    # Hlavičku hľadáme iba hore,
    # aby sme náhodou nemenili údaje v tabuľke KSP.
    max_search_row = min(
        30,
        worksheet.max_row
    )

    max_search_column = min(
        20,
        worksheet.max_column
    )

    for row in range(
        1,
        max_search_row + 1
    ):
        for column in range(
            1,
            max_search_column + 1
        ):

            cell = worksheet.cell(
                row=row,
                column=column
            )

            if isinstance(
                cell,
                MergedCell
            ):
                continue

            cell_text = normalize_text(
                cell.value
            )

            if not cell_text:
                continue

            for label in normalized_labels:

                if (
                    cell_text == label
                    or cell_text.startswith(label)
                ):
                    return cell

    return None


def find_value_cell_next_to_label(
    worksheet,
    label_cell
):
    """
    Nájde vhodnú bunku napravo od názvu položky.

    Napríklad:
    A4 = Stavba:
    B4 = názov stavby
    """

    if label_cell is None:
        return None

    row = label_cell.row
    start_column = label_cell.column + 1

    # Hľadáme najbližšiu zapisovateľnú bunku napravo.
    for column in range(
        start_column,
        min(
            worksheet.max_column,
            start_column + 8
        ) + 1
    ):

        real_cell = get_real_cell(
            worksheet,
            row,
            column
        )

        if real_cell is None:
            continue

        # Nesmie to byť tá istá bunka ako label
        if real_cell.coordinate == label_cell.coordinate:
            continue

        return real_cell

    return None


def write_header_value(
    worksheet,
    labels,
    value
):
    """
    Nájde položku hlavičky podľa názvu
    a zapíše novú hodnotu vedľa nej.
    """

    if not value:
        return False

    if value == "OVERIŤ":
        return False

    label_cell = find_label_cell(
        worksheet,
        labels
    )

    if label_cell is None:
        return False

    value_cell = find_value_cell_next_to_label(
        worksheet,
        label_cell
    )

    if value_cell is None:
        return False

    value_cell.value = value

    return True


def update_project_header(
    worksheet,
    metadata
):
    """
    Prepíše údaje starej stavby v mustre
    údajmi, ktoré boli overené v kroku 1.
    """

    if not metadata:
        return

    stavba = metadata.get(
        "stavba",
        {}
    ).get(
        "value"
    )

    objekt = metadata.get(
        "objekt",
        {}
    ).get(
        "value"
    )

    zhotovitel = metadata.get(
        "zhotovitel",
        {}
    ).get(
        "value"
    )

    objednavatel = metadata.get(
        "objednavatel",
        {}
    ).get(
        "value"
    )

    write_header_value(
        worksheet,
        [
            "Stavba",
            "Názov stavby"
        ],
        stavba
    )

    write_header_value(
        worksheet,
        [
            "Objekt",
            "Stavebný objekt",
            "SO"
        ],
        objekt
    )

    write_header_value(
        worksheet,
        [
            "Zhotoviteľ",
            "Dodávateľ"
        ],
        zhotovitel
    )

    write_header_value(
        worksheet,
        [
            "Objednávateľ",
            "Investor",
            "Stavebník"
        ],
        objednavatel
    )


# --------------------------------------------------
# PÔVODNÝ OBSAH KSP
# --------------------------------------------------

def clear_existing_ksp_rows(
    worksheet,
    start_row
):
    """
    Vymaže pôvodné hodnoty dátových riadkov KSP,
    ale zachová štruktúru a formátovanie.
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


# --------------------------------------------------
# TVORBA VÝSLEDNÉHO KSP
# --------------------------------------------------

def create_ksp_excel(
    template_bytes,
    ksp_rows,
    metadata=None
):
    """
    Vytvorí nový KSP Excel.

    template_bytes:
        vybraná KSP mustra

    ksp_rows:
        riadky KSP vytvorené AI

    metadata:
        overené údaje z kroku 1:
        stavba, objekt, zhotoviteľ,
        objednávateľ
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
    # PREPÍSANIE HLAVIČKY
    # --------------------------------------------------

    update_project_header(
        worksheet,
        metadata
    )

    # --------------------------------------------------
    # VYČISTENIE STARÝCH RIADKOV
    # --------------------------------------------------

    style_source_row = START_ROW

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

            target_cell.value = item.get(
                field_name,
                ""
            )

    # --------------------------------------------------
    # ULOŽENIE
    # --------------------------------------------------

    output = io.BytesIO()

    workbook.save(
        output
    )

    output.seek(0)

    return output.getvalue()
