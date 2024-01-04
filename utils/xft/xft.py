import os
import argparse
import socket
import re
import time
import glob
import subprocess
import paramiko
import pandas as pd
from tabulate import tabulate
from paramiko import BadHostKeyException, AuthenticationException, SSHException

"""
# Directly execute the following command to run weekly test  and no logs will be output:
    python3 xft.py  --ww 51 --weekly
    or
    python3 xft.py  --ww 51 --w
# Only print the command of run case and and the cases of all models will not be run:
    python3 xft.py  --ww 51  --d
# Test the test case running env:
    python3 xft.py  --ww 51 --t --d
# Run run weekly test cmd and output to the output.log: 
    python3 xft.py  --ww 51 --weekly 2>&1 | tee output.log
    or
    python3 xft.py  --ww 51 --w 2>&1 | tee output.log
# Run run bi-weekly test cmd and output to the output.log: 
    python3 xft.py  --ww 51 --bi_weekly 2>&1 | tee output.log
    or
    python3 xft.py  --ww 51 --bw 2>&1 | tee output.log
# Run run monthly test cmd and output to the output.log: 
    python3 xft.py  --ww 51 --monthly 2>&1 | tee output.log
    or
    python3 xft.py  --ww 51 --m 2>&1 | tee output.log
# Only parse the ouput log: 
    python3 xft.py --o
"""

class Env():
    
    def __init__(self, ssh_user, ssh_pwd, ssh_ip):
        self.ssh_user = ssh_user
        self.ssh_pwd = ssh_pwd
        self.ssh_ip = ssh_ip
        self.ssh_client = paramiko.client.SSHClient()

    def check_ssh_connect(self):
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh_client.connect(self.ssh_ip, username=self.ssh_user)
            print('\033[32mSSH connect successed, the setting is OK\033[0m')
            return True
        except (BadHostKeyException, AuthenticationException, 
                SSHException) as e:
            print(e)
        self.ssh_client.close()
        return False
    
    def set_ssh_env(self):
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh_client.connect(self.ssh_ip, username=self.ssh_user, password=self.ssh_pwd)
            filename='/home/yangkun/.ssh/id_rsa.pub'
            ftp_client=self.ssh_client.open_sftp()
            ftp_client.put(filename,"/home/yangkun/.ssh/authorized_keys")
            print('\033[32mSSH Passwordless Login set up successed \033[0m')
            return True
        except (BadHostKeyException, AuthenticationException, 
                SSHException) as e:
            print(e)
        ftp_client.close()
        self.ssh_client.close()
        return False
    
    def check_docker_env(self):
        check_docker_install = os.system("docker -v 2>&1 >/dev/null")
        # print(check_docker_install)
        if check_docker_install == 0:
            check_docker_install=True
        else:
            print("\033[1;31;40mDocker not install, please install docker at first\033[0m")
            check_docker_install=False
            exit(1)
        check_docker_registy = subprocess.check_output("docker ps | grep 'registry' | grep ':20666'", shell=True, encoding='utf-8').split("\n")
        check_docker_registy = list(set([x for x in check_docker_registy if x != "" ]))
        # print(len(check_docker_registy))
        if len(check_docker_registy) == 1:
            check_docker_registy=True
        else:
            print("\033[1;31;40mThe contanier of registry_v2 is not deployed, please deploy it at first\033[0m")
            check_docker_registy=False
            exit(1)
        
        if check_docker_install and check_docker_registy:
            print('\033[32mThe docker env is OK\033[0m')
        
        return check_docker_install and check_docker_registy
    
    def check_k8s_env(self):
        check_kubectl_install = os.system("kubectl cluster-info 2>&1 >/dev/null")
        if check_kubectl_install == 0:
            check_kubectl_install=True
        else:
            print("\033[1;31;40mkubectl not install, please install kubectl at first\033[0m")
            check_kubectl_install=False
            exit(1)
        
        check_k8s_cluster = subprocess.check_output("kubectl cluster-info", shell=True, encoding='utf-8').split("\n")
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        check_k8s_cluster = [ansi_escape.sub('', text) for text in check_k8s_cluster]
        check_k8s_cluster = list(set([x for x in check_k8s_cluster if x != "" ]))
        cluster_running_text = "Kubernetes control plane is running at https://{}:6443".format(self.ssh_ip)
        if cluster_running_text in check_k8s_cluster:
            check_k8s_cluster=True
        else:
            print("\033[1;31;40mThe cluster of k8s is not ready, please deploy it at first\033[0m")
            check_k8s_cluster=False
            exit(1)
        
        if check_kubectl_install and check_k8s_cluster:
            print('\033[32mThe k8s env is OK\033[0m')
        
        return check_kubectl_install and check_k8s_cluster

