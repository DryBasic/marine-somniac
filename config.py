from utils.EDF.EDF import Channel
from utils.EDF.EDF import EXGChannel
from utils.EDF.EDF import ECGChannel

APP_NAME = 'Marine Somniac'
PROJECT_NAME = ''

ANALYSIS_STORE = 'filestore'

GET_STARTED = "Create or Edit Analysis"



# Related to Feature Computation
any_feats ={
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

# any_feats ={
#     'Mean': 'get_rolling_mean',
#     'Standard Deviation': 'get_rolling_std',
# }
# exg_only ={
#     'Multitaper Band Power': 'get_rolling_band_power_multitaper',
#     'Zero Crossings': 'get_rolling_zero_crossings',
#     'Fourier Sum Band Power': 'get_rolling_band_power_fourier_sum',
#     'Welch Band Power': 'get_rolling_band_power_welch'
# }
# ecg_only = {
#     'Heart Rate': 'get_heart_rate',
# }
FEATURE_OPTIONS = {
    'all': {**any_feats, **exg_only, **ecg_only},
    'EEG': {**any_feats, **exg_only},
    'ECG': {**any_feats, **exg_only, **ecg_only},
    'Motion': {**any_feats},
    'Other': {**any_feats}
}
