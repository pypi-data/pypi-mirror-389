# -*- coding: utf-8 -*-
"""
Created on Mon Jan 20 13:24:40 2025

@author: atakan
"""


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from rws_py.residual_analyse import storage


def calc_residuals(power_df,
                   load_df,
                   gamma=1.0,
                   columns={"in-power": 'power',
                            "in-load": 'load',
                            "out-residual": 'residual-no-storage',
                            "out-unchanged": 'residual-not-normalized'},
                   normalize=True):
    """
    Calculate residual load from load and power dataframes

    Parameters
    ----------
    power_df : pandas.DataFrame
        datframe with the power column.
    load_df : pandas.DataFrame
        dataframe with the load column.
    gamma : Float, optional
        the load is multiplied by this factor, before the residual is
        calculated. A measure of how much residuals are available. The default
        is 1.0.
    columns : Dictionary, optional
        where to find the input columns and in which column to write the output.
        The default is {"in-power": 'power', "in_load": 'load',
                        "out-residual": 'residual-no-storage',
                        "out-unchanged" : 'residual-not-normalized'}.
    normalize : Boolean, optional
        the residuals will be divided by the absolute mean of the negative
        residuals. The default is True.

    Returns
    -------
    power_df : pandas.DataFrame
        dataframe with the load and the residual included.

    """
    # Explizite Kopie erstellen
    result_df = power_df.copy()

    # .loc verwenden für das Zuweisen von Werten
    result_df.loc[:, columns["in-load"]] = load_df[columns['in-load']]
    result_df.loc[:, columns["out-unchanged"]] = load_df[columns['in-load']] \
        * gamma - result_df[columns['in-power']]
    result_df['$\gamma$'] = gamma

    if normalize:
        result_df.loc[:, columns["out-residual"]
                      ] = result_df[columns["out-unchanged"]]
        negative_values = result_df[result_df[columns["out-residual"]] < 0]

        mean_negative_values = abs(
            negative_values[columns["out-residual"]].sum()) \
            / result_df[columns["out-residual"]].count()
        # this is the mean per year, NOT the mean of only the times with
        # negative values!
        result_df.loc[:, columns["out-residual"]] /= mean_negative_values

    return result_df


def weather_load_storage(energy_in_df, load_df=None, storage_size=None,
                         pow_index="power",
                         eff=.75,
                         residual=False):
    """
    Calculate the remaining load and storage charging as a function of energy.

    Parameters
    ----------
    energy_in_df : pandas DataFrame
        The given index values are analyzed as time and energy.
    load_df : pandas DataFrame, optional
        If not None, a DataFrame with the date as index and load values in 
        column 'load'. The default is None.
    storage_size : float, optional
        Size in the units of "power" times hours. If None, the maximum value 
        of "power" will be multiplied by 2. The default is None.
    pow_index : string, optional
        Index of energy_df with 'power' values. The default is "power".
    eff : float, optional
        Storage efficiency (energy out / energy in). The default is 0.75.
    residual : Boolean, optional
        True, when residuals are already included in energy_df. Default: False.

    Returns
    -------
    energy_df : pandas DataFrame
        All input data frames, residuals, with and without storage,
        SOC (state of charge) of the storage.
    """
    energy_df = energy_in_df.copy()
    time_resolution_hours = energy_df.index.to_series(
    ).diff().median().total_seconds() / 3600

    if storage_size is None:
        storage_size = energy_df[pow_index].max() * 2
        print(f"St-size in: {storage_size}")

    soc_act = 0
    act_capacity = soc_act * storage_size

    col_n = ["load", "residual-no-storage", "residual-w-storage"]

    for ind in energy_df.index:
        if residual:
            res_act = energy_df.loc[ind, "residual-no-storage"]
        else:
            res_act = load_df.loc[ind, "load"] - energy_df.loc[ind, pow_index]
            energy_df.loc[ind, "load"] = load_df.loc[ind, "load"]

        st_res = storage(-res_act, act_capacity, storage_size,
                         efficiency=eff,
                         time_step=time_resolution_hours)

        energy_df.loc[ind, st_res.keys()] = st_res.values()
        energy_df.loc[ind, "residual-no-storage"] = res_act
        energy_df.loc[ind, "residual-w-storage"] = res_act + \
            st_res["power_st_in"]

        act_capacity = st_res["act_st_cap"]

    return energy_df


