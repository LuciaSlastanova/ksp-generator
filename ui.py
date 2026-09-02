import streamlit as st

from database import (
    create_project,
    get_projects,
    upload_project_file,
    get_project_documents,
    download_project_file
)

from ai import improve_technical_procedure
from file_processing import extract_text_from_file

from pages.project_detail import show_project_detail


# --------------------------------------------------
# VZHĽAD APLIKÁCIE
# --------------------------------------------------

def apply_styles():
    st.markdown("""
    <style>

        .stApp {
            background-color: #f7fbf7;
        }

        h1, h2, h3 {
            color: #1f5f3b;
        }

        section[data-testid="stSidebar"] {
            background-color: #eaf5ea;
        }

        div.stButton > button {
            background-color: #2e7d32;
            color: white;
            border-radius: 8px;
            border: none;
            font-weight: 600;
        }

        div.stButton > button:hover {
            background-color: #256628;
            color: white;
        }

        div[data-baseweb="select"] > div {
            border: 2px solid #7fb77e;
            border-radius: 8px;
        }

        div[data-testid="stFileUploader"] {
            border: 1px solid #b8d8b8;
            border-radius: 10px;
            padding: 10px;
            background-color: white;
        }

    </style>
    """, unsafe_allow_html=True)


# --------------------------------------------------
# BOČNÉ MENU
# --------------------------------------------------

def show_sidebar():
    apply_styles()

    with st.sidebar:
        st.title("KSP Generator")

        menu = st.selectbox(
            "Menu",
            [
                "Nový projekt",
                "Moje projekty",
                "Detail projektu",
                "KSP dokumenty",
                "AI asistent"
            ]
        )

    return menu


# --------------------------------------------------
# NAVIGÁCIA
# --------------------------------------------------

def show_page(menu):

    if menu == "Nový projekt":
        show_new_project()

    elif menu == "Moje projekty":
        show_projects()

    elif menu == "Detail projektu":
        show_project_detail()

    elif menu == "KSP dokumenty":
        show_ksp_documents()

    elif menu == "AI asistent":
        show_ai_assistant()


# --------------------------------------------------
# NOVÝ PROJEKT
# --------------------------------------------------

def show_new_project():
    st.title("📋 Nový projekt")

    st.info(
        "Nahraj projektové podklady "
        "a aplikácia pripraví návrh KSP."
    )

    project_name = st.text_input(
        "Názov projektu",
        placeholder="napr. Jahodná – kanalizácia"
    )

    st.markdown(
        "### 📄 Projektové podklady"
    )

    col1, col2 = st.columns(2)

    with col1:

        technical_report = st.file_uploader(
            "Technická správa",
            type=[
                "pdf",
                "docx",
                "doc"
            ]
        )

        budget = st.file_uploader(
            "Rozpočet",
            type=[
                "xlsx",
                "xls"
            ]
        )

    with col2:

        drawings = st.file_uploader(
            "Výkresy",
            type=[
                "pdf",
                "dwg",
                "dxf"
            ],
            accept_multiple_files=True
        )

        ksp_template = st.file_uploader(
            "KSP šablóna / mustra",
            type=[
                "xlsx",
                "xls"
            ]
        )

        reference_ksp = st.file_uploader(
            "Referenčný KSP – kontroly a skúšky",
            type=[
                "xlsx",
                "xls"
            ]
        )

    st.markdown(
        "### 💾 Uloženie projektu"
    )

    if st.button(
        "Vytvoriť projekt",
        use_container_width=True
    ):

        if not project_name:
            st.warning(
                "Zadaj názov projektu."
            )
            return

        try:
            project = create_project(
                project_name
            )

            if not project:
                st.error(
                    "Projekt sa nepodarilo vytvoriť."
                )
                return

            project_id = project["id"]

            if technical_report:
                upload_project_file(
                    project_id,
                    technical_report,
                    "technical_report"
                )

            if budget:
                upload_project_file(
                    project_id,
                    budget,
                    "budget"
                )

            if drawings:
                for drawing in drawings:
                    upload_project_file(
                        project_id,
                        drawing,
                        "drawing"
                    )

            if ksp_template:
                upload_project_file(
                    project_id,
                    ksp_template,
                    "ksp_template"
                )

            if reference_ksp:
                upload_project_file(
                    project_id,
                    reference_ksp,
                    "reference_ksp"
                )

            st.session_state[
                "active_project"
            ] = project_name

            st.success(
                f"Projekt '{project_name}' "
                f"a jeho podklady boli uložené."
            )

        except Exception as e:
            st.error(
                f"Chyba pri vytváraní projektu: {e}"
            )


