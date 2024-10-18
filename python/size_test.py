from test_parser import create_csv, display_graph, display_size_graph
from recompiler import compile_all, compile_champsim_instance, find_2_pow, delete_make
import sys
import os
import subprocess
import threading
import time
import json
import pathlib


MAIN_PATH           = pathlib.Path(__file__).parent.parent.resolve()
LOG_PATH            = MAIN_PATH.joinpath("python/Test_logs/")
CHAMPSIM_EXE_PATH   = MAIN_PATH.joinpath("ChampSim/bin/")
TRACER_PATH         = MAIN_PATH.joinpath("ChampSim/tracer") # Tracer tests 
PREDICTOR_PATH      = MAIN_PATH.joinpath("ChampSim/branch") # Predictors

assert LOG_PATH.is_dir()
assert CHAMPSIM_EXE_PATH.is_dir()
assert TRACER_PATH.is_dir()
assert PREDICTOR_PATH.is_dir()

global warmup_instructions  
warmup_instructions = 20000
global simulated_instructions 
simulated_instructions = 100000
args = len(sys.argv)


# check if all of the tests the user requested are compiled 
def check_missing(comp_list):
    compiled_execs = os.listdir(CHAMPSIM_EXE_PATH)
    execs_to_compile = []

    found = False
    for i in comp_list:
        for j in compiled_execs:
            # print(("champsim_"+i)  + " |"+ j + "|" + str(found))
            if (("champsim_"+i) == j): # search for existing compiled instances
                found = True # if we find the instance already exists we can break
                break
        if (found == False): # if we didn't find an existing predictor we added to the list of predictors to be compiled 
            # print(i)
            execs_to_compile.append(i)
        found = False # reset the found variable 
    return execs_to_compile

# compile the missing executables
def compile_missing(comp_list: list[str]) -> list[str]: 
    # the following section is a cognito-hazard, I do not recommend looking at it if you wish to retain your sanity 
    for i in comp_list:
        tempsize = []
        for j in reversed(i): # traverse the name of the instance to compile from the back
            if j == "k":  # ignore the first k
                continue 
            else:
                try: 
                    tempsize.insert(0,int(j)) # insert each element into the tempsize variable, the try accept structure causes a break if int(j) cannot find any more ints 
                except:
                    break
        i = i[0:len(i)-(len(tempsize)+1)] # remove the size of the predictor from the name
        int_result = find_2_pow(int(''.join(map(str, tempsize)))) # cursed way to join lists of ints into one int 
        #print(i)
        compile_champsim_instance(i,int_result-1) # compile the predictor i with our joined integer list 

def create_test(instruction_list):
    with open(os.devnull, 'w') as ignore:
        procs = [subprocess.Popen([i], shell=True, stdout=ignore) for i in instruction_list]
        for p in procs:
            p.wait()

def merge_json(predictors):
    json_list = os.listdir(LOG_PATH)
    for i in predictors:
        # print(i)
        merge_list = []
        for j in json_list:
            # print(j[:len(j)-5] + "|" + i)
            if (j[:len(j)-5] == i):
                pass # print("already exists \n \n ")
            elif(j.startswith(i)):
                merge_list.append(j)
        # print(merge_list)
        data = []
        for j in range(0,len(merge_list)):
            # print(str(LOG_PATH)+ "/"+merge_list[j])
            with open(str(LOG_PATH)+ "/" +merge_list[j],"r") as file2:
                    data2 = json.load(file2)
                    data.append(data2[0])
                    file2.close()
        with open(str(LOG_PATH)+ "/"+i+".json","w+") as file1:
            try: 
                len(json.load(file1)) > len(predictors)
            except:
                pass # print(len(data))
            file1.seek(0)
            json.dump(data, file1, indent=4)
            file1.truncate()
            file1.close()

# clean the 
def clear():
    a = 2

def main():

    print(os.getcwd())
    # delete_make()
    # subprocess.run(["make","configclean"], check=True)

    
    run_predictors = []
    recompile_list = []
    predictor_list = os.listdir(PREDICTOR_PATH)

    print("use --help to see avaliable commands")

    count = 0
    size = 1
    recompile = False
    comp_check = False
    for i in sys.argv:
        count += 1
        if i == "--compcheck":
            comp_check = True
        if i == "--size":
            try:
                size = int(sys.argv[count])
            except:
                print("size needs to be a valid integer")
                exit()
        if i == "--recompile":
            for j in sys.argv[count:]:
                if j == "all":
                    recompile_list = predictor_list
                temp = len(recompile_list)
                for k in predictor_list:
                
                    if (j == k):
                        recompile_list.append(k)
                        break
                if temp == len(recompile_list):
                    break
            recompile = True
        if i == "--predictors":
            for j in sys.argv[count:]:
                power = 0
                if j == "all":
                    run_predictors = predictor_list
                    break
                temp = len(run_predictors)
                for k in predictor_list:
                    print(j + "|" + k)
                    if (j == k):
                        while pow(2,power) <= size:
                            run_predictors.append(k+str(pow(2,power))+"k")
                            power += 1
                        break
                if temp == len(run_predictors):
                    break

    

    if recompile:
        print("Recompiling the following predictors:")
        print(recompile_list)
        compile_all(recompile_list,size) # use -1 if we don't want to change the size


    print("Predictors to run:")
    print(run_predictors)
    missing = check_missing(run_predictors)

    if len(missing) != 0:
        compile_missing(missing)

    # # recompile errant executables(should be fast)
    # if  comp_check:
    #     compile_missing(run_predictors,1)
    # print(run_predictors)

    # find all of the files in the tracer folder, then copy the names into tracelist 
    file_list = os.listdir(TRACER_PATH)
    tracelist = []
    for i in file_list:
        if (i.find('.xz') != -1): # filter out only tracer files 
            tracelist.append(i)

    #print("Predictors to run:")
    #print(run_predictors)
    for i in run_predictors:
        # Create the list of instructions through concatenation
        instruction_list = []
        for j in tracelist:
            instruction = (str(CHAMPSIM_EXE_PATH) + "/champsim_" + i +
                        " --warmup-instructions " + str(warmup_instructions) +
                        " --simulation-instructions "  + str(simulated_instructions) + 
                        " --json " + str(LOG_PATH) + "/"  + i + j + ".json " + str(TRACER_PATH) + "/" + j )
            instruction_list.append(instruction)
        # print("Instruction list :")
        # print(instruction_list)
        thread = threading.Thread(target = create_test , args = [instruction_list])
        print ("Creating thread for:" + i )
        thread.start()
    for i in run_predictors:
        thread.join()

    # for some reason the files do not finish writing, even after they join
    time.sleep(5)
    
    merge_json(run_predictors)

    for i in run_predictors:
        create_csv(str(LOG_PATH) + "/" + i+".json")

    if (len(run_predictors) > 0):
        time.sleep(3)
        display_size_graph(run_predictors,size)

main()