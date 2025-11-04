# -*- coding: utf-8 -*-
"""

Run script to analyse ESM residual data together with a storage


DFG SPP 2403

Created on Sun Jan 26 10:16:56 2025

@author: atakan
"""



import pandas as pd

import rws_py

from rws_py import RESULTS_DIR, app_suf, esm_residual_to_df

if __name__ == "__main__":
    COUNTRIES = ["DE0 Tot", "IT0 0", "GB5 0", "ES0 0", "IE4 0"]
    DIR_NAME = RESULTS_DIR
    input_dict = {"storage-hours-max" : 12,
                  }
    
    for act_country in COUNTRIES:
        f_name = f"{act_country}, {input_dict['storage-hours-max']} h"
    
    
    
        fil_name = app_suf(DIR_NAME,  f_name.replace(" ", "-").replace(",", ""))
        data_act = esm_residual_to_df(country=act_country)
        data_act.index = pd.to_datetime(data_act.index)
    
        # for storage sizing
        negative_values = data_act[data_act["residual-no-storage"] < 0]
        mean_negative_values = negative_values["residual-no-storage"].mean()
        st_size = input_dict["storage-hours-max"] * abs(mean_negative_values)
    
        # generate data with storage included
        data_act = rws_py.weather_load_storage(data_act,
                                        None,
                                        storage_size=st_size,
                                        residual=True)
        # get period lengths, mean values, following period with pos residuals
        eval_results = rws_py.residual_analyse(
            data_act, "residual-no-storage", thresholds={'direct': 0.})
    
        rws_py.plot_analysis_b(eval_results, file=fil_name, label=f_name)
        rws_py.plot_res(data_act, file=fil_name, label=f_name)
    
        storage_states, level_of_autonomy, charging = \
            rws_py.posterior_analysis_residual(data_act, storage_capacity=st_size)
    
        print("\n", f_name)
        rws_py.print_dict([storage_states, level_of_autonomy, charging],
                       app_suf(fil_name,"-stor-eval"))
    
        data_act.to_csv(app_suf(fil_name,"-time-series.csv"), sep=";")
        rws_py.plot_histo_analysis(eval_results, en_t =f_name, name_file=fil_name)
        rws_py.plot_histo_int_analysis(eval_results, en_t =f_name, name_file=fil_name,
                                    integral =True)




