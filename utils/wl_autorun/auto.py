import os
import argparse
import socket
import re
import shutil

def chdir(path):
    """
    切换目录
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


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except socket.error:
        return None



parser = argparse.ArgumentParser()
parser.add_argument("--ww", type=str, required=True, help="work week")
parser.add_argument("--root_dir", type=str, required=True, default="/home/wsf")
parser.add_argument("--platform", type=str, required=True, default="spr")

args = parser.parse_args()

models = ["llama-2-7b"]

chdir(args.root_dir)

wsf_repo="https://github.com/intel-innersource/applications.benchmarking.benchmark.platform-hero-features"
target_repo_name = "wsf-dev-" + args.ww
wsf_dir = args.root_dir + "/" + target_repo_name
if not os.path.exists(wsf_dir):
    os.system("git clone -b develop " + wsf_repo + " " + target_repo_name)

ww_repo_dir = chdir(wsf_dir)

local_ip = get_local_ip()
# modify terraform config
terraform_config_file = wsf_dir + "/script/terraform/terraform-config.static.tf"




def replacetext(replace_text): 
    with open(terraform_config_file,'r+') as f: 
        file = f.read() 
        search_text=r'"public_ip": "127.0.0.1"'
        replace_text=r'"public_ip": "{}"'.format(replace_text)
        # print(re.findall(search_text, file))
        file = re.sub(search_text, replace_text, file) 
        f.seek(0)
        f.write(file)
        f.truncate()
    print("{} text replaced".format(search_text))
    return "Text replaced"

replacetext(local_ip)


# sys.exit()

INPUTS_TOKENS=[32, 128]
OUTPUT_TOKENS=[32, 128]
BATCH_SIZE=[1, 4]


for model in models:
    build_name = "build_" + model
    build_path = os.path.join(ww_repo_dir, build_name)
    create_dir_or_file(build_path)
    model_build_dir = chdir(build_path)
    cmake_cmd = "cmake -DPLATFORM=SPR -DRELEASE=latest -DACCEPT_LICENSE=ALL -DBACKEND=terraform -DBENCHMARK= \
                 -DTERRAFORM_SUT=static -DTERRAFORM_OPTIONS='--docker --svrinfo --intel_publish --tags={}_{}_QUAD \
                 --owner=sf-post-silicon' -DTIMEOUT=60000,3600 ..".format(args.ww.upper(), args.platform)
    print('\033[32mcmake命令:\033[0m {}'.format(cmake_cmd))
    os.system(cmake_cmd)
    wl = 'xFTBench'
    wl_dir = chdir(os.path.join(build_path, "workload"))
    os.system("make")
    # print(build_path)
#     if not os.path.exists(build_dir):
#         os.system("mkdir -p " + build_dir)
#         os.chdir(build_dir)
#         cmake_cmd = "cmake -DPLATFORM=SPR -DRELEASE=latest -DACCEPT_LICENSE=ALL -DBACKEND=terraform -DBENCHMARK= -DTERRAFORM_SUT=static \
#         -DTERRAFORM_OPTIONS='--docker --svrinfo --intel_publish --tags={}_{}_QUAD --owner=sf-post-silicon' -DTIMEOUT=60000,3600 ../".format(args.ww.upper(), args.platform)
#         os.system(cmake_cmd)
#     else:
#         os.chdir(build_dir)


#     target_dir = build_dir + "/workload/xFTBench"
#     os.chdir(target_dir)
#     os.system("make")






