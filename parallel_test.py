import subprocess
import os

printout = 1
warmup_instructions = 2000000
simulated_instructions = 5000000
path = 'ChampSim/bin/champsim'        # path for executable
tracer = 'ChampSim/tracer'            # path for tracer tests
output_file_name = 'Champsim_log.txt' # Output file name

# find all of the files in the tracer folder, then copy the names into tracelist 
file_list = os.listdir(tracer)
tracelist = []
for i in file_list:
    if (i.find('.xz') != -1): # filter out only tracer files 
        tracelist.append(i)

# print the traces to be run
if printout == True:
    print("The following tests will be run")
    print(tracelist)

# Create the instructions through concatonation 
instruction_list = []
for i in tracelist:
    instruction = (path + 
                  " --warmup-instructions " + str(warmup_instructions) +
                  " --simulation-instructions "  + str(simulated_instructions) + 
                  " " + tracer + "/" + i)
    instruction_list.append(instruction)

if printout == True:
    print("The following commands were constructed")
    print(instruction_list)

# from https://stackoverflow.com/questions/30686295/how-do-i-run-multiple-subprocesses-in-parallel-and-wait-for-them-to-finish-in-py

n = len(instruction_list) #Number of processess to be created
for j in range(max(int(len(instruction_list)/n), 1)):
    with open(output_file_name,'w') as test_log:
        procs = [subprocess.Popen(i, shell=True, stdout=test_log) for i in instruction_list[j*n: min((j+1)*n, len(instruction_list))] ]
        for p in procs:
            print("finished:" + p.args)
            p.wait()
