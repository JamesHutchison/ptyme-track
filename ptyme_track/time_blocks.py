import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ptyme_track.signed_time import SignedTime
from ptyme_track.validation import validate_entries


@dataclass
class TimeBlock:
    start_time: datetime.datetime
    end_time: datetime.datetime

    @property
    def duration(self):
        return self.end_time - self.start_time


def get_time_blocks(
    file: Path,
    secret: str,
    buffer_minutes: int = 5,
    start_time_utc: Optional[datetime.datetime] = None,
    end_time_utc: Optional[datetime.datetime] = None,
) -> List[TimeBlock]:
    valid, invalid = validate_entries(file, secret)
    considered = []
    for record in valid:
        signed_time = SignedTime(**record["signed_time"])
        if start_time_utc and signed_time.dt <= start_time_utc:
            continue
        if end_time_utc and signed_time.dt >= end_time_utc:
            continue
        considered.append(record)
    return build_time_blocks_from_records(considered, datetime.timedelta(minutes=buffer_minutes))


def build_time_blocks_from_records(
    records: List[dict], buffer: datetime.timedelta
) -> List[TimeBlock]:
    sorted_signed_times: List[SignedTime] = sorted(
        [SignedTime(**r["signed_time"]) for r in records], key=lambda r: r.dt
    )
    blocks: List[TimeBlock] = []

    def add_block(signed_time: SignedTime) -> None:
        blocks.append(
            TimeBlock(
                start_time=signed_time.dt - buffer,
                end_time=signed_time.dt + buffer,
            )
        )

    for signed_time in sorted_signed_times:
        if not blocks:
            add_block(signed_time)
            continue
        last_block = blocks[-1]
        # note: block already incorporates the buffer
        if signed_time.dt < last_block.end_time:
            last_block.end_time = signed_time.dt + buffer
        else:
            add_block(signed_time)
    return blocks
