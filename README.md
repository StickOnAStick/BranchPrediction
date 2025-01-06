# Repository for SJSU CMPE 195 __Branch Prediction__ Capstone project.

Description of the project goes here

## Contributors
Nick
John
Evan
Ayman


# Running and installation

## Clone and initalize repo

Clone this repo into a chosen directory with:
```bash
git clone git@github.com:StickOnAStick/BranchPrediction.git
```

**Initalize** the ___ChampSim___ submodule
```bash
cd BranchPrediciton
git submodule update --init
```
Your `./ChampSim` directory will now be filled with content. 

## Initalizing ChampSim
#### Important Note for Windows Users:
ChampSim is designed to be run on a _Debian-Based_ operating system. If you're using Windows you will need to execute the following commands in __WSL__ (Windows Sub-System for Linux) __OR__ a __Virtual Machine__ running Ubuntu, Arch, Mint, etc.

### Pull latest ChampSim changes
Our current submodule is a detached head, because of this we need to checkout the master to ensure we're working off the latest revision.
```bash
git checkout master
```

### Download ChampSim dependencies

#### Pre-Requisites  
You will need to have the following apt packages installed: 
```bash
sudo apt install curl zip unzip tar gcc ninja-build clang pkg-config
```

ChampSim relies on VCPKG to manage dependencies. To install it and all packages use the following commands from the `/ChampSim/.` directory.

```bash
git submodule update --init 
sudo vcpkg/bootstrap-vcpkg.sh
sudo vcpkg/vcpkg install
```
These will download the vcpkg submodule, setup the vcpkg configuration, and install all the packages.

### Build Champsim
Setup the champsim configuration.
```bash
./config.sh <file_name> // Leave blank to use default
make
```
This will create a `_configuration.mk` file in the main ChampSim directory.


If successfully built from here you're set to begin development!

# Installing CUDA for ChampSim

### Using Windows WSL or Linux

If using a Windows machine that already has the [CUDA ToolKit](https://developer.nvidia.com/cuda-downloads?target_os=Windows&target_arch=x86_64&target_version=11) installed follow this guide carefully as we make steps to ensure no overwrites occur. 

[The full guide](https://docs.nvidia.com/cuda/wsl-user-guide/index.html) for this goes into more detail and is worth a read, this guide will only cover key topics to get up & running (Steps 3+ on Nvidia's guide).


### Install WSL cuda drivers
Get the local [WSL Cuda Drivers](https://developer.nvidia.com/cuda-downloads?target_os=Linux&target_arch=x86_64&Distribution=WSL-Ubuntu&target_version=2.0&target_type=deb_local)

The following will install the _CUDA ToolKit_ **NOT THE DRIVER**
```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.6.3/local_installers/cuda-repo-wsl-ubuntu-12-6-local_12.6.3-1_amd64.deb
sudo dpkg -i cuda-repo-wsl-ubuntu-12-6-local_12.6.3-1_amd64.deb
sudo cp /var/cuda-repo-wsl-ubuntu-12-6-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda-toolkit-12-6
```

**DO NOT** install the drivers in WSL. You should already have [the drivers](https://www.nvidia.com/en-us/drivers/) installed locally on your windows machine via Nvidia App or manual install.

After the installation you might've noticed that `nvcc --version` is still not working. To remedy this, we need to add the just installed _CUDA ToolKit_ to our path by updating `bash.rc`

```bash
nano ~/.bashrc 
# OR (recommended extension)
micro ~/.bashrc
```
Inside here add the following exports near the top, similar to adding PATH variables on Windows.
**Note**: Verify the PATHs to each of these directories for your own machine.
```bash
export PATH="/usr/local/cuda-12.6/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/cuda-12.6/lib64:$LD_LIBRARY_PATH" 
```
In order to see the changes either `close and open another terminal` **or** run `source ~/.bashrc`

#### Check installation

```bash
~$ nvcc --version
# Should return this: 
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2024 NVIDIA Corporation
Built on Tue_Oct_29_23:50:19_PDT_2024
Cuda compilation tools, release 12.6, V12.6.85
Build cuda_12.6.r12.6/compiler.35059454_0
```

Now we're set!




## Champsim MAC setup:
1. Install parallels
2. Install ubuntu with rosetta x86_64 emulation
3. Clone this repo
4. Double click on Resources/sources.list and click install (copy)
5. Run `sudo dpkg --add-architecture amd64`
6. Run `sudo apt update`
7. Clone champsim repo
8. Delete vcpkg folder inside the champsim repo
9. Clone the microsoft/vcpgk repo inside the champsim repo
10. Cd back to the champsim repo
11. Run `git submodule update --init`
12. Run `sudo apt install cmake`
13. Run `sudo apt-get install ninja-build`
14. Run `sudo apt-get update && sudo apt-get install build-essential`
15. Run `export VCPKG_FORCE_SYSTEM_BINARIES=1`
16. Run `vcpkg/bootstrap-vcpkg.sh`
17. Run `sudo apt-get install pkg-config`
18. Run `vcpkg/vcpkg install`
19. Run `./config.sh [YOUR CHAMPSIM CONFIG].json`
20. Run `make`

## Main python worker:

We're currently using poetry for package managment. Briefly, Poetry manages dependencies and versioning across machines and differening operating systems.

### __Install Poety__

This project using Poetry to manage dependencies. If you do not have it installed, please install it [here](https://python-poetry.org/docs/) and review the [usage docs](https://python-poetry.org/docs/basic-usage/).

### __Setup Poetry__ 
Setup your poetry virtual enviornment, for reproducibilty we will creat this inside the projects directory using the following commands.

```bash
cd BranchPredictor
poetry config virtualenvs.in-project true
poetry install
```
After this you will see a .venv folder be created inside the project's root. 

### __Activate Poetry Venv__
Now that the venv is setup we can activate it using:

__linux__
```bash
source .venv/bin/activate
```

__windows__:
```cmd
.venv\Scripts\activate
```

Now we are free to install all packages without conflicting dependencies!

Use the `poetry install` command to install all current existing dependencies or `poetry add myPackage` to extend the current package set. 

### Important Note:
Also ensure you've set VsCode's interpreter to use the poetry venv. You can change the interpreter using: `CTRL + SHIFT + P`, enter in `>Interpreter` then select the interpreter located at:
#### Windows:
 ```
 BranchPredictor/.venv/Scripts/python.exe
 ```
#### Linux:
 ```
 BranchPredictor/.venv/bin/python3.12
 ```


__ALSO:__ If you're using Ubuntu >= 22.04 you'll need to install _libxcb-cursor_ for displaying graphs. Do so using: 
```bash
sudo apt install libxcb-cursor0
```  