def parse_log(log_path, local_ip):
    """
    parse log
    """
    #Read output log file
    single_file_list = []
    with open(log_path, 'r') as ds_log:
        lines = ds_log.readlines()
        for line in lines:
            if re.search("Setting: REGISTRY=", line):
                # print(line)
                collect_ip = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)[0]
            if re.search("\d\:\sMODE=", line):
                single_case_list = []
                input_tokens=0
                output_tokens=0
                batch_size=0
                latency=0
                first_token_average_latency=0
                second_token_average_latency=0
                max_latency=0
                min_latency=0
                p90_latency=0
                throughput=0
                accuracy=0
                dashboard_link=""
                BASE_MODEL_NAME=""
                precision=""
                model_name=""
            if re.search("BASE_MODEL_NAME:", line):
                BASE_MODEL_NAME=re.findall('BASE_MODEL_NAME:.*', line)[0].split(":")[1]
            if re.search("\d\:\sPRECISION=", line):
                precision=re.findall('\d\:\sPRECISION=.*', line)[0].split("=")[1]
                if precision == "bf16":
                    precision = "bfloat16"
                elif precision == "bf16_fp16":
                    precision = "bfloat16_float16"
                elif precision == "bf16_int8":
                    precision = "bfloat16_int8"
                elif precision == "fp16":
                    precision = "float16"
                elif precision == "bf16_int4":
                    precision = "bfloat16_int4"
            if re.search("\d\:\sMODEL_NAME=", line):
                model_name=re.findall('\d\:\sMODEL_NAME=.*', line)[0].split("=")[1]
            if re.search("\d\:\sINPUT_TOKENS=", line):
                input_tokens=int(re.findall('\d\:\sINPUT_TOKENS=.*', line)[0].split("=")[1])

            if re.search("\d\:\sOUTPUT_TOKENS=", line):
                output_tokens=int(re.findall('\d\:\sOUTPUT_TOKENS=.*', line)[0].split("=")[1])
                
            if re.search("\d\:\sBATCH_SIZE=", line):
                batch_size=int(re.findall('\d\:\sBATCH_SIZE=.*', line)[0].split("=")[1])
                
            # Get latency
            if re.search("Inference Latency:", line):
                latency=round(float(re.findall('\d+\.\d+', line)[0]) / 1000, 5)
            # Get first_token_average_latency
            if re.search("First token Avg Latency:", line):
                first_token_average_latency=round(float(re.findall('\d+\.\d+', line)[0]) / 1000, 5)
            # Get first_token_average_latency
            if re.search("Throughput without 1st token:", line):
                throughput=round(float(re.findall('\d+\.\d+', line)[0]), 5)
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
            # Get accuracy
            if re.search("\|acc", line):
                accuracy = round(float(re.findall('\d+\.\d+', line)[0]), 5)
            # Get dashboard link
            if re.search("WSF Portal URL:", line):
                dashboard_link = re.findall('https://.*', line)[0]
                dashboard_id = dashboard_link.split("/")[-1]
                zip_link = 'https://d15e4ftowigvkb.cloudfront.net/{}-gptj_pytorch_public.zip'.format(dashboard_id)
                # Get link
                _link = '=HYPERLINK("{0}", "{1}")'.format(dashboard_link, BASE_MODEL_NAME)
                # link = '=HYPERLINK("{0}", "{1}")'.format(dashboard_link, float(latency))
                
                single_case_list.append(_link)
                single_case_list.append(model_name)
                single_case_list.append(precision)
                single_case_list.append(batch_size)
                single_case_list.append(input_tokens)
                single_case_list.append(output_tokens)
                single_case_list.append("pytorch+xfasttransformer")
                single_case_list.append("True")
                single_case_list.append(throughput)
                single_case_list.append(min_latency)
                single_case_list.append(max_latency)
                single_case_list.append(p90_latency)
                single_case_list.append(first_token_average_latency)
                single_case_list.append(second_token_average_latency)
                single_case_list.append(accuracy)
                single_case_list.append("xftbench")
                single_case_list.append(dashboard_id)
                single_case_list.append(collect_ip)
                # single_case_list.append(dashboard_link)
                # single_case_list.append(zip_link)
                single_file_list.append(single_case_list)
                print('model_name: {0}'.format(model_name))
                print('precision: {0}'.format(precision))
                print('batch_size: {0}'.format(batch_size))
                print('input_tokens: {0}'.format(input_tokens))
                print('output_tokens: {0}'.format(output_tokens))
                print('output_tokens: {0}'.format(throughput))
                print('max_latency: {0}'.format(max_latency))
                print('min_latency: {0}'.format(min_latency))
                print('p90_latency: {0}'.format(p90_latency))
                print('first_token_average_latency: {0}'.format(first_token_average_latency))
                print('second_token_average_latency: {0}'.format(second_token_average_latency))
                print('accuracy: {0}'.format(accuracy))
                print('latency: {0}'.format(latency))
                print('dashboard_link: {0}'.format(_link))
                print('zip_link: {0}'.format(zip_link))
                print('local_ip: {0}'.format(collect_ip))


    # print(single_file_list)
    return single_file_list

