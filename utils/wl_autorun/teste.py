
import yaml

yml_file_name= "./wl.yaml"
data = yaml.load(open(yml_file_name, 'r'),Loader=yaml.FullLoader)

print(data['WorkLoad']['LLMs-IPEXBench-Dev']['set_args'])