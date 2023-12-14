import os
import argparse
import socket
import re
import time
import pandas as pd


def parse_log(log_path):
    """
    parse log
    """
    #Read output log file
    single_file_list = []
    with open(log_path, 'r') as ds_log:
        lines = ds_log.readlines()
        for line in lines:
            if re.search("\d\:\sMODE=", line):
                single_case_list = []
                latency=0
                first_token_average_latency=0
                second_token_average_latency=0
                max_latency=0
                min_latency=0
                p90_latency=0
                dashboard_link=""
            if re.search("\d\:\sPRECISION=", line):
                print(re.findall('\d\:\sPRECISION=.*', line)[0].split("=")[1])
                precision=re.findall('\d\:\sPRECISION=.*', line)[0].split("=")[1]
            if re.search("\d\:\sMODEL_NAME=", line):
                model_name=re.findall('\d\:\sMODEL_NAME=.*', line)[0].split("=")[1]
            if re.search("\d\:\sINPUT_TOKENS=", line):
                input_tokens=float(re.findall('\d\:\sINPUT_TOKENS=.*', line)[0].split("=")[1])

            if re.search("\d\:\sOUTPUT_TOKENS=", line):
                output_tokens=float(re.findall('\d\:\sOUTPUT_TOKENS=.*', line)[0].split("=")[1])
                
            if re.search("\d\:\sBATCH_SIZE=", line):
                batch_size=float(re.findall('\d\:\sBATCH_SIZE=.*', line)[0].split("=")[1])
                
            # Get latency
            if re.search("Inference Latency:", line):
                latency=round(float(re.findall('\d+\.\d+', line)[0]) / 1000, 5)
            # Get first_token_average_latency
            if re.search("First token Avg Latency:", line):
                first_token_average_latency=round(float(re.findall('\d+\.\d+', line)[0]) / 1000, 5)
            # Get max_latency
            if re.search("Next token Max Latency:", line):
                max_latency=round(float(re.findall('\d+\.\d+', line)[0]) / 1000, 5)
            # Get min_latency
            if re.search("Next token Min Latency:", line):
                min_latency=round(float(re.findall('\d+\.\d+', line)[0]) / 1000, 5)   
            # Get second_token_average_latency
            if re.search("Next token Avg Latency:", line):
                second_token_average_latency=round(float(re.findall('\d+\.\d+', line)[0]) / 1000, 5)
            # Get p90_latency
            if re.search("Next token P90 Latency:", line):
                p90_latency=round(float(re.findall('\d+\.\d+', line)[0]) / 1000, 5)
            # Get dashboard link
            if re.search("WSF Portal URL:", line):
                dashboard_link = re.findall('https://.*', line)[0]
                dashboard_id = dashboard_link.split("/")[-1]
                zip_link = 'https://d15e4ftowigvkb.cloudfront.net/{}-gptj_pytorch_public.zip'.format(dashboard_id)
                # Get link
                link = '=HYPERLINK("{0}", "{1}")'.format(dashboard_link, float(latency))
                
                single_case_list.append(model_name)
                single_case_list.append(precision)
                single_case_list.append(input_tokens)
                single_case_list.append(output_tokens)
                single_case_list.append(batch_size)
                single_case_list.append(latency)
                single_case_list.append(first_token_average_latency)
                single_case_list.append(second_token_average_latency)
                single_case_list.append(max_latency)
                single_case_list.append(min_latency)
                single_case_list.append(p90_latency)
                single_case_list.append(dashboard_link)
                single_case_list.append(zip_link)
                single_file_list.append(single_case_list)
                print('model_name: {0}'.format(model_name))
                print('precision: {0}'.format(precision))
                print('input_tokens: {0}'.format(input_tokens))
                print('output_tokens: {0}'.format(output_tokens))
                print('batch_size: {0}'.format(batch_size))
                print('latency: {0}'.format(latency))
                print('first_token_average_latency: {0}'.format(first_token_average_latency))
                print('second_token_average_latency: {0}'.format(second_token_average_latency))
                print('max_latency: {0}'.format(max_latency))
                print('min_latency: {0}'.format(min_latency))
                print('p90_latency: {0}'.format(p90_latency))
                print('dashboard_link: {0}'.format(dashboard_link))
                print('zip_link: {0}'.format(zip_link))
    
    # print(single_file_list)
    return single_file_list

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

# def set_style(df, sheet_name, column_no=0):
#     """Setting sheet style

#     Args:
#         df (dataframe): a dataframe
#         sheet_name (string): the name of sheet
#         column_no (int, optional): add columns num. Defaults to 0.
#     """
#     workbook = writer.book
#     worksheet = writer.sheets[sheet_name]
    
#     border_fmt = workbook.add_format({'bottom':1, 'top':1, 'left':1, 'right':1})
#     worksheet.conditional_format(xlsxwriter.utility.xl_range(0, 0, len(df), len(df.columns)+column_no), {'type': 'no_errors', 'format': border_fmt})

