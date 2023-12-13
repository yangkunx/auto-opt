import os
import argparse
import socket
import re
import time
import yaml

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
            latency=0
            first_token=0
            next_token=0
            dashboard_link=""
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
                    print("cannot access local variable '{}' where it is not associated with a value".format(link))
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
    if "/" in model:
        build_name = "build_" + model.replace("/","_")
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
    # os.system("make")
    #准备sut
    run_args = './ctest.sh -R {0} --prepare-sut -V'.format("pkm")
    print('\033[32msut_args:\033[0m {0}'.format(run_args))
    # os.system(run_args)
    #运行sut 
    base_args, loop_sum= format_args(**kwargs)
    sut_args = ' --loop={0} --reuse-sut -V --continue'.format(loop_sum)
    model_path_args = ' --set "MODEL_PATH={0}"'.format(model_path)
    run_args = './ctest.sh -R {0} --set "{1}" --set "MODEL_NAME={2}"{3}{4} '.format("pkm", base_args, model, model_path_args, sut_args)
    print('\033[32mTest_case_args:\033[0m {0}'.format(run_args))
    # os.system(run_args)


parser = argparse.ArgumentParser()
parser.add_argument("--ww", type=str, required=True, help="work week")
parser.add_argument("--root_dir", type=str, default="/home/wsf")
parser.add_argument("--platform", type=str, default="spr")
parser.add_argument("--yaml_dir", type=str, default="./wl.yaml")

args = parser.parse_args()

data = yaml.load(open(args.yaml_dir, 'r'),Loader=yaml.FullLoader)

create_dir_or_file(args.root_dir)
chdir(args.root_dir)

# git clone code
wsf_repo = data['system']['git']['repo']
branch = data['system']['git']['branch']
target_repo_name = "wsf-dev-{}".format(args.ww)
wsf_dir = os.path.join(args.root_dir, target_repo_name)
print(wsf_dir)
if not os.path.exists(wsf_dir):
    os.system("git clone -b {} {} {}".format(branch, wsf_repo, wsf_dir))
ww_repo_dir = chdir(wsf_dir)

#get local ip
local_ip, local_user= get_local_ip_user()

# modify terraform config
terraform_config_file = os.path.join(wsf_dir, "script/terraform/terraform-config.static.tf")
replacetext(local_ip, local_user)

tags = "{}_{}".format(args.ww.upper(), data['system']['tags'])
if data['system']['cmake']['docker'] is True and data['system']['cmake']['k8s'] is True:
    print("The docker and k8s can not setting to True the same time in cmake node")
    exit(1)
elif data['system']['cmake']['docker']:
    if_docker_or_k8s = "--docker"
elif data['system']['cmake']['k8s']:  
    if_docker_or_k8s = "--kubernetes"
else:
    if_docker_or_k8s = ""
# run model
start_time = time.time()
for wl, wl_value in data['WorkLoad'].items():
    args_info_case01= wl_value['common_args']
    print(args_info_case01)
    # if local_ip == "172.17.29.24":
    for all_models in wl_value['special_args']['MODEL_NAME']:
        print(all_models)
        for model, model_path in all_models.items():
            run_workload(wl, model, tags, local_ip, if_docker_or_k8s, model_path, **args_info_case01) 

# run this cmd to create output.log: python3 m_trigger_xft_test.py --platform spr --root_dir /home/jason/test --ww ww44 2>&1 | tee output.log
# python3 xft_by_yaml.py  --ww ww44 2>&1 | tee output.log
# parse output.log
end_time = time.time()
print("耗时: {:.2f}秒".format(end_time - start_time))
output_file = os.path.join(os.path.realpath(os.path.dirname(__file__)), "output.log")
if os.path.exists(output_file):
    print('{0}\033[32m parse log result \033[0m{1}'.format("-"*50,"-"*50))
    parse_log(output_file)
