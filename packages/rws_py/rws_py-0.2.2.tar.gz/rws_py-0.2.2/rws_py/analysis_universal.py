# -*- coding: utf-8 -*-
"""
New residual analysis unifying for weather data and ESM residuals.

Created on Sat Jan 25 11:21:18 2025

@author: atakan
"""

import json
import numpy as np
import pandas as pd
import seaborn as sbn
import matplotlib.pyplot as plt
from rws_py import app_suf


pd.set_option('display.max_columns', None)



def rename_count_columns(df):
    """
    Replace Column names in pandas dataFrame

    from count to period and from sum to integral, should help understanding/
    readability.

    Parameters
    ----------
    df : pandas DataFrame
        DtaFrame with the columns to replace.

    Returns
    -------
    pandas DataFrame
        column names changed.

    """
    return df.rename(columns={
        col: col.replace('count', 'period').replace('sum', 'integral')
        for col in df.columns
        if 'count' in col or 'sum' in col
    })




def residual_analyse(data, column, thresholds={'direct': 0.},
                     verbose=False, time_base_e=1.0):
    """
    Comprehensive analysis of time series data with threshold-based period analysis

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame containing the data to be analyzed
    column : str
        Name of the column to analyze
    thresholds : dict or None, optional
        Dictionary of thresholds for different analyses (example {"name":0.0}).
        Default is {'direct': 0.}.
    verbose : bool, optional
        If True, print additional information (default is False)
    time_base_e : float
        units in hours for determination of periods etc. default is 1.0

    Returns
    -------
    dict of analysis results
    """
    # Validate datetime index
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("DataFrame must have a datetime index")

    # Calculate time resolution in hours
    time_deltas = data.index.to_series().diff()
    time_per_point = time_deltas.median().total_seconds() / 3600
    time_conversion = time_per_point / time_base_e

    # Create a copy of the data to avoid modifying the original
    # data = data.copy()

    # Initialize results dictionary
    results = {'time_resolution_hours': time_per_point}

    # Default analysis with zero threshold
    data['above_threshold'] = data[column] > 0
    data['block'] = (data['above_threshold'].diff() != 0).cumsum()

    # Period statistics
    df_period = data.groupby('block').agg(
        # Verwende die variable column
        count=(column, lambda x: len(x) * time_conversion),
        mean=(column, 'mean'),
        std=(column, 'std'),
        sum=(column, lambda x: sum(x) * time_conversion),
        min=(column, 'min'),
        max=(column, 'max'),
        time=(column, lambda x: x.index[0])  # Startzeitpunkt der Periode
    ).reset_index()

    # Add quantiles
    quantile_cols = data.groupby('block')[column].quantile([
        0.25, 0.5, 0.75]).unstack()
    df_period['25%'] = quantile_cols[0.25].values
    df_period['50%'] = quantile_cols[0.5].values
    df_period['75%'] = quantile_cols[0.75].values

    df_period['positive'] = df_period['sum'] > 0

    # Combinations of periods
    pos_neg_list, neg_pos_list = [], []
    for i in range(len(df_period)):
        current_row = df_period.iloc[i]
        if current_row['positive']:
            # Positive-Negative combination
            if i + 1 < len(df_period) and not df_period.iloc[i + 1]['positive']:
                next_row = df_period.iloc[i + 1]
                combined = pd.concat([current_row.add_suffix(
                    '_pos'), next_row.add_suffix('_neg')])
            else:
                zero_row = pd.Series(
                    0, index=current_row.index).add_suffix('_neg')
                combined = pd.concat(
                    [current_row.add_suffix('_pos'), zero_row])
            pos_neg_list.append(combined)
        else:
            # Negative-Positive combination
            if i + 1 < len(df_period) and df_period.iloc[i + 1]['positive']:
                next_row = df_period.iloc[i + 1]
                combined = pd.concat([current_row.add_suffix(
                    '_neg'), next_row.add_suffix('_pos')])
            else:
                zero_row = pd.Series(
                    0, index=current_row.index).add_suffix('_pos')
                combined = pd.concat(
                    [current_row.add_suffix('_neg'), zero_row])
            neg_pos_list.append(combined)

    df_pos_neg = pd.DataFrame(pos_neg_list).reset_index(drop=True)
    df_neg_pos = pd.DataFrame(neg_pos_list).reset_index(
        drop=True)  # This is the important one!

    # Verbose output
    if verbose:
        print("Positive-Negative Periods:")
        print(df_pos_neg)
        print("\nNegative-Positive Periods:")
        print(df_neg_pos)

    # Default analysis results and renaming
    results['default_analysis'] = {
        'period_stats': rename_count_columns(df_period),
        'pos_neg_periods': rename_count_columns(df_pos_neg),
        'neg-pos-res': rename_count_columns(df_neg_pos)

    }

    # Additional threshold analyses
    if thresholds:
        for threshold_name, threshold_value in thresholds.items():
            # Analyze periods above specific thresholds
            data['neg-residual'] = data[column] < threshold_value
            data['block_custom'] = (data['neg-residual'].diff() != 0).cumsum()

            # Threshold-specific analysis
            df_threshold = data.groupby('block_custom').agg(
                count=(column, lambda x: len(x) * time_conversion),
                mean=(column, 'mean'),
                std=(column, 'std'),
                sum=(column, lambda x: sum(x) * time_conversion),
                min=(column, 'min'),
                max=(column, 'max'),
                # Startzeitpunkt der Periode
                time=(column, lambda x: x.index[0])
            ).reset_index()

            # Storage period analysis
            neg_pos_residual_list = []
            for i in range(len(df_threshold)):
                if i + 1 < len(df_threshold):
                    current_row = df_threshold.iloc[i].copy()
                    next_row = df_threshold.iloc[i + 1]

                    if current_row['mean'] < threshold_value and \
                            next_row['mean'] >= threshold_value:
                        current_row['period-pos'] = next_row['count'].copy()
                        neg_pos_residual_list.append(current_row)

            df_neg_pos_residual = pd.DataFrame(neg_pos_residual_list)

            # Storage periods statistics
            storage_periods = {
                'count': len(df_neg_pos_residual),
                'mean_duration': df_neg_pos_residual['count'].mean() if not
                df_neg_pos_residual.empty else 0,
                'total_duration': df_neg_pos_residual['count'].sum() if not
                df_neg_pos_residual.empty else 0,
                'mean_intensity': df_neg_pos_residual['mean'].mean() if not
                df_neg_pos_residual.empty else 0,
                'mean_pos_duration': df_neg_pos_residual['period-pos'].mean()
                if not df_neg_pos_residual.empty else 0,
            }

            # Store results for this threshold
            results[f'{threshold_name}_threshold_analysis'] = {
                'period_data': rename_count_columns(df_threshold),
                'storage_periods': storage_periods,
                'neg-pos-res': rename_count_columns(df_neg_pos_residual)
            }

    return results


