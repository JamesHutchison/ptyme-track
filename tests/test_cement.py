from pathlib import Path

from ptyme_track.cement import cement_cur_times


def test_cement_cur_times_appends_to_file(tmp_path: Path) -> None:
    source_file = tmp_path / "source_file"
    source_file.write_text('{"new": "value"}\n')
    target_file = tmp_path / "target_file"
    target_file.write_text('{"existing": "value"}\n')

    cement_cur_times(target_file, source_file)

    assert (
        target_file.read_text() == '{"existing": "value"}\n{"new": "value", "git-branch": null}\n'
    )


def test_cement_cur_times_adds_git_branch(tmp_path: Path) -> None:
    source_file = tmp_path / "source_file"
    source_file.write_text('{"new": "value"}\n')
    target_file = tmp_path / "target_file"
    target_file.write_text('{"existing": "value"}\n')

    cement_cur_times(target_file, source_file, git_branch="git_branch")

    assert (
        target_file.read_text()
        == '{"existing": "value"}\n{"new": "value", "git-branch": "git_branch"}\n'
    )
