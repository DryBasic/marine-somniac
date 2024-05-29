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
    page.configure_output_freq()
    page.specify_computations_per_channel()

    valid = page.validate_configuration()
    if not valid[0]:
        st.error(valid[1])
    else:
        st.success(valid[1])

    if st.button("Save Configuration & Build Features", disabled=not valid[0]):
        page.save_configuration()
        page.build_features()

    st.divider()
    with st.expander('View Configuration'):
        st.write(page.feature_config)