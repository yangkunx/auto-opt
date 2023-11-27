import re
import os
import pickle
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
    
def storeData(data, pickle_name):
    # Its important to use binary mode
    dbfile = open(pickle_name, 'ab')
     
    # source, destination
    pickle.dump(data, dbfile)                    
    dbfile.close()
    

def loadData(pickle_name):
    # for reading also binary mode is important
    dbfile = open(pickle_name, 'rb')    
    db = pickle.load(dbfile)
    print(db)
    dbfile.close()
    
def parse_log_name(log_file):
    """
    parse log's name and return precison core and batch_size values
    """
    logfile_result = {}
    logfile_info = os.path.splitext(log_file)[0].split('_')
    logfile_result['core'] = logfile_info[1]
    logfile_result['precision'] = logfile_info[2]
    logfile_result['batch_size'] = logfile_info[3]
    return logfile_result

def parse_to_excel(platform, report_path, log_file_name):
    """
    parse log to excel
    """
    logfile_result = parse_log_name(log_file_name)
    logfile_fullpath = os.path.join(report_path,log_file_name)
    single_file_dict = {}
    #Read output log file
    with open(logfile_fullpath, 'r') as ds_log:
        lines = ds_log.readlines()
        for line in lines:
            # Get latency
            if re.search("Inference latency:", line):
                single_loop_list = []
                latency=re.findall('\d+\.\d+', line)[0]
                # single_loop_list.append(latency)
                print("latency:", float(latency))
            # Get first_token
            if re.search("First token average latency:", line):
                first_token=re.findall('\d+\.\d+', line)[0]
                single_loop_list.append(first_token)
                print("first_token:", float(first_token))
            if re.search("Average 2... latency:", line):
                second_token=re.findall('\d+\.\d+', line)[0]
                single_loop_list.append(second_token)
                print("second_token:",float(second_token))
            if re.search("WSF Portal URL:", line):
                dashboard_link = re.findall('https://.*', line)[0]
                # single_loop_list.append(dashboard_link)
                print(dashboard_link)
            if re.search("Current\s+\d+-\d+-\w+.*", line):
                loop_time=re.findall('([0-9])', line)[0]
                current_frequency=re.findall('\d.\dGhz', line)[0]
                print("loop_time and current_frequency:", loop_time, current_frequency)
                #single_file_dict[current_frequency] = single_loop_list
                # single_file_dict[current_frequency] = {'kpi_values':single_loop_list, 'dashboard_link': dashboard_link}
                link = '=HYPERLINK("{0}", "{1}")'.format(dashboard_link, latency)
                single_loop_list.insert(0, link)
                single_file_dict[current_frequency] = single_loop_list
    
    logfile_result['kpi'] = single_file_dict
    return logfile_result

def merge():
    pass

parser = argparse.ArgumentParser('Auto run the specify WL case', add_help=False)
parser.add_argument("--platform", "--p", default="SPR", type=str, help="hardware platform")

pass_args = parser.parse_args()
platform = pass_args.platform

base_path='/home/yangkun/lab/yangkunx/build-gptj/workload/GPTJ-PyTorch-Public/report'

if platform.lower() == "spr":
    report_path='{0}/{1}'.format(base_path,'spr-bz-fre-core')
elif platform.lower() == "emr":
    report_path='{0}/{1}'.format(base_path,'emr')  
else:
    exit(1)

check_and_create_dir(os.path.join(report_path,"output"))

last_re = []
for file in os.listdir(report_path):
    if os.path.isfile(os.path.join(report_path,file)):
        single = parse_to_excel( platform, report_path, file)
        last_re.append(single)
        
storeData(last_re, "re.pickle")

# loadData("re.pickle")
# print(last_re)
sheet_list = []
with pd.ExcelWriter('output.xlsx') as writer:
    for value in last_re:
        result_df = list(value['kpi'].values())
        sun = list(value['kpi'].keys())
        index = [i for i in sun]
        sheet_name = '{0}_{1}_{2}'.format(value['core'], value['precision'], value['batch_size'])
        cols = ["Avg", "1st", "2nd"] 
        sheet_list.append(sheet_name)       
        df = pd.DataFrame(result_df, columns=cols, index=index)
        df.to_excel(writer, sheet_name=sheet_name, index_label="Fre")

print(sheet_list)
