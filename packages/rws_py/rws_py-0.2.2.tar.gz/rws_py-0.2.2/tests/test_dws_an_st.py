# -*- coding: utf-8 -*-
"""

tests for the weather data from dws and the analysis
-not yet useful !

Created on Mon Feb  3 12:52:34 2025

@author: atakan
"""
import os
import unittest
import pandas as pd
from pathlib import Path
from rws_py import load_data, analyze_weather, resample_to_hourly, plot_analysis, plot_enhanced_analysis

class TestRWS(unittest.TestCase):

    def test_load_data(self):
        base_url = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/solar/historical"
        filename = "10minutenwerte_SOLAR_00891_20200101_20231231_hist.zip"
        expected_columns = ["MESS_DATUM", "QN", "GS_10"]
        data = load_data(base_url, filename, expected_columns)
        self.assertIsInstance(data, pd.DataFrame)

    def test_analyze_weather(self):
        # Beispielhafte Testdaten
        data = pd.DataFrame({
            "MESS_DATUM": pd.date_range(start="2020-01-01", periods=4, freq='H'),
            "power": [10, 20, 30, 40]
        }).set_index('MESS_DATUM')
        
        column = "power"
        threshold = 15
        
        # Aufruf der Funktion
        results = analyze_weather(data, column, threshold)
        
        # Überprüfen des Rückgabeformats
        self.assertIsInstance(results, tuple)
        self.assertEqual(len(results), 3)
        
        df_period, df_active_inactive, df_inactive_active = results
        
        # Weitere Assertions, um die Inhalte der DataFrames zu prüfen
        self.assertIsInstance(df_period, pd.DataFrame)
        self.assertIsInstance(df_active_inactive, pd.DataFrame)
        self.assertIsInstance(df_inactive_active, pd.DataFrame)
        
        # Angepasste Überprüfung der Spalten, einschließlich 'block'
        self.assertListEqual(
            list(df_period.columns),
            ['block', 'count', 'mean', 'std', 'sum', 'min', 'max']
        )
        self.assertListEqual(
            list(df_active_inactive.columns),
            ['count', 'mean', 'std', 'sum', 'min', 'max']
        )
        self.assertListEqual(
            list(df_inactive_active.columns),
            ['block','count', 'mean', 'std', 'sum', 'min', 'max', 'count_inv']
        )

    

import pytest
from unittest import mock
from unittest.mock import patch, MagicMock
import pandas as pd
from pathlib import Path
import shutil
import tempfile
import rws_py._weather_analysis as weather_analysis # Stellen Sie sicher, dass das Verzeichnis als Paket erkannt wird

@pytest.fixture
def mock_load_data():
    # Mock-Daten für Solar und Wind
    solar_data = pd.DataFrame({
        "MESS_DATUM": pd.date_range(start="2020-01-01", periods=24, freq='H'),
        "QN": [18]*24,
        "GS_10": [i * 10 for i in range(24)],
        "power": [i * 16.66 for i in range(24)]
    }).set_index("MESS_DATUM")

    wind_data = pd.DataFrame({
        "MESS_DATUM": pd.date_range(start="2020-01-01", periods=24, freq='H'),
        "QN": [3]*24,
        "FF_10": [i * 1.5 for i in range(24)],
        "power": [(i * 1.5) ** 3 for i in range(24)]
    }).set_index("MESS_DATUM")

    def load_data_side_effect(base_url, filename, expected_columns):
        if "SOLAR" in filename:
            return solar_data
        elif "wind" in filename:
            return wind_data
        else:
            return pd.DataFrame()

    with patch('weather_analysis.load_data', side_effect=load_data_side_effect):
        yield

@pytest.fixture
def temporary_results_dir():
    # Erstellen eines temporären Verzeichnisses für die Ergebnisse
    temp_dir = tempfile.mkdtemp()
    with patch('weather_analysis.RESULTS_DIR', Path(temp_dir)):
        yield Path(temp_dir)
    # Bereinigen nach dem Test
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_plot_functions():
    # Mocken der Plot-Funktionen, um das Erstellen von Dateien zu verhindern
    with patch('weather_analysis.plot_analysis') as mock_plot_analysis, \
         patch('weather_analysis.plot_enhanced_analysis') as mock_plot_enhanced:
        yield mock_plot_analysis, mock_plot_enhanced

def test_main_flow(mock_load_data, temporary_results_dir, mock_plot_functions):
    """
    Integrationstest für den Hauptablauf der main()-Funktion.
    """
    mock_plot_analysis, mock_plot_enhanced = mock_plot_functions

    # Mocken Sie andere abhängige Funktionen, falls notwendig
    with patch('weather_analysis.generate_load_curve', return_value=pd.DataFrame()), \
         patch('weather_analysis.weather_load_storage', return_value=pd.DataFrame()), \
         patch('weather_analysis.analyze_residual', return_value={
             'active_inactive': pd.DataFrame({
                 'count': [1, 2, 3],
                 'count_inv': [4, 5, 6],
                 'mean': [10, 20, 30],
                 'sum': [100, 200, 300]
             }),
             'basic_stats': {
                 'mean_active_periods': 15
             },
             'direct_threshold': 12.5,
             'storage_periods': {
                 'count': 2,
                 'mean_duration': 10,
                 'mean_pause_duration': 5,
                 'std_pause_duration': 2,
                 'std_duration': 3,
                 'sum': 100
             }
         }):
        # Führen Sie die main()-Funktion aus
       weather_analysis.main()

    # Überprüfen Sie, ob die Evaluierungs-CSV erstellt wurde
    eval_csv = temporary_results_dir / "H-all-eval-enhanced.csv"
    assert eval_csv.exists(), "Evaluierungs-CSV wurde nicht erstellt."

    # Laden und prüfen Sie den Inhalt der Evaluierungs-CSV
    evaluation_df = pd.read_csv(eval_csv, sep=';')
    assert not evaluation_df.empty, "Evaluierungs-CSV ist leer."
    expected_columns = ["Station", "Year", "power", "Threshold", "sum", "mean",
                        "10 min periods", "periods>1h", "sum with energy",
                        "sum without energy", "ratio of period lengths",
                        "mean_active_periods", "direct_threshold",
                        "storage_periods_count", "period_mean_duration", "mean_pause_duration",
                        'std_pause_duration', 'std_duration']
    for col in expected_columns:
        assert col in evaluation_df.columns, f"Spalte {col} fehlt in der Evaluierungs-CSV."

    # Weitere Überprüfungen können hinzugefügt werden, z.B. die Anzahl der Zeilen
    assert len(evaluation_df) > 0, "Evaluierungs-CSV enthält keine Daten."

    # Überprüfen Sie, ob Plot-Funktionen aufgerufen wurden
    mock_plot_analysis.assert_called()
    mock_plot_enhanced.assert_called()

    # Optional: Überprüfen Sie spezifische Werte in der Evaluierungs-CSV
    first_row = evaluation_df.iloc[0]
    assert first_row['Station'] == 'Cuxhaven', "Station-Name stimmt nicht."
    assert first_row['Year'] == 2020, "Jahr stimmt nicht."
    assert first_row['power'] == 752.447269, "Power-Wert stimmt nicht."
    # Fügen Sie weitere Assertions hinzu, um andere Werte zu überprüfen


if __name__ == "__main__":
    unittest.main()
