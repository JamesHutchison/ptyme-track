import datetime
import json
import os
import re
import subprocess
from shutil import which
from typing import List, Optional, Union

from ptyme_track.time_blocks import build_time_blocks_from_records


def display_git_ci_diff_times(base_branch: str, feature_branch: Optional[str] = None) -> None:
    if os.name == "nt":
        raise Exception("Windows is not supported.")
    if not which("git"):
        raise Exception("Git does not appear to be installed.")
    output = subprocess.getoutput(
        f"git diff --unified=0 --output-indicator-new=+ {base_branch} -- .ptyme_track | grep '^+'"
    )
    user: Union[str, None] = None
    records: Union[list, None] = None
    branch_records: Union[list, None] = None

    def display_user_info(
        user: Optional[str], records: Optional[List[dict]], branch_records: Optional[List[dict]]
    ) -> None:
        if not user or records is None:
            return
        time_blocks = build_time_blocks_from_records(
            records, buffer=datetime.timedelta(minutes=5)
        )
        total_time = datetime.timedelta(minutes=0)
        for block in time_blocks:
            total_time += block.duration

        # this is plugged into javascript, so remove backticks
        user_display = user.replace("`", "")

        if branch_records:
            total_branch_time = datetime.timedelta(minutes=0)
            branch_time_blocks = build_time_blocks_from_records(
                branch_records, buffer=datetime.timedelta(minutes=5)
            )
            for block in branch_time_blocks:
                total_branch_time += block.duration
            print(f"{user_display}: {total_branch_time} [{total_time} across all branches]")
        else:
            print(f"{user_display}: {total_time}")

    print("Ptyme Track total time logged:")

    for line in output.splitlines():
        if line.startswith("+++"):
            match = re.match(r"\+\+\+ .*/(\S+)$", line)
            if match:
                display_user_info(user, records, branch_records)
                user = match.group(1)
                if user == ".gitignore":
                    user = None
                    records = None
                    branch_records = None
                else:
                    records = []
                    branch_records = []
        elif line.startswith("+"):
            if records is not None:
                record: dict = json.loads(line[1:])
                records.append(record)
                if (
                    feature_branch
                    and branch_records is not None
                    and record.get("git-branch") == feature_branch
                ):
                    branch_records.append(record)
    display_user_info(user, records, branch_records)
