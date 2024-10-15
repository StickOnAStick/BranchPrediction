import pandas as pd
import numpy as np
import datetime

params = ("Test",
        "IPC",
        "Instructions",
        "Cycles",
        "Branch Prediction Accuracy",
        "MPKI",
        "Avg ROB occupancy at mispredict",
        "Branch indirect Jump",
        "Branch Indirect",
        "Branch Conditional",
        "Branch Direct Call",
        "Branch Indirect Call",
        "Branch_Return",
        "Test Length",
        "Memory Usage")
data = pd.DataFrame(columns=params)

output = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

# parses the relavant part of the output for branch prediction 
def Subparse(string,log_text):
    # ChampSim/tracer/600.perlbench_s-210B.champsimtrace.xz


    start = string.find("tracer/") + len("tracer/")
    stop = string.find(".champsimtrace.xz")
    output[0] = string[start:stop]

    start = string.find("CPU 0 cumulative IPC: ") + len("CPU 0 cumulative IPC:")
    stop = string.find(" instructions: ",start)
    output[1] = float(string[start:stop])

    start = stop + len(" instructions: ")
    stop = string.find("cycles:",start)
    output[2] = float(string[start:stop])

    start = stop + len("cycles:")
    stop = string.find("CPU 0 Branch Prediction Accuracy:",start)
    output[3] = float(string[start:stop])

    start = stop + len("CPU 0 Branch Prediction Accuracy:")
    stop = string.find("% MPKI: ",start)
    output[4] = float(string[start:stop])

    start = stop + len("% MPKI: ")
    stop = string.find(" Average ROB Occupancy at Mispredict: ",start)
    output[5] = float(string[start:stop])

    start = stop + len(" Average ROB Occupancy at Mispredict: ")
    stop = string.find("Branch type MPKI",start)
    output[6] = float(string[start:stop])

    start = string.find("BRANCH_DIRECT_JUMP:") + len("BRANCH_DIRECT_JUMP:")
    stop = string.find("BRANCH_INDIRECT:",start)
    output[7] = float(string[start:stop])

    start = stop + len("BRANCH_INDIRECT:")
    stop = string.find("BRANCH_CONDITIONAL:",start)
    output[8] = float(string[start:stop])

    start = stop + len("BRANCH_CONDITIONAL:")
    stop = string.find("BRANCH_DIRECT_CALL:",start)
    output[9] = float(string[start:stop])

    start = stop + len("BRANCH_DIRECT_CALL:")
    stop = string.find("BRANCH_INDIRECT_CALL:",start)
    output[10] = float(string[start:stop])

    start = stop + len("BRANCH_INDIRECT_CALL:")
    stop = string.find("BRANCH_RETURN:",start)
    output[11] = float(string[start:stop])

    start = stop + len("BRANCH_RETURN:")
    output[12] = float(string[start:len(string)])

    start = string.find("(Simulation time: ") + len("(Simulation time: ")
    stop = string.find(")",start)
    output[13] = string[start:stop]

    start = log_text.find(output[0])
    start = log_text.find(output[0],start + len(output[0]))  + len(".champsimtrace.xz|") + len(output[0])
    stop = log_text.find(")",start)
    output[14] = log_text[start:stop]

    append_data = pd.DataFrame(list([output]),columns=params)
    # print(append_data)
    return append_data

# find the relavent text blocks in the champsim_log output 
# parse the individual components of the text block into a dataframe
# concatenate the tests together to get one dataframe of tests
testlog = open('Champsim_log.txt','r')
log_text = testlog.read()
test_start = 0
test_end = 0
test_it = 0
while (test_end != -1):
    test_it =+ 1
    test_start = log_text.find("Simulation complete",test_end)
    test_end = log_text.find("LLC TOTAL",test_start)
    if (test_start == -1 or test_end == -1):
        break
    else:
        temp_string = log_text[test_start:test_end]
        append_data = Subparse(temp_string,log_text)
        data = pd.concat([data,append_data])
print(data)

# find the name of the branch predictor from the json, the csv file will be named after it 
file = open('ChampSim/champsim_config.json',"r")
file = file.read()
start = file.find("branch_predictor") + len("branch_predictor: ")  + 1
end = file.find(",", start)
predictor_name = file[start+1:end-1] # we remove the following and tailing "
data.to_csv("Trace_tests/" + predictor_name +".csv")




# This is the section of the program that graphs the data 
import matplotlib.pyplot as plt
import os

# Find the CSV logs 
# then add them to the test if they have unique names 
file_list = os.listdir("Trace_tests")
csvlist = []
for i in file_list:
    if (i.find('.csv') != -1): # filter out only tracer files 
        csvlist.append(i)

# initialization data for the plot 
fig,ax = plt.subplots(figsize =(16, 9))
names = data["Test"]
branch_csvs = []
barwidth = 1/(len(csvlist)+1)
count = 0

# todo, this code looks awful please rewrite if showing anyone else
for i in csvlist:
    
    branch_csvs = pd.read_csv("Trace_tests/" + i)
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


# label axis
plt.xlabel('Trace Benchmarks', fontweight ='bold', fontsize = 15) 
plt.ylabel('Branch Prediction Accuracy', fontweight ='bold', fontsize = 15) 

# Add Text watermark
fig.text(0.125, 0.875, 'Project Claros', fontsize = 12,
         color ='grey', ha ='left', va ='top',
         alpha = 0.7)

# Create appropriate X axis labels 
plt.xticks([r+barwidth for r in range(len(branch_csvs))],data["Test"])

plt.legend()
plt.show()


a = 2

