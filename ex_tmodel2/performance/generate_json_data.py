"""
Load test data generator for merge_jsonl_with_protocol function.

Generates traffic_<protocol>.json files with configurable parameters
for performance testing and load testing.
"""

import json
import random
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any


def generate_random_string(min_length: int, max_length: int) -> str:
    """Generate a random alphanumeric string."""
    length = random.randint(min_length, max_length)
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_timestamp(base_time: datetime, offset_seconds: float, keep_isoformat_problem: bool) -> str:
    """
    Generate an ISO 8601 timestamp.

    Args:
        base_time: Starting datetime
        offset_seconds: Seconds to add to base_time

    Returns:
        ISO 8601 formatted timestamp string
    """
    timestamp = base_time + timedelta(seconds=offset_seconds)
    return timestamp.isoformat() + ('Z' if keep_isoformat_problem else '')


def generate_message(
    timestamp: str,
    min_tags: int,
    max_tags: int,
    min_tag_name_length: int,
    max_tag_name_length: int,
    min_tag_value_length: int,
    max_tag_value_length: int
) -> Dict[str, Any]:
    """
    Generate a single message with random tags.

    Args:
        timestamp: ISO 8601 timestamp string
        min_tags: Minimum number of tags (excluding #timestamp)
        max_tags: Maximum number of tags (excluding #timestamp)
        min_tag_name_length: Minimum tag name length
        max_tag_name_length: Maximum tag name length
        min_tag_value_length: Minimum tag value length
        max_tag_value_length: Maximum tag value length

    Returns:
        Dictionary representing a single message
    """
    message = {"#timestamp": timestamp}

    num_tags = random.randint(min_tags, max_tags)

    for _ in range(num_tags):
        tag_name = generate_random_string(min_tag_name_length, max_tag_name_length)
        # Ensure tag name doesn't conflict with reserved names
        while tag_name in message or tag_name.startswith('#'):
            tag_name = generate_random_string(min_tag_name_length, max_tag_name_length)

        # Randomly choose tag value type (string, int, float, bool)
        value_type = random.choice(['string', 'int', 'float', 'bool'])

        if value_type == 'string':
            tag_value = generate_random_string(min_tag_value_length, max_tag_value_length)
        elif value_type == 'int':
            tag_value = random.randint(0, 1000000)
        elif value_type == 'float':
            tag_value = random.uniform(0, 1000000)
        else:  # bool
            tag_value = random.choice([True, False])

        message[tag_name] = tag_value

    return message


