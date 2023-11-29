import yaml
import git
import logging
import argparse
import shlex
import copy
import time, os, re
from glob import glob
from itertools import product
from subprocess import PIPE, Popen
from git import RemoteProgress


class Parse_yaml():
    """
    #解析yaml文件
    """
    def __init__(self, yaml_path):
        self.yaml_path = yaml_path
        self.data = yaml.load(open(yaml_path, 'r'),Loader=yaml.FullLoader) 

    def get_tag(self):
        #print(self.data)
        tag_list = self.data['dashboadtags']
        return tag_list

    def get_workload(self):
        workloads = self.data['WorkLoad']
        return workloads

class Git_progress(RemoteProgress):
    """
    #打印git clone的进度条
    """
    def update(self, *args):
        print(self._cur_line)

class Get_wsf_code():
    """
    获取wsf 代码
    """
    def __init__(self, llm_dir, repo_url, repo_dir_name, branch=None):
        self.llm_dir = llm_dir
        self.repo_url = repo_url
        self.repo_dir_name = repo_dir_name
        try:
            self.repo = git.Repo(repo_dir_name)
        except git.exc.InvalidGitRepositoryError:
            logging.error("Check-git-dir: The {} directory is not a git repository ".format(repo_dir_name))
        except git.exc.NoSuchPathError:
           logging.error("Check-git-dir: The {} directory is not found".format(repo_dir_name)) 
        self.branch = branch
        self.process = Git_progress()

    def __check_git_dir(self, check_git_dir):
        """
        检查指定目录是否是git repo
        """
        try:
            repo = git.Repo(check_git_dir)
            git_dir = repo.git_dir
            active_branch = repo.active_branch.name
            logging.info("Check-git-dir: The {} directory is a git repository ".format(git_dir) )
            logging.info("Aurrent_branch: {}".format(active_branch) )
            return True
        except git.exc.InvalidGitRepositoryError:
            logging.error("Check-git-dir: The {} directory is not a git repository ".format(check_git_dir))
            return False
        except git.exc.NoSuchPathError:
            logging.error("Check-git-dir: The {} directory is not exsit".format(check_git_dir))
            return False
        
    def __clone(self, branch):
        """
        clone code
        """
        git.Repo.clone_from(self.repo_url, self.repo_dir_name, branch=self.branch, progress=self.process)
        active_branch = git.Repo(self.repo_dir_name).active_branch.name
        logging.info("Aurrent_branch: {}".format(active_branch) )

    def __reset(self):
        """
        reset repo
        """
        logging.info("Reset: reset the git repo")
        self.repo.git.reset('--hard')
    
    def __checkout(self):
        """
        checkout branch
        """
        logging.info("Checkout: checkout the branch")
        if self.branch == None:
            self.repo.git.checkout("develop")
        else:
            self.repo.git.checkout(self.branch)
    
    def __pull(self):
        """
        pull code
        """
        active_branch = git.Repo(self.repo_dir_name).active_branch.name
        logging.info("Aurrent_branch: {}".format(active_branch) )
        logging.info("Pull: pull the latest code")
        origin = self.repo.remotes.origin
        origin.pull()
        logging.info("Pull: over to pull the latest code")
    
    def get_code(self):
        """
        克隆wsf,并执行reset, checkout, pull
        """
        logging.info("Repo_url: {0}".format(repo_url))
        if not self.__check_git_dir(self.repo_dir_name):
            logging.info("Clone: the wsf code is downloading")
            if self.branch == None:
                try:
                    self.__clone("develop")
                    return True
                except:
                    logging.error("Remote: {} Repository not found.".format("develop"))
                    return False
            else:
                try:
                    self.__clone(self.branch)
                    return True
                except:
                    logging.error("Remote: {} Repository not found.".format(self.branch))
                    return False
        else:
            self.__reset()
            self.__checkout()
            self.__pull()
            return True

