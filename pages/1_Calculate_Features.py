import streamlit as st
from modules.MakeFeatures import MakeFeatures
from modules.ConfigureSession import SessionConfig
import modules.instructions as instruct
from config.meta import APP_NAME

st.set_page_config(
    page_title=f"{APP_NAME}: Feature Builder",
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


    st.radio(
        "Choose a starting point",
        options=["Custom", 'Base Model', 'Extended Model', 'Refined Model'],
        horizontal=True
    )
    conf, build = st.tabs(['Configure', 'Build & Explore Features'])

    with conf:
        page.specify_methods_per_channel()

        valid = page.validate_all_configurations()
        if not valid[0]:
            st.error(valid[1])
        else:
            st.success(valid[1])

        view_config = st.container()
        if st.button("Save Configuration", disabled=not valid[0], use_container_width=True):
            page.save_configuration()


    with view_config.expander('View Current Configuration'):
        st.write(page.feature_config)