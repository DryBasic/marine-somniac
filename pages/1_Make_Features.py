import streamlit as st
from modules.MakeFeatures import MakeFeatures
from modules.ConfigureSession import SessionConfig
import modules.instructions as instruct
import config as cfg

st.set_page_config(
    page_title=f"{cfg.APP_NAME}: Feature Builder",
    initial_sidebar_state='expanded',
    layout='wide'
)
session = SessionConfig()

st.title('Compute Features')
instruct.feature_generation()

validity = session.validate_analysis(modes=['edfconfig'])
if not validity[0]:
    st.error(validity[1])
else:
    page = MakeFeatures(session.analysis)
    page.configure_()
    page.specify_computations()