class Test_case():
    """
    运行case
    """
    def __init__(self, host=None, backend=None, platform=None, nightly_tag=None, tag_recipe_type=None, workload_name=None, args=None, use_deepspeed=False):
        self.tag_recipe_type = tag_recipe_type
        self.workload_name = workload_name
        self.args = args
        self.host = host
        self.backend = backend
        self.platform = platform
        self.nightly_tag = nightly_tag
        self.use_deepspeed = use_deepspeed

    def __Cartesian(self, input_dict):
        args_values = product(*[v if isinstance(v, (list, tuple)) else [v] for v in input_dict.values()])
        all_cases_dict = [dict(zip(input_dict.keys(), values)) for values in args_values]
        return all_cases_dict

    def __run_command(self, command, log_path="./wl_run.log", ds_log_path='./ds_url.log', base_args=None, wl_name=None):
        # print(log_path)
        logging.info("workload_run_log:" + log_path)
        logging.info("dashboad_url_log:" + ds_log_path)
        process = Popen(shlex.split(command), stdout=PIPE)
        # list=[]
        # dict={}
        while True:
            output = process.stdout.readline().rstrip().decode('utf-8')
            if output == '' and process.poll() is not None:
                break
            if output:
                with open(log_full_path, 'a') as logfile:
                    logfile.write(output.strip() + "\n")
                    print(output.strip())
                    with open(ds_log_path, 'a') as ds_log:
                        if re.search("WSF Portal URL", output):
                            #提取dashboad_url
                            ds_log.write(re.sub("^[0-9]+(.*])?:", "", output.strip()) + ", ")
                            ds_log.write(wl_name)
                            ds_log.write("\n")
                        elif re.search("INPUT_TOKENS:", output) or re.search("OUTPUT_TOKENS:", output) or re.search("PRECISION:", output) or re.search('(Average\s+latency.*: |Inference\s+latency: |acc\s+\|(\d+(\.\d+)?))', output):
                            ds_log.write(re.sub("^[0-9]+(.*])?:", "", output.strip()) + ", ")
        rc = process.poll()
        return rc

    def __format_args(self, test_case, **kwargs):
        """
        格式化输出参数，以 key1=value1/key2=value2 输出
        """
        base_args= ''
        loop_sum = 1
        if test_case == "accuracy":
            base_args = '{0}={1}'.format('PRECISION', str(" ".join(str(v) for v in kwargs['PRECISION'])))
            loop_sum = len(kwargs['PRECISION'])
        else:
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

    def __run_workloads(self, backend_run, test_case='pkm',special_args=None, logs_path="./wl_run.log", ds_log_path='./ds_url.log', wl_name=None, **kwargs):
        """
        #backend是docker和terraform的case执行
        """
        self.__run_command('make', log_path=logs_path)
        if backend_run == "terraform":
            base_args, loop_sum = self.__format_args(test_case, **kwargs)
            #准备sut
            run_args = './ctest.sh -R {0} --prepare-sut -V'.format(test_case)
            logging.info('\033[32mTest_case:\033[0m {0}'.format(run_args))
            self.__run_command(run_args, log_path=logs_path)
            #运行sut 
            sut_args = ' --loop={0} --reuse-sut -V'.format(loop_sum)
            if special_args is None:
                run_args = './ctest.sh -R {0} --set "{1}"{2}'.format(test_case, base_args, sut_args)
                logging.info('\033[32mTest_case:\033[0m {0}'.format(run_args))
                self.__run_command(run_args, log_path=logs_path, ds_log_path=ds_log_path, base_args=base_args, wl_name=wl_name)
            else:
                all_cases_list = self.__Cartesian(special_args)
                for spec_args in all_cases_list:
                    for key, value in spec_args.items():
                        for model_name, model_path in value.items():
                                model_name_value = '{0}={1}'.format(key, model_name)
                                model_path_value = '{0}={1}'.format('MODEL_PATH', model_path)
                                run_args = './ctest.sh -R {0} --set "{1}" --set "{2}" --set "{3}"{4}'.format(test_case, model_name_value, model_path_value, base_args, sut_args)
                                logging.info('\033[32mTest_case:\033[0m {0}'.format(run_args))
                                self.__run_command(run_args, log_path=logs_path, ds_log_path=ds_log_path, base_args=base_args, wl_name=wl_name)
        elif backend_run == "docker":
            all_cases_dict = Cartesian(kwargs)
            for set_args in all_cases_dict:
                base_args = ""
                for key, value in set_args.items():
                    arg_keys = '{0}={1}'.format(key, value)
                    base_args = base_args + arg_keys + "/"
                run_args = './ctest.sh -R {0} --set "{1}" -V'.format(test_case, base_args[:-1])
                logging.info('\033[32mTest_case:\033[0m {0}'.format(run_args))
                # os.system('{0}'.format(run_args))
    
    def cmake(self):
        logging.info('\033[32mcmake命令:\033[0m cmake  -DREGISTRY={0}:5000 -DBACKEND={1} -DPLATFORM={2} -DTERRAFORM_OPTIONS="--docker --svrinfo --intel_publish --owner=sf-ai-kun  --tags={3}" -DTERRAFORM_SUT=static -DBENCHMARK= .. '.format(self.host, self.backend, self.platform, self.nightly_tag))
        self.__run_command('cmake  -DREGISTRY={0}:5000 -DBACKEND={1} -DPLATFORM={2} -DTERRAFORM_OPTIONS="--docker --svrinfo  --intel_publish --owner=sf-ai-kun  --tags={3}" -DTERRAFORM_SUT=static -DBENCHMARK= .. '.format(self.host, self.backend, self.platform, self.nightly_tag), log_path=log_full_path)

    def scenes(self):
        if re.search(self.tag_recipe_type, self.workload_name):
            if dry_run:
                if self.use_deepspeed:
                    base_args = "USE_DEEPSPEED=True/STEPS=10"
                else:
                    base_args = 'STEPS=10'
                logging.info('\033[32mTest_case:\033[0m ./ctest.sh -R pkm --set "{0}"  -V'.format(base_args))
                os.system('./ctest.sh -R pkm --set "{0}"  -V'.format(base_args))
            else:
                for test_case in self.args['test_cases']:
                    recipe_type_args = copy.deepcopy(self.args['set_args'])
                    if self.use_deepspeed:
                        if tag_recipe_type == "OOB":
                            recipe_type_args['PRECISION'] = ['bfloat16']
                        else:
                            recipe_type_args['PRECISION'] = ['amx_bfloat16']
                    else:
                        recipe_type_args['USE_DEEPSPEED'] = False
                    self.__run_workloads(backend, test_case, self.args['special_args'], log_full_path, dashboad_url_log, self.workload_name, **recipe_type_args)


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

