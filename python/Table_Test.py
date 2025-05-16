from test_parser import create_csv, display_graph, display_size_graph, display_table_graph
from table_recompiler import compile_champsim_instance, generate_valid_hyperparams
from loguru import logger
from argparse import Namespace
from collections import defaultdict

import sys
import os
import subprocess
import threading
import json
import pathlib
import argparse


MAIN_PATH           = pathlib.Path(__file__).parent.parent.resolve()
CSV_PATH            = MAIN_PATH.joinpath("python/Trace_tests/")
LOG_PATH            = MAIN_PATH.joinpath("python/Test_logs/")
CHAMPSIM_EXE_PATH   = MAIN_PATH.joinpath("ChampSim/bin/")
TRACER_PATH         = MAIN_PATH.joinpath("ChampSim/tracer") # Tracer tests 
PREDICTOR_PATH      = MAIN_PATH.joinpath("ChampSim/branch") # Predictors

# assert LOG_PATH.is_dir()
# assert CHAMPSIM_EXE_PATH.is_dir()
# assert TRACER_PATH.is_dir()
# assert PREDICTOR_PATH.is_dir()

printout = 1
tables = 0
bits = 0
table_size = 0
warmup_instructions = 10000
simulated_instructions = 50000

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
        threads = []
        for predictor in run_predictors:
            valid_parameters = generate_valid_hyperparams(tables, 1024, table_size, bits)
            for parameter_test in valid_parameters:
                print(f"{predictor} {parameter_test}")
                # Each parameter_test is a tuple: (table, local_size, bits)
                thread = threading.Thread(target=compile_champsim_instance, args=(predictor, parameter_test))
                thread.start()
                threads.append(thread)
        # Wait for all threads to complete.
        for thread in threads:
            thread.join()

    # check_missing(run_predictors)

    # find all of the files in the tracer folder, then copy the names into tracelist 
    file_list = os.listdir(TRACER_PATH)

    tracelist = []
    for i in file_list:
        if (i.find('.xz') != -1): # filter out only tracer files 
            tracelist.append(i)

    run_predictor_params = []
    for predictor in run_predictors:
        valid_paramiters = generate_valid_hyperparams(tables, 1024, table_size, bits)
        for parameter_test in valid_paramiters:
            run_predictor_params.append(predictor + "_" + str(parameter_test[0]) + "_" + str(parameter_test[1]) + "_" + str(parameter_test[2]))
        logger.info(f"Running the following predictors: {run_predictor_params}")
        print(run_predictor_params)
        run_instructions(tracelist=tracelist, predictors=run_predictor_params)

    merge_json(run_predictor_params)

    create_csv()

    if (len(run_predictors) > 0):
        display_table_graph(CSV_PATH)


        
def parse_args():
    parser = argparse.ArgumentParser(description="Claros CLI parser")

     # Define arguments with their respective options
    parser.add_argument('--warmup_instructions', type=int, help='Number of warmup instructions to run')
    parser.add_argument('--simulation_instructions', type=int, help='Number of total instructions to run')
    parser.add_argument('--predictors', nargs='+', help='List of predictors to run')
    parser.add_argument('--recompile', type=bool, help='recompile')
    parser.add_argument('--log_level', type=int, help="Set the log level for your session. 0 == info only, 1 == debug")
    parser.add_argument('--tables', type=int, help='number of local tables in the attention mechanism')
    parser.add_argument('--bits', type=int, help='max size for an entry in a table')
    parser.add_argument('--table_size', type=int, help='max number of entries for a table')

    return parser.parse_args()

def config_setup(args: Namespace) -> None:
    global warmup_instructions, simulated_instructions, recompile, run_predictors, tables, bits, table_size, recompile_list

    args = parse_args()

    if args.tables:
        try:
            int(args.tables)
            print(tables)
        except ValueError:
            logger.error("Wrong type of value passed into --tables")
        tables = int(args.tables)
        print(tables)

    if args.bits:
        try:
            int(args.bits)
            print(bits)
        except ValueError:
            logger.error("Wrong type of value passed into --bits")
        bits = int(args.bits)
        print(bits)

    if args.table_size:
        try:
            int(args.table_size)
            print(table_size)
        except ValueError:
            logger.error("Wrong type of value passed into --table_size")
        table_size = int(args.table_size)
        print(table_size)
    
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

    recompile = args.recompile
                     
