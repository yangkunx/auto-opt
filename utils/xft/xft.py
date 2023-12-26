import os
import argparse
import socket
import re
import time
import glob
import pandas as pd
# from kubernetes import client, config
# from kubernetes.client.rest import ApiException


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

### clean unused pod and job
# def clean_job_and_pod(clean_name):
#     # Configs can be set in Configuration class directly or using helper utility
#     config.load_kube_config()

#     v1 = client.BatchV1Api()
#     ret_all_job = v1.list_job_for_all_namespaces(watch=False)
#     # pprint(ret)
#     for item in ret_all_job.items:
#         # pprint(i.metadata)
#         name = item.metadata.name
#         namespace = item.metadata.namespace
#         # "llms-xft-public"
#         if re.search(clean_name, name):
#             # print(item.metadata.name)
#             # print(i.metadata.namespace)
#             print(
#             "%s\t%s\t%s" %
#             (item.metadata.namespace,
#                 item.metadata.name))
#             try:
#                 v1.delete_namespaced_job(name, namespace)
#             except ApiException as e:
#                 print("Exception when calling BatchV1Api->delete_namespaced_job: %s\n" % e)
        
#     v1 = client.CoreV1Api()
#     ret_all_pod = v1.list_pod_for_all_namespaces(watch=False)
#     for item in ret_all_pod.items:
        
#         name = item.metadata.name
#         ns = item.metadata.namespace
#         if re.search(clean_name, name):
#             print(
#             "%s\t%s\t%s" %
#             (item.status.pod_ip,
#                 item.metadata.namespace,
#                 item.metadata.name))
#             try:
#                 v1.delete_namespaced_pod(name, namespace)
#             except ApiException as e:
#                 print("Exception when calling CoreV1Api->delete_namespaced_pod: %s\n" % e)

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
                latency=0
                first_token_average_latency=0
                second_token_average_latency=0
                max_latency=0
                min_latency=0
                p90_latency=0
                throughput=0
                dashboard_link=""
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
                print('latency: {0}'.format(latency))
                print('dashboard_link: {0}'.format(_link))
                print('zip_link: {0}'.format(zip_link))
                print('local_ip: {0}'.format(collect_ip))


    # print(single_file_list)
    return single_file_list

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
    
def run_workload(workload, model, tags, local_ip, if_docker, model_path="", dry_run=False, **kwargs):
    cmake_cmd = "cmake -DREGISTRY={}:20666 -DPLATFORM=SPR -DRELEASE=latest -DACCEPT_LICENSE=ALL -DBACKEND=terraform -DBENCHMARK= \
                    -DTERRAFORM_SUT=static -DTERRAFORM_OPTIONS='{} --svrinfo --intel_publish --tags={} \
                    --owner=sf-post-silicon' -DTIMEOUT=60000,3600 ..".format(local_ip, if_docker,tags)
    pre_run_args = './ctest.sh -R {0} --prepare-sut -V'.format("pkm")
    base_args, loop_sum= format_args(**kwargs)
    sut_args = ' --loop={0} --reuse-sut -V --continue'.format(loop_sum)
    model_path_args = ' --set "MODEL_PATH={0}"'.format(model_path)
    run_args = './ctest.sh -R {0} --set "{1}" --set "MODEL_NAME={2}"{3}{4} '.format("pkm", base_args, model, model_path_args, sut_args)
    if dry_run:
        print('\033[32mRun_model:\033[0m \033[32m【\033[0m{}\033[32m】\033[0m'.format(model))
        print('\033[32mcmake命令:\033[0m \033[32m【\033[0m{}\033[32m】\033[0m'.format(cmake_cmd))
        print('\033[32msut_args:\033[0m \033[32m【\033[0m{}\033[32m】\033[0m'.format(pre_run_args))
        print('\033[32mRun_case_args:\033[0m \033[32m【\033[0m{}\033[32m】\033[0m'.format(run_args))
    else:
        build_name = "build_" + model
        if "/" in model:
            build_name = "build_" + model.replace("/","_")
        build_path = os.path.join(ww_repo_dir, build_name)
        create_dir_or_file(build_path)
        chdir(build_path, "ww_repo_model_build")
        #cmake
        print('\033[32mcmake命令:\033[0m \033[32m【\033[0m{}\033[32m】\033[0m'.format(cmake_cmd))
        os.system(cmake_cmd)
        chdir(os.path.join(build_path, "workload", workload), "ww_build_workload_path")
        os.system("make")
        #准备sut
        print('\033[32msut_args:\033[0m \033[32m【\033[0m{}\033[32m】\033[0m'.format(pre_run_args))
        os.system(pre_run_args)
        #运行sut
        print('\033[32mRun_case_args:\033[0m \033[32m【\033[0m{}\033[32m】\033[0m'.format(run_args))
        os.system(run_args)



