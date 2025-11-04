# -*- coding: utf-8 -*-
"""
Created on Thu Jan 16 11:16:16 2025

@author: atakan
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import requests
import zipfile
import numpy as np
import os

from numpy.polynomial import Polynomial
from scipy import signal

from rws_py import weather_load_storage
from rws_py import generate_load_curve
from rws_py import analyze_residual
from rws_py import RESULTS_DIR, WEATHER_DATA_DIR


pd.set_option('display.max_columns', None)

WITH_LOAD = True  # analyze the weather data togeher with an estimated load or not

SOLAR_THRESHOLD = 0  # J/cm2 [x10000/600 -> W/m²] ; ca. 100 W/m2
# km/h (converted: 1 m/s = 3.6 km/h), energy conversion:cubic
WIND_THRESHOLD = 0


# URLs for DWD data Düsseldorf/Cuxhaven
stations = {"Cuxhaven": '00891',
            "Düsseldorf": '01078',
            'Freiburg': '01443'}
# stations = {"Cuxhaven": '00891'}
# ACT_STATION = "Düsseldorf"
SOLAR_URL_BASE = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/solar/historical"
WIND_URL_BASE = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/wind/historical"

# SOLAR_ACT = '10minutenwerte_SOLAR_' + \
#     stations[ACT_STATION]+'_20200101_20231231_hist.zip'
# WIND_ACT = '10minutenwerte_wind_' + \
#     stations[ACT_STATION]+'_20200101_20231231_hist.zip'
solar_columns = ['MESS_DATUM', 'QN', 'GS_10']
wind_columns = ['MESS_DATUM', 'QN', 'FF_10']

DATA_SOURCE =  WEATHER_DATA_DIR


def load_data(bse_url_in, filename_in, exp_col, directory=DATA_SOURCE,
              energy_column=2,
              wind_bounds=(3.3, 11.0, 25),
              normalize=True,
              resample=None):
    """
    Load weatherdata from a directory if it already exists,
    and only download and save if it does not exist.


    Parameters
    ----------
    bse_url_in : string
        url from websiteN.
    filename_in : string
        DESCRIPTION.
    exp_col : List
        Which column (names) are expected at least in the file.
    directory : string, optional
        folder to look for data first and store them after downloading, when
        they do not exist. The default is DATA_SOURCE.
    energy_column : Integer, optional
        position of thecolumn within expected_columns, where the solar energy
        density or wind velocity is to be found. The default is 2.
    wind_bounds : list or tuple of length 3, optional
        Minimum, nominal and maximum wind speed of turbine in m/s . The default
        is (3.3, 11.0, 25).
    normalize : Boolean, optional
        for normalizing the "power" column by its mean value, The default
        value is True.
    resample : String/None, optional
        if 'h' the data will be resampled to hourly, taken the mean(other
        resampling would also be ok, check the panadas resample manual). If it
        is None, no resampling will be performed. The default is None.

    Raises
    ------
    IOError
        DESCRIPTION.
    KeyError
        DESCRIPTION.

    Returns
    -------
    df : Pandas DataFrame
        The data with the important values in the power column and the datime
        as index.

    """

    verbose = False
    filepath = os.path.join(directory, filename_in)
    if os.path.exists(filepath):
        print(f"Data found: {filename_in}")
    else:
        url_act = bse_url_in+"/"+filename_in
        print(f"Data not found: {filename_in}. Downloading...")
        response = requests.get(url_act)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"File downloaded and saved: {filename_in}")
        else:
            raise IOError(f"Failed to download file: {filename_in}")

    with zipfile.ZipFile(filepath) as z:
        csv_filename = z.namelist()[0]
        with z.open(csv_filename) as csv_file:
            df = pd.read_csv(csv_file, sep=None, engine='python', header=0)

    # Debug: Zeige die tatsächlichen Spaltennamen
    if verbose:
        print("Actual columns:", df.columns.tolist())

    df.columns = df.columns.str.strip()
    df = df.replace(-999, 0)

    # Debug: Zeige die Spaltennamen nach strip()
    if verbose:
        print("Columns after strip:", df.columns.tolist())

    # Check for missing columns before proceeding
    missing_columns = [
        col for col in exp_col if col not in df.columns]
    if missing_columns:
        raise KeyError(
            f"The following columns are missing in the data: {missing_columns}")
    energy_column = exp_col[energy_column]

    # Prüfe, ob das Format der MESS_DATUM-Spalte numerisch ist (Wind-Daten)
    if df['MESS_DATUM'].dtype == 'int64' or df['MESS_DATUM'].dtype == 'object' \
        and df['MESS_DATUM'].str.isnumeric().all():
        df['MESS_DATUM'] = pd.to_datetime(
            df['MESS_DATUM'], format='%Y%m%d%H%M')

    else:
        df['MESS_DATUM'] = pd.to_datetime(df['MESS_DATUM'])

    if filename_in.find("SOLAR") > 0:
        df["power"] = df[energy_column]*16.66  # from J/(cm2 h) to W/m2

        df["solar intensity / (J/cm2/10 min)"] = df[energy_column]
    elif filename_in.find("wind") > 0:
        df["power"] = (df[energy_column])**3
        df["velocity / (m/s)"] = df[energy_column]  # km/h ->m/s

        df.loc[(df[energy_column] > wind_bounds[1]),
               "power"] = wind_bounds[1]**3  # reaching the nominal wind speed
        df.loc[(df[energy_column] < wind_bounds[0]) | (df[energy_column]
                                                       > wind_bounds[2]),
               "power"] = 0  # too low or too high velocity

    else:
        print("Problem: Neither wind nor solar data!")


    df.set_index('MESS_DATUM', inplace=True)  # dateime is Index now
    if resample is not None:
        df = df.drop('eor', axis=1).resample(resample).mean()
    df['time_diff_seconds'] = df.index.to_series().diff().dt.total_seconds()

    if normalize:
        # Jahrweise Mittelwert berechnen
        mean_act = df.groupby(df.index.year)['power'].transform('mean')

        # Originalwerte speichern
        df["power not normalized"] = df["power"].copy()

        # Jahrweise Normierung
        df["power"] = df["power"] / mean_act


    return df


def resample_to_hourly(data_in, energy):
    """
    Resample 10-minute data to hourly data by taking the mean.
    """

    data_hourly_in = None
    if energy == "Solar":

        data_hourly_in = data_in.resample('h').mean()

    elif energy == "Wind":

        data_hourly_in = data_in.resample('h').mean()  # BA must be checked!
    return data_hourly_in


def analyze_weather(data, column, threshold, time_per_point=1):
    """
    Analyze weather data based on periods above and below a threshold.
    """
    data = data.copy()
    # Create sign series based on the threshold
    data['above_threshold'] = data[column] > threshold
    data['block'] = (data['above_threshold'].diff() != 0).cumsum()

    # Calculate period length in hours (hourly intervals -> hours)
    data['count'] = 1  # 1 hour per row, for aggregation
    data['count'] = data.groupby('block')['count'].transform(
        'sum') * time_per_point  # Convert to hours

    # Calculate the total number of inactive periods per block (scaled to hours)
    df_period = data.groupby('block')[column].agg(
        ['count', 'mean', 'std', 'sum', 'min', 'max']).reset_index()

    # Calculate the mean for active periods
    df_period['mean'] = df_period.apply(
        lambda row: data[data['block'] == row['block']][column].mean(), axis=1)
    df_period['count'] = df_period['count'] * time_per_point

    # Lists for active-inactive and inactive-active combinations
    active_inactive_list = []
    inactive_active_list = []

    for i in range(len(df_period)):
        current_row = df_period.iloc[i]
        current_row = current_row.copy()
        if i + 1 < len(df_period):
            next_row = df_period.iloc[i + 1]
            if current_row['mean'] > threshold:
                # Active-Inactive combination
                if not df_period.iloc[i + 1]['mean'] > threshold:
                    count_inv = next_row['count']
                    # Add the value as a new column in current_row
                    current_row['count_inv'] = count_inv
                    active_inactive_list.append(current_row)
            else:
                # Inactive-Active combination
                if df_period.iloc[i + 1]['mean'] > threshold:
                    count_inv = next_row['count']
                    # Add the value as a new column in current_row
                    current_row['count_inv'] = count_inv
                    inactive_active_list.append(current_row)

    # Ensure that the lists for active and inactive periods are 2D data
    # Use `.concat()` on the list of DataFrames and ensure the DataFrame is created correctly
    df_active_inactive = pd.DataFrame(active_inactive_list)
    df_inactive_active = pd.DataFrame(inactive_active_list)

    return df_period, df_active_inactive, df_inactive_active


# Modifizierte Visualisierungsfunktion


def plot_enhanced_analysis(data, results, column, threshold, en_t, year, fil_name):
    """
    Create enhanced visualizations for the analysis results with improved period distribution plots
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

    # Plot 1: Time series with thresholds
    part = data.iloc[7000:10000]
    sns.lineplot(data=part, y=column, x="MESS_DATUM", ax=ax1)
    ax1.axhline(threshold, color='k', label='Basic threshold', linestyle='--')
    ax1.axhline(results['direct_threshold'], color='r',
                label='Direct usage threshold', linestyle=':')
    ax1.set_title(f'Time Series with Thresholds\n{en_t}, {year}')
    ax1.legend()

    # Plot 2: Period Length Distributions (log scale)
    # Verbesserte Darstellung der Periodenlängen mit logarithmischer Skala
    ax2.set_xscale('linear')
    ax2.set_yscale('linear')
    bins = np.linspace(
        1, max(results['active_inactive']['count'].max(), 1), 30)
    if not results['active_inactive'].empty:
        sns.histplot(data=results['active_inactive'], x='count', ax=ax2,
                     label='Basic threshold periods', bins=bins, alpha=0.6)

    if not results['direct_period_data'].empty:
        sns.histplot(data=results['direct_period_data'], x='count', ax=ax2,
                     label='Direct usage periods', color='r', bins=bins, alpha=0.4)

    ax2.set_title('Period Length Distribution')
    ax2.set_xlabel('Period length (hours)')
    ax2.set_ylabel('Count')
    ax2.legend()

    # Plot 3: Scatter plot of period lengths vs intensities
    if not results['active_inactive'].empty:
        sns.scatterplot(data=results['active_inactive'],
                        x='count', y='mean',
                        size='sum',
                        alpha=0.6,
                        ax=ax3)
        ax3.set_xscale('linear')
        ax3.set_title('Period Length vs Intensity')
        ax3.set_xlabel('Period length (hours)')
        ax3.set_ylabel('Mean intensity')

    # Plot 4: Cumulative distribution of period lengths
    if not results['active_inactive'].empty:
        counts_sorted = np.sort(results['active_inactive']['count'])
        cumulative = np.arange(1, len(counts_sorted) + 1) / len(counts_sorted)
        ax4.plot(counts_sorted, cumulative, 'b-', label='Basic threshold')

    if not results['direct_period_data'].empty:
        counts_sorted_direct = np.sort(results['direct_period_data']['count'])
        cumulative_direct = np.arange(
            1, len(counts_sorted_direct) + 1) / len(counts_sorted_direct)
        ax4.plot(counts_sorted_direct, cumulative_direct,
                 'r-', label='Direct usage')

    ax4.set_xscale('log')
    ax4.set_title('Cumulative Distribution of Period Lengths')
    ax4.set_xlabel('Period length (hours)')
    ax4.set_ylabel('Cumulative probability')
    ax4.legend()

    plt.tight_layout()
    plt.savefig(fil_name + "-enhanced-analysis.png",
                bbox_inches='tight', dpi=300)
    plt.show()