def chdir(path):
    """
    切换目录
    """
    try:
        os.chdir(path)
        parent_dir = os.getcwd()
        logging.info('Current working directory: {0}'.format(parent_dir))
    except FileNotFoundError:
        logging.error("Directory: {0} does not exist".format(path))
        parent_dir = None
    except NotADirectoryError:
        logging.error("{0} is not a directory".format(path))
        parent_dir = None
    except PermissionError:
        logging.error("You do not have permissions to change to {0}".format(path))
        parent_dir = None
    
    return parent_dir


yaml_path = "/home/yangkun/lab/yangkunx/autorun/wl.yaml"
base_path = "/home/yangkun/lab/yangkunx"
yaml_name = "wl.yaml"
repo_dir_name = 'ww38_new'
branch_name = "ww38"
build_name = "build"
repo_url = "https://github.com/yangkunx/applications.benchmarking.benchmark.platform-hero-features.git"
#定义日志文件路径，如果存在则删除
log_full_path =  create_log(base_path, 'wl_run')
dashboad_url_log = create_log(base_path, 'ds_url')

#定义logging
level = logging.INFO
format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
handlers = [logging.FileHandler(log_full_path), logging.StreamHandler()]
logging.basicConfig(level = level, format = format, handlers = handlers)

parser = argparse.ArgumentParser('Auto run the specify WL case', add_help=False)
parser.add_argument("--host", "--h", default="172.17.29.24",  type=str, help="host ip")
parser.add_argument("--nightly", "--n", default="ww22.1", type=str, help="tag nightly")
parser.add_argument("--backend", "--b", default="terraform", type=str, help="wsf run backend")
parser.add_argument("--platform", "--p", default="SPR", type=str, help="wsf run platform")
parser.add_argument("--dry-run", "--d", action="store_true", help="dry run")

