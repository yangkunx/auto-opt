import yaml
import time
import os

yml_file = "/home/yangkun/fork/autorun/wl-bak.yaml"
data = yaml.load(open(yml_file, 'r'),Loader=yaml.FullLoader) 

print("开始日期：{}".format(time.strftime("%Y-%m-%d %H:%M:%S")))
start_time = time.time()
for tag in data['dashboadtags']:
    # for in tag
    # parent_build_dir = chdir(path)
    # print(parent_build_dir)
    # parent_build_dir = chdir(path)
    # print(parent_build_dir)
    #os.system('cmake  -DREGISTRY=172.17.29.24:20666 -DBACKEND=terraform -DTERRAFORM_OPTIONS="--svrinfo --owner=sf-ai-kun --intel_publish --tags={}" -DTERRAFORM_SUT=static -DBENCHMARK= ..'.format(tag))

    print("Dashbord_tag: {}".format(tag))
    for wl, args in data['WorkLoad'].items():
        if args is not None:
            # print(os.path.join(parent_build_dir, "workload", wl))
            # build_wl_dir = chdir(os.path.join(parent_build_dir, "workload", wl))
            # print(build_wl_dir)
            print("WORK_LOAD_NAME: {}".format(wl))
            if tag =="ww30.1,LLM,Dev":
                for precision in args['precision']:
                    for test_case in args['test_cases']:
                        for input_token in args["input_tokens"]:
                            print('./ctest.sh -R {0} --set "STEPS={1}/PRECISION={2}/INPUT_TOKENS={3}" -V'.format(test_case, args['STEPS'], precision, input_token))
                            #os.system('make')
                            #os.system('./ctest.sh -R {0} --set "STEPS={1}/PRECISION={2}" -V'.format(test_case, args['STEPS'], precision))
            if tag =="ww30.1,LLM,Dev,TPP":
                if wl not in ['OPT-PyTorch-Dev', "Bloom-PyTorch-Dev"] :
                    for precision in args['precision']:
                        for test_case in args['test_cases']:
                            for input_token in args["input_tokens"]:
                                if precision == "amx_bfloat16":
                                    print('./ctest.sh -R {0} --set "STEPS={1}/PRECISION={2}/USE_TPP=True/INPUT_TOKENS={3}" -V'.format(test_case, args['STEPS'], precision,input_token))
                                    #os.system('make')
                                    #os.system('./ctest.sh -R {0} --set "STEPS={1}/PRECISION={2}/USE_TPP=True" -V'.format(test_case, args['STEPS'], precision))
            if tag =="ww30.1,LLM,Dev,DeepSpeed":
                for precision in args['precision']:
                    for test_case in args['test_cases']:
                        for input_token in args["input_tokens"]:
                            if precision == "amx_bfloat16":
                                print('./ctest.sh -R {0} --set "STEPS={1}/PRECISION={2}/USE_DEEPSPEED=True/INPUT_TOKENS={3}" -V'.format(test_case, args['STEPS'], precision,input_token))
                                #os.system('make')
                                #os.system('./ctest.sh -R {0} --set "STEPS={1}/PRECISION={2}/USE_DEEPSPEED=True" -V'.format(test_case, args['STEPS'], precision))
            if tag =="ww30.1,LLM,Dev,DeepSpeed,TPP":
                if wl not in ['OPT-PyTorch-Dev', "Bloom-PyTorch-Dev"] :
                    for precision in args['precision']:
                        for test_case in args['test_cases']:
                            for input_token in args["input_tokens"]:
                                if precision == "amx_bfloat16":
                                    #os.system('make')
                                    print('./ctest.sh -R {0} --set "STEPS={1}/PRECISION={2}/USE_TPP=True/USE_DEEPSPEED=True/INPUT_TOKENS={3}" -V'.format(test_case, args['STEPS'], precision, input_token))
                                    #os.system('./ctest.sh -R {0} --set "STEPS={1}/PRECISION={2}/USE_TPP=True/USE_DEEPSPEED=True" -V'.format(test_case, args['STEPS'], precision))


end_time = time.time()
print("耗时: {:.2f}秒".format(end_time - start_time))
print("结束日期：{}".format(time.strftime("%Y-%m-%d %H:%M:%S")))