import re
import os
import shutil
import xlsxwriter
import pickle
import argparse
import logging
import time
import pandas as pd
import numpy as np

def create_dir_or_file(path):
    if os.path.isfile(path):
        os.remove(path)
    else:
        if not os.path.exists(path):
            os.makedirs(path)
            if os.path.exists(path):
                print("Directory {0} already created".format(path))
        else:
            if re.match("build", path):
                shutil.rmtree(path)
                print("Directory or file {0} already deleted".format(path))
                create_dir_or_file()

def create_log(log_path, log_name):
    current_date = time.strftime("%Y%m%d")
    current_time = time.strftime("%H_%M_%S")
    log_dir = "{}/log/{}".format(log_path, current_date)
    create_dir_or_file(log_dir)
    log_full_path = "{}/{}_{}.log".format(log_dir, log_name, current_time)
    return log_full_path


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
    
    if "int" in log_file:
        logfile_result['precision'] = "{}_{}".format(logfile_info[2], logfile_info[3])
    else:
        logfile_result['precision'] = logfile_info[2]
    logfile_result['core'] = logfile_info[1]
    logfile_result['batch_size'] = logfile_info[-1]
    return logfile_result

def parse_to_excel(platform, report_path, log_file_name):
    """
    parse log to excel
    """
    logfile_result = parse_log_name(log_file_name)
    
    logging.info('Current logfile result: {0}'.format(logfile_result))
    
    logfile_fullpath = os.path.join(report_path,log_file_name)
    single_file_dict = {}
    #Read output log file
    with open(logfile_fullpath, 'r') as ds_log:
        lines = ds_log.readlines()
        for line in lines:
            # Get latency
            # logging.info(re.search("Inference latency:", line))
            if re.search("Inference latency:", line):
                single_loop_list = []
                latency=re.findall('\d+\.\d+', line)[0]
            # Get 1st_token
            if re.search("First token average latency:", line):
                first_token=re.findall('\d+\.\d+', line)[0]
                try:
                    single_loop_list.append(float(first_token))
                except UnboundLocalError:
                    logging.error("cannot access local variable '{}' where it is not associated with a value".format("first_token"))
            # Get 2nd_token
            if re.search("Average 2... latency:", line):
                second_token=re.findall('\d+\.\d+', line)[0]
                try:
                    single_loop_list.append(float(second_token))
                except UnboundLocalError:
                    logging.error("cannot access local variable '{}' where it is not associated with a value".format("second_token"))
            # Get dashboard link
            if re.search("WSF Portal URL:", line):
                dashboard_link = re.findall('https://.*', line)[0]
                dashboard_id = dashboard_link.split("/")[-1]
                zip_link = 'https://d15e4ftowigvkb.cloudfront.net/{}-gptj_pytorch_public.zip'.format(dashboard_id)
                logging.info(zip_link)
                # if add zip_link: single_loop_list.append(zip_link)
            # Get frequency
            if re.search("Current\s+\d+-\d+-\w+.*", line):
                loop_time=re.findall('([0-9])', line)[0]
                current_frequency=re.findall('\d.\dGhz', line)[0]
                try:
                    link = '=HYPERLINK("{0}", "{1}")'.format(dashboard_link, float(latency))
                    single_loop_list.insert(0, link)
                except UnboundLocalError:
                    logging.error("cannot access local variable '{} or {} or ' where it is not associated with a value".format("dashboard_link", "latency", "link"))
                single_file_dict[current_frequency] = single_loop_list
                logging.info('loop_time: {0}'.format(int(loop_time)))
                logging.info('frequency: {0}'.format( current_frequency))
                logging.info('latency: {0}'.format(float(latency)))
                logging.info('first_token: {0}'.format(float(first_token)))
                logging.info('second_token: {0}'.format(float(second_token)))
                logging.info('dashboard_link: {0}'.format(dashboard_link))

    
    logfile_result['kpi'] = single_file_dict

    return logfile_result

