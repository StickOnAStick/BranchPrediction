import matplotlib
matplotlib.use("TkAgg")       # or "Qt5Agg" if you have PyQt5 installed
import matplotlib.pyplot as plt
print("Backend in use:", matplotlib.get_backend())
import pandas as pd
import numpy as np
from recompiler import find_2_pow
import warnings
import datetime
import os
import re
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
SPEED_PATH          = MAIN_PATH.joinpath("python/Speed_logs")
CHART_PATH          = MAIN_PATH.joinpath("python/Learning_charts")


# assert LOG_PATH.is_dir()
# assert CSV_PATH.is_dir()
# assert CHAMPSIM_EXE_PATH.is_dir()
# assert TRACER_PATH.is_dir()
# assert PREDICTOR_PATH.is_dir()
# assert SPEED_PATH.is_dir()


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


def display_size_graph(predictors, size):
    file_list = os.listdir(CSV_PATH)
    predictor_set = []
    predictor_list = [0, 0, 0]
    # create a list object for each csv file,
    # it contains the predictor type, predictor size, and average prediction accuracy for the tests
    for file in file_list:
        branch_csvs = pd.read_csv(str(CSV_PATH / file))
        size_set = set(branch_csvs["Size"])
        number_of_test_per_size = int(len(branch_csvs.index) / len(size_set))
        predictor_list[0] = file[:-len(".csv")]
        for size_val in size_set:
            predictor_list[1] = size_val
            predictor_list[2] = 0
            for i in range(0, len(branch_csvs.index)):
                if size_val == branch_csvs["Size"][i]:
                    predictor_list[2] += branch_csvs["Branch Prediction Accuracy"][i]
            predictor_list[2] = predictor_list[2] / number_of_test_per_size
            predictor_set.append(predictor_list[:])
    
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
        plt.xscale('log', base=2)
        plt.plot(x_axis, y_axis, label=ps)
    
    plt.legend()
    plt.ylabel("Prediction Accuracy")
    plt.xlabel("Predictor size (bits)")
    plt.show()
    input("Press Enter to close the size graph...")

def asort(val):
    return val[1]
    # input: list of names of the predictors you want graphed 
    # ALERT: this needs to be redone

def display_speed_graph(traces):
    file_list = os.listdir(str(SPEED_PATH))
    
    for file in file_list:
        if not any(trace in file for trace in traces):  # Only process files that match traces
            continue

        cycle_list = []
        accuracy_list = []
        
        with open(os.path.join(SPEED_PATH, file)) as speed_file:
            speed = speed_file.read()
            sim_finish = speed.find("Simulation finished CPU")
            end = 0

            while end < sim_finish or end == -1:
                begin = speed.find("Heartbeat CPU 0 instructions:", end) + len("Heartbeat CPU 0 instructions:")
                end = speed.find("cycles:", begin)

                if (end - begin) >= 50:
                    break
                cycle_list.append(int(speed[begin:end]))

                begin = speed.find("Prediction_Accuracy:", end) + len("Prediction_Accuracy:")
                end = speed.find("%", begin)

                if (end - begin) >= 50:
                    break
                accuracy_list.append(float(speed[begin:end]))

        x_axis = np.array(cycle_list)
        y_axis = np.array(accuracy_list)
        plt.plot(x_axis, y_axis, label=file)

    
    plt.legend()
    plt.ylabel("Prediction Accuracy")
    plt.xlabel("Instruction cycles")
    plt.show()


def create_learning_graph(trace,ittr):
    plt.ion()  # Enable interactive mode to avoid Tkinter errors
    file_list = os.listdir(str(SPEED_PATH))

    plt.figure(figsize=(10, 5))  # Adjust the figure size (Width=10, Height=5)
    for file in file_list:
        if trace in file:  # Ensure the file contains the trace name
            cycle_list = []
            accuracy_list = []

            with open(os.path.join(SPEED_PATH, file)) as speed_file:
                speed = speed_file.read()
                sim_finish = speed.find("Simulation finished CPU")
                end = 0

                while end < sim_finish or end == -1:
                    begin = speed.find("Heartbeat CPU 0 instructions:", end) + len("Heartbeat CPU 0 instructions:")
                    end = speed.find("cycles:", begin)

                    if (end - begin) >= 50:
                        break
                    cycle_list.append(int(speed[begin:end]))

                    begin = speed.find("Prediction_Accuracy:", end) + len("Prediction_Accuracy:")
                    end = speed.find("%", begin)

                    if (end - begin) >= 50:
                        break
                    accuracy_list.append(float(speed[begin:end]))

            x_axis = np.array(cycle_list)
            y_axis = np.array(accuracy_list)

            plt.plot(x_axis, y_axis, label=file)
    
   
    plt.legend()
    plt.ylabel("Prediction Accuracy")
    plt.xlabel("Instruction cycles")
    plt.savefig(os.path.join(CHART_PATH, f"{trace}.png"))

    plt.close("all")  # Ensure all figures are properly closed

