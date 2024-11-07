import threading
import json
import subprocess
import os
import pathlib
import math

# this file is ment to compile all of the make files so they are ready for the tests
# Compile the makefiles for each champsim instance with it's own predictor

MAIN_PATH           = pathlib.Path(__file__).parent.parent.resolve()
LOG_PATH            = MAIN_PATH.joinpath("python/Test_logs")
CHAMPSIM_EXE_PATH   = MAIN_PATH.joinpath("ChampSim/bin/")
TRACER_PATH         = MAIN_PATH.joinpath("ChampSim/tracer") # Tracer tests 
PREDICTOR_PATH      = MAIN_PATH.joinpath("ChampSim/branch") # Predictors
CONFIG_PATH         = MAIN_PATH.joinpath("python/Test_configs")

assert LOG_PATH.is_dir()
assert CHAMPSIM_EXE_PATH.is_dir()
assert TRACER_PATH.is_dir()
assert PREDICTOR_PATH.is_dir()

tage_tables = 0
min_size = 1024
def delete_make():
    # with open('_configuration.mk', "w") as config_file:
    #     config_file.seek(0)
    #     config_file.write("")
    #     config_file.close()
    os.chdir('.csconfig')
    files = os.listdir()
    for i in files:
        print("folder: " + i)
        for j in os.listdir(i):
            if os.path.isdir(i+"/"+j):
               # print("    folder: " + j) 
                for k in os.listdir(i+"/"+j):
                    if os.path.isdir(i+"/"+j +"/"+k):
                       # print("         folder:" + k)
                        for l in os.listdir(i+"/"+j +"/"+k):
                            if os.path.isdir(i+"/"+j +"/"+k + "/" + l):
                                a =2 
                            #    print("             folder:" + l)
                            else:
                        #        print("             file:" + l)
                                os.remove(i+"/"+j +"/"+k + "/" + l)
                    else:
                   #     print("         file:" + k)
                        os.remove(i+"/"+j +"/"+k)
            else: 
              #  print("    file: " + j)
                os.remove(i+"/"+j)
    for i in files:
       # print("folder: " + i)
        for j in os.listdir(i):
            for k in os.listdir(i+"/"+j):
                for l in os.listdir(i+"/"+j +"/"+k):
                    os.rmdir(i+"/"+j +"/"+k + "/" +l)
                os.rmdir(i+"/"+j +"/"+k)
            os.rmdir(i+"/"+j)
        os.rmdir(i)
    os.chdir('..')

# this is literally copy and pasted from gemini but it works 
def replace_from_position(string, old, new, position):
  # Replaces a substring in a string starting from a specific position
  return string[:position] + string[position:].replace(old, new, 1)

# find all the powers of two below the input number
def find_2_pow(max):
    count = 0
    while (pow(2,count) <= max):
        count += 1
    return count

def find_itt_ammount(predictor, max):
    max = max * 1024  # convert to kbits
    # print (predictor + "|" + str(max))
    predictor_sizes = []
    size = 0
    n = 0
    match predictor:
        case 'gshare' | 'global_history' | 'bimodal':
           while (3*size <= max):
                predictor_sizes.append([3*size,n])
                size = pow(2,n)
                n += 1
        case "Bi-Mode":
            while (9*size <= max):
                predictor_sizes.append([9*size,n])
                size = pow(2,n)
                n += 1
        case 'yags':
            while ((9+(2*8))*size <= max):
                predictor_sizes.append([(9+(2*8))*size,n])
                size = pow(2,n)
                n += 1
        case "local_history":
           while (3*size <= max):
                predictor_sizes.append([3*size,n])
                size = pow(2,n)
                n += 1
        case "tage" | "tage2" | "tage4" | "tage8" | "tage16":
        # tage size = bimodal_table_size*bimodal_bits + tablenum*2^indexsize*(tage_bimodal_bits*tag_length*useful_bits)
        # size = bimodal_table_size*3 + tablenum*(bimodal_table_size/4)*(7+2+2)
        # size = 3*(tablenum+1)(bimodal_table_size)
            with open((str(PREDICTOR_PATH) + "/" +predictor+"/"+predictor+".cc"),'r+') as c_file:
                c_code = c_file.read()
                start = c_code.find("TAGE_TABLES ") + len("TAGE_TABLES ")
                end = c_code.find("\n", start)
                tage_tables = int(c_code[start:end])
            c_file.close()
            while (3*(tage_tables+1)*size <= max):
                predictor_sizes.append([3*(tage_tables+1)*size,n])
                size = pow(2,n)
                n += 1
    count = 0
    for size in predictor_sizes:
        if size[0] < min_size:
            count += 1
    return predictor_sizes[count:]
            


           



