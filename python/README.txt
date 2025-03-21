How to Use python commands provided in this folder, and short descriptions of what each does
(file descriptions are gpt, accuracy may vary, but I wrote how to use the actual commands, and file saving):


Note for all python tests:
    When running any of the tests, the trace files that will be used are those in the ChampSim/tracer file,
    move trace files in or out of this folder depending on which tests you wish to run 


Testing Files: 
    parallel_test.py:
    Description:
            This script automates running and compiling ChampSim branch predictors. Key functionalities include:

                1. Command-Line Execution – Runs simulations for specified predictors and traces, handling command-line arguments.
                2. Compilation Management – If a predictor’s executable doesn’t exist, it compiles it; otherwise, it skips recompilation.
                3. Multi-Threaded Execution – Runs simulations in parallel for efficiency.
                4. Configuration Parsing – Handles input parameters like warmup instructions, simulation length, and predictor selection.
                5. Result Processing – Merges JSON outputs, generates CSV reports, and displays performance graphs.
                This ensures efficient and automated testing of branch predictors in ChampSim.
        
        Where files are saved: Test_logs & Trace_tests 
            Final CSV files are stored in Trace tests 
            Temporary files, whith the name of each test and predictor are saved to Test_logs, these will be deleted during the JSON merge
        
        Commands:
            python3 parallel_test.py --warmup_instructions 100000 --simulation_instructions 250000 --predictors tage-sc hashed_perceptron Local_transformer Attention --recompile Attention Local_transformer
            use help command for more info on each arguments
                

    Training_speed_test.py:
        Description:
            Same as parallel_test, but we generate txt files instead of json, we read these to get a graph of accuracy over execution time
            - I don't recommend you run more than one trace at a time, it will make the graph really messy 
            
        Where files are saved:
            Saves files into Speed_logs as a txt, this txt will have the same output as stdout, any cout in the predictor will go to the txt file
        
        Commands: 
            python3 Training_speed_test.py --warmup_instructions 250000 --simulation_instructions 1000000 --predictors tage-sc Attention hashed_perceptron Local_transformer --recompile Attention
            use help command for more info on each arguments

    NN_Trainer.py:
        Description: 
            This script is a "parallel test" 
            (Comments from John: it's only parallel in the sense that you could train multiple models at the same time, however the tests for each model are run sequentially)
            launcher for branch predictor evaluation in ChampSim. It automates the process of running simulations with different branch predictors by:

            1. Managing Predictors: Determines which predictors need to be compiled and recompiles them if necessary.
            2. Running Simulations: Executes branch prediction tests using multiple predictors and instruction traces in parallel.
            3. Logging and Analysis: Saves logs, creates CSVs, and generates learning graphs based on the test results.
            It supports command-line arguments to configure test iterations, warm-up instructions, simulation instructions, and specific predictors to test or recompile.
        
        Where files are saved: Learning_chats_Speed_logs
            Saves files into Speed_logs as a txt, this txt will have the same output as stdout, any cout in the predictor will go to the txt file,
            At the end of each test we add the previous iterration of that test to the old test graphs so we can see any learned progress. 
            These graphs are saved in Learning_chats 
        
        Commands:
            python3 NN_trainer.py --test_itt 20 --warmup_instructions 5000 --simulation_instructions 100000 --predictors Transformer_NN --recompile Transformer_NN
            test_itt will run the tests N times, each test will have that number of warmup instructions and simulation instrucitons.
            The tests will be run in a random order for each test itteration

Helper Files or depricated: 
    test_parser.py 
        This script processes ChampSim branch predictor logs, extracts key metrics (e.g., prediction accuracy, IPC, MPKI) from JSON files, saves them as CSVs, and generates performance graphs.

        Main Features:
        1. Parse JSON Logs → Extracts branch prediction stats.
        2. Create CSVs → Saves parsed data for analysis.
        3. Generate Graphs:
            - Size vs. Accuracy → Shows accuracy trends for different predictor sizes.
            - Speed vs. Accuracy → Tracks learning progress over instruction cycles.
            - Comparison Graphs → Visualizes accuracy across different tests.
        Helps analyze branch predictor performance across multiple tests and configurations.


    recompiler.py
        This script automates the compilation of ChampSim branch predictors by generating customized configurations and Makefiles for each predictor. Key functionalities include:

        1. File and Directory Setup  – Defines paths for logs, executables, predictors, and configurations.
        2. Cleanup Function (delete_make) – Deletes old compiled files.
        3. Helper Functions – Calculates valid predictor sizes (find_itt_ammount), replaces strings in code (replace_from_position), and finds power-of-two limits.
        4. Compilation Logic (compile_champsim_instance) 
            – Modifies predictor source code based on size.
            – Creates a custom JSON config.
            – Runs config.sh and make to compile the predictor.
        5. Batch Compilation (compile_all) – Iterates through predictors, adjusting sizes, and compiling them sequentially.
        It allows flexible, automated compilation of various branch predictors with different size constraints.


    size_test.py: (Mostly depricated but will likely use some of the code for hyperparameter searching)
        This script automates the testing of ChampSim branch predictors by compiling, running, and analyzing results from different predictor configurations.

        Main Features:
        1. Argument Parsing → Allows users to specify predictors, recompile options, instruction counts, and log levels.
        2. Compilation Management → Checks if predictors are compiled and recompiles if necessary.
        3. Test Execution → Runs simulations for selected predictors using multiple trace files.
        4. Parallel Execution → Uses threading to speed up testing.
        5. Data Merging & Analysis → Collects JSON logs, calculates accuracy, and saves final results.
        6. Graph Generation → Creates CSV files and visualizes predictor performance.
        This automates large-scale branch predictor benchmarking with minimal manual intervention. 🚀


    Weights_Heatmap.py: (Mostly depricated)
        This script visualizes differences between old and new weight matrices using heatmaps and ensures old weights are backed up before updates. Key functionalities:

        Heatmap Visualization (show_heatmap)
        1. Loads matrices from two JSON files (old and new weight files).
        2. Computes differences between corresponding matrices.
        3. Uses Seaborn to generate heatmaps for visual comparison.
        4. Handles missing data, ensures matrices are in a valid shape, and stops plotting when subplots are filled.
        5. Backup Old Weights (save_old_weights)
        6. Copies weights_new.json (new weights) into weights_old.json (old weights) before updates.
        
        Prevents accidental overwrites by keeping a backup.
        This helps track weight updates visually and maintains a backup for reference.
