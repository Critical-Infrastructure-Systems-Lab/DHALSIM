# includes
import pandas as pd

def get_demand_patterns_from_nodes(wn, index=0):
    df_pat = pd.DataFrame(columns = wn.junction_name_list)
    for name, j in wn.junctions():    
        try:
            base = j.demand_timeseries_list[index].base_value
            pat = j.demand_timeseries_list[index].pattern
            if pat is not None:
                df_pat.loc[:,name] = base * pat.multipliers
        except IndexError:
            print('Index Error excepted')
    return df_pat.dropna(axis=1)