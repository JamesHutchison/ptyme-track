from pathlib import Path

from ptyme_track.cement import cement_cur_times


def test_cement_cur_times_appends_to_file(tmp_path: Path):
    source_file = tmp_path / "source_file"
    source_file.write_text("source_file\n")
    target_file = tmp_path / "target_file"
    target_file.write_text("existing\n")

    cement_cur_times(target_file, source_file)

    assert target_file.read_text() == "existing\nsource_file\n"