pass_args = parser.parse_args()
nightly = pass_args.nightly
host = pass_args.host
backend = pass_args.backend
platform = pass_args.platform
dry_run = pass_args.dry_run

logging.info('Current pass argument: {}'.format({'nightly': nightly, 'host': host, 'backend': backend, 'platform': platform, 'dry_run': dry_run}))

llm = Get_wsf_code(base_path, repo_url, repo_dir_name, branch_name)
llm.get_code()

#切换到wsf代码的目录
wsf_path = os.path.join(base_path,'autorun', repo_dir_name)
parent_dir = chdir(wsf_path)
#拼接出需要创建build目录的完整路径
build_path = os.path.join(parent_dir, build_name)

#判断build_dir目录是否存在，存在先删除build_dir目录, 创建build目录

create_dir_or_file(build_path)

#配置运行k8s的terraform的环境
terraform_config_name = os.path.join(wsf_path, "script/terraform", "terraform-config.static.tf")

os.system('sed -i "s/xwu2/yangkun/g; s/10.165.31.154/{0}/g; s/10.165.31.40/{0}/g" {1}'.format(host, terraform_config_name))
logging.info("terraform的环境配置完成")

yml_file_name = os.path.join(base_path, "autorun", yaml_name)
yaml_data = Parse_yaml(yml_file_name)

for tag in yaml_data.get_tag():
    parent_build_dir = chdir(build_path)
    logging.info("\033[32mDashbord_tag:\033[0m {}".format(tag))
    nightly_tag = "{0},{1}".format(nightly, tag)
    #运行cmake 命令
    wsf_case = Test_case(host=host, backend=backend, platform=platform, nightly_tag=nightly_tag)
    wsf_case.cmake()
    for wl, args in yaml_data.get_workload().items():
        if args is not None:
            build_wl_dir = chdir(os.path.join(parent_build_dir, "workload", wl))
            logging.info("\033[32mWORKLOAD_BUILD_NAME:\033[0m {}".format(build_wl_dir))
            logging.info("\033[32mWORKLOAD_NAME:\033[0m {}".format(wl))
            use_deepspeed = args['set_args']['USE_DEEPSPEED']
            #platform是EMR，那么只执行deepspeed,且只执行bfloat16
            if platform != "EMR":
                if tag =="LLM,Dev":
                    dev_case = Test_case(tag_recipe_type="Dev", workload_name=wl, args=args)
                    dev_case.scenes()
                if tag =="LLM,OOB":
                    oob_case = Test_case(tag_recipe_type="OOB", workload_name=wl, args=args)
                    oob_case.scenes()
            if tag =="LLM,OOB,DeepSpeed":
                oob_ds_case = Test_case(tag_recipe_type="OOB", workload_name=wl, args=args, use_deepspeed=use_deepspeed)
                oob_ds_case.scenes()
            if tag =="LLM,Dev,DeepSpeed":
                dev_ds_case = Test_case(tag_recipe_type="Dev", workload_name=wl, args=args, use_deepspeed=use_deepspeed)
                dev_ds_case.scenes()