import io
from copy import copy

from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell


START_ROW = 11


COLUMN_MAP = {
    "poradie": 1,
    "subproces": 2,
    "mnozstvo": 4,
    "druh_kontroly": 5,
    "sposob_kontroly": 6,
    "kriterium": 7,
    "pocetnost": 8,
    "celkovy_pocet": 9,
    "zodpoveda": 10,
    "vykona": 11,
    "tolerancia": 12,
    "dokumentovanie": 13,
    "poznamka": 14
}


# --------------------------------------------------
# POMOCNÉ FUNKCIE
# --------------------------------------------------

def normalize_text(value):
    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace(":", "")
        .replace("\n", " ")
    )


def is_empty_metadata_value(value):
    """
    OVERIŤ alebo prázdna hodnota znamená,
    že starý údaj z mustry sa má vymazať.
    """

    if value is None:
        return True

    value = str(value).strip()

    return (
        not value
        or value.upper() == "OVERIŤ"
    )


def get_real_cell(
    worksheet,
    row,
    column
):
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
# NÁJDENIE KSP LISTU
# --------------------------------------------------

def find_ksp_worksheet(workbook):
    required_markers = [
        "názov subprocesu",
        "druh skúšky/kontroly",
        "spôsob kontroly",
        "početnosť"
    ]

    best_sheet = None
    best_score = 0

    for worksheet in workbook.worksheets:

        sheet_text_parts = []

        max_row = min(
            worksheet.max_row,
            25
        )

        max_column = min(
            worksheet.max_column,
            20
        )

        for row in range(
            1,
            max_row + 1
        ):
            for column in range(
                1,
                max_column + 1
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

                text = normalize_text(
                    cell.value
                )

                if text:
                    sheet_text_parts.append(
                        text
                    )

        sheet_text = " ".join(
            sheet_text_parts
        )

        score = 0

        for marker in required_markers:

            if marker in sheet_text:
                score += 1

        if score > best_score:
            best_score = score
            best_sheet = worksheet

    if (
        best_sheet is None
        or best_score < 3
    ):
        raise ValueError(
            "Nepodarilo sa automaticky nájsť "
            "list s KSP tabuľkou."
        )

    return best_sheet


# --------------------------------------------------
# NÁJDENIE TITULNÉHO LISTU
# --------------------------------------------------

def find_title_worksheet(workbook):
    markers = [
        "názov stavby",
        "objednávateľ",
        "zhotoviteľ"
    ]

    best_sheet = None
    best_score = 0

    for worksheet in workbook.worksheets:

        sheet_text_parts = []

        max_row = min(
            worksheet.max_row,
            40
        )

        max_column = min(
            worksheet.max_column,
            15
        )

        for row in range(
            1,
            max_row + 1
        ):
            for column in range(
                1,
                max_column + 1
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

                text = normalize_text(
                    cell.value
                )

                if text:
                    sheet_text_parts.append(
                        text
                    )

        sheet_text = " ".join(
            sheet_text_parts
        )

        score = 0

        for marker in markers:

            if marker in sheet_text:
                score += 1

        if score > best_score:
            best_score = score
            best_sheet = worksheet

    if best_score >= 2:
        return best_sheet

    return None


# --------------------------------------------------
# HLAVIČKA - NÁJDENIE LABELU
# --------------------------------------------------

def find_label_cell(
    worksheet,
    possible_labels
):
    normalized_labels = [
        normalize_text(label)
        for label in possible_labels
    ]

    max_search_row = min(
        40,
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
    if label_cell is None:
        return None

    row = label_cell.row
    start_column = (
        label_cell.column + 1
    )

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

        if (
            real_cell.coordinate
            == label_cell.coordinate
        ):
            continue

        return real_cell

    return None


# --------------------------------------------------
# ZÁPIS / VYMAZANIE HLAVIČKY
# --------------------------------------------------

def set_header_value(
    worksheet,
    labels,
    value
):
    """
    Ak je value OVERIŤ alebo prázdna,
    starý údaj z mustry sa vymaže.
    """

    label_cell = find_label_cell(
        worksheet,
        labels
    )

    if label_cell is None:
        return False

    value_cell = (
        find_value_cell_next_to_label(
            worksheet,
            label_cell
        )
    )

    if value_cell is None:
        return False

    if is_empty_metadata_value(
        value
    ):
        value_cell.value = None

    else:
        value_cell.value = value

    return True


def clear_header_value(
    worksheet,
    labels
):
    """
    Vynútené vymazanie starej hodnoty z mustry.
    """

    label_cell = find_label_cell(
        worksheet,
        labels
    )

    if label_cell is None:
        return False

    value_cell = (
        find_value_cell_next_to_label(
            worksheet,
            label_cell
        )
    )

    if value_cell is None:
        return False

    value_cell.value = None

    return True


# --------------------------------------------------
# AKTUALIZÁCIA HLAVIČKY
# --------------------------------------------------

def update_project_header(
    worksheet,
    metadata
):
    if not metadata:
        return

    stavba = (
        metadata
        .get("stavba", {})
        .get("value")
    )

    objekt = (
        metadata
        .get("objekt", {})
        .get("value")
    )

    cast = (
        metadata
        .get("cast", {})
        .get("value")
    )

    zhotovitel = (
        metadata
        .get("zhotovitel", {})
        .get("value")
    )

    objednavatel = (
        metadata
        .get("objednavatel", {})
        .get("value")
    )

    # ------------------------------------------
    # STAVBA
    # ------------------------------------------

    set_header_value(
        worksheet,
        [
            "Stavba",
            "Názov stavby",
            "Názov stavby / Építkezés neve"
        ],
        stavba
    )

    # ------------------------------------------
    # OBJEKT
    # ------------------------------------------

    set_header_value(
        worksheet,
        [
            "Objekt",
            "Stavebný objekt",
            "Číslo a názov objektu"
        ],
        objekt
    )

    # ------------------------------------------
    # ČASŤ
    # ------------------------------------------

    set_header_value(
        worksheet,
        [
            "Časť",
            "Časť stavby"
        ],
        cast
    )

    # ------------------------------------------
    # OBJEDNÁVATEĽ 1
    # ------------------------------------------

    set_header_value(
        worksheet,
        [
            "Objednávateľ 1",
            "Objednávateľ",
            "Investor",
            "Stavebník"
        ],
        objednavatel
    )

    # ------------------------------------------
    # ZHOTOVITEĽ
    # ------------------------------------------

    set_header_value(
        worksheet,
        [
            "Zhotoviteľ",
            "Dodávateľ"
        ],
        zhotovitel
    )

    # ------------------------------------------
    # OBJEDNÁVATEĽ 2
    # ------------------------------------------
    # Tento projekt ho nemá.
    # Starý údaj z mustry odstránime.

    clear_header_value(
        worksheet,
        [
            "Objednávateľ 2"
        ]
    )


# --------------------------------------------------
# VYČISTENIE PÔVODNÝCH KSP RIADKOV
# --------------------------------------------------

def clear_existing_ksp_rows(
    worksheet,
    start_row
):
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
# TVORBA EXCELU
# --------------------------------------------------

def create_ksp_excel(
    template_bytes,
    ksp_rows,
    metadata=None
):
    template_file = io.BytesIO(
        template_bytes
    )

    workbook = load_workbook(
        template_file
    )

    # ------------------------------------------
    # NÁJDEME KSP LIST
    # ------------------------------------------

    ksp_worksheet = (
        find_ksp_worksheet(
            workbook
        )
    )

    # ------------------------------------------
    # NÁJDEME TITULNÝ LIST
    # ------------------------------------------

    title_worksheet = (
        find_title_worksheet(
            workbook
        )
    )

    # ------------------------------------------
    # HLAVIČKA KSP LISTU
    # ------------------------------------------

    update_project_header(
        ksp_worksheet,
        metadata
    )

    # ------------------------------------------
    # HLAVIČKA TITULNÉHO LISTU
    # ------------------------------------------

    if (
        title_worksheet is not None
        and title_worksheet
        is not ksp_worksheet
    ):

        update_project_header(
            title_worksheet,
            metadata
        )

    # ------------------------------------------
    # VYČISTENIE KSP RIADKOV
    # ------------------------------------------

    style_source_row = (
        START_ROW
    )

    clear_existing_ksp_rows(
        ksp_worksheet,
        START_ROW
    )

    # ------------------------------------------
    # ZÁPIS NOVÝCH RIADKOV
    # ------------------------------------------

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
                ksp_worksheet,
                style_source_row,
                column_number
            )

            target_cell = get_real_cell(
                ksp_worksheet,
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

            target_cell.value = (
                item.get(
                    field_name,
                    ""
                )
            )

    # ------------------------------------------
    # ULOŽENIE
    # ------------------------------------------

    output = io.BytesIO()

    workbook.save(
        output
    )

    output.seek(0)

    return output.getvalue()