def posterior_analysis_residual(actual_df, storage_capacity=1., verbose=True):
    """
    Evaluate the residual load with energy storage DataFrame after its calculation

    The number of full charging/discharging cycles ("charging"), the level of
    autonomy, and the times the storag changed its state either from empty or
    from full("storage_states are evaluated.

    Parameters
    ----------
    actual_df : panda DataFrame
        the data timeseries with the residuals, storage states.
    storage_capacity : Float, optional
        max. storage capacity, needed to calculate the equivalent full charging
        /discharging cycles. The default is 1..
    verbose : Boolean, optional
        for getting some printings. The default is True.

    Returns
    -------
    storage_states : Dictionary
        DESCRIPTION.
    level_of_autonomy : Dictionary
        DESCRIPTION.
    charging : Dictionary
        DESCRIPTION.

    """

    number_all = actual_df['SOC'].count()
    soc_counts = actual_df['SOC'].value_counts()
    zero_count = soc_counts.get(0, 0)  # Anzahl der 0en
    one_count = soc_counts.get(1, 0)    # Anzahl der 1en
    if "time_diff_seconds" in actual_df.columns:
        power_energy = actual_df["time_diff_seconds"].mean() / 3600
    else:
        print("WARNING: Time difference not n dataframe, assumed to be 1 h!")
        power_energy = 1.0

    # Berechnung der Differenzen zwischen aufeinanderfolgenden Werten
    actual_df['previous_SOC'] = actual_df['SOC'].shift(
        1)  # Vorheriger Wert

    # Bedingung für Wechsel von 0 auf einen höheren Wert
    from_0_to_higher = ((actual_df['previous_SOC'] == 0) & (
        actual_df['SOC'] > 0)).sum()

    # Bedingung für Wechsel von 1 auf einen niedrigeren Wert
    from_1_to_lower = ((actual_df['previous_SOC'] == 1) & (
        actual_df['SOC'] < 1)).sum()

    # Ausgabe der Ergebnisse
    if verbose:

        print(f"""Anzahl der Werte 0 in 'SOC': {
              zero_count} und 1 in 'SOC': {one_count}""")
        print(f"""Anzahl der Wechsel von 0 auf einen höheren Wert: {
              from_0_to_higher}; von 1 auf einen niedrigeren Wert: {
            from_1_to_lower}""")

    storage_states = {
        "empty": zero_count / number_all,
        "full": one_count / number_all,
        "charging": from_0_to_higher,
        "discharging":  from_1_to_lower
    }
    c_name = "residual-no-storage"
    total_pos_residual = (actual_df.loc[actual_df[c_name] > 0, c_name] *
                          power_energy).sum()
    total_neg_residual = (actual_df.loc[actual_df[c_name] < 0, c_name] *
                          power_energy).sum()
    residual_ratio_n_p = abs(total_neg_residual / total_pos_residual)

    c_name = "residual-w-storage"
    total_pos_residual_w = (actual_df.loc[actual_df[c_name] > 0, c_name] *
                          power_energy).sum()
    total_neg_residual_w = (actual_df.loc[actual_df[c_name] < 0, c_name] *
                          power_energy).sum()
    residual_ratio_n_p_w = abs(total_neg_residual_w / total_pos_residual_w)
    # Zugrunde liegende Werte zur LA Auswertung
    time_pos_res_remain = actual_df[actual_df[c_name] > 0].count()[c_name]
    time_neg_res_remain = actual_df[actual_df[c_name] < 0].count()[c_name]
    time_no_res_remain = actual_df[actual_df[c_name] == 0].count()[c_name]

    la_pos = 1 - (time_pos_res_remain / actual_df[c_name].count())
    la_neg = 1 - (time_neg_res_remain / actual_df[c_name].count())
    la_eq = time_no_res_remain / actual_df[c_name].count()
    level_of_autonomy = {
        "LA-pos": la_pos,
        "LA-neg": la_neg,
        "Zero-Residual-Time": la_eq,
        "Pos. Residuals (no-storage)" : total_pos_residual,
        "Neg. Residuals (no-storage)" : total_neg_residual,
        "Neg./Pos. residual ratio (no-storage)" : residual_ratio_n_p,
        "Pos. Residuals (w-storage)" : total_pos_residual_w,
        "Neg. Residuals (w-storage)" : total_neg_residual_w,
        "Neg./Pos. residual ratio (w-storage)" : residual_ratio_n_p_w,
        
        
    }

    charging = None
    c_name = "power_st_in"
   
    total_energy_to_storage = (
        actual_df.loc[actual_df[c_name] > 0, c_name] *
        power_energy).sum()

    # Skalieren der negativen Werte (Energie aus dem Speicher entnommen)
    total_energy_from_storage = (
        actual_df.loc[actual_df[c_name] < 0, c_name] *
        power_energy).sum()
   
    number_charging = total_energy_to_storage / storage_capacity
    number_discharging = total_energy_from_storage / storage_capacity

    charging = {"total energy stored": total_energy_to_storage,
                "total energy discharged": total_energy_from_storage,
                "Number of full charging": number_charging,
                "Number of full discharging": number_discharging,

                }

    return storage_states, level_of_autonomy, charging


