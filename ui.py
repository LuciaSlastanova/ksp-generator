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
        :root {
            --bg: #0f2347;
            --bg-deep: #0a1730;
            --panel: rgba(20, 47, 86, 0.88);
            --panel-soft: rgba(27, 58, 103, 0.78);
            --border: rgba(121, 157, 220, 0.35);
            --text: #f7f9ff;
            --muted: #b8c7e6;
            --blue: #3f7cff;
            --violet: #7b5cff;
            --pink: #ec4899;
            --orange: #ff9f43;
            --cyan: #2dd4ff;
        }

        /* Hlavná plocha */
        .stApp {
            background:
                radial-gradient(circle at 80% 0%, rgba(255, 159, 67, 0.10), transparent 24%),
                radial-gradient(circle at 62% 10%, rgba(123, 92, 255, 0.14), transparent 30%),
                linear-gradient(135deg, #10284f 0%, #102349 48%, #0b1a36 100%);
            color: var(--text);
        }

        .block-container {
            max-width: 1500px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        /* Nadpisy */
        h1, h2, h3 {
            color: var(--text) !important;
            letter-spacing: -0.02em;
        }

        h1 {
            font-weight: 800 !important;
        }

        p, label, .stMarkdown {
            color: var(--text);
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background:
                radial-gradient(circle at 20% 90%, rgba(123, 92, 255, 0.22), transparent 30%),
                linear-gradient(180deg, #0a1b38 0%, #0b2142 55%, #09162e 100%);
            border-right: 1px solid rgba(127, 162, 219, 0.22);
        }

        section[data-testid="stSidebar"] > div {
            padding-top: 1.25rem;
        }

        section[data-testid="stSidebar"] h1 {
            font-size: 1.65rem !important;
            margin-bottom: 0.2rem;
        }

        /* Input */
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea {
            background: rgba(9, 27, 58, 0.72) !important;
            color: #ffffff !important;
            border: 1px solid rgba(110, 150, 220, 0.55) !important;
            border-radius: 12px !important;
        }

        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus {
            border-color: #7b5cff !important;
            box-shadow: 0 0 0 1px rgba(123, 92, 255, 0.40) !important;
        }

        /* Selectbox */
        div[data-baseweb="select"] > div {
            background: rgba(12, 32, 67, 0.90) !important;
            color: white !important;
            border: 1px solid rgba(103, 142, 210, 0.52) !important;
            border-radius: 11px !important;
        }

        /* File uploader - zámerne jednoduchý */
        div[data-testid="stFileUploader"] {
            border: 1px solid rgba(106, 147, 214, 0.42);
            border-radius: 14px;
            padding: 0.55rem 0.75rem 0.35rem 0.75rem;
            background: rgba(27, 58, 103, 0.45);
            box-shadow: none;
        }

        div[data-testid="stFileUploader"] section {
            background: rgba(17, 42, 78, 0.52) !important;
            border: 1px dashed rgba(127, 162, 219, 0.38) !important;
            border-radius: 10px !important;
            padding: 0.55rem !important;
        }

        div[data-testid="stFileUploader"] button {
            background: #f8fafc !important;
            color: #15233e !important;
            border: 1px solid #d7dfec !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            box-shadow: none !important;
        }

        /* Tlačidlá */
        div.stButton > button {
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.14) !important;
            border-radius: 11px !important;
            font-weight: 700 !important;
            background: linear-gradient(
                90deg,
                #ff9f43 0%,
                #f43f5e 28%,
                #c43be4 62%,
                #3f6cf5 100%
            ) !important;
            box-shadow: 0 8px 22px rgba(34, 63, 128, 0.24);
            transition: all 0.18s ease;
        }

        div.stButton > button:hover {
            transform: translateY(-1px);
            filter: brightness(1.05);
            border-color: rgba(255, 255, 255, 0.30) !important;
        }

        /* Info / success / warning boxy */
        div[data-testid="stAlert"] {
            border-radius: 13px;
            border: 1px solid rgba(106, 147, 214, 0.30);
            background: rgba(24, 55, 101, 0.70);
            color: white;
        }

        /* Dataframe */
        div[data-testid="stDataFrame"] {
            border: 1px solid rgba(106, 147, 214, 0.30);
            border-radius: 14px;
            overflow: hidden;
        }

        /* Jemná karta okolo hlavných sekcií cez HTML utility triedy */
        .ksp-hero {
            padding: 1.35rem 1.55rem;
            margin-bottom: 1.15rem;
            border-radius: 18px;
            border: 1px solid rgba(115, 153, 218, 0.34);
            background:
                radial-gradient(circle at 86% 24%, rgba(255, 159, 67, 0.18), transparent 20%),
                radial-gradient(circle at 72% 8%, rgba(236, 72, 153, 0.15), transparent 24%),
                linear-gradient(120deg, rgba(19, 49, 93, 0.94), rgba(13, 34, 69, 0.90));
            box-shadow: 0 12px 34px rgba(4, 16, 39, 0.18);
        }

        .ksp-hero-title {
            font-size: clamp(2.1rem, 4vw, 3.55rem);
            font-weight: 850;
            line-height: 1;
            margin: 0;
            color: white;
        }

        .ksp-gradient-text {
            background: linear-gradient(90deg, #ff9f43, #fb4667, #d23be7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .ksp-hero-subtitle {
            color: #d9e3f7;
            font-size: 1.03rem;
            margin-top: 0.55rem;
            margin-bottom: 0;
        }

        .ksp-section-title {
            margin-top: 1.35rem;
            padding: 0.1rem 0 0.55rem 0;
            font-size: 1.42rem;
            font-weight: 800;
            color: #ffffff;
        }

        .ksp-mini-label {
            color: #9fb2d6;
            font-size: 0.88rem;
            letter-spacing: 0.01em;
        }

        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
        }

        ::-webkit-scrollbar-thumb {
            background: #38558a;
            border-radius: 10px;
        }
    </style>
    """, unsafe_allow_html=True)


# --------------------------------------------------
# BOČNÉ MENU
# --------------------------------------------------

def show_sidebar():
    apply_styles()

    with st.sidebar:
        st.markdown(
            """
            <div style="padding:0.25rem 0 1.0rem 0;">
                <div style="font-size:1.75rem;font-weight:850;line-height:1;">
                    <span style="background:linear-gradient(90deg,#ff9f43,#fb4667,#d23be7);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">KSP</span>
                    <span style="color:white;"> Generator</span>
                </div>
                <div style="color:#9fb2d6;font-size:0.82rem;margin-top:0.45rem;">
                    Kontroly. Skúšky. Projekty.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

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
    st.markdown(
        """
        <div class="ksp-hero">
            <div class="ksp-hero-title">
                Nový <span class="ksp-gradient-text">projekt</span>
            </div>
            <div class="ksp-hero-subtitle">
                Nahraj projektové podklady a aplikácia pripraví návrh KSP.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    project_name = st.text_input(
        "Názov projektu",
        placeholder="napr. Jahodná – kanalizácia"
    )

    st.markdown(
        '<div class="ksp-section-title">📄 Projektové podklady</div>',
        unsafe_allow_html=True
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
        '<div class="ksp-section-title">💾 Uloženie projektu</div>',
        unsafe_allow_html=True
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
