"""Top-level package for residuals_weather_storage.

rws_py package.

DFG - SPP2403

B.Atakan, Univ. Duisburg-Essen
2025-02-07

"""

import pkgutil
from .config import RESULTS_DIR, DATA_DIR, WEATHER_DATA_DIR
from .analyze_weather_load_storage import weather_load_storage, calc_residuals
from .load_curve_simple import generate_load_curve
from .residual_analyse import analyze_residual, storage, esm_residual_to_df
from .dwd_analyze_store_second_threshold import load_data, analyze_weather, \
    resample_to_hourly, plot_analysis, plot_enhanced_analysis

from .help_funcs import append_suffix_to_path as app_suf
from .help_funcs import get_stations
from .analysis_universal import residual_analyse, plot_analysis_b, plot_res,\
    plot_histo_analysis,plot_histo_int_analysis, posterior_analysis_residual,\
        print_dict


__author__ = """Burak Atakan"""
__email__ = 'atakan.thermodynamik.duisburg@gmail.com'
__version__ = '0.2.1.post1'

__all__ = [
    'weather_load_storage',
    'calc_residuals',
    'generate_load_curve',
    'analyze_residual',
    'residual_analyse',
    'plot_analysis_b',
    'plot_res',
    'plot_histo_analysis',
    'plot_histo_int_analysis',
    'posterior_analysis_residual',
    'print_dict',
    'storage',
    'esm_residual_to_df',
    'RESULTS_DIR',
    'DATA_DIR',
    'WEATHER_DATA_DIR',
    'load_data',
    'analyze_weather',
    'resample_to_hourly',
    'plot_analysis',
    'plot_enhanced_analysis',
    'help_funcs',
    'app_suf',

]

stations = get_stations() # all DWD weather stations for 10 min data->dictionary

__path__ = pkgutil.extend_path(__path__, __name__)

# Automatisches Importieren aller Untermodule (inkl. utils)
for finder, module_name, ispkg in pkgutil.walk_packages(__path__, __name__ + "."):
    __import__(module_name)

