import os
import re
import copy
import pandas as pd


emon_data='./simd'

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

def get_emon_data(file_path, sheet_name, sample_list, select_col):
    sample_dict = []
    df = pd.read_excel(file_path, index_col=0, header=0, sheet_name=sheet_name)
    for sample_name in sample_list:
        #sample_dict[sample_name] = df.loc[sample_name, select_col]
        sample_dict.append(df.loc[sample_name, select_col])
    return sample_dict

sample_list=["metric_CPU operating frequency (in GHz)", "metric_uncore frequency GHz", 'metric_package power (watts)']
colums = copy.deepcopy(sample_list)
colums = copy.deepcopy(sample_list)
colums.insert(0, "core")
df = pd.DataFrame(columns=colums)
print(df)

for file_name in os.listdir(emon_data):
    if os.path.isfile(os.path.join(emon_data,file_name)):
        file_info = parse_file_name(file_name)
        print(file_info['core'])
        file_path = os.path.join(emon_data, file_name)
        sample_dict = get_emon_data(file_path, "socket view", sample_list, "socket 0")
        sample_dict.insert(0, file_info['core'])
        print(sample_dict)
        df = pd.concat([df, pd.DataFrame([sample_dict], columns=colums)], ignore_index=True)
        print(df.to_excel('t.xlsx'))