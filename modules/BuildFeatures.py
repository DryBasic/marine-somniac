import streamlit as st
from modules.ConfigureSession import SessionConfig
from utils.EDF.EDF import EDFutils, Channel
from utils.EDF.Epoch import Epoch
from utils.EDF.SpectralDensity import SpectralDensity


class BuildFeatures(SessionConfig):
    def __init__(self, analysis, build_config: dict) -> None:
        self.analysis = analysis
        self.build_config = build_config
        self.feature_store = {}
        self.derivand_store = {}

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
            self.feature_store[cmd['alias']] = self.execute_command(ch, cmd, derivand_name)
            st.write(cmd['alias'])
            
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
                feature = feature.signal
            elif isinstance(feature, Epoch):
                feature = feature.times
            elif isinstance(feature, SpectralDensity):
                feature = feature.welches
            else:
                raise TypeError(f"Feature, {command['alias']}, of type: {type(feature)} not expected.")
        return feature

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