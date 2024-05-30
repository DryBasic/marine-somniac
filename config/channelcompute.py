from utils.EDF.EDF import Channel
from utils.EDF.EDF import EXGChannel
from utils.EDF.EDF import ECGChannel

CHANNEL_TYPES = [
    "EEG",
    "ECG",
    "Pressure",
    "ODBA",
    "Gyroscope",
    "Other"
]
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