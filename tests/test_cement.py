import json
from pathlib import Path

import pytest

from ptyme_track.cement import cement_cur_times


class TestCementCurrentTimes:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.source_file = tmp_path / "source_file"
        self.source_file.write_text('{"new": "value"}\n')
        self.target_file = tmp_path / "target_file"
        self.target_file.write_text('{"existing": "value"}\n')
        self.cement_path = tmp_path / "cement"

    def test_cement_cur_times_appends_to_file(self) -> None:
        cement_cur_times(self.target_file, self.source_file, self.cement_path)

        assert (
            self.target_file.read_text()
            == '{"existing": "value"}\n{"new": "value", "git-branch": null}\n'
        )

    def test_cement_cur_times_adds_git_branch(self) -> None:
        cement_cur_times(
            self.target_file, self.source_file, self.cement_path, git_branch="git_branch"
        )

        assert (
            self.target_file.read_text()
            == '{"existing": "value"}\n{"new": "value", "git-branch": "git_branch"}\n'
        )

    def test_cement_writes_cement_file_when_hash_provided(self) -> None:
        self.source_file.write_text(json.dumps({"hash": "abc123"}))
        cement_cur_times(
            self.target_file, self.source_file, self.cement_path, git_branch="git_branch"
        )

        assert self.cement_path.exists()
        assert self.cement_path.read_text() == "abc123"
