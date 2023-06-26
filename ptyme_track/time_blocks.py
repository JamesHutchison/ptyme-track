import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ptyme_track.signed_time import SignedTime
from ptyme_track.validation import load_entries, validate_entries


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
    check_against_secret: bool = True,
    bufferless_block_min_size: int = 5,
    bufferless_block_gap: int = 90,
) -> List[TimeBlock]:
    """
    Get the time blocks from a file

    :param file: The file to read time blocks from
    :param secret: The secret to use for validating entries
    :param buffer_minutes: The number of minutes before and after entries to add a buffer.
        Note that this isn't always there. The bufferless block configuration determines
        which blocks are too small and isolated to get a buffer.
    :param start_time_utc: The start time to read entries from, in UTC
    :param end_time_utc: The end time to read entries from, in UTC
    :param check_against_secret: Whether to validate against the secret or not. Entries
        that do not validate against the secret are discarded.
    :param bufferless_block_min_size: The minimum size of a bufferless block. This exists
        to reduce the effects of "rogue" time recordings from previous work. The value is
        in minutes.
    :param bufferless_block_gap: The gap size to treat a block of time as bufferless.
        This exists to reduce the effect of "rogue" time recordings from previous work.
        The value is in minutes. As an example, if this value is 90, and the time gap to
        the next block is over 90 minutes, then the block will NOT be given a buffer.
        If there are two blocks near each other and and the gap between them is less than
        90 minutes, then the two blocks will have a buffer around them.
    :return: _description_
    """
    if check_against_secret:
        valid, invalid = validate_entries(file, secret)
    else:
        valid, invalid = load_entries(file)
    considered = []
    for record in valid:
        signed_time = SignedTime(**record["signed_time"])
        if start_time_utc and signed_time.dt <= start_time_utc:
            continue
        if end_time_utc and signed_time.dt >= end_time_utc:
            continue
        considered.append(record)
    return build_time_blocks_from_records(
        considered,
        datetime.timedelta(minutes=buffer_minutes),
        bufferless_block_min_size,
        bufferless_block_gap,
    )


def build_time_blocks_from_records(
    records: List[dict],
    buffer: datetime.timedelta,
    bufferless_block_min_size: int = 5,
    bufferless_block_gap: int = 90,
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

    _remove_buffer_from_bufferless_blocks(
        blocks, buffer, bufferless_block_min_size, bufferless_block_gap
    )

    return blocks


def _remove_buffer_from_bufferless_blocks(
    blocks: List[TimeBlock],
    buffer: datetime.timedelta,
    bufferless_block_min_size: int,
    bufferless_block_gap: int,
) -> List[TimeBlock]:
    minimum_gap_size = datetime.timedelta(minutes=bufferless_block_gap)
    for idx, block in enumerate(blocks):
        if block.duration - buffer * 2 <= datetime.timedelta(minutes=bufferless_block_min_size):
            if (
                idx > 0
                and (block.start_time + buffer) - blocks[idx - 1].end_time <= minimum_gap_size
            ):
                continue
            if (
                idx < len(blocks) - 1
                and blocks[idx + 1].start_time - (block.end_time - buffer) <= minimum_gap_size
            ):
                continue

            # remove the buffer
            block.start_time += buffer
            block.end_time -= buffer

    return blocks
