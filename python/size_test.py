from test_parser import create_csv, display_graph, display_size_graph
from recompiler import compile_all, compile_champsim_instance, find_2_pow, find_itt_ammount
from loguru import logger
from argparse import Namespace

import sys
import os
import subprocess
import threading
import json
import pathlib
import argparse


MAIN_PATH           = pathlib.Path(__file__).parent.parent.resolve()
LOG_PATH            = MAIN_PATH.joinpath("python/Test_logs/")
CHAMPSIM_EXE_PATH   = MAIN_PATH.joinpath("ChampSim/bin/")
TRACER_PATH         = MAIN_PATH.joinpath("ChampSim/tracer") # Tracer tests 
PREDICTOR_PATH      = MAIN_PATH.joinpath("ChampSim/branch") # Predictors

assert LOG_PATH.is_dir()
assert CHAMPSIM_EXE_PATH.is_dir()
assert TRACER_PATH.is_dir()
assert PREDICTOR_PATH.is_dir()

printout = 1
size = 1
warmup_instructions = 1000000
simulated_instructions = 5000000

run_predictors: list[str] = []
recompile_list: list[str] = []
predictor_list: list[str] = os.listdir(PREDICTOR_PATH)
logger.debug(f"Predictor list: {predictor_list}")

# print(predictor_list)
# Take command line arguments (for debugging)
args = len(sys.argv)
recompile = False

def main():
    global recompile
   
    args: Namespace = parse_args()
    config_setup(args=args)

    if recompile:
        print("Recompiling the following predictors:")
        print(recompile_list)
        compile_all(recompile_list,size) # use -1 if we don't want to change the size

    check_missing(run_predictors)

    # find all of the files in the tracer folder, then copy the names into tracelist 
    file_list = os.listdir(TRACER_PATH)

    tracelist = []
    for i in file_list:
        if (i.find('.xz') != -1): # filter out only tracer files 
            tracelist.append(i)

    run_predictor_sizes = []
    for predictor in run_predictors:
        valid_sizes = find_itt_ammount(predictor,size)
        for valid_size in valid_sizes:
            run_predictor_sizes.append(predictor + "_size-" + str(valid_size[0]) + "bits")
    logger.info(f"Running the following predictors: {run_predictor_sizes}")
    run_instructions(tracelist=tracelist, predictors=run_predictor_sizes)

    merge_json(run_predictor_sizes)

    for i in run_predictor_sizes:
        create_csv(str(LOG_PATH) + "/" + i+".json")

    if (len(run_predictors) > 0):
        display_size_graph(run_predictor_sizes,size)

        
def parse_args():
    parser = argparse.ArgumentParser(description="Claros CLI parser")

     # Define arguments with their respective options
    parser.add_argument('--warmup_instructions', type=int, help='Number of warmup instructions to run')
    parser.add_argument('--simulation_instructions', type=int, help='Number of total instructions to run')
    parser.add_argument('--predictors', nargs='+', help='List of predictors to run')
    parser.add_argument('--recompile', nargs='+', help='List of predictors to recompile')
    parser.add_argument('--log_level', type=int, help="Set the log level for your session. 0 == info only, 1 == debug")
    parser.add_argument('--size', type=int, help='run test for predictors up to this size in Kilobits')

    return parser.parse_args()

def config_setup(args: Namespace) -> None:
    global warmup_instructions, simulated_instructions, recompile, run_predictors, size, recompile_list

    args = parse_args()

    if args.size:
        try:
            int(args.size)
            print(size)
        except ValueError:
            logger.error("Wrong type of value passed into --size")
        size = int(args.size)
        print(size)
    
    if args.warmup_instructions:
        try:
            int(args.warmup_instructions)
        except ValueError:
            logger.error("Wrong type of value passed into warmup_instructions!")
        warmup_instructions = int(args.warmup_instructions)

    if args.simulation_instructions:
        try:
            int(args.simulation_instructions)
        except ValueError:
            logger.error("Wrong type of value passed into --simulation_instructions")
        simulated_instructions = int(args.simulation_instructions)

    if args.predictors:
        if "all" in args.predictors:
            run_predictors = predictor_list
        else:
            for predictor in args.predictors:             
                if predictor in predictor_list:
                    run_predictors.append(predictor)
                else:
                    logger.error(f"Predictor {predictor} not found in predictor list!")
                    SystemError(f"Predictor not found {predictor}")

    if args.recompile:
        if "all" in args.recompile:
            recompile_list = predictor_list
        else:
            for predictor in args.recompile:
                if predictor in predictor_list:
                    recompile_list.append(predictor)
                else:
                    logger.error(f"Recompile {predictor} not found in recompile list!")
                    SystemError(f"Predictor not found for recompilation {predictor}")
        recompile = True  
                     
