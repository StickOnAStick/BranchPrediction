import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import json
import pathlib

MAIN_PATH = pathlib.Path(__file__).parent.parent.resolve()
OLD_WEIGHTS_PATH = MAIN_PATH.joinpath("ChampSim/branch/transformer")
NEW_WEIGHTS_PATH = MAIN_PATH.joinpath("python")
# \\wsl.localhost\Ubuntu\home\john\Branch_Transformer_CUDA\BranchPrediction\matrix-OUT.json
# '\\\\wsl.localhost\\Ubuntu\\home\\john\\Branch_Transformer_CUDA\\BranchPrediction\\ChampSim\\matrix-OUT.json'
def show_heatmap():
    try:
        old_file_path = OLD_WEIGHTS_PATH / "matrix"
        new_file_path = NEW_WEIGHTS_PATH / "matrix-OUT.json"
        
        with open(old_file_path, 'r') as old:
            old_data = json.load(old)
            matrix_list = list(old_data.keys())  # Ensure we get valid keys
        
        try:
            with open(new_file_path, 'r') as new:
                new_data = json.load(new)
        except FileNotFoundError:
            print(f"Could not open new weight file: {new_file_path}")
            return
        
    except FileNotFoundError:
        print(f"Could not open old weight file: {old_file_path}")
        return

    # Check if matrix_list has enough elements
    if len(matrix_list) < 10:
        print("Warning: Not enough matrices to display. Check data.")
        return

    matrix_list_2d = matrix_list[:6]
    line_list = matrix_list[7:10]
    plot_axis = (3, 3)

    fig, axs = plt.subplots(plot_axis[0], plot_axis[1], figsize=(10, 8))
    count_x, count_y, count = 0, 0, 0

    for matrix_name in matrix_list:
        if matrix_name not in old_data or matrix_name not in new_data:
            print(f"Skipping {matrix_name}: Missing in one of the datasets")
            continue

        matrix_a = np.array(old_data[matrix_name])
        matrix_b = np.array(new_data[matrix_name])
        matrix_a = np.nan_to_num(np.array(old_data[matrix_name], dtype=np.float64))
        matrix_b = np.nan_to_num(np.array(new_data[matrix_name], dtype=np.float64))

        # Compute the difference
        difference = matrix_b - matrix_a

        # Ensure difference is a 2D array
        if difference.ndim == 1:  # If 1D
            if difference.size >= 10:  # Only reshape if it's large enough
                difference = np.reshape(difference, (-1, 10))
            else:
                print(f"Skipping {matrix_name}: Difference size too small ({difference.size})")
                continue  # Skip plotting if reshaping isn't possible
        elif difference.shape[1] == 1:  # If it's (N,1), squeeze it to (N,)
            difference = np.squeeze(difference)

        print(f"{matrix_name} shape: {difference.shape}")  # Debugging print

        # Plot the heatmap
        ax = axs[count_y, count_x]
        sns.heatmap(difference, annot=False, cmap="coolwarm", center=0, cbar=True, ax=ax)
        ax.set_title(matrix_name)

        count += 1
        count_x += 1
        if count_x % plot_axis[1] == 0:
            count_x = 0
            count_y += 1
        
        if count >= plot_axis[0] * plot_axis[1]:  # Stop if all subplots are filled
            break


    plt.tight_layout()
    plt.show()


# this should run before we edit the new weights file 
def save_old_weights():
    new_file_path = OLD_WEIGHTS_PATH / "weights_new.json"
    old_file_path = NEW_WEIGHTS_PATH / "weights_old.json"
    
    try:
        with open(new_file_path, 'r') as new:
            with open(old_file_path, 'w') as old:
                new_data = json.load(new)
                json.dump(new_data, old, indent=4)
        print(f"Old weights saved successfully to {old_file_path}")
    except FileNotFoundError:
        print(f"Could not find new weights file: {new_file_path}")