"""
Copyright 2025 Exactpro Systems Limited - All Rights Reserved.

This software is owned by Exactpro Systems Limited and/or its affiliates
(hereinafter collectively referred to as the "Exactpro Group").

The scope and terms of a user license for this proprietary software
(hereinafter referred to as the "Exactpro Software License")
granted by the Exactpro Group to Your Firm are set out in the existing applicable
Master Services Agreement (or a similar overarching services agreement)
and/or relevant statement(s) of work (hereinafter collectively referred to as the "MSA")
between Your Firm and an affiliate of the Exactpro Group.

Any violation of the Exactpro Software License is prohibited and may result in legal action(s),
such as claim(s), lawsuit(s) and severe penalties.

Except as set out in the applicable MSA, this source code is provided 'AS IS'
without warranty of any kind.
The limitations of liability are set out in the applicable MSA.

Please reach out to Your Firm’s Legal department for a copy of the applicable MSA.

Code Overview
This is a JSONL (JSON Lines) merge utility
It performs a k-way merge of multiple files sorted by timestamp.
Purpose: Merges multiple JSONL files in chronological order based on a timestamp field,
tagging each message with its protocol.
"""

import json
import os
import heapq
import logging
import csv
from typing import Dict, Any, Iterator, TextIO, List, Optional, Union, Set
from itertools import count
from pathlib import Path

from ex_tmodel2.base.base import Event, EventLog

logger = logging.getLogger(__name__)


class JSONLFileReader:
    """Iterator wrapper for reading JSONL files line by line."""

    def __init__(self, file_handle: TextIO, file_path: str):
        self.file_handle = file_handle
        self.file_path = file_path
        self._iterator = iter(file_handle)

    def read_next(self) -> Optional[Dict[str, Any]]:
        """
        Read and parse the next valid JSON line.
        Returns None if EOF or all remaining lines are invalid.
        """
        for line in self._iterator:
            line = line.strip()
            if not line:
                continue
            if '\x00' in line:
                logger.warning(
                    f"Invalid JSON contains NULLs {line}"
                )
                line = line.replace('\x00', '')

            try:
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    logger.warning(
                        f"Skipping non-dict JSON in {self.file_path}: {type(obj).__name__}"
                    )
                    continue
                return obj
            except json.JSONDecodeError as e:
                logger.warning(
                    f"Invalid JSON in {self.file_path} at position {e.pos}: {e.msg}"
                )
                continue

        return None  # EOF


class CSVLFileReader:
    """Iterator wrapper for reading CSV files row by row."""

    def __init__(self, file_handle: TextIO, file_path: str):
        self.file_handle = file_handle
        self.file_path = file_path
        self._csv_reader = csv.DictReader(file_handle)
        self._iterator = iter(self._csv_reader)

    def read_next(self) -> Optional[Dict[str, Any]]:
        """
        Read and parse the next CSV row as a dictionary.
        Returns None if EOF or all remaining lines are invalid.
        """
        try:
            row = next(self._iterator)
            if row is None:
                return None
            # Convert all values to appropriate types, keeping them as strings for now
            return dict(row)
        except StopIteration:
            return None  # EOF
        except csv.Error as e:
            logger.warning(
                f"Invalid CSV row in {self.file_path}: {e}"
            )
            return self.read_next()  # Try to read next row


