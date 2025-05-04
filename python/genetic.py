import random
import subprocess
import threading
import json
import os
import pathlib
import concurrent.futures
import time
import argparse
import re
import csv

# ---------------- CLI Argument Parsing ----------------
parser = argparse.ArgumentParser(
    description="Run GA for a branch predictor variant"
)
parser.add_argument(
    "-p", "--predictor",
    required=True,
    help="Name of the branch predictor (e.g. Attention, MyPred, ...)"
)
args = parser.parse_args()
PREDICTOR = args.predictor

#256k
CUSTOM_SEED_STRINGS = [
    #  "n=8, sizes=[4096, 256, 8192, 8192, 1024, 2048, 32768, 16384], bits=[8, 4, 4, 8, 8, 4, 1, 2], start_hist=2, alpha=1.513, GH_bits=20, IP_bits=24, PATH_bits=16, PATH_reg=8, hidden=8, num_heads=4, dropout=0.174, lr=0.001195",
    #  "n=8, sizes=[16384, 128, 2048, 1024, 16384, 512, 8192, 32768], bits=[4, 12, 8, 2, 1, 12, 2, 2], start_hist=4, alpha=1.336, GH_bits=24, IP_bits=12, PATH_bits=24, PATH_reg=4, hidden=16, num_heads=4, dropout=0.148, lr=0.000995"
]
#1024k
CUSTOM_SEED_STRINGS = [
    "n=16, sizes=[4096, 2048, 32768, 2048, 32768, 8192, 32768, 16384, 4096, 4096, 32768, 32768, 4096, 128, 32768, 2048], bits=[8, 4, 4, 4, 8, 8, 2, 4, 8, 12, 2, 2, 12, 2, 2, 8], start_hist=2, alpha=1.380, GH_bits=4, IP_bits=16, PATH_bits=2, PATH_reg=16, hidden=8, num_heads=4, dropout=0.052, lr=0.000931",
    "n=18, sizes=[8192, 16384, 8192, 8192, 16384, 16384, 128, 16384, 512, 16384, 32768, 8192, 512, 4096, 4096, 256, 8192, 2048], bits=[4, 8, 8, 8, 1, 4, 8, 8, 8, 2, 8, 2, 4, 12, 8, 2, 2, 8], start_hist=3, alpha=1.331, GH_bits=24, IP_bits=12, PATH_bits=24, PATH_reg=64, hidden=12, num_heads=4, dropout=0.145, lr=0.001277",
    "n=18, sizes=[8192, 4096, 256, 8192, 32768, 32768, 512, 16384, 1024, 16384, 32768, 512, 32768, 4096, 8192, 1024, 1024, 32768], bits=[8, 8, 2, 8, 1, 2, 8, 8, 8, 2, 2, 12, 1, 8, 4, 2, 2, 8], start_hist=3, alpha=1.294, GH_bits=12, IP_bits=20, PATH_bits=16, PATH_reg=8, hidden=12, num_heads=4, dropout=0.048, lr=0.001390",
    "n=17, sizes=[4096, 16384, 32768, 32768, 16384, 4096, 1024, 16384, 128, 32768, 32768, 32768, 1024, 256, 32768, 2048, 8192], bits=[8, 4, 4, 4, 8, 8, 4, 1, 8, 2, 2, 2, 12, 8, 2, 4, 12], start_hist=4, alpha=1.337, GH_bits=2, IP_bits=20, PATH_bits=20, PATH_reg=16, hidden=16, num_heads=4, dropout=0.154, lr=0.001093",
    "n=17, sizes=[256, 16384, 8192, 32768, 16384, 16384, 8192, 16384, 8192, 16384, 512, 8192, 256, 4096, 16384, 1024, 8192], bits=[8, 12, 8, 4, 4, 8, 4, 1, 8, 2, 2, 2, 12, 8, 2, 4, 2], start_hist=4, alpha=1.337, GH_bits=2, IP_bits=20, PATH_bits=20, PATH_reg=4, hidden=16, num_heads=4, dropout=0.121, lr=0.000925",
    "n=15, sizes=[32768, 16384, 1024, 256, 32768, 8192, 32768, 16384, 4096, 32768, 16384, 16384, 16384, 2048, 32768], bits=[2, 4, 8, 2, 2, 12, 4, 4, 8, 1, 8, 1, 8, 8, 1], start_hist=2, alpha=1.347, GH_bits=2, IP_bits=12, PATH_bits=20, PATH_reg=8, hidden=16, num_heads=4, dropout=0.094, lr=0.000704",
    "n=16, sizes=[4096, 16384, 32768, 1024, 32768, 1024, 1024, 16384, 2048, 32768, 32768, 32768, 4096, 256, 32768, 2048], bits=[8, 4, 4, 4, 8, 8, 2, 4, 8, 2, 2, 2, 12, 8, 2, 4], start_hist=4, alpha=1.314, GH_bits=4, IP_bits=12, PATH_bits=20, PATH_reg=4, hidden=12, num_heads=4, dropout=0.185, lr=0.000826"
    "n=16, sizes=[512, 4096, 16384, 8192, 1024, 32768, 256, 8192, 32768, 512, 512, 32768, 4096, 16384, 16384, 8192], bits=[8, 8, 1, 8, 8, 8, 2, 12, 1, 12, 2, 1, 2, 2, 12, 12], start_hist=2, alpha=1.397, GH_bits=2, IP_bits=20, PATH_bits=24, PATH_reg=4, hidden=12, num_heads=4, dropout=0.234, lr=0.001281",
    "n=10, sizes=[16384, 32768, 128, 8192, 32768, 256, 16384, 16384, 256, 32768], bits=[8, 12, 2, 4, 4, 12, 12, 2, 12, 1], start_hist=4, alpha=1.333, GH_bits=20, IP_bits=12, PATH_bits=4, PATH_reg=4, hidden=16, num_heads=4, dropout=0.125, lr=0.001702",
    "n=18, sizes=[8192, 8192, 16384, 4096, 8192, 32768, 32768, 1024, 8192, 2048, 4096, 16384, 2048, 16384, 256, 2048, 32768, 4096], bits=[1, 1, 4, 1, 8, 2, 2, 12, 2, 4, 8, 8, 2, 4, 8, 8, 8, 2], start_hist=2, alpha=1.315, GH_bits=12, IP_bits=8, PATH_bits=4, PATH_reg=32, hidden=16, num_heads=4, dropout=0.184, lr=0.001607",
    "n=10, sizes=[4096, 32768, 32768, 128, 2048, 8192, 8192, 32768, 32768, 2048], bits=[8, 8, 8, 8, 1, 2, 1, 8, 2, 4], start_hist=3, alpha=1.447, GH_bits=2, IP_bits=20, PATH_bits=24, PATH_reg=4, hidden=12, num_heads=4, dropout=0.233, lr=0.000897",
    "n=15, sizes=[4096, 16384, 1024, 128, 32768, 4096, 32768, 16384, 2048, 32768, 16384, 32768, 16384, 1024, 2048],bits=[8, 12, 8, 4, 8, 8, 2, 2, 8, 2, 8, 2, 1, 2, 2], start_hist=4, alpha=1.329, GH_bits=2, IP_bits=12, PATH_bits=20, PATH_reg=8, hidden=16, num_heads=4, dropout=0.158, lr=0.001567",
    "n=17, sizes=[16384, 1024, 8192, 16384, 16384, 8192, 16384, 16384, 8192, 16384, 4096, 8192, 1024, 128, 16384, 1024, 512],bits=[8, 4, 8, 8, 2, 4, 8, 8, 8, 8, 8, 1, 1, 4, 2, 2, 1], start_hist=2, alpha=1.458, GH_bits=16, IP_bits=20, PATH_bits=12,  PATH_reg=16, hidden=12, num_heads=4, dropout=0.242, lr=0.000544",
    "n=17, sizes=[4096, 32768, 32768, 128, 2048, 8192, 8192, 32768, 32768, 2048, 512, 8192, 1024, 512, 512, 512, 512], bits=[8, 4, 8, 1, 4, 2, 1, 8, 4, 12, 12, 2, 1, 12, 12, 4, 1], start_hist=2, alpha=1.442, GH_bits=8, IP_bits=4, PATH_bits=24, PATH_reg=4, hidden=12, num_heads=4, dropout=0.236, lr=0.001095",
    "n=14, sizes=[8192, 16384, 16384, 16384, 16384, 256, 8192, 32768, 512, 16384, 16384, 512, 8192, 4096], bits=[4, 8, 2, 8, 2, 4, 8, 8, 12, 2, 8, 8, 4, 12], start_hist=3, alpha=1.498, GH_bits=12, IP_bits=24, PATH_bits=20, PATH_reg=64, hidden=12, num_heads=4, dropout=0.027, lr=0.001724"
]