def checkout_origin(remote_url, branch_name):
    remote_urls = subprocess.check_output("git remote -v | awk '{print $2}'", shell=True).decode("utf-8").split('\n')
    remote_urls = list(set([x for x in remote_urls if x != "" ]))
    # print(remote_urls)
    if remote_url not in remote_urls:
        print('\033[32mAdding the remote origin\033[0m')
        subprocess.check_output("git remote add {} {}".format("new_origin", remote_url), shell=True)
        print('\033[32mFetching the remote origin \033[0m')
        subprocess.check_output("git fetch {} {}".format("new_origin", branch_name), shell=True, encoding='utf-8')
        print('\033[32mCheckoutting the remote origin branch \033[0m')
        subprocess.check_output("git checkout {}/{}".format("new_origin", branch_name), shell=True, encoding='utf-8')
        subprocess.check_output("git pull", shell=True, encoding='utf-8')
    else:
        print('\033[32mCheckoutting the origin branch \033[0m')
        subprocess.check_output("git checkout {}".format(branch_name), shell=True, encoding='utf-8')
        subprocess.check_output("git pull", shell=True, encoding='utf-8')
        print('\033[32mReset the HEAD\033[0m')
        print(subprocess.check_output("git reset --hard", shell=True, encoding='utf-8'),end="")

def chdir(path, text="wsf"):
    """
    check and change directory
    """
    try:
        os.chdir(path)
        parent_dir = os.getcwd()
        print('\033[32mCurrent directory {1} is: \033[0m{0}'.format(parent_dir, text))
    except FileNotFoundError:
        print("\033[1;31;40m Directory: {0} does not exist \033[0m".format(path))
        parent_dir = None
        exit(1)
    except NotADirectoryError:
        print("\033[1;31;40m {0} is not a directory \033[0m".format(path))
        parent_dir = None
        exit(1)
    except PermissionError:
        print("\033[1;31;40m You do not have permissions to change to {0} \033[0m".format(path))
        parent_dir = None
        exit(1)
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
    format output: key1=value1/key2=value2 
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