def chdir(path):
    """
    check and change directory
    """
    try:
        os.chdir(path)
        parent_dir = os.getcwd()
        print('\033[32mCurrent working directory: \033[0m{0}'.format(parent_dir))
    except FileNotFoundError:
        print("Directory: {0} does not exist".format(path))
        parent_dir = None
    except NotADirectoryError:
        print("{0} is not a directory".format(path))
        parent_dir = None
    except PermissionError:
        print("You do not have permissions to change to {0}".format(path))
        parent_dir = None
    
    return parent_dir


def create_dir_or_file(path):
    """
    check and create dir or file
    """
    if os.path.isfile(path):
        os.remove(path)
    else:
        if not os.path.exists(path):
            os.makedirs(path)

def replacetext(ip,user):
    """
    replace the text
    """
    with open(terraform_config_file,'r+') as f: 
        file = f.read()
        search_text=r'# "user_name": "<user>"'
        replace_text=r'"user_name": "{}"'.format(user)
        file = re.sub(search_text, replace_text, file)
        search_text=r'"public_ip": "127.0.0.1"'
        replace_text=r'"public_ip": "{}"'.format(ip)
        file = re.sub(search_text, replace_text, file)
        search_text=r'"private_ip": "127.0.0.1"'
        replace_text=r'"private_ip": "{}"'.format(ip)
        file = re.sub(search_text, replace_text, file)
        file = re.sub('variable "client_profile" {\n.*\n.*vm_count = 1', 'variable "client_profile" {\n  default = {\n    vm_count = 0', file)
        f.seek(0)
        f.write(file)
        f.truncate()
    return "Text replaced"