def test_weather_load_storage(verbose=False, hours=48):
    # np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=hours, freq="h")

    # Create situations with different load and energy patterns
    energy_values = np.random.choice(
        [0] + list(np.arange(00, 1001.)), size=len(dates))
    load_values_high = np.linspace(
        900, -150, num=len(dates))  # Load greater than energy
    # Load less than energy
    load_values_low = np.linspace(-300, 950, num=len(dates))
    load_values_equal = energy_values                          # Load equal to energy
    load_values_mean_equal = np.random.choice(
        [0] + list(np.arange(00, 1001.)), size=len(dates))

    energy_df = pd.DataFrame(
        {"MESS_DATUM": dates, "power": energy_values}, index=dates)
    load_df_high = pd.DataFrame({"load": load_values_high}, index=dates)
    load_df_low = pd.DataFrame({"load": load_values_low}, index=dates)
    load_df_equal = pd.DataFrame({"load": load_values_equal}, index=dates)
    load_mean_equal = pd.DataFrame(
        {"load": load_values_mean_equal}, index=dates)

    # Call the function for each scenario
    scenarios = {"High to low Load": load_df_high,
                 "Low Load": load_df_low,
                 "Equal Load": load_df_equal,
                 "Mean Load equal": load_mean_equal}

    for scenario, load_df in scenarios.items():
        test_df = calc_residuals(energy_df, load_df)
        print('\nFrom calc_residuals', test_df.describe())
        result_df = weather_load_storage(energy_df.copy(), load_df)

        if verbose:
            plt.figure(figsize=(10, 4))
            plt.plot(
                result_df.index, result_df['residual-w-storage'], "<g", label='Residual with Storage')
            plt.plot(result_df.index, result_df['residual-no-storage'],
                     "vb", label='Residual without Storage', linestyle='--')
            plt.plot(result_df.index,
                     result_df['load'], "ok", label='Load', linestyle='-.')
            plt.plot(
                result_df.index, result_df['act_st_cap'], "k", label='act_st_cap', linestyle='-.')
            plt.plot(result_df.index,
                     energy_df['power'], "k", label='power', linestyle='-')
            plt.xlabel('Time')
            plt.ylabel('power / [a.u.]')
            plt.title(f'Scenario: {scenario}')
            plt.legend(loc='center left', bbox_to_anchor=(1.1, 0.75))
            # Alternativ: ax1.legend(lines, labels, loc='center left', bbox_to_anchor=(1.1, 0.5))

            plt.tight_layout()  # um Platz für beide y-Achsen zu garantieren
            plt.grid(True)
            plt.show()
            print(f"\n{scenario}")
            print(result_df.describe())
            print_summary_stats(result_df, energy_df)


def print_summary_stats(result_df, energy_df):
    metrics = {
        'Residual with Storage': result_df['residual-w-storage'],
        'Residual without Storage': result_df['residual-no-storage'],
        'Load': result_df['load'],
        'Energy': energy_df['power']
    }

    print("{:<25} {:>10} {:>10} {:>10}".format(
        "Kategorie", "Mittelwert", "Minimum", "Maximum"))
    print("-" * 57)

    for label, data in metrics.items():
        mean_val = data.mean()
        min_val = data.min()
        max_val = data.max()
        print(f"{label:<25} {mean_val:>10.2f} {min_val:>10.2f} {max_val:>10.2f}")

# Beispiel, um die Funktion zu verwenden:
# print_summary_stats(result_df, energy_df)


if __name__ == "__main__":
    test_weather_load_storage(verbose=True)
