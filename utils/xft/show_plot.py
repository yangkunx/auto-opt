import pandas as pd
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

def dict_sort(dict_name):
    # 按照字典key(model name) 排序
    myKeys = list(dict_name.keys())
    myKeys.sort()
    sorted_dict = {i: dict_name[i] for i in myKeys}
    return sorted_dict

def check_dict_eunm(dict_name, model_name):
    # model 的值不存在，就添加该model值为0
    for model in model_name:
        if model not in list(send.keys()):
            dict_name[model]=0
    return dict_name


def get_emon_data(file_path, sheet_name, sample, select_col):
    df = pd.read_excel(file_path, index_col=0, header=0, sheet_name=sheet_name, usecols=lambda x: 'BaseModelName' not in x)
    sample_value = df.loc[(df['Precision'] == sample) & (df['Input_Tokens'] == 1024) & (df['Output_Tokens'] == 512) & (df['BatchSize'] == 1)]
    return sample_value

path = "./ww"

# input1024 output128 bs1 precision bf16_fp16
hbm_sheet_name = "HBM-Flat-SNC4"
simple = 'bfloat16_float16'
select_col = '1st_Token_Latency (sec)'
file_list = glob.glob(path + "/*.xlsx")
model_name = ['llama-2-7b','baichuan2-7b','baichuan2-13b','chatglm2-6b','chatglm-6b','llama-2-13b']
ww_all = {}
for file in file_list:
    ww = os.path.splitext(file)[0].split('_')[1]
    re = get_emon_data(file, hbm_sheet_name, simple, select_col).to_dict()
    send = re['2nd+_Tokens_Average_Latency (sec)']
    send = check_dict_eunm(send, model_name)
    print(dict_sort(send))
    # 以每周嵌套字典组合
    # {'ww50': {'baichuan2-13b': 0.1223, 'baichuan2-7b': 0.0659, 'chatglm-6b': 0.02743, 'chatglm2-6b': 0.02485, 'llama-2-13b': 0.05007, 'llama-2-7b': 0.06083}, 'ww48': {'baichuan2-13b': 0, 'baichuan2-7b': 0, 'chatglm-6b': 0, 'chatglm2-6b': 0.02646, 'llama-2-13b': 0, 'llama-2-7b': 0.05434}, 'ww51': {'baichuan2-13b': 0.05058, 'baichuan2-7b': 0.03004, 'chatglm-6b': 0.02745, 'chatglm2-6b': 0.0249, 'llama-2-13b': 0.05029, 'llama-2-7b': 0.02914}, 'ww49': {'baichuan2-13b': 0.12861, 'baichuan2-7b': 0.03321, 'chatglm-6b': 0.02722, 'chatglm2-6b': 0.02594, 'llama-2-13b': 0, 'llama-2-7b': 0.03042}}
    ww_all[ww] = dict_sort(send)
    

all= dict_sort(ww_all)
sample_list = list(all.values())

default_dict = defaultdict(list)

for dc in sample_list:
    for ke, va in dc.items():
        default_dict[ke].append(va)

default_dict = dict(default_dict)
print(default_dict)

df = pd.DataFrame(default_dict, index=list(all.keys()))


plt.title("2nd+_Tokens_Average_Latency")
plt.xlabel("Weekly_{}".format("model")) 
plt.ylabel("2nd+_Tokens_Average_Latency (sec)")

# setting style
plt.style.use('Solarize_Light2') 
plt.rcParams['figure.figsize'] = [14, 5] 
x = np.array(list(all.keys()))
y = np.array(default_dict['chatglm-6b'])

plt.plot(x, y,'bo-',label="2nd")

for a,b in zip(x, y):
    plt.annotate(str(b), # this is the text
                (a,b), # these are the coordinates to position the label
                textcoords="offset points", # how to position the text
                xytext=(0,4), # distance from text to points (x,y)
                ha='left') # horizontal alignment can be left, right or center

plt.show()