def plot_analysis(data, results, column, threshold, en_t, year, fil_name,
                  period_pause,
                  bins=[0, 1, 2, 4, 8, 16, 32, 64, 128, 200]):
    """
    Create  visualizations for the analysis results with improved period distribution plots
    """
    # Visualize results
    fig0 = plt.figure()

    sns.scatterplot(data=results['direct_inactive'],
                    x='count', y='count_inv', size='sum', hue='mean')
    plt.title(f'Active vs Inactive Periods, {en_t}, {year}')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
    plt.tight_layout()
    plt.savefig(str(fil_name)+"-periods.png")
    plt.show()
    # plt.figure()
    histo2, xedges, yedges = np.histogram2d(
        results['direct_inactive']['count_inv'], results['direct_inactive']['count'], bins=bins)

    fig0, ax0 = plt.subplots(1)

    ax0.imshow(histo2)
    xranges = [
        f"period {xedges[i]:.1f} - {xedges[i+1]:.1f}" for i in range(len(xedges) - 1)]
    yranges = [
        f"pause {yedges[i]:.1f} - {yedges[i+1]:.1f}" for i in range(len(xedges) - 1)]
    ax0.set_xticks(np.arange(len(xranges)), labels=xranges,
                   rotation=45, ha="right", rotation_mode="anchor")
    ax0.set_yticks(np.arange(len(yranges)), labels=yranges)
    for i in range(len(yranges)):
        for j in range(len(xranges)):
            if histo2[i, j] > 0:
                ax0.text(j, i, f"{histo2[i, j]:.0f}",
                                ha="center", va="center", color="w", fontsize=10)

    ax0.set_title(fil_name+", 2D Histogram")
    fig0.tight_layout()
    fig0.savefig(fil_name+"-2D-hist.png")
    plt.show()
    df = pd.DataFrame(histo2.T, index=yranges, columns=xranges)

    # xedges als eigene Spalte hinzufügen
    df.insert(0, "y_edges_start", yedges[:-1])

    # CSV speichern
    df.to_csv(fil_name+"histogram_data.csv")

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(ncols=2, nrows=2)

    pcm = ax1.pcolormesh(xedges, yedges, histo2, cmap='rainbow')
    fig.colorbar(pcm, ax=ax1)
    ax1.set_xlabel("Period length / h")
    ax1.set_ylabel("pause length / h")
    sum_count_fit = Polynomial.fit(
        results['direct_inactive']['count'], results['direct_inactive']['sum'], 2)
    ax2.plot(results['direct_inactive']['count'],
             results['direct_inactive']['sum'], "+k")
    ax2.plot(results['direct_inactive']['count'], sum_count_fit(
        results['direct_inactive']['count']), '.')
    ax2.set_xlabel("Period length / h")
    ax2.set_ylabel("total intensity")
    ax3.plot(period_pause['count'], period_pause['mean'], "+k")
    ax3.set_xlabel("Period length / h")
    ax3.set_ylabel("mean intensity")

    act_corr = signal.correlate(data[column], data[column])
    # f, Pxx_den = signal.periodogram(data[expected_columns[2]], fs=1/600)
    # ax4.semilogy(f, Pxx_den)
    ax4.plot(act_corr)
    ax4.set_xlabel("time shift / h")
    ax4.set_ylabel("autocorrelation")
    fig.suptitle(en_t)
    fig.savefig(fil_name+"-cor-hist.png")
    plt.show()

    # for illustration
    fff, (aaa, aab) = plt.subplots(2)
    part = data.iloc[7000:10000]
    sns.lineplot(data=part, y=column, x="MESS_DATUM", ax=aaa)
    aaa.axhline(threshold, color='k')
    aaa.set_title(en_t)
    # Erstelle den Inlay-Plot
    # Erstellen Sie Achsen für den Inlay-Plot

    sns.lineplot(data=data, y=column, x="MESS_DATUM", ax=aab)
    aab.axhline(threshold, color="k")
    aab.set_title('All Data')  # optional
    fff.savefig(fil_name+"-timeseries.png")
    plt.show()
    fig_n, axn = plt.subplots(1)

    results['direct_inactive'].hist(
        column='count_inv', ax=axn, bins=bins, log=True)
    results['direct_inactive'].hist(
        column='count', ax=axn, bins=bins, rwidth=.75, log=True)
    axn.set_xlabel("period/pause duration / h")
    axn.legend(["pause", 'with'])

    axn.set_title(en_t+", histogram")


