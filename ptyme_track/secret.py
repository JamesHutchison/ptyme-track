import uuid
from pathlib import Path
from typing import Union

from ptyme_track.ptyme_env import SECRET, SECRET_PATH

secret_path = Path(SECRET_PATH)


class MissingSecretError(Exception):
    def __str__(self) -> str:
        return "Generate the secret file first using `ptyme-track --generate-secret`"


def get_secret() -> str:
    if secret_path.exists():
        return secret_path.read_text().strip()
    return SECRET


def generate_secret() -> None:
    with open(SECRET_PATH, "w") as f:
        f.write(str(uuid.uuid4()))
    git_ignore = Path(".gitignore")
    if git_ignore.exists():
        contents = git_ignore.read_text()
        if SECRET_PATH not in contents:
            to_write = contents + "\n# ptyme server secret\n" + SECRET_PATH
            if contents.endswith("\n"):
                to_write += "\n"
            git_ignore.write_text(to_write)


def ensure_secret(secret_path: Union[Path, str] = SECRET_PATH) -> None:
    try:
        validate_secret_file_exists(secret_path)
    except MissingSecretError:
        generate_secret()


def validate_secret_file_exists(secret_path: Union[Path, str] = SECRET_PATH) -> None:
    if not Path(secret_path).exists():
        raise MissingSecretError()
