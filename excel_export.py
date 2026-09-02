import io
import json
from copy import copy

from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell
from openpyxl.utils import get_column_letter


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


def capture_style(
    cell
):
    if cell is None:
        return None

    if isinstance(
        cell,
        MergedCell
    ):
        return None

    return {
        "style": copy(cell._style),
        "font": copy(cell.font),
        "fill": copy(cell.fill),
        "border": copy(cell.border),
        "alignment": copy(cell.alignment),
        "protection": copy(cell.protection),
        "number_format": cell.number_format
    }


def apply_style(
    cell,
    style_data
):
    if cell is None:
        return

    if style_data is None:
        return

    if isinstance(
        cell,
        MergedCell
    ):
        return

    cell._style = copy(
        style_data["style"]
    )

    cell.font = copy(
        style_data["font"]
    )

    cell.fill = copy(
        style_data["fill"]
    )

    cell.border = copy(
        style_data["border"]
    )

    cell.alignment = copy(
        style_data["alignment"]
    )

    cell.protection = copy(
        style_data["protection"]
    )

    cell.number_format = (
        style_data["number_format"]
    )


# --------------------------------------------------
# KONTROLA RIADKOV Z AI
# --------------------------------------------------

def normalize_ksp_rows(ksp_rows):
    """
    Zabezpečí, že do Excelu ide vždy
    zoznam dictionary objektov.
    """

    if isinstance(
        ksp_rows,
        str
    ):

        text = ksp_rows.strip()

        if text.startswith("```json"):
            text = text[7:]

        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        try:
            ksp_rows = json.loads(
                text.strip()
            )

        except json.JSONDecodeError as e:
            raise ValueError(
                "AI vrátila text, ktorý nie je "
                "platný JSON pre KSP."
            ) from e

    if isinstance(
        ksp_rows,
        dict
    ):

        found_rows = None

        for key in [
            "rows",
            "ksp_rows",
            "items",
            "data"
        ]:

            value = ksp_rows.get(
                key
            )

            if isinstance(
                value,
                list
            ):
                found_rows = value
                break

        if found_rows is None:

            if (
                "subproces"
                in ksp_rows
            ):
                found_rows = [
                    ksp_rows
                ]

        if found_rows is None:
            raise ValueError(
                "AI vrátila JSON objekt, "
                "ale nenašiel sa zoznam riadkov KSP."
            )

        ksp_rows = found_rows

    if not isinstance(
        ksp_rows,
        list
    ):
        raise ValueError(
            "Riadky KSP nemajú správny formát."
        )

    clean_rows = []

    for item in ksp_rows:

        if not isinstance(
            item,
            dict
        ):
            raise ValueError(
                "Jeden z riadkov KSP nie je "
                "v správnom JSON formáte."
            )

        clean_rows.append(
            item
        )

    if not clean_rows:
        raise ValueError(
            "AI nevytvorila žiadne riadky KSP."
        )

    return clean_rows


# --------------------------------------------------
# NÁJDENIE KSP LISTU A TABUĽKY
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
            30
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


