import streamlit as st
import os
import pandas as pd
import modules.instructions as instruct
from modules.ConfigureSession import SessionConfig
from utils.EDF.EDF import EDFutils, Channel
from utils.EDF.Epoch import Epoch
from utils.EDF.SpectralDensity import SpectralDensity
from utils.PlottingUtils import PlottingUtils


class BuildFeatures(SessionConfig, PlottingUtils):
    def __init__(self, analysis, build_config: dict) -> None:
        self.analysis = analysis
        self.build_config = build_config
        self.derivand_store = {}
        self.feature_store_name = 'feature_store'

    def execute_all_commands(self):
        edf = EDFutils(
            self.get_edf_from_analysis(),
            fetch_metadata=False,
            config=self.get_edfconfig() 
        )
        loading_bar = st.progress(0, "Calcuting features, please wait...")
        for i, cmd in enumerate(self.commands):
            loading_bar.progress(i/len(self.commands), 
                f"Calculating {cmd['alias']} (feature {i+1} of {len(self.commands)}), please wait...")
            ch = edf[cmd['channel']]
            if cmd['is_derived']:
                len_self = len(cmd['alias'].split('.')[-1])+1
                derivand_name = cmd['alias'][:-len_self]
            else: 
                derivand_name = None
            feature = self.execute_command(ch, cmd, derivand_name)
            self.save_feature(feature, specs=cmd)
        loading_bar.empty()
        st.success("Feature calculation successful!")
            
    def execute_command(self, root_obj, command, derivand_name=None) -> dict:
        if not command['is_derived']:
            feature = root_obj.run_method(command['method'], command['args'])
        else:
            args = {} if command['args'] == [] else command['args']
            derivand = self.derivand_store[derivand_name]
            feature = derivand.run_method(command['method'], args)

        if not isinstance(feature, dict):
            self.derivand_store[command['alias']] = feature
            if issubclass(feature.__class__, Channel):
                feature = feature.to_DataFrame()
            elif isinstance(feature, Epoch):
                feature = pd.DataFrame.from_dict({'epoch': feature.times})
            elif isinstance(feature, SpectralDensity):
                feature = feature.make_dataframe(feature.welches)
            else:
                raise TypeError(f"Feature, {command['alias']}, of type: {type(feature)} not expected.")
        else:
            feature = derivand.make_dataframe(feature)
        return feature
    
    def save_feature(self, feature_df: pd.DataFrame, specs: dict) -> None:
        parent = self.get_analysis_path()
        if self.feature_store_name not in os.listdir(parent):
            os.mkdir(f"{parent}/{self.feature_store_name}")
        feature_df.to_csv(f"{parent}/{self.feature_store_name}/{specs['alias']}.csv", index=False)

    def compile_commands(self) -> None:
        self.commands = self.flatten_configuration()

    def flatten_configuration(self) -> list[dict]:
        commands = []
        for channel, method_configs in self.build_config.items():
            commands += self.flatten_method_config(channel, method_configs)
        return commands

    def flatten_method_config(self, channel:str, method_configs:dict, derived_from='') -> list[dict]:
        commands = []
        for method, instances in method_configs.items():
            derived_tag = derived_from+'.' if derived_from else ''
            name = f"{channel}.{derived_tag}{method}"
            if not instances:
                # Non-configurable methods (no args)
                commands.append({
                    'alias': f"{name}[0]",
                    'channel': channel,
                    'method': method,
                    'args': {},
                    'is_derived': bool(derived_from)
                })
            else:
                # Configurable methods (have args)
                for i, instance in enumerate(instances):
                    commands.append({
                        'alias': f"{name}[{i}]",
                        'channel': channel,
                        'method': method,
                        'args': instance['args'],
                        'is_derived': bool(derived_from)
                    })
                    if 'derived' in instance:
                        ddfrom = f"{derived_tag}{method}[{i}]"
                        dcommands = self.flatten_method_config(
                            channel, instance['derived'], derived_from=ddfrom
                        )
                        commands += dcommands
        return commands
    
    def configure_output_freq(self) -> None:
        self.output_freq = st.number_input(
            "Output frequency (Hz)",
            min_value=1,
            help=instruct.FEATURE_FREQUENCY_HELP
        )
    
    def visualize_feature(self):
        opts = ['.'.join(i.split('.')[:-1]) 
                for i in os.listdir(self.get_file_from_analysis(
                    self.feature_store_name
                ))]
        pick = st.selectbox(
            "Select computed features",
            options=['']+opts
        )
        if pick:
            parent = f"{self.get_analysis_path()}/{self.feature_store_name}"
            df = pd.read_csv(f"{parent}/{pick}.csv")
            if len(df) > 10_000:
                og_len = len(df)
                step = len(df)//10_000
                df = df.iloc[::step]
                st.write(f"Data is too large to plot ({og_len} points). "
                         f"Downsampling to {len(df)} points")
            plt = st.radio('', ['line', 'scatter'], horizontal=True)
            st.plotly_chart(self.plot_feature(df, plot=plt), use_container_width=True)

3_600_001