def _print_dict(my_dict):
    for k, v in my_dict.items():
        if isinstance(v, np.float64):
            print(f"{k}: {float(v):.4f}")
        elif isinstance(v, float):
            print(f"{k}: {v:.4f}")
        else:
            print(f"{k}: {v}")


def print_dict(my_dict, filename=None):
    """
    print the dictionary and optional: store it to the json file

    Parameters
    ----------
    my_dict : dictionary
        DESCRIPTION.
    filename : string, optional
        DESCRIPTION. The default is None.

    Returns
    -------
    output : TYPE
        DESCRIPTION.

    """

    # Funktion zum Verarbeiten eines einzelnen Dictionaries
    def process_single_dict(d):
        output = {}
        for k, v in d.items():
            if isinstance(v, (np.float64, float)):
                output[k] = f"{float(v):.4f}"
            elif isinstance(v, (np.int64, float)):
                output[k] = f"{int(v)}"
            else:
                output[k] = v
            print(f"{k}: {output[k]}")
        return output

    # Wenn my_dict eine Liste von Dictionaries ist
    if isinstance(my_dict, list):
        processed_list = [process_single_dict(d) for d in my_dict]
        output_to_save = processed_list
    else:
        # Ansonsten wird das einzelne Dictionary verarbeitet
        output_to_save = process_single_dict(my_dict)

    # Speichern in einer JSON-Datei, wenn ein Dateiname angegeben ist
    if filename is not None:
        try:
            with open(app_suf(filename, ".json"), 'w') as f:
                json.dump(output_to_save, f, indent=4)
            print(
                f"Ergebnisse wurden in {app_suf(filename,'.json')} gespeichert.")
        except Exception as e:
            print(f"Fehler beim Schreiben in die Datei '{filename}': {e}")


