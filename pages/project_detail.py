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
    generate_ksp_rows,
    extract_project_metadata
)

from excel_export import create_ksp_excel


# --------------------------------------------------
# POMOCNÁ FUNKCIA - NAČÍTANIE TEXTU DOKUMENTOV
# --------------------------------------------------

def build_documents_text(documents):
    """
    Načíta text z vybraných dokumentov projektu.
    """

    text_parts = []

    for doc in documents:

        file_bytes = download_project_file(
            doc["file_path"]
        )

        extracted_text = extract_text_from_file(
            doc["file_name"],
            file_bytes
        )

        text_parts.append(
            f"""
--- TYP DOKUMENTU: {doc['document_type']} ---
Súbor: {doc['file_name']}

{extracted_text}
"""
        )

    return "\n".join(text_parts)


# --------------------------------------------------
# DETAIL PROJEKTU
# --------------------------------------------------

def show_project_detail():

    st.title("📂 Detail projektu")

    try:

        projects = get_projects()

        if not projects:
            st.info(
                "Zatiaľ nemáš uložený žiadny projekt."
            )
            return

        # ==================================================
        # VÝBER PROJEKTU
        # ==================================================

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

        metadata_key = (
            f"project_metadata_{project_id}"
        )

        excel_key = (
            f"ksp_excel_{project_id}"
        )

        # ==================================================
        # EXISTUJÚCE PODKLADY
        # ==================================================

        st.markdown(
            "### 📄 Existujúce podklady"
        )

        documents = get_project_documents(
            project_id
        )

        if not documents:

            st.info(
                "K projektu zatiaľ nie sú uložené "
                "žiadne dokumenty."
            )

        else:

            for doc in documents:

                st.write(
                    f"- {doc['document_type']}: "
                    f"{doc['file_name']}"
                )

        # ==================================================
        # AKTUÁLNA KSP MUSTRA
        # ==================================================

        st.markdown(
            "### 🧾 Aktuálna KSP mustra"
        )

        ksp_templates = [
            doc
            for doc in documents
            if doc["document_type"]
            == "ksp_template"
        ]

        current_template = None

        if ksp_templates:

            current_template = (
                ksp_templates[-1]
            )

            st.info(
                f"Aktuálne používaná mustra: "
                f"**{current_template['file_name']}**"
            )

        else:

            st.warning(
                "Projekt zatiaľ nemá KSP mustru."
            )

        # ==================================================
        # NAHRADENIE KSP MUSTRY
        # ==================================================

        with st.expander(
            "🔄 Nahradiť KSP mustru"
        ):

            replacement_template = (
                st.file_uploader(
                    "Vyber novú KSP mustru",
                    type=[
                        "xlsx",
                        "xls"
                    ],
                    key=(
                        f"replace_template_"
                        f"{project_id}"
                    )
                )
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

                    # Najprv uložíme novú mustru
                    upload_project_file(
                        project_id,
                        replacement_template,
                        "ksp_template"
                    )

                    # Až potom zmažeme starú
                    if current_template:

                        delete_project_document(
                            current_template["id"],
                            current_template[
                                "file_path"
                            ]
                        )

                    # Starý Excel už nie je aktuálny
                    st.session_state.pop(
                        excel_key,
                        None
                    )

                    st.success(
                        "KSP mustra bola úspešne "
                        "nahradená."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Chyba pri nahradení "
                        f"mustry: {e}"
                    )

        # ==================================================
        # DOPLNENIE PODKLADOV
        # ==================================================

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

                "Technická správa":
                    "technical_report",

                "Rozpočet":
                    "budget",

                "Výkres":
                    "drawing",

                "KSP šablóna / mustra":
                    "ksp_template",

                "Referenčný KSP – kontroly a skúšky":
                    "reference_ksp",

                "Iný dokument":
                    "other"
            }

            selected_document_type = (
                type_map[document_type]
            )

            upload_project_file(
                project_id,
                new_file,
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

            st.session_state.pop(
                excel_key,
                None
            )

            st.success(
                f"Súbor '{new_file.name}' "
                f"bol pridaný k projektu."
            )

            st.rerun()

        # ==================================================
        # 1. KONTROLA HLAVIČKY
        # ==================================================

        st.markdown(
            "### 1️⃣ 🔎 Kontrola údajov hlavičky KSP"
        )

        st.caption(
            "AI navrhne údaje podľa podkladov. "
            "Pred vytvorením Excelu ich môžeš "
            "ľubovoľne opraviť."
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
                    "Kontrolujem údaje hlavičky..."
                ):

                    header_text = (
                        build_documents_text(
                            header_documents
                        )
                    )

                    metadata = (
                        extract_project_metadata(
                            header_text
                        )
                    )

                st.session_state[
                    metadata_key
                ] = metadata

                # ------------------------------------------
                # AI HODNOTY PREDVYPLNÍME DO EDITOVATEĽNÝCH POLÍ
                # ------------------------------------------

                for field in [
                    "stavba",
                    "objekt",
                    "cast",
                    "zhotovitel",
                    "objednavatel"
                ]:

                    value = (
                        metadata
                        .get(field, {})
                        .get(
                            "value",
                            "OVERIŤ"
                        )
                    )

                    st.session_state[
                        f"header_{field}_{project_id}"
                    ] = value

        # ==================================================
        # EDITOVATEĽNÁ HLAVIČKA
        # ==================================================

        if metadata_key in st.session_state:

            metadata = (
                st.session_state[
                    metadata_key
                ]
            )

            st.markdown(
                "#### ✏️ Údaje, ktoré sa zapíšu do Excelu"
            )

            st.info(
                "Ak je niečo označené OVERIŤ "
                "alebo je údaj nesprávny, "
                "prepíš ho priamo v poli."
            )

            # ------------------------------------------
            # STAVBA
            # ------------------------------------------

            stavba_info = metadata.get(
                "stavba",
                {}
            )

            st.caption(
                f"AI kontrola: "
                f"{stavba_info.get('status', 'OVERIŤ')} | "
                f"Zdroj: "
                f"{stavba_info.get('source', 'nenájdené')}"
            )

            st.text_input(
                "Stavba",
                key=f"header_stavba_{project_id}"
            )

            # ------------------------------------------
            # OBJEKT
            # ------------------------------------------

            objekt_info = metadata.get(
                "objekt",
                {}
            )

            st.caption(
                f"AI kontrola: "
                f"{objekt_info.get('status', 'OVERIŤ')} | "
                f"Zdroj: "
                f"{objekt_info.get('source', 'nenájdené')}"
            )

            st.text_input(
                "Objekt / SO",
                key=f"header_objekt_{project_id}"
            )

            # ------------------------------------------
            # ČASŤ
            # ------------------------------------------

            cast_info = metadata.get(
                "cast",
                {}
            )

            st.caption(
                f"AI kontrola: "
                f"{cast_info.get('status', 'OVERIŤ')} | "
                f"Zdroj: "
                f"{cast_info.get('source', 'nenájdené')}"
            )

            st.text_input(
                "Časť",
                key=f"header_cast_{project_id}"
            )

            # ------------------------------------------
            # ZHOTOVITEĽ
            # ------------------------------------------

            zhotovitel_info = metadata.get(
                "zhotovitel",
                {}
            )

            st.caption(
                f"AI kontrola: "
                f"{zhotovitel_info.get('status', 'OVERIŤ')} | "
                f"Zdroj: "
                f"{zhotovitel_info.get('source', 'nenájdené')}"
            )

            st.text_input(
                "Zhotoviteľ",
                key=f"header_zhotovitel_{project_id}"
            )

            # ------------------------------------------
            # OBJEDNÁVATEĽ
            # ------------------------------------------

            objednavatel_info = metadata.get(
                "objednavatel",
                {}
            )

            st.caption(
                f"AI kontrola: "
                f"{objednavatel_info.get('status', 'OVERIŤ')} | "
                f"Zdroj: "
                f"{objednavatel_info.get('source', 'nenájdené')}"
            )

            st.text_input(
                "Objednávateľ / investor",
                key=f"header_objednavatel_{project_id}"
            )

        # ==================================================
        # 2. GENEROVANIE KSP EXCEL
        # ==================================================

        st.markdown(
            "### 2️⃣ 📥 Vygenerovať KSP Excel"
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

            # ------------------------------------------
            # VÝBER MUSTRY
            # ------------------------------------------

            template_names = [
                doc["file_name"]
                for doc in ksp_templates
            ]

            selected_template_name = (
                st.selectbox(
                    "KSP šablóna / "
                    "MUSTRA výsledného Excelu",
                    template_names,
                    index=(
                        len(template_names) - 1
                    )
                )
            )

            selected_template = next(
                doc
                for doc in ksp_templates
                if doc["file_name"]
                == selected_template_name
            )

            # ------------------------------------------
            # VÝBER REFERENČNÉHO KSP
            # ------------------------------------------

            reference_names = [
                doc["file_name"]
                for doc in reference_ksps
            ]

            selected_reference_name = (
                st.selectbox(
                    "Referenčný KSP – "
                    "zdroj kontrol a skúšok",
                    reference_names,
                    index=(
                        len(reference_names) - 1
                    )
                )
            )

            selected_reference = next(
                doc
                for doc in reference_ksps
                if doc["file_name"]
                == selected_reference_name
            )

            # ------------------------------------------
            # POKYNY PRE KSP
            # ------------------------------------------

            generation_instruction = (
                st.text_area(
                    "Pokyny pre vytvorenie KSP",
                    value=(
                        "Vytvor KSP pre tento projekt. "
                        "Použi iba kontroly a skúšky "
                        "z vybraného referenčného KSP. "
                        "Projektové podklady použi na "
                        "určenie rozsahu prác, materiálov "
                        "a množstiev. "
                        "Nevymýšľaj nové skúšky ani normy. "
                        "Ak údaj nie je možné určiť, "
                        "označ ho ako OVERIŤ."
                    ),
                    height=150
                )
            )

            st.info(
                f"Výsledný Excel bude vytvorený "
                f"z mustry: "
                f"**{selected_template['file_name']}**"
                f"\n\n"
                f"Kontroly a skúšky budú vychádzať "
                f"z: "
                f"**{selected_reference['file_name']}**"
            )

            # ------------------------------------------
            # GENEROVANIE
            # ------------------------------------------

            if st.button(
                "Vygenerovať KSP Excel",
                use_container_width=True
            ):

                if (
                    metadata_key
                    not in st.session_state
                ):

                    st.warning(
                        "Najprv skontroluj "
                        "údaje hlavičky KSP."
                    )

                    return

                # --------------------------------------
                # FINÁLNA HLAVIČKA PODĽA EDITOVANÝCH POLÍ
                # --------------------------------------

                final_metadata = {
                    "stavba": {
                        "value": st.session_state.get(
                            f"header_stavba_{project_id}",
                            ""
                        )
                    },

                    "objekt": {
                        "value": st.session_state.get(
                            f"header_objekt_{project_id}",
                            ""
                        )
                    },

                    "cast": {
                        "value": st.session_state.get(
                            f"header_cast_{project_id}",
                            ""
                        )
                    },

                    "zhotovitel": {
                        "value": st.session_state.get(
                            f"header_zhotovitel_{project_id}",
                            ""
                        )
                    },

                    "objednavatel": {
                        "value": st.session_state.get(
                            f"header_objednavatel_{project_id}",
                            ""
                        )
                    }
                }

                # --------------------------------------
                # PROJEKTOVÉ PODKLADY PRE AI
                # --------------------------------------

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

                ai_documents = (
                    project_documents
                    + [
                        selected_reference
                    ]
                )

                with st.spinner(
                    "Načítavam projektové podklady..."
                ):

                    project_text = (
                        build_documents_text(
                            ai_documents
                        )
                    )

                    project_text += (
                        "\n\n"
                        "=================================\n"
                        "POKYNY POUŽÍVATEĽA\n"
                        "=================================\n"
                        f"{generation_instruction}"
                    )

                # --------------------------------------
                # HLAVNÉ AI VOLANIE
                # --------------------------------------

                with st.spinner(
                    "AI pripravuje riadky KSP..."
                ):

                    ksp_rows = (
                        generate_ksp_rows(
                            project_text
                        )
                    )

                # --------------------------------------
                # EXCEL
                # --------------------------------------

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
        # ==================================================

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
