
from test_parser import create_csv, display_graph
from recompiler import compile_all
from loguru import logger
from argparse import Namespace

import subprocess
import os
import time
import sys
import threading
import psutil
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
LOG_PATH            = MAIN_PATH.joinpath("python/Test logs/champsim")
CHAMPSIM_EXE_PATH   = MAIN_PATH.joinpath("ChampSim/bin/champsim")
TRACER_PATH         = MAIN_PATH.joinpath("ChampSim/tracer") # Tracer tests 
PREDICTOR_PATH      = MAIN_PATH.joinpath("ChampSim/branch") # Predictors

assert LOG_PATH.is_dir()
assert CHAMPSIM_EXE_PATH.is_file()
assert TRACER_PATH.is_dir()
assert PREDICTOR_PATH.is_dir()

printout = 1
warmup_instructions = 200000
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

    if recompile:
        logger.info(f"Recompiling the following predictors: {recompile_list}")
        compile_all(recompile_list, -1)

    logger.info(f"Running the following predictors: {run_predictors}")
    tracelist: list[str] = [trace for trace in os.listdir(TRACER_PATH) if os.path.isdir(f"{TRACER_PATH}/{trace}")] # Select only top level directories.
    run_instructions(tracelist=tracelist, predictors=run_predictors)

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
    for predictor in predictors:
        instruction_list = []
        # Create the list of instructions through concatenation
        for trace in tracelist:
            base_command = [
                f"{str(CHAMPSIM_EXE_PATH)}_{predictor}",
                f"--warmup-instructions {str(warmup_instructions)}",
                f"--simulation-instructions {str(simulated_instructions)}", 
                f"{str(TRACER_PATH)}/{trace}"
            ]
            instruction = " ".join(base_command)      
            instruction_list.append(instruction)

        # Create a new thread for a single predictor with multiple instructions.
        thread = threading.Thread(target = create_test , args = [instruction_list,predictor]) 
        logger.info(f"Starting thread {thread} for predictor: {predictor}" )
        thread.start()

    for _ in run_predictors:
        thread.join()

# from https://stackoverflow.com/questions/30686295/how-do-i-run-multiple-subprocesses-in-parallel-and-wait-for-them-to-finish-in-py

# Create a thread for each list of tests, the argument is a list of instructions 
def create_test(instruction_list: list[str], predictor: str) -> None:
    logger.debug(f"CREATE TEST \nPREDICTOR: {predictor}\n Instruction list: {instruction_list}")
    log_name = str(LOG_PATH.joinpath(predictor.join("_log.txt"))) # I know this looks gross, but it's O(n) vs O(n^2)
    count = -1
    logger.debug(f"LOG NAME: {log_name}\t")

    n = len(instruction_list) #Number of processess to be created


    for j in range(n):
        with open(log_name,'w') as test_log:
            logger.debug("writing to: " + log_name)
            procs = [subprocess.Popen(i, shell=True, stdout=test_log) for i in instruction_list[j*n: min((j+1)*n, len(instruction_list))] ]
            #thread = threading.Thread(target = memchecker, args = [procs,log_name])
            #print("Starting Memchecker")
            #thread.start()
            for p in procs:
                if (count != -1):
                    logger.success(procs[count].args + "Has finished Computing")
                p.wait()
                count += 1
            print(procs[count].args + "Has finished Computing")
            test_log.close()
            
            # thread.join()
            create_csv(log_name)
            # print("exiting memchecker, " + i +"has finished ")

def memchecker(pids,log):
    """ DEPRECATED """
    time.sleep(10)
    for p in pids:
        a = psutil.Process(p.pid)
        for i in a.children():
            print ("PID:" + str(i.pid))
            print("Memory amount: " + str((i.memory_info().rss/(1024*1024))) + "MB")
            with open(log,'w') as data_log:
                data_log.write("Memory Info: (" + p.args + "|" + str((i.memory_info().rss/(1024*1024))) + "MB )")  


if __name__ == "__main__":
    main()