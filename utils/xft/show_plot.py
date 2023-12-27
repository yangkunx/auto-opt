import pandas as pd
import os
import glob

import matplotlib.pyplot as plt

def dict_sort(dict_name):
    myKeys = list(dict_name.keys())
    myKeys.sort()
    sorted_dict = {i: dict_name[i] for i in myKeys}
    return sorted_dict

def check_dict_eunm(dict_name):
    for model in model_name:
        if model not in list(send.keys()):
            dict_name[model]=0
    return dict_name

def show_plot(x_axis, y_axis, model):
    plt.title("2nd_report")
    plt.xlabel("Weekly_{}".format(model))
    plt.ylabel("2nd+_Tokens_Average_Latency (sec)")

    plt.rcParams['figure.figsize'] = [14, 5] 
    x = np.array(x_axis)
    y = np.array(y_axis)

    plt.plot(x, y, color = 'green', 
         linestyle = 'solid', marker = 'o', 
         markerfacecolor = 'red', markersize = 5) 
    # for a,b in zip(x, y): 
    #     plt.text(a, b, str(b), offset = 0.5)
    for a,b in zip(x, y):
        plt.annotate(str(b), # this is the text
                    (a,b), # these are the coordinates to position the label
                    textcoords="offset points", # how to position the text
                    xytext=(0,4), # distance from text to points (x,y)
                    ha='left') # horizontal alignment can be left, right or center

    plt.grid()

    plt.show()

def get_emon_data(file_path, sheet_name, sample, select_col):
    """
    Use pandas to get the data of Specify sample and sheet from excel
    Args:
        file_path (_type_): the path of excel
        sheet_name (_type_): the sheet of excel
        sample (_type_): the sample of excel
        select_col (_type_): the select coloum of excel

    Returns:
        _type_: Returns the float value of each cell
    """
    df = pd.read_excel(file_path, index_col=0, header=0, sheet_name=sheet_name, usecols=lambda x: 'BaseModelName' not in x)
    # 
    # sample_value = df.loc[sample, select_col]
    # print(df['Precision'])
    sample_value = df.loc[(df['Precision'] == sample) & (df['Input_Tokens'] == 1024) & (df['Output_Tokens'] == 128) & (df['BatchSize'] == 1)]
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
    # print(file)
    # print(send)
    send = check_dict_eunm(send)
    ww_all[ww] = dict_sort(send)
# print(ww_all)
all= dict_sort(ww_all)
# print(all)
from collections import defaultdict
# {i:list(j) for i in dict1.keys() for j in zip(dict1.values(),dict2.values())} 
test = []
for ww, ww_value in all.items():
    # print(ww)
    # print(ww_value)
    # test.append(ww)
    test.append(ww_value)
print(all)
print(test)
ddef = defaultdict(list)
for dc in test:
    for ke, va in dc.items():
        #   following statement is also valid
        #   ddef[ke] += [va]
        ddef[ke].append(va)

dcombo = dict(ddef)
print(dcombo)
# dcombo.update({"ww": list(all.keys())})
print(dcombo)
df = pd.DataFrame(dcombo, index=list(all.keys()))
#df.plot(kind='area', figsize=(9,6), stacked=False)
# df.plot.line( y=model_name, figsize=(20,10), title='ww_model({}_{}_{}_{})'.format("bf16_bf16","1024","128","1"), ylabel='2nd+_Tokens_Average_Latency (sec)')
import numpy as np

# x = list(all.keys())
# for model, value in dcombo.items():
#     show_plot(x, value, model)

print(plt.style.available)

plt.title("2nd+_Tokens_Average_Latency")
plt.xlabel("Weekly_{}".format("model"))
plt.ylabel("2nd+_Tokens_Average_Latency (sec)")

plt.rcParams['figure.figsize'] = [14, 5] 
x = np.array(list(all.keys()))
y = np.array(dcombo['chatglm-6b'])
# plt.style.use('seaborn-v0_8')

available = ['default'] + plt.style.available
# for i, style in enumerate(available):
#         # ax = fig.add_subplot(10, 3, i + 1)
plt.plot(x, y, color = 'blue', 
    linestyle = 'solid', marker = 'o', 
    markerfacecolor = 'red', markersize = 5) 
# for a,b in zip(x, y): 
#     plt.text(a, b, str(b), offset = 0.5)
for a,b in zip(x, y):
    plt.annotate(str(b), # this is the text
                (a,b), # these are the coordinates to position the label
                textcoords="offset points", # how to position the text
                xytext=(0,4), # distance from text to points (x,y)
                ha='left') # horizontal alignment can be left, right or center
# plt.grid()
plt.style.use("tableau-colorblind10")

# print(style)
plt.show()