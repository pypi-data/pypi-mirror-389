# -*- coding: utf-8 -*-
"""
Created on Sat Feb  1 10:59:13 2025

@author: atakan
"""
import pytest
import pandas as pd
import numpy as np
from rws_py.load_curve_simple import generate_load_curve

def test_generate_load_curve():
    # Testdaten
    time_ind = pd.date_range(start='2021-01-01', end='2022-12-31', freq="h")
    load_params = {
        'min_weekday': 0.650,
        'max_weekday': 1.0,
        'min_weekend': 0.650,
        'max_weekend': 0.85,
        'intermediate_fraction': 0.80,
        'multiplier': 50.0,
        'offset': 0.0,
        'normalize': True,
        'amplitude_season': 0.05,  # seasonal
    }

    # Generiere die Lastkurven
    load_curve_step = generate_load_curve(time_ind, step=True, load_parameters=load_params)
    load_curve_sine = generate_load_curve(time_ind, step=False, load_parameters=load_params)

    # Überprüfe die Summe/Integral der Lastkurven
    int_step = load_curve_step["load"].sum()
    int_sine = load_curve_sine["load"].sum()

    assert np.isclose(int_step, 17497.0), f"Expected 17497.0, but got {int_step}"
    assert np.isclose(int_sine, 17497.0), f"Expected 17497.0, but got {int_sine}"

    # Überprüfe die statistischen Werte der Lastkurven
    step_describe = load_curve_step.describe()
    sine_describe = load_curve_sine.describe()

   
    expected_step_describe = pd.Series({
        'count': 17497.0,
        'mean': 1.000000,
        'std': 0.177557,
        'min': 0.742097,
        '25%': 0.810880,
        '50%': 0.999602,
        '75%': 1.166246,
        'max': 1.261863
    })

    expected_sine_describe = pd.Series({
        'count': 17497.000000,
        'mean': 1.000000,
        'std': 0.149037,
        'min': 0.768476,
        '25%': 0.866095,
        '50%': 0.984161,
        '75%': 1.124193,
        'max': 1.306717
    })


    pd.testing.assert_series_equal(step_describe['load'], expected_step_describe, check_names=False)
    pd.testing.assert_series_equal(sine_describe['load'], expected_sine_describe, check_names=False)

if __name__ == '__main__':
    pytest.main()