def display_table_graph(csv_folder):
    # List all CSV files in the given folder
    file_list = os.listdir(csv_folder)
    csv_files = [f for f in file_list if f.endswith('.csv')]
    print("Found CSV Files:", csv_files)
    if not csv_files:
        print("No CSV files found in the folder.")
        return

    # Dictionary to store results grouped by table number.
    # results[table] is a dictionary where keys are (history_size, bits) and values are avg prediction accuracy.
    results = {}

    # Process each CSV file
    for filename in csv_files:
        # Expecting filenames like "Attention_0_128_2.csv"
        name_no_ext = filename.replace('.csv', '')
        parts = name_no_ext.split('_')
        if len(parts) < 4:
            print(f"Skipping {filename} (filename does not match expected pattern)")
            continue

        try:
            # Assume pattern: <prefix>_<table>_<local_history_size>_<bits>
            table = parts[-3]  # table number as string
            history_size = int(parts[-2])
            bits = int(parts[-1])
        except Exception as e:
            print(f"Error parsing {filename}: {e}")
            continue

        # Read CSV file
        full_path = os.path.join(csv_folder, filename)
        df = pd.read_csv(full_path)
        if "Branch Prediction Accuracy" not in df.columns:
            print(f"Warning: Skipping {filename} (Missing 'Branch Prediction Accuracy' column)")
            continue

        # Compute the average prediction accuracy from all tests in the CSV file
        avg_accuracy = df["Branch Prediction Accuracy"].mean()
        
        # Use a regular dict to group the results by table number
        if table not in results:
            results[table] = {}
        results[table][(history_size, bits)] = avg_accuracy

    # For each table number, build and display a heatmap
    for table, data in results.items():
        # Get all unique local history sizes (x axis) and bits (y axis)
        history_sizes = sorted(set(x for (x, y) in data.keys()))
        bits_values = sorted(set(y for (x, y) in data.keys()))
        
        # Initialize a matrix with NaNs to hold the average accuracy values
        heatmap_matrix = np.full((len(bits_values), len(history_sizes)), np.nan)
        
        # Fill the matrix: rows correspond to bits, columns to history_sizes
        for (h_size, bit), accuracy in data.items():
            x_index = history_sizes.index(h_size)
            y_index = bits_values.index(bit)
            heatmap_matrix[y_index, x_index] = accuracy

        # Create the heatmap figure
        fig, ax = plt.subplots(figsize=(8, 6))
        cax = ax.imshow(heatmap_matrix, aspect='auto', origin='lower', cmap='viridis')
        ax.set_title(f"Heatmap for Table {table}")
        ax.set_xlabel("Local History Table Size")
        ax.set_ylabel("Bits")
        
        # Set x and y ticks with the corresponding values
        ax.set_xticks(np.arange(len(history_sizes)))
        ax.set_xticklabels(history_sizes)
        ax.set_yticks(np.arange(len(bits_values)))
        ax.set_yticklabels(bits_values)
        
        # Add text annotations for each cell with a valid average accuracy value
        for i in range(heatmap_matrix.shape[0]):
            for j in range(heatmap_matrix.shape[1]):
                value = heatmap_matrix[i, j]
                if not np.isnan(value):
                    ax.text(j, i, f'{value:.2f}', ha='center', va='center', 
                            fontsize=8, color='white', 
                            bbox=dict(facecolor='black', edgecolor='none', alpha=0.7))
        
        # Add a colorbar to indicate average branch prediction accuracy
        fig.colorbar(cax, ax=ax, label='Average Branch Prediction Accuracy')
        plt.show()


