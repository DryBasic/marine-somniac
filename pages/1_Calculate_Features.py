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


@st.experimental_dialog(f'Feature Configuration for "{session.analysis}"')
def show_config(config):
    st.write(config)


st.title('Compute Features')
instruct.feature_generation()

validity = session.validate_analysis(modes=['edfconfig'])
if not validity[0]:
    st.error(validity[1])
else:
    page = MakeFeatures(session.analysis)
    page.configure_output_freq()

    starting_point = st.radio(
        "Choose a starting point",
        options=["Saved configuration", "From scratch", "All possible", 'Base Model', 'Extended Model', 'Refined Model'],
        horizontal=True
    )
    conf, build = st.tabs(['Configure', 'Build & Explore Features'])

    with conf:
        view_config = st.container()
        page.specify_methods_per_channel(starting_point)

        valid = page.validate_all_configurations()
        if not valid[0]:
            st.error(valid[1])
        else:
            st.success(valid[1])

        if st.button("Save Configuration", disabled=not valid[0], use_container_width=True):
            page.save_configuration()

    with view_config:
        if st.button("View current configuration", use_container_width=True):
            show_config(page.feature_config)



