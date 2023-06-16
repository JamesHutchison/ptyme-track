import json
from pathlib import Path
from typing import Callable, List, NamedTuple, Optional, Tuple, Union

from ptyme_track.signature import signature_from_time
from ptyme_track.signed_time import SignedTime

_SecretAndValidator = NamedTuple(
    "_SecretAndValidator", [("secret", str), ("validator", Callable)]
)


def validate_signed_time_given_secret(secret: str, signed_time: SignedTime) -> dict:
    server_id_matches = signed_time.server_id == signed_time.server_id
    hash_sig = signature_from_time(secret, signed_time.time)
    return {
        "server_id_match": server_id_matches,
        "time": signed_time.time,
        "sig_matches": hash_sig == signed_time.sig,
    }


def validate_entries(file: Path, secret: str) -> Tuple[List[dict], List[Union[dict, str]]]:
    return load_entries(file, _SecretAndValidator(secret, validate_signed_time_given_secret))


def load_entries(
    file: Path, secret_and_validator: Optional[_SecretAndValidator] = None
) -> Tuple[List[dict], List[Union[dict, str]]]:
    valid: List[dict] = []
    invalid: List[Union[dict, str]] = []
    with file.open() as times_file:
        for line in times_file.readlines():
            try:
                record: dict = json.loads(line)
                if secret_and_validator:
                    result = secret_and_validator.validator(
                        secret_and_validator.secret, SignedTime(**record["signed_time"])
                    )
                else:
                    valid.append(record)
                    continue
            except (json.JSONDecodeError, ValueError, KeyError):
                invalid.append(line)
            else:
                if result["sig_matches"]:
                    valid.append(record)
                else:
                    invalid.append(record)
    return valid, invalid
