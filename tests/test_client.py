import datetime
import hashlib
import json
from pathlib import Path
from unittest import mock

import freezegun
import pytest
from pytest_mock import MockerFixture

from ptyme_track.client import PtymeClient
from ptyme_track.signed_time import SignedTime


class PtymeClientTestBase:
    @pytest.fixture(autouse=True)
    def setup(self, mocker: MockerFixture, tmp_path: Path) -> None:
        self._sleep_mock = mocker.patch.object(PtymeClient, "_perform_sleep")
        self._mock_signed_time = mocker.patch.object(PtymeClient, "_retrieve_signed_time")
        self._watched_path = tmp_path / "watched"
        self._watched_dirs = [str(self._watched_path)]
        self._ptyme_track_dir = tmp_path / ".ptyme-track"
        self._cur_times_path = self._ptyme_track_dir / ".cur_times"


class TestPtymeClient:
    def test_run_forever_feeds_run_loop_returned_values(self, mocker: MockerFixture) -> None:
        new_hash = "new hash"
        stopped = False
        run_loop_mock = mocker.patch.object(
            PtymeClient,
            "_run_loop",
            side_effect=[(new_hash, stopped), StopIteration],
        )

        client = PtymeClient("", ["a directory"], [], Path(""))

        with pytest.raises(StopIteration):
            client.run_forever()

        assert run_loop_mock.call_count == 2
        run_loop_mock.assert_called_with(new_hash, stopped)

    class TestRunLoop(PtymeClientTestBase):
        def test_with_empty_watched_dir(self, mocker: MockerFixture) -> None:
            record_time_mock = mocker.patch.object(PtymeClient, "_record_time")

            client = PtymeClient("", self._watched_dirs, [], self._cur_times_path)
            client._run_loop(None, False)

            record_time_mock.assert_called_once_with(mock.ANY)

        def test_when_stopping_then_records_stop(self, mocker: MockerFixture) -> None:
            prev_hash = "prev hash"

            record_time_mock = mocker.patch.object(PtymeClient, "_record_time")
            mocker.patch.object(
                PtymeClient, "_get_files_hash_for_watched_dirs", return_value=prev_hash
            )

            client = PtymeClient("", self._watched_dirs, [], self._cur_times_path)
            client._run_loop(prev_hash, False)

            record_time_mock.assert_called_once_with(mock.ANY, stop=True)

        def test_when_already_stopped_does_not_record(self, mocker: MockerFixture) -> None:
            prev_hash = "prev hash"

            record_time_mock = mocker.patch.object(PtymeClient, "_record_time")
            mocker.patch.object(
                PtymeClient, "_get_files_hash_for_watched_dirs", return_value=prev_hash
            )

            client = PtymeClient("", self._watched_dirs, [], self._cur_times_path)
            client._run_loop(prev_hash, True)

            record_time_mock.assert_not_called()

        @freezegun.freeze_time("2020-01-02 03:04:05")
        def test_sets_last_update(self, mocker: MockerFixture) -> None:
            mocker.patch.object(PtymeClient, "_record_time")

            client = PtymeClient("", self._watched_dirs, [], self._cur_times_path)
            client._run_loop(None, False)

            # last update is used by get files hash
            assert client._last_update == 1577934245.0

        def test_when_no_updates_does_not_record_multiple_times(
            self, mocker: MockerFixture
        ) -> None:
            record_time_mock = mocker.patch.object(PtymeClient, "_record_time")

            client = PtymeClient("", self._watched_dirs, [], self._cur_times_path)
            prev_files_hash, stopped = client._run_loop(None, False)
            prev_files_hash, stopped = client._run_loop(prev_files_hash, stopped)
            client._run_loop(prev_files_hash, stopped)

            # stops on second call
            assert record_time_mock.call_count == 2
            assert stopped is True

    class TestGetFilesHash(PtymeClientTestBase):
        @pytest.fixture(autouse=True)
        def setup_2(self) -> None:
            self._client = PtymeClient(
                "", self._watched_dirs, ["node_modules", "__pycache__"], self._cur_times_path
            )
            self._watched_dir = Path(self._watched_dirs[0])
            self._watched_dir.mkdir()

        def test_when_no_files_in_watched_dir(self) -> None:
            result = self._client._get_files_hash(self._watched_dir)

            assert result == "d41d8cd98f00b204e9800998ecf8427e"

        def test_when_watched_dir_does_not_exist(self) -> None:
            self._watched_dir.rmdir()

            result = self._client._get_files_hash(self._watched_dir)

            assert result == "d41d8cd98f00b204e9800998ecf8427e"

        def test_ignores_hidden_files(self) -> None:
            hidden = self._watched_dir / ".hidden"
            hidden.write_text("Some value")

            result = self._client._get_files_hash(self._watched_dir)

            assert result == "d41d8cd98f00b204e9800998ecf8427e"

        def test_ignores_hidden_directories(self) -> None:
            hidden_dir = self._watched_dir / ".hidden"
            hidden_dir.mkdir()
            subfile = hidden_dir / "a_file"
            subfile.write_text("Some value")

            result = self._client._get_files_hash(self._watched_dir)

            assert result == "d41d8cd98f00b204e9800998ecf8427e"

        def test_is_recursive(self) -> None:
            subdir = self._watched_dir / "subdir"
            subdir.mkdir()
            subfile = subdir / "a_file"
            subfile.write_text("Some value")

            result = self._client._get_files_hash(self._watched_dir)

            assert result == "231ce651470e28a49815b51ff3e0d5a3"

        def test_basic_case(self) -> None:
            inner_file = self._watched_dir / "inner_file"
            inner_file.write_text("Some value")

            result = self._client._get_files_hash(self._watched_dir)

            assert result == "231ce651470e28a49815b51ff3e0d5a3"

        def test_works_when_watched_dir_is_hidden(self) -> None:
            watched_dir = self._watched_dir / ".hidden"
            watched_dir.mkdir()

            inner_file = watched_dir / "inner_file"
            inner_file.write_text("Some value")

            result = self._client._get_files_hash(watched_dir)

            assert result == "231ce651470e28a49815b51ff3e0d5a3"

        def test_sets_file_cache(self) -> None:
            inner_file = self._watched_dir / "some_file"
            inner_file.write_text("Some value")

            self._client._get_files_hash(self._watched_dir)

            assert str(inner_file) in self._client._file_hash_cache

        def test_uses_files_cache(self) -> None:
            inner_file = self._watched_dir / "some_file"
            inner_file.write_text("Some value")

            self._client._last_update = datetime.datetime.now().timestamp() + 1000
            self._client._file_hash_cache[str(inner_file)] = b"some hash"

            result = self._client._get_files_hash(self._watched_dir)

            running_hash = hashlib.md5()
            running_hash.update(b"some hash")
            assert running_hash.hexdigest() == result

        def test_ignores_ignored_directories(self) -> None:
            node_modules = self._watched_dir / "node_modules"
            node_modules.mkdir()

            inner_file = node_modules / "inner_file"
            inner_file.write_text("Some value")

            result = self._client._get_files_hash(self._watched_dir)

            assert result == "d41d8cd98f00b204e9800998ecf8427e"

    class TestPerformRecordTime(PtymeClientTestBase):
        @freezegun.freeze_time("2020-01-02 03:04:05")
        def test_perform_record_time(self) -> None:
            client = PtymeClient("", self._watched_dirs, [], self._cur_times_path)
            self._cur_times_path.parent.mkdir()

            client._perform_record_time(SignedTime("server_id", "time", "sig"), "hash", False)

            cur_times = self._cur_times_path.read_text()

            assert (
                cur_times
                == json.dumps(
                    {
                        "time": "2020-01-02 03:04:05",
                        "signed_time": {"server_id": "server_id", "time": "time", "sig": "sig"},
                        "hash": "hash",
                        "stop": False,
                    }
                )
                + "\n"
            )
