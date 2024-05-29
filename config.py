from utils.EDF.EDF import Channel
from utils.EDF.EDF import EXGChannel
from utils.EDF.EDF import ECGChannel


APP_NAME = 'Marine Somniac'
PROJECT_NAME = ''
GET_STARTED = "Create or Edit Analysis"

ANALYSIS_STORE = 'filestore'
__PAPER_LINK = ''


CHANNEL_TYPES = [
    "EEG",
    "ECG",
    "Pressure",
    "ODBA",
    "Gyroscope",
    "Other"
]

BASE_FEATURE_SET = {
    "Pressure": {
        "get_rolling_mean": [{"window_sec": 30, "step_size": 1}],
        "get_rolling_std": [{"window_sec": 30, "step_size": 1}]
    },
    "ODBA": {
        "get_rolling_mean": [{"window_sec": 30, "step_size": 1}],
        "get_rolling_std": [{"window_sec": 30, "step_size": 1}]
    },
    "ODBA": {
        "get_rolling_mean": [{"window_sec": 30, "step_size": 1}],
        "get_rolling_std": [{"window_sec": 30, "step_size": 1}]
    },
    "ECG": {
        "get_heart_rate": [
            {"search_radius": 200, "filter_threshold": 200}
        ]
    },
    "EEG": {
        "get_yasa_welch": [
            {"preset_band_range": "alpha"},
            {"preset_band_range": "beta"},
            {"preset_band_range": "sigma"},
            {"preset_band_range": "theta"},
            {"preset_band_range": "sdelta"},
            {"preset_band_range": "fdelta"},
        ],
        "get_hjorth_mobility": [{}],
        "get_hjorth_complexity": [{}],
        
    }
}
EXTENDED_FEATURE_SET = {
    
}
REFINED_FEATURE_SET = {

}

# Related to Feature Computation
any_feats ={
    # 'Self': Channel.downsample,
    'Mean': Channel.get_rolling_mean,
    'Standard Deviation': Channel.get_rolling_std,
}
exg_only ={
    'Multitaper Band Power': EXGChannel.get_rolling_band_power_multitaper,
    'Zero Crossings': EXGChannel.get_rolling_zero_crossings,
    'Fourier Sum Band Power': EXGChannel.get_rolling_band_power_fourier_sum,
    'Welch Band Power': EXGChannel.get_rolling_band_power_welch
}
ecg_only = {
    'Heart Rate': ECGChannel.get_heart_rate,
}
FEATURE_OPTIONS = {
    'all': {**any_feats, **exg_only, **ecg_only},
    'EEG': {**any_feats, **exg_only},
    'ECG': {**any_feats, **exg_only, **ecg_only},
    'Pressure': {**any_feats},
    'ODBA': {**any_feats},
    'Gyroscope': {**any_feats},
    'Other': {**any_feats}
}
