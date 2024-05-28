import streamlit as st
import modules.instructions as instruct
from utils.EDF.EDF import EDFutils
from modules.ConfigureSession import SessionConfig
from config import *

st.set_page_config(
    page_title=APP_NAME,
    initial_sidebar_state='expanded',
    layout='wide'
)
session = SessionConfig()
SessionConfig.insert_logo()

st.title('Compute Features')
instruct.feature_generation()

validity = session.validate_analysis(modes=['edfconfig'])
if not validity[0]:
    st.error(validity[1])
else:
    edf = EDFutils(
        session.get_edf_from_analysis(),
        fetch_metadata=False,
        config=session.get_edfconfig()
    )

