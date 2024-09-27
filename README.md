# Repository for SJSU CMPE 195 __Branch Prediction__ Capstone project.

Description of the project goes here

## Contributors
Nick
Ayman
John

## Extras

### How to setup champsim on an apple silicon mac
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