import streamlit as st
import config as cfg

PICK_ANALYSIS_HELP = 'You can create an analysis in the "Start New Analysis" page.'
CHANNEL_TYPE_HELP = 'The channel type tells us what features should be built off a given channel.'
FEATURE_FREQUENCY_HELP = "All features genereated herein must be of the same output frequency. " \
                         "This widget is where that output frequency is specified."
N_COMPS_HELP = "You may want to calculate multiple instances of a feature to experiment with different " \
               "parameters like window sizes, etc."

ANALYSIS_NAME = 'This will be a directory name, special characters may be rejected'

def feature_generation():
    # Instruct which feature computations are recommended
    st.markdown('')

def get_started():
    st.subheader('Getting Started')
    st.markdown(
        "Please note, this tool only functions on data of the .edf format. "
        "We have found that most feature computations are more effective on electrophysiological data "
        f"that has already undergone [some degree of processing (ICA)]({cfg.__PAPER_LINK}). "
    )
    st.markdown("**Mapping your files**")
    st.markdown(f"""
        This application needs to know a few details about your data before we can get started
        with your analysis. In the ***{cfg.GET_STARTED}*** page, you can specify things like which channels you'll
        be exploring and letting the application know what they are. Configurations need to be 
        specified for both your EDF data as well as any label data (if you will be training your
        own models).
    """)

    with st.expander("Configuration Summary & File Constraints"):
        st.markdown("""
            **Signal Data (must be EDF)**  
            * Config will specify time bracket of your analysis (needed to line up with your labels)
            * Config will specify what your custom channel names represent (are they ECG, motion data?)
                    
            **Label Data (must be CSV)**
            * All rows should be equally spaced time intervals (ex: each row labels 1 second)
            * Config will specify which column refers to your time interval and your label(s)
        """)

    st.markdown("""        
        You only have to do this once per analysis. If you ever need to edit your configuration, you can 
        simply return to that page, make your edits, and save them.
    """)

def compute_features():
    st.subheader("Computing Features")