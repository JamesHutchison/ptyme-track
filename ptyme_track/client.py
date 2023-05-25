import datetime
import hashlib
import json
import logging
import time
import urllib.request
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Iterator, List, Union

from ptyme_track.ptyme_env import (
    PTYME_TRACK_DIR,
    PTYME_WATCH_INTERVAL_MIN,
    SERVER_URL,
)
from ptyme_track.server import sign_time
from ptyme_track.signed_time import SignedTime

CUR_TIMES_FILE = Path(".cur_times")
CUR_TIMES_PATH = Path(PTYME_TRACK_DIR) / CUR_TIMES_FILE
COUNT_MOD = 10  # when to take a small break when hashing files

logger = logging.getLogger(__name__)


class PtymeClient:
    def __init__(self, server_url: str, watched_dirs: List[str]) -> None:
        self.server_url = server_url
        self._file_hash_cache: Dict[str, bytes] = {}
        self._last_update: Union[float, None] = None
        self._watched_dirs = watched_dirs

    def run_forever(self) -> None:
        print("Starting ptyme-track", flush=True)
        prev_files_hash = None
        stopped = False
        rolling_hash = hashlib.md5()
        while True:
            start = time.time()
            for watched_dir in self._get_watched_dirs():
                rolling_hash.update(self._get_files_hash(watched_dir).encode("utf-8"))
            self._last_update = start
            files_hash = rolling_hash.hexdigest()
            if files_hash != prev_files_hash:
                self.record_time(files_hash)
                prev_files_hash = files_hash
            else:
                if not stopped:
                    self.record_stop(files_hash)
                stopped = True
            end = time.time()
            logger.debug(f"Hash took {(end - start):.1f} seconds")
            next_time = start + PTYME_WATCH_INTERVAL_MIN * 60
            cur_time = time.time()
            if cur_time < next_time:
                time.sleep(next_time - cur_time)

    def _get_watched_dirs(self) -> Iterator[Path]:
        for path in self._watched_dirs:
            yield Path(path)

    def _get_files_hash(self, watched_dir: Path) -> str:
        # get the hash of all the files in the watched directory
        # use the built-in hashlib module
        count = 0
        running_hash = hashlib.md5()
        last_update = self._last_update
        start = time.time()
        if str(watched_dir).startswith(".") and str(watched_dir) not in (".", ".."):
            glob = "**/*"
        else:
            glob = "[!.]*/**/[!.]*"
        for file in watched_dir.glob(glob):
            if file.is_file() and not str(file.name).startswith("."):
                if not last_update or file.stat().st_mtime > last_update:
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
            logger.info("Creating {PTYME_TRACK_DIR}")
            track_dir.mkdir()
        git_ignore = track_dir / ".gitignore"
        if not git_ignore.exists():
            git_ignore.write_text(str(CUR_TIMES_FILE))

    def _retrieve_signed_time(self) -> SignedTime:
        # retrieve the current time from the server using the built-in urllib module
        response = urllib.request.urlopen(SERVER_URL)
        logger.debug("Got signed time")
        return json.loads(response.read().decode("utf-8"))

    def record_time(self, files_hash: str, stop: bool = False) -> None:
        signed_time = self._retrieve_signed_time()
        self._record_time(signed_time, files_hash, stop)

    def record_stop(self, files_hash: str) -> None:
        self.record_time(files_hash, stop=True)

    def _record_time(self, signed_time: SignedTime, hash: str, stop: bool) -> None:
        cur_time = datetime.datetime.utcnow()
        time_as_str = cur_time.strftime("%Y-%m-%d %H:%M:%S")
        with CUR_TIMES_PATH.open("a") as cur_time_log:
            json.dump(
                {"time": time_as_str, "signed_time": asdict(signed_time), "hash": hash, "stop": stop},
                cur_time_log,
            )
            cur_time_log.write("\n")


class StandalonePtymeClient(PtymeClient):
    def __init__(self, watched_dirs: List[str]) -> None:
        super().__init__("", watched_dirs)

    def _retrieve_signed_time(self) -> SignedTime:
        return sign_time()
