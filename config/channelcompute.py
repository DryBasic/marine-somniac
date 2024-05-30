from utils.EDF.EDF import Channel
from utils.EDF.EDF import EXGChannel
from utils.EDF.EDF import ECGChannel
from utils.EDF.Epoch import Epoch

CHANNEL_TYPES = [
    "EEG",
    "ECG",
    "Pressure",
    "ODBA",
    "Gyroscope",
    "Other"
]


BASIC = {
    'Mean': Channel.get_rolling_mean,
    'Standard Deviation': Channel.get_rolling_std,
}
EXG_DERIVED ={'Epoch': EXGChannel.get_epochs}
HEARTRATE_DERIVED = {'Epoch': EXGChannel.get_epochs, **BASIC}
EPOCH_DERIVED = {
    'Hjorth Parameters': Epoch.get_hjorth_params,
    'Permutation Entropy': Epoch.get_permutation_entropy,
    'Higuchi Fractal Dimension': Epoch.get_higuchi,
    'Petrosian Fractal Dimension': Epoch.get_petrosian,
    'Zero Crossings': Epoch.get_zero_crossings,
    "Welch's Power Spectral Density": Epoch.get_welch,
    'Standard Deviation': Epoch.get_std,
    'Interquartile Range': Epoch.get_interquartile_range,
    'Kurtosis': Epoch.get_kurtosis,
    'Skewness': Epoch.get_skew,
}
WELCH_DERIVED = {}
ECG_DERIVED = {'Heart Rate': ECGChannel.get_heart_rate}

DERIVANDS = {
    # 'Gyroscope': {**BASIC}, 'ODBA': {**BASIC}, 'Pressure': {**BASIC}, 'Other': {**BASIC},
    # 'EEG': {**EXG_DERIVED, **BASIC},
    'Epoch': EPOCH_DERIVED,
    # 'ECG': {**ECG_DERIVED, **EXG_DERIVED, **BASIC},
    'Heart Rate': HEARTRATE_DERIVED,
    "Welch's Power Spectral Density": WELCH_DERIVED 
}

FEATURE_OPTIONS = {
    'all': {**BASIC, **EXG_DERIVED, **ECG_DERIVED, **EPOCH_DERIVED},
    'EEG': {**EXG_DERIVED, **BASIC},
    'ECG': {**ECG_DERIVED, **EXG_DERIVED, **BASIC},
    'Pressure': {**BASIC},
    'ODBA': {**BASIC},
    'Gyroscope': {**BASIC},
    'Other': {**BASIC}
}