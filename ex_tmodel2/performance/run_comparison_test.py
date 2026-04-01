"""
Run side-by-side comparison of merge performance on existing test files.

This script expects test files to already exist in the specified folder.
It runs merge twice on the same files:
1. With validation enabled
2. With validation disabled

Use generate_json_data.py to create test files first.
"""

import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple

from ex_tmodel2.utils.merge_jsons import merge_jsonl_with_protocol, find_jsons

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def count_messages_in_files(file_paths: Dict[str, str]) -> int:
    """Count total number of messages across all files."""
    total = 0
    for file_path in file_paths.keys():
        with open(file_path, 'r', encoding='utf-8') as f:
            total += sum(1 for line in f if line.strip())
    return total


def run_single_merge_test(
    file_protocols: Dict[str, str],
    version: str,
    message_processor: Optional[Callable[[Dict[str, Any], Dict[str, Any]], None]] = None
) -> Tuple[float, int, Dict[str, Any]]:
    """
    Run a single merge test.

    Args:
        file_protocols: Dictionary mapping file paths to protocol names
        version: A/B test version label
        message_processor: Optional function to process each message
                          Signature: processor(message, metrics_dict)

    Returns:
        Tuple of (merge_time, message_count, metrics_dict)

    Example:
        >>> def track_errors(msg, metrics):
        ...     ts = msg.get("#timestamp")
        ...     if 'last_ts' in metrics and ts < metrics['last_ts']:
        ...         metrics['errors'] = metrics.get('errors', 0) + 1
        ...     metrics['last_ts'] = ts
        >>>
        >>> time, count, metrics = run_single_merge_test(
        ...     file_protocols,
        ...     validate_timestamps=True,
        ...     message_processor=track_errors
        ... )
        >>> print(f"Processed {count} messages in {time:.3f}s")
        >>> print(f"Errors: {metrics.get('errors', 0)}")
    """
    start_time = time.perf_counter()
    message_count = 0
    metrics = {}

    for message in merge_jsonl_with_protocol(
        file_protocols=file_protocols,
        validate_timestamps=True
    ):
        message_count += 1

        if message_processor is not None:
            message_processor(version, message, metrics)

    merge_time = time.perf_counter() - start_time

    return merge_time, message_count, metrics


