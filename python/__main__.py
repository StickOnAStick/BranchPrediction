from loguru import logger

import pathlib


MAIN_PATH           = pathlib.Path(__file__).parent.parent.resolve()
LOG_PATH            = MAIN_PATH.joinpath("python/Test logs/champsim")
CHAMPSIM_EXE_PATH   = MAIN_PATH.joinpath("ChampSim/bin/champsim")
TRACER_PATH         = MAIN_PATH.joinpath("ChampSim/tracer") # Tracer tests 
PREDICTOR_PATH      = MAIN_PATH.joinpath("ChampSim/branch") # Predictors

assert LOG_PATH.is_dir()
assert CHAMPSIM_EXE_PATH.is_file()
assert TRACER_PATH.is_dir()
assert PREDICTOR_PATH.is_dir()




def main() -> None:
    pass



if __name__ == "__main__":
    main()
    