parser = argparse.ArgumentParser()
parser.add_argument("--ww", type=str, default="40", help="work week")
parser.add_argument("--weekly", "--w", action="store_true", help="weekly")
parser.add_argument("--bi_weekly", "--bw", action="store_true", help="bi-weekly")
parser.add_argument("--monthly", "--m", action="store_true", help="monthly")
parser.add_argument("--root_dir", "--r", type=str, default=".", help="wsf code and exec script root_dir")
parser.add_argument("--platform", type=str, default="spr", help="the platform of run case")
parser.add_argument("--test", "--t", action="store_true", help="test the case or run env")
parser.add_argument("--dry_run", "--d", action="store_true", help="dry run")
parser.add_argument("--only_parse", "--o", action="store_true", help="Only parse the log")

args = parser.parse_args()

#get local ip
local_ip, local_user= get_local_ip_user()

start_time = time.time()
if ( not args.only_parse or (args.only_parse and args.dry_run) or 
   ( args.only_parse and args.weekly) or (args.only_parse and args.bi_weekly) or
   ( args.only_parse and args.monthly) or ( args.only_parse and args.test) or 
   (args.only_parse and args.test and args.dry_run )):
    create_dir_or_file(args.root_dir)
    wsf_root_path = chdir(args.root_dir, "wsf_root_path")
    # git clone code
    # wsf_repo = "https://github.com/JunxiChhen/applications.benchmarking.benchmark.platform-hero-features"
    # wsf_repo = "https://github.com/intel-innersource/applications.benchmarking.benchmark.platform-hero-features"
    wsf_repo = "https://github.com/yangkunx/applications.benchmarking.benchmark.platform-hero-features"
    branch = "llm-xft-ww52"
    print('\033[32mCurrent wsf_repo is: \033[0m{0}'.format(wsf_repo))
    print('\033[32mCurrent wsf_branch is: \033[0m{0}'.format(branch))
    target_repo_name = "wsf-dev-" + args.ww
    wsf_dir = os.path.join(wsf_root_path, target_repo_name)
    if not os.path.exists(wsf_dir):
        os.system("git clone -b {} {} {}".format(branch, wsf_repo, wsf_dir))
    ww_repo_dir = chdir(wsf_dir, "ww_repo_dir")

    # modify terraform config
    terraform_config_file = os.path.join(wsf_dir, "script/terraform/terraform-config.static.tf")
    replacetext(local_ip, local_user)

    # Only test the running env on each server when args.test is True
    tag_extend=""
    if args.test:
        if args.weekly:
            args_info_case01 = { 'INPUT_TOKENS': [1024], 'OUTPUT_TOKENS': [512], 
                                'BATCH_SIZE': 1,'PRECISION': ['bf16_fp16','bf16'] }
            args_info_case02 =  { 'INPUT_TOKENS': [1024], 'OUTPUT_TOKENS': [512], 
                                'BATCH_SIZE': 1, 'PRECISION': ['bf16'] }
            tag_extend="test_weekly"
        elif args.bi_weekly:
            args_info_case01 = { 'INPUT_TOKENS': [1024], 'OUTPUT_TOKENS': [1024],
                                'BATCH_SIZE': [1], 'PRECISION': ['bf16'] }
            args_info_case02 = { 'INPUT_TOKENS': [1024], 'OUTPUT_TOKENS': [1024],
                                'BATCH_SIZE': [1], 'PRECISION': ['bf16_fp16'] }
            tag_extend="test_bi-weekly"
        elif args.monthly:
            args_info_case01 = { 'INPUT_TOKENS': [512], 'OUTPUT_TOKENS': [512],
                                'BATCH_SIZE': [1], 'PRECISION': ['int8','int4', 'nf4'] }
            args_info_case02 = { 'INPUT_TOKENS': [2048], 'OUTPUT_TOKENS': [512], 
                                'BATCH_SIZE': [1], 'PRECISION': ['bf16_int8','bf16_int4', 'w8a8'] }
            tag_extend="test_monthly"
        else:
            print("\033[1;31;40m Please specify parameter --weekly(--w) or --bi_weekly(--bw) or --monthly(--m) \033[0m")
            exit(1)
    else:
        ### args info
        if args.weekly:
            args_info_case01 = { 'INPUT_TOKENS': [32], 'OUTPUT_TOKENS': [32], 
                                'BATCH_SIZE': 1,'PRECISION': ['bf16_fp16','bf16'] }
            args_info_case02 =  { 'INPUT_TOKENS': [32], 'OUTPUT_TOKENS': [32], 
                                'BATCH_SIZE': 1, 'PRECISION': ['bf16'] }
            tag_extend="weekly"
        elif args.bi_weekly:
            args_info_case01 = { 'INPUT_TOKENS': [512,1024,2048], 'OUTPUT_TOKENS': [32,128,512,1024,2048],
                                'BATCH_SIZE': [1,4,8,16,32], 'PRECISION': ['bf16'] }
            args_info_case02 = { 'INPUT_TOKENS': [512,1024,2048], 'OUTPUT_TOKENS': [32,128,512,1024,2048],
                                'BATCH_SIZE': [1], 'PRECISION': ['bf16_fp16'] }
            tag_extend="bi-weekly"
        elif args.monthly:
            args_info_case01 = { 'INPUT_TOKENS': [512], 'OUTPUT_TOKENS': [512],
                                'BATCH_SIZE': [1,8], 'PRECISION': ['int8','int4', 'nf4'] }
            args_info_case02 = { 'INPUT_TOKENS': [2048], 'OUTPUT_TOKENS': [512], 
                                'BATCH_SIZE': [1,8], 'PRECISION': ['bf16_int8','bf16_int4', 'w8a8'] }
            tag_extend="bi-monthly"
        else:
            print("\033[1;31;40m Please specify parameter --weekly(--w) or --bi_weekly(--bw) or --monthly(--m) \033[0m")
            exit(1)

    if_docker = ""
    tags = ""
    # 10.165.174.148 172.17.29.24
    if local_ip == "172.17.29.24":
        if_docker = "--docker"
        tags = "ww{}_SPR_QUAD_{}".format(args.ww.upper(), tag_extend)
        models = [{'llama-2-13b': '/mnt/nfs_share/xft/llama2-xft'}, {'baichuan2-13b': '/mnt/nfs_share/xft/baichuan2-xft'}]
    elif local_ip == "192.168.14.61":
        if_docker = "--docker"
        tags = "ww{}_SPR_QUAD_{}".format(args.ww.upper(), tag_extend)
        models = [ {'llama-2-7b': '/opt/dataset/llama2-xft'}, {'chatglm2-6b': '/opt/dataset/chatglm2-xft'},
                   {'baichuan2-7b': '/opt/dataset/baichuan2-xft'}, {'chatglm-6b': '/opt/dataset/chatglm-xft'} ]
    elif local_ip == "192.168.14.121":
        tags = "ww{}_HBM_FLAT_SNC4_{}".format(args.ww.upper(), tag_extend)
        models = [ {'llama-2-7b': '/opt/dataset/llama2-xft'}, {'baichuan2-7b': '/opt/dataset/baichuan2-xft'}, 
                  {'baichuan2-13b': '/opt/dataset/baichuan2-xft'} ]
    elif local_ip == "192.168.14.119":
        tags = "ww{}_HBM_FLAT_SNC4_{}".format(args.ww.upper(), tag_extend)
        models = [ {'chatglm2-6b': '/opt/dataset/chatglm2-xft'}, {'chatglm-6b': '/opt/dataset/chatglm-xft'}, 
                  {'llama-2-13b': '/opt/dataset/llama2-xft'} ]
    elif local_ip == "10.165.174.148":
        if_docker = "--docker"
        tags = "ww{}_SPR_QUAD_148_{}".format(args.ww.upper(), tag_extend)
        models = [{'chatglm-6b': '/opt/dataset/chatglm-xft'}]

    elif local_ip == "10.45.247.77":
        if_docker = "--docker"
        tags = "ww{}_SPR_QUAD_{}_susan_2712".format(args.ww.upper(), tag_extend)
        models = [{'chatglm2-6b': '/opt/dataset/chatglm2-xft'}]
    else:
        print("Not support this IP")
        exit(1)
    
    if args.weekly:
        models = [ {'llama-2-7b': '/opt/dataset/llama2-xft'}, {'chatglm-6b': '/opt/dataset/chatglm-xft'} ]

    workload_name = 'LLMs-xFT-Public'

    # run model
    for all_models in models:
        for model, model_path in all_models.items():
            run_workload(workload_name, model, tags, local_ip, if_docker, model_path, dry_run=args.dry_run, **args_info_case01)
            run_workload(workload_name, model, tags, local_ip, if_docker, model_path, dry_run=args.dry_run, **args_info_case02)

