import datetime
from dataclasses import dataclass
from functools import cached_property


@dataclass
class SignedTime:
    server_id: str
    time: str
    sig: str

    @cached_property
    def dt(self) -> datetime.datetime:
        return datetime.datetime.strptime(self.time, "%Y-%m-%d %H:%M:%S")
