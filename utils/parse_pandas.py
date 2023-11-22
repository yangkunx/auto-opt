import re
import os
import pandas as pd
import argparse


def check_and_create_dir(path):
    """
    check dir and create new dir
    """
    try:
        os.makedirs(path)
    except FileExistsError:
        return False

def parse_log_name(log_file):
    """
    parse log's name and return precison and core values
    support precison: bfloat16, woq_int8, static_int8
    """
    if re.search("bfloat16", log_file):
        precision=re.findall('bfloat16', log_file)[0]
        try:
            core=re.findall('\d{2}', log_file)[1]
        except IndexError:
            core='56'
    if re.search("woq_int8", log_file):
        precision=re.findall('woq_int8', log_file)[0]
        print(precision)
        try:
            core=re.findall('\d{2}', log_file)[0]
        except IndexError:
            core='56'
    if re.search("static_int8", log_file):
        precision=re.findall('static_int8', log_file)[0]
        try:
            core=re.findall('\d{2}', log_file)[0]
        except IndexError:
            core='56'
    return precision, core

def parse_to_excel(platform, report_path, log_file_name, loop, frequencys):
    """
    parse log to excel
    """
    single_file_dict = {}
    precision, core= parse_log_name(log_file_name)
    logfile_path = os.path.join(report_path,log_file_name)
    #Read output log file
    single_file_list = []
    fre_dict = {}
    with open(logfile_path, 'r') as ds_log:
        lines = ds_log.readlines()
        for line in lines:
            # Get latency
            if re.search("Inference latency:", line):
                latency=re.findall('\d+\.\d+', line)[0]
                print(float(latency))
                single_file_dict['latency'] = latency
            # Get first_token
            if re.search("First token average latency:", line):
                first_token=re.findall('\d+\.\d+', line)[0]
                print(float(first_token))
                single_file_dict['first_token'] = first_token
            if re.search("Average 2... latency:", line):
                second_token=re.findall('\d+\.\d+', line)[0]
                print(float(second_token))
                single_file_dict['second_token'] = second_token
            if re.search("Current\s+.*\{[0-9]\}.*", line):
                loop_time=re.findall('([0-9])', line)[0]
                current_frequency=re.findall('\d.\dGhz', line)[0]
                print(loop_time, current_frequency)
                single_file_list.append({'{}'.format(loop_time): single_file_dict})
                fre_dict['{0}'.format(current_frequency)] = single_file_list
    """

    {'2.0': [{'1': {'latency': '8.577', 'first_token': '0.917', 'second_token': '0.060'}}, {'2': {'latency': '8.577', 'first_token': '0.917', 'second_token': '0.060'}],
     '2.2': [{'1': {'latency': '8.577', 'first_token': '0.917', 'second_token': '0.060'}}, {'2': {'latency': '8.577', 'first_token': '0.917', 'second_token': '0.060'}],
     '2.4': [{'1': {'latency': '8.577', 'first_token': '0.917', 'second_token': '0.060'}}, {'2': {'latency': '8.577', 'first_token': '0.917', 'second_token': '0.060'}],
    }
    """
    
    print(fre_dict)
    return single_file_dict

def save():
    """
    Save single dataframe
    Args:
        df_data (_type_): the require format of dataframe

    Returns:
        _type_: return dataframe instance
    """
    multi_index = pd.MultiIndex.from_tuples([("2.0Ghz", )])
    
    #, ("2.2Ghz",), ("2.4Ghz",), ("2.6Ghz",), ("2.8Ghz",),("3.0Ghz",), ("3.2Ghz",),("3.4Ghz",), ("3.6Ghz",), ("3.8Ghz", )                                   
             
    cols = pd.MultiIndex.from_tuples([("Avg",), ("1st",), ("2nd",), ("Avg",), ("1st",), ("2nd",), ("Avg",), ("1st",), ("2nd",)], names=['fre'])
    
    df_data = [['5.701', '0.74', '0.039', '5.701', '0.74', '0.039', '5.701', '0.74', '0.039']]                       
    df = pd.DataFrame(df_data, columns=cols, index=multi_index)
    df.to_excel("3.xlsx")
    return df 


parser = argparse.ArgumentParser('Auto run the specify WL case', add_help=False)
parser.add_argument("--platform", "--p", default="SPR", type=str, help="wsf run platform")

pass_args = parser.parse_args()
platform = pass_args.platform

base_path='/home/yangkun/lab/auto-opt/utils/report'

if platform.lower() == "spr":
    report_path='{0}/{1}'.format(base_path,'spr')
elif platform.lower() == "emr":
    report_path='{0}/{1}'.format(base_path,'emr')  
else:
    print('Not support')

#create dir
check_and_create_dir(os.path.join(report_path,"output"))


frequencys=("2.0Ghz","2.2Ghz","2.4Ghz","2.6Ghz","2.8Ghz","3.0Ghz","3.2Ghz","3.4Ghz","3.6Ghz","3.8Ghz")
#frequencys=("2.8Ghz","3.0Ghz" , "3.4Ghz" ,"3.8Ghz")
loop=1
for file in os.listdir(report_path):
    if os.path.isfile(os.path.join(report_path,file)):
        single = parse_to_excel(platform, report_path, file, loop, frequencys)
        
