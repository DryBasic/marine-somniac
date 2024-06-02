from utils.SessionBase import SessionBase
from utils.EDF.EDF import EDFutils


class BuildFeatures(SessionBase):
    def __init__(self, build_config: dict) -> None:
        self.build_config = build_config

    def execute_commands(self):
        edf = EDFutils(
            self.get_edf_from_analysis(),
            fetch_metadata=False,
            config=self.get_edfconfig() 
        )
        for cmd in self.commands:
            ch = edf[cmd['channel']]
            ch.run_method(cmd['method'], ch['args'])

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
                    'alias': (f"{name}[0]", 0),
                    'channel': channel,
                    'method': method,
                    'args': {},
                    'is_derived': bool(derived_from)
                })
            else:
                # Configurable methods (have args)
                for i, instance in enumerate(instances):
                    commands.append({
                        'alias': (f"{name}[{i}]", i),
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