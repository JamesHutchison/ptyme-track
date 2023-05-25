import json
from pathlib import Path
from typing import List, Tuple

from ptyme_track.signature import signature_from_time
from ptyme_track.signed_time import SignedTime


def validate_signed_time_given_secret(secret: str, signed_time: SignedTime) -> dict:
    server_id_matches = signed_time.server_id == signed_time.server_id
    hash_sig = signature_from_time(secret, signed_time.time)
    return {
        "server_id_match": server_id_matches,
        "time": signed_time.time,
        "sig_matches": hash_sig == signed_time.sig,
    }


def validate_entries(file: Path, secret: str) -> Tuple[List[dict], List[dict]]:
    valid = []
    invalid = []
    with file.open() as times_file:
        for line in times_file.readlines():
            try:
                record = json.loads(line)
                result = validate_signed_time_given_secret(
                    secret, SignedTime(**record["signed_time"])
                )
            except (json.JSONDecodeError, ValueError, KeyError):
                invalid.append(record)
            else:
                if result["sig_matches"]:
                    valid.append(record)
                else:
                    invalid.append(record)
    return valid, invalid