def plot_analysis_b(evaluation_df, thresh_n="default", file=None, label=None,
                    y_max=None):
    """
    Scatterplot of periods with neg. residuals vs. the following pos. residual

    Parameters
    ----------
    evaluation_df : dictionary withpandas dataFrame
        period lengths and integgrals for negative residuals and th directly
        following positive residuals.
    thresh_n : float, optional
        threshold-dictionary name (part, typically "basic", "direct" or
                                   "default". The default is "default".
    file : string, optional
        filename without ending for storing the plot. The default is None.
    label : string, optional
        title of the plot. The default is None.

    Returns
    -------
    None.

    """

    plt.figure()

    # neg_pos[['integral_pos', 'integral_neg']] = neg_pos[[
    #     'integral_pos', 'integral_neg']] * SUM_UNITS
    if thresh_n == "default":
        direct = evaluation_df[thresh_n + '_analysis']
        df_act = direct["neg-pos-res"]
        sbn.scatterplot(data=df_act,
                        x='period_neg', y='period_pos',
                        size='integral_neg', hue='integral_pos')
    else:
        direct = evaluation_df[thresh_n + '_threshold_analysis']
        df_act = direct["neg-pos-res"]
        sbn.scatterplot(data=df_act,
                        x='period', y='period-pos',
                        size='integral', hue='mean')  # , style='mean_pos')
    if y_max is not None:
        plt.ylim(0, y_max)
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))

    # Optional: Ändere die Größe des Plots, um Platz für die Legende zu schaffen
    plt.tight_layout()
    plt.title(label)
    plt.savefig(app_suf(file, "_scat_neg_pos", "jpg"))

    plt.show()
    if file is not None:
        df_act.to_csv(app_suf(file, "-eval-neg-pos-res", "csv"))
        print_dict(evaluation_df['direct_threshold_analysis']
                   ["storage_periods"], app_suf(file, "-eval-st-periods"))


def plot_res(dat_in,  file=None, label=None):
    """
    Plot time dependent residuals with and w/o storage, loads and power

    in case of ESM residual analysis, without öoad and power

    Parameters
    ----------
    dat_in : DataFrame
        all data, index is datetime.
    file : string, optional
        filename without ending for storing the plot. The default is None.
    label : string, optional
        plot title. The default is None.

    Returns
    -------
    None.

    """
    n_s = 2
    with_power = "power" in dat_in.columns
    if with_power:
        n_s += 1
    figx, ax = plt.subplots(n_s, sharex=True, figsize=(
        10, 8), constrained_layout=True)  # Größere Abbildung für Platz
    if with_power:
        dat_in.plot(y="power", ax=ax[n_s-1], legend=True)
        dat_in.plot(y="load", ax=ax[n_s-1], legend=True)
    dat_in.plot(y="residual-w-storage", ax=ax[0], legend=True)
    dat_in.plot(y="residual-no-storage", ax=ax[1], legend=True)
    dat_in.plot(y="act_st_cap", ax=ax[1], legend=True)

    # Legenden außerhalb platzieren
    for axis in ax:
        axis.legend(loc="upper left", bbox_to_anchor=(
            1.02, 1))  # Position außerhalb rechts

    ax[0].set_title(label)
    # Zusätzlicher Platz bei Speicherung
    figx.savefig(app_suf(file, "_res_storage_time", "jpg"),
                 bbox_inches="tight")
    plt.show()


def generate_test_data(duration_hours=48, resolution_minutes=60):
    """Generate test data with datetime index"""
    timestamps = pd.date_range(
        start='2024-01-01',
        periods=int(duration_hours * 60 / resolution_minutes),
        freq=f'{resolution_minutes}min'
    )

    # Generate sine wave
    time_array = np.linspace(0, duration_hours, len(timestamps))
    sine_values = np.sin(2 * np.pi * (1/12) * time_array)

    return pd.DataFrame({'value': sine_values}, index=timestamps)


