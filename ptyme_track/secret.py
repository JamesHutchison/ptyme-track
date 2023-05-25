from pathlib import Path

from ptyme_track.ptyme_env import SECRET, SECRET_PATH

secret_path = Path(SECRET_PATH)


def get_secret() -> str:
    if secret_path.exists():
        return secret_path.read_text().strip()
    return SECRET
