import hashlib


def signature_from_time(secret: str, time_as_str: str) -> str:
    hash_str = secret + time_as_str
    hash_sig = hashlib.sha256(hash_str.encode("utf-8")).hexdigest()
    return hash_sig