if __name__ == "__main__":
    VERBOSE = True

    columns = ["Station", "Year", "power", "Threshold", "sum", "mean",
               "10 min periods", "periods>1h", "sum with energy",
               "sum without energy", "ratio of period lengths",
               "mean_active_periods", "direct_threshold",
               "storage_periods_count", "period_mean_duration", "mean_pause_duration",
               'std_pause_duration',
               'std_duration']

    evaluation = pd.DataFrame(columns=columns)
    outp = []
    histos = []
    BINS = 30

    all_dat = []
    ENERGY_COLUMN = "power"  # Name of the column with the energy proportional data

    # Prepare data sources
    for ACT_STATION in stations.keys():
        SOLAR_ACT = '10minutenwerte_SOLAR_' + \
            stations[ACT_STATION]+'_20200101_20240902_hist.zip'
        WIND_ACT = '10minutenwerte_wind_' + \
            stations[ACT_STATION]+'_20200101_20241231_hist.zip'
        all_dat.append([SOLAR_URL_BASE, SOLAR_ACT,
                       solar_columns, SOLAR_THRESHOLD, ACT_STATION])
        all_dat.append([WIND_URL_BASE, WIND_ACT, wind_columns,
                       WIND_THRESHOLD, ACT_STATION])

    # Main analysis loop
    for dat_act in all_dat:
        base_url = dat_act[0]
        filename = dat_act[1]
        expected_columns = dat_act[2]
        thresh_out = dat_act[3]
        ACT_STATION = dat_act[4]

        # Load data and  # Resample data to hourly
        data_all = load_data(base_url, filename, expected_columns,
                             resample="h")

        # Process each year
        for year in range(2020, 2022):
            print(f"year: {year}\n")
            en_t = ACT_STATION+", "
            if dat_act[0].count('wind'):
                act_energy = "Wind"
            else:
                act_energy = "Solar"
            en_t += act_energy
            f_name = f"{en_t}, {year}"
            f_base=f_name.replace(", ", "-")
            dir_name = RESULTS_DIR

            fil_name = dir_name / f_base
            data_hourly = data_all[data_all.index.year == year]

           
            description = data_hourly.describe()
            description.to_csv(f"{fil_name.stem}-describe.csv", sep=";")

            if WITH_LOAD:
                load_par = {
                    'min_weekday': 0.650,
                    'max_weekday': 1.0,
                    'min_weekend': 0.650,
                    'max_weekend': 0.85,  # only for step-function
                    'intermediate_fraction': .75,
                    # scales everything
                    'multiplier': data_hourly["power"].mean()
                }
                load_df = generate_load_curve(
                    data_hourly.index, load_parameters=load_par)
                with_load = weather_load_storage(data_hourly, load_df)
                # BA with load must be stored and evaluated/plotted

            if VERBOSE:
                print(description)
            # Perform enhanced analysis (includes basic analysis)
            if WITH_LOAD:
                data_hourly = with_load.copy()
                results_act = analyze_residual(data_hourly, "residual-no-storage")

            else:
                pass

            # Extract results for further processing
            period_pause = results_act['active_inactive']
            long_per_pause = period_pause[period_pause['count'] >= 1]

            # Calculate metrics
            sum_all = data_hourly[ENERGY_COLUMN].sum()
            mean_all = data_hourly[ENERGY_COLUMN].mean()
            sh_periods = period_pause['count'].count()
            long_periods = long_per_pause['count'].count()
            periods_with_energy = period_pause['count'].sum()
            periods_without_energy = period_pause['count_inv'].sum()
            per_ratio = periods_with_energy / \
                periods_without_energy if periods_without_energy != 0 else 0

            # Print analysis results
            print(
                f"Threshold:{thresh_out:.1f}, No.-10 min periods: {sh_periods}, above 1h: {long_periods}")
            print(
                f"Sum of all times, with energy {periods_with_energy:.1f}, without {periods_without_energy:.1f}, ratio:{per_ratio:.3f} \n")

            # Create evaluation row
            eval_row = [
                ACT_STATION,
                year,
                act_energy,
                thresh_out,
                sum_all,
                mean_all,
                sh_periods,
                long_periods,
                periods_with_energy,
                periods_without_energy,
                per_ratio,
                results_act['basic_stats']['mean_active_periods'],
                results_act['direct_threshold'],
                results_act['storage_periods']['count'],
                results_act['storage_periods']['mean_duration'],
                results_act['storage_periods']['mean_pause_duration'],
                results_act['storage_periods']['std_pause_duration'],
                results_act['storage_periods']['std_duration'],
            ]

            # Add to evaluation DataFrame
            evaluation.loc[len(evaluation)] = eval_row

            # Create visualizations
            plot_analysis(
                data_hourly, results_act, ENERGY_COLUMN, thresh_out, en_t, year,
                str(fil_name)+"-H-",
                period_pause)
            plot_enhanced_analysis(
                data_hourly, results_act, ENERGY_COLUMN, thresh_out, en_t, year,
                str(fil_name)+"-H-")

    # Save final results
    evaluation.to_csv(dir_name/("H-"+"all-eval-enhanced.csv"),
                      sep=";", encoding='utf-8')