def run_model(models_list, **kwargs):
        all_model_case_sum = 0 # define the case loop sum of all models
        all_summary_list = [] # Loop summary information for all models
        
        for all_models in models_list: # 2
            model_case_sum = 0 # define the case loop sum
            groups_num = 0 # define how mach the cases
            header_list = [] # define the header of table
            header_list.append('model')

            for model, model_path in all_models.items():
                each_model_summary_list = [] # Loop summary information for each model
                each_model_summary_list.append(model)
                cmake_cmd = "cmake -DREGISTRY={}:20666 -DPLATFORM=SPR -DRELEASE=latest -DACCEPT_LICENSE=ALL -DBACKEND=terraform -DBENCHMARK= \
-DTERRAFORM_SUT=static -DTERRAFORM_OPTIONS='{} --svrinfo --intel_publish --tags={} \
--owner=sf-post-silicon' -DTIMEOUT=60000,3600 ..".format(local_ip, if_docker,tags)
                
                print('{}\033[32m {} \033[0m{}'.format("-"*50,model,"-"*50))
                if args.dry_run:
                    print('\033[32mCmake cmd:\033[0m     \033[32m【\033[0m{}\033[32m】\033[0m'.format(cmake_cmd))
                else:
                    build_name = "build_" + model
                    if "/" in model:
                        build_name = "build_" + model.replace("/","_")
                    build_path = os.path.join(ww_repo_dir, build_name)
                    create_dir_or_file(build_path)
                    chdir(build_path, "ww_repo_model_build")
                    #cmake
                    print('\033[32mCmake cmd:\033[0m \033[32m【\033[0m{}\033[32m】\033[0m'.format(cmake_cmd))
                    os.system(cmake_cmd)
                    chdir(os.path.join(build_path, "workload", workload_name), "ww_build_workload_path")
                    os.system("make")
                
                for case_name , args_list in kwargs.items():
                    case_num = 1 # define the case num
                    pre_run_args = './ctest.sh -R {0} --prepare-sut -V'.format(case_name)
                    if args.dry_run:
                        print('\033[32m{}_sut_args:\033[0m  \033[32m【\033[0m{}\033[32m】\033[0m'.format(case_name, pre_run_args))
                    else:
                        #prepare sut
                        print('\033[32m{}_sut_args:\033[0m  \033[32m【\033[0m{}\033[32m】\033[0m'.format(case_name, pre_run_args))
                        os.system(pre_run_args)
                    for args_info in args_list:
                        case_loop = run_workload(model,  model_path, case_num, dry_run=args.dry_run, case_name=case_name, **args_info)
                        model_case_sum +=case_loop
                        each_model_summary_list.append(case_loop)
                        header_list.append('{}_case_{}_sum'.format(case_name, case_num))
                        case_num +=1 
                    groups_num +=len(args_list)
                
                print('{}\033[32m {} \033[0m{}'.format("-"*55,"end","-"*55))
                each_model_summary_list.extend([groups_num, model_case_sum])
            
            
            all_model_case_sum += model_case_sum
            all_summary_list.append(each_model_summary_list)

        header_list.append('args_groups_sum')
        header_list.append('all_case_sum')
        results_list = [ sum(all_summary_list[i][y] for i in range(len(all_summary_list))) for y in range(1,len(all_summary_list[0])) ]
        results_list.insert(0,len(models))
        all_summary_list.append(results_list)
        
        return all_summary_list, header_list
    
def run_workload(model, model_path="", case_num=0, dry_run=False, case_name="", **kwargs):

    base_args, loop_sum= format_args(**kwargs)
    sut_args = ' --loop={0} --reuse-sut -V --continue'.format(loop_sum)
    model_path_args = ' --set "MODEL_PATH={0}"'.format(model_path)
    run_args = './ctest.sh -R {0} --set "{1}" --set "MODEL_NAME={2}"{3}{4} '.format(case_name, base_args, model, model_path_args, sut_args)
    if dry_run:
        # print('\033[32mSut_args:\033[0m      \033[32m【\033[0m{}\033[32m】\033[0m'.format(pre_run_args))
        print('\033[32m{}_{}_args:\033[0m \033[32m   【\033[0m{}\033[32m】\033[0m'.format(case_name, case_num, run_args))
        
        # '{}_case_{}_sum'.format(case_name, case_num)
        # termtables.print([[model,pre_run_args,run_args]],header=header_list)
        # print(tabulate([[cmake_cmd]], tablefmt="fancy_grid", headers=['cmake_cmd'], maxcolwidths=[120], numalign="right"))
        # print(tabulate([[model,pre_run_args,run_args]], tablefmt="fancy_grid", headers=header_list, maxcolwidths=[None, None, 60], numalign="right"))
    else:
        

        
        #run sut
        print('\033[32m{}_{}_args:\033[0m \033[32m   【\033[0m{}\033[32m】\033[0m'.format(case_name, case_num, run_args))
        os.system(run_args)
    
    return loop_sum
    
   

parser = argparse.ArgumentParser()
parser.add_argument("--ww", type=str, default="40", help="work week")
parser.add_argument("--weekly", "--w", action="store_true", help="weekly")
parser.add_argument("--bi_weekly", "--bw", action="store_true", help="bi-weekly")
parser.add_argument("--monthly", "--m", action="store_true", help="monthly")
parser.add_argument("--normal", "--n", action="store_true", help="normal")
parser.add_argument("--root_dir", "--rd", type=str, default=".", help="wsf code and exec script root_dir")
parser.add_argument("--platform","--p", type=str, default="spr", help="the platform of run case")
parser.add_argument("--test", "--t", action="store_true", help="test the case or run env")
parser.add_argument("--dry_run", "--d", action="store_true", help="dry run")
parser.add_argument("--only_parse", "--o", action="store_true", help="Only parse the log")
parser.add_argument("--branch", "--b", type=str, default="develop", help="Specify the branch of wsf repo")
parser.add_argument("--repo", "--r", type=str, default="https://github.com/intel-innersource/applications.benchmarking.benchmark.platform-hero-features", help="Specify wsf the repo")
parser.add_argument("--log_file", "--l", type=str, help="Specify the log file")

