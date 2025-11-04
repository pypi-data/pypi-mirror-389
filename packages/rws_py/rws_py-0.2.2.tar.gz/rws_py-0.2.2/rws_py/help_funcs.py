# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 15:45:31 2025

@author: atakan
"""
import os
from pathlib import Path

def append_suffix_to_path(base_path: Path, suffix: str, new_extension: str = None) -> Path:
    """
    Fügt einen Suffix zu einem Basispfad hinzu und optional eine neue Erweiterung.

    Args:
        base_path (Path): Der ursprüngliche Dateipfad.
        suffix (str): Der Suffix, der dem Dateinamen hinzugefügt werden soll (z.B. "-akt").
        new_extension (str, optional): Die neue Dateierweiterung inklusive Punkt (z.B. ".csv").
                                       Wenn None, bleibt die ursprüngliche Erweiterung erhalten.

    Returns:
        Path: Der neue Dateipfad mit hinzugefügtem Suffix und optionaler neuer Erweiterung.
    """
    # Basisname ohne Erweiterung
    base_stem = base_path.stem

    # Neuer Basisname mit Suffix
    new_stem = f"{base_stem}{suffix}"

    # Bestimmen der neuen Erweiterung
    if new_extension is not None:
        if not new_extension.startswith('.'):
            new_extension = f".{new_extension}"
        new_suffix = new_extension
    else:
        new_suffix = base_path.suffix

    # Neuer Dateiname
    new_name = f"{new_stem}{new_suffix}"

    # Neuer Pfad
    return base_path.with_name(new_name)

import pandas as pd
import rws_py

def get_stations():
    """
    Read all dwd-station numers from file 'stations_data.csv' in data folder

    Parameters
    ----------
    station_name : TYPE, optional
        DESCRIPTION. The default is None.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """

    # Bestimme den Pfad zur aktuellen Datei (rws_py/__init__.py)
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Bestimme den Pfad zur Datei stations_data.csv im Ordner data
    stations_data_path = os.path.join(
        current_dir,  'data', 'stations_data.csv')

    # Überprüfe, ob die Datei existiert
    if os.path.exists(stations_data_path):
        pass
        # print(f"Datei gefunden: {stations_data_path}")
    else:
        print(f"Stations file NOT found: {stations_data_path}")

    df = pd.read_csv(stations_data_path,
                     dtype=str)
    return df.set_index("Stationsname")["Stations_id"].to_dict()

if __name__ == "__main__":
    #print( get_stations())
    pass



# Beispielhafte Verwendung
if __name__ == "__main__":
    # Ursprünglicher Pfad ohne Erweiterung
    file_n = Path("C:/results/heute")
    file_aktuell1 = append_suffix_to_path(file_n, "-akt", ".csv")
    print(file_aktuell1)  # Ausgabe: C:/results/heute-akt.csv

    # Ursprünglicher Pfad mit Erweiterung
    file_mit_ext = Path("C:/results/heute.txt")
    file_aktuell2 = append_suffix_to_path(file_mit_ext, "-akt", ".csv")
    print(file_aktuell2)  # Ausgabe: C:/results/heute-akt.csv

    # Ohne Änderunge der Erweiterung
    file_aktuell3 = append_suffix_to_path(file_mit_ext, "-akt")
    print(file_aktuell3)  # Ausgabe: C:/results/heute-akt.txt
