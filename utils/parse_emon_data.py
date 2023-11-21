import os
import re
import argparse
import pandas as pd
from datetime import datetime

def parse_file_name(file_name, instance, flag=""):
    """
    parse file's name and return one dict, contain: instance type,  flag, core and freq so on values
    type: eg: simd
    flag: eg: avx
    core: eg: 28
    freq: eg: 3.0Ghz
    support
    
    用于demo，不同的指令集，当在不同的 core freq，不同的 Cores，其实际cpu freq, uncore freq, power 的关系
    数据集文件基于如下规则：
    <inst>_<cores>_<freq>.dat.xlsx
    <inst>: general(busy), simd_sse, simd_avx, simd_avx512, amx : Total 5
    <cores>: 4..56..4 : Total 14
    <freq>: 2.4..3.8..0.2 : Total 8
    Total files: 5 * 14 * 8 = 560
    Sample: simd_sse_56_3.6Ghz.dat.xls
    每个emon文件，取 "socket view" 的 Socket 0 数据，取3个值：
    "metric_CPU operating frequency (in GHz)": 标记运行时实际cpu frequency
    "metric_uncore frequency GHz": 标记 uncore frequency
    "metric_package power (watts)": 标记功耗
    """
    file_info = {}
    # print(instance)
    if instance == "busy":
        if re.search("^busy", file_name):
            file_gather = file_name.split('_')
            file_info['type'] = instance
            file_info['core'] = file_gather[1]
            file_info['freq'] = re.findall('\d+\.\d+Ghz',file_gather[2])[0]
    elif instance == "simd":
        if flag == "sse":
            file_gather = file_name.split('_')
            file_info['type'] = "{}_{}".format(file_gather[0], file_gather[1])
            file_info['core'] = file_gather[2]
            file_info['freq'] = re.findall('\d+\.\d+Ghz',file_gather[3])[0]
        else:
            file_gather = file_name.split('_')
            file_info['type'] = instance
            file_info['flag'] = flag
            file_info['core'] = file_gather[2]
            file_info['freq'] = re.findall('\d+\.\d+Ghz',file_gather[3])[0]
                
    return file_info

def get_emon_data(file_path, sheet_name, sample, select_col):
    """
    Use pandas to get the data of Specify sample and sheet from excel
    Args:
        file_path (_type_): the path of excel
        sheet_name (_type_): the sheet of excel
        sample (_type_): the sample of excel
        select_col (_type_): the select coloum of excel

    Returns:
        _type_: Returns the float value of each cell
    """
    df = pd.read_excel(file_path, index_col=0, header=0, sheet_name=sheet_name)
    sample_value = df.loc[sample, select_col]
    return sample_value

def save_df(core_info):
    """
    Convert the list to pd require format
    Args:
        core_info (_type_): core info list

    Returns:
        _type_: the list of same core
    """
    result = {}
    for single_core in core_info:
        for core, s_value_list in single_core.items():
            result[core] = result.get(core, []) + s_value_list
    result_df = list(dict(sorted(result.items())).values())
    return result_df

def get_dataframe_data(emon_data, sample_list, instance, flag=""):
    """Create the datarame data

    Args:
        emon_data (_type_): the path of emon data
        sample_list (_type_): Need to return sample type
        instance (_type_): the instance of sample
        flag (str, optional): Such as avx . Defaults to "".

    Returns:
        _type_: Return dick, contain key is freq and the parse file of sum
    """
    core_info = []
    files_num = 0
    for file_name in os.listdir(emon_data):
        if flag == "avx":
            partern = "^{}_avx_[0-9]+".format(instance, flag)
        else:
            partern = "^{}(_{})?_[0-9]+".format(instance, flag)
        if re.search(".xlsx$", file_name) and re.search(partern, file_name):
            file_info = parse_file_name(file_name, instance, flag)
            samplev_list = []
            if os.path.isfile(os.path.join(emon_data,file_name)):
                file_path = os.path.join(emon_data, file_name) 
                for sample in sample_list: 
                    sample_value = get_emon_data(file_path, "socket view", sample, "socket 0")
                    samplev_list.append(sample_value)
            core_info.append({file_info['core']: samplev_list})
            files_num += 1
    result=save_df(core_info)
    return result,files_num

def save(df_data):
    """
    Save single dataframe
    Args:
        df_data (_type_): the require format of dataframe

    Returns:
        _type_: return dataframe instance
    """
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
    
    return df 
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser('Parse the emon data', add_help=False)
    parser.add_argument("--emon_data", "--d", default="/home/yangkun/emon-2", type=str, help="specish the emon data path")

    pass_args = parser.parse_args()
    emon_data = pass_args.emon_data
    sample_list=["metric_CPU operating frequency (in GHz)", "metric_uncore frequency GHz", 'metric_package power (watts)']
    
    inst = ["busy", "simd"]
    flag = ["sse", "avx", "avx512", "amx"]
    
    print("Starting parse the excel files..........")
    start = datetime.now()
    type_dict = {}
    for i in inst:
        if i == "busy":
            df_data, files_num = get_dataframe_data(emon_data, sample_list, i)
            type_dict[i] = {'data': df_data, 'files_num': files_num}
        elif i == "simd":
            for f in flag:
                df_data, files_num = get_dataframe_data(emon_data, sample_list, i, f)
                type_dict["{}_{}".format(i,f)] = {'data': df_data, 'files_num': files_num}
    with pd.ExcelWriter('2.xlsx') as writer:
        for k, v in type_dict.items():
            if len(v['data']) != 0:
                print(k,len(v['data']), v['files_num'])
                save(v['data']).to_excel(writer, sheet_name=k)
    print("总计处理文件:", sum([i['files_num'] for i in list(type_dict.values())]), "个文件")
    end = datetime.now()
    print("Ending parse the excel files..........")
    print("Sum:", (end - start).total_seconds(), "sec")