import streamlit as st

from database import (
    get_projects,
    get_project_documents,
    upload_project_file,
    download_project_file
)

from file_processing import extract_text_from_file

from ai import (
    improve_technical_procedure,
    generate_ksp_rows
)

from excel_export import create_ksp_excel


def show_project_detail():
    st.title("📂 Detail projektu")

    try:
        projects = get_projects()

        if not projects:
            st.info("Zatiaľ nemáš uložený žiadny projekt.")
            return

        # --------------------------------------------------
        # VÝBER PROJEKTU
        # --------------------------------------------------

        project_names = [
            project["name"]
            for project in projects
        ]

        active_project = st.session_state.get(
            "active_project"
        )

        default_index = 0

        if active_project in project_names:
            default_index = project_names.index(
                active_project
            )

        selected_name = st.selectbox(
            "Vyber projekt",
            project_names,
            index=default_index
        )

        st.session_state[
            "active_project"
        ] = selected_name

        selected_project = next(
            project
            for project in projects
            if project["name"] == selected_name
        )

        project_id = selected_project["id"]

        # --------------------------------------------------
        # EXISTUJÚCE PODKLADY
        # --------------------------------------------------

        st.markdown(
            "### 📄 Existujúce podklady"
        )

        documents = get_project_documents(
            project_id
        )

        if not documents:
            st.info(
                "K projektu zatiaľ nie sú uložené žiadne dokumenty."
            )
        else:
            for doc in documents:
                st.write(
                    f"- {doc['document_type']}: "
                    f"{doc['file_name']}"
                )

        # --------------------------------------------------
        # DOPLNENIE PODKLADOV
        # --------------------------------------------------

        st.markdown(
            "### ➕ Doplniť podklady"
        )

        document_type = st.selectbox(
            "Typ dokumentu",
            [
                "Technická správa",
                "Rozpočet",
                "Výkres",
                "KSP šablóna / mustra",
                "Referenčný KSP – kontroly a skúšky",
                "Iný dokument"
            ]
        )

        new_file = st.file_uploader(
            "Nahraj nový súbor",
            type=[
                "pdf",
                "docx",
                "doc",
                "xlsx",
                "xls",
                "dwg",
                "dxf"
            ]
        )

        if st.button(
            "Uložiť nový podklad",
            use_container_width=True
        ):
            if not new_file:
                st.warning(
                    "Najprv vyber súbor."
                )
                return

            type_map = {
                "Technická správa": "technical_report",
                "Rozpočet": "budget",
                "Výkres": "drawing",
                "KSP šablóna / mustra": "ksp_template",
                "Referenčný KSP – kontroly a skúšky": "reference_ksp",
                "Iný dokument": "other"
            }

            upload_project_file(
                project_id,
                new_file,
                type_map[document_type]
            )

            st.success(
                f"Súbor '{new_file.name}' "
                f"bol pridaný k projektu."
            )

            st.rerun()

        # --------------------------------------------------
        # AI ANALÝZA
        # --------------------------------------------------

        st.markdown(
            "### 🤖 AI analýza projektu"
        )

        instruction = st.text_area(
            "Čo má AI urobiť?",
            value=(
                "Vytvor návrh kontrolného a skúšobného "
                "plánu pre tento projekt. "
                "Referenčný KSP používaj ako záväzný "
                "zdroj kontrol a skúšok. "
                "KSP šablónu / mustru používaj ako vzor "
                "štruktúry výsledného KSP. "
                "Technickú správu, rozpočet a výkresy "
                "použi na určenie konkrétneho rozsahu prác. "
                "Nevymýšľaj nové skúšky, kontroly ani normy. "
                "Ak niečo nie je možné jednoznačne určiť, "
                "označ to ako OVERIŤ."
            ),
            height=170
        )

        if st.button(
            "Analyzovať projekt pomocou AI",
            use_container_width=True
        ):
            if not documents:
                st.warning(
                    "Projekt nemá žiadne podklady na analýzu."
                )
                return

            with st.spinner(
                "Načítavam projektové podklady..."
            ):
                project_text_parts = []

                for doc in documents:
                    file_bytes = download_project_file(
                        doc["file_path"]
                    )

                    extracted_text = extract_text_from_file(
                        doc["file_name"],
                        file_bytes
                    )

                    project_text_parts.append(
                        f"""
--- TYP DOKUMENTU: {doc['document_type']} ---
Súbor: {doc['file_name']}

{extracted_text}
"""
                    )

                project_text = "\n".join(
                    project_text_parts
                )

            with st.spinner(
                "AI pripravuje návrh KSP..."
            ):
                result = improve_technical_procedure(
                    project_text,
                    instruction
                )

            st.session_state[
                f"ksp_ai_result_{project_id}"
            ] = result

            st.session_state[
                f"project_text_{project_id}"
            ] = project_text

        # --------------------------------------------------
        # ZOBRAZENIE AI VÝSLEDKU
        # --------------------------------------------------

        result_key = (
            f"ksp_ai_result_{project_id}"
        )

        if result_key in st.session_state:
            st.markdown(
                "### 📋 Návrh KSP"
            )

            st.write(
                st.session_state[
                    result_key
                ]
            )

        # --------------------------------------------------
        # GENEROVANIE EXCEL KSP
        # --------------------------------------------------

        st.markdown(
            "### 📥 Vygenerovať KSP Excel"
        )

        ksp_templates = [
            doc
            for doc in documents
            if doc["document_type"]
            == "ksp_template"
        ]

        reference_ksps = [
            doc
            for doc in documents
            if doc["document_type"]
            == "reference_ksp"
        ]

        if not ksp_templates:
            st.warning(
                "Projekt nemá nahranú "
                "KSP šablónu / mustru."
            )

        if not reference_ksps:
            st.warning(
                "Projekt nemá nahraný "
                "referenčný KSP."
            )

        if (
            ksp_templates
            and reference_ksps
        ):
            template_names = [
                doc["file_name"]
                for doc in ksp_templates
            ]

            selected_template_name = st.selectbox(
                "KSP šablóna / MUSTRA výsledného Excelu",
                template_names,
                index=len(template_names) - 1
            )

            selected_template = next(
                doc
                for doc in ksp_templates
                if doc["file_name"]
                == selected_template_name
            )

            reference_names = [
                doc["file_name"]
                for doc in reference_ksps
            ]

            selected_reference_name = st.selectbox(
                "Referenčný KSP – zdroj kontrol a skúšok",
                reference_names,
                index=len(reference_names) - 1
            )

            selected_reference = next(
                doc
                for doc in reference_ksps
                if doc["file_name"]
                == selected_reference_name
            )

            st.info(
                f"Výsledný Excel bude vytvorený z mustry: "
                f"**{selected_template['file_name']}**\n\n"
                f"Kontroly a skúšky budú vychádzať z: "
                f"**{selected_reference['file_name']}**"
            )

            if st.button(
                "Vygenerovať KSP Excel",
                use_container_width=True
            ):
                project_text_key = (
                    f"project_text_{project_id}"
                )

                if (
                    project_text_key
                    not in st.session_state
                ):
                    st.warning(
                        "Najprv spusti AI analýzu projektu."
                    )
                    return

                with st.spinner(
                    "AI pripravuje štruktúrované riadky KSP..."
                ):
                    ksp_rows = generate_ksp_rows(
                        st.session_state[
                            project_text_key
                        ]
                    )

                with st.spinner(
                    "Vytváram Excel podľa "
                    "vybratej KSP mustry..."
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
                            ksp_rows
                        )
                    )

                st.session_state[
                    f"ksp_excel_{project_id}"
                ] = excel_bytes

                st.session_state[
                    f"ksp_rows_{project_id}"
                ] = ksp_rows

                st.success(
                    "KSP Excel bol vytvorený "
                    "z vybratej mustry."
                )

        # --------------------------------------------------
        # STIAHNUTIE HOTOVÉHO EXCELU
        # --------------------------------------------------

        excel_key = (
            f"ksp_excel_{project_id}"
        )

        if excel_key in st.session_state:
            st.download_button(
                label="⬇️ Stiahnuť KSP Excel",
                data=st.session_state[
                    excel_key
                ],
                file_name=(
                    f"KSP_{selected_name}.xlsx"
                ),
                mime=(
                    "application/vnd.openxmlformats-"
                    "officedocument.spreadsheetml.sheet"
                ),
                use_container_width=True
            )

    except Exception as e:
        st.error(
            f"Chyba pri načítaní "
            f"detailu projektu: {e}"
        )