def find_table_header_row(
    worksheet
):
    markers = [
        "názov subprocesu",
        "druh skúšky/kontroly",
        "spôsob kontroly",
        "početnosť"
    ]

    for row in range(
        1,
        min(
            worksheet.max_row,
            30
        ) + 1
    ):

        row_text = []

        for column in range(
            1,
            min(
                worksheet.max_column,
                20
            ) + 1
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
                row_text.append(
                    text
                )

        joined = " ".join(
            row_text
        )

        score = sum(
            marker in joined
            for marker in markers
        )

        if score >= 3:
            return row

    raise ValueError(
        "Nepodarilo sa nájsť riadok "
        "s hlavičkou KSP tabuľky."
    )


def find_start_row(
    worksheet,
    header_row
):
    """
    V mustre je pod hlavičkou často ešte
    zelený/žltý riadok 'Názov procesu'.
    Dáta začnú až pod ním.
    """

    candidate_row = (
        header_row + 1
    )

    row_text = []

    for column in range(
        1,
        min(
            worksheet.max_column,
            15
        ) + 1
    ):

        cell = worksheet.cell(
            row=candidate_row,
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
            row_text.append(
                text
            )

    joined = " ".join(
        row_text
    )

    if (
        "názov procesu"
        in joined
        or "material"
        in joined
        or "materiál"
        in joined
    ):
        return (
            header_row + 2
        )

    return (
        header_row + 1
    )


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
# HLAVIČKA PROJEKTU
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


def clear_unique_real_cells(
    worksheet,
    row,
    start_column,
    end_column
):
    """
    Vyčistí staré údaje v riadku napravo od označenia,
    aj keď boli bunky zlúčené.
    """

    cleared = set()

    for column in range(
        start_column,
        end_column + 1
    ):

        real_cell = get_real_cell(
            worksheet,
            row,
            column
        )

        if real_cell is None:
            continue

        if real_cell.coordinate in cleared:
            continue

        real_cell.value = None

        cleared.add(
            real_cell.coordinate
        )


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


def set_header_value(
    worksheet,
    labels,
    value
):
    label_cell = find_label_cell(
        worksheet,
        labels
    )

    if label_cell is None:
        return False

    # Najprv odstránime starý projektový text
    # v celom riadku napravo od labelu.
    clear_unique_real_cells(
        worksheet,
        label_cell.row,
        label_cell.column + 1,
        min(
            worksheet.max_column,
            15
        )
    )

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
    label_cell = find_label_cell(
        worksheet,
        labels
    )

    if label_cell is None:
        return False

    clear_unique_real_cells(
        worksheet,
        label_cell.row,
        label_cell.column + 1,
        min(
            worksheet.max_column,
            15
        )
    )

    return True


def get_metadata_value(
    metadata,
    field
):
    if not isinstance(
        metadata,
        dict
    ):
        return None

    item = metadata.get(
        field
    )

    if isinstance(
        item,
        dict
    ):
        return item.get(
            "value"
        )

    if isinstance(
        item,
        str
    ):
        return item

    return None


def clear_old_unlabelled_part_row(
    worksheet
):
    """
    V KSP mustre býva pod riadkom 'Objekt'
    ešte starý nezalabelovaný text typu:
    'Časť 300 Spodná stavba ...'

    Ten sa musí odstrániť, inak zostane
    v novom projekte.
    """

    object_label = find_label_cell(
        worksheet,
        [
            "Objekt",
            "Stavebný objekt",
            "Číslo a názov objektu"
        ]
    )

    if object_label is None:
        return None

    try:
        table_header_row = (
            find_table_header_row(
                worksheet
            )
        )

    except ValueError:
        return None

    first_row = (
        object_label.row + 1
    )

    last_row = (
        table_header_row - 1
    )

    if first_row > last_row:
        return None

    first_value_cell = None

    for row in range(
        first_row,
        last_row + 1
    ):

        # Nechávame ľavé labelové bunky na pokoji.
        start_column = (
            object_label.column + 1
        )

        # Zapamätáme si prvú vhodnú bunku
        # pre hodnotu ČASŤ.
        if first_value_cell is None:

            first_value_cell = get_real_cell(
                worksheet,
                row,
                start_column
            )

        clear_unique_real_cells(
            worksheet,
            row,
            start_column,
            min(
                worksheet.max_column,
                15
            )
        )

    return first_value_cell


def update_project_header(
    worksheet,
    metadata
):
    if not metadata:
        return

    stavba = get_metadata_value(
        metadata,
        "stavba"
    )

    objekt = get_metadata_value(
        metadata,
        "objekt"
    )

    cast = get_metadata_value(
        metadata,
        "cast"
    )

    zhotovitel = get_metadata_value(
        metadata,
        "zhotovitel"
    )

    objednavatel = get_metadata_value(
        metadata,
        "objednavatel"
    )

    set_header_value(
        worksheet,
        [
            "Stavba",
            "Názov stavby",
            "Názov stavby / Építkezés neve"
        ],
        stavba
    )

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
    # STARÁ NEZALABELOVANÁ ČASŤ Z MUSTRY
    # ------------------------------------------

    part_cell = (
        clear_old_unlabelled_part_row(
            worksheet
        )
    )

    # Ak je v mustre normálny label "Časť",
    # zapíšeme ho tam.
    part_was_set = set_header_value(
        worksheet,
        [
            "Časť",
            "Časť stavby"
        ],
        cast
    )

    # Ak label "Časť" neexistuje, ale mustra
    # používa samostatný nezalabelovaný riadok,
    # použijeme práve ten.
    if (
        not part_was_set
        and part_cell is not None
        and not is_empty_metadata_value(
            cast
        )
    ):
        part_cell.value = cast

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

    set_header_value(
        worksheet,
        [
            "Zhotoviteľ",
            "Dodávateľ"
        ],
        zhotovitel
    )

    clear_header_value(
        worksheet,
        [
            "Objednávateľ 2"
        ]
    )


# --------------------------------------------------
# KSP STĹPCE
# --------------------------------------------------

def get_column_map():
    """
    Táto mustra má presne tieto existujúce stĺpce.

    A = Por. č.
    B:C = Názov subprocesu
    D = Množstvo
    E = Druh skúšky/kontroly
    F = Spôsob kontroly
    G = Kritérium kvality
    H = Početnosť
    I = Celkový počet
    J = Za skúšku zodpovedá
    K = Skúšku vykoná
    L = Požiadavky a tolerancie
    M = Spôsob dokumentovania

    ŽIADNY nový stĺpec Poznámka sa nepridáva.
    """

    return {
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
        "dokumentovanie": 13
    }


# --------------------------------------------------
# DÁTOVÁ ČASŤ KSP
# --------------------------------------------------

def capture_template_styles(
    worksheet,
    start_row,
    column_map
):
    """
    Zachytíme štýl pôvodnej mustry ešte predtým,
    než odstránime staré zlúčenia buniek.
    """

    styles = {}

    for (
        field_name,
        column_number
    ) in column_map.items():

        source_cell = get_real_cell(
            worksheet,
            start_row,
            column_number
        )

        styles[
            field_name
        ] = capture_style(
            source_cell
        )

    # Pre stĺpec C použijeme štýl subprocesu.
    styles[
        "_subproces_c"
    ] = capture_style(
        get_real_cell(
            worksheet,
            start_row,
            3
        )
    )

    return styles


def unmerge_data_area(
    worksheet,
    start_row
):
    """
    Starý referenčný obsah obsahuje veľa vertikálne
    zlúčených buniek. Tie nemôžu zostať, pretože
    nové AI riadky by sa zapisovali do rovnakých
    top-left buniek.
    """

    ranges_to_unmerge = []

    for merged_range in list(
        worksheet.merged_cells.ranges
    ):

        if (
            merged_range.max_row
            >= start_row
        ):
            ranges_to_unmerge.append(
                str(merged_range)
            )

    for range_string in ranges_to_unmerge:

        worksheet.unmerge_cells(
            range_string
        )


def clear_existing_ksp_rows(
    worksheet,
    start_row,
    column_map
):
    """
    Vyčistí iba existujúce KSP dátové stĺpce A:M.
    Nevytvára ani nemaže stĺpce.
    """

    used_columns = sorted(
        set(
            list(
                column_map.values()
            )
            + [3]
        )
    )

    for row in range(
        start_row,
        worksheet.max_row + 1
    ):

        for column in used_columns:

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


def write_ksp_rows(
    worksheet,
    start_row,
    ksp_rows,
    column_map,
    styles
):
    source_height = (
        worksheet
        .row_dimensions[start_row]
        .height
    )

    for index, item in enumerate(
        ksp_rows
    ):

        target_row = (
            start_row + index
        )

        if source_height is not None:
            worksheet.row_dimensions[
                target_row
            ].height = source_height

        for (
            field_name,
            column_number
        ) in column_map.items():

            target_cell = worksheet.cell(
                row=target_row,
                column=column_number
            )

            apply_style(
                target_cell,
                styles.get(
                    field_name
                )
            )

            value = item.get(
                field_name,
                ""
            )

            if value is None:
                value = ""

            target_cell.value = value

        # C patrí k názvu subprocesu a zostáva
        # súčasťou jeho vizuálneho poľa.
        cell_c = worksheet.cell(
            row=target_row,
            column=3
        )

        apply_style(
            cell_c,
            styles.get(
                "_subproces_c"
            )
            or styles.get(
                "subproces"
            )
        )

        cell_c.value = None


def get_consecutive_groups(
    ksp_rows,
    field_name,
    start_row,
    group_start_index=0,
    group_end_index=None
):
    if group_end_index is None:
        group_end_index = (
            len(ksp_rows) - 1
        )

    groups = []

    index = group_start_index

    while index <= group_end_index:

        value = ksp_rows[index].get(
            field_name,
            ""
        )

        if value is None:
            value = ""

        value = str(
            value
        ).strip()

        start_index = index
        end_index = index

        while (
            end_index + 1
            <= group_end_index
        ):

            next_value = (
                ksp_rows[
                    end_index + 1
                ]
                .get(
                    field_name,
                    ""
                )
            )

            if next_value is None:
                next_value = ""

            next_value = str(
                next_value
            ).strip()

            if (
                not value
                or next_value != value
            ):
                break

            end_index += 1

        groups.append(
            (
                start_index,
                end_index,
                value
            )
        )

        index = (
            end_index + 1
        )

    return groups


def merge_generated_rows(
    worksheet,
    start_row,
    ksp_rows
):
    """
    Vrátime typické zlúčenia mustry:

    - Por. č. vertikálne pre rovnaký subproces
    - Názov subprocesu B:C horizontálne
      a zároveň vertikálne pre rovnaký subproces
    - Množstvo vertikálne pre rovnaký subproces
    - Druh kontroly vertikálne pri po sebe
      idúcich rovnakých hodnotách v rámci subprocesu
    """

    if not ksp_rows:
        return

    subproces_groups = get_consecutive_groups(
        ksp_rows,
        "subproces",
        start_row
    )

    for (
        group_start_index,
        group_end_index,
        subproces_value
    ) in subproces_groups:

        excel_start = (
            start_row
            + group_start_index
        )

        excel_end = (
            start_row
            + group_end_index
        )

        # --------------------------------------
        # SUBPROCES B:C
        # --------------------------------------

        worksheet.merge_cells(
            start_row=excel_start,
            start_column=2,
            end_row=excel_end,
            end_column=3
        )

        # --------------------------------------
        # PORADIE A
        # --------------------------------------

        poradie_values = {
            str(
                ksp_rows[i]
                .get(
                    "poradie",
                    ""
                )
            ).strip()
            for i in range(
                group_start_index,
                group_end_index + 1
            )
        }

        poradie_values.discard(
            ""
        )

        if (
            excel_end > excel_start
            and len(
                poradie_values
            ) == 1
        ):
            worksheet.merge_cells(
                start_row=excel_start,
                start_column=1,
                end_row=excel_end,
                end_column=1
            )

        # --------------------------------------
        # MNOŽSTVO D
        # --------------------------------------

        mnozstvo_values = {
            str(
                ksp_rows[i]
                .get(
                    "mnozstvo",
                    ""
                )
            ).strip()
            for i in range(
                group_start_index,
                group_end_index + 1
            )
        }

        mnozstvo_values.discard(
            ""
        )

        if (
            excel_end > excel_start
            and len(
                mnozstvo_values
            ) == 1
        ):
            worksheet.merge_cells(
                start_row=excel_start,
                start_column=4,
                end_row=excel_end,
                end_column=4
            )

        # --------------------------------------
        # DRUH KONTROLY E
        # --------------------------------------

        control_groups = get_consecutive_groups(
            ksp_rows,
            "druh_kontroly",
            start_row,
            group_start_index,
            group_end_index
        )

        for (
            control_start_index,
            control_end_index,
            control_value
        ) in control_groups:

            if (
                control_value
                and control_end_index
                > control_start_index
            ):

                worksheet.merge_cells(
                    start_row=(
                        start_row
                        + control_start_index
                    ),
                    start_column=5,
                    end_row=(
                        start_row
                        + control_end_index
                    ),
                    end_column=5
                )


# --------------------------------------------------
# TVORBA EXCELU
# --------------------------------------------------

def create_ksp_excel(
    template_bytes,
    ksp_rows,
    metadata=None
):
    # ------------------------------------------
    # 1. KONTROLA AI DÁT
    # ------------------------------------------

    ksp_rows = normalize_ksp_rows(
        ksp_rows
    )

    template_file = io.BytesIO(
        template_bytes
    )

    workbook = load_workbook(
        template_file
    )

    # ------------------------------------------
    # 2. KSP LIST
    # ------------------------------------------

    ksp_worksheet = (
        find_ksp_worksheet(
            workbook
        )
    )

    table_header_row = (
        find_table_header_row(
            ksp_worksheet
        )
    )

    start_row = find_start_row(
        ksp_worksheet,
        table_header_row
    )

    column_map = get_column_map()

    # ------------------------------------------
    # 3. TITULNÝ LIST
    # ------------------------------------------

    title_worksheet = (
        find_title_worksheet(
            workbook
        )
    )

    # ------------------------------------------
    # 4. HLAVIČKA
    # ------------------------------------------

    update_project_header(
        ksp_worksheet,
        metadata
    )

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
    # 5. ZACHYTENIE PÔVODNÉHO ŠTÝLU
    # ------------------------------------------

    styles = capture_template_styles(
        ksp_worksheet,
        start_row,
        column_map
    )

    # ------------------------------------------
    # 6. ODSTRÁNENIE STARÝCH MERGE V DÁTACH
    # ------------------------------------------

    unmerge_data_area(
        ksp_worksheet,
        start_row
    )

    # ------------------------------------------
    # 7. VYČISTENIE STARÝCH DÁT
    # ------------------------------------------

    clear_existing_ksp_rows(
        ksp_worksheet,
        start_row,
        column_map
    )

    # ------------------------------------------
    # 8. NOVÉ RIADKY
    # ------------------------------------------

    write_ksp_rows(
        ksp_worksheet,
        start_row,
        ksp_rows,
        column_map,
        styles
    )

    # ------------------------------------------
    # 9. OBNOVENIE VZHĽADU MUSTRY
    # ------------------------------------------

    merge_generated_rows(
        ksp_worksheet,
        start_row,
        ksp_rows
    )

    # ------------------------------------------
    # 10. ULOŽENIE
    # ------------------------------------------

    output = io.BytesIO()

    workbook.save(
        output
    )

    output.seek(0)

    return output.getvalue()
