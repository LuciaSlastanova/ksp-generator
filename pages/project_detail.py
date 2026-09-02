import streamlit as st

from database import (
    get_projects,
    get_project_documents,
    upload_project_file,
    download_project_file
)

from file_processing import extract_text_from_file
from ai import improve_technical_procedure


def show_project_detail():
    st.title("📂 Detail projektu")

    try:
        projects = get_projects()

        if not projects:
            st.info("Zatiaľ nemáš uložený žiadny projekt.")
            return

        project_names = [p["name"] for p in projects]

        active_project = st.session_state.get("active_project")

        default_index = 0

        if active_project in project_names:
            default_index = project_names.index(active_project)

        selected_name = st.selectbox(
            "Vyber projekt",
            project_names,
            index=default_index
        )

        selected_project = next(
            p for p in projects
            if p["name"] == selected_name
        )

        project_id = selected_project["id"]

        # ------------------------------------------
        # EXISTUJÚCE PODKLADY
        # ------------------------------------------

        st.markdown("### 📄 Existujúce podklady")

        documents = get_project_documents(project_id)

        if not documents:
            st.info(
                "K projektu zatiaľ nie sú uložené žiadne dokumenty."
            )

        else:
            for doc in documents:
                st.write(
                    f"- {doc['document_type']}: {doc['file_name']}"
                )

        # ------------------------------------------
        # DOPLNENIE NOVÉHO PODKLADU
        # ------------------------------------------

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
                st.warning("Najprv vyber súbor.")
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
                f"Súbor '{new_file.name}' bol pridaný k projektu."
            )

            st.rerun()

        # ------------------------------------------
        # AI ANALÝZA
        # ------------------------------------------

        st.markdown("### 🤖 AI analýza projektu")

        instruction = st.text_area(
            "Čo má AI urobiť?",
            value=(
                "Vytvor návrh kontrolného a skúšobného plánu pre tento projekt. "
                "Vychádzaj z technickej správy, rozpočtu, výkresov a "
                "referenčného KSP. KSP šablónu používaj ako vzor štruktúry. "
                "Nevymýšľaj normy ani skúšky, ktoré nie sú podložené dokumentmi. "
                "Ak niečo nie je možné určiť, označ to ako OVERIŤ."
            ),
            height=150
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

            st.session_state["ksp_ai_result"] = result

        # ------------------------------------------
        # ZOBRAZENIE AI VÝSLEDKU
        # ------------------------------------------

        if "ksp_ai_result" in st.session_state:
            st.markdown("### 📋 Návrh KSP")

            st.write(
                st.session_state["ksp_ai_result"]
            )

    except Exception as e:
        st.error(
            f"Chyba pri načítaní detailu projektu: {e}"
        )
