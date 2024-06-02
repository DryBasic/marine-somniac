import numpy as np
from scipy.integrate import simpson


class WelchDerived:
    @staticmethod
    def get_power_ratios(welches: dict) -> dict:
        power_ratios = {}
        if 'sdelta' in welches and 'fdelta' in welches:
            delta = welches["sdelta"] + welches["fdelta"]
            for wave in [w for w in welches.keys() if w not in ('sdelta', 'fdelta')]:
                power_ratios[f"delta/{wave}"] = delta / welches[wave]
        if 'alpha' in welches and 'theta' in welches:
            power_ratios["alpha/theta"] = welches["alpha"] / welches["theta"]
        return power_ratios
    
    @staticmethod
    def get_absolute_power(freqs: np.array, freq_broad: tuple[float, float], power_spectral_density: np.array) -> dict:
        idx_broad = np.logical_and(freqs >= freq_broad[0], freqs <= freq_broad[1])
        dx = freqs[1] - freqs[0]
        return {"absolute_power": simpson(power_spectral_density[:, idx_broad], dx=dx)}

    @staticmethod
    def get_power_std(welches):
        welch_stds = {f"{k}_std": [np.std(array)] * len(array) for k, array in welches}
        return welch_stds
    
    @staticmethod
    def get_relative_powers(welches, absolute_power):
        relative_powers = {f"{k}_relative": array/absolute_power['absolute_power'] for k, array in welches}
        return relative_powers
    
    @staticmethod
    def get_total_power(powers):
        total = np.zeros(len(powers[0]))
        for power in powers:
            total += power
        return total