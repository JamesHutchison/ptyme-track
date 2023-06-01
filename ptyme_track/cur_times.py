from pathlib import Path

from ptyme_track.ptyme_env import PTYME_TRACK_DIR

CUR_TIMES_FILE = Path(".cur_times")
CUR_TIMES_PATH = Path(PTYME_TRACK_DIR) / CUR_TIMES_FILE
CEMENTED_PATH = Path(PTYME_TRACK_DIR) / ".cemented"
