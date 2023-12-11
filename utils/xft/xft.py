import os
import argparse
import socket
import re
import shutil
import time


def parse_log(log_path):
    """
    parse log
    """
    #Read output log file
    single_file_list = []
    with open(log_path, 'r') as ds_log:
        lines = ds_log.readlines()
        for line in lines:
            if re.search("\d\:\sMODEL_NAME=", line):
                single_loop_list = []
                model_name=re.findall('\d\:\sMODEL_NAME=.*', line)[0].split("=")[1]
            if re.search("\d\:\sPRECISION=", line):
                single_loop_list = []
                precision=re.findall('\d\:\sPRECISION=.*', line)[0].split("=")[1]
            if re.search("\d\:\sINPUT_TOKENS=", line):
                single_loop_list = []
                input_tokens=re.findall('\d\:\sINPUT_TOKENS=.*', line)[0].split("=")[1]
            if re.search("\d\:\sOUTPUT_TOKENS=", line):
                single_loop_list = []
                output_tokens=re.findall('\d\:\sOUTPUT_TOKENS=.*', line)[0].split("=")[1]
            if re.search("\d\:\sBATCH_SIZE=", line):
                single_loop_list = []
                batch_size=re.findall('\d\:\sBATCH_SIZE=.*', line)[0].split("=")[1]
            # Get latency
            if re.search("Inference Latency:", line):
                latency=re.findall('\d+\.\d+', line)[0]
            # Get 1st_token
            if re.search("First token Avg Latency:", line):
                first_token=re.findall('\d+\.\d+', line)[0]
                try:
                    single_loop_list.append(float(first_token))
                except UnboundLocalError:
                    print("cannot access local variable '{}' where it is not associated with a value".format("first_token"))
            # Get 2nd_token
            if re.search("Next token Max Latency:", line):
                next_token=re.findall('\d+\.\d+', line)[0]
                try:
                    single_loop_list.append(float(next_token))
                except UnboundLocalError:
                    print("cannot access local variable '{}' where it is not associated with a value".format("next_token"))
            # Get dashboard link
            if re.search("WSF Portal URL:", line):
                dashboard_link = re.findall('https://.*', line)[0]
                dashboard_id = dashboard_link.split("/")[-1]
                zip_link = 'https://d15e4ftowigvkb.cloudfront.net/{}-gptj_pytorch_public.zip'.format(dashboard_id)
                single_loop_list.append(zip_link)
                # Get frequency
                try:
                    link = '=HYPERLINK("{0}", "{1}")'.format(dashboard_link, float(latency))
                    single_loop_list.insert(0, link)
                except UnboundLocalError:
                    print("cannot access local variable '{} or {} or ' where it is not associated with a value".format("dashboard_link", "latency", "link"))
                single_file_list.append(single_loop_list)
                print('model_name: {0}'.format(model_name))
                print('precision: {0}'.format(precision))
                print('input_tokens: {0}'.format(input_tokens))
                print('output_tokens: {0}'.format(output_tokens))
                print('batch_size: {0}'.format(batch_size))
                print('latency: {0}'.format(float(latency)))
                print('first_token: {0}'.format(float(first_token)))
                print('next_token: {0}'.format(float(next_token)))
                print('dashboard_link: {0}'.format(dashboard_link))
                print('zip_link: {0}'.format(zip_link))

    return single_file_list

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

def replacetext(replace_text):
    """
    replace the text
    """
    with open(terraform_config_file,'r+') as f: 
        file = f.read() 
        search_text=r'"public_ip": "127.0.0.1"'
        replace_text=r'"public_ip": "{}"'.format(replace_text)
        file = re.sub(search_text, replace_text, file) 
        f.seek(0)
        f.write(file)
        f.truncate()
    return "Text replaced"

def get_local_ip():
    """
    get local ip 
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
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
    
def run_workload(workload, model, tags, if_docker, model_path="", **kwargs):
    build_name = "build_" + model
    build_path = os.path.join(ww_repo_dir, build_name)
    create_dir_or_file(build_path)
    chdir(build_path)
    #cmake 
    cmake_cmd = "cmake -DPLATFORM=SPR -DRELEASE=latest -DACCEPT_LICENSE=ALL -DBACKEND=terraform -DBENCHMARK= \
                -DTERRAFORM_SUT=static -DTERRAFORM_OPTIONS='{} --svrinfo --intel_publish --tags={} \
                --owner=sf-post-silicon' -DTIMEOUT=60000,3600 ..".format(if_docker,tags)
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
parser.add_argument("--root_dir", type=str, required=True, default="/home/wsf")
parser.add_argument("--platform", type=str, required=True, default="spr")

args = parser.parse_args()

create_dir_or_file(args.root_dir)
chdir(args.root_dir)

# git clone code
wsf_repo="https://github.com/intel-innersource/applications.benchmarking.benchmark.platform-hero-features"
target_repo_name = "wsf-dev-" + args.ww
wsf_dir = os.path.join(args.root_dir, target_repo_name)
if not os.path.exists(wsf_dir):
    os.system("git clone -b develop " + wsf_repo + " " + target_repo_name)
ww_repo_dir = chdir(wsf_dir)

#get local ip
local_ip = get_local_ip()

# modify terraform config
terraform_config_file = os.path.join(wsf_dir, "script/terraform/terraform-config.static.tf")
replacetext(local_ip)

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

args_info_case01 = {"WARMUP_STEPS": 1, 'STEPS': 5, 'PRECISION': ['bf16_fp16'], 'INPUT_TOKENS': [32], 'OUTPUT_TOKENS': [32], 'BATCH_SIZE':[1]}
args_info_case02 = {"WARMUP_STEPS": 1, 'STEPS': 5, 'PRECISION': ['bf16'], 'INPUT_TOKENS': [32], 'OUTPUT_TOKENS': [32], 'BATCH_SIZE':[1]}
# args_info_case01 = {"WARMUP_STEPS": 1, 'STEPS': 5, 'PRECISION': ['bf16_fp16'], 'INPUT_TOKENS': [32,512,1024,2048], 'OUTPUT_TOKENS': [32,128,512,1024,2048], 'BATCH_SIZE':[1,4]}
# args_info_case02 = {"WARMUP_STEPS": 1, 'STEPS': 5, 'PRECISION': ['bf16'], 'INPUT_TOKENS': [32,512,1024,2048], 'OUTPUT_TOKENS': [32,128,512,1024,2048], 'BATCH_SIZE':[1,4,8,16,32]}
workload_name = 'xFTBench' 

# run model
start_time = time.time()
if local_ip == "10.165.174.148" or local_ip == "172.17.29.24":
    for all_models in models:
        for model, model_path in all_models.items():
            print(model)
            run_workload(workload_name, model, tags, if_docker, model_path, **args_info_case01)
            run_workload(workload_name, model, tags, if_docker, model_path, **args_info_case02)             
else:
    for model in models:
        run_workload(workload_name, model, tags, if_docker, **args_info_case01)
        run_workload(workload_name, model, tags, if_docker, **args_info_case02)

# run this cmd to create output.log: python3 m_trigger_xft_test.py --platform spr --root_dir /home/jason/test --ww 44 2>&1 | tee output.log
# parse output.log
end_time = time.time()
print("耗时: {:.2f}秒".format(end_time - start_time))
output_file = os.path.join(os.path.realpath(os.path.dirname(__file__)), "output.log")
if os.path.exists(output_file):
    print('{0}\033[32m parse log result \033[0m{1}'.format("-"*50,"-"*50))
    parse_log(output_file)