def plot_histo_analysis(results, select=None,  en_t="title", name_file="histo",
                        bins=[0, 1, 2, 4, 8, 16, 32, 64, 128, 200],
                        integral=False,
                        n_bins_middle=10):
    """
    Create  visualizations for the analysis results with improved period distribution plots
    """
    pl_name = f"{en_t}"
    # Visualize results
    if select is None:
        select = {'lev-1': "default_analysis",
                  'lev-2': "neg-pos-res",
                  'col-1': 'period_neg',
                  'col-2': 'period_pos',
                  'col-1a': 'integral_neg',
                  'col-2a': 'integral_pos',

                  }

    act_df = results[select['lev-1']][select['lev-2']]
    if integral:
        bins_all = []
        for dat_bin in [act_df[select['col-1a']], act_df[select['col-2a']]]:
            p10 = np.percentile(dat_bin, 10)
            p90 = np.percentile(dat_bin, 90)
            print(p90, p10)
            # Create bin edges
            middle_bins = np.linspace(p10, p90, n_bins_middle + 1)
            bins_all.append(np.concatenate(
                [[dat_bin.min()], middle_bins, [dat_bin.max()]]))
        histo_2, xedges, yedges = np.histogram2d(
            act_df[select['col-1a']], act_df[select['col-2a']], bins=bins_all)
    else:

        histo_2, xedges, yedges = np.histogram2d(
            act_df[select['col-1']], act_df[select['col-2']], bins=bins)

    fig0, ax0 = plt.subplots(1)
    histo_2=histo_2.T

    ax0.imshow(histo_2)
    xranges = [
        f"neg {xedges[i]:.1f} - {xedges[i+1]:.1f}" for i in range(len(xedges) - 1)]
    yranges = [
        f"pos {yedges[i]:.1f} - {yedges[i+1]:.1f}" for i in range(len(xedges) - 1)]
    ax0.set_xticks(np.arange(len(xranges)), labels=xranges,
                   rotation=45, ha="right", rotation_mode="anchor")
    ax0.set_yticks(np.arange(len(yranges)), labels=yranges)
    for i in range(len(yranges)):
        for j in range(len(xranges)):
            if histo_2[i, j] > 0:
                ax0.text(j, i, f"{histo_2[i, j]:.0f}",
                         ha="center", va="center", color="w", fontsize=10)

    ax0.set_title(pl_name+", 2D Histogram")
    fig0.tight_layout()
    fig0.savefig(app_suf(name_file, "-2D-hist.png"))
    plt.show()
    df = pd.DataFrame(histo_2.T, index=yranges, columns=xranges)

    # xedges als eigene Spalte hinzufügen
    df.insert(0, "y_edges_start", yedges[:-1])

    # CSV speichern
    df.to_csv(app_suf(name_file, "histogram_data.csv"))

    # fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(ncols=2, nrows=2)

    # pcm = ax1.pcolormesh(xedges, yedges, histo_2, cmap='rainbow')
    # fig.colorbar(pcm, ax=ax1)
    # ax1.set_xlabel("Period length / h")
    # ax1.set_ylabel("pause length / h")
    # sum_count_fit = Polynomial.fit(
    #     results['direct_inactive']['count'], results['direct_inactive']['sum'], 2)
    # ax2.plot(results['direct_inactive']['count'],
    #          results['direct_inactive']['sum'], "+k")
    # ax2.plot(results['direct_inactive']['count'], sum_count_fit(
    #     results['direct_inactive']['count']), '.')
    # ax2.set_xlabel("Period length / h")
    # ax2.set_ylabel("total intensity")
    # ax3.plot(period_pause['count'], period_pause['mean'], "+k")
    # ax3.set_xlabel("Period length / h")
    # ax3.set_ylabel("mean intensity")


