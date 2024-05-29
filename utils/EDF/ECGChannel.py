from .EXGChannel import EXGChannel
from typing import Self
import pandas as pd
import numpy as np
import mne
import yasa
import wfdb.processing
from scipy.signal import welch
from scipy.stats import iqr, skew, kurtosis
from sleepecg import detect_heartbeats


class ECGChannel(EXGChannel):
    def get_heart_rate(self, search_radius:int=200, filter_threshold:int=200) -> Self:
        """
        Gets heart rate at 1 Hz and extrapolates it to the same frequency as input data
        search_radius: search radius to look for peaks (200 ~= 150 bpm upper bound)
        filter_threshold: threshold above which to throw out values (filter_threshold=200 would throw out any value above 200 bpm and impute it from its neighbors)
        """
        rpeaks = detect_heartbeats(self.signal, self.freq)  # using sleepecg
        rpeaks_corrected = wfdb.processing.correct_peaks(
            self.signal, rpeaks, search_radius=search_radius, smooth_window_size=50, peak_dir="up"
        )
        heart_rates = [60 / ((rpeaks_corrected[i+1] - rpeaks_corrected[i]) / self.freq) for i in range(len(rpeaks_corrected) - 1)]
        # Create a heart rate array matching the frequency of the ECG trace
        hr_data = np.zeros_like(self.signal)
        # Assign heart rate values to the intervals between R-peaks
        for i in range(len(rpeaks_corrected) - 1):
            start_idx = rpeaks_corrected[i]
            end_idx = rpeaks_corrected[i+1]
            hr_data[start_idx:end_idx] = heart_rates[i]

        hr_data = pd.Series(hr_data)
        hr_data[hr_data > filter_threshold] = np.nan
        hr_data = hr_data.interpolate(method='quadratic', order=5).fillna('ffill').fillna('bfill')
        hr_data = hr_data.to_numpy()
        return self._return(hr_data, step_size=1)
    

def get_features_yasa_heartrate(heart_rate_data, sfreq=500, epoch_window_sec=512, welch_window_sec=512, step_size=32):
    """
    Gets heartrate features using similar code & syntax as YASA's feature generation, calculates deterministic features as well as spectral features
    heart_rate_data: heart rate vector data (must already be processed from an ECG, this function does NOT take ECG data)
    sfreq: sampling frequeuency, by default 500 Hz
    epoch_window_sec: size of the epoch rolling window to use
    welch_window_sec: size of the welch window for power spectral density calculations (this affects the low frequeuncy power and very low frequency power calculations, etc.)
    step_size: how big of a step size to use, in seconds
    """
    dt_filt = mne.filter.filter_data(
        heart_rate_data, sfreq, l_freq=0, h_freq=1, verbose=False
    )
    
    # - Extract epochs. Data is now of shape (n_epochs, n_samples).
    times, epochs = yasa.sliding_window(dt_filt, sf=sfreq, window=epoch_window_sec, step=step_size)
    times = times + epoch_window_sec // 2 # add window/2 to the times to make the epochs "centered" around the times
    
    window_length = sfreq*welch_window_sec
    kwargs_welch = dict(
        window='hann',
        nperseg=window_length, # a little more than  4 minutes
        noverlap=window_length//2,
        scaling='density',
        average='median'
    )
    bands = [
        (0.0033, 0.04, 'vlf'),
        (0.04, 0.15, 'lf'),
        (0.15, 0.4, 'hf')
    ]
    freqs, psd = sp_sig.welch(epochs, sfreq, **kwargs_welch)
    bp = bandpower_from_psd_ndarray(psd, freqs, bands=bands)
    
    feat = {}
    
    # Calculate standard descriptive statistics
    hmob, hcomp = ant.hjorth_params(epochs, axis=1)
    
    feat = {
        "mean": np.mean(epochs, axis=1),
        "std": np.std(epochs, ddof=1, axis=1),
        "iqr": sp_stats.iqr(epochs, rng=(25, 75), axis=1),
        "skew": sp_stats.skew(epochs, axis=1),
        "kurt": sp_stats.kurtosis(epochs, axis=1),
        "hmob": hmob,
        "hcomp": hcomp,
    }
    
    # Bandpowers
    for j, (_, _, b) in enumerate(bands):
        feat[b] = bp[j]

    feat['lf/hf'] = feat['lf'] / feat['hf']
    feat['p_total'] = feat['vlf'] + feat['lf'] + feat['hf']

    # compute relative and normalized power measures
    perc_factor = 100 / feat['p_total']
    feat['vlf_perc'] = feat['vlf'] * perc_factor
    feat['lf_perc'] = feat['lf'] * perc_factor
    feat['hf_perc'] = feat['hf'] * perc_factor

    nu_factor = 100 / (feat['lf'] + feat['hf'])
    feat['lf_nu'] = feat['lf'] * nu_factor
    feat['hf_nu'] = feat['hf'] * nu_factor

    # Convert to dataframe
    feat = pd.DataFrame(feat)
    feat["epoch_index"] = times # added window / 2 to the times above to center the epochs on the times
    return feat
