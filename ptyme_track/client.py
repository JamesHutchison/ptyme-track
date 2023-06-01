from __future__ import annotations

import datetime
import hashlib
import itertools
import json
import logging
import time
import urllib.request
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple, Union

from ptyme_track.cur_times import CEMENTED_PATH, CUR_TIMES_PATH
from ptyme_track.ptyme_env import (
    PTYME_TRACK_DIR,
    PTYME_WATCH_INTERVAL_MIN,
)
from ptyme_track.server import sign_time
from ptyme_track.signed_time import SignedTime

COUNT_MOD = 10  # when to take a small break when hashing files
IGNORED_COUNT_MOD = 1000  # when to take a small break when ignoring files

logger = logging.getLogger(__name__)


class PtymeClient:
    def __init__(
        self,
        server_url: str,
        watched_dirs: List[str],
        ignored_dirs: List[str],
        cur_times: Path = CUR_TIMES_PATH,
    ) -> None:
        self.server_url = server_url
        self._file_hash_cache: Dict[str, bytes] = {}
        self._last_update: Union[float, None] = None
        self._watched_dirs = watched_dirs
        self._cur_times = cur_times
        self._ignored_dirs = ignored_dirs

    def run_forever(self, cemented_file=Path(CEMENTED_PATH)) -> None:
        print("Starting ptyme-track", flush=True)
        prev_files_hash = None
        stopped = False
        freshly_cemented = False
        while True:
            if cemented_file.exists():
                prev_files_hash = cemented_file.read_text().strip()
                stopped = True
                cemented_file.unlink()
                freshly_cemented = True
            prev_files_hash, stopped = self._run_loop(prev_files_hash, stopped, freshly_cemented)
            freshly_cemented = False

    def _run_loop(
        self, prev_files_hash: Optional[str], stopped: bool, freshly_cemented: bool = False
    ) -> Tuple[Union[str, None], bool]:
        start = time.time()
        files_hash = self._get_files_hash_for_watched_dirs()
        # _last_update should be set BEFORE the hash is calculated to avoid a race condition
        self._last_update = start
        if not freshly_cemented:
            stopped = self._record_time_or_stop(files_hash, prev_files_hash, stopped)
        prev_files_hash = files_hash
        end = time.time()
        logger.debug(f"Hash took {(end - start):.1f} seconds")
        next_time = start + PTYME_WATCH_INTERVAL_MIN * 60
        cur_time = time.time()
        if cur_time < next_time:
            self._perform_sleep(next_time - cur_time)
        return prev_files_hash, stopped

    def _get_files_hash_for_watched_dirs(self) -> str:
        rolling_hash = hashlib.md5()
        for watched_dir in self._get_watched_dirs():
            result = self._get_files_hash(watched_dir)
            if result:
                rolling_hash.update(result.encode("utf-8"))
        return rolling_hash.hexdigest()

    def _record_time_or_stop(
        self, files_hash: str, prev_files_hash: Optional[str], stopped: bool
    ) -> bool:
        if files_hash != prev_files_hash:
            self._record_time(files_hash)
            return False
        if not stopped:
            self._record_stop(files_hash)
        return True

    def _perform_sleep(self, duration: float) -> None:
        time.sleep(duration)

    def _get_watched_dirs(self) -> Iterator[Path]:
        for path in self._watched_dirs:
            yield Path(path)

    def _get_files_hash(self, watched_dir: Path) -> Union[None, str]:
        # get the hash of all the files in the watched directory
        # use the built-in hashlib module
        count = 0
        ignored_count = 0
        running_hash = hashlib.md5()
        last_update = self._last_update
        start = time.time()
        local_glob = "[!.]*"
        glob = "[!.]*/**/[!.]*"
        for file in itertools.chain(watched_dir.glob(local_glob), watched_dir.glob(glob)):
            if file.is_file() and not str(file.name).startswith("."):
                for ignored_dir in self._ignored_dirs:
                    if ignored_dir in str(file):
                        ignored_count += 1
                        if ignored_count % IGNORED_COUNT_MOD == 0:
                            time.sleep(0.01)
                        break
                else:
                    if (
                        not last_update
                        or str(file) not in self._file_hash_cache
                        or file.stat().st_mtime > last_update
                    ):
                        count += 1
                        if count % COUNT_MOD == 0:
                            time.sleep(0.01)
                        with file.open("rb") as f:
                            file_hash = hashlib.md5()
                            file_hash.update(f.read())
                        self._file_hash_cache[str(file)] = file_hash.hexdigest().encode("utf-8")
                    running_hash.update(self._file_hash_cache[str(file)])
        logger.debug(f"Hashed {count} files in {(time.time() - start):.1f} seconds")
        return running_hash.hexdigest()

    def prep_ptyme_dir(self) -> None:
        track_dir = Path(PTYME_TRACK_DIR)
        if not track_dir.exists():
            logger.info(f"Creating {PTYME_TRACK_DIR}")
            track_dir.mkdir()
        git_ignore = track_dir / ".gitignore"
        if not git_ignore.exists():
            git_ignore.write_text("!.gitignore\n.*")

    def _retrieve_signed_time(self) -> SignedTime:
        # retrieve the current time from the server using the built-in urllib module
        response = urllib.request.urlopen(self.server_url)
        logger.debug("Got signed time")
        return json.loads(response.read().decode("utf-8"))

    def _record_time(self, files_hash: str, stop: bool = False) -> None:
        signed_time = self._retrieve_signed_time()
        self._perform_record_time(signed_time, files_hash, stop)

    def _record_stop(self, files_hash: str) -> None:
        self._record_time(files_hash, stop=True)

    def _perform_record_time(self, signed_time: SignedTime, hash: str, stop: bool) -> None:
        cur_time = datetime.datetime.utcnow()
        time_as_str = cur_time.strftime("%Y-%m-%d %H:%M:%S")
        with self._cur_times.open("a") as cur_time_log:
            json.dump(
                {
                    "time": time_as_str,
                    "signed_time": asdict(signed_time),
                    "hash": hash,
                    "stop": stop,
                },
                cur_time_log,
            )
            cur_time_log.write("\n")


class StandalonePtymeClient(PtymeClient):
    def __init__(self, watched_dirs: List[str], ignored_dirs: List[str]) -> None:
        super().__init__("", watched_dirs, ignored_dirs)

    def _retrieve_signed_time(self) -> SignedTime:
        return sign_time()