# wsf_repo = "https://github.com/JunxiChhen/applications.benchmarking.benchmark.platform-hero-features"
# wsf_repo = "https://github.com/yangkunx/applications.benchmarking.benchmark.platform-hero-features"

args = parser.parse_args()

#get local ip
local_ip, local_user= get_local_ip_user()

run_env = Env(local_user, "111111", local_ip)
start_time = time.time()
if ( not args.only_parse or (args.only_parse and args.dry_run) or 
   ( args.only_parse and args.weekly) or (args.only_parse and args.bi_weekly) or
   ( args.only_parse and args.monthly) or ( args.only_parse and args.test) or 
   ( args.only_parse and args.normal) or (args.only_parse and args.test and args.dry_run )):
    
    
    # check ssh
    check_ssh_con = run_env.check_ssh_connect()
    
    # setting the ssh private key
    if not check_ssh_con:
        print(run_env.set_ssh_env())
    
    # Only test the running env on each server when args.test is True
    tag_extend=""
    args_info_cases = {}
    # case_name = ['pkm', 'accuracy']
    args_info_acc01 = {}
    args_info_case02 = {}
    if args.test:
        if args.weekly:
            args_info_case01 = { 'INPUT_TOKENS': [32], 'OUTPUT_TOKENS': [512], 
                                'BATCH_SIZE': 1,'PRECISION': ['bf16_fp16','bf16'] }
            args_info_case02 =  { 'INPUT_TOKENS': [1024], 'OUTPUT_TOKENS': [512], 
                                'BATCH_SIZE': 1, 'PRECISION': ['bf16'] }
            tag_extend="test_weekly"
        elif args.bi_weekly:
            args_info_case01 = { }
            args_info_case02 = { }
            args_info_acc01 = { 'PRECISION': ['bf16', 'fp16', 'int8', 'int4'] }
            tag_extend="test_bi-weekly"
        elif args.monthly:
            args_info_case01 = { 'INPUT_TOKENS': [32], 'OUTPUT_TOKENS': [512],
                                'BATCH_SIZE': [1], 'PRECISION': ['int8','int4', 'nf4'] }
            args_info_case02 = { 'INPUT_TOKENS': [32], 'OUTPUT_TOKENS': [512], 
                                'BATCH_SIZE': [1], 'PRECISION': ['bf16_int8','bf16_int4', 'w8a8'] }
            tag_extend="test_monthly"
        elif args.normal:
            args_info_case01 = { "WARMUP_STEPS": 1, 'STEPS': 5, 
                            'XFT_FAKE_MODEL':1, 'PRECISION': ['bf16_fp16','bf16','bf16_int8','bf16_int4'], 
                            'INPUT_TOKENS': [32], 'OUTPUT_TOKENS': [32] }
            
            tag_extend="test_normal"
        else:
            print("\033[1;31;40m Please specify parameter --weekly(--w) or --bi_weekly(--bw) or --monthly(--m) or --normal(--n)\033[0m")
            exit(1)
    else:
        ### args info
        if args.weekly:
            args_info_case01 = { 'INPUT_TOKENS': [1024], 'OUTPUT_TOKENS': [512], 
                                'BATCH_SIZE': 1,'PRECISION': ['bf16','bf16_fp16'] }
            args_info_case02 =  { 'INPUT_TOKENS': [1024], 'OUTPUT_TOKENS': [512], 
                                'BATCH_SIZE': 32, 'PRECISION': ['bf16'] }
            tag_extend="weekly"
        elif args.bi_weekly:
            args_info_case01 = { 'INPUT_TOKENS': [512,1024,2048], 'OUTPUT_TOKENS': [32,128,512,1024,2048],
                                'BATCH_SIZE': [1,4,8,16,32], 'PRECISION': ['bf16'] }
            args_info_case02 = { 'INPUT_TOKENS': [512,1024,2048], 'OUTPUT_TOKENS': [32,128,512,1024,2048],
                                'BATCH_SIZE': [1], 'PRECISION': ['bf16_fp16'] }
            args_info_acc01 = { 'PRECISION': ['bf16', 'fp16', 'int8', 'int4'] }
            tag_extend="bi-weekly"
        elif args.monthly:
            args_info_case01 = { 'INPUT_TOKENS': [512], 'OUTPUT_TOKENS': [512],
                                'BATCH_SIZE': [1,8], 'PRECISION': ['int8','int4', 'nf4'] }
            args_info_case02 = { 'INPUT_TOKENS': [2048], 'OUTPUT_TOKENS': [512], 
                                'BATCH_SIZE': [1,8], 'PRECISION': ['bf16_int8','bf16_int4', 'w8a8'] }
            tag_extend="monthly"
        elif args.normal:
            args_info_case01 = { "WARMUP_STEPS": 1, 'STEPS': 5, 
                            'XFT_FAKE_MODEL':1, 'PRECISION': ['bf16_fp16','bf16','bf16_int8','bf16_int4'], 
                            'INPUT_TOKENS': [32,512,1024,2048], 'OUTPUT_TOKENS': [32,128,512,1024,2048] }
            args_info_case02 = { }
            tag_extend="test_normal"
        else:
            print("\033[1;31;40m Please specify parameter --weekly(--w) or --bi_weekly(--bw) or --monthly(--m) or --normal(--n)\033[0m")
            exit(1)
 
    args_info_cases.update({"pkm":[args_info_case01, args_info_case02], "accuracy":[args_info_acc01]})
    args_info_cases = {k: [ case for case in v if len(case) !=0 ]  for k, v in args_info_cases.items()}
 
    if_docker = ""
    tags = ""
    if local_ip == "172.17.29.24":
        # check docker env 
        run_env.check_docker_env()
        if_docker = "--docker"
        tags = "ww{}_SPR_QUAD_{}".format(args.ww.upper(), tag_extend)
        models = [{'llama-2-13b': '/mnt/nfs_share/xft/llama2-xft'}, {'baichuan2-13b': '/mnt/nfs_share/xft/baichuan2-xft'},
                  {'chatglm2-6b': '/opt/dataset/chatglm2-xft'}]
    elif local_ip == "192.168.14.61":
        # check docker env 
        run_env.check_docker_env()
        if_docker = "--docker"
        tags = "ww{}_SPR_QUAD_{}".format(args.ww.upper(), tag_extend)
        models = [ {'llama-2-7b': '/opt/dataset/llama2-xft'}, {'baichuan2-7b': '/opt/dataset/baichuan2-xft'}, 
                  {'chatglm-6b': '/opt/dataset/chatglm-xft'} ]
    elif local_ip == "192.168.14.121":
        # check k8s env 
        run_env.check_k8s_env()
        tags = "ww{}_HBM_FLAT_SNC4_{}".format(args.ww.upper(), tag_extend)
        models = [ {'llama-2-7b': '/opt/dataset/llama2-xft'}, {'baichuan2-7b': '/opt/dataset/baichuan2-xft'}, 
                  {'baichuan2-13b': '/opt/dataset/baichuan2-xft'} ]
    elif local_ip == "192.168.14.119":
        # check k8s env
        run_env.check_k8s_env()
        tags = "ww{}_HBM_FLAT_SNC4_{}".format(args.ww.upper(), tag_extend)
        models = [ {'chatglm2-6b': '/opt/dataset/chatglm2-xft'}, {'chatglm-6b': '/opt/dataset/chatglm-xft'}, 
                  {'llama-2-13b': '/opt/dataset/llama2-xft'} ]
    elif local_ip == "10.165.174.148":
        # check k8s env
        run_env.check_docker_env()
        if_docker = "--docker"
        tags = "ww{}_SPR_QUAD_148_{}".format(args.ww.upper(), tag_extend)
        models = [ {'llama-2-7b': '/opt/dataset/llama2-xft'}, {'chatglm-6b': '/opt/dataset/chatglm-xft'},
                  {'baichuan2-13b': '/opt/dataset/baichuan2-xft'}, 
                  {'chatglm2-6b': '/opt/dataset/chatglm2-xft'}, {'baichuan2-7b': '/opt/dataset/baichuan2-xft'}]
    else:
        run_env.check_docker_env()
        if_docker = "--docker"
        tags = "ww{}_SPR_QUAD_{}_susan_2712".format(args.ww.upper(), tag_extend)
        models = [{'chatglm2-6b': '/opt/dataset/chatglm2-xft'}]
    
    if args.weekly:
        models = [ {'llama-2-7b': '/opt/dataset/llama2-xft'}, {'chatglm-6b': '/opt/dataset/chatglm-xft'} ]

    workload_name = 'LLMs-xFT-Public'
    
    create_dir_or_file(args.root_dir)
    wsf_root_path = chdir(args.root_dir, "wsf_root_path")
    
    # git clone code
    wsf_repo = args.repo
    branch = args.branch
    print('\033[32mCurrent wsf_repo is: \033[0m{0}'.format(wsf_repo))
    print('\033[32mCurrent wsf_branch is: \033[0m{0}'.format(branch))
    target_repo_name = "wsf-dev-" + args.ww
    wsf_dir = os.path.join(wsf_root_path, target_repo_name)
    if not os.path.exists(wsf_dir):
        os.system("git clone -b {} {} {}".format(branch, wsf_repo, wsf_dir))
    ww_repo_dir = chdir(wsf_dir, "ww_repo_dir")
    # checkout_origin(wsf_repo, branch)

    # modify terraform config
    terraform_config_file = os.path.join(wsf_dir, "script/terraform/terraform-config.static.tf")
    replacetext(local_ip, local_user)

    # run model
    print('{0}\033[32m summary result \033[0m{1}'.format("-"*50,"-"*50))
    
    all_summary_list, header_list = run_model(models, **args_info_cases)
    print(tabulate(all_summary_list, tablefmt="fancy_grid", headers=header_list, numalign="center"))

