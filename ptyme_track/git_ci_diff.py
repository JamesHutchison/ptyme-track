import datetime
import json
import os
import re
import subprocess
from shutil import which
from typing import List, Optional, Union

from ptyme_track.time_blocks import build_time_blocks_from_records


def display_git_ci_diff_times(base_branch: str) -> None:
    if os.name == "nt":
        raise Exception("Windows is not supported.")
    if not which("git"):
        raise Exception("Git does not appear to be installed.")
    output = subprocess.getoutput(
        f"git diff --unified=0 --output-indicator-new=+ {base_branch} -- .ptyme_track | grep '^+'"
    )
    user: Union[str, None] = None
    records: Union[list, None] = None

    def display_user_info(user: Optional[str], records: Optional[List[dict]]) -> None:
        if not user or records is None:
            return
        time_blocks = build_time_blocks_from_records(
            records, buffer=datetime.timedelta(minutes=5)
        )
        total_time = datetime.timedelta(minutes=0)
        for block in time_blocks:
            total_time += block.duration
        print(f"{user}: {total_time}")

    print("Ptyme Track time logged:")

    for line in output.splitlines():
        if line.startswith("+++"):
            match = re.match(r"\+\+\+ .*/(\S+)$", line)
            if match:
                display_user_info(user, records)
                user = match.group(1)
                records = []
        elif line.startswith("+"):
            if records is not None:
                record = json.loads(line[1:])
                records.append(record)
    display_user_info(user, records)
