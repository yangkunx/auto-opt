import os
import re
import copy
import pandas as pd




def parse_file_name(file_name):
    """
    type: eg: simd
    flag: eg: avx
    core: eg: 28
    freq: eg: 3.0Ghz
    parse file's name and return flog, core and so on values
    support
    """
    file_info={}
    if re.search("^busy", file_name):
        pass
    if re.search("^simd", file_name):
        file_gather = file_name.split('_')
        file_info['type'] = file_gather[0]
        file_info['flag'] = file_gather[1]
        file_info['core'] = file_gather[2]
        file_info['freq'] = re.findall('\d+\.\d+Ghz',file_gather[3])[0]
    return file_info

def get_emon_data(file_path, sheet_name, sample, select_col):
    dict_s = {}
    df = pd.read_excel(file_path, index_col=0, header=0, sheet_name=sheet_name)
    sample_value = df.loc[sample, select_col]
    dict_s[sample] = sample_value
    return sample_value

def save_df(core_info):
    result = {}
    for single_core in core_info:
        for core, s_value_list in single_core.items():
            result[core] = result.get(core, []) + s_value_list
    result_df = list(dict(sorted(result.items())).values())
    return result_df


def get_dataframe_data(emon_data, sample_list):
    # core_dict = {}
    core_info = []
    for file_name in os.listdir(emon_data):
        if re.search(".xlsx$", file_name) and re.search("^simd", file_name) and re.search("avx512", file_name):
            # print(file_name)
            # print(emon_data)
            file_info = parse_file_name(file_name)
            samplev_list = []
            if os.path.isfile(os.path.join(emon_data,file_name)):
                file_path = os.path.join(emon_data, file_name) 
                for sample in sample_list: 
                    print(sample)
                    sample_value = get_emon_data(file_path, "socket view", sample, "socket 0")
                    samplev_list.append(sample_value)
            # core_dict[file_info['core']]=samplev_list
            core_info.append({file_info['core']: samplev_list})

    # print(core_l)
    result=save_df(core_info)
    return result

def save(df_data):
    multi_index = pd.MultiIndex.from_tuples([("4", ), ("8",), ("12",), ("16",), ("20",),
                                             ("24",), ("28",),("32",), ("36",), ("40", ),
                                             ("44",), ("48",),("52",), ("56",)], names=['core'])
                                       
             
    cols = pd.MultiIndex.from_tuples([("2.4", "metric_CPU"), ("2.4", "metric_uncore"), ("2.4", "power"), 
                                      ("2.6", "metric_CPU"), ("2.6", "metric_uncore"), ("2.6", "power"),
                                      ("2.8", "metric_CPU"), ("2.8", "metric_uncore"), ("2.8", "power"),
                                      ("3"  , "metric_CPU"), ("3",   "metric_uncore"), ("3",   "power"),          
                                      ("3.2", "metric_CPU"), ("3.2", "metric_uncore"), ("3.2", "power"),
                                      ("3.4", "metric_CPU"), ("3.4", "metric_uncore"), ("3.4", "power"),
                                      ("3.6", "metric_CPU"), ("3.6", "metric_uncore"), ("3.6", "power"),
                                      ("3.8", "metric_CPU"), ("3.8", "metric_uncore"), ("3.8", "power"),])
                                    
    df = pd.DataFrame(df_data, columns=cols, index=multi_index)
    print(df)
    df.to_excel("1.xlsx")
    
    
if __name__ == "__main__":   
    emon_data='/home/yangkun/emon-2'
    sample_list=["metric_CPU operating frequency (in GHz)", "metric_uncore frequency GHz", 'metric_package power (watts)']
    df_data = get_dataframe_data(emon_data, sample_list)
    save(df_data)