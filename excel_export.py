import io
from openpyxl import load_workbook


def create_ksp_excel(template_bytes, ksp_rows):
    """
    Vytvorí nový KSP Excel podľa nahranej šablóny.

    template_bytes:
        obsah pôvodnej KSP šablóny

    ksp_rows:
        zoznam riadkov vytvorených AI
    """

    template_file = io.BytesIO(template_bytes)

    workbook = load_workbook(template_file)

    # Zatiaľ použijeme prvý pracovný list.
    # Neskôr nastavíme presne list KSP podľa tvojej mustry.
    worksheet = workbook.worksheets[0]

    # Zatiaľ iba testovací zápis.
    # Presný riadok a stĺpce nastavíme podľa tvojej šablóny.
    start_row = worksheet.max_row + 2

    for index, item in enumerate(ksp_rows):
        row = start_row + index

        worksheet.cell(
            row=row,
            column=1,
            value=item.get("subprocess", "")
        )

        worksheet.cell(
            row=row,
            column=2,
            value=item.get("control", "")
        )

        worksheet.cell(
            row=row,
            column=3,
            value=item.get("method", "")
        )

        worksheet.cell(
            row=row,
            column=4,
            value=item.get("standard", "")
        )

        worksheet.cell(
            row=row,
            column=5,
            value=item.get("frequency", "")
        )

        worksheet.cell(
            row=row,
            column=6,
            value=item.get("responsibility", "")
        )

        worksheet.cell(
            row=row,
            column=7,
            value=item.get("tolerance", "")
        )

    output = io.BytesIO()

    workbook.save(output)

    output.seek(0)

    return output.getvalue()