def compile_champsim_instance(*args):
    # account for whether or not we are compiling to a certain size 
    predictor = args[0]
    if len(args) > 1:
        size = args[1] 
    else:
        size = -1
    print("Compiling Predictor: " + predictor)
    print("size:" + str(size[0]))
    if (size[0] != -1):
        # print("Compilation size = " + str(pow(2,size)*1024) + "Bits")
        with open((str(PREDICTOR_PATH) + "/" +predictor+"/"+predictor+".cc"),'r+') as c_file:
            c_code = c_file.read()
           # print(c_code)
           # becuase we can't change the variables in the C code we need to make scaling size for each branch predictor
            match predictor:
                case 'gshare':
                    start = c_code.find("GS_HISTORY_TABLE_SIZE = ") + len("GS_HISTORY_TABLE_SIZE = ")
                    end = c_code.find(";", start)
                    c_code = replace_from_position(c_code, c_code[start:end], str(int(size[0]/3)),start)
                case 'global_history':
                    start = c_code.find("BIMODAL_TABLE_SIZE = ") + len("BIMODAL_TABLE_SIZE = ")
                    end = c_code.find(";", start)
                    c_code = replace_from_position(c_code, c_code[start:end], str(int(size[0]/3)),start)

                    start = c_code.find("HISTORY_LENGTH = ") + len("HISTORY_LENGTH = ")
                    end = c_code.find(";", start)
                    c_code = replace_from_position(c_code, c_code[start:end], str(size[1]-1),start)

                case 'bimodal': 
                    start = c_code.find("BIMODAL_TABLE_SIZE = ") + len("BIMODAL_TABLE_SIZE = ")
                    end = c_code.find(";", start)
                    c_code = replace_from_position(c_code, c_code[start:end], str(int(size[0]/3)),start)

                case "local_history":
                    start = c_code.find("BIMODAL_TABLE_SIZE = ") + len("BIMODAL_TABLE_SIZE = ")
                    end = c_code.find(";", start)
                    print(str(start)+"|"+str(end))
                    print("replacing table size with: " + str(pow(2,size)*256))
                    c_code = c_code.replace(c_code[start:end],str(pow(2,size)*256),1) # multiply by the n * 2k * 4 = n*8096 = nkb
                    
                    start = c_code.find("HISTORY_TABLE_SIZE = ") + len("HISTORY_TABLE_SIZE = ")
                    end = c_code.find(";", start)
                    print(str(start)+"|"+str(end))
                    print("replacing table size with: " + str(pow(2,size)*32))
                    c_code = c_code.replace(c_code[start:end],str(pow(2,size)*32),1) # multiply by the n * 2k * 4 = n*8096 = nkb

                    start = c_code.find("INDEX_SIZE = ") + len("INDEX_SIZE = ")
                    end = c_code.find(";", start)
                    print(str(start)+"|"+str(end))
                    print("History length with " + str(size+8))
                    c_code = c_code.replace(c_code[start:end],str(size+8),1) # multiply by the n * 2k * 4 = n*8096 = nkb

                case "Bi-Mode":
                    start = c_code.find("TABLE_SIZE = ") + len("TABLE_SIZE = ")
                    end = c_code.find(";", start)
                    c_code = replace_from_position(c_code, c_code[start:end], str(int(size[0]/9)),start)

                    start = c_code.find("GLOBAL_HISTORY_LENGTH = ") + len("GLOBAL_HISTORY_LENGTH = ")
                    end = c_code.find(";", start)
                    c_code = replace_from_position(c_code, c_code[start:end], str(size[1]-1),start)
                case "yags":
                    start = c_code.find("TABLE_SIZE = ") + len("TABLE_SIZE = ")
                    end = c_code.find(";", start)
                    c_code = replace_from_position(c_code, c_code[start:end], str(int(size[0]/(9+(2*8)))),start)

                    start = c_code.find("GLOBAL_HISTORY_LENGTH = ") + len("GLOBAL_HISTORY_LENGTH = ")
                    end = c_code.find(";", start)
                    c_code = replace_from_position(c_code, c_code[start:end], str(size[1]-1),start)

                case "tage" | "tage2" | "tage4" | "tage8" | "tage16":
                    start = c_code.find("BIMODAL_TABLE_SIZE ") + len("BIMODAL_TABLE_SIZE ")
                    end = c_code.find("\n", start)
                    c_code = replace_from_position(c_code, c_code[start:end], str(int(size[0]/(3*(tage_tables+1)))),start)

                    start = c_code.find("MAX_INDEX_BITS ") + len("MAX_INDEX_BITS ")
                    end = c_code.find("\n", start)
                    c_code = replace_from_position(c_code, c_code[start:end], str(size[1]-3),start)

            c_file.seek(0)
            c_file.write(c_code)
            c_file.truncate()
            c_file.close()

    # create a copy of the configuration json and create our own config and add it to the files 
    with open((MAIN_PATH.joinpath("ChampSim/champsim_config.json")),'r') as file:
        data = json.load(file)
        remove = data['ooo_cpu'][0]['branch_predictor'] # remove this when not debugging 
        with open(str(CONFIG_PATH) + "/" + predictor + "_config.json",'w') as config_file:
            data['ooo_cpu'][0]['branch_predictor'] = predictor # change the branch predictor
            if (size != -1):
                data['executable_name'] = "champsim_" + predictor + "_size-" + str(size[0]) + "bits" # change the executable name
                # print(data['executable_name'])
            else:
                data['executable_name'] = "champsim_" + predictor # change the executable name
            # implement changes and close files 
            config_file.seek(0)
            json.dump(data, config_file,indent=4)
            config_file.truncate()
            config_file.close()
            file.close()
    try:
        print ("config file:" +str(CONFIG_PATH) + "/" + predictor + "_config.json")
        print("compiling...")
        os.chdir(MAIN_PATH.joinpath("champsim"))
        subprocess.run(["./config.sh", str(CONFIG_PATH) + "/"+ predictor + "_config.json"])
        subprocess.run(["make","-j","-s"], check=True)
        subprocess.run(["make","-j","clean"], check=True)
        os.chdir(MAIN_PATH)

    except subprocess.CalledProcessError as e:
        print(f"Error running make: {e}")
    
    



# runs in series 
def compile_all(predictors,size):
    print("Compiling Champsim instances(This may take a few minutes)")
    for i in predictors: 
        threading.Thread()
        if (size != -1):
            print(find_itt_ammount(i,size))
            for k in find_itt_ammount(i,size):
                compile_champsim_instance(i,k)
        else:
            compile_champsim_instance(i)
    print("Instance Compilation has finished")

# os.chdir("Z:/shared_files/Champsim/BranchPrediction/Champsim")
# print(os.getcwd())
# compile_champsim_instance("bimodal",4)

# runs in parallel but has a weird clock skew error
# def compile_all(predictors,size):
#     print("Compiling Champsim instances(This may take a few minutes)")
#     size = find_2_pow(size)
#     for i in predictors:
#         for k in range(0,size):
#             thread = threading.Thread(target = compile_champsim_instance, args = [i,k])
#             print("starting thread for compiling:" + i + "of size " + str(pow(2,k)) + "kb")
#             thread.start()
#     for j in predictors:
#         thread.join()    
#     print("Instance Compilation has finished)")

                
