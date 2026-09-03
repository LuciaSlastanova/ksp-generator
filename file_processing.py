def aggregate_budget_rows(classified_rows):
    """
    Sčíta položky rozpočtu, ktoré AI už predtým
    semanticky zaradila.

    AI rozhoduje, ktoré položky patria k sebe cez group_key.
    Python robí iba presnú matematiku.

    Zásady:
    - spracujú sa iba include=True položky,
    - sčítava sa podľa (group_key, unit),
    - bez group_key alebo bez číselného quantity
      položka zostane samostatne,
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
                    "áno",
                    "ano"
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

        is_number = isinstance(
            quantity,
            (
                int,
                float
            )
        ) and not isinstance(
            quantity,
            bool
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
            ] += float(
                quantity
            )

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

    result = list(
        grouped.values()
    ) + standalone

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
