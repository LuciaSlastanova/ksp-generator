import streamlit as st
from database import create_project

from ui import show_sidebar, show_page

st.set_page_config(
    page_title="KSP Generator",
    page_icon="📋",
    layout="wide"
)

menu = show_sidebar()
show_page(menu)