def run_instructions(tracelist: list[str], predictors: list[str]) -> None:
    global CHAMPSIM_EXE_PATH, TRACER_PATH
    threads = []

    # Create and start all threads first
    for predictor in predictors:
        print("Creating thread for: " + predictor)
        instruction_list = []
        for trace in tracelist:
            instruction = (
                str(CHAMPSIM_EXE_PATH) + "/champsim_" + predictor,
                "--warmup-instructions", str(warmup_instructions),
                "--simulation-instructions", str(simulated_instructions),
                "--json", str(LOG_PATH) + "/(" + predictor + ")" + trace + ".json",
                str(TRACER_PATH) + "/" + trace
            )
            instruction_list.append(instruction)
            logger.debug(instruction)

        # Create a thread for each predictor
        t = threading.Thread(target=create_test, args=(instruction_list,))
        threads.append(t)
        t.start()

    # Ensure all threads join before continuing
    for t in threads:
        t.join()
    #print("All threads are finished" )

# check if all of the tests the user requested are compiled 
def check_missing(comp_list):
    print(comp_list)
    compiled_execs = os.listdir(CHAMPSIM_EXE_PATH)
    for predictor in comp_list:
        compile_missing(compiled_execs,predictor)
        
def compile_missing(compiled_execs,predictor):
    
    valid_sizes = find_itt_ammount(predictor,size)
    print(valid_sizes)
    for valid_size in valid_sizes:
        if ("champsim_" + predictor + "_size-" + str(valid_size[0]) + "bits") not in compiled_execs:
            compile_champsim_instance(predictor,valid_size)

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
    size_independent_predictors = []
    
    for predictor in predictors:
        if predictor.find("_size") != -1:
            size_independent_predictors.append(predictor[:predictor.find("_size")])
        else:
            size_independent_predictors.append(predictor)
    
    size_independent_predictors = set(size_independent_predictors)

    for predictor in size_independent_predictors:
        # Find which json test files to merge into one predictor json file 
        merge_list = []
        for json_file in json_list:
            tempstring = "("  + predictor + ")"
            if json_file.find(tempstring, 0) != -1:
                merge_list.append(json_file)
        
        data = []
        total_accuracy = 0
        count = 0

        for tracer_test in range(len(merge_list)): 
            # Append the data from each item in merge list into one json data structure  
            with open(str(LOG_PATH) + "/" + merge_list[tracer_test], "r") as fromfile:
                data2 = json.load(fromfile)  # Load the test file we are merging from
                
                # Extract and store predictor size if applicable
                start = fromfile.name.find("_size-") + len("_size-")
                end = fromfile.name.find("bits")
                if start != -1 and end != -1:
                    size = fromfile.name[start:end]
                    data2[0]['traces'].append(size)

                # Sum up Branch Prediction Accuracy
                for core in data2[0]["sim"]["cores"]:
                    total_accuracy += core["Branch Prediction Accuracy"]
                    count += 1

                data.append(data2[0])  # Append that data to the data object
                os.remove(str(LOG_PATH) + "/" + merge_list[tracer_test])

        # Calculate and print the average branch prediction accuracy for this predictor
        avg_accuracy = (total_accuracy / count) if count > 0 else 0
        print(f"Predictor: {predictor}, Average Branch Prediction Accuracy: {avg_accuracy:.2f}%")

        # Open the json file with the name of the predictor, and write the merged data
        with open(str(LOG_PATH) + "/" + predictor + ".json", "w+") as tofile:
            tofile.seek(0)
            json.dump(data, tofile, indent=4)
            tofile.truncate()
            
if __name__ == "__main__":
    main()