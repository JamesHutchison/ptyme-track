import argparse
import json
import logging
import subprocess
from datetime import timedelta
from pathlib import Path
from shutil import which

from ptyme_track.cement import cement_cur_times
from ptyme_track.client import PtymeClient, StandalonePtymeClient
from ptyme_track.git_ci_diff import display_git_ci_diff_times
from ptyme_track.ptyme_env import (
    PTYME_IGNORED_DIRS,
    PTYME_TRACK_BASE_BRANCH,
    PTYME_TRACK_FEATURE_BRANCH,
    PTYME_WATCHED_DIRS,
    SERVER_URL,
)
from ptyme_track.secret import get_secret

logging.basicConfig(level=logging.INFO)


def main() -> None:
    parser = argparse.ArgumentParser(description="ptyme_track")
    parser.add_argument(
        "--generate-secret", action="store_true", help="Generate a secret and update gitignore"
    )
    parser.add_argument("--server", action="store_true", help="Run as server")
    parser.add_argument("--client", action="store_true", help="Run as client")
    # cement takes a parameter which is the name of the file to cement to
    parser.add_argument("--cement", help="Cement to file")
    # time-blocks takes a file to extract the time blocks from
    parser.add_argument("--time-blocks", help="Extract time blocks from file")
    parser.add_argument(
        "--standalone", action="store_true", help="Run as both a client and a server"
    )
    parser.add_argument(
        "--git-ci-times", action="store_true", help="Get the current times on this PR from git"
    )

    args = parser.parse_args()

    if args.server:
        from ptyme_track.server import run_forever

        run_forever()
    if args.cement:
        if which("git"):
            git_branch = subprocess.getoutput("git branch --show-current").strip() or None
        else:
            git_branch = None
        cement_cur_times(args.cement, git_branch=git_branch)
        return
    if args.git_ci_times:
        base_branch = PTYME_TRACK_BASE_BRANCH
        if not base_branch:
            raise Exception("PTYME_TRACK_BASE_BRANCH environment variable not set.")
        feature_branch = PTYME_TRACK_FEATURE_BRANCH
        display_git_ci_diff_times(base_branch, feature_branch)
        return
    if args.generate_secret:
        from ptyme_track.server import generate_secret

        generate_secret()
        return
    if args.time_blocks:
        from ptyme_track.time_blocks import get_time_blocks

        time_blocks = get_time_blocks(Path(args.time_blocks), get_secret())
        total_time = timedelta(minutes=0)
        for block in time_blocks:
            total_time += block.duration
            print(
                json.dumps(
                    {
                        "start": str(block.start_time),
                        "end": str(block.end_time),
                        "duration": str(block.duration),
                    }
                )
            )
        print("Total duration: ", total_time)
        return
    watched_dirs = PTYME_WATCHED_DIRS.split(":")
    ignored_dirs = PTYME_IGNORED_DIRS.split(":")
    if args.client:
        client = PtymeClient(SERVER_URL, watched_dirs, ignored_dirs)
    elif args.standalone:
        client = StandalonePtymeClient(watched_dirs, ignored_dirs)
    else:
        parser.print_help()
        return
    client.prep_ptyme_dir()
    client.run_forever()


if __name__ == "__main__":
    main()
