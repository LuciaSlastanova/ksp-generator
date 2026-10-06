get_project_header
)

from file_processing import extract_text_from_file
from file_processing import (
    extract_text_from_file,
    process_budget_python,
    merge_aggregated_budget_rows
)

from ai import (
generate_ksp_rows,
@@ -54,6 +58,65 @@ def build_documents_text(documents):
return "\n".join(text_parts)


def build_aggregated_budget_text(aggregated_rows):
    """
    Prevedie Python-om spočítané položky rozpočtu
    na jednoznačný text pre AI.
    """

    text_parts = [
        """
========================================
AGREGOVANÉ POLOŽKY CENOVEJ PONUKY
========================================

Tento zoznam vznikol Python spracovaním všetkých
detailných hárkov rozpočtu.

PRE MNOŽSTVÁ A ROZSAH PRÁC JE TENTO ZOZNAM
HLAVNÝM ZDROJOM PRE TVORBU KSP.

AI NESMIE množstvá znovu sčítavať.
"""
    ]

    for index, item in enumerate(
        aggregated_rows,
        start=1
    ):

        source_rows = item.get(
            "source_rows",
            []
        )

        source_text = ", ".join(
            (
                f"{source.get('sheet', '')}"
                f"/riadok {source.get('row_number', '')}"
            )
            for source in source_rows
        )

        text_parts.append(
            (
                f"{index}. "
                f"group_key={item.get('group_key', '')} | "
                f"položka={item.get('item_name', '')} | "
                f"kategória={item.get('category', '')} | "
                f"materiál={item.get('material', '')} | "
                f"rozmer={item.get('dimension', '')} | "
                f"množstvo={item.get('quantity', '')} | "
                f"MJ={item.get('unit', '')} | "
                f"zdroj={source_text}"
            )
        )

    return "\n".join(
        text_parts
    )


def get_saved_header_value(saved_header, field):
"""
   Podporuje uloženú hlavičku vo forme:
@@ -137,6 +200,10 @@ def show_project_detail():
f"ksp_excel_{project_id}"
)

        aggregated_budget_key = (
            f"aggregated_budget_{project_id}"
        )

# ==================================================
# ULOŽENÁ HLAVIČKA PROJEKTU
# ==================================================
@@ -488,36 +555,22 @@ def show_project_detail():
selected_document_type
)

            # Po zmene podkladov staré údaje
            # hlavičky nemusia byť aktuálne.
            if selected_document_type in [
                "technical_report",
                "budget"
            ]:

                st.session_state.pop(
                    metadata_key,
                    None
                )

                for field in [
                    "stavba",
                    "objekt",
                    "cast",
                    "zhotovitel",
                    "objednavatel"
                ]:

                    st.session_state.pop(
                        f"header_{field}_{project_id}",
                        None
                    )
            # Po pridaní nového podkladu
            # ponecháme uloženú hlavičku projektu.
            # AI kontrola hlavičky sa spustí iba vtedy,
            # keď ju používateľ vedome vyžiada.

st.session_state.pop(
excel_key,
None
)

            if selected_document_type == "budget":
                st.session_state.pop(
                    aggregated_budget_key,
                    None
                )

st.success(
f"Súbor '{new_file.name}' "
f"bol pridaný k projektu."
@@ -533,11 +586,6 @@ def show_project_detail():
"### 1️⃣ 🔎 Kontrola údajov hlavičky KSP"
)

        # ==================================================
        # AK UŽ JE HLAVIČKA ULOŽENÁ,
        # NEVOLÁME AI AUTOMATICKY ANI ZBYTOČNE
        # ==================================================

if saved_header:

st.success(
@@ -611,11 +659,6 @@ def show_project_detail():
f"header_{field}_{project_id}"
] = value

        # ==================================================
        # AK HLAVIČKA EŠTE NIE JE ULOŽENÁ,
        # PONÚKNEME PRVÚ AI KONTROLU
        # ==================================================

else:

st.caption(
@@ -688,6 +731,7 @@ def show_project_detail():
st.session_state[
f"header_{field}_{project_id}"
] = value

# ==================================================
# EDITOVATEĽNÁ HLAVIČKA + ULOŽENIE
# ==================================================
@@ -706,12 +750,6 @@ def show_project_detail():
"#### ✏️ Údaje, ktoré sa zapíšu do Excelu"
)

            st.info(
                "Údaje môžeš ručne opraviť. "
                "Po oprave klikni na "
                "💾 Uložiť hlavičku projektu."
            )

fields = [
("stavba", "Stavba"),
("objekt", "Objekt / SO"),
@@ -750,7 +788,8 @@ def show_project_detail():

if st.button(
"💾 Uložiť hlavičku projektu",
                use_container_width=True
                use_container_width=True,
                key=f"save_header_{project_id}"
):

header_to_save = {
@@ -782,6 +821,7 @@ def show_project_detail():
)

if saved_result:

saved_header = header_to_save

st.success(
@@ -794,6 +834,7 @@ def show_project_detail():
)

else:

st.error(
"Hlavičku sa nepodarilo uložiť."
)
@@ -839,10 +880,6 @@ def show_project_detail():
and reference_ksps
):

            # ------------------------------------------
            # VÝBER MUSTRY
            # ------------------------------------------

template_names = [
doc["file_name"]
for doc in ksp_templates
@@ -866,10 +903,6 @@ def show_project_detail():
== selected_template_name
)

            # ------------------------------------------
            # VÝBER REFERENČNÉHO KSP
            # ------------------------------------------

reference_names = [
doc["file_name"]
for doc in reference_ksps
@@ -893,10 +926,6 @@ def show_project_detail():
== selected_reference_name
)

            # ------------------------------------------
            # POKYNY PRE KSP
            # ------------------------------------------

generation_instruction = (
st.text_area(
"Pokyny pre vytvorenie KSP",
@@ -906,14 +935,9 @@ def show_project_detail():
"Použi iba kontroly a skúšky z vybraného "
"referenčného KSP. "
"Projektové podklady použi na určenie "
                        "rozsahu prác, materiálov a množstiev. "
                        "rozsahu prác a materiálov. "
                        "Množstvá používaj iba z agregovaného rozpočtu. "
"Nevymýšľaj nové skúšky, kontroly ani normy. "
                        "Zaraď iba tie skúšky a kontroly, ktoré sú "
                        "pre daný rozsah prác potrebné podľa projektu, "
                        "platných predpisov alebo záväzných technických "
                        "požiadaviek. "
                        "Cieľom je KSP s čo najmenším potrebným "
                        "rozsahom skúšok, ale technicky a právne správny. "
"Ak niečo nie je možné jednoznačne určiť, "
"označ to ako OVERIŤ."
),
@@ -931,176 +955,369 @@ def show_project_detail():
f"**{selected_reference['file_name']}**"
)

            # ------------------------------------------
            # GENEROVANIE
            # ------------------------------------------
            budget_documents = [
                doc
                for doc in documents
                if doc["document_type"]
                == "budget"
            ]

            if st.button(
                "Vygenerovať KSP Excel",
                use_container_width=True
            ):
            if not budget_documents:

                saved_header_now = get_project_header(
                    project_id
                st.warning(
                    "Projekt nemá nahraný rozpočet "
                    "alebo cenovú ponuku."
)

                if not saved_header_now:
            else:

                    st.warning(
                        "Najprv skontroluj a ulož "
                        "hlavičku projektu."
                    )
                st.markdown(
                    "#### Krok A – spočítať cenovú ponuku"
                )

                    return
                st.caption(
                    "Tento krok je 100 % Python. "
                    "Nevolá OpenAI API a nespotrebúva API kredit."
                )

                current_header = {
                    "stavba": st.session_state.get(
                        f"header_stavba_{project_id}",
                        ""
                    ),
                    "objekt": st.session_state.get(
                        f"header_objekt_{project_id}",
                        ""
                    ),
                    "cast": st.session_state.get(
                        f"header_cast_{project_id}",
                        ""
                    ),
                    "zhotovitel": st.session_state.get(
                        f"header_zhotovitel_{project_id}",
                        ""
                    ),
                    "objednavatel": st.session_state.get(
                        f"header_objednavatel_{project_id}",
                        ""
                if st.button(
                    "1️⃣ Spočítať cenovú ponuku bez AI",
                    use_container_width=True,
                    key=f"aggregate_budget_{project_id}"
                ):

                    aggregated_lists = []

                    with st.spinner(
                        "Čítam všetky detailné hárky "
                        "a presne sčítavam množstvá..."
                    ):

                        for budget_doc in budget_documents:

                            budget_bytes = (
                                download_project_file(
                                    budget_doc[
                                        "file_path"
                                    ]
                                )
                            )

                            one_budget_result = (
                                process_budget_python(
                                    budget_bytes,
                                    project_hint=selected_name
                                )
                            )

                            aggregated_lists.append(
                                one_budget_result
                            )

                        aggregated_budget_rows = (
                            merge_aggregated_budget_rows(
                                aggregated_lists
                            )
                        )

                    if not aggregated_budget_rows:

                        st.error(
                            "Z cenovej ponuky sa nepodarilo "
                            "načítať tabuľku "
                            "Kód / Popis / MJ / Množstvo."
                        )

                        return

                    st.session_state[
                        aggregated_budget_key
                    ] = aggregated_budget_rows

                    st.session_state.pop(
                        excel_key,
                        None
)
                }

                normalized_saved_header = {
                    field: get_saved_header_value(
                        saved_header_now,
                        field
                    st.session_state.pop(
                        f"ksp_rows_{project_id}",
                        None
)
                    for field in [
                        "stavba",
                        "objekt",
                        "cast",
                        "zhotovitel",
                        "objednavatel"
                    ]
                }

                if current_header != normalized_saved_header:
                    st.success(
                        "Cenová ponuka bola spočítaná bez AI. "
                        "Skontroluj výsledky nižšie."
                    )

                    st.warning(
                        "Hlavičku si zmenila. "
                        "Najprv klikni na "
                        "💾 Uložiť hlavičku projektu."
                aggregated_budget_rows = (
                    st.session_state.get(
                        aggregated_budget_key,
                        []
)
                )

                    return
                if aggregated_budget_rows:

                # --------------------------------------
                # FINÁLNA HLAVIČKA = ULOŽENÁ HLAVIČKA
                # --------------------------------------
                    st.markdown(
                        "#### 🔎 Agregovaný rozpočet pred KSP"
                    )

                final_metadata = {
                    field: {
                        "value": normalized_saved_header[field]
                    }
                    for field in normalized_saved_header
                }
                    st.info(
                        "Táto tabuľka vznikla iba v Pythone. "
                        "Zobrazenie ani sčítanie nepoužíva OpenAI API."
                    )

                # --------------------------------------
                # PROJEKTOVÉ PODKLADY PRE AI
                # --------------------------------------
                    budget_preview_rows = []

                project_documents = [
                    doc
                    for doc in documents
                    if doc["document_type"]
                    in [
                        "technical_report",
                        "budget",
                        "drawing",
                        "other"
                    ]
                ]
                    for item in aggregated_budget_rows:

                ai_documents = (
                    project_documents
                    + [
                        selected_reference
                    ]
                )
                        source_rows = item.get(
                            "source_rows",
                            []
                        )

                with st.spinner(
                    "Načítavam projektové podklady..."
                ):
                        source_text = ", ".join(
                            (
                                f"{source.get('sheet', '')}"
                                f" / r. "
                                f"{source.get('row_number', '')}"
                            )
                            for source in source_rows
                        )

                    project_text = (
                        build_documents_text(
                            ai_documents
                        budget_preview_rows.append(
                            {
                                "Položka":
                                    item.get(
                                        "item_name",
                                        ""
                                    ),
                                "Kategória":
                                    item.get(
                                        "category",
                                        ""
                                    ),
                                "Množstvo":
                                    item.get(
                                        "quantity",
                                        ""
                                    ),
                                "MJ":
                                    item.get(
                                        "unit",
                                        ""
                                    ),
                                "Počet zdrojových riadkov":
                                    len(
                                        source_rows
                                    ),
                                "Zdrojové hárky / riadky":
                                    source_text
                            }
)

                    st.dataframe(
                        budget_preview_rows,
                        use_container_width=True,
                        hide_index=True
)

                    project_text += (
                        "\n\n"
                        "=================================\n"
                        "POKYNY POUŽÍVATEĽA\n"
                        "=================================\n"
                        f"{generation_instruction}"
                    st.markdown(
                        "#### Krok B – vytvoriť KSP"
)

                # --------------------------------------
                # HLAVNÉ AI VOLANIE
                # --------------------------------------
                    st.caption(
                        "Až toto tlačidlo spustí AI volanie. "
                        "Množstvá už boli predtým spočítané v Pythone."
                    )

                with st.spinner(
                    "AI pripravuje riadky KSP..."
                ):
                    if st.button(
                        "2️⃣ Pokračovať a vygenerovať KSP",
                        use_container_width=True,
                        key=f"generate_ksp_{project_id}"
                    ):

                    ksp_rows = (
                        generate_ksp_rows(
                            project_text
                        saved_header_now = (
                            get_project_header(
                                project_id
                            )
)
                    )

                # --------------------------------------
                # EXCEL
                # --------------------------------------
                        if not saved_header_now:

                with st.spinner(
                    "Vytváram Excel podľa mustry..."
                ):
                            st.warning(
                                "Najprv skontroluj a ulož "
                                "hlavičku projektu."
                            )

                    template_bytes = (
                        download_project_file(
                            selected_template[
                                "file_path"
                            return

                        current_header = {
                            "stavba":
                                st.session_state.get(
                                    f"header_stavba_{project_id}",
                                    ""
                                ),
                            "objekt":
                                st.session_state.get(
                                    f"header_objekt_{project_id}",
                                    ""
                                ),
                            "cast":
                                st.session_state.get(
                                    f"header_cast_{project_id}",
                                    ""
                                ),
                            "zhotovitel":
                                st.session_state.get(
                                    f"header_zhotovitel_{project_id}",
                                    ""
                                ),
                            "objednavatel":
                                st.session_state.get(
                                    f"header_objednavatel_{project_id}",
                                    ""
                                )
                        }

                        normalized_saved_header = {
                            field:
                                get_saved_header_value(
                                    saved_header_now,
                                    field
                                )
                            for field in [
                                "stavba",
                                "objekt",
                                "cast",
                                "zhotovitel",
                                "objednavatel"
]
                        }

                        if current_header != normalized_saved_header:

                            st.warning(
                                "Hlavičku si zmenila. "
                                "Najprv klikni na "
                                "💾 Uložiť hlavičku projektu."
                            )

                            return

                        final_metadata = {
                            field: {
                                "value":
                                    normalized_saved_header[
                                        field
                                    ]
                            }
                            for field
                            in normalized_saved_header
                        }

                        aggregated_budget_text = (
                            build_aggregated_budget_text(
                                aggregated_budget_rows
                            )
)
                    )

                    excel_bytes = (
                        create_ksp_excel(
                            template_bytes,
                            ksp_rows,
                            final_metadata
                        project_documents = [
                            doc
                            for doc in documents
                            if doc["document_type"]
                            in [
                                "technical_report",
                                "drawing",
                                "other"
                            ]
                        ]

                        ai_documents = (
                            project_documents
                            + [
                                selected_reference
                            ]
)
                    )

                st.session_state[
                    excel_key
                ] = excel_bytes
                        with st.spinner(
                            "Načítavam technickú správu "
                            "a referenčný KSP..."
                        ):

                st.session_state[
                    f"ksp_rows_{project_id}"
                ] = ksp_rows
                            project_text = (
                                build_documents_text(
                                    ai_documents
                                )
                            )

                st.success(
                    "KSP Excel bol vytvorený."
                )
                            project_text += (
                                "\n\n"
                                f"{aggregated_budget_text}"
                            )

                            project_text += (
                                "\n\n"
                                "=================================\n"
                                "DÔLEŽITÉ PRAVIDLO PRE MNOŽSTVÁ\n"
                                "=================================\n"
                                "Množstvá vo výslednom KSP ber "
                                "výhradne z AGREGOVANÝCH POLOŽIEK "
                                "CENOVEJ PONUKY uvedených vyššie. "
                                "Nesčítavaj ich znova, "
                                "neber množstvá z referenčného KSP "
                                "a nevymýšľaj nové množstvá.\n"
                            )

                            project_text += (
                                "\n\n"
                                "=================================\n"
                                "POKYNY POUŽÍVATEĽA\n"
                                "=================================\n"
                                f"{generation_instruction}"
                            )

                        with st.spinner(
                            "AI pripravuje riadky KSP..."
                        ):

                            ksp_rows = (
                                generate_ksp_rows(
                                    project_text
                                )
                            )

                        with st.spinner(
                            "Vytváram Excel podľa mustry..."
                        ):

                            template_bytes = (
                                download_project_file(
                                    selected_template[
                                        "file_path"
                                    ]
                                )
                            )

                            excel_bytes = (
                                create_ksp_excel(
                                    template_bytes,
                                    ksp_rows,
                                    final_metadata
                                )
                            )

                        st.session_state[
                            excel_key
                        ] = excel_bytes

                        st.session_state[
                            f"ksp_rows_{project_id}"
                        ] = ksp_rows

                        st.success(
                            "KSP Excel bol vytvorený."
                        )

# ==================================================
# STIAHNUTIE EXCELU