def run_instructions(tracelist: list[str], predictors: list[str]) -> None:
    global CHAMPSIM_EXE_PATH, TRACER_PATH
    threads = []
    for predictor in predictors:
        print ("Creating thread for:" + predictor)
        instruction_list = []
        for trace in tracelist:
            instruction = (str(CHAMPSIM_EXE_PATH) + "/champsim_" + predictor,
                        "--warmup-instructions", str(warmup_instructions),
                        "--simulation-instructions"  , str(simulated_instructions),
                        "--json", str(LOG_PATH) + "/"  + predictor + trace + ".json",
                         str(TRACER_PATH) + "/" + trace )
            instruction_list.append(instruction)   
            logger.debug(instruction)  

        # Create a new thread for a single predictor with multiple instructions.
        t = threading.Thread(target = create_test , args = [instruction_list])
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    #print("All threads are finished" )

# check if all of the tests the user requested are compiled 
def check_missing(comp_list):
    print(comp_list)
    compiled_execs = os.listdir(CHAMPSIM_EXE_PATH)
    for predictor in comp_list:
        compile_missing(compiled_execs,predictor)

    # Tried threading each predictor, make was upset and didn't work
    #     thread = threading.Thread(target = compile_missing, args = [compiled_execs,predictor])
    #     thread.start()

    # for _ in comp_list:
    #     thread.join()
        
def compile_missing(compiled_execs,predictor):
    
    valid_sizes = find_itt_ammount(predictor,size)
    print(valid_sizes)
    for valid_size in valid_sizes:
        if ("champsim_" + predictor + "_size-" + str(valid_size[0]) + "bits") not in compiled_execs:
            compile_champsim_instance(predictor,valid_size)

# compile the missing executables
# def compile_missing(comp_list: list[str]) -> list[str]: 
#     # the following section is a cognito-hazard, I do not recommend looking at it if you wish to retain your sanity 
#     # there is a better version of this code in the test_parser
#     for i in comp_list:
#         tempsize = []
#         for j in reversed(i): # traverse the name of the instance to compile from the back
#             if j == "k":  # ignore the first k
#                 continue 
#             else:
#                 try: 
#                     tempsize.insert(0,int(j)) # insert each element into the tempsize variable, the try accept structure causes a break if int(j) cannot find any more ints 
#                 except:
#                     break
#         i = i[0:len(i)-(len(tempsize)+1)] # remove the size of the predictor from the name
#         int_result = find_2_pow(int(''.join(map(str, tempsize)))) # cursed way to join lists of ints into one int 
#         #print(i)
#         compile_champsim_instance(i,int_result-1) # compile the predictor i with our joined integer list 

def create_test(instruction_list):
    for i in instruction_list:
        thread = threading.Thread(target = run_command , args = [i])
        thread.start()

    for _ in instruction_list:
        thread.join()
            
def run_command(cmd):
    with open(os.devnull, 'w') as ignore:
        p = subprocess.run(cmd, shell=False, stdout=ignore)

# merge the different individual json tests files generated by champsim, and create one json file for each predcitor that contains all of the test information 
def merge_json(predictors):
    json_list = os.listdir(LOG_PATH)
    for i in predictors:

        # Find which json test files to merge into one predictor json file 
        merge_list = []
        for j in json_list:
            # print(j[:len(j)-5] + "|" + i)
            if (j[:len(j)-5] == i): # check if the file names are the same - .json file tag
                pass # print("already exists \n \n ")
            elif(j.startswith(i)): # check if the item in json list starts with the predictor name 
                merge_list.append(j) # add them to list of items to merge into one .json file
        data = []
        for j in range(0,len(merge_list)): 
            # append the data from the from each item in merge list into one json data structure  
            with open(str(LOG_PATH)+ "/" +merge_list[j],"r") as file2:
                    data2 = json.load(file2) # load the test file we are merging from 
                    data.append(data2[0]) # append that data to the data object
                    file2.close() # close the test file 

        # open the json file with the name of the predictor, we will write our new data structure to this file 
        with open(str(LOG_PATH)+ "/"+i+".json","w+") as file1:
            try: 
                len(json.load(file1)) > len(predictors)
            except:
                pass # print(len(data))
            # save the json data to the new file and close 
            file1.seek(0)
            json.dump(data, file1, indent=4)
            file1.truncate()
            file1.close()
main()