# parse the output*.log
if ((args.only_parse and args.dry_run) or (args.only_parse and args.test) or 
    ( args.only_parse and args.weekly) or (args.only_parse and args.bi_weekly) or
    ( args.only_parse and args.monthly) or ( args.only_parse and args.normal) or 
    (args.only_parse and args.test and args.dry_run ) or args.only_parse ):
    # parse output.log
    script_exec_path = os.path.realpath(os.path.dirname(__file__))
    if args.log_file:
        file_list = glob.glob(script_exec_path + "/{}".format(args.log_file))
    else:
        print("tt")
        file_list = glob.glob(script_exec_path + "/output*.log")
    summary_excel = os.path.join(script_exec_path, "{}.xlsx".format("summary"))
    print('\033[32mLog file list is: \033[0m{0}'.format(file_list))
    each_kpi_summary = []
    parse_case_sum=[]
    headers_list=[]
    if len(file_list) != 0:
        for file in file_list:
            output_file = os.path.join(script_exec_path, file)
            basename = os.path.basename(output_file).split(".")[0]
            output_excel = os.path.join(script_exec_path, "{}.xlsx".format(basename))
            headers_list.append(basename)
            if os.path.exists(output_file):
                print('{0}\033[32m parse log result \033[0m{1}'.format("-"*50,"-"*50))
                data = parse_log(output_file, local_ip)
                sheet_list = []
                with pd.ExcelWriter(output_excel) as writer:
                    cols = ["BaseModelName","Variant", "Precision", "BatchSize", "Input_Tokens","Output_Tokens",
                            "Framework", "IsPass", "Throughput", "Min_Latency", "Max_Latency" ,"P90_Latency", 
                            "1st_Token_Latency", "2nd+_Tokens_Average_Latency","accuracy", "WorkloadName","run_uri_perf", "local_IP"]
                    # print(len(data))
                    parse_case_sum.append(len(data))
                    df = pd.DataFrame(data, columns=cols)
                    df.to_excel(writer, index=False)
                    each_kpi_summary.append(data)
        
        # Summary multiple output logs
        with pd.ExcelWriter(summary_excel) as writer:
            each_kpi_summary = sum(each_kpi_summary, [])
            # print(len(each_kpi_summary))
            parse_case_sum.append(len(each_kpi_summary))
            df = pd.DataFrame(each_kpi_summary, columns=cols)
            df.to_excel(writer, index=False)
    headers_list.append("parse_all_logfile_case_sum")
    print('{0}\033[32m summary result \033[0m{1}'.format("-"*50,"-"*50))
    print(tabulate([parse_case_sum], headers=headers_list, tablefmt="fancy_grid", numalign="center"))
end_time = time.time()
print("Total time spent: {:.2f}sec".format(end_time - start_time))
