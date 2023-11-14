# parse log
#               frequency-set
# core setting  Power	core 	uncore

import argparse
import os
import re

def check_and_create_dir(path):
    """
    check dir and create new dir
    """
    try:
        os.makedirs(path)
    except FileExistsError:
        return False


class Opt_file():
    
    def __init__(self, file_name, file_path):
        self.file_name = file_name
        self.file_path = file_path
    
    def parse_log_name(self):
        """
        parse log's name and return precison and core values
        support precison: bfloat16, woq_int8, static_int8
        
        """
        if re.search("bfloat16", self.file_name):
            precision=re.findall('bfloat16', self.file_name)[0]
            try:
                core=re.findall('\d{2}', self.file_name)[1]
            except IndexError:
                core='56'
        if re.search("woq_int8", self.file_name):
            precision=re.findall('woq_int8', self.file_name)[0]
            try:
                core=re.findall('\d{2}', self.file_name)[0]
            except IndexError:
                core='56'
        if re.search("static_int8", self.file_name):
            precision=re.findall('static_int8', self.file_name)[0]
            try:
                core=re.findall('\d{2}', self.file_name)[0]
            except IndexError:
                core='56'
        return precision, core
    
    def parse_log(self):
        pass




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
    print('not surppot')

#create dir
check_and_create_dir(os.path.join(report_path,"output"))
    
for filename in os.listdir(report_path):
    if os.path.isfile(os.path.join(report_path,filename)):
        opt1 = Opt_file(filename)
        print(opt1.parse_log_name())