def display_grid_search_graph(csv_folder):
    """
    Displays a heatmap for grid search results based on files with the pattern:
    Attention_<dropout>_<learning_rate>.csv

    The function reads the file to compute the average branch prediction accuracy, then builds
    a heatmap with learning rate on the x-axis and dropout on the y-axis.
    """
    file_list = os.listdir(csv_folder)

    # Match files like Attention_0.1_0.0001.csv
    pattern = re.compile(r'^Attention_(?P<dropout>[\d\.eE+-]+)_(?P<lr>[\d\.eE+-]+)\.csv$')
    matching_files = [f for f in file_list if pattern.match(f)]
    print("Found matching files:", matching_files)
    if not matching_files:
        print("No matching files found in the folder.")
        return

    results = {}

    for filename in matching_files:
        match = pattern.match(filename)
        if not match:
            continue

        try:
            dropout = float(match.group("dropout"))
            lr = float(match.group("lr"))
        except Exception as e:
            print(f"Error parsing numbers in {filename}: {e}")
            continue

        full_path = os.path.join(csv_folder, filename)
        try:
            df = pd.read_csv(full_path)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            continue

        if "Branch Prediction Accuracy" not in df.columns:
            print(f"Warning: Skipping {filename} (Missing 'Branch Prediction Accuracy' column)")
            continue

        avg_accuracy = df["Branch Prediction Accuracy"].mean()
        results[(dropout, lr)] = avg_accuracy

    if not results:
        print("No valid data to display.")
        return

    dropout_vals = sorted(set(d for (d, _) in results.keys()))
    lr_vals = sorted(set(lr for (_, lr) in results.keys()))

    heatmap_matrix = np.full((len(dropout_vals), len(lr_vals)), np.nan)

    for (dropout, lr), accuracy in results.items():
        x_index = lr_vals.index(lr)
        y_index = dropout_vals.index(dropout)
        heatmap_matrix[y_index, x_index] = accuracy

    fig, ax = plt.subplots(figsize=(8, 6))
    cax = ax.imshow(heatmap_matrix, aspect='auto', origin='lower', cmap='viridis')
    ax.set_title("Grid Search Heatmap for Dropout Rate and Learning Rate")
    ax.set_xlabel("Learning Rate")
    ax.set_ylabel("Dropout Rate")

    ax.set_xticks(np.arange(len(lr_vals)))
    ax.set_xticklabels([f"{lr:.4g}" for lr in lr_vals])
    ax.set_yticks(np.arange(len(dropout_vals)))
    ax.set_yticklabels([f"{d:.2f}" for d in dropout_vals])

    for i in range(heatmap_matrix.shape[0]):
        for j in range(heatmap_matrix.shape[1]):
            value = heatmap_matrix[i, j]
            if not np.isnan(value):
                ax.text(j, i, f'{value:.2f}', ha='center', va='center',
                        fontsize=8, color='white',
                        bbox=dict(facecolor='black', edgecolor='none', alpha=0.7))

    fig.colorbar(cax, ax=ax, label='Average Branch Prediction Accuracy')
    plt.tight_layout()
    plt.show()


def display_graph(input_str, warmup, test):
    print("Current Directory:", os.getcwd())
    file_list = os.listdir(str(CSV_PATH))
    # Select CSV files whose name contains any predictor from input_str
    csvlist = [f for f in file_list if any(p in f for p in input_str) and f.endswith('.csv')]
    
    # Order the CSV list based on the order the predictors appear in input_str:
    ordered_csvlist = []
    for predictor in input_str:
        for f in csvlist:
            if predictor in f and f not in ordered_csvlist:
                ordered_csvlist.append(f)
                
    if not ordered_csvlist:
        print("No matching CSV files found.")
        return

    # Create data frames in order of the predictors from the command prompt
    data_frames = {}
    for filename in ordered_csvlist:
        df = pd.read_csv(os.path.join(str(CSV_PATH), filename), index_col=0)
        # Verify necessary columns are present for calculating IPC
        if "Test" not in df.columns or "instructions" not in df.columns or "cycles" not in df.columns:
            print(f"Warning: Skipping {filename} (Missing necessary columns)")
            continue
        # Compute IPC as instructions divided by cycles and add as a new column
        df["IPC_calculated"] = df["instructions"] / df["cycles"]
        data_frames[filename] = df

    # Collect tests from all files and sort them alphabetically (for x-axis ordering)
    all_tests = set()
    for df in data_frames.values():
        all_tests.update(df["Test"].tolist())
    all_tests = sorted(all_tests, key=str.lower)

    fig, ax = plt.subplots(figsize=(16, 9))
    bar_width = 1 / (len(ordered_csvlist) + 1)
    x_positions = np.arange(len(all_tests))
    for count, (filename, df) in enumerate(data_frames.items()):
        # Reindex based on the collected tests
        df = df.set_index("Test").reindex(all_tests)
        # Use the computed IPC values
        ipc = df["IPC_calculated"].values
        avg_ipc = np.nanmean(ipc)
        label_text = f"{filename} (avg IPC: {avg_ipc:.2f})"
        bar_offsets = x_positions + count * bar_width
        bars = plt.bar(bar_offsets, ipc, width=bar_width, label=label_text)
        for bar in bars:
            height = bar.get_height()
            if not np.isnan(height):
                plt.text(bar.get_x() + bar.get_width()/2, height, f'{height:.2f}',
                         ha='center', va='bottom', fontsize=6)
    plt.xlabel('Trace Benchmarks', fontweight='bold', fontsize=15)
    plt.ylabel('IPC (instructions / cycles)', fontweight='bold', fontsize=15)
    plt.title(f'IPC per test\n warmup instructions: {warmup}\n sim instructions: {test}')
    fig.text(0.125, 0.875, 'Project Claros', fontsize=12,
             color='grey', ha='left', va='top', alpha=0.7)
    plt.xticks(x_positions + (len(ordered_csvlist) - 1) * bar_width / 2,
               all_tests, rotation=30, ha="right")
    plt.legend(loc='lower center', bbox_to_anchor=(0.5, 0.1), ncol=2)
    plt.show(block=False)
    input("Press Enter to close the graph...")
    plt.close()