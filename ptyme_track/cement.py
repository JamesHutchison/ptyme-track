import json
from pathlib import Path
from typing import Optional, Union

from ptyme_track.cur_times import CEMENTED_PATH, CUR_TIMES_PATH
from ptyme_track.ptyme_env import PTYME_TRACK_DIR


def cement_cur_times(
    target_file: Union[Path, str],
    cur_times_path: Path = CUR_TIMES_PATH,
    cement_path: Path = CEMENTED_PATH,
    git_branch: Optional[str] = None,
) -> None:
    """
    Cement the current times saved in the temporary file

    :param target_file: File to cement to, relative to the PTYME_TRACK_DIR
    """
    with cur_times_path.open() as f:
        cur_times = f.readlines()
    target_file = Path(PTYME_TRACK_DIR) / target_file
    record = None
    with target_file.open("a") as f:
        for line in cur_times:
            record = json.loads(line)
            record["git-branch"] = git_branch
            f.write(json.dumps(record) + "\n")
    cur_times_path.open("w").close()

    if record and record.get("hash"):
        last_hash = record["hash"]
        cement_path.write_text(last_hash)
