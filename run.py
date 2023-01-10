from datetime import datetime
from argparse import ArgumentParser
from subprocess import run

parser = ArgumentParser(prog="P0K3RB0TS", description="Runs the PokerBots engine.")
parser.add_argument('path1')
parser.add_argument('path2')
parser.add_argument('-n', '--rounds', type=int, default=1000)
parser.add_argument('-c', '--chips', type=int, default=400)
parser.add_argument('-b', '--big', type=int, default=2)
parser.add_argument('-s', '--small', type=int, default=1)
parser.add_argument('-o', '--out')


args = parser.parse_args()
name1 = args.path1.split("/")[-1]
name2 = args.path2.split("/")[-1]

if name1 == name2:
    name1 += " (1)"
    name2 += " (2)"

if args.out is None:
    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d-%H%M%S")
    args.out = "logs/" + name1 + " vs. " + name2 + "-" + dt_string



config = f"""# PARAMETERS TO CONTROL THE BEHAVIOR OF THE GAME ENGINE
# DO NOT REMOVE OR RENAME THIS FILE
PLAYER_1_NAME = "{name1}"
PLAYER_1_PATH = "{args.path1}"
# NO TRAILING SLASHES ARE ALLOWED IN PATHS
PLAYER_2_NAME = "{name2}"
PLAYER_2_PATH = "{args.path2}"
# GAME PROGRESS IS RECORDED HERE
GAME_LOG_FILENAME = "{args.out}"
# PLAYER_LOG_SIZE_LIMIT IS IN BYTES
PLAYER_LOG_SIZE_LIMIT = 524288
# STARTING_GAME_CLOCK AND TIMEOUTS ARE IN SECONDS
ENFORCE_GAME_CLOCK = True
STARTING_GAME_CLOCK = 30.
BUILD_TIMEOUT = 10.
CONNECT_TIMEOUT = 10.
# THE GAME VARIANT FIXES THE PARAMETERS BELOW
# CHANGE ONLY FOR TRAINING OR EXPERIMENTATION
NUM_ROUNDS = {args.rounds}
STARTING_STACK = {args.chips}
BIG_BLIND = {args.big}
SMALL_BLIND = {args.small}
"""

with open("config.py", "w") as f:
    f.write(config)

run("python engine.py")