from utils.EDF.EDF import Channel
from utils.EDF.EDF import EXGChannel
from utils.EDF.EDF import ECGChannel
from utils.EDF.EpochDerived import EpochDerived
from utils.EDF.WelchDerived import WelchDerived

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
    'Hjorth Parameters': EpochDerived.get_hjorth_params,
    'Permutation Entropy': EpochDerived.get_permutation_entropy,
    'Higuchi Fractal Dimension': EpochDerived.get_higuchi,
    'Petrosian Fractal Dimension': EpochDerived.get_petrosian,
    'Zero Crossings': EpochDerived.get_zero_crossings,
    "Welch's Power Spectral Density": EpochDerived.get_welch,
    'Standard Deviation_': EpochDerived.get_std,
    'Interquartile Range': EpochDerived.get_interquartile_range,
    'Kurtosis': EpochDerived.get_kurtosis,
    'Skewness': EpochDerived.get_skew,
}
WELCH_DERIVED = {
    'Power Ratios': WelchDerived.get_power_ratios,
    'Absolute Power': WelchDerived.get_absolute_power,
    'Power Standard Deviation': WelchDerived.get_power_std,
    'Relative Powers': WelchDerived.get_relative_powers,
    'Total Power': WelchDerived.get_total_power
}
ECG_DERIVED = {'Heart Rate': ECGChannel.get_heart_rate}
NOT_CONFIGURABLE = [
    'Hjorth Parameters',
    'Permutation Entropy',
    'Higuchi Fractal Dimension',
    'Petrosian Fractal Dimension',
    'Zero Crossings',
    'Standard Deviation_',
    'Interquartile Range',
    'Kurtosis',
    'Skewness',
    'Power Ratios',
    'Absolute Power',
    'Power Standard Deviation',
    'Relative Powers',
    'Total Power'
]
CUSTOM_ARGSPEC = ['get_welch']



DERIVANDS = {
    'Pressure': {**BASIC}, 'ODBA': {**BASIC}, 'Gyroscope': {**BASIC}, 'Other': {**BASIC},
    'EEG': {**EXG_DERIVED, **BASIC},
    'ECG': {**ECG_DERIVED, **EXG_DERIVED, **BASIC},
    'Epoch': EPOCH_DERIVED,
    'Heart Rate': HEARTRATE_DERIVED,
    "Welch's Power Spectral Density": WELCH_DERIVED 
}
LABEL_TO_METHOD = {**BASIC, **EXG_DERIVED, **ECG_DERIVED, **EPOCH_DERIVED, **WELCH_DERIVED}

FEATURE_OPTIONS = {
    'all': {**BASIC, **EXG_DERIVED, **ECG_DERIVED, **EPOCH_DERIVED},
    'EEG': {**EXG_DERIVED, **BASIC},
    'ECG': {**ECG_DERIVED, **EXG_DERIVED, **BASIC},
    'Pressure': {**BASIC},
    'ODBA': {**BASIC},
    'Gyroscope': {**BASIC},
    'Other': {**BASIC}
}