def merge_jsonl_with_protocol(
    file_protocols: Dict[str, str],
    ts_key: str = "#timestamp",
    protocol_key: Optional[str] = "#protocol",
    validate_timestamps: bool = True,
    ignore_exceptions: bool = False
) -> Iterator[Dict[str, Any]]:
    """
    Merge multiple JSONL files sorted by timestamp field.

    Args:
        file_protocols: Dict mapping file paths to protocol names
        ts_key: Field name containing the timestamp (default: "#timestamp")
        protocol_key: Field name for protocol tag (default: "#protocol").
                     If None, no protocol field will be added to the records.
        validate_timestamps: If True, validates timestamp type and sorting order,
                           raises ValueError if files are not sorted.
                           If False, uses fast path without validation.
        ignore_exceptions: If True, ignores exceptions raised by readers and continues merging.

    Yields:
        Dict objects from all files in chronological order, with protocol tag added
        (unless protocol_key is None)

    Raises:
        ValueError: If validate_timestamps=True and timestamps are not sorted

    Notes:
        - Files must be pre-sorted by timestamp
        - Timestamps are compared as strings (works for ISO 8601 format)
        - Lines without timestamps are skipped (with warning if validate_timestamps=True)
        - Invalid JSON lines are skipped with a warning
        - Use validate_timestamps=False for best performance with trusted data
    """
    if not file_protocols:
        logger.warning("No files provided to merge_jsonl_with_protocol")
        return

    file_paths = list(file_protocols.keys())
    handles: List[TextIO] = []
    readers: List[Union[JSONLFileReader, CSVLFileReader]] = []

    try:
        # Open all files
        for file_path in file_paths:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                continue

            try:
                fh = open(file_path, "r", encoding="utf-8")
                handles.append(fh)

                # Choose reader based on file extension
                if file_path.lower().endswith('.csv'):
                    readers.append(CSVLFileReader(fh, file_path))
                else:
                    # Default to JSON for .json and other extensions
                    readers.append(JSONLFileReader(fh, file_path))
            except IOError as e:
                logger.error(f"Failed to open {file_path}: {e}")
                continue

        if not readers:
            logger.error("No files could be opened for merging")
            return

        # Min-heap: (timestamp,c file_idx, sequence_number, dict_object)
        # sequence_number ensures stable sort for equal timestamps
        heap: List[tuple] = []
        per_file_seq = [count() for _ in readers]
        # Track last timestamp from each file to validate sorting
        last_timestamps: List[Optional[str]] = [None for _ in readers]

        def push_next_from_file(file_idx: int) -> None:
            """Read next valid record from file and push to heap."""
            reader = readers[file_idx]

            while True:
                try:
                    obj = reader.read_next()
                except Exception as e:
                    if ignore_exceptions:
                        print(e)
                        continue
                    raise e

                if obj is None:
                    # EOF reached
                    return

                # Add protocol tag if protocol_key is not None
                if protocol_key is not None:
                    obj[protocol_key] = file_protocols[file_paths[file_idx]]

                if validate_timestamps:
                    # Get timestamp
                    ts = obj[ts_key]

                    # Validation path: check type and ordering
                    # Validate it's a string
                    if not isinstance(ts, str):
                        logger.warning(
                            f"Timestamp {ts_key} is not a string in {file_paths[file_idx]}: "
                            f"{type(ts).__name__}"
                        )
                        ts = str(ts)  # Convert to string for comparison

                    # Validate that timestamps are sorted within this file
                    last_ts = last_timestamps[file_idx]
                    if last_ts is not None and ts < last_ts:
                        raise ValueError(
                            f"File {file_paths[file_idx]} is not sorted: "
                            f"timestamp {ts} appears after {last_ts}"
                        )
                    last_timestamps[file_idx] = ts

                else:
                    if ts_key not in obj:
                        continue

                    # Get timestamp
                    ts = obj[ts_key]

                # Push to heap
                seq = next(per_file_seq[file_idx])
                heapq.heappush(heap, (ts, file_idx, seq, obj))
                return


        # Prime the heap with first record from each file
        for i in range(len(readers)):
            push_next_from_file(i)

        # Merge
        while heap:
            timestamp, file_idx, seq, obj = heapq.heappop(heap)
            yield obj
            push_next_from_file(file_idx)

    finally:
        # Clean up all file handles
        for fh in handles:
            try:
                fh.close()
            except Exception as e:
                logger.error(f"Error closing file handle: {e}")


