# -*- coding: utf-8 -*-
"""
test wind data load and conversion to power

Created on Mon Jan 27 11:01:47 2025

@author: atakan
"""

import pandas as pd
import matplotlib.pyplot as plt
import zipfile
from rws_py.dwd_analyze_store_second_threshold import load_data


# Funktion zur Erzeugung synthetischer Testdaten
def create_test_data(num_hours=30):
    time_index = pd.date_range(start='2023-01-01', periods=num_hours, freq='h')
    wind_speeds = pd.Series(range(num_hours))  # Geschwindigkeit von 0 bis num_hours m/s
    data = pd.DataFrame({"MESS_DATUM": time_index, "WIND_SPEED": wind_speeds})
    return data

# Funktion zur Erstellung eines ZIP-Archivs mit der Test-CSV-Datei
def create_test_zip(data, zip_filename="testdata.zip", csv_filename="testdata.csv"):
    csv_data = data.to_csv(index=False)
    with zipfile.ZipFile(zip_filename, 'w') as zf:
        zf.writestr(csv_filename, csv_data)

# Haupttestfunktion zum Laden und Plotten der Daten
def test_load_and_plot():
    # Erstellen der Testdaten und des ZIP-Archivs
    test_data = create_test_data()
    zip_filename = "test_wind_data.zip"
    csv_filename = "test_wind_data.csv"
    create_test_zip(test_data, zip_filename, csv_filename)

    # Definition der erwarteten Spalten zum Testen
    expected_columns = ["MESS_DATUM", "WIND_SPEED"]
    directory = "."  # Verzeichnis, in dem die Test-Datei gespeichert wird

    # Laden der Daten mit der load_data-Funktion
    df = load_data(bse_url_in=None, filename_in=zip_filename,
                   exp_col=expected_columns, directory=directory,
                   energy_column=1, wind_bounds=(3.3, 11.0, 25))

   
    # Plotting
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    # Erste y-Achse für Power
    line1, = ax1.plot(df.index, df["power"], label="Power", color='b')
    ax1.set_xlabel('time')
    ax1.set_ylabel('Power (a.u.)', color='b')
    ax1.tick_params(axis='y', labelcolor='b')
    
    # Zweite y-Achse für Windgeschwindigkeit
    ax2 = ax1.twinx()
    line2, = ax2.plot(df.index, df["velocity / (m/s)"], label="Wind velocity", color='r')
    ax2.set_ylabel('Wind velocity (m/s)', color='r')
    ax2.tick_params(axis='y', labelcolor='r')
    
    # Titel hinzufügen
    plt.title('Power and Wind Velocity vs. Time')
    
    # Sammeln der Handles und Labels beider Achsen
    lines = [line1, line2]
    labels = [line.get_label() for line in lines]
    
    # Legende nach außen legen
    fig.legend(lines, labels, loc='center left', bbox_to_anchor=(1.1, 0.75))
    # Alternativ: ax1.legend(lines, labels, loc='center left', bbox_to_anchor=(1.1, 0.5))
    
    fig.tight_layout()  # um Platz für beide y-Achsen zu garantieren
    plt.show()
    
if __name__ == "__main__":
        test_load_and_plot()
