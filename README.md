# Repository for SJSU CMPE 195 __Branch Prediction__ Capstone project.

CLI framework to test various branch predictors.

## Contributors
Nick
Ayman
John

# Running and installation

## Champsim Windows setup:

### Installation
Firstly, clone the Champsim repo into the BranchPrediction Repository via:

`git clone git@github.com:ChampSim/ChamdpSim.git`

You should now have a `BranchPrediction/ChampSim` directory. We also need to update and install __VCpkg__ for __C/C++ dependencies__. To do this first navigate inside the created _ChampSim_ directory and run: 

`git submodule update --init`

To install the C/C++ dependencies run the following two commands:

`vcpkg/bootstrap-vcpkg.bat` __(Windows)__ `vcpkg/bootstrap-vcpkg.sh` **(Linux)**

`vcpkg/vcpkg.exe install --triplet x64-linux` __(Windows)__ `vcpkg/vcpkg install` __(Linux)__

#### IMPORTANT NOTE:
Yes, we __ARE compiling to linux__ despite being on windows! You can do this in wsl, and run champsim as normal. 

The reason for this is due to the makefile being written for UNIX-based systems. If you want to, you can re-write the commands to make it Windows compatible. ~10 min.

### Compilation

If you're using windows, we will need to access wsl for a moment. Open a wsl terminal and run `./config.sh` from the ChampSim directory.

This will create a `_configuration.mk` file in the main directory.

Now we can make the main _ChampSim_ project. To do so, use `make clean` _to ensure your project is clean_ then run `make` in the main ChampSim directory. 


### Notes:
If you get `Error 1` after running `make` #### FILL ME IN #####



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