# --------------------------------------------------
# MOJE PROJEKTY
# --------------------------------------------------

def show_projects():
    st.title("📁 Moje projekty")

    try:
        projects = get_projects()

        if not projects:
            st.info(
                "Zatiaľ nemáš uložený žiadny projekt."
            )
            return

        table_data = []

        for project in projects:
            table_data.append(
                {
                    "Projekt":
                        project["name"],

                    "Stav":
                        project["status"],

                    "Vytvorený":
                        project["createds_at"]
                }
            )

        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True
        )

        project_names = [
            project["name"]
            for project in projects
        ]

        active_project = (
            st.session_state.get(
                "active_project"
            )
        )

        default_index = 0

        if active_project in project_names:
            default_index = (
                project_names.index(
                    active_project
                )
            )

        selected_project = st.selectbox(
            "Vyber projekt",
            project_names,
            index=default_index
        )

        if st.button(
            "Otvoriť projekt",
            use_container_width=True
        ):
            st.session_state[
                "active_project"
            ] = selected_project

            st.success(
                f"Projekt '{selected_project}' "
                f"je vybraný. "
                f"Otvor Detail projektu."
            )

    except Exception as e:
        st.error(
            f"Chyba pri načítaní projektov: {e}"
        )


# --------------------------------------------------
# KSP DOKUMENTY
# --------------------------------------------------

def show_ksp_documents():
    st.title("📑 KSP dokumenty")

    st.info(
        "Tu budú vytvorené KSP "
        "a ich jednotlivé verzie."
    )


# --------------------------------------------------
# AI ASISTENT
# --------------------------------------------------

def show_ai_assistant():
    st.title(
        "🤖 AI asistent pre KSP"
    )

    st.write(
        "Vyber projekt a aplikácia "
        "načíta jeho uložené podklady."
    )

    try:
        projects = get_projects()

        if not projects:
            st.info(
                "Najprv vytvor aspoň jeden projekt."
            )
            return

        project_names = [
            project["name"]
            for project in projects
        ]

        active_project = (
            st.session_state.get(
                "active_project"
            )
        )

        default_index = 0

        if active_project in project_names:
            default_index = (
                project_names.index(
                    active_project
                )
            )

        selected_name = st.selectbox(
            "Projekt",
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

        project_id = (
            selected_project["id"]
        )

        documents = (
            get_project_documents(
                project_id
            )
        )

        if not documents:
            st.warning(
                "K tomuto projektu zatiaľ "
                "nie sú uložené žiadne dokumenty."
            )
            return

        st.markdown(
            "### 📄 Načítané podklady"
        )

        for doc in documents:
            st.write(
                f"- {doc['document_type']}: "
                f"{doc['file_name']}"
            )

        instruction = st.text_area(
            "Čo má AI urobiť?",
            height=150,
            value=(
                "Vytvor návrh KSP pre tento projekt. "
                "Referenčný KSP používaj ako záväzný "
                "zdroj kontrol a skúšok. "
                "KSP šablónu používaj ako vzor štruktúry. "
                "Projektové podklady použi na určenie "
                "konkrétneho rozsahu prác. "
                "Nič nevymýšľaj. "
                "Nejasnosti označ ako OVERIŤ."
            )
        )

        if st.button(
            "Analyzovať projekt pomocou AI",
            use_container_width=True
        ):

            with st.spinner(
                "Načítavam dokumenty projektu..."
            ):
                project_text_parts = []

                for doc in documents:

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
                "AI analyzuje projektové podklady..."
            ):

                result = (
                    improve_technical_procedure(
                        project_text,
                        instruction
                    )
                )

            st.session_state[
                f"ksp_ai_result_{project_id}"
            ] = result

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

    except Exception as e:
        st.error(
            f"Chyba pri AI spracovaní projektu: {e}"
        )