def create_sum(data):
    """create dict of the same batch_size 

    Args:
        data (list): [{'core': '50', 'precision': 'bfloat16', 'batch_size': '1', 'kpi': {'2.8Ghz':
                      ['=HYPERLINK("https://wsf-dashboards.intel.com", "8.652")', 0.892, 0.061]}]

    Returns:
        _type_: dict
        value: grouped_dict
    """
    grouped_dict = {}
    for x in data:
        if x['batch_size'] not in grouped_dict:
            grouped_dict[x['batch_size']] = [x]
        else:
            grouped_dict[x['batch_size']].append(x)
    return grouped_dict

def set_index(core):
    """Create multi index

    Args:
        core (int): core

    Returns:
        _type_: function
        value: multi_index
    """
    multi_index = pd.MultiIndex.from_tuples([(core, "2.8Ghz"), (core, "3.0Ghz"), (core, "3.2Ghz"), (core, "3.4Ghz"), (core, "3.6Ghz"),
                                             (core, "3.8Ghz")], names=['core', 'fre'])
    return multi_index

def set_style(df, sheet_name, column_no=0):
    """Setting sheet style

    Args:
        df (dataframe): a dataframe
        sheet_name (string): the name of sheet
        column_no (int, optional): add columns num. Defaults to 0.
    """
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    
    border_fmt = workbook.add_format({'bottom':1, 'top':1, 'left':1, 'right':1})
    worksheet.conditional_format(xlsxwriter.utility.xl_range(0, 0, len(df), len(df.columns)+column_no), {'type': 'no_errors', 'format': border_fmt})
    

base_path='/home/yangkun/lab/yangkunx/build-gptj/workload/GPTJ-PyTorch-Public/report'

#定义日志文件路径，如果存在则删除
log_full_path =  create_log('./', 'run_case')

#定义logging
level = logging.INFO
format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
handlers = [logging.FileHandler(log_full_path), logging.StreamHandler()]
logging.basicConfig(level = level, format = format, handlers = handlers)

parser = argparse.ArgumentParser('Auto run the specify WL case', add_help=False)
parser.add_argument("--hardware", "--h", default="SPR", type=str, help="hardware platform")
parser.add_argument("--precison", "--p", default="bfloat16", type=str, help="precision")

pass_args = parser.parse_args()
platform = pass_args.hardware
precison = pass_args.precison

if platform.lower() == "spr":
    plat_dir = 'spr'
elif platform.lower() == "emr":
    plat_dir = 'emr'
else:
    exit(1)

report_path='{0}/{1}'.format(base_path, "{}/{}".format(plat_dir, precison))
logging.info('logs path: {}'.format(report_path))
logging.info('Starting parse the logs')

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
output_excel = '{}_{}.xlsx'.format(platform.lower(),precison)
with pd.ExcelWriter(output_excel) as writer:
    cols = ["Avg", "1st", "2nd"] 
    bs_class = create_sum(last_re)
    for key, value in bs_class.items():
        for bs_sample in value:
            sheet_name = '{0}_{1}'.format(bs_sample['precision'], str(key))
            sun = list(bs_sample['kpi'].keys())
        index = [i for i in sun]
        dist = [ pd.DataFrame(list(bs_value['kpi'].values()), columns=cols,index=set_index(int(bs_value['core']))).reset_index('fre') for bs_value in value ]
        """
        below code is added empty row to excel when concat the sheet
            dist = []
            em_multi_index = pd.MultiIndex.from_tuples([(np.nan, np.nan)], names=['core', 'fre'])
            for d in df_list:
                dist.append(d)
                empty_df = pd.DataFrame([[np.nan] * len(d.columns)], columns=d.columns, index=em_multi_index).reset_index('fre', drop=True)
                dist.append(empty_df)
        """
        df= pd.concat(dist)
        df.to_excel(writer, sheet_name=sheet_name)
        set_style(df, sheet_name)
    
    for value in last_re:
        result_df = list(value['kpi'].values())
        sun = list(value['kpi'].keys())
        index = [i for i in sun]
        sheet_name = '{0}_{1}_{2}'.format(value['core'], value['precision'], value['batch_size'])

        sheet_list.append(sheet_name)       
        df = pd.DataFrame(result_df, columns=cols, index=index)
        df.to_excel(writer, sheet_name=sheet_name, index_label="Fre")
        set_style(df, sheet_name)
logging.info('End parse the logs')