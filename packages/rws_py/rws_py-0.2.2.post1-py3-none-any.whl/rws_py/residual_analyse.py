# -*- coding: utf-8 -*-
"""
Analyse the rsidual loads from different countries statistically

with respect to the correlation of periods with positive and negative residual loads.
sum: integral (Energy)
mean: measure for Power
count: period (in h)
and further values are also calculated like the 25%, 75% etc.

Context: SPP2403 Cooperation Atakan / Bertsch

Created on Thu Dec  5 10:00:37 2024

@author: atakan

"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sbn
from scipy import signal

from rws_py import DATA_DIR, RESULTS_DIR
plt.close("all")

# Beispiel-Daten (ersetze durch deine eigene Datenserie)
# data_0 = pd.DataFrame(
#     {'Residuallast': [5, 1, 2, -2, -1, -3, 5, 2, -4, -6, 8, 1, 6, 7, 8]})
test = False
dir_name = RESULTS_DIR
f_name_base = dir_name/"res_store"

def analyze_residual(data, column, verbose=False):
    """
    Analyze Residual load data for periods of negative residuals followed by positive

    with respect to time (length), integral(sum)=energy and the mean values
    of each period.

    Parameters
    ----------
    data : pd.DataFrame
        to be analyzed.
    column : string
        the column with the data to be analyzed.
    verbose : Boolean, optional
        if you want some printing. The default is False.

    Raises
    ------
    KeyError
        DESCRIPTION.

    Returns
    -------
    results : dictionary with three entries, as follows
        -""
    df_period : pd.DataFrame
        all periods ith the folowing one of opposite sign .
    df_pos_neg : pd.DataFrame
        positive residual load  periods with the folowing one of opposite sign .
    df_neg_pos : pd.DataFrame
        negative residual load  periods with the folowing one of opposite sign .

    """

    # Vorzeichenserien erstellen
    data['sign'] = np.sign(data[column])

    # Finden Sie die Perioden positiver und negativer Zahlen
    data['block'] = (data['sign'].diff() != 0).cumsum()

    # Statistik für jede Periode erstellen
    df_period = data.groupby('block')[column].agg(
        ['count', 'mean', 'std', 'sum', 'min', 'max']).reset_index()
    df_period['25%'] = data.groupby('block')[column].quantile(0.25).values
    df_period['50%'] = data.groupby('block')[column].quantile(0.5).values
    df_period['75%'] = data.groupby('block')[column].quantile(0.75).values
    df_period['positive'] = df_period['sum'] > 0

    # Listen für Positive-Negative und Negative-Positive Kombinationen
    pos_neg_list = []
    neg_pos_list = []

    # Iteriere durch die Perioden und kombiniere sie
    for i in range(len(df_period)):
        current_row = df_period.iloc[i]

        if current_row['positive']:
            # Positive-Negative Kombination
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
            # Negative-Positive Kombination
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

    # DataFrames erstellen
    df_pos_neg = pd.DataFrame(pos_neg_list).reset_index(drop=True)
    df_neg_pos = pd.DataFrame(neg_pos_list).reset_index(drop=True)

    # Ergebnisse anzeigen
    if verbose:
        print("Positive-Negative Perioden (fehlende negative Werte mit Nullen aufgefüllt):")
        print(df_pos_neg)

        print(
            "\nNegative-Positive Perioden (fehlende positive Werte mit Nullen aufgefüllt):")
        print(df_neg_pos)
    return df_period, df_pos_neg, df_neg_pos




def storage(power, actual_capacity, full_capacity, efficiency=1, time_step=1,
            sp_names=None):
    """
    Simple storage model without power restriction but max. capacity.

    Parameters
    ----------
    power : Float
        power entering the storage (=positive) or wanted(=negative), if possible
                    with the actual state of charge.
    actual_capacity : Float
        what is the actual charge (energy).
    full_capacity : Float
        what is the full capacity.
    efficiency : Float, optional
        discharging efficiency. The default is 1.
    time_step : Float, optional
        time step relative to the next value in hours. The default is 1.
    sp_names : list of strings, optional
        the names of the three values calculated. The default is None.
    Returns
    -------
    result_dict : Dictionary

        - "act_st_cap" actual loading/energy after the time step
        - "power_st_in": the real power entering/exiting the storage
        - "SOC": state of charge.

    """

    if power >= 0:  # Laden
        if actual_capacity < full_capacity - power*time_step:
            pass
        elif actual_capacity < full_capacity:
            power = (full_capacity - actual_capacity)/time_step
        else:
            power = 0
        actual_capacity += time_step*power
    else:  # Entladen
        power_with_efficiency = power / efficiency  # Berücksichtige Effizienz bei der Entladeleistung
        if actual_capacity > np.abs(time_step*power_with_efficiency):
            pass
        elif actual_capacity > 0:
            power = -actual_capacity*efficiency/time_step  # Anpassen der Leistung basierend auf verfügbarer Kapazität
        else:
            power = 0
        actual_capacity += time_step * power_with_efficiency

    # Sicherheitscheck für numerische Ungenauigkeiten
    actual_capacity = max(0, min(actual_capacity, full_capacity))

    soc = actual_capacity/full_capacity
    if not sp_names:
        sp_names = ["act_st_cap", "power_st_in", "SOC"]
    result_dict = dict(zip(sp_names, [actual_capacity, power, soc]))

    return result_dict

def create_filenames(value, base=None):

    exponent = int(np.floor(np.log10(value)))  # Berechne den Exponenten
    base_value = value / (10 ** exponent)  # Basiswert berechnen

    # Runden die Basis auf 3 signifikante Stellen und ohne Dezimalstellen
    # Multiplizieren und umwandeln in Ganze Zahl zur Eliminierung der Dezimalstellen
    rounded_value = round(base_value, 3)

    # Entferne Punkte durch Umwandlung in integer und formatiere den Namen
    filename = f"{int(rounded_value * 1000)}E{exponent - 3}"

    return base+filename




def eval_df_pos_neg(df, col, time=1, verbose=False):
    positive_residuals = df[df[col] > 0][col]
    positive_mean = positive_residuals.mean()
    positive_sum = positive_residuals.sum()
    positive_count = positive_residuals.count()
    # Berechnung für negative Residualwerte
    negative_residuals = df[df[col] < 0][col]
    negative_mean = negative_residuals.mean()
    negative_sum = negative_residuals.sum()
    negative_count = negative_residuals.count()
    if verbose:
        # Ausgabe der Ergebnisse
        print(f"""Positive Residuals: Mittelwert: {
              positive_mean:.2e}, Summe: {positive_sum:.2e}""")
        print(f"""Negative Residuals: Mittelwert: {
              negative_mean:.2e}, Summe: {negative_sum:.2e}""")
        print(f"""summe Residuals: Mittelwert: {
              positive_mean+negative_mean:.2e},
            Summe: {positive_sum+negative_sum:.2e}""")

    return np.array([positive_mean, positive_sum, positive_count, negative_mean,
                     negative_sum, negative_count])

def calc_capacity_dependence(in_ser, m_cap, EFF_STOR=0.75,
                             make_df=False,
                             verbose = False,
                             file_name = 'cap_res-',
                             title = None):
    """
    Calculate a storage (dis-)charging as a function of residual loads

    Parameters
    ----------
    in_ser : pd.Series
        hourly Residual loads (neg->entering).
    m_cap : array of floats
        storage capacities for which the behaviour is calculated.
    EFF_STOR : Float, optional
        discharging efficiency of the storage. The default is 0.75.
    make_df : Boolean, optional
        shall all results be returned as pd.DataFrame or as some numpy.arrays.
        The default is False.
    verbose : Boolean, optional
        if printing is wanted. The default is False.
    file_name : string, optional
        place to store the results, the name will be extended. The default
        is 'cap_res-'.

    Returns
    -------
    Dataframe
        assessment as  function of the residual loads time series.
    or numpy arrays
        if make_df=False, cap_dep_res, st_state, la, cap_change.

    """
    cap_dep_res = []
    st_state = []
    cap_change = []
    la = []
    in_df = pd.DataFrame(in_ser)
    in_df.columns = ["residual"]

    for mca in m_cap:
        cap = 0  # Initiale Speicherkapazität

        fn_act = create_filenames(mca, file_name)

        results = []
        for po in in_df["residual"]:
            st_res = storage(-po, cap, mca, efficiency=EFF_STOR)
            results.append(st_res)
            cap = st_res["act_st_cap"]
        results = pd.DataFrame(results)
        #results.set_index('row_num', inplace=True)
        in_df.set_index(results.index, inplace=True)


        actual_df = pd.concat([in_df, results], axis=1)
        actual_df["row_num"] = actual_df.index
        actual_df["pow_rest"] = actual_df["residual"] + actual_df["power_st_in"]

        # Berechne die Differenzen und weitere Statistiken
        actual_df['change_act_st_cap'] = actual_df['act_st_cap'].diff()

        fi_, ax_ = plt.subplots(3)
        sbn.lineplot(data=actual_df, x="row_num", y="SOC",
                        ax=ax_[0], color='b')
        sbn.lineplot(data=actual_df, x="row_num", y="pow_rest",
                        ax=ax_[1], color='b')
        sbn.lineplot(data=actual_df, x="row_num", y="residual",
                        ax=ax_[2], color='k')
        ax_[0].set_title(title+f", Cap: {mca:2.2e}")
        fi_.savefig(fn_act+".jpg")



        soc_counts = actual_df['SOC'].value_counts()
        zero_count = soc_counts.get(0, 0)  # Anzahl der 0en
        one_count = soc_counts.get(1, 0)    # Anzahl der 1en



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
            print(f"Max. storage capacity: {mca}")
            print(f"""Anzahl der Werte 0 in 'SOC': {
                  zero_count} und 1 in 'SOC': {one_count}""")
            print(f"""Anzahl der Wechsel von 0 auf einen höheren Wert: {
                  from_0_to_higher}; von 1 auf einen niedrigeren Wert: {
                from_1_to_lower}""")

        st_state.append(np.array([zero_count,
                                 one_count,
                                 from_0_to_higher,
                                 from_1_to_lower]))


        # Zugrunde liegende Werte zur LA Auswertung
        time_pos_res_remain = actual_df[actual_df['pow_rest'] > 0].count()['pow_rest']
        time_neg_res_remain = actual_df[actual_df['pow_rest'] < 0].count()['pow_rest']
        time_no_res_remain = actual_df[actual_df['pow_rest'] == 0].count()['pow_rest']

        la_pos = 1 - (time_pos_res_remain / actual_df["pow_rest"].count())
        la_neg = 1 - (time_neg_res_remain / actual_df["pow_rest"].count())
        la_eq = (time_no_res_remain / actual_df["pow_rest"].count())
        la.append(np.array([la_pos, la_neg, la_eq]))

        cap_change.append(eval_df_pos_neg(actual_df, "change_act_st_cap"))

        # Ergebnisse sammeln
        pos_neg_stat = eval_df_pos_neg(actual_df, "pow_rest")
        cap_dep_res.append(np.array([*pos_neg_stat, actual_df["act_st_cap"].iloc[-1]]))
        actual_df.to_csv(fn_act+".csv", sep=";")



    cap_dep_res = np.array(cap_dep_res)
    st_state = np.array(st_state)
    la = np.array(la)
    cap_change= np.array(cap_change)

    # Rückgabe je nach Bedarf



    if make_df:
        cd_names=['load_pos_mean', 'load_pos_sum', 'load_pos_count', 'load_neg_mean', 'load_neg_sum', 'load_neg_count', "final_storedCharge"]
        st_names =["empty", "full", "0->up", "1->down"]
        la_names= ["LA+", "LA-", "eq_ratio"]
        cap_change_names=['load_diff_pos_mean', 'load_diff_pos_sum', 'load_diff_pos_count', 'load_diff_neg_mean', 'load_diff_neg_sum', 'load_diff_neg_count']
        col_names = [ *cd_names, *st_names, *la_names, *cap_change_names]
        combined_df = pd.DataFrame(np.hstack((cap_dep_res, st_state, la, cap_change)), columns=col_names)
        combined_df["storage capacity"] = m_cap
        combined_df["Eff_dis"] = EFF_STOR
        combined_df.to_csv(file_name+"_cap_dependence.csv",sep=";")
        return combined_df
    else:
        return cap_dep_res, st_state, la, cap_change


def esm_residual_to_df(country=None, file_in=None,
                       col_name="residual-no-storage", first_day=None,
                       save_csv=True, verbose=False,
                       get_countries=False,
                       normalize=True):
    """
    Reads ESM residual load data from a CSV or Excel file, extracts the data for a specific country,
    sets the date as the index, and optionally normalizes the data.

    Parameters:
    -----------
    country : str, optional
        The country for which the residual load data should be extracted.
        Defaults to "DE0 Tot" if not specified.

    file_in : str, optional
        The filename (without extension) containing the residual load data.
        If None, defaults to '2024_Bertsch_residual_Load'.

    col_name : str, optional
        The name of the column to store the extracted residual load data.
        Default is "residual-no-storage".

    first_day : str, optional
        Not used in the current function.

    save_csv : bool, optional
        If True, saves the extracted and transposed data to a CSV file for future use. Default is True.

    verbose : bool, optional
        If True, prints the first few rows of the dataset and the index for debugging purposes. Default is False.

    get_countries : bool, optional
        If True, returns a list of available country names from the dataset instead of extracting data. Default is False.

    normalize : bool, optional
        If True, normalizes the extracted residual load data by computing
        the absolute mean of the negative values (=> positive!).
        The original values are then divided by this value. Default is True.

    Returns:
    --------
    pd.DataFrame or list
        - If `get_countries` is True: Returns a list of available country names.
        - Otherwise: Returns a DataFrame with extracted residual load data for the specified country.

    Raises:
    -------
    ValueError
        If the specified file cannot be loaded.

    FileNotFoundError
        If neither the CSV nor the Excel file is found.

    Notes:
    ------
    - The function first attempts to read data from a CSV file. If the CSV is missing, it tries to read from an Excel file.
    - If an Excel file is used, the dataset is transposed, and a datetime index is generated starting from '2050-01-01 00:00:00' with hourly frequency.
    - Normalization is performed only if the normalization factor (difference between mean positive and mean negative values) is nonzero.
    """

    COL_N_ORIGINAL = "residual-original"
    if file_in is None:
        file_in = '2024_Bertsch_residual_Load'

    # **Pfad zum data-Ordner setzen**
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Ordner von residual_analyse.py
    data_dir = os.path.join(base_dir, "..", "data")  # Wechselt eine Ebene hoch und geht in "data"
    file_csv = os.path.join(data_dir, file_in + ".csv")
    file_xlsx = os.path.join(data_dir, file_in + ".xlsx")

    df_transponiert = None  # Initialisierung

    try:
        df_transponiert = pd.read_csv(file_csv, index_col=0)
    except:
        try:
            df = pd.read_excel(file_xlsx)
            df_transponiert = df.set_index('node').T
            start_date = '2050-01-01 00:00:00'
            date_range = pd.date_range(start=start_date, periods=8760, freq='h')
            df_transponiert.index = date_range
            if save_csv:
                df_transponiert.to_csv(file_csv)
        except FileNotFoundError:
            print(f"Fehler: Datei '{file_csv}' oder '{file_xlsx}' nicht gefunden.")
        except Exception as e:
            print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

    if df_transponiert is None:
        raise ValueError(f"Konnte Datei '{file_csv}' oder '{file_xlsx}' nicht laden!")

    if verbose:
        print(df_transponiert.head())
        print(df_transponiert.index)

    if get_countries:
        return list(df_transponiert.columns)

    if country is None:
        country = "DE0 Tot"

    actual_values = df_transponiert[country].values
    actual_country_df = pd.DataFrame(actual_values, columns=[col_name])
    actual_country_df[COL_N_ORIGINAL] = actual_country_df[col_name]
    actual_country_df.index = pd.to_datetime(df_transponiert.index)
    if normalize:
        actual_values = actual_country_df[COL_N_ORIGINAL].values
        hours = (actual_country_df.index[-1] - actual_country_df.index[0]).total_seconds() / 3600

        # Compute mean of the negative values separately
        # this is, what could be stored on average per year
        norm_factor = abs(actual_values[actual_values < 0].sum()) \
            / hours

        
        
        actual_country_df.loc[:, 'residual-not-normalized'] = actual_country_df[col_name]

        if norm_factor != 0:  # Avoid division by zero
            actual_country_df[col_name] = actual_country_df[col_name]/ norm_factor
        else:
            pass  # Keep original if no variation





    return actual_country_df


if __name__ == "__main__":
        
    test_countries = esm_residual_to_df(get_countries =True)
    test_df = esm_residual_to_df()
    
    EFF_STOR = .75
    m_cap = np.linspace(1e6, 20e6, 15)
    
    if test:
        verbose = False
        df = pd.read_excel('2024_Bertsch_residual_Load.xlsx')
    
        # Lade die Excel-Datei mit pandas
    
        # output_folder = create_output_folder()
        # Transponiere die Tabelle
        df_transponiert = df.set_index('node').T
        df_transponiert['time_diff_seconds'] = np.zeros(
            len(df_transponiert)) + 3600
    
        df_transponiert['time'] = np.arange(0, len(df_transponiert) * 3600., 3600)
        countries = ["DE0 Tot", "IT0 0", "GB5 0", "ES0 0", "IE4 0"]
        spalten = ["act_st_cap", "power_st_in", "SOC"]
        actual_df = df_transponiert["DE0 Tot"].values
        actual_df = pd.DataFrame(actual_df, columns=["residual"])
    
    
        # Beispielaufruf der neuen Funktion
    
        results_df = calc_capacity_dependence(actual_df,
                                              m_cap,
                                              EFF_STOR,
                                              make_df=True,
                                              file_name=f_name_base)
    
        # Wenn du die NumPy-Arrays willtest
        cap_dep_res, st_state, la, cap_change = calc_capacity_dependence(actual_df,
                                                                         m_cap,
                                                                         EFF_STOR,
                                                                         make_df=False,
                                                                         file_name=f_name_base)
    
        fi_n, (ax_n, ax_s)= plt.subplots(2)
        fi_n2, (ax_c, ax_e)= plt.subplots(2)
    
        # Energy integral
        ax_n.plot(m_cap, cap_dep_res[:, 1], "k", label="pos res")
        # integral of remaining negative residuals
        ax_n.plot(m_cap, -cap_dep_res[:, 4], "b:", label="neg res")
        ax_n.plot(m_cap, cap_dep_res[:, -1], "bv",
                  label = "stored finally")  # am Ende im Speicher
        ax_n.plot(m_cap, cap_dep_res[:, 1] + \
                  cap_dep_res[:, 4], "kv-", label="sum res")
        ax_n.plot(m_cap, cap_dep_res[:, 1]+cap_dep_res[:,
                  4]+cap_dep_res[:, -1], "ro", label="sum")
        ax_n.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax_n.set_xlabel("storage capacity")
        ax_n.set_ylabel("integral energy")
    
    
        # Storage loads
        ax_s.plot(m_cap, st_state[:, 0], "k", label="empty")
        ax_s.plot(m_cap, st_state[:, 1]/20, "b", label="full/20")
        ax_s.plot(m_cap, st_state[:, 2], "k", label="0->up")
        ax_s.plot(m_cap, st_state[:, 3], "k", label="1->down")
        ax_s.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax_s.set_xlabel("storage capacity")
        ax_s.set_ylabel("number of states")
        # Raum für die Legende schaffen
        fi_n.tight_layout(rect=[0, 0, 0.85, 1])
        fi_n.savefig(f_name_base+"-number_cap-plot.png")
    
        # Storage capacity change
        ax_c.plot(m_cap, cap_change[:, 1], "k", label="charging")
        ax_c.plot(m_cap, -cap_change[:, 4], "b", label="discharging")
        ax_e.plot(m_cap, cap_change[:, 2], "k", label="number chg")
        ax_e.plot(m_cap, cap_change[:, 5], "b:", label="number disc")
        ax_c.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax_e.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax_c.set_xlabel("storage capacity")
        ax_c.set_ylabel("integral charging")
        # Raum für die Legende schaffen
        fi_n2.tight_layout(rect=[0, 0, 0.85, 1])
        fi_n2.savefig(f_name_base+"-integral-charge_cap-plot.png")
    
        # Number of full charging equivalents
        fi_n3, (ax_g, ax_h)= plt.subplots(2)
        equiv_no_charging = cap_change[:, 1] / m_cap
        equiv_no_discharging = cap_change[:, 4] / m_cap
        ax_g.plot(m_cap, equiv_no_charging, "k", label="charging")
        ax_g.plot(m_cap, equiv_no_discharging, "b:", label="discharging")
        ax_g.set_xlabel("storage capacity")
        ax_g.set_ylabel("no eq. full cyc. / y")
        ax_g.legend(loc='upper left', bbox_to_anchor=(1, 1))
    
        e2p_mean_charge = m_cap/cap_change[:, 0]
        e2p_mean_discharge = m_cap/cap_change[:, 3]
        ax_h.plot(m_cap, e2p_mean_charge, "k", label="charging")
        ax_h.plot(m_cap, e2p_mean_discharge, "b:", label="discharging")
        ax_h.set_xlabel("storage capacity")
        ax_h.set_ylabel("E2P / h")
        ax_h.legend(loc='upper left', bbox_to_anchor=(1, 1))
    
        # Raum für die Legende schaffen
        fi_n3.tight_layout(rect=[0, 0, 0.85, 1])
        fi_n3.savefig(f_name_base+"-charge_discharge-plot.png")
    
        fig_e, ax_p =plt.subplots(1)
    
        ax_p.plot(m_cap, la[:,0], "k", label="LA_pos")
        ax_p.plot(m_cap, la[:,1], "b", label="LA_neg")
        ax_p.plot(m_cap, la[:,2], "r:", label="ratio_eq")
        ax_p.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax_p.set_title("Level of Autononomy (LA)")
        ax_p.set_xlabel("storage capacity")
        ax_p.set_ylabel("LA")
    
        # Raum für die Legende schaffen
        fig_e.tight_layout(rect=[0, 0, 0.85, 1])
        fig_e.savefig(f_name_base+"-la-plot.png")

    
    #-----------------------
    #-----------------------
    aa =storage(-1, 2 , 5, .5,.1666,)
    print (aa)
    pd.set_option('display.max_columns', None)
    # a, b, c = analyze_residual(data_0, 'Residuallast')
    df = pd.read_excel(DATA_DIR/'2024_Bertsch_residual_Load.xlsx')

    # Lade die Excel-Datei mit pandas

    # output_folder = create_output_folder()
    # Transponiere die Tabelle
    df_transponiert = df.set_index('node').T
    df_transponiert['time_diff_seconds'] = np.zeros(
        len(df_transponiert)) + 3600

    df_transponiert['time']= np.arange(0, len(df_transponiert) * 3600., 3600)
    countries= ["DE0 Tot"]# , "IT0 0", "GB5 0", "ES0 0", "IE4 0"]
    sum_units= 1/1000
    EFF_STOR = .75
    m_cap = np.linspace(1e6, 20e6, 15)
    for what in countries:
        fnam =f_name_base+what[:3]
        res_max = df_transponiert[what].max()
        m_cap = np.linspace(res_max/20, res_max*20, 7)

        results_df = calc_capacity_dependence(df_transponiert[what],
                                              m_cap,
                                              EFF_STOR,
                                              make_df=True,
                                              file_name=f_name_base+"-"+what[:3]+"-",
                                              title = what[:3])


        fig_e, ax_p = plt.subplots()
        line_labels = ['LA+', 'LA-', 'eq_ratio']
        colors = ['black', 'blue', 'green']  # Beispiel Farben können angepasst werden

        for label, color in zip(line_labels, colors):
            sbn.lineplot(data=results_df, x='storage capacity', y=label, ax=ax_p, label=label, color=color)

        # Anpassen der Legende
        ax_p.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax_p.set_title("Level of Autonomy (LA), "+what[:3])
        ax_p.set_xlabel("Storage Capacity")
        ax_p.set_ylabel("LA")

        # Raum für die Legende schaffen
        fig_e.tight_layout(rect=[0, 0, 0.85, 1])

        # Speichern des Plots
        fig_e.savefig("la-plot.png")

        plt.show()

        all_periods, pos_neg, neg_pos = analyze_residual(df_transponiert, what)
        neg_pos[['sum_pos', 'sum_neg']] = neg_pos[[
            'sum_pos', 'sum_neg']] *  sum_units
        sbn.scatterplot(data=neg_pos, x='count_neg', y='count_pos',
                        size = 'sum_pos', hue = 'sum_neg')  # , style='mean_pos')
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))

                            # Optional: Ändere die Größe des Plots, um Platz für die Legende zu schaffen
        plt.tight_layout()
        plt.title(what)
        plt.savefig(fnam+"sum_count.jpg")

        plt.figure()
        sbn.scatterplot(data=neg_pos, x='sum_neg', y='sum_pos',
                        size = 'count_pos', hue = 'count_neg')  # , style='mean_pos')
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))

        # Optional: Ändere die Größe des Plots, um Platz für die Legende zu schaffen
        plt.tight_layout()
        plt.title(what)
        plt.savefig(fnam+"_count_sum.jpg")
        fi, ax= plt.subplots(2)
        print(
            f"country:{what}, No.-periods: {pos_neg['count_pos'].count()}")
        act_corr= signal.correlate(
        df_transponiert[what], df_transponiert[what])
        # f, Pxx_den = signal.periodogram(data[dat_act[1][2]], fs =1/600)
        # ax4.semilogy(f, Pxx_den)
        ax[0].plot(act_corr)
        # positive_values = df_transponiert[what][df_transponiert[what] > 0]

        # Falls die Indizes wichtig sind, erstelle einen Array nur mit den positiven Werten

        # Setze negative Werte auf 0
        df_transponiert[what+"mod"] = np.where(
        df_transponiert[what] < 0, 0, df_transponiert[what])

        # Erstelle ein NumPy-Array aus der Spalte
        modified_array = df_transponiert[what+"mod"].to_numpy()

        # Berechne die Kreuzkorrelation der modifizierten Werte
        # , mode='full')
        corr = signal.correlate(modified_array, modified_array)

        # Optional: Wenn du auch die Lag-Werte berechnen möchtest
        lags = signal.correlation_lags(
        len(modified_array), len(modified_array), mode ='full')

        # Ausgabe der Korrelation und der Lags

        lc = len(corr)
        corr_n = corr[int((lc-1)/2):]
        ax[1].plot(corr_n[:200]/np.abs(corr_n).max())
        ax[0].set_title("Autocorrelation, "+what[:3])
        fi.savefig(fnam+"_correl.jpg")

        neg_pos.to_csv(fnam+"neg_pos.csv",sep=';')
        pos_neg.to_csv(fnam+"pos_neg.csv",sep=';')
        all_periods.to_csv(fnam+"all_periods.csv",sep=';')
        neg_sum = np.where(
        df_transponiert[what] > 0, 0, df_transponiert[what]).sum()
        pos_sum = np.where(
        df_transponiert[what] < 0, 0, df_transponiert[what]).sum()
        print(f"{what}, pos/neg residuals: {-pos_sum/neg_sum:.2f}")
