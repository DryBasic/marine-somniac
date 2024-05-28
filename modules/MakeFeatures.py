import streamlit as st
import pandas as pd
import modules.instructions as instruct
from utils.EDF.EDF import EDFutils
from modules.ConfigureSession import SessionConfig
import config as cfg


class MakeFeatures(SessionConfig):
    def __init__(self, analysis) -> None:
        self.analysis = analysis
        self.output_freq = None
        self.edf = EDFutils(
            self.get_edf_from_analysis(),
            fetch_metadata=False,
            config=self.get_edfconfig() 
        )

    def configure_(self) -> None:
        self.output_freq = st.number_input(
            "Output frequency (Hz)",
            min_value=1,
            help=instruct.FEATURE_FREQUENCY_HELP
        )

    def configure_channel_method(self, ch_name, computation):
        method = cfg.FEATURE_OPTIONS['all'][computation]
        method_name = method.__name__
        method_argspec = self.edf.get_method_args(ch_name, method_name)
        arg_names=method_argspec[0]
        arg_defaults=method_argspec[1]

        df = pd.DataFrame(
            data=[
                [method_name]+[i for i in arg_defaults]
            ],
            columns=['']+arg_names
        )
        editor = st.data_editor(df,
            use_container_width=True,
            hide_index=True
        )
        return editor

    def computation_popover(self, ch_name, computation):
        with st.popover(f"Configure {computation}", use_container_width=True):
            n = st.number_input("How many instances?",
                    min_value=1,
                    key=f"{ch_name}{computation}",
                    help=instruct.N_COMPS_HELP
                )
            
            self.configure_channel_method(ch_name, computation)
                
            st.divider()
            derivatives = st.multiselect(
                'Calculate derivate features',
                options=cfg.FEATURE_OPTIONS['Other'],
                key=f"{ch_name}deriv"
            )

    def specify_computations(self):
        st.subheader("Specify first round calculations")
        compute = {}
        for ch_name, ch_type in self.edf.channel_types.items():
            with st.expander(f"({ch_type}): {ch_name}", True):
                compute[ch_name] = st.multiselect(
                    "Calculate features",
                    options=cfg.FEATURE_OPTIONS[ch_type],
                    key=f"{ch_name}round1"
                )

                for calc in compute[ch_name]:
                    self.computation_popover(ch_name, calc)
                
                st.divider()

