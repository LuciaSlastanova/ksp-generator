import streamlit as st
from ui import show_sidebar, show_page

st.set_page_config(
    page_title="KSP Generator",
    page_icon="📋",
    layout="wide"
)

menu = show_sidebar()
show_page(menu)