def get_local_ip_user():
    """
    get local ip 
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        user=os.getlogin()
        return ip, user
    except socket.error:
        return None

def format_args(**kwargs):
    """
    格式化输出参数，以 key1=value1/key2=value2 输出
    """
    base_args= ''
    loop_sum = 1
    for arg_key in kwargs:
        if isinstance(kwargs[arg_key],list):
            length = len(kwargs[arg_key])
            arg_keys = '{0}={1}'.format(arg_key, str(" ".join(str(v) for v in kwargs[arg_key])))
        else:
            length = 1
            arg_keys = '{0}={1}'.format(arg_key, str(kwargs[arg_key]))
        base_args += arg_keys + "/"
        loop_sum = loop_sum * length
    base_args = base_args[0:-1]
    return base_args, loop_sum
    
def run_workload(workload, model, tags, local_ip, if_docker, model_path="", **kwargs):
    build_name = "build_" + model
    build_path = os.path.join(ww_repo_dir, build_name)
    create_dir_or_file(build_path)
    chdir(build_path)
    #cmake
    cmake_cmd = "cmake -DREGISTRY={}:20666 -DPLATFORM=SPR -DRELEASE=latest -DACCEPT_LICENSE=ALL -DBACKEND=terraform -DBENCHMARK= \
                -DTERRAFORM_SUT=static -DTERRAFORM_OPTIONS='{} --svrinfo --intel_publish --tags={} \
                --owner=sf-post-silicon' -DTIMEOUT=60000,3600 ..".format(local_ip, if_docker,tags)
    print('\033[32mcmake命令:\033[0m {}'.format(cmake_cmd))
    os.system(cmake_cmd)
    chdir(os.path.join(build_path, "workload", workload))
    os.system("make")
    #准备sut
    run_args = './ctest.sh -R {0} --prepare-sut -V'.format("pkm")
    print('\033[32msut_args:\033[0m {0}'.format(run_args))
    os.system(run_args)
    #运行sut
    base_args, loop_sum= format_args(**kwargs)
    sut_args = ' --loop={0} --reuse-sut -V --continue'.format(loop_sum)
    model_path_args = ""
    if local_ip == "10.165.174.148" or local_ip == "172.17.29.24":
        model_path_args = ' --set "MODEL_PATH={0}"'.format(model_path)
    run_args = './ctest.sh -R {0} --set "{1}" --set "MODEL_NAME={2}"{3}{4} '.format("pkm", base_args, model, model_path_args, sut_args)
    print('\033[32mTest_case_args:\033[0m {0}'.format(run_args))
    os.system(run_args)



parser = argparse.ArgumentParser()
parser.add_argument("--ww", type=str, required=True, help="work week")
parser.add_argument("--root_dir", type=str, default="/home/wsf")
parser.add_argument("--platform", type=str, default="spr")

args = parser.parse_args()

create_dir_or_file(args.root_dir)
chdir(args.root_dir)

# git clone code
#wsf_repo = "https://github.com/JunxiChhen/applications.benchmarking.benchmark.platform-hero-features"
wsf_repo = "https://github.com/intel-innersource/applications.benchmarking.benchmark.platform-hero-features"
branch = "develop"
target_repo_name = "wsf-dev-" + args.ww
wsf_dir = os.path.join(args.root_dir, target_repo_name)
if not os.path.exists(wsf_dir):
    os.system("git clone -b {} {} {}".format(branch, wsf_repo, wsf_dir))
ww_repo_dir = chdir(wsf_dir)

#get local ip
local_ip, local_user= get_local_ip_user()

# modify terraform config
terraform_config_file = os.path.join(wsf_dir, "script/terraform/terraform-config.static.tf")
replacetext(local_ip, local_user)

if_docker = ""
tags = ""
# 10.165.174.148 172.17.29.24
if local_ip == "172.17.29.24":
    if_docker = "--docker"
    tags = "{}_SPR_QUAD".format(args.ww.upper())
    models = [{'llama-2-13b': '/mnt/nfs_share/xft/llama2-xft'}, {'baichuan2-13b': '/mnt/nfs_share/xft/baichuan2-xft'}]
elif local_ip == "192.168.14.91":
    if_docker = "--docker"
    tags = "{}_SPR_QUAD".format(args.ww.upper())
    models = ["llama-2-7b","chatglm2-6b","baichuan2-7b","chatglm-6b"]
elif local_ip == "192.168.14.121":
    tags = "{}_HBM_FLAT_SNC4".format(args.ww.upper())
    models = ["llama-2-7b","baichuan2-7b","baichuan2-13b"]
elif local_ip == "192.168.14.119":
    tags = "{}_HBM_FLAT_SNC4".format(args.ww.upper())
    models = ["chatglm2-6b","chatglm-6b","llama-2-13b"]
elif local_ip == "10.165.174.148":
    if_docker = "--docker"
    tags = "{}_SPR_QUAD".format(args.ww.upper())
    models = [{'chatglm-6b': '/opt/dataset/chatglm-xft'}, {'baichuan-7b': '/opt/dataset/baichuan-xft'}]
elif local_ip == "10.45.247.77":
    if_docker = "--docker"
    tags = "{}_SPR_QUAD_susan_2712".format(args.ww.upper())
    models = ['chatglm2-6b']
else:
    print("Not support this IP")
    exit(1)

# args_info_case01 = {"WARMUP_STEPS": 1, 'STEPS': 20, 'XFT_FAKE_MODEL':1, 'PRECISION': ['bf16_fp16'], 'INPUT_TOKENS': [32], 'OUTPUT_TOKENS': [32], 'BATCH_SIZE':[1]}
# args_info_case02 = {"WARMUP_STEPS": 1, 'STEPS': 5, 'PRECISION': ['bf16'], 'INPUT_TOKENS': [32], 'OUTPUT_TOKENS': [32], 'BATCH_SIZE':[1,2]}
# args_info_case01 = {"WARMUP_STEPS": 1, 'STEPS': 5, 'XFT_FAKE_MODEL':1, 'PRECISION': ['bf16_fp16','bf16','bf16_int8','bf16_int4'], 'INPUT_TOKENS': [32,512,1024,2048], 'OUTPUT_TOKENS': [32,128,512,1024,2048]}
args_info_case01 = {"WARMUP_STEPS": 1, 'STEPS': 5, 'XFT_FAKE_MODEL':1, 'PRECISION': ['bf16_int4'], 'INPUT_TOKENS': [32,512,1024,2048], 'OUTPUT_TOKENS': [32,128,512,1024,2048]}
# args_info_case02 = {"WARMUP_STEPS": 1, 'STEPS': 5, 'PRECISION': ['bf16'], 'INPUT_TOKENS': [32,512,1024,2048], 'OUTPUT_TOKENS': [32,128,512,1024,2048], 'BATCH_SIZE':[1,4,8,16,32]}
workload_name = 'xFTBench'

# run model
start_time = time.time()
if local_ip == "172.17.29.24":
    for all_models in models:
        for model, model_path in all_models.items():
            pass 
            # run_workload(workload_name, model, tags, local_ip, if_docker, model_path, **args_info_case01)
            # run_workload(workload_name, model, tags, local_ip, if_docker, model_path, **args_info_case02)             
else:
    for model in models:
        pass 
        # run_workload(workload_name, model, tags, local_ip, if_docker, **args_info_case01)
        # run_workload(workload_name, model, tags, local_ip, if_docker, **args_info_case02)

# run this cmd to create output.log: python3 m_trigger_xft_test.py --platform spr --root_dir /home/jason/test --ww ww44 2>&1 | tee output.log
# python3 xft.py  --ww ww44 2>&1 | tee output.log
# parse output.log
end_time = time.time()
print("耗时: {:.2f}秒".format(end_time - start_time))
output_file = os.path.join(os.path.realpath(os.path.dirname(__file__)), "output_int4_121.log")
basename = os.path.basename(output_file).split(".")[0]
output_excel = os.path.join(os.path.realpath(os.path.dirname(__file__)), "{}.xlsx".format(basename))
print(output_excel)
if os.path.exists(output_file):
    print('{0}\033[32m parse log result \033[0m{1}'.format("-"*50,"-"*50))
    data = parse_log(output_file)
    sheet_list = []
    # output_excel = '{}/{}.xlsx'.format(output_file, "output")
    with pd.ExcelWriter(output_excel) as writer:
        cols = ["model_name", "precision", "input_tokens","output_tokens", "batch_size", "latency","first_token_average_latency", "second_token_average_latency", "max_latency", "min_latency" , "p90_latency", "dashboard_link", "zip_link"]
        print(len(data))
        df = pd.DataFrame(data, columns=cols)
        df.to_excel(writer)
