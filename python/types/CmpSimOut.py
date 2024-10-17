from pydantic import BaseModel
from pendulum import datetime

import numpy as np
import pandas as pd



class ChampSimOut(BaseModel):
    test: str
    ipc: int
    instructions: int
    cycles: int
    BPAccuracy: float
    MPKI: float
    avg_ROB_occupancy_at_mispredict: float
    branch_indirect: float
    branch_conditional: float
    branch_indirect_call: float
    branch_return: float
    test_len: 