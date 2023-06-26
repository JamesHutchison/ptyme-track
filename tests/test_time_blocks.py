import datetime

from ptyme_track.time_blocks import (
    TimeBlock,
    _remove_buffer_from_bufferless_blocks,
    build_time_blocks_from_records,
)


class TestBuildTimeBlocksFromRecords:
    def test_removes_buffer_from_isolated_blocks(self) -> None:
        records = [
            {
                "signed_time": {
                    "time": "2020-01-01 00:00:00",
                    "sig": "sig",
                    "server_id": "server_id",
                },
            },
            {
                "signed_time": {
                    "time": "2020-01-01 00:02:00",
                    "sig": "sig",
                    "server_id": "server_id",
                }
            },
        ]
        result = build_time_blocks_from_records(records, datetime.timedelta(minutes=5), 5, 90)
        assert result[0].duration == datetime.timedelta(minutes=2)

    def test_adds_buffer_to_non_isolated_blocks(self) -> None:
        records = [
            {
                "signed_time": {
                    "time": "2020-01-01 00:00:00",
                    "sig": "sig",
                    "server_id": "server_id",
                },
            },
            {
                "signed_time": {
                    "time": "2020-01-01 00:02:00",
                    "sig": "sig",
                    "server_id": "server_id",
                }
            },
            {
                "signed_time": {
                    "time": "2020-01-01 00:12:00",
                    "sig": "sig",
                    "server_id": "server_id",
                },
            },
            {
                "signed_time": {
                    "time": "2020-01-01 00:16:00",
                    "sig": "sig",
                    "server_id": "server_id",
                }
            },
        ]
        result = build_time_blocks_from_records(records, datetime.timedelta(minutes=5), 5, 90)
        assert result[0].duration == datetime.timedelta(minutes=12)
        assert result[1].duration == datetime.timedelta(minutes=14)


class TestRemoveBufferFromBufferlessBlocks:
    def test_removes_buffer_from_only_isolated_blocks(self) -> None:
        start_time = datetime.datetime(2020, 1, 1, 0, 0, 0)
        buffer = datetime.timedelta(minutes=5)
        bufferless_block_min_size = 5
        bufferless_block_gap = 90

        timeblocks = [
            TimeBlock(
                start_time=start_time - buffer,
                end_time=start_time + datetime.timedelta(minutes=2) + buffer,
            ),
            TimeBlock(
                start_time=start_time + datetime.timedelta(days=1),
                end_time=start_time + datetime.timedelta(days=1, minutes=20),
            ),
            TimeBlock(
                start_time=start_time + datetime.timedelta(days=1, minutes=50),
                end_time=start_time + datetime.timedelta(days=1, minutes=90),
            ),
            TimeBlock(
                start_time=start_time + datetime.timedelta(days=2),
                end_time=start_time + datetime.timedelta(days=2, minutes=(2 + 5 + 5)),
            ),
            TimeBlock(
                start_time=start_time
                + datetime.timedelta(days=2, minutes=((2 + 5) + bufferless_block_gap)),
                end_time=start_time
                + datetime.timedelta(days=2, minutes=((2 + 5 + 12) + bufferless_block_gap)),
            ),
        ]
        result = _remove_buffer_from_bufferless_blocks(
            timeblocks, buffer, bufferless_block_min_size, bufferless_block_gap
        )
        # buffer removed
        assert result[0].duration == datetime.timedelta(minutes=2)

        # buffer not removed
        assert result[1].duration == datetime.timedelta(minutes=20)
        assert result[2].duration == datetime.timedelta(minutes=40)
        assert result[3].duration == datetime.timedelta(minutes=12)
        assert result[4].duration == datetime.timedelta(minutes=12)