def generate_traffic_files(
    output_folder: str,
    protocols: List[str],
    num_files_per_protocol: int = 1,
    min_messages_per_file: int = 100,
    max_messages_per_file: int = 1000,
    min_tags_per_message: int = 5,
    max_tags_per_message: int = 20,
    min_tag_name_length: int = 3,
    max_tag_name_length: int = 15,
    min_tag_value_length: int = 5,
    max_tag_value_length: int = 50,
    timestamp_base: datetime = None,
    time_spread_seconds: float = 3600.0,
    ensure_unique_timestamps: bool = True,
    keep_isoformat_problem: bool = True,
    partition_time_across_files: bool = False
) -> Dict[str, int]:
    """
    Generate multiple traffic JSON files for load testing.

    Args:
        output_folder: Directory to write the files
        protocols: List of protocol names (e.g., ["FIX", "ITCH", "OUCH"])
        num_files_per_protocol: Number of files to generate per protocol
        min_messages_per_file: Minimum number of messages per file
        max_messages_per_file: Maximum number of messages per file
        min_tags_per_message: Minimum number of tags per message (excluding #timestamp)
        max_tags_per_message: Maximum number of tags per message (excluding #timestamp)
        min_tag_name_length: Minimum length of tag names
        max_tag_name_length: Maximum length of tag names
        min_tag_value_length: Minimum length of string tag values
        max_tag_value_length: Maximum length of string tag values
        timestamp_base: Base datetime for timestamps (defaults to now)
        time_spread_seconds: Time range in seconds over which to spread messages
        ensure_unique_timestamps: If True, guarantees strictly monotonic increasing timestamps
                                  by adding a minimum increment (1 microsecond) between messages
        keep_isoformat_problem: If True will not add Z to ISO 8601 timestamps to avoid random problem
        partition_time_across_files: If True, divides time_spread_seconds equally among files
                                     from the same protocol to avoid timestamp overlaps.
                                     If False (default), all files use the full time range.

    Returns:
        Dictionary mapping file paths to message counts

    Example:
        >>> stats = generate_traffic_files(
        ...     output_folder="test_data",
        ...     protocols=["FIX", "ITCH"],
        ...     num_files_per_protocol=2,
        ...     min_messages_per_file=100,
        ...     max_messages_per_file=500,
        ...     ensure_unique_timestamps=True
        ... )
        >>> print(stats)
        {'test_data/traffic_fix_0.json': 324, 'test_data/traffic_fix_1.json': 421, ...}
    """
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    if timestamp_base is None:
        timestamp_base = datetime.now()

    file_stats = {}

    for protocol in protocols:
        for file_idx in range(num_files_per_protocol):
            # Generate filename
            subfolder_path = output_path / str(file_idx)
            subfolder_path.mkdir(parents=True, exist_ok=True)

            filename = f"traffic_{protocol.lower()}.json"

            file_path = subfolder_path / filename

            # Determine number of messages for this file
            num_messages = random.randint(min_messages_per_file, max_messages_per_file)

            # Calculate time range for this file
            if partition_time_across_files and num_files_per_protocol > 1:
                # Divide time range equally among files of the same protocol
                time_per_file = time_spread_seconds / num_files_per_protocol
                time_start = file_idx * time_per_file
                time_end = (file_idx + 1) * time_per_file
            else:
                # All files use the full time range (overlapping timestamps possible)
                time_start = 0
                time_end = time_spread_seconds

            # Generate sorted timestamps for this file
            if ensure_unique_timestamps:
                # Calculate minimum increment to guarantee unique timestamps
                # Use 1 microsecond (0.000001 seconds) as minimum increment
                min_increment = 0.000001
                time_range = time_end - time_start
                max_possible_messages = int(time_range / min_increment)

                if num_messages > max_possible_messages:
                    raise ValueError(
                        f"Cannot generate {num_messages} unique timestamps in "
                        f"{time_range:.2f} seconds with {min_increment*1e6:.1f}μs minimum increment. "
                        f"Max possible: {max_possible_messages}"
                    )

                # Generate strictly monotonic timestamps by spacing them evenly
                # with some randomness, but ensuring minimum increment
                time_offsets = []
                current_offset = time_start

                for i in range(num_messages):
                    # Add random increment between min_increment and average spacing
                    remaining_messages = num_messages - i
                    remaining_time = time_end - current_offset
                    avg_spacing = remaining_time / remaining_messages if remaining_messages > 0 else min_increment

                    # Random increment between min and 2x average (to add variability)
                    max_increment = min(avg_spacing * 2, remaining_time - min_increment * (remaining_messages - 1))
                    increment = random.uniform(min_increment, max(min_increment, max_increment))

                    time_offsets.append(current_offset)
                    current_offset += increment
            else:
                # Original behavior: random offsets, sorted but may have duplicates
                time_offsets = sorted([
                    random.uniform(time_start, time_end)
                    for _ in range(num_messages)
                ])

            # Generate messages
            messages = []
            for offset in time_offsets:
                timestamp = generate_timestamp(timestamp_base, offset, keep_isoformat_problem)
                message = generate_message(
                    timestamp=timestamp,
                    min_tags=min_tags_per_message,
                    max_tags=max_tags_per_message,
                    min_tag_name_length=min_tag_name_length,
                    max_tag_name_length=max_tag_name_length,
                    min_tag_value_length=min_tag_value_length,
                    max_tag_value_length=max_tag_value_length
                )
                messages.append(message)

            # Write to file in JSONL format (one JSON per line)
            with open(file_path, 'w', encoding='utf-8') as f:
                for message in messages:
                    json.dump(message, f, ensure_ascii=False)
                    f.write('\n')

            file_stats[str(file_path)] = num_messages
            print(f"Generated {file_path} with {num_messages} messages")

    return file_stats


def print_generation_summary(file_stats: Dict[str, int]) -> None:
    """Print a summary of generated files."""
    total_messages = sum(file_stats.values())
    total_files = len(file_stats)

    print("\n" + "=" * 60)
    print("Generation Summary")
    print("=" * 60)
    print(f"Total files generated: {total_files}")
    print(f"Total messages generated: {total_messages}")
    print(f"Average messages per file: {total_messages / total_files:.1f}")
    print("=" * 60)

    for file_path, count in sorted(file_stats.items()):
        print(f"  {Path(file_path).name}: {count} messages")
    print("=" * 60)

if __name__ == "__main__":
    import sys

    stats = generate_traffic_files(
        output_folder="test_data",
        protocols=["FIX", "ITCH", "OUCH"],
        num_files_per_protocol=2,
        min_messages_per_file=200000,
        max_messages_per_file=300000,
        min_tags_per_message=15,
        max_tags_per_message=35,
        min_tag_name_length=3,
        max_tag_name_length=15,
        min_tag_value_length=5,
        max_tag_value_length=50,
        time_spread_seconds=3600.0,  # 1 hour
        ensure_unique_timestamps=True,  # Guarantee strictly monotonic timestamps
        keep_isoformat_problem=False,
        partition_time_across_files=False  # Files can have overlapping timestamps
    )

    print_generation_summary(stats)

    print("\nTo run comparison test on this data:")
    print("  python run_comparison_test.py test_data/custom")