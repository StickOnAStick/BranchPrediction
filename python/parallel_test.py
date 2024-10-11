import subprocess
import os
import sys
import time
import threading
import psutil

from typing import TextIO
from subprocess import Popen
from loguru import logger


printout = 1
warmup_instructions = 2000000
simulated_instructions = 5000000


path = 'ChampSim/bin/champsim'        # path for executable
tracer = 'ChampSim/tracer'            # path for tracer tests
output_file_name = 'Champsim_log.txt' # Output file name



# from https://stackoverflow.com/questions/30686295/how-do-i-run-multiple-subprocesses-in-parallel-and-wait-for-them-to-finish-in-py


def main():
    executable, tracer_path = ensure_paths()
    out_file = main_screen()

    trace_list: list[str] = get_trace_tests()
    instruction_list: list[str] = get_instruction_list(traces=trace_list, champsim_path=executable, tracer_path=tracer_path)

    run_instructions(instructions=instruction_list, out_file=out_file)

    # Load Result data

    # Generate graphs
    # Yippie
    logger.success("ChampSim Benchmarks complete!")


def main_screen() -> str:
    """
        I'm no ascii artist
    """
    print("--------------------------------------\n------------ChampSim Benchmark--------\n--------------------------------------")
    output_file_name = input("Output file name: ")
    output_file_name = output_file_name.join(".txt") # Join is faster

    while True:
        user_in: str = input("\nEnable debug logs? Y/N: ").strip().upper()
        if user_in in ("Y", "N"):
            if user_in == "N":
                logger.add(sys.stdout, level="INFO")                   # Change log level to ignore debug logs.
            break
        else:
            print("Invlaid input")

    return output_file_name

def ensure_paths() -> tuple[str, str]:
    # Assert ChampSim is installed
    logger.debug("Ensuring Champsim Directory exists...")
    current_path: str = os.path.dirname(os.path.realpath(__file__))     # Path where script is called
    parent_path: str = os.path.dirname(current_path)                    # Parent path of ChampSim
    champsim_path: str = os.path.join(parent_path, "ChampSim")
    executable_path: str = os.path.join(champsim_path, "bin/champsim")
    tracer_path: str = os.path.join(champsim_path, "tracer")

    if not os.path.exists(champsim_path):
        logger.exception("ChampSim is not currently installed or misplaced!")
    if not os.path.exists(executable_path):
        logger.exception("ChampSim Executable not found! Ensure you've compiled ChampSim")
    if not os.path.exists():
        logger.exception("ChampSim Tracer tests not found!")
    
    return executable_path, tracer_path

def get_trace_tests():
    # find all of the files in the tracer folder, then copy the names into tracelist 
    file_list = os.listdir(tracer)
    tracelist = [ file for file in file_list if file.find(".xz") == -1]
    logger.debug(f"Running the following tests: {tracelist}")
    
    if len(tracelist) == 0:
        logger.exception("No trace tests were found!")
        SystemExit()

    return tracelist

def get_instruction_list(traces: list[str], champsim_path: str, tracer_path: str) -> list[str]:
    # Create the instructions through concatonation 
    instruction_list = [""] * len(traces)
    instruction_list = [ champsim_path.join(
        f""" --warmup-instructions {str(warmup_instructions)} --simulation-instructions {str(simulated_instructions)} {tracer_path}/{trace}""")
        for trace in traces
        ]
    logger.debug(f"\nInstructions generated: {instruction_list}")

    if len(instruction_list) == 0:
        logger.exception("No instructions were generated!")

    return instruction_list

def run_instructions(instructions: list[str], out_file: str):
    with open(output_file_name,'w') as test_log:
        # Launch subprocesses
        procs = [subprocess.Popen(instruction, shell=True, stdout=test_log) for instruction in instructions]
        
        # Mem check thread
        logger.info("Starting Memchecker")
        thread = threading.Thread(target = memchecker, args = [procs]) # creating the memchecker thread 
        thread.start()
        
        # wait for all processes to complete
        while procs:
            for idx, proc in enumerate(procs):

                ret_code: int | None = proc.poll()
                if ret_code is not None:
                    logger.debug(f"Process: {proc.args} finished with return code: {ret_code}")
                    procs.pop(idx)

            # Don't kill your cpu, sleepy time
            time.sleep(1)  

        # Join memcheck thread when all procs complete
        thread.join()

        logger.info("All processes have finished")
        logger.info("Exiting memchecker, ")


def memchecker(pids: list[Popen[bytes]], test_log: TextIO):
    time.sleep(10)
    for p in pids:
        a = psutil.Process(p.pid)
        for i in a.children():
            print ("PID:" + str(i.pid))
            print("Memory amount: " + str((i.memory_info().rss/(1024*1024))) + "MB")
            test_log.write("Memory Info: (" + p.args + "|" + str((i.memory_info().rss/(1024*1024))) + "MB )")  


if __name__ == "__main__":
    main()
