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
        self.feature_config = {}
        self.config_name = "MakeFeatures.json"
        self.feature_data_name = "features.csv"

    def configure_output_freq(self) -> None:
        self.output_freq = st.number_input(
            "Output frequency (Hz)",
            min_value=1,
            help=instruct.FEATURE_FREQUENCY_HELP
        )
    
    def specify_computation_arguments(self, ch_name, computation, key_str='') -> dict:
        """
        Generate the widgets that allow the user to modify the parameters
        going into a feature computation. Sets defaults and gives argument
        descriptions by reading the method argspec and docstring.
        """
        method = cfg.FEATURE_OPTIONS['all'][computation]
        method_name = method.__name__
        method_argspec = self.edf.get_method_args(ch_name, method_name)
        arg_names = method_argspec[0]
        arg_defaults = method_argspec[1]
        arg_descs = [self.extract_arg_desc_from_docstring(method.__doc__, arg)
                      for arg in arg_names]

        arg_vals = {}
        c = st.columns(len(arg_names))
        for i, arg in enumerate(arg_names):
            arg_vals[arg] = c[i].text_input(
                arg,
                value=arg_defaults[i],
                help=arg_descs[i],
                key=f"{key_str}{ch_name}{computation}{arg}"
            )

        return arg_vals
    
    def computation_derivatives(self):
        pass

    def specify_computations(self, ch_name, computation) -> dict:
        """
        Create a popover to contain the configuration of a feature computation.
        """
        comp_config = {'self': [], 'derivative': []}
        with st.popover(f"Configure {computation}", use_container_width=True):
            slf, drv = st.tabs([f"{computation}", f'{computation} Derivatives'])
            with slf:
                n = st.number_input("How many instances?",
                        min_value=1,
                        key=f"{ch_name}{computation}",
                        help=instruct.N_COMPS_HELP
                    )
                st.markdown(f"**Parameters for {computation} Calculation**")
                for i in range(n):
                    st.markdown(f"Instance {i+1}")
                    comp_config['self'].append(
                        self.specify_computation_arguments(ch_name, computation, str(i))
                    )
                    
            deriv_source = self.format_method_arg_labels(argset=comp_config['self'])
            with drv:
                derive_from = st.multiselect(
                    'Derive from',
                    options=deriv_source,
                    key=f"{ch_name}{computation}deriv"
                )
            return comp_config

    def specify_computations_per_channel(self) -> None:
        """
        Create expanders for each specified channel and let user specify which
        features should be computed from it. Modifies self.feature_config to contain
        all the specifications generated by the nested functions.
        """
        st.subheader("Specify first round calculations")
        compute = {}
        for ch_name, ch_type in self.edf.channel_types.items():
            self.feature_config[ch_name] = {}
            with st.expander(f"({ch_type}): {ch_name}", True):
                compute[ch_name] = st.multiselect(
                    "Calculate features",
                    options=cfg.FEATURE_OPTIONS[ch_type],
                    key=f"{ch_name}round1"
                )
                
                for comp in compute[ch_name]:
                    method = cfg.FEATURE_OPTIONS['all'][comp].__name__
                    self.feature_config[ch_name][method] = self.specify_computations(ch_name, comp)
                
                validity = self.validate_channel_configuration(self.feature_config[ch_name])
                
                if not validity[0]:
                    st.error(validity[1])
                else:
                    st.success(validity[1])

    def validate_channel_configuration(self, channel_config) -> tuple[bool, str]:
        if not channel_config:
            return (False, "No features specified. Either remove this channel from the main "
                    "configuration, or specify features to compute from this channel.")
        
        return (True, "Configuration valid")

    def validate_configuration(self) -> tuple[bool, str]:
        validities = []
        for channel_config in self.feature_config.values():
            validities.append(self.validate_channel_configuration(channel_config)[0])

        if not all(validities):
            return (False, "One or more channels have invalid configurations.")
        return (True, "All configurations valid. "
                "Saving this configuration will overwrite the previous.")
    
    # TODO
    def retrieve_configuration(self) -> dict:
        pass

    def save_configuration(self) -> None:
        self.write_configuration(
            analysis=self.analysis,
            config=self.feature_config,
            name=self.config_name
        )
        st.toast(f"Configuration saved.")

    # TODO
    def build_features(self):
        with st.spinner("Calculating features, this may take a while..."):
            pass
            # df.to_csv(f"{}/{self.feature_data_name}")
        st.toast("Features computed and saved to analysis.")

    @staticmethod
    def format_method_arg_labels(argset: list[dict]) -> str:

        def remove_chain(base_str: str, replacements: list):
            removed = base_str
            for r in replacements:
                removed = removed.replace(r, '') 
            return removed
        
        labels = []
        remove = ["'", '"', '{', '}']
        for i, arg_dict in enumerate(argset):
            instance = i+1
            labels.append(
                f"{instance}: ({remove_chain(str(arg_dict), remove)})"
            )
        return labels

    @staticmethod
    def extract_arg_desc_from_docstring(doc_str: str, arg: str) -> str:
        """
        The docstrings of EDF.Channel, .EXGChannel, and .ECGChannel follow a specific
        format such that the description of an argument can be extracted with the following
        string operation.
        """
        desc = doc_str.split(f"{arg}:")[1].split('\n')[0]
        return desc
    