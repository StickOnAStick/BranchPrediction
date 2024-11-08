import pandas as pd
import numpy as np
from recompiler import find_2_pow
import warnings
import datetime
import matplotlib.pyplot as plt
import os
import json
import pathlib
from scipy.interpolate import make_interp_spline, pchip
warnings.simplefilter(action='ignore', category=FutureWarning)

MAIN_PATH           = pathlib.Path(__file__).parent.parent.resolve()
LOG_PATH            = MAIN_PATH.joinpath("python/Test_logs")
CSV_PATH            = MAIN_PATH.joinpath("python/Trace_tests/")
CHAMPSIM_EXE_PATH   = MAIN_PATH.joinpath("ChampSim/bin/")
TRACER_PATH         = MAIN_PATH.joinpath("ChampSim/tracer") # Tracer tests 
PREDICTOR_PATH      = MAIN_PATH.joinpath("ChampSim/branch") # Predictors
CONFIG_PATH         = MAIN_PATH.joinpath("python/Test_configs")

assert LOG_PATH.is_dir()
assert CSV_PATH.is_dir()
assert CHAMPSIM_EXE_PATH.is_dir()
assert TRACER_PATH.is_dir()
assert PREDICTOR_PATH.is_dir()


def PARSE_JSON(log,test):
    params=["Test",
            "Size",
            "Branch Prediction Accuracy",
            "instructions",
            "cycles",
            "MPKI",
            "Avg ROB occupancy at mispredict",
            "IPC"]

    mispredict = [  "BRANCH_CONDITIONAL",
                    "BRANCH_DIRECT_JUMP",
                    "BRANCH_DIRECT_CALL",
                    "BRANCH_INDIRECT",
                    "BRANCH_INDIRECT_CALL",
                    "BRANCH_RETURN"]
    
    output = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    with open(log,"r") as file:
        data = json.load(file)
        output[0] = data[test]['traces'][0][len(str(TRACER_PATH))+1:len(str(data[test]['traces'][0]))-len(".champsimtrace.xz")]
        try: 
            output[1] = data[test]['traces'][1]
        except: 
            output[1] = 0
        a = data[test]['sim']['cores'][0]
        for i in range(2,len(params)-1):
            output[i] = data[test]['sim']['cores'][0][params[i]]
        output[7] = data[test]['sim']['cores'][0][params[5]]/data[test]['sim']['cores'][0][params[4]]
        for i in range(0,len(mispredict)):
            output[i+7] = data[test]['sim']['cores'][0]['mispredict'][mispredict[i]]
        for i in mispredict:
            params.append(i)
        # print(output)
    return pd.DataFrame(list([output]),columns= params)



# find the relavent text blocks in the champsim_log output 
# parse the individual components of the text block into a dataframe
# concatenate the tests together to get one dataframe of tests
def create_csv():
    # print ("creating a csv file for: " + log)
    params =["Test",
            "Size",
            "Branch Prediction Accuracy",
            "instructions",
            "cycles",
            "MPKI",
            "Avg ROB occupancy at mispredict",
            "IPC",
            "BRANCH_CONDITIONAL",
            "BRANCH_DIRECT_JUMP",
            "BRANCH_DIRECT_CALL",
            "BRANCH_INDIRECT",
            "BRANCH_INDIRECT_CALL",
            "BRANCH_RETURN"]


    for json_file in os.listdir(LOG_PATH):
        data = pd.DataFrame(columns=params)
        test = 0
        while True:
            try:
                append_data = PARSE_JSON(str(LOG_PATH) + "/" + json_file,test)
                data = pd.concat([data,append_data])
                test += 1
            except: 
                break
        data.sort_values(['Size'],inplace=True)
        data.to_csv(str(CSV_PATH) + "/" + json_file[:len(json_file)-len(".json")] + ".csv", mode='w+')
    # print("Created file:" + str(CSV_PATH) +"/"+ log[(len(str(CSV_PATH)) -2):(len(log) - len(".json"))] +".csv")


def display_size_graph(predictors,size):
    file_list = os.listdir(CSV_PATH)
    csvlist = []
    predictor_list = [0,0,0]
    predictor_set = []

    # create a list object for each csv file,
    # it contains the predictor type, predictor size, and average prediction acurracy for the tests that
    for file in file_list:
        branch_csvs = pd.read_csv(str(CSV_PATH) + "/" + file)
        size_set = set(branch_csvs["Size"]) 
        number_of_test_per_size = int(len(branch_csvs.index) / len(size_set)) 
        predictor_list[0] = file[:len(file)-len(".cvs")]
        count = 0
        for size in size_set:
            count += 1
            predictor_list[1] = size
            for i in range(0,len(branch_csvs.index)):
                if size == branch_csvs["Size"][i]:
                    predictor_list[2]+= branch_csvs["Branch Prediction Accuracy"][i]
            predictor_list[2] = predictor_list[2] / number_of_test_per_size
            predictor_set.append(predictor_list[:])
            predictor_list[2] = 0
    
    size_independent_predictors = []
    for predictor in predictors:
        size_independent_predictors.append(predictor[:predictor.find("_size")])
    predictor_set.sort(key=asort)
    for ps in set(size_independent_predictors):
        y_axis = []
        x_axis = []
        for pl in predictor_set:
            if pl[0] == ps:
                x_axis.append(int(pl[1]))
                y_axis.append(pl[2])
        x_axis = np.array(x_axis)
        y_axis = np.array(y_axis)

        # if you want an interped graph
        # X_ = np.linspace(0, np.max(x_axis), 5000)
        # Y_ = pchip(x_axis,y_axis)
        # plt.plot(X_, Y_(X_), label= ps)
        
        # if you want no interp
        plt.xscale('log', base=2)
        plt.plot(x_axis,y_axis, label = ps)
    
    plt.legend()
    plt.ylabel("Prediction Accuracy")
    plt.xlabel("Predictor size (bits)")
    plt.show(block=True)
def asort(val):
    return val[1]
    # input: list of names of the predictors you want graphed 
    # ALERT: this needs to be redone
def display_graph(input):
    # This is the section of the program that graphs the data 

    print(os.getcwd())
    # Find the CSV logs 
    # then add them to the test if they have unique names 
    file_list = os.listdir(str(CSV_PATH)) 
    csvlist = []
    for i in file_list:
        for j in input:
            if (i.find(j) != -1):
                if (i.find('.csv') != -1): # filter out only tracer files 
                    csvlist.append(i)
                    break
                    
    print(csvlist)
    csvlist.sort(key = str.casefold)
    print(csvlist)
    # initialization data for the plot 
    fig,ax = plt.subplots(figsize =(16, 9))
    branch_csvs = []
    barwidth = 1/(len(csvlist)+1)
    count = 0

    # todo, this code looks awful please rewrite if showing anyone else
    for i in csvlist:
        
        branch_csvs = pd.read_csv(str(CSV_PATH) + "/" + i)
        BPA = branch_csvs["Branch Prediction Accuracy"]
        bar_offset = []
        a = np.arange(float(len(BPA)))
        for i in a:
            bar_offset.append(i + barwidth*count)
        bar = plt.bar(bar_offset, BPA, width=barwidth, label = csvlist[count])
        for i in bar:
            height = i.get_height()
            plt.text( i.get_x() + i.get_width()/2, height, f'{height:.2f}', ha='center', va='bottom')
        count += 1

    branch_csvs = pd.read_csv(str(CSV_PATH) + "/" + csvlist[0])
    # label axis
    plt.xlabel('Trace Benchmarks', fontweight ='bold', fontsize = 15) 
    plt.ylabel('Branch Prediction Accuracy', fontweight ='bold', fontsize = 15) 

    # Add Text watermark
    fig.text(0.125, 0.875, 'Project Claros', fontsize = 12,
            color ='grey', ha ='left', va ='top',
            alpha = 0.7)
    a = csvlist[0]
    # Create appropriate X axis labels 
    plt.xticks([r+barwidth for r in range(len(branch_csvs))],branch_csvs["Test"])

    plt.legend()
    plt.show(block=True)

#create_csv("ChampSim/python/Test_logs/bimodal1k.json")

# for windows only
# for i in os.listdir("champsim/python/Test logs"):
#     create_csv("champsim/python/Test logs/"+ i)

# display_size_graph(["bimodal1k","bimodal2k","bimodal4k","bimodal8k","bimodal16k","bimodal32k","bimodal64k","bimodal128k",
#                    "gshare1k","gshare2k","gshare4k","gshare8k","gshare16k","gshare32k","gshare64k","gshare128k",
#                    "global_history1k","global_history2k","global_history4k","global_history8k","global_history16k","global_history32k","global_history64k","global_history128k"],128)


#,"bimodal256k","bimodal512k","bimodal1024k "gshare256k","gshare512k","gshare1024k","global_history256k","global_history512k","global_history1024k"