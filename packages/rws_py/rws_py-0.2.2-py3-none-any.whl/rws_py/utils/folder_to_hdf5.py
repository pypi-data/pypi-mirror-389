# -*- coding: utf-8 -*-
"""
Create a HDF5 File out of a folder with subfolders

Created on Mon Feb 10 21:45:58 2025

@author: atakan
Universität Duisburg-Essen, Germany

In the framework of the Priority Programme: "Carnot Batteries: Inverse Design from
Markets to Molecules" (SPP 2403)
https://www.uni-due.de/spp2403/
https://git.uni-due.de/spp-2403/residuals_weather_storage

"""

import os
import h5py
import yaml
import numpy as np
from pathlib import Path

def load_yaml(file_path):
    """Lädt eine YAML-Datei und gibt sie als Dictionary zurück."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def add_metadata(hdf5_obj, metadata):
    """Fügt Metadaten als Attribute zu einem HDF5-Objekt hinzu."""
    for key, value in metadata.items():
        if isinstance(value, (int, float, str, bool)):
            hdf5_obj.attrs[key] = value
        else:
            hdf5_obj.attrs[key] = str(value)  # Komplexe Daten als String speichern

def store_data_in_hdf5(hdf5_file, base_path, current_path):
    """Rekursives Speichern von Dateien und Metadaten in HDF5."""
    rel_path = os.path.relpath(current_path, base_path)
    group = hdf5_file.create_group(rel_path) if rel_path != '.' else hdf5_file
    
    yaml_metadata = {}
    
    # Suche nach YAML-Dateien
    for file in Path(current_path).glob("*.yaml"):
        yaml_metadata[file.stem] = load_yaml(file)
    
    # Falls es eine allgemeine YAML-Datei gibt, die nicht mit einer Datei übereinstimmt
    general_metadata = yaml_metadata.pop(Path(current_path).name, None)
    if general_metadata:
        add_metadata(group, general_metadata)
    
    for file in Path(current_path).iterdir():
        if file.is_dir():
            store_data_in_hdf5(hdf5_file, base_path, file)
        elif file.suffix not in ['.yaml', '.hdf5']:
            dataset_name = os.path.join(rel_path, file.name)
            try:
                data = np.loadtxt(file, delimiter=',') if file.suffix in ['.csv', '.txt'] else open(file, 'rb').read()
                dset = hdf5_file.create_dataset(dataset_name, data=data)
                
                # Falls es eine passende YAML-Datei gibt, Metadaten speichern
                if file.stem in yaml_metadata:
                    add_metadata(dset, yaml_metadata[file.stem])
            except Exception as e:
                print(f"Fehler beim Speichern von {file}: {e}")

def convert_folder_to_hdf5(source_folder, output_hdf5):
    """Konvertiert einen gesamten Ordner rekursiv in eine HDF5-Datei."""
    with h5py.File(output_hdf5, 'w') as hdf5_file:
        store_data_in_hdf5(hdf5_file, source_folder, source_folder)
    print(f"HDF5-Datei gespeichert unter: {output_hdf5}")

# Beispielaufruf:
# convert_folder_to_hdf5("mein_ordner", "output.hdf5")
