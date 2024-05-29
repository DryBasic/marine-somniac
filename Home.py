import streamlit as st
from modules.ConfigureSession import SessionConfig
import modules.instructions as instruct
import config as cfg

st.set_page_config(
    page_title=cfg.APP_NAME,
    initial_sidebar_state='expanded',
    layout='centered',
    page_icon='assets/logo_dark.jpeg'
)
SessionConfig.initialize_session()

title, image = st.columns([4,2])
with title:
    st.title(cfg.APP_NAME)
    st.subheader('Sleep scoring for our aquatic pals')
with image:
    SessionConfig.insert_logo(sidebar=False)


st.markdown(
    f"Welcome to {cfg.APP_NAME}! This is a tool for partially automating sleep stage scoring. "
    "While this app was built with Northern elephant seals in mind, many utilities are "
    "generalizeable to other organisms, namely the computation of aggregate/windowed features "
    "from electrophysiological data (EEG, ECG) such as frequency power or heart rate."
)
st.markdown("""
    This tool will save your uploaded data to a remote server on which all computations will be 
    performed.
""")
instruct.get_started()
instruct.compute_features()

