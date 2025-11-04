# -*- coding: utf-8 -*-
"""
Read weather data, estimated load, calculate residuals, analyze pause etc.

Created on Wed Jan 22 12:43:27 2025

@author: atakan
"""
import pandas as pd
import rws_py
import rws_py.dwd_analyze_store_second_threshold as awls
from rws_py import generate_load_curve
# import residual_analyse as resa
#import rws_py.analysis_universal as anu
from rws_py import RESULTS_DIR, app_suf


if __name__ == "__main__":
    SUM_UNITS = 1.0
    HOURLY = "h" # None  # conversion to houtly data , or stick to 10 min?
    N_BEG = 0
    N_END = -1  # analyze data until to this index (for fast computation)
    CALC_ST = True
    DIR_NAME = RESULTS_DIR
    act_stations ={'Cuxhaven': '00891',}
    
    input_dict = {"load-scaling": 1.070,  # scales the load relative to the meaan value of the energy
                  # hours to calculate the storage capacity, multiplied with the max. value of
                  "storage-hours-max": 10.,
                  }
    
    
    if __name__ == "__main__":
        VERBOSE = True
    
        all_dat = []
        eval_docu=[]
        ENERGY_COLUMN = "power"  # Name of the column with the energy proportional data
    
        # Prepare data sources
        for ACT_STATION in act_stations.keys(): #awls.stations.keys():
            SOLAR_ACT = '10minutenwerte_SOLAR_' + \
                awls.stations[ACT_STATION]+'_20200101_20231231_hist.zip'
            WIND_ACT = '10minutenwerte_wind_' + \
                awls.stations[ACT_STATION]+'_20200101_20231231_hist.zip'
            all_dat.append([awls.SOLAR_URL_BASE, SOLAR_ACT,
                           awls.solar_columns, awls.SOLAR_THRESHOLD, ACT_STATION])
            all_dat.append([awls.WIND_URL_BASE, WIND_ACT, awls.wind_columns,
                           awls.WIND_THRESHOLD, ACT_STATION])
    
        # Main analysis loop
        for dat_act in all_dat:
            base_url = dat_act[0]
            filename = dat_act[1]
            expected_columns = dat_act[2]
            threshold = dat_act[3]
            ACT_STATION = dat_act[4]
    
            # Load data
            data_all = awls.load_data(base_url, filename, expected_columns,
                                      resample = HOURLY)
    
            # Process each year
            for year in range(2020, 2021):
    
    
                en_t = ACT_STATION+", "
                if dat_act[0].count('wind'):
                    ACTUAL_ENERGY = "Wind"
                else:
                    ACTUAL_ENERGY = "Solar"
                en_t += ACTUAL_ENERGY
                TITLE_NAME = f"{en_t}, {year}"
                print(f"\nNOW: {TITLE_NAME}")
    
                FILE_NAME = app_suf(DIR_NAME, TITLE_NAME.replace(", ", "-"))
                data = data_all[data_all.index.year == year]
                data_act = data.iloc[N_BEG: N_END]
    
                
    
                load_par = {
                    'min_weekday': 0.650,
                    'max_weekday': 1.0,
                    'min_weekend': 0.650,
                    'max_weekend': 0.85,  # only for step-function
                    'intermediate_fraction': .75,
                    # scales everything
                    'multiplier': 1.0,
                    'offset': 0.0,
                    'normalize': True,
                    'amplitude_season':0.05, 
                }
                load_df = generate_load_curve(
                    data_act.index, load_parameters=load_par)
                data_act =rws_py.calc_residuals(data_act, 
                                                load_df,
                                                gamma=input_dict["load-scaling"])
                # residuals calculated and in data_act now
                
                # let's analyse them
                eval_results = rws_py.residual_analyse(
                    data_act, "residual-no-storage")
                rws_py.plot_analysis_b(eval_results, file=FILE_NAME, label=TITLE_NAME)
                
                # here is the storage part now
                
                
    
                if CALC_ST is True: # analyse residuals with storage
                    print("Berechnung von st_size:",
                          input_dict["storage-hours-max"] * data_act["power"].mean())
                    st_size = (input_dict["storage-hours-max"]
                               * data_act["power"].mean()).copy()
                    print("Neuer Wert von st_size:", st_size)
                with_load = rws_py.weather_load_storage(data_act,
                                                      load_df,
                                                      storage_size=st_size,
                                                      residual =True,
                                                      )
    
    
                # Perform period analysis (includes basic analysis)
    
                data_act = with_load.copy()
                
    
                
                rws_py.plot_res(data_act, file=FILE_NAME, label=TITLE_NAME)
    
                storage_states, level_of_autonomy, charging = rws_py.posterior_analysis_residual(
                    data_act, storage_capacity=st_size)
    
                print("\n", TITLE_NAME)
                rws_py.print_dict([storage_states, level_of_autonomy,
                               charging], filename=app_suf(FILE_NAME,"eval-storage"))
                rws_py.plot_histo_analysis(
                    eval_results, en_t=TITLE_NAME, name_file=FILE_NAME)
                rws_py.plot_histo_int_analysis(
                    eval_results, en_t=TITLE_NAME, name_file=FILE_NAME, integral=True)
    
                # Documentation of the results
                row_data = {
                       "Location": ACT_STATION,
                       "Energy": ACTUAL_ENERGY,
                       "Year": year,
                       "Load Scaling":  input_dict["load-scaling"],
                       "Storage Capacity": st_size,
                       "Storage Time" :  input_dict["storage-hours-max"] ,
    
                   }
                row_data.update( storage_states)
                row_data.update(level_of_autonomy)
                row_data.update( charging)
    
                   # Fügen Sie die Zeilendaten der Gesamt-Datenliste hinzu
                eval_docu.append(row_data)
        df_docu = pd.DataFrame(eval_docu)
    
        # Verwenden Sie 'Location' als Index
        df_docu.set_index("Location", inplace=True)
    
        print(df_docu)