def run_merge_jsons_performance_comparison(
    test_folder: str,
    message_processor: Callable[[Dict[str, Any], Dict[str, Any]], None],
    protocols: Optional[List[str]] = None,
    test_name: Optional[str] = None
) -> Dict[str, any]:
    """
    Run merge comparison test on existing files in a folder.

    Args:
        test_folder: Path to folder containing traffic_*.json files
        message_processor: Custom message processor function to run after each message.
        protocols: List of protocol names to search for. If None, auto-detect from files.
        test_name: Optional name for the test (defaults to folder name)

    Returns:
        Dictionary with comparison results
    """

    test_folder_path = Path(test_folder)
    if not test_folder_path.exists():
        raise FileNotFoundError(f"Test folder does not exist: {test_folder}")

    if test_name is None:
        test_name = test_folder_path.name

    print("\n" + "=" * 80)
    print(f"COMPARISON TEST: {test_name}")
    print(f"Folder: {test_folder}")
    print("=" * 80)

    # Find files
    print("\n[1/3] Finding test files...")

    if protocols is None:
        # Auto-detect protocols from filenames
        protocols = []
        for file in test_folder_path.rglob("traffic_*.json"):
            # Extract protocol from filename (e.g., traffic_fix.json -> FIX)
            filename = file.stem  # traffic_fix
            parts = filename.split('_')
            if len(parts) >= 2:
                protocol = parts[1].upper()  # FIX
                # Handle numbered files like traffic_fix_0.json
                protocol = protocol.split('_')[0] if '_' in protocol else protocol
                if protocol not in protocols:
                    protocols.append(protocol)

        if not protocols:
            raise ValueError(f"No traffic_*.json files found in {test_folder}")

        print(f"  Auto-detected protocols: {', '.join(protocols)}")

    file_protocols = find_jsons(test_folder, protocols)

    if not file_protocols:
        raise ValueError(f"No files found for protocols {protocols} in {test_folder}")

    print(f"✓ Found {len(file_protocols)} files:")
    for file_path, protocol in sorted(file_protocols.items()):
        print(f"  - {Path(file_path).name} ({protocol})")

    # Count messages
    total_messages = count_messages_in_files(file_protocols)
    print(f"✓ Total messages: {total_messages:,}")

    # Run Test A
    print("\n[2/3] Running Test A...")
    time_a, count_a, metrics_a = run_single_merge_test(
        file_protocols,
        version="A",
        message_processor=message_processor
    )
    throughput_a = count_a / time_a if time_a > 0 else 0

    print(f"✓ Merged {count_a:,} messages in {time_a:.3f}s ({throughput_a:,.0f} msg/s)")
    if metrics_a.get('timestamp_errors', 0) > 0:
        print(f"  WARNING: {metrics_a['timestamp_errors']} timestamp ordering errors detected")

    # Run Test B
    print("\n[3/3] Running Test B")
    time_b, count_b, metrics_b = run_single_merge_test(
        file_protocols,
        version="B",
        message_processor=message_processor
    )
    throughput_b = count_b / time_b if time_b > 0 else 0

    print(f"✓ Merged {count_b:,} messages in {time_b:.3f}s ({throughput_b:,.0f} msg/s)")
    if metrics_b.get('timestamp_errors', 0) > 0:
        print(f"  WARNING: {metrics_b['timestamp_errors']} timestamp ordering errors detected")

    # Calculate speedup
    speedup = time_a / time_b if time_b > 0 else 0
    speedup_pct = (speedup - 1) * 100
    time_saved = time_a - time_b

    # Print comparison results
    print("\n" + "=" * 80)
    print("COMPARISON RESULTS")
    print("=" * 80)
    print(f"Test Configuration:")
    print(f"  Folder:               {test_folder}")
    print(f"  Files:                {len(file_protocols)}")
    print(f"  Protocols:            {', '.join(protocols)}")
    print(f"  Messages:             {total_messages:,}")
    print()
    print(f"{'Metric':<30} {'Test A':<20} {'Test B':<20} {'Difference':<15}")
    print("-" * 80)
    print(f"{'Merge Time (s)':<30} {time_a:<20.3f} {time_b:<20.3f} {time_saved:.3f}s saved")
    print(f"{'Throughput (msg/s)':<30} {throughput_a:<20,.0f} {throughput_b:<20,.0f} {speedup:.2f}x faster")
    print(f"{'Messages Processed':<30} {count_a:<20,} {count_b:<20,}")

    # Print custom metrics if available
    if metrics_a or metrics_b:
        print()
        print("Custom Metrics:")
        all_metric_keys = set(metrics_a.keys()) | set(metrics_b.keys())
        for key in sorted(all_metric_keys):
            if key != 'last_timestamp':  # Skip internal tracking fields
                val_a = metrics_a.get(key, 'N/A')
                val_b = metrics_b.get(key, 'N/A')
                print(f"  {key:<28} {str(val_a):<20} {str(val_b):<20}")

    print("=" * 80)
    print(f"\nPerformance improvement without validation: {speedup_pct:+.1f}%")
    print("=" * 80)

    if count_a != count_b:
        logger.warning(f"Message count mismatch: Test A={count_a}, Test B={count_b}")

    if count_a != total_messages:
        logger.warning(f"Message count mismatch: expected={total_messages}, got={count_a}")

    results = {
        "test_name": test_name,
        "folder": test_folder,
        "num_files": len(file_protocols),
        "total_messages": total_messages,
        "protocols": protocols,
        "test_a": {
            "merge_time": time_a,
            "throughput": throughput_a,
            "messages": count_a,
            "custom_metrics": metrics_a
        },
        "test_b": {
            "merge_time": time_b,
            "throughput": throughput_b,
            "messages": count_b,
            "custom_metrics": metrics_b
        },
        "speedup": speedup,
        "speedup_pct": speedup_pct,
        "time_saved": time_saved
    }

    return results

# Define message processor to track timestamp errors
def track_timestamp_errors(version: str, msg: Dict[str, Any], metrics: Dict[str, Any]) -> None:
    """Track timestamp ordering errors."""
    if 'timestamp_errors' not in metrics:
        metrics['timestamp_errors'] = 0
        metrics['last_timestamp'] = None

    current_ts = msg.get("#timestamp")
    last_ts = metrics['last_timestamp']
    metrics['num_messages'] = metrics.get('num_messages', 0) + 1

    if last_ts is not None and current_ts is not None and current_ts < last_ts:
        metrics['timestamp_errors'] += 1

    metrics['last_timestamp'] = current_ts
    metrics['version'] = version


if __name__ == "__main__":
    # Default: look for test_data folder with subdirectories
    test_data_path = Path("test_data")
    run_merge_jsons_performance_comparison(
        test_folder=test_data_path,
        message_processor=track_timestamp_errors,
        protocols=None,
        test_name="Simple Benchmarking"
    )