def plot_histo_int_analysis(results, select=None,  en_t="title", name_file="histo",
                            bins=[0, 1, 2, 4, 8, 16, 32, 64, 128, 200],
                            integral=False,
                            n_bins_middle=5,
                            dict_dict=True):
    """
    Create  visualizations for the analysis results with improved period distribution plots
    """
    pl_name = f"{en_t}"
    # Visualize results
    if select is None:
        select = {'lev-1': "default_analysis",
                  'lev-2': "neg-pos-res",
                  'col-1': 'period_neg',
                  'col-2': 'period_pos',
                  'col-1a': 'integral_neg',
                  'col-2a': 'integral_pos',

                  }
    if dict_dict:
        act_df = results[select['lev-1']][select['lev-2']]
    else:
        act_df = results
    if integral:
        bins_all = []
        for i_d, dat_bin in enumerate([act_df[select['col-1a']], act_df[select['col-2a']]]):
            p10 = int(np.percentile(dat_bin, 10))
            p90 = int(np.percentile(dat_bin, 90))
            if i_d==0:
                p90=-1
            elif i_d==1:
                p10 =1
            print(p90, p10)
            # Create bin edges
            middle_bins = np.linspace(p10, p90, n_bins_middle + 1, dtype=int)
            bins_all.append(np.concatenate(
                [[int(np.floor(dat_bin.min()))], middle_bins,
                 [int(np.ceil(dat_bin.max()))]]))
        histo_2, xedges, yedges = np.histogram2d(
            act_df[select['col-1a']], act_df[select['col-2a']], bins=bins_all)
    else:

        histo_2, xedges, yedges = np.histogram2d(
            act_df[select['col-1']], act_df[select['col-2']], bins=bins)

    histo_2=histo_2.T
    x_hist = np.histogram(act_df[select['col-1a']], bins=xedges)
    y_hist = np.histogram(act_df[select['col-2a']], bins=yedges)
    hist_2n = np.zeros((n_bins_middle+3, n_bins_middle+3))
    hist_2n[:-1, :-1]=histo_2
    hist_2n[:-1, -1]=y_hist[0]
    hist_2n[-1, :-1]=x_hist[0]
    histo_2 = hist_2n
    fig0, ax0 = plt.subplots(1, figsize=(
        10, 8), constrained_layout=True)
    

    ax0.imshow(histo_2, cmap="YlGnBu_r")
    xranges = [
        f"{xedges[i]:.0f} - {xedges[i+1]:.0f}" for i in range(len(xedges) - 1)]
    yranges = [
        f"{yedges[i]:.0f} - {yedges[i+1]:.0f}" for i in range(len(xedges) - 1)]
    xranges.append("sum")
    yranges.append("sum")
    ax0.set_xticks(np.arange(len(xranges)), labels=xranges,
                   rotation=45, ha="right", rotation_mode="anchor")
    ax0.set_yticks(np.arange(len(yranges)), labels=yranges)
    ax0.tick_params(axis="both", labelsize=12)
    for i in range(len(yranges)):
        for j in range(len(xranges)):
            if histo_2[i, j] > histo_2.max()/2:
                ax0.text(j, i, f"{histo_2[i, j]:.0f}",
                         ha="center", va="center", color="k", fontsize=14)
            elif histo_2[i, j] > 0:
                ax0.text(j, i, f"{histo_2[i, j]:.0f}",
                         ha="center", va="center", color="w", fontsize=14)
            

    ax0.set_title(pl_name+", 2D Int-Histogram")
    fig0.tight_layout()
    fig0.savefig(app_suf(name_file, "-2D-hist-int.png"))
    plt.show()
    df = pd.DataFrame(histo_2.T, index=yranges, columns=xranges)

    # xedges als eigene Spalte hinzufügen
    #df.insert(0, "y_edges_start", yedges[:-1])

    # CSV speichern
    df.to_csv(app_suf(name_file, "integral-histogram_data.csv"))


if __name__ == "__main__":

    data_out = generate_test_data(duration_hours=48, resolution_minutes=60)

    # Analyze with different thresholds
    result = residual_analyse(
        data_out, 'value',
        thresholds={'basic': -0.1, 'direct': 0.}
    )
    print("\n", result["basic_threshold_analysis"]["period_data"])
    fig, (ax1, ax2) = plt.subplots(2)
    sbn.scatterplot(data=result["basic_threshold_analysis"]
                    ["neg-pos-res"], x="period", y="period-pos", ax=ax1)
    sbn.scatterplot(data=result["direct_threshold_analysis"]
                    ["neg-pos-res"], x="period", y="period-pos", ax=ax1)
    data_out.plot(y="value", ax=ax2)

    # Basic sign-based analysis
    result1 = residual_analyse(data_out, 'value')
    print("\n", result1["default_analysis"])
    # # With basic threshold
    # result2 = residual_analyse(data, 'value',
    #     thresholds={'basic': 10})

    # # With basic and direct thresholds
    # result3 = residual_analyse(data, 'value',
    #     thresholds={

    #         'direct': 0,

    #     })