def find_jsons(
    input_data_folder: str,
    protocol_list: List[str],
    include_csv: bool = False
) -> Dict[str, str]:
    """
    Find all traffic JSON files matching protocol names in the folder.

    Args:
        input_data_folder: Root directory to search
        protocol_list: List of protocol names (e.g., ["FIX", "ITCH"])
        include_csv: If True, also search for .csv files (default: False)

    Returns:
        Dict mapping file paths (as strings) to uppercase protocol names

    Example:
        >>> find_jsons("/data", ["fix", "itch"])
        {"/data/logs/traffic_fix.json": "FIX",
         "/data/logs/traffic_itch.json": "ITCH"}
        >>> find_jsons("/data", ["fix", "itch"], include_csv=True)
        {"/data/logs/traffic_fix.json": "FIX",
         "/data/logs/traffic_itch.json": "ITCH",
         "/data/logs/traffic_fix.csv": "FIX"}
    """
    if not os.path.exists(input_data_folder):
        logger.error(f"Input folder does not exist: {input_data_folder}")
        return {}

    file_protocols = {}

    # Define file extensions to search for
    extensions = ['.json']
    if include_csv:
        extensions.append('.csv')

    for protocol in protocol_list:
        for ext in extensions:
            pattern = f"traffic_{protocol.lower()}{ext}"

            for file_path in Path(input_data_folder).rglob(pattern):
                # Convert Path to string for consistency
                file_path_str = str(file_path)
                protocol_upper = protocol.upper()

                if file_path_str in file_protocols:
                    logger.warning(
                        f"Duplicate file found: {file_path_str} "
                        f"(was {file_protocols[file_path_str]}, now {protocol_upper})"
                    )

                file_protocols[file_path_str] = protocol_upper
                logger.debug(f"Found {pattern}: {file_path_str}")

    if not file_protocols:
        file_types = "traffic_<protocol>.json" + (" or .csv" if include_csv else "")
        logger.warning(
            f"No files found matching {file_types} in {input_data_folder}"
        )

    return file_protocols


def eventlog_to_csv(
    event_log: EventLog,
    output_file: str,
    encoding: str = 'utf-8',
    newline: str = ''
) -> None:
    """
    Convert an EventLog (iterable of Event dictionaries) to a CSV file.

    This function collects all unique column names from all events and writes
    them to a CSV file using csv.DictWriter. Events may have different sets of keys,
    and all unique keys across all events will be included as columns.

    Args:
        event_log: An iterable of Event dictionaries (EventLog)
        output_file: Path to the output CSV file
        encoding: File encoding (default: 'utf-8')
        newline: Newline character for CSV file (default: '')

    Raises:
        ValueError: If event_log is empty or contains no valid events with fields

    Example:
        >>> events = [
        ...     {"timestamp": "2025-01-01", "price": 100, "quantity": 10},
        ...     {"timestamp": "2025-01-02", "price": 101, "side": "BUY"}
        ... ]
        >>> eventlog_to_csv(events, "output.csv")
        # Creates CSV with columns: price, quantity, side, timestamp

    Notes:
        - The function makes two passes through the event log:
          1st pass to collect all unique column names
          2nd pass to write the data
        - If event_log is a generator or one-time iterator, convert it to a list first
        - Missing fields in events will be written as empty strings in the CSV
        - Column names are sorted alphabetically for consistent ordering
    """
    # Convert to list if it's a generator to allow multiple iterations
    events_list = list(event_log)

    if not events_list:
        raise ValueError("EventLog is empty - no events to write")

    # Collect all unique column names from all events
    fieldnames: Set[str] = set()
    for event in events_list:
        if isinstance(event, dict):
            fieldnames.update(event.keys())
        else:
            logger.warning(f"Skipping non-dict event: {type(event).__name__}")

    if not fieldnames:
        raise ValueError("No valid fields found in events - all events are either non-dict or have no keys")

    # Sort fieldnames for consistent column ordering
    sorted_fieldnames = sorted(fieldnames)

    # Write to CSV
    try:
        with open(output_file, 'w', encoding=encoding, newline=newline) as f:
            writer = csv.DictWriter(f, fieldnames=sorted_fieldnames)
            writer.writeheader()

            for event in events_list:
                if isinstance(event, dict):
                    writer.writerow(event)

        logger.info(f"Successfully wrote {len(events_list)} events to {output_file}")
        logger.debug(f"CSV columns: {sorted_fieldnames}")

    except IOError as e:
        logger.error(f"Failed to write CSV file {output_file}: {e}")
        raise


def write_dicts_to_jsonl(
    records: List[Dict[str, Any]],
    file_path: str,
    encoding: str = 'utf-8'
) -> None:
    """
    Write a list of dictionaries to a JSONL (JSON Lines) file.

    Each dictionary is written as a separate JSON object on its own line.

    Args:
        records: List of dictionaries to write
        file_path: Path to the output file
        encoding: File encoding (default: 'utf-8')

    Raises:
        IOError: If the file cannot be written
    """
    with open(file_path, 'w', encoding=encoding) as f:
        for record in records:
            cleaned = {k: v for k, v in record.items() if v is not None and v != ''}
            f.write(json.dumps(cleaned, ensure_ascii=False) + '\n')
