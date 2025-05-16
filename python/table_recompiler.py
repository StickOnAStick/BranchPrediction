import threading
import json
import subprocess
import os
import pathlib
import math

# Global paths
MAIN_PATH           = pathlib.Path(__file__).parent.parent.resolve()
LOG_PATH            = MAIN_PATH.joinpath("python/Test_logs")
CHAMPSIM_EXE_PATH   = MAIN_PATH.joinpath("ChampSim/bin/")
TRACER_PATH         = MAIN_PATH.joinpath("ChampSim/tracer")  # Tracer tests 
PREDICTOR_PATH      = MAIN_PATH.joinpath("ChampSim/branch")    # Predictors
CONFIG_PATH         = MAIN_PATH.joinpath("python/Test_configs")

assert LOG_PATH.is_dir()
assert CHAMPSIM_EXE_PATH.is_dir()
assert TRACER_PATH.is_dir()
assert PREDICTOR_PATH.is_dir()

tage_tables = 0
min_size = 32000
min_local_size = 64
min_bits = 1


# Global mutex to protect file modifications and compilation.
compile_lock = threading.Lock()

# this is literally copy and pasted from gemini but it works 
def replace_from_position(string, old, new, position):
    # Replaces a substring in a string starting from a specific position
    return string[:position] + string[position:].replace(old, new, 1)

from itertools import product

def generate_valid_hyperparams(table, min_size, max_size, bits):
    """
    Generate all valid hyperparameter combinations.
    
    Parameters:
        table (int): Maximum value for the table parameter (iterates from 0 to table).
        min_size (int): Minimum value for the size parameter (starting value for powers of 2).
        max_size (int): Maximum value for the size parameter (upper limit for powers of 2).
        bits (int): Maximum value for the bits parameter.
        
    Returns:
        list of tuples: Each tuple contains a valid combination (table_value, size_value, bits_value).
    """
    hyperparams = []
    t = table
    s = min_size
    while s <= max_size:
        for b in range(2, bits + 1,2): 
            hyperparams.append((t, s, b))
        s *= 2  # Iterate in powers of 2 starting from min_size
    return hyperparams


def compile_champsim_instance(*args):
    # Acquire the mutex to ensure thread safety for file editing and compilation.
    with compile_lock:
        predictor = args[0]
        table = args[1][0]
        local_size = args[1][1]
        bits = args[1][2]
        print("Compiling Predictor: " + predictor + " table index: " + str(table) + " local size:" + str(local_size)+ " bits:" + str(bits))
        
        # Update the predictor C file.
        predictor_file = PREDICTOR_PATH.joinpath(predictor, predictor + ".cc")
        with open(predictor_file, 'r+') as c_file:
            c_code = c_file.read()
            table_marker = "NUM_LOCAL_HISTORY_SCALES = "
            start = c_code.find(table_marker) + len(table_marker)
            end = c_code.find(";", start)
            num_tables = int(c_code[start:end])
            
            # Update LOCAL_HISTORY_TABLE_SIZES at the specified index.
            sizes_marker = "LOCAL_HISTORY_TABLE_SIZES = {"
            # start = c_code.find(sizes_marker) + len(sizes_marker)
            # end = c_code.find("};",start)
            # min_str = ",".join([str(min_local_size)] * num_tables)
            # c_code = replace_from_position(c_code, c_code[start:end], str(min_str), start)
            start = c_code.find(sizes_marker) + len(sizes_marker)
            for i in range(0, table):
                start = c_code.find(",", start) + 1
            end = c_code.find(",", start)
            c_code = replace_from_position(c_code, c_code[start:end], str(local_size), start)
            
            # Update LOCAL_HISTORY_TABLE_BITS at the specified index.
            bits_marker = "LOCAL_HISTORY_TABLE_BITS = {"
            # start = c_code.find(bits_marker) + len(bits_marker)
            # end = c_code.find("};",start)
            # min_str = ",".join([str(min_bits)] * num_tables)
            # c_code = replace_from_position(c_code, c_code[start:end], str(min_str), start)
            start = c_code.find(bits_marker) + len(bits_marker)
            for i in range(0, table):
                start = c_code.find(",", start) + 1
            end = c_code.find(",", start)
            c_code = replace_from_position(c_code, c_code[start:end], str(bits), start)
            c_file.seek(0)
            c_file.write(c_code)
            c_file.truncate()
        
        # Update the configuration JSON file.
        config_json_path = MAIN_PATH.joinpath("ChampSim/champsim_config.json")
        with open(config_json_path, 'r') as file:
            data = json.load(file)
            # Create our own config.
            config_path = str(CONFIG_PATH.joinpath(predictor + "_config.json"))
            with open(config_path, 'w') as config_file:
                data['ooo_cpu'][0]['branch_predictor'] = predictor  # Change the branch predictor.
                data['executable_name'] = "champsim_" + predictor + '_' + str(table) + '_' + str(local_size) + '_' + str(bits)
                config_file.seek(0)
                json.dump(data, config_file, indent=4)
                config_file.truncate()
        
        # Compile the code.
        try:
            print("Using config file: " + config_path)
            print("Compiling...")
            os.chdir(MAIN_PATH.joinpath("ChampSim"))
            subprocess.run(["./config.sh", config_path])
            subprocess.run(["make", "-j", "-s"], check=True)
            os.chdir(MAIN_PATH)
        except subprocess.CalledProcessError as e:
            print(f"Error running make: {e}")
