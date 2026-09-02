import streamlit as st

from database import (
    get_projects,
    get_project_documents,
    upload_project_file,
    download_project_file,
    delete_project_document
)

from file_processing import extract_text_from_file

from ai import (
    improve_technical_procedure,
    generate_ksp_rows,
    extract_project_metadata
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

        st.session_state["active_project"] = selected_name

        selected_project = next(
            project
            for project in projects
            if project["name"] == selected_name
        )

        project_id = selected_project["id"]

        # --------------------------------------------------
        # EXISTUJÚCE PODKLADY
        # --------------------------------------------------

        st.markdown("### 📄 Existujúce podklady")

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
        # AKTUÁLNA KSP MUSTRA
        # --------------------------------------------------

        st.markdown("### 🧾 Aktuálna KSP mustra")

        ksp_templates = [
            doc
            for doc in documents
            if doc["document_type"] == "ksp_template"
        ]

        current_template = None

        if ksp_templates:
            current_template = ksp_templates[-1]

            st.info(
                f"Aktuálne používaná mustra: "
                f"**{current_template['file_name']}**"
            )
        else:
            st.warning(
                "Projekt zatiaľ nemá KSP mustru."
            )

        # --------------------------------------------------
        # NAHRADENIE KSP MUSTRY
        # --------------------------------------------------

        with st.expander("🔄 Nahradiť KSP mustru"):

            replacement_template = st.file_uploader(
                "Vyber novú KSP mustru",
                type=[
                    "xlsx",
                    "xls"
                ],
                key=f"replace_template_{project_id}"
            )

            if st.button(
                "Nahradiť aktuálnu mustru",
                use_container_width=True
            ):
                if not replacement_template:
                    st.warning(
                        "Najprv vyber novú mustru."
                    )
                    return

                try:
                    upload_project_file(
                        project_id,
                        replacement_template,
                        "ksp_template"
                    )

                    if current_template:
                        delete_project_document(
                            current_template["id"],
                            current_template["file_path"]
                        )

                    st.success(
                        "KSP mustra bola úspešne nahradená."
                    )

                    st.rerun()

                except Exception as e:
                    st.error(
                        f"Chyba pri nahradení mustry: {e}"
                    )

        # --------------------------------------------------
        # DOPLNENIE PODKLADOV
        # --------------------------------------------------

        st.markdown("### ➕ Doplniť podklady")

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

        st.markdown("### 🤖 AI analýza projektu")

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
            st.markdown("### 📋 Návrh KSP")

            st.write(
                st.session_state[
                    result_key
                ]
            )

        # --------------------------------------------------
        # KONTROLA ÚDAJOV HLAVIČKY
        # --------------------------------------------------

        st.markdown(
            "### 🔎 Kontrola údajov hlavičky KSP"
        )

        st.caption(
            "Pre túto kontrolu sa používajú iba "
            "technická správa a rozpočet / cenová ponuka."
        )

        if st.button(
            "Skontrolovať údaje hlavičky",
            use_container_width=True
        ):

            header_documents = [
                doc
                for doc in documents
                if doc["document_type"]
                in [
                    "technical_report",
                    "budget"
                ]
            ]

            if not header_documents:
                st.warning(
                    "Na kontrolu hlavičky chýba "
                    "technická správa alebo rozpočet."
                )

            else:
                with st.spinner(
                    "Načítavam údaje pre hlavičku..."
                ):
                    header_text_parts = []

                    for doc in header_documents:

                        file_bytes = (
                            download_project_file(
                                doc["file_path"]
                            )
                        )

                        extracted_text = (
                            extract_text_from_file(
                                doc["file_name"],
                                file_bytes
                            )
                        )

                        header_text_parts.append(
                            f"""
--- TYP DOKUMENTU: {doc['document_type']} ---
Súbor: {doc['file_name']}

{extracted_text}
"""
                        )

                    header_text = "\n".join(
                        header_text_parts
                    )

                with st.spinner(
                    "Kontrolujem stavbu, objekt, "
                    "zhotoviteľa a objednávateľa..."
                ):
                    metadata = (
                        extract_project_metadata(
                            header_text
                        )
                    )

                st.session_state[
                    f"project_metadata_{project_id}"
                ] = metadata

        metadata_key = (
            f"project_metadata_{project_id}"
        )

        if metadata_key in st.session_state:

            metadata = st.session_state[
                metadata_key
            ]

            st.markdown("#### Nájdené údaje")

            for field, label in [
                ("stavba", "Stavba"),
                ("objekt", "Objekt / SO"),
                ("zhotovitel", "Zhotoviteľ"),
                (
                    "objednavatel",
                    "Objednávateľ / investor"
                )
            ]:

                item = metadata.get(
                    field,
                    {}
                )

                value = item.get(
                    "value",
                    "OVERIŤ"
                )

                status = item.get(
                    "status",
                    "OVERIŤ"
                )

                st.write(
                    f"**{label}:** {value}  \n"
                    f"Kontrola: `{status}`"
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
                "Projekt nemá nahranú KSP šablónu / mustru."
            )

        if not reference_ksps:
            st.warning(
                "Projekt nemá nahraný referenčný KSP."
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

                    excel_bytes = create_ksp_excel(
                        template_bytes,
                        ksp_rows
                    )

                st.session_state[
                    f"ksp_excel_{project_id}"
                ] = excel_bytes

                st.session_state[
                    f"ksp_rows_{project_id}"
                ] = ksp_rows

                st.success(
                    "KSP Excel bol vytvorený."
                )

        # --------------------------------------------------
        # STIAHNUTIE EXCELU
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
            f"Chyba pri načítaní detailu projektu: {e}"
        )
