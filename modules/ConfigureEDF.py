import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import modules.instructions as instruct
from utils.SessionBase import SessionBase
from utils.EDF import EDFutils
from streamlit.runtime.uploaded_file_manager import UploadedFile


@st.cache_data(show_spinner=False)
def load_edf_details(path):
    edf = EDFutils(path)
    details = {}
    details['start_ts'] = edf.start_ts
    details['end_ts'] = edf.end_ts
    details['freqs'] = edf.channel_freqs
    details['channels'] = edf.channels
    return details


class ConfigureEDF(SessionBase):
    def __init__(self, analysis) -> None:
        self.analysis = analysis
        self.edfpath = self.get_edf_from_analysis(analysis, path=True)
        self.channel_map = None
        self.time_range = None

    def upload_file(self: UploadedFile) -> None:
        file = st.file_uploader('Drop your EDF file here')
        file_validity = self.validate_file(file)
        if not file_validity[0]:
            st.error(file_validity[1])
        else:
            st.success(file_validity[1])
        if st.button('Save EDF to analysis', disabled=not file_validity[0]):
            with st.spinner('Writing file to disk, this may take a minute...'):
                self.write_edf(file, self.analysis)

        existing_edf = self.get_edf_from_analysis(self.analysis)
        if existing_edf:
            st.warning("An EDF file already exists in this analysis. "
                       "Clicking the save button will overwrite it")
        self.edfpath = self.get_edf_from_analysis(self.analysis, path=True)

    def initialize_edf_properties(self) -> None:
        with st.spinner(f'Reading metadata from EDF, please wait...'):
            self.edf = load_edf_details(self.edfpath)

    def set_time_range(self) -> None:
        with st.expander("Set time range", True):
            start = self.edf['start_ts']
            end = self.edf['end_ts']

            c = st.columns([6, 1, 6])
            c[0].markdown(f"EDF Start Timestamp: `{start}`")
            c[2].write(f"EDF End Timestamp: `{end}`")

            c = st.columns([2, 2, 2, 1, 2, 2, 2])
            start_date = c[0].date_input("Start Date",
                value=start.date())
            start_time = c[1].time_input("Start Time",
                value=start.time(), step=60)
            start_secs = c[2].number_input("Start Seconds",
                value=start.second + start.microsecond/10**6,
                min_value=0.0,
                max_value=60.0,
                step=1e-6,
                format="%.6f")
            
            end_date = c[4].date_input("End Date",
                value=end.date())
            end_time = c[5].time_input("End Time",
                value=end.time(), step=60)
            end_secs = c[6].number_input("End Seconds",
                value=end.second + end.microsecond/10**6,
                min_value=0.0,
                max_value=60.0,
                step=1e-6,
                format="%.6f")
            
        user_start = datetime.combine(start_date, start_time)
        user_start += timedelta(seconds=start_secs) 
        user_end = datetime.combine(end_date, end_time)
        user_end += timedelta(seconds=end_secs)

        self.time_range = (user_start, user_end)
        
    def channel_mapping(self) -> None:
        # TODO: read in existing config

        ch_default = None 
        picked_channels = st.multiselect(
            'What channels will you be using?',
            options=self.edf['channels'],
            default=ch_default
        )
        channel_map = pd.DataFrame(
            picked_channels,
            columns=["ch_name"]
        )
        channel_map["ch_type"] = [None for _ in picked_channels]
        channel_map["ch_freq"] = [self.edf['freqs'][ch] for ch in picked_channels]

        self.channel_map = st.data_editor(
            channel_map,
            column_config={
                "ch_name": st.column_config.TextColumn(
                    "Channel Name",
                    disabled=True
                ),
                "ch_type": st.column_config.SelectboxColumn(
                    "Channel Type",
                    help=instruct.CHANNEL_TYPE_HELP,
                    options=[None, "EEG", "ECG", "Motion", "Other"],
                    required=True
                ),
                "ch_freq": st.column_config.NumberColumn(
                    "Channel Frequency",
                    disabled=True
                )
            },
            use_container_width=True,
            hide_index=True
        )
        if not all(self.channel_map.ch_type):
            st.error("Ensure all channel types are specified")

    # TODO
    def retrieve_configuration(self, filetype) -> None|pd.DataFrame|dict:
        """
        Check if config files exist in the analysis directory and return them.
        Used for loading previous values in config editors.
        """
        config_exists = False
        if config_exists:
            match filetype:
                case "EDFconfig.json":
                    path = ''
                    with open(path) as f:
                        edfconfig = json.load(f)
                    return edfconfig
                case "channel_map.csv":
                    path = ''
                    channel_map = pd.read_csv(path)
                    return channel_map
        else:
            return None

    def construct_configuration(self) -> dict:
        config = {
            'time': {
                'start': self.time_range[0],
                'end': self.time_range[1],
                'tz': None
            },
            'channels': {
                'map': {
                    'EEG': [],
                    'ECG': [],
                    'misc': [],
                    'ignore': []
                },
                'freq': {}
            }
        }
        for _, row in self.channel_map.iterrows():
            label_to_group = {
                'EEG': 'EEG',
                'ECG': 'ECG',
                'Motion': 'misc',
                'Other': 'misc'
            }
            if row['ch_type'] in label_to_group:
                group = label_to_group[row['ch_type']]
            else:
                group = 'ignore'
            config['channels']['map'][group].append(row['ch_name'])
            if row['ch_freq'] not in config['channels']['freq']:
                config['channels']['freq'][row['ch_freq']] = []
            config['channels']['freq'][row['ch_freq']].append(row['ch_name'])
        return config
    
    @staticmethod
    def validate_file(file) -> tuple:
        if file is None:
            return (False, "No file detected (may take a moment even when loading bar is full)")
        ext = file.name.split('.')[-1].lower()
        if not ext == 'edf':
            return (False, f'Only accepts .edf file extension, not "{ext}"')
        else:
            return (True, "Valid file")

    def validate_configuration(self) -> tuple:
        if self.channel_map is None:
            return (False, "`self.channel_map` not found")
        if not all(self.channel_map.ch_type):
            return (False, "Ensure all channel types are specified"
                    'in the "Map Channels" menu')
        if self.time_range[0] > self.time_range[1]:
            return (False, f"Specified start time `{self.time_range[0]}` "
                    "occurs after end time `{self.time_range[1]}`")
        if self.time_range[0] < self.edf['start_ts']:
            return (False, f"Specified start time `{self.time_range[0]}` " 
                    f"occurs before EDF start time `{self.edf['start_ts']}`")
        if self.time_range[1] > self.edf['end_ts']:
            return (False, f"Specified end time `{self.time_range[1]}` "
                    f"occurs after EDF end time `{self.edf['end_ts']}`")
        else:
            return (True, "Configuration valid, please confirm & save (will overwrite previous)")
        
    def save_configuration(self):
        # self.channel_map.to_csv(
        #     f"{self.get_analysis_path()}/channel_map.csv",
        #     index=False
        # )
        self.write_configuration(
            self.construct_configuration(),
            self.analysis,
            name="EDFconfig.json"
        )