import streamlit as st

from database import (
    get_projects,
    get_project_documents,
    upload_project_file,
    download_project_file
)

from file_processing import extract_text_from_file
from ai import improve_technical_procedure