if ((args.only_parse and args.dry_run) or (args.only_parse and args.test) or 
    ( args.only_parse and args.weekly) or (args.only_parse and args.bi_weekly) or
    ( args.only_parse and args.monthly) or 
    (args.only_parse and args.test and args.dry_run ) or args.only_parse ):
    # parse output.log
    script_exec_path = os.path.realpath(os.path.dirname(__file__))
    file_list = glob.glob(script_exec_path + "/output*.log")
    summary_excel = os.path.join(script_exec_path, "{}.xlsx".format("summary"))
    print('\033[32mLog file list is: \033[0m{0}'.format(file_list))
    each_kpi_summary = []
    if len(file_list) != 0:
        for file in file_list:
            output_file = os.path.join(script_exec_path, file)
            basename = os.path.basename(output_file).split(".")[0]
            output_excel = os.path.join(script_exec_path, "{}.xlsx".format(basename))

            if os.path.exists(output_file):
                print('{0}\033[32m parse log result \033[0m{1}'.format("-"*50,"-"*50))
                data = parse_log(output_file, local_ip)
                sheet_list = []
                with pd.ExcelWriter(output_excel) as writer:
                    cols = ["BaseModelName","Variant", "Precision", "BatchSize", "Input_Tokens","Output_Tokens",
                            "Framework", "IsPass", "Throughput", "Min_Latency", "Max_Latency" ,"P90_Latency", 
                            "1st_Token_Latency", "2nd+_Tokens_Average_Latency", "WorkloadName","run_uri_perf", "local_IP"]
                    print(len(data))
                    df = pd.DataFrame(data, columns=cols)
                    df.to_excel(writer, index=False)
                    each_kpi_summary.append(data)
        
        # Summary multiple output logs
        with pd.ExcelWriter(summary_excel) as writer:
            each_kpi_summary = sum(each_kpi_summary, [])
            print(len(each_kpi_summary))
            df = pd.DataFrame(each_kpi_summary, columns=cols)
            df.to_excel(writer, index=False)

end_time = time.time()
print("耗时: {:.2f}秒".format(end_time - start_time))
