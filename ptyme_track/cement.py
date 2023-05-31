from pathlib import Path
from typing import Union

from ptyme_track.cur_times import CUR_TIMES_PATH
from ptyme_track.ptyme_env import PTYME_TRACK_DIR


def cement_cur_times(
    target_file: Union[Path, str], cur_times_path: Path = CUR_TIMES_PATH
) -> None:
    """
    Cement the current times saved in the temporary file

    :param target_file: File to cement to, relative to the PTYME_TRACK_DIR
    """
    with cur_times_path.open() as f:
        cur_times = f.read()
    target_file = Path(PTYME_TRACK_DIR) / target_file
    with target_file.open("a") as f:
        f.write(cur_times)
    cur_times_path.open("w").close()
