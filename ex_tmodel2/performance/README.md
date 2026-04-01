# Performance Testing User Manual

This directory contains tools for performance testing the `merge_jsonl_with_protocol` function. The framework is split into two separate concerns: test data generation and performance comparison testing.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [File Descriptions](#file-descriptions)
4. [Detailed Usage](#detailed-usage)
5. [Examples](#examples)
6. [Troubleshooting](#troubleshooting)

---

## Overview

The performance testing framework consists of two main components:

1. **`generate_json_data.py`** - Generates synthetic test data files
2. **`run_comparison_test.py`** - Runs A/B performance tests on existing data

This separation allows you to:
- Generate test data once and reuse it for multiple test runs
- Test different configurations without regenerating data
- Share test datasets across team members

---

## Quick Start

### Step 1: Generate Test Data

```bash
# Generate a single test dataset with default settings
python performance/generate_json_data.py
```

This creates test files in `test_data/` directory.

### Step 2: Run Performance Test

```bash
# Run comparison test on the generated data
python performance/run_comparison_test.py
```

This will run Test A and Test B on the same dataset and show performance metrics.

---

## File Descriptions

### 1. generate_json_data.py

**Purpose**: Generate synthetic traffic JSON files for performance testing.

**Key Features**:
- Creates `traffic_<protocol>.json` files in JSONL format
- Generates strictly monotonic timestamps (no duplicates)
- Configurable message counts, tag counts, protocols
- Supports multiple data types (string, int, float, bool)

**Main Function**:
```python
generate_traffic_files(
    output_folder: str,              # Where to save files
    protocols: List[str],            # Protocol names ["FIX", "ITCH", etc.]
    num_files_per_protocol: int,     # Number of files per protocol
    min_messages_per_file: int,      # Minimum messages per file
    max_messages_per_file: int,      # Maximum messages per file
    min_tags_per_message: int,       # Min tags (excluding #timestamp)
    max_tags_per_message: int,       # Max tags (excluding #timestamp)
    min_tag_name_length: int,        # Min length of tag names
    max_tag_name_length: int,        # Max length of tag names
    min_tag_value_length: int,       # Min length of string values
    max_tag_value_length: int,       # Max length of string values
    time_spread_seconds: float,      # Time range for timestamps
    ensure_unique_timestamps: bool,  # Guarantee monotonic timestamps
    partition_time_across_files: bool # Divide time among files
)
```

### 2. run_comparison_test.py

**Purpose**: Run side-by-side performance comparison tests.

**Key Features**:
- Runs two tests (A and B) on the same dataset
- Measures merge time, throughput, message counts
- Supports custom message processors for metrics collection
- Auto-detects protocols from filenames
- Calculates performance improvement (speedup)

**Main Function**:
```python
run_merge_jsons_performance_comparison(
    test_folder: str,                                      # Path to test data
    message_processor: Callable,                           # Custom processor function
    protocols: Optional[List[str]] = None,                 # Protocol list (auto-detect if None)
    test_name: Optional[str] = None                        # Test name (defaults to folder name)
)
```

**Core Test Runner**:
```python
run_single_merge_test(
    file_protocols: Dict[str, str],     # File path to protocol mapping
    version: str,                        # Test version label ("A" or "B")
    message_processor: Optional[Callable] = None  # Optional processor
) -> Tuple[float, int, Dict[str, Any]]  # Returns (time, count, metrics)
```

---

## Detailed Usage

### Generating Test Data

#### Example 1: Basic Usage

```python
from generate_json_data import generate_traffic_files

# Generate small test dataset
stats = generate_traffic_files(
    output_folder="test_data/small",
    protocols=["FIX", "ITCH", "OUCH"],
    num_files_per_protocol=1,
    min_messages_per_file=1000,
    max_messages_per_file=1000,
    min_tags_per_message=5,
    max_tags_per_message=10
)

print(f"Generated {sum(stats.values())} total messages")
```

#### Example 2: Large Dataset with Multiple Files

```python
# Generate large dataset with multiple files per protocol
stats = generate_traffic_files(
    output_folder="test_data/large",
    protocols=["FIX", "ITCH", "OUCH"],
    num_files_per_protocol=5,          # 5 files per protocol
    min_messages_per_file=10000,
    max_messages_per_file=10000,
    min_tags_per_message=10,
    max_tags_per_message=30,
    time_spread_seconds=7200.0,        # 2 hours
    ensure_unique_timestamps=True,     # Guarantee ordering
    partition_time_across_files=True   # Non-overlapping times
)
```

#### Example 3: Custom Tag Lengths

```python
# Generate data with specific tag characteristics
stats = generate_traffic_files(
    output_folder="test_data/custom",
    protocols=["FIX"],
    num_files_per_protocol=1,
    min_messages_per_file=5000,
    max_messages_per_file=5000,
    min_tags_per_message=3,
    max_tags_per_message=5,
    min_tag_name_length=8,             # Longer tag names
    max_tag_name_length=20,
    min_tag_value_length=10,           # Longer values
    max_tag_value_length=100
)
```

### Running Performance Tests

#### Example 1: Basic Comparison Test

```python
from run_comparison_test import run_merge_jsons_performance_comparison

# Define a simple message processor
def my_processor(version, msg, metrics):
    """Count messages per version."""
    metrics['total'] = metrics.get('total', 0) + 1
    metrics['version'] = version

# Run test
results = run_merge_jsons_performance_comparison(
    test_folder="test_data/small",
    message_processor=my_processor
)

print(f"Speedup: {results['speedup']:.2f}x")
```

#### Example 2: Custom Metrics Tracking

```python
def track_protocols_and_errors(version, msg, metrics):
    """Track both protocol counts and timestamp errors."""
    # Initialize metrics
    if 'protocols' not in metrics:
        metrics['protocols'] = {}
        metrics['timestamp_errors'] = 0
        metrics['last_timestamp'] = None

    # Count by protocol
    protocol = msg.get("#protocol", "unknown")
    metrics['protocols'][protocol] = metrics['protocols'].get(protocol, 0) + 1

    # Check timestamp ordering
    current_ts = msg.get("#timestamp")
    if metrics['last_timestamp'] and current_ts < metrics['last_timestamp']:
        metrics['timestamp_errors'] += 1
    metrics['last_timestamp'] = current_ts

    metrics['version'] = version

# Run test
results = run_merge_jsons_performance_comparison(
    test_folder="test_data/medium",
    message_processor=track_protocols_and_errors
)

# Access custom metrics
print("Test A metrics:", results['test_a']['custom_metrics'])
print("Test B metrics:", results['test_b']['custom_metrics'])
```

#### Example 3: Direct Test Runner Usage

```python
from run_comparison_test import run_single_merge_test
from ex_tmodel2.utils.merge_jsons import find_jsons

# Find files
file_protocols = find_jsons("test_data/small", ["FIX", "ITCH", "OUCH"])


# Define processor
def count_messages(version, msg, metrics):
   metrics['count'] = metrics.get('count', 0) + 1
   metrics['version'] = version


# Run single test
time, count, metrics = run_single_merge_test(
   file_protocols,
   version="Test1",
   message_processor=count_messages
)

print(f"Processed {count} messages in {time:.3f}s")
print(f"Throughput: {count / time:,.0f} msg/s")
print(f"Custom metrics: {metrics}")
```

---

## Examples

### Complete Workflow Example

```python
from generate_json_data import generate_traffic_files
from run_comparison_test import run_merge_jsons_performance_comparison

# Step 1: Generate test data
print("Step 1: Generating test data...")
stats = generate_traffic_files(
    output_folder="my_test",
    protocols=["FIX", "ITCH"],
    num_files_per_protocol=1,
    min_messages_per_file=10000,
    max_messages_per_file=10000,
    min_tags_per_message=10,
    max_tags_per_message=20
)
print(f"Generated {sum(stats.values())} messages")

# Step 2: Define custom processor
def analyze_performance(version, msg, metrics):
    """Track performance metrics."""
    if 'start_time' not in metrics:
        import time
        metrics['start_time'] = time.time()
        metrics['message_count'] = 0
        metrics['total_tag_count'] = 0

    metrics['message_count'] += 1
    metrics['total_tag_count'] += len(msg) - 1  # Exclude #timestamp
    metrics['version'] = version

# Step 3: Run performance test
print("\nStep 2: Running performance test...")
results = run_merge_jsons_performance_comparison(
    test_folder="my_test",
    message_processor=analyze_performance
)

# Step 4: Analyze results
print("\n=== Results ===")
print(f"Test A: {results['test_a']['merge_time']:.3f}s")
print(f"Test B: {results['test_b']['merge_time']:.3f}s")
print(f"Speedup: {results['speedup']:.2f}x ({results['speedup_pct']:+.1f}%)")
print(f"Time saved: {results['time_saved']:.3f}s")
```

### Message Processor Examples

#### Example 1: Timestamp Validator (Built-in)

```python
def track_timestamp_errors(version, msg, metrics):
    """Track timestamp ordering errors."""
    if 'timestamp_errors' not in metrics:
        metrics['timestamp_errors'] = 0
        metrics['last_timestamp'] = None

    current_ts = msg.get("#timestamp")
    if metrics['last_timestamp'] and current_ts < metrics['last_timestamp']:
        metrics['timestamp_errors'] += 1

    metrics['last_timestamp'] = current_ts
    metrics['version'] = version
```

#### Example 2: Protocol Counter

```python
def count_by_protocol(version, msg, metrics):
    """Count messages by protocol."""
    if 'by_protocol' not in metrics:
        metrics['by_protocol'] = {}

    protocol = msg.get("#protocol", "unknown")
    metrics['by_protocol'][protocol] = metrics['by_protocol'].get(protocol, 0) + 1
    metrics['version'] = version
```

#### Example 3: Tag Statistics

```python
def collect_tag_stats(version, msg, metrics):
    """Collect statistics about tags."""
    if 'tag_stats' not in metrics:
        metrics['tag_stats'] = {
            'total_tags': 0,
            'unique_tag_names': set(),
            'min_tags': float('inf'),
            'max_tags': 0
        }

    tag_count = len(msg) - 1  # Exclude #timestamp
    metrics['tag_stats']['total_tags'] += tag_count
    metrics['tag_stats']['unique_tag_names'].update(msg.keys())
    metrics['tag_stats']['min_tags'] = min(metrics['tag_stats']['min_tags'], tag_count)
    metrics['tag_stats']['max_tags'] = max(metrics['tag_stats']['max_tags'], tag_count)
    metrics['version'] = version
```

#### Example 4: No Processing (Performance Only)

```python
# Pass None to skip custom processing
results = run_merge_jsons_performance_comparison(
    test_folder="test_data/large",
    message_processor=lambda v, m, metrics: None  # No-op processor
)
```

---

## File Format

Generated files follow JSONL (JSON Lines) format where each line is a valid JSON object:

```json
{"#timestamp": "2025-01-15T10:23:45.123456Z", "#protocol": "FIX", "tag1": "value1", "tag2": 12345}
{"#timestamp": "2025-01-15T10:23:45.234567Z", "#protocol": "FIX", "tag1": "value2", "tag2": 67890}
```

**Key Properties**:
- Each line is a complete, valid JSON object
- `#timestamp` field contains ISO 8601 timestamp
- `#protocol` field is automatically added during merge
- Timestamps are strictly monotonically increasing within each file
- Tag names and values are randomly generated
- Values can be string, int, float, or boolean types

---

## Configuration Parameters

### generate_json_data.py

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_folder` | str | Required | Directory to save generated files |
| `protocols` | List[str] | Required | List of protocol names (e.g., ["FIX", "ITCH"]) |
| `num_files_per_protocol` | int | 1 | Number of files to generate per protocol |
| `min_messages_per_file` | int | 100 | Minimum messages per file |
| `max_messages_per_file` | int | 1000 | Maximum messages per file |
| `min_tags_per_message` | int | 5 | Minimum tags per message (excluding #timestamp) |
| `max_tags_per_message` | int | 20 | Maximum tags per message |
| `min_tag_name_length` | int | 3 | Minimum length of tag names |
| `max_tag_name_length` | int | 15 | Maximum length of tag names |
| `min_tag_value_length` | int | 5 | Minimum length of string tag values |
| `max_tag_value_length` | int | 50 | Maximum length of string tag values |
| `time_spread_seconds` | float | 3600.0 | Time range in seconds for spreading messages |
| `ensure_unique_timestamps` | bool | True | Guarantee strictly monotonic timestamps |
| `partition_time_across_files` | bool | False | Divide time range among files to avoid overlaps |

### run_comparison_test.py

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `test_folder` | str | Required | Path to folder containing test files |
| `message_processor` | Callable | Required | Function to process each message |
| `protocols` | List[str] | None | Protocol list (auto-detects if None) |
| `test_name` | str | None | Test name (uses folder name if None) |

---

## Performance Metrics

The framework automatically collects and reports these metrics:

### Standard Metrics

| Metric | Description |
|--------|-------------|
| **Merge Time** | Total time to merge all messages (seconds) |
| **Message Count** | Total number of messages processed |
| **Throughput** | Messages processed per second |
| **Speedup** | Ratio of Test A time to Test B time |
| **Speedup %** | Percentage improvement |
| **Time Saved** | Absolute time difference (seconds) |

### Custom Metrics

Any metrics you track in your `message_processor` function will be:
- Stored in the `custom_metrics` dictionary
- Displayed in the "Custom Metrics" section of the output
- Included in the results dictionary for programmatic access

---

## Troubleshooting

### Issue: "No traffic_*.json files found"

**Cause**: The test folder doesn't contain any files matching the pattern.

**Solution**:
- Verify the folder path is correct
- Ensure files are named `traffic_<protocol>.json`
- Run `generate_json_data.py` first to create test files

### Issue: "Cannot generate N unique timestamps"

**Cause**: Not enough time range for the requested number of messages.

**Solution**:
- Increase `time_spread_seconds` parameter
- Reduce number of messages
- The algorithm needs ~1μs between messages for uniqueness

### Issue: Message count mismatch

**Cause**: File may be corrupted or contain empty lines.

**Solution**:
- Check for empty lines in JSONL files
- Verify each line contains valid JSON
- Regenerate the test data

### Issue: Performance numbers seem inconsistent

**Cause**: System load, disk cache, or other processes affecting timing.

**Solution**:
- Run tests multiple times and average results
- Close other applications during testing
- Run a warmup test first to prime disk cache
- Use SSD storage for test data

### Issue: Custom metrics not appearing

**Cause**: Processor function not adding data to metrics dict.

**Solution**:
- Ensure processor modifies the `metrics` parameter
- Check that metrics keys don't start with underscore
- Verify `version` parameter is being set

---

## Recommended Practices

1. **Generate data once, test many times**
   - Separate data generation from testing
   - Reuse datasets across multiple test runs
   - Share datasets with team members

2. **Use realistic data sizes**
   - Test with production-like message counts
   - Include various tag counts and sizes
   - Use multiple protocols if applicable

3. **Define clear test objectives**
   - Know what you're measuring
   - Use custom processors for specific metrics
   - Document test configurations

4. **Run multiple iterations**
   - Performance can vary between runs
   - Average results from 3-5 runs
   - Discard first run (cold cache)

5. **Version your test data**
   - Use descriptive folder names
   - Document generation parameters
   - Track test data alongside code

6. **Monitor system resources**
   - Check disk I/O during tests
   - Monitor memory usage
   - Close unnecessary applications

---

## Advanced Usage

### Testing Different Merge Configurations

The current implementation uses a fixed merge configuration. To test different configurations, you can modify `run_single_merge_test()` to accept additional parameters:

```python
# In the version parameter, encode different configurations
# Test A: with validation
# Test B: without validation

def run_single_merge_test(file_protocols, version, message_processor):
    # Decode version to get configuration
    validate = (version == "A")

    for message in merge_jsonl_with_protocol(
        file_protocols=file_protocols,
        validate_timestamps=validate
    ):
        # ... process message
```

### Batch Testing

Run tests on multiple datasets:

```python
from pathlib import Path
from run_comparison_test import run_merge_jsons_performance_comparison

test_folders = ["test_data/small", "test_data/medium", "test_data/large"]

for folder in test_folders:
    if Path(folder).exists():
        print(f"\n{'='*60}")
        print(f"Testing: {folder}")
        print('='*60)

        results = run_merge_jsons_performance_comparison(
            folder,
            message_processor=track_timestamp_errors
        )

        print(f"Result: {results['speedup']:.2f}x speedup")
```

---

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the example code
- Examine the source code comments
- Create an issue in the project repository