import streamlit as st

from database import create_project, get_projects
from ai import improve_technical_procedure


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


def show_sidebar():
    apply_styles()

    with st.sidebar:
        st.title("KSP Generator")

        menu = st.selectbox(
            "Menu",
            [
                "Nový projekt",
                "Moje projekty",
                "KSP dokumenty",
                "AI asistent"
            ]
        )

    return menu


def show_page(menu):
    if menu == "Nový projekt":
        show_new_project()

    elif menu == "Moje projekty":
        show_projects()

    elif menu == "KSP dokumenty":
        show_ksp_documents()

    elif menu == "AI asistent":
        show_ai_assistant()


def show_new_project():
    st.title("📋 Nový projekt")

    st.info(
        "Nahraj projektové podklady a aplikácia pripraví návrh KSP."
    )

    project_name = st.text_input(
        "Názov projektu",
        placeholder="napr. Jahodná – kanalizácia"
    )

    st.markdown("### 📄 Projektové podklady")

    col1, col2 = st.columns(2)

    with col1:
        technical_report = st.file_uploader(
            "Technická správa",
            type=["pdf", "docx", "doc"]
        )

        budget = st.file_uploader(
            "Rozpočet",
            type=["xlsx", "xls"]
        )

    with col2:
        drawings = st.file_uploader(
            "Výkresy",
            type=["pdf"],
            accept_multiple_files=True
        )
        
        ksp_template = st.file_uploader(
           "KSP šablóna / mustra",
           type=["xlsx", "xls"]
        )        

        reference_ksp = st.file_uploader(
            "Referenčný KSP",
            type=["xlsx"]
        )

    if st.button(
        "Vytvoriť projekt",
        use_container_width=True
    ):
        if not project_name:
            st.warning("Zadaj názov projektu.")

        else:
            try:
                create_project(project_name)

                st.success(
                    f"Projekt '{project_name}' bol uložený do databázy."
                )

            except Exception as e:
                st.error(
                    f"Chyba pri ukladaní projektu: {e}"
                )


def show_projects():
    st.title("📁 Moje projekty")

    try:
        projects = get_projects()

        if not projects:
            st.info("Zatiaľ nemáš uložený žiadny projekt.")

        else:
            table_data = []

            for project in projects:
                table_data.append(
                    {
                        "Projekt": project["name"],
                        "Stav": project["status"],
                        "Vytvorený": project["createds_at"]
                    }
                )

            st.dataframe(
                table_data,
                use_container_width=True,
                hide_index=True
            )

    except Exception as e:
        st.error(
            f"Chyba pri načítaní projektov: {e}"
        )


def show_ksp_documents():
    st.title("📑 KSP dokumenty")

    st.info(
        "Tu budú vytvorené KSP a ich jednotlivé verzie."
    )


def show_ai_assistant():
    st.title("🤖 AI asistent pre KSP")

    st.write(
        "Vlož technologický postup alebo časť KSP a napíš, čo chceš zmeniť."
    )

    procedure_text = st.text_area(
        "Pôvodný technologický postup / časť KSP",
        height=250,
        placeholder=(
            "Sem vlož napríklad postup uloženia kanalizačného potrubia..."
        )
    )

    instruction = st.text_area(
        "Čo má AI upraviť?",
        height=120,
        placeholder=(
            "napr. Skontroluj technologické poradie, "
            "doplň chýbajúce kontroly a skúšky."
        )
    )

    if st.button(
        "Upraviť pomocou AI",
        use_container_width=True
    ):
        if not procedure_text:
            st.warning(
                "Najprv vlož technologický postup."
            )

        elif not instruction:
            st.warning(
                "Napíš, čo má AI upraviť."
            )

        else:
            try:
                with st.spinner(
                    "AI spracováva technologický postup..."
                ):
                    result = improve_technical_procedure(
                        procedure_text,
                        instruction
                    )

                st.markdown("### Návrh AI")

                st.write(result)

            except Exception as e:
                st.error(
                    f"Chyba pri AI spracovaní: {e}"
                )
