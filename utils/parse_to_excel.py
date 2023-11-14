import re
import os
import argparse
from xlwt import *

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

def excel_style():
    """
    Setting excel style
    """
    # Configuration style
    borders = Borders()
    borders.left = 1
    borders.right = 1
    borders.top = 1
    borders.bottom = 1

    style = XFStyle()
    style.borders = borders
    
    return style

def parse_to_excel(platform, report_path, log_file_name):
    """
    parse log to excel
    """
    precision, core= parse_log_name(log_file_name)
    # Workbook is created
    print(core)
    wb = Workbook()
    core_sheet = wb.add_sheet(core)
    
    row=0
    column=1
    fre_row=0
    logfile_path = os.path.join(report_path,log_file_name)
    #Read output log file
    with open(logfile_path, 'r') as ds_log:
        lines = ds_log.readlines()
        frequencys=("2.0Ghz","2.2Ghz","2.4Ghz","2.6Ghz","2.8Ghz","3.0Ghz","3.2Ghz","3.4Ghz","3.6Ghz","3.8Ghz")
        for line in lines:
            # Get latency
            if re.search("Inference latency:", line):
                latency=re.findall('\d+\.\d+', line)[0]
                # print(latency)
                core_sheet.write(row, column, float(latency), excel_style())
                row+=1
            # Get first_token
            if re.search("First token average latency:", line):
                first_token=re.findall('\d+\.\d+', line)[0]
                print(first_token)
                core_sheet.write(row, column, float(first_token), excel_style())
                row+=1
            # Get second_token
            if re.search("Average 2... latency:", line):
                second_token=re.findall('\d+\.\d+', line)[0]
                print(second_token)
                core_sheet.write(row, column, float(second_token), excel_style())
                row+=1
            # Get loop times
            if re.search("Current\s+\{[0-9]\}.*", line):
                loop_time=re.findall('\{([0-9])\}', line)[0]
                current_frequency=re.findall('\d.\dGhz', line)[0]
                for frequency in frequencys:
                    if int(loop_time) <= 3 and current_frequency == frequency:
                        column+=1
                        row-=3
                    if int(loop_time) == 3 and current_frequency == frequency:
                        row+=3
                        column=1
                        merge_num = int(fre_row) + 2
                        core_sheet.write_merge(fre_row, merge_num , 0, 0, frequency, excel_style())
                        fre_row+=3
    # output excel file to current path
    wb.save(os.path.join(report_path,'output','{}.xls'.format(log_file_name.split(".")[0])))

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
    print('not support')

#create dir
check_and_create_dir(os.path.join(report_path,"output"))
    
for file in os.listdir(report_path):
    if os.path.isfile(os.path.join(report_path,file)):
        parse_to_excel(platform, report_path, file)
