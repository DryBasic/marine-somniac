import streamlit as st
from modules.ConfigureSession import SessionConfig
import config as cfg

st.set_page_config(
    page_title=f"{cfg.APP_NAME}: Download Results",
    initial_sidebar_state='expanded',
    layout='wide'
)
session = SessionConfig()

st.warning("Please note that EDF files cannot be redownloaded.")
if session.analysis:
    for file in session.get_analysis_files():
        if file.split(".")[-1].lower() != 'edf':
            fpath = session.get_file_from_analysis(file)
            with open(fpath) as f:
                f_bytes = f.read()
            st.download_button(
                f"Download {file}",
                data=f_bytes,
                file_name=file
            )