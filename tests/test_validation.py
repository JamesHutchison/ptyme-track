import json
from pathlib import Path

import pytest

from ptyme_track.validation import _SecretAndValidator, load_entries


class TestLoadEntries:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path) -> None:
        self.input_file = tmp_path / "input"
        with self.input_file.open("w") as in_file:
            json.dump(
                {
                    "time": "2023-06-16 22:26:26",
                    "signed_time": {
                        "server_id": "46deb06b-1052-47b0-96ec-f9fad7411763",
                        "time": "2023-06-16 22:26:26",
                        "sig": "60123fec2ea2a396868bbcad6b9551fb76f7ef6929a58ab5af5db10a55282151",
                    },
                    "hash": "18bd235e559a67ce6a923577476031f2",
                    "stop": True,
                },
                in_file,
            )
            in_file.write("\n")
            json.dump(
                {
                    "time": "2023-06-16 22:27:36",
                    "signed_time": {
                        "server_id": "7ccbea7a-1993-4d06-8bde-990fdeee1d7b",
                        "time": "2023-06-16 22:27:36",
                        "sig": "f99d6ddb60a5cc874fb5313609b7db300807c3ae095620c797af07ae62c0affc",
                    },
                    "hash": "26b523ae7cac51a78f1eb2dcebefb23b",
                    "stop": True,
                },
                in_file,
            )
            in_file.write("\n")

    def test_when_entries_are_valid_returns_them(self) -> None:
        valid, invalid = load_entries(
            self.input_file,
            _SecretAndValidator("secret", lambda secret, signed_time: {"sig_matches": True}),
        )

        assert len(valid) == 2
        assert len(invalid) == 0

    def test_when_entries_are_not_valid_json_does_not_return_them(self) -> None:
        self.input_file.write_text("{")
        valid, invalid = load_entries(self.input_file, None)

        assert len(valid) == 0
        assert len(invalid) == 1

    def test_when_signature_doesnt_match_does_not_return_them(self) -> None:
        valid, invalid = load_entries(
            self.input_file,
            _SecretAndValidator("secret", lambda secret, signed_time: {"sig_matches": False}),
        )

        assert len(valid) == 0
        assert len(invalid) == 2

    def test_when_no_validator_then_returns_them(self) -> None:
        valid, invalid = load_entries(self.input_file, None)

        assert len(valid) == 2
        assert len(invalid) == 0