# ---------------- Paths & GA Hyperparameters ----------------
MAIN_PATH        = pathlib.Path(__file__).parent.parent.resolve()
CHAMPSIM_DIR     = MAIN_PATH / "ChampSim"
GEN_CONFIG       = MAIN_PATH / "python/gen_config.h"
BASE_CONFIG_JSON = CHAMPSIM_DIR / "champsim_config.json"

CONFIGS_DIR      = MAIN_PATH / "python/ga_configs"
# predictor‐specific logs (accuracy CSV, JSON per gen)
LOG_DIR          = MAIN_PATH / "python/ga_logs" / PREDICTOR
# shared directory for storing GA state across predictors
STATE_DIR        = MAIN_PATH / "python/ga_logs"
STATE_FILE       = STATE_DIR / f"ga_state_{PREDICTOR}.json"

TRACE_DIR        = CHAMPSIM_DIR / "tracer"
ACC_DIR          = MAIN_PATH / "python/ga_logs"

# prepare directories
CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
# ensure the shared state directory exists
STATE_DIR.mkdir(parents=True, exist_ok=True)


SCALES_MIN, SCALES_MAX = 6, 20
BIT_BUDGET = 1024 * 64

SIZE_OPTS = [128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
BITS_OPTS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
GH_TOKEN_BITS_OPTS = [2, 4, 8, 12, 16, 20, 24]
IP_LSB_BITS_OPTS   = [2, 4, 8, 12, 16, 20, 24]
PATH_BITS_OPTS     = [2, 4, 8, 12, 16, 20, 24]
PATH_REG_OPTS      = [4, 8, 16, 32, 64, 128]
HIDDEN_OPTS   = [
    (6, 2), (6, 3),
    (8, 2), (8, 4),
    (9, 3),
    (10, 2), (10, 5),
    (12, 2), (12, 3), (12, 4), (12, 6),
    (14, 2), (14, 7),
    (15, 3), (15, 5),
    (16, 2), (16, 4), (16, 8),
    (18, 2), (18, 3), (18, 6), (18, 9),
    (20, 2), (20, 4), (20,5), (20, 10)
]

# New GA ranges for dropout and learning rate:
DROPOUT_RATE_RANGE = (0.0, 0.3)
LEARNING_RATE_RANGE = (0.00025, 0.002)

WARMUP_MIN, WARMUP_MAX = 250_000, 250_000
SIM_MIN,    SIM_MAX    = 250_000, 250_000
INIT_POP_SIZE = 64
POP_SIZE, GENERATIONS, TOUR_K = 16, 48, 4
INIT_MUT_RATE, MIN_MUT_RATE = 0.2, 0.2
BIT_PENALTY = 0.0001
DIVERSITY_PENALTY = 0.35
ELITE_COUNT = 1
START_HISTORY_MIN, START_HISTORY_MAX = 2, 7
ALPHA_MIN, ALPHA_MAX = 1.2, 1.8

# ---------------- Attention Memory Calculation ----------------
def calculate_attention_memory(total_input_bits, num_tokens, hidden_size, num_heads, bits_per_float=32):
    T, H, nh = num_tokens, hidden_size, num_heads
    proj_bits = T * H * bits_per_float
    interm_elems = (9 * T * H) + (2 * T * nh) + ((H * H) // nh) + H
    interm_bits = interm_elems * bits_per_float
    total_bits = proj_bits + interm_bits
    return {
        "raw_input_bits": total_input_bits,
        "projected_memory_bits": proj_bits,
        "projected_memory_bytes": proj_bits // 8,
        "intermediate_memory_bits": interm_bits,
        "intermediate_memory_bytes": interm_bits // 8,
        "total_memory_bits": total_bits,
        "total_memory_bytes": total_bits // 8,
    }

# ---------------- Helper Functions ----------------
def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)
    print(f"[save_state] Saved GA state to {STATE_FILE}")

def load_state():
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
    print(f"[load_state] Loaded GA state from {STATE_FILE}")
    return state

fitness_cache = {}

def individual_key(ind):
    n, sizes, bits, sh, a, gh, ip, ph, pr, hs, dr, lr = ind
    return (
        n,
        tuple(sizes),
        tuple(bits),
        sh,
        round(a, 3),
        gh,
        ip,
        ph,
        pr,
        hs,
        round(dr, 4),
        round(lr, 6)
    )

def parse_seed_str(s: str):
    """Parse one GA‐printout seed line into the (n, sizes, bits, …) tuple."""
    # grab the comma‐separated number lists
    n = int(re.search(r"\bn=(\d+)", s).group(1))
    sizes = list(map(int, re.search(r"sizes=\[([0-9,\s]+)\]", s).group(1).split(",")))
    bits  = list(map(int, re.search(r"bits=\[([0-9,\s]+)\]", s).group(1).split(",")))
    sh    = int(re.search(r"\bstart_hist=(\d+)", s).group(1))
    a     = float(re.search(r"\balpha=([\d.]+)", s).group(1))
    gh    = int(re.search(r"\bGH_bits=(\d+)", s).group(1))
    ip    = int(re.search(r"\bIP_bits=(\d+)", s).group(1))
    ph    = int(re.search(r"\bPATH_bits=(\d+)", s).group(1))
    pr    = int(re.search(r"\bPATH_reg=(\d+)", s).group(1))
    hidden_val = int(re.search(r"\bhidden=(\d+)", s).group(1))
    num_heads  = int(re.search(r"\bnum_heads=(\d+)", s).group(1))
    hs    = (hidden_val, num_heads)
    dr    = float(re.search(r"\bdropout=([\d.]+)", s).group(1))
    lr    = float(re.search(r"\blr=([\d.]+)", s).group(1))

    return (n, sizes, bits, sh, a, gh, ip, ph, pr, hs, dr, lr)

def smart_seeds():
    """Returns a list of parsed seeds from CUSTOM_SEED_STRINGS."""
    seeds = []
    for line in CUSTOM_SEED_STRINGS:
        try:
            seed = parse_seed_str(line)
            print(f"[smart_seeds] parsed seed: {seed}")
            seeds.append(seed)
        except Exception as e:
            print(f"[smart_seeds] failed to parse '{line}': {e}")
    return seeds

def estimate_runtime(avg_time_per_eval, curr_gen):
    remaining = (GENERATIONS - curr_gen) * POP_SIZE
    total_sec = remaining * avg_time_per_eval
    h, rem = divmod(total_sec, 3600)
    m, s = divmod(rem, 60)
    print(f"[estimate_runtime] Remaining runtime: {int(h)}h {int(m)}m {int(s)}s")

def predictor_raw_bits(n_scales, sizes, bits, gh, ip, ph, pr):
    local_bits = sum(size * bit for size, bit in zip(sizes, bits))
    return local_bits + gh + ip + ph + (pr * 64)

def is_valid(n_scales, sizes, bits, sh, a, gh, ip, ph, pr, hs, dr, lr):
    raw = predictor_raw_bits(n_scales, sizes, bits, gh, ip, ph, pr)
    tokens = n_scales + 3
    attn = calculate_attention_memory(raw, tokens, hs[0], hs[1])
    used = raw + attn["total_memory_bits"]
    return BIT_BUDGET*0.9 <= used <= BIT_BUDGET

def random_individual():
    while True:
        n = random.randint(SCALES_MIN, SCALES_MAX)
        s = [random.choice(SIZE_OPTS) for _ in range(n)]
        b = [random.choice(BITS_OPTS) for _ in range(n)]
        gh = random.choice(GH_TOKEN_BITS_OPTS)
        ip = random.choice(IP_LSB_BITS_OPTS)
        ph = random.choice(PATH_BITS_OPTS)
        pr = random.choice(PATH_REG_OPTS)
        sh = random.randint(START_HISTORY_MIN, START_HISTORY_MAX)
        a = random.uniform(ALPHA_MIN, ALPHA_MAX)
        hs = random.choice(HIDDEN_OPTS)
        dr = random.uniform(*DROPOUT_RATE_RANGE)
        lr = random.uniform(*LEARNING_RATE_RANGE)
        if is_valid(n, s, b, sh, a, gh, ip, ph, pr, hs, dr, lr):
            print(f"[random_individual] newcomer: n={n}, sizes={s}, bits={b}, "
                  f"sh={sh}, a={a:.3f}, GH={gh}, IP={ip}, PH={ph}, PR={pr}, "
                  f"HIDDEN_SIZE={hs[0]}, NUM_HEADS={hs[1]}, DR={dr:.3f}, LR={lr:.6f}")
            return (n, s, b, sh, a, gh, ip, ph, pr, hs, dr, lr)

def write_config(n, s, b, sh, a, gh, ip, ph, pr, hs, dr, lr):
    with open(GEN_CONFIG, "w") as f:
        f.write("#pragma once\n\n")
        f.write(f"#define GLOBAL_HISTORY_TOKEN_BITS {gh}\n")
        f.write(f"#define IP_LSB_TOKEN_BITS {ip}\n\n")
        f.write(f"constexpr int PATH_HISTORY_TOKEN_BITS = {ph};\n")
        f.write(f"constexpr int PATH_HISTORY_REG_SIZE   = {pr};\n\n")
        f.write(f"constexpr int NUM_LOCAL_HISTORY_SCALES = {n};\n")
        f.write("constexpr std::array<uint16_t, NUM_LOCAL_HISTORY_SCALES> "
                "LOCAL_HISTORY_TABLE_SIZES = { " + ", ".join(map(str, s)) + " };\n")
        f.write("constexpr std::array<uint8_t, NUM_LOCAL_HISTORY_SCALES> "
                "LOCAL_HISTORY_TABLE_BITS = { " + ", ".join(map(str, b)) + " };\n")
        f.write(f"constexpr int    START_HISTORY = {sh};\n")
        f.write(f"constexpr double ALPHA         = {a};\n")
        f.write(f"#define HIDDEN_SIZE {hs[0]}\n")
        f.write(f"#define NUM_HEADS {hs[1]}\n")
        f.write(f"#define DROPOUT_RATE {dr}\n")
        f.write(f"#define LEARNING_RATE {lr}\n")

    target = CHAMPSIM_DIR / "branch" / PREDICTOR
    target.mkdir(parents=True, exist_ok=True)
    (target / "gen_config.h").write_text(pathlib.Path(GEN_CONFIG).read_text())

def write_json_config():
    data = json.loads(pathlib.Path(BASE_CONFIG_JSON).read_text())
    data['ooo_cpu'][0]['branch_predictor'] = [PREDICTOR]
    data['executable_name'] = f"champsim_{PREDICTOR}"
    path = CONFIGS_DIR / f"ga_config_{PREDICTOR}.json"
    path.write_text(json.dumps(data, indent=4))
    return path

def compile_champsim(cfg_path):
    cwd = os.getcwd()
    os.chdir(CHAMPSIM_DIR)
    try:
        start = time.time()
        subprocess.run(["./config.sh", str(cfg_path)], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["make", "-j", "-s"], check=True, stdout=subprocess.DEVNULL)
        end = time.time()
        print(f"[compile_champsim] Compilation took {end - start:.2f} seconds")
    finally:
        os.chdir(cwd)

def run_trace(trace_file, warmup_instr, sim_instr):
    """
    Run a single ChampSim trace with a dynamic number of warmup
    and simulation instructions.
    """
    binary   = CHAMPSIM_DIR / "bin" / f"champsim_{PREDICTOR}"
    out_json = LOG_DIR / f"{PREDICTOR}_{trace_file}.json"
    cmd = [
        str(binary),
        "--warmup-instructions",     str(warmup_instr),
        "--simulation-instructions", str(sim_instr),
        "--json",                    str(out_json),
        str(TRACE_DIR / trace_file)
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        cores = json.loads(pathlib.Path(out_json).read_text())[0]['sim']['cores']
        accuracy = sum(c.get('Branch Prediction Accuracy', 0) for c in cores)
        return accuracy, len(cores)
    except subprocess.CalledProcessError as e:
        print(f"[run_trace] ERROR on {trace_file}: {e}")
        return 0.0, 0
    
def evaluate(ind, curr_gen, idx):
    """
    Evaluate one individual:
      - print generation & individual index
      - normalize any inner lists to tuples for hashing
      - compute dynamic instruction counts based on generation
      - write config, compile ChampSim
      - print memory footprint and config details
      - run all traces in parallel with those counts
      - compute and return adjusted fitness
    """
    # 1) Print which individual we’re evaluating
    print(f"[evaluate] Generation {curr_gen}, individual {idx+1}")

    # 2) Normalize lists → tuples for caching
    n, s, b, sh, a, gh, ip, ph, pr, hs, dr, lr = ind
    s  = tuple(s)
    b  = tuple(b)
    hs = tuple(hs) if isinstance(hs, (list, tuple)) else hs
    ind = (n, s, b, sh, a, gh, ip, ph, pr, hs, dr, lr)

    # 3) Compute dynamic instruction counts
    frac         = curr_gen / GENERATIONS
    warmup_instr = int(WARMUP_MIN + (WARMUP_MAX - WARMUP_MIN) * frac)
    sim_instr    = int(SIM_MIN    + (SIM_MAX    - SIM_MIN)    * frac)
    print(f"[evaluate] Gen {curr_gen}: warmup={warmup_instr}, sim={sim_instr}")

    # 4) Check cache
    key = individual_key(ind)
    if key in fitness_cache:
        print("found in cache")
        cached = fitness_cache[key]
        return (cached[0],) + ind + (0.0,)

    start_time = time.time()

    # 5) Write config and compile (always incremental)
    write_config(n, s, b, sh, a, gh, ip, ph, pr, hs, dr, lr)
    cfg_path = write_json_config()
    compile_champsim(cfg_path)

    # 6) Print memory footprint
    raw_bits    = predictor_raw_bits(n, s, b, gh, ip, ph, pr)
    attn        = calculate_attention_memory(raw_bits, n+3, hs[0], hs[1])
    total_bits  = raw_bits + attn["total_memory_bits"]
    total_bytes = total_bits // 8
    print(f"[evaluate] Memory: raw={raw_bits} bits, "
          f"attention={attn['total_memory_bits']} bits, "
          f"total={total_bits} bits ({total_bytes} bytes)")

    # 7) Print full config details
    print(f"[evaluate] Config -> n={n}, sizes={s}, bits={b}, "
          f"start_hist={sh}, alpha={a:.3f}, GH_bits={gh}, "
          f"IP_bits={ip}, PATH_bits={ph}, PATH_reg={pr}, "
          f"hidden={hs[0]}, heads={hs[1]}, "
          f"dropout={dr:.3f}, lr={lr:.6f}")

    # 8) Run traces in parallel
    traces      = [t for t in os.listdir(TRACE_DIR) if t.endswith('.xz')]
    total_acc   = 0.0
    total_cnt   = 0
    with concurrent.futures.ThreadPoolExecutor() as pool:
        for acc, cnt in pool.map(lambda t: run_trace(t, warmup_instr, sim_instr), traces):
            total_acc += acc
            total_cnt += cnt

    # 9) Clean up old logs
    for f in LOG_DIR.iterdir():
        if f.name != STATE_FILE.name:
            f.unlink()

    # 10) Compute fitness
    raw_fit = total_acc / total_cnt if total_cnt else 0.0
    penalty = max(0.0,
        (raw_bits + attn["total_memory_bits"] - 0.7 * BIT_BUDGET)
        / (0.3 * BIT_BUDGET)
    )
    adj_fit = raw_fit - BIT_PENALTY * penalty

    elapsed = time.time() - start_time
    print(f"[evaluate] Accuracy={raw_fit:.4f}, Adjusted fitness={adj_fit:.4f}, "
          f"time={elapsed:.2f}s\n")

    # 11) Cache & return
    fitness_cache[key] = (adj_fit,) + ind + (elapsed,)
    return (adj_fit,) + ind + (elapsed,)



def get_diversity_multipliers(population):
    freq = {}
    for ind in population:
        freq[individual_key(ind)] = freq.get(individual_key(ind), 0) + 1
    return [max(0.5, 1 - (freq[individual_key(ind)] - 1) * DIVERSITY_PENALTY)
            for ind in population]

def tournament_select(population, fitnesses):
    k = min(TOUR_K, len(population))
    contestants = random.sample(list(zip(population, fitnesses)), k=k)
    winner = max(contestants, key=lambda x: x[1])[0]
    return winner

def crossover(parent1, parent2, T, max_attempts=500):
    """
    One–point list crossover + blended continuous parameters.
    Now ensures size/bit vectors are lists before we concat.
    """
    def blend(a, b, span):
        return (a + b) / 2 + random.uniform(-span, span) * T

    for _ in range(max_attempts):
        # Unpack parents
        nA, sA, bA, shA, aA, ghA, ipA, phA, prA, hsA, drA, lrA = parent1
        nB, sB, bB, shB, aB, ghB, ipB, phB, prB, hsB, drB, lrB = parent2

        # Force list types so concat works
        sA = list(sA);  bA = list(bA)
        sB = list(sB);  bB = list(bB)

        # ----- Child 1 -----
        n1 = random.choice([nA, nB])
        split1 = random.randrange(1, n1) if n1 > 1 else 1

        sizes1 = (sA + [random.choice(SIZE_OPTS)] * n1)[:n1]
        sizes1 = sizes1[:split1] + (sB + [random.choice(SIZE_OPTS)] * n1)[:n1][split1:]
        bits1  = (bA + [random.choice(BITS_OPTS)] * n1)[:n1]
        bits1  = bits1[:split1] + (bB + [random.choice(BITS_OPTS)] * n1)[:n1][split1:]

        sh1 = random.choice([shA, shB])
        gh1 = random.choice([ghA, ghB])
        ip1 = random.choice([ipA, ipB])
        ph1 = random.choice([phA, phB])
        pr1 = random.choice([prA, prB])
        hs1 = random.choice([hsA, hsB])
        a1  = blend(aA, aB, 0.05)
        dr1 = blend(drA, drB, 0.01)
        lr1 = blend(lrA, lrB, 0.0001)
        child1 = (n1, sizes1, bits1, sh1, a1, gh1, ip1, ph1, pr1, hs1, dr1, lr1)

        # ----- Child 2 -----
        n2 = random.choice([nA, nB])
        split2 = random.randrange(1, n2) if n2 > 1 else 1

        sizes2 = (sB + [random.choice(SIZE_OPTS)] * n2)[:n2]
        sizes2 = sizes2[:split2] + (sA + [random.choice(SIZE_OPTS)] * n2)[:n2][split2:]
        bits2  = (bB + [random.choice(BITS_OPTS)] * n2)[:n2]
        bits2  = bits2[:split2] + (bA + [random.choice(BITS_OPTS)] * n2)[:n2][split2:]

        sh2 = random.choice([shA, shB])
        gh2 = random.choice([ghA, ghB])
        ip2 = random.choice([ipA, ipB])
        ph2 = random.choice([phA, phB])
        pr2 = random.choice([prA, prB])
        hs2 = random.choice([hsA, hsB])
        a2  = blend(aA, aB, 0.05)
        dr2 = blend(drA, drB, 0.01)
        lr2 = blend(lrA, lrB, 0.0001)
        child2 = (n2, sizes2, bits2, sh2, a2, gh2, ip2, ph2, pr2, hs2, dr2, lr2)

        if is_valid(*child1) and is_valid(*child2):
            return child1, child2

    # Fallback
    return parent1, parent2

def mutate(ind, T, base_mut_rate=0.1, max_attempts=500):
    """
    Mutate `ind`; ensures `sizes`/`bits` start as lists so padding/truncation works.
    """
    for _ in range(max_attempts):
        n, sizes, bits, sh, a, gh, ip, ph, pr, hs, dr, lr = ind

        # Coerce to lists
        sizes = list(sizes)
        bits   = list(bits)

        mut_rate = base_mut_rate * (0.5 + T)

        # maybe change number of scales
        if random.random() < mut_rate:
            n = random.randint(SCALES_MIN, SCALES_MAX)

        # pad/truncate to n
        sizes = (sizes + [random.choice(SIZE_OPTS) for _ in range(n)])[:n]
        bits   = (bits   + [random.choice(BITS_OPTS)  for _ in range(n)])[:n]

        # per‐scale mutations
        for i in range(n):
            if random.random() < mut_rate:
                sizes[i] = random.choice(SIZE_OPTS)
            if random.random() < mut_rate:
                bits[i] = random.choice(BITS_OPTS)

        # discrete params
        if random.random() < mut_rate:
            sh = random.randint(START_HISTORY_MIN, START_HISTORY_MAX)
        if random.random() < mut_rate:
            gh = random.choice(GH_TOKEN_BITS_OPTS)
        if random.random() < mut_rate:
            ip = random.choice(IP_LSB_BITS_OPTS)
        if random.random() < mut_rate:
            ph = random.choice(PATH_BITS_OPTS)
        if random.random() < mut_rate:
            pr = random.choice(PATH_REG_OPTS)
        if random.random() < mut_rate:
            hs = random.choice(HIDDEN_OPTS)

        # continuous params
        a  += random.uniform(-0.05,  0.05)  * T
        dr += random.uniform(-0.01,  0.01)  * T
        lr += random.uniform(-0.0001, 0.0001) * T
        dr = min(max(dr, DROPOUT_RATE_RANGE[0]), DROPOUT_RATE_RANGE[1])
        lr = min(max(lr, LEARNING_RATE_RANGE[0]), LEARNING_RATE_RANGE[1])

        candidate = (n, sizes, bits, sh, a, gh, ip, ph, pr, hs, dr, lr)
        if is_valid(*candidate):
            return candidate

    return ind


if __name__ == "__main__":
    # Define the CSV log file and JSON log file paths with predictor as part of the filename
    CSV_LOG = ACC_DIR / f"acc_log_{PREDICTOR}.csv"
    if not CSV_LOG.exists():
        with open(CSV_LOG, "w", newline="") as tmp_csv:
            csv.writer(tmp_csv).writerow(["generation", "average_fitness", "best_fitness"])

    JSON_LOG = LOG_DIR / f"ga_log_{PREDICTOR}.json"
    if JSON_LOG.exists():
        with open(JSON_LOG, "r") as jf:
            json_logs = json.load(jf).get("generations", [])
    else:
        json_logs = []

    # load or initialize state
    if STATE_FILE.exists():
        state = load_state()
        gen = state.get("generation", 0)
        population = [tuple(ind) for ind in state.get("population", [])]
        acc_log = state.get("accuracy_log", [])
        tot_time = state.get("total_eval_time", 0.0)
        ev_count = state.get("eval_count", 0)
        print(f"[main] Resuming generation {gen}, population size {len(population)}")
    else:
        population = smart_seeds()
        while len(population) < INIT_POP_SIZE:
            population.append(random_individual())
        gen, acc_log, tot_time, ev_count = 0, [], 0.0, 0

    # Initialize annealing variables
    last_reset_gen = gen
    global_best_fit = 0.0
    reset_period = 40

    for curr_gen in range(gen, GENERATIONS):
        # determine population size for this generation
        if curr_gen == 0:
            curr_pop_size = int(INIT_POP_SIZE)
        elif curr_gen == 1:
            curr_pop_size = int((INIT_POP_SIZE + POP_SIZE) / 2)
        else:
            curr_pop_size = int(POP_SIZE)

        print(f"\n[main] Generation {curr_gen} — pop size = {curr_pop_size}")
        mut_rate = MIN_MUT_RATE + (INIT_MUT_RATE - MIN_MUT_RATE) * (1 - curr_gen / GENERATIONS)

        # 1) Evaluate
        results = [evaluate(ind, curr_gen, idx)for idx, ind in enumerate(population[:curr_pop_size])]
        fits = [res[0] for res in results]
        population = [tuple(res[1:13]) for res in results]
        eval_times = [res[-1] for res in results]
        tot_time += sum(eval_times)
        ev_count += len(eval_times)
        estimate_runtime(tot_time / ev_count, curr_gen)

        # 2) Logging
        avg_fit = sum(fits) / len(fits)
        best_fit = max(fits)
        print(f"[main] Avg fit={avg_fit:.4f}, Best fit={best_fit:.4f}")
        with open(CSV_LOG, "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([curr_gen, avg_fit, best_fit])

        # 3) JSON log
        sorted_pop = sorted(zip(fits, population), key=lambda x: x[0], reverse=True)
        best_score, best_model = sorted_pop[0]
        gen_log_entry = {
            "generation": curr_gen,
            "average_fit": avg_fit,
            "best_fit": best_fit,
            "best_model": {
                "score":       best_score,
                "n":           best_model[0],
                "sizes":       best_model[1],
                "bits":        best_model[2],
                "start_hist":  best_model[3],
                "alpha":       best_model[4],
                "GH_bits":     best_model[5],
                "IP_bits":     best_model[6],
                "PATH_bits":   best_model[7],
                "PATH_reg":    best_model[8],
                "hidden_size": best_model[9][0],
                "num_heads":   best_model[9][1],
                "dropout":     best_model[10],
                "lr":          best_model[11],
            }
        }
        json_logs.append(gen_log_entry)
        with open(JSON_LOG, "w") as jf:
            json.dump({"generations": json_logs}, jf, indent=4)

        # 4) Annealing reset
        if best_fit > global_best_fit * 1.01:
            print("[annealing] Significant jump detected, resetting annealing temperature")
            last_reset_gen = curr_gen
            global_best_fit = best_fit

        anneal_temp = max(0.1, 1 - (curr_gen - last_reset_gen) / reset_period)
        print(f"[annealing] anneal_temp = {anneal_temp:.3f}")

        # 5) Selection & reserve for immigrants
        num_imm = max(1, int(0.1 * curr_pop_size))
        survivors = curr_pop_size - num_imm
        n_elites = min(ELITE_COUNT, survivors)
        elites = [ind for _, ind in sorted_pop[:n_elites]]
        # Mutate the elite individuals lightly before adding them
        mutated_elites = [mutate(elite, anneal_temp, mut_rate * 0.5) for elite in elites]
        print(f"[selection] elites kept (after mutation): {mutated_elites}")
        next_pop = mutated_elites.copy()

        # 6) Immigration
        print(f"[immigration] adding {num_imm} new random individuals")
        for _ in range(num_imm):
            next_pop.append(random_individual())

        # 7) Reproduction until full
        print(f"[repro] Starting reproduction: have {len(next_pop)} survivors + immigrants, target = {curr_pop_size}")
        adjusted = [f * m for f, m in zip(fits, get_diversity_multipliers(population))]
        while len(next_pop) < curr_pop_size:
            p1 = tournament_select(population, adjusted)
            p2 = tournament_select(population, adjusted)
            print(f"[repro] parents: {p1}, {p2}")
            c1, c2 = crossover(p1, p2, anneal_temp)
            m1 = mutate(c1, anneal_temp, mut_rate)
            m2 = mutate(c2, anneal_temp, mut_rate)
            print(f"[repro] offspring: {m1}, {m2}")
            next_pop.extend([m1, m2])
        print(f"[repro] Finished reproduction: next_pop size = {len(next_pop)}")

        # 8) Truncate & prepare next generation
        print(f"[main] Truncating population from {len(next_pop)} down to {curr_pop_size}")
        population = next_pop[:curr_pop_size]
        print(f"[main] Population ready for next gen: size = {len(population)}")


        # 9) Save GA state
        state = {
            "generation":      curr_gen + 1,
            "population":      [list(ind) for ind in population],
            "accuracy_log":    [],
            "total_eval_time": tot_time,
            "eval_count":      ev_count
        }
        save_state(state)

    # Final evaluation & cleanup...
    print("\n[main] Final evaluation of all individuals")
    final_results = [
        evaluate(ind, GENERATIONS - 1, idx)
        for idx, ind in enumerate(population)
    ]
    best = max(final_results, key=lambda x: x[0])
    print(f"[main] Best config: fit={best[0]:.4f}, params={best[1:13]}")

    final_best = {
        "final_best": {
            "score":        best[0],
            "n":            best[1],
            "sizes":        best[2],
            "bits":         best[3],
            "start_hist":   best[4],
            "alpha":        best[5],
            "GH_bits":      best[6],
            "IP_bits":      best[7],
            "PATH_bits":    best[8],
            "PATH_reg":     best[9],
            "hidden_size":  best[10][0],
            "num_heads":    best[10][1],
            "dropout":      best[11],
            "lr":           best[12],
            "evaluation_time": best[13]
        }
    }
    with open(JSON_LOG, "w") as jf:
        json.dump({"generations": json_logs, **final_best}, jf, indent=4)
