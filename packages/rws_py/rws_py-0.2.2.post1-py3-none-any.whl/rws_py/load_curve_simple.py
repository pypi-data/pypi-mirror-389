"""

Generate simple energy load curves for analysis of weather data

Either as step function or as sine, differences for weekdays and weekends
included.

B. Atakan, Uni Duisburg-Essen, Germany

SPP2403

2025-01-20

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def generate_seasonal_modulation(time_index, amplitude=0.05):
    """
    Generate a seasonal modulation function using a cosine wave.
    
    Parameters
    ----------
    time_index : pandas DateTimeIndex
        The period for which values are generated.
    amplitude : float, optional
        The amplitude of the seasonal variation. Default is 0.05.
    
    Returns
    -------
    pandas Series
        Seasonal modulation factor for each timestamp.
    """
    # Umwandlung der Zeitstempel in den Tagesindex innerhalb eines Jahres (0 bis 364 oder 365)
    day_of_year = time_index.day_of_year
    
    # Kosinusfunktion für die jahreszeitliche Modulation
    seasonal_factor = 1 + amplitude * np.cos(2 * np.pi * day_of_year / 365)

    
    return pd.Series(seasonal_factor, index=time_index)

def generate_load_curve(time_index, step=True, load_parameters=None):
    """
    Generate simple load curves either step function or sine,
    with an additional seasonal modulation.

    Parameters
    ----------
    time_index : pandas DateTimeIndex
        The period for which values are generated.
    step : Boolean, optional
        If True, it is a step function, else a sine. Default is True.
    load_parameters : dictionary, optional
        Values for min/max and weekend/workdays and intermediate values.

    Returns
    -------
    pandas dataframe
        With the load values.
    """
    if load_parameters is None:
        load_parameters = {
            'min_weekday': 0.650,
            'max_weekday': 1.0,
            'min_weekend': 0.650,
            'max_weekend': 0.85,
            'intermediate_fraction': 0.80,
            'multiplier': 1.0,
            'offset': 0.0,
            'normalize': True,
            'amplitude_season':0.05,  # seasonal
        }

    load_curve = pd.DataFrame(index=time_index)
    load_curve['load'] = 0.0

    def generate_sinusoidal_load(t, wert_min, wert_max):
        amplitude = (wert_max - wert_min) / 2
        offset = wert_min + amplitude
        phase_shift = 6
        return offset + amplitude * np.sin((2 * np.pi / 24) * (t - phase_shift))

    for timestamp in load_curve.index:
        hour = timestamp.hour
        is_weekend = timestamp.weekday() >= 5

        if is_weekend:
            if step:
                if hour < 6:
                    load_curve.at[timestamp, 'load'] = load_parameters['min_weekend']
                elif hour < 7:
                    load_curve.at[timestamp, 'load'] = load_parameters['intermediate_fraction']
                elif hour < 22:
                    load_curve.at[timestamp, 'load'] = load_parameters['max_weekend']
                elif hour < 23:
                    load_curve.at[timestamp, 'load'] = load_parameters['intermediate_fraction']
                else:
                    load_curve.at[timestamp, 'load'] = load_parameters['min_weekend']
            else:
                load_curve.at[timestamp, 'load'] = generate_sinusoidal_load(
                    hour, load_parameters['min_weekend'], load_parameters['max_weekend']
                )
        else:
            if step:
                if hour < 6:
                    load_curve.at[timestamp, 'load'] = load_parameters['min_weekday']
                elif hour < 7:
                    load_curve.at[timestamp, 'load'] = load_parameters['intermediate_fraction']
                elif hour < 19:
                    load_curve.at[timestamp, 'load'] = load_parameters['max_weekday']
                elif hour < 22:
                    load_curve.at[timestamp, 'load'] = load_parameters['intermediate_fraction']
                else:
                    load_curve.at[timestamp, 'load'] = load_parameters['min_weekday']
            else:
                load_curve.at[timestamp, 'load'] = generate_sinusoidal_load(
                    hour, load_parameters['min_weekday'], load_parameters['max_weekday']
                )

    # Offset und Skalierung
    load_curve['load'] -= load_parameters['offset']
    load_curve['load'] *= load_parameters['multiplier']

    # Normierung (falls gewünscht)
    l_mean = load_curve['load'].mean()
    if load_parameters['normalize']:
        load_curve["load not normalized"] = load_curve['load']
        load_curve['load'] /= l_mean
        if load_parameters['multiplier']!=1.0:
            print('WARNING, load-multiplier neglected, due to normalization!')

    # Saisonale Modulation
    load_curve['seasonal_factor'] = generate_seasonal_modulation(time_index, amplitude=load_parameters["amplitude_season"])
    load_curve['load'] *= load_curve['seasonal_factor']
    load_curve['load'] = load_curve['load'] /load_curve['load'].mean()

    return load_curve

def _generate_sinusoidal_load(t, wert_min, wert_max):
    """
    Generiert einen sinusförmigen Verlauf mit einer Periode von 24 Stunden,
    einer Phasenverschiebung von 6 Stunden, sowie einem bestimmten
    minimalen und maximalen Wert.

    :param t: Array von Zeitpunkten (in Stunden), von 0 bis 24.
    :param wert_min: Minimalwert der Lastkurve.
    :param wert_max: Maximalwert der Lastkurve.
    :return: Sinusförmige Lastkurve.
    """
    # Definiere die Amplitude und den Offset
    amplitude = (wert_max - wert_min) / 2
    offset = wert_min + amplitude

    # Phasenverschiebung von 6 Stunden für die Sinusfunktion
    phase_shift = 6

    # Generiere die sinusförmige Lastkurve
    load_curve = offset + amplitude * \
        np.sin((2 * np.pi / 24) * (t - phase_shift))

    return load_curve


if __name__ == '__main__':
    time_ind = pd.date_range(start='2021-01-01', end='2022-12-31', freq="h")
    # Beispielaufruf der Funktion
    load_params = {
        'min_weekday': 0.650,
        'max_weekday': 1.0,
        'min_weekend': 0.650,
        'max_weekend': 0.85,
        'intermediate_fraction': 0.80,
        'multiplier': 50.0,
        'offset':0.0,
        'normalize': True,
        'amplitude_season':0.05,  # seasonal
    }

    # For step function
    load_curve_step = generate_load_curve(time_ind,
                                          step=True, load_parameters=load_params)

    # For sinusoidal function
    load_curve_sine = generate_load_curve(time_ind,
                                          step=False, load_parameters=load_params)

    # Plot der ersten zwei Wochen
    N_H = 24*14
    plt.figure(figsize=(12, 6))
    plt.plot(load_curve_step.index[:N_H], load_curve_step['load'][:N_H],
             label='Stufenfunktion', color='blue')  # N_H Stunden = 14 Tage
    plt.plot(load_curve_sine.index[:N_H], load_curve_sine['load']
             [:N_H], label='Sinusfunktion', color='orange')
    plt.title('Lastkurve: Stufenfunktion vs. Sinusfunktion (Erste zwei Wochen)')
    plt.xlabel('Datum')
    plt.ylabel('Last (Skaliert)')
    plt.grid()
    plt.legend()
    plt.show()

    int_step = load_curve_step["load"].sum()
    int_sine = load_curve_sine["load"].sum()

    print(f"Sum/Integral, sine: {int_sine}, setep: {int_step}")
    print("step:\n", load_curve_step.describe())

    print("sine:\n", load_curve_sine.describe())
