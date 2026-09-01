import streamlit as st
from datetime import date

st.set_page_config(
    page_title="KSP Generator",
    page_icon="📋",
    layout="wide"
)

# --------------------------------------------------
# VZHĽAD APLIKÁCIE
# --------------------------------------------------

st.markdown("""
<style>

    .stApp {
        background-color: #f7fbf7;
    }

    h1, h2, h3 {
        color: #1f5f3b;
    }

    div.stButton > button {
        background-color: #2e7d32;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
    }

    div.stButton > button:hover {
        background-color: #256628;
        color: white;
        border: none;
    }

    section[data-testid="stSidebar"] {
        background-color: #eaf5ea;
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


# --------------------------------------------------
# NOVÝ PROJEKT
# --------------------------------------------------

if menu == "Nový projekt":

    st.title("📋 KSP Generator")
    st.subheader("AI generátor kontrolných a skúšobných plánov")

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
            type=["pdf", "docx"]
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

        reference_ksp = st.file_uploader(
            "Referenčný KSP",
            type=["xlsx"]
        )

    st.markdown("### 🤖 AI spracovanie")

    if st.button(
        "Vytvoriť návrh KSP",
        use_container_width=True
    ):
        if not project_name:
            st.warning("Najprv zadaj názov projektu.")
        else:
            st.success(
                f"Projekt '{project_name}' je pripravený na spracovanie."
            )


# --------------------------------------------------
# MOJE PROJEKTY
# --------------------------------------------------

elif menu == "Moje projekty":

    st.title("📁 Moje projekty")

    st.write(
        "Tu budú uložené všetky projekty a ich aktuálny stav."
    )

    projects = [
        {
            "Projekt": "Jahodná – kanalizácia",
            "Stav": "Rozpracované",
            "Posledná zmena": "01.09.2026"
        },
        {
            "Projekt": "Ukážkový projekt",
            "Stav": "Hotové",
            "Posledná zmena": "28.08.2026"
        }
    ]

    st.dataframe(
        projects,
        use_container_width=True,
        hide_index=True
    )

    selected_project = st.selectbox(
        "Vyber projekt",
        [
            "Jahodná – kanalizácia",
            "Ukážkový projekt"
        ]
    )

    if st.button("Otvoriť projekt"):
        st.success(
            f"Otvorený projekt: {selected_project}"
        )


# --------------------------------------------------
# KSP DOKUMENTY
# --------------------------------------------------

elif menu == "KSP dokumenty":

    st.title("📑 KSP dokumenty")

    st.write(
        "Tu budú jednotlivé vytvorené KSP a ich verzie."
    )

    ksp_documents = [
        {
            "Projekt": "Jahodná – kanalizácia",
            "KSP": "KSP kanalizácia",
            "Verzia": "v1",
            "Stav": "Rozpracované"
        },
        {
            "Projekt": "Ukážkový projekt",
            "KSP": "KSP zemné práce",
            "Verzia": "v3",
            "Stav": "Hotové"
        }
    ]

    st.dataframe(
        ksp_documents,
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# AI ASISTENT
# --------------------------------------------------

elif menu == "AI asistent":

    st.title("🤖 AI asistent pre KSP")

    st.write(
        "Tu budeš môcť zadávať pripomienky a meniť vytvorený KSP pomocou AI."
    )

    selected_project = st.selectbox(
        "Projekt",
        [
            "Jahodná – kanalizácia",
            "Ukážkový projekt"
        ]
    )

    user_question = st.text_area(
        "Napíš otázku alebo požiadavku na zmenu",
        placeholder=(
            "napr. Pridaj skúšku zhutnenia po každej vrstve."
        )
    )

    if st.button("Odoslať AI"):
        if not user_question:
            st.warning("Napíš otázku alebo požiadavku.")
        else:
            st.info(
                "AI odpoveď zatiaľ pripojíme v ďalšom kroku."
            )
