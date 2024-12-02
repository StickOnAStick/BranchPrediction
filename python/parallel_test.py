from test_parser import create_csv
from test_parser import display_graph
from recompiler import compile_all, compile_champsim_instance
from loguru import logger
from argparse import Namespace
from size_test import merge_json

import subprocess
import os
import time
import sys
import threading
# import psutil
import json
import pathlib
import argparse

"""
What I want for this file: 
 Run a command line with different predictors, if that predictor does not exist, 
 generate the executable, if it does already exist do not generate the executable
 
 TODO:  Some way to figure out if the executable is up to date, I could just try 
        using the make, becuase once the json is created we can just do the make 
"""

MAIN_PATH           = pathlib.Path(__file__).parent.parent.resolve()
LOG_PATH            = MAIN_PATH.joinpath("python/Test_logs")
CHAMPSIM_EXE_PATH   = MAIN_PATH.joinpath("ChampSim/bin")
TRACER_PATH         = MAIN_PATH.joinpath("ChampSim/tracer") # Tracer tests 
PREDICTOR_PATH      = MAIN_PATH.joinpath("ChampSim/branch") # Predictors

print(MAIN_PATH)
print(LOG_PATH)
assert LOG_PATH.is_dir()
assert CHAMPSIM_EXE_PATH.is_dir()
assert TRACER_PATH.is_dir()
assert PREDICTOR_PATH.is_dir()

printout = 1
warmup_instructions = 0
simulated_instructions = 500000

run_predictors: list[str] = []
recompile_list: list[str] = []
predictor_list: list[str] = os.listdir(PREDICTOR_PATH)
logger.debug(f"Predictor list: {predictor_list}")
# print(predictor_list)
# Take command line arguments 
args = len(sys.argv)

recompile = False
print("\n\n------------ChampSim Parallel Test Launcher----------")

def main():
    global recompile
    # Parse and deal with input argv's
    args: Namespace = parse_args()
    config_setup(args=args)
    print("yeet")
    if recompile:
        logger.info(f"Recompiling the following predictors: {recompile_list}")
        size = -1
        print("size=" + size)
        compile_all(recompile_list, size)

    check_missing(run_predictors)
    logger.info(f"Running the following predictors: {run_predictors}")
     # find all of the files in the tracer folder, then copy the names into tracelist 
    file_list = os.listdir(TRACER_PATH)

    tracelist = []
    for i in file_list:
        if (i.find('.xz') != -1): # filter out only tracer files 
            tracelist.append(i)
    run_instructions(tracelist=tracelist, predictors=run_predictors)

    merge_json(run_predictors)

    create_csv()

    if (len(run_predictors) > 0):
        display_graph(run_predictors)


def parse_args():
    parser = argparse.ArgumentParser(description="Claros CLI parser")

     # Define arguments with their respective options
    parser.add_argument('--warmup_instructions', type=int, help='Number of warmup instructions to run')
    parser.add_argument('--simulation_instructions', type=int, help='Number of total instructions to run')
    parser.add_argument('--all', action='store_true', help='Compile and run all available predictors')
    parser.add_argument('--predictors', nargs='+', help='List of predictors to run')
    parser.add_argument('--recompile', nargs='+', help='List of predictors to recompile')
    parser.add_argument('--log_level', type=int, help="Set the log level for your session. 0 == info only, 1 == debug")

    return parser.parse_args()

def config_setup(args: Namespace) -> None:
    """Function to config your champsim run"""
    global warmup_instructions, simulated_instructions, recompile, run_predictors

    args = parse_args()
        
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
        print(recompile_list)
        if "all" in args.recompile:
            recompile_list = predictor_list
        else:
            for predictor in args.predictors:
                if predictor in recompile_list:
                    recompile_list.append(predictor)
                else:
                    logger.error(f"Recompile {predictor} not found in recompile list!")
                    SystemError(f"Predictor not found for recompilation {predictor}")
        recompile = True

    if args.all: # Leave this last to prevent overwrites
        recompile = True
        run_predictors = predictor_list
        recompile_list = predictor_list
    
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
                        "--json", str(LOG_PATH) + "/("  + predictor + ")" + trace + ".json",
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

# from https://stackoverflow.com/questions/30686295/how-do-i-run-multiple-subprocesses-in-parallel-and-wait-for-them-to-finish-in-py

# Create a thread for each list of tests, the argument is a list of instructions 
def create_test(instruction_list):
    for i in instruction_list:
        thread = threading.Thread(target = run_command , args = [i])
        thread.start()

    for _ in instruction_list:
        thread.join()

def run_command(cmd):
    with open(os.devnull, 'w') as ignore:
        p = subprocess.run(cmd, shell=False, stdout=ignore)

# check if all of the tests the user requested are compiled 
def check_missing(comp_list):
    print(comp_list)
    compiled_execs = os.listdir(CHAMPSIM_EXE_PATH)
    for predictor in comp_list:
        if ("champsim_" + predictor) not in compiled_execs:
            compile_champsim_instance(predictor,-1)

# def memchecker(pids,log):
#     """ DEPRECATED """
#     time.sleep(10)
#     for p in pids:
#         a = psutil.Process(p.pid)
#         for i in a.children():
#             print ("PID:" + str(i.pid))
#             print("Memory amount: " + str((i.memory_info().rss/(1024*1024))) + "MB")
#             with open(log,'w') as data_log:
#                 data_log.write("Memory Info: (" + p.args + "|" + str((i.memory_info().rss/(1024*1024))) + "MB )")  


if __name__ == "__main__":
    main()