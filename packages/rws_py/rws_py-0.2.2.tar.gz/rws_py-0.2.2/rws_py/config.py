# -*- coding: utf-8 -*-
"""
Created on Sat Feb  1 11:22:18 2025

@author: atakan
"""
import os
from pathlib import Path

# Standardverzeichnisse
DEFAULT_RESULTS_DIR = os.path.join(os.getenv('TEMP', '/tmp'), 'results', 'storage_residual')
DEFAULT_WEATHER_DATA_DIR = os.path.join(os.getenv('TEMP', '/tmp'), 'data')

# Benutzerdefinierte Verzeichnisse
RESULTS_DIR = os.getenv('RESULTS_DIR', DEFAULT_RESULTS_DIR)
RESULTS_DIR =Path(RESULTS_DIR)

DATA_DIR = Path('data')
WEATHER_DATA_DIR = DEFAULT_WEATHER_DATA_DIR

# Sicherstellen, dass die Verzeichnisse existieren
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(WEATHER_DATA_DIR, exist_ok=True)

