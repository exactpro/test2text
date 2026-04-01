"""
Store Transitions Module

This module provides a class for storing transitions to files for later analysis.
It allows capturing transition data with custom formatting and automatic file rotation.
"""

import json
import os
from pathlib import Path
from typing import Optional, Callable, Any, Dict

from ex_tmodel2.base.rule_base import ReportedRuleData, NoRelevantCheckClass
from ex_tmodel2.exchange import ModelExchange
from ex_tmodel2.exchange.exchange import ExchangeTransitionAudit
from ex_tmodel2.exchange.model_base import ModelStateTransition


def default_transition_formatter(
    exchange: ModelExchange,
    transition: ModelStateTransition,
    exchange_next: ModelExchange,
    audit_data: ExchangeTransitionAudit,
    rules: dict[str, list[ReportedRuleData] | NoRelevantCheckClass]
) -> str:
    """
    Default formatter that converts transition data to a dictionary.

    Override this by passing a custom formatter to StoreTransitions.
    """
    return str({
        "input_signal": transition.input_signal.to_dict(),
        "downstream_effects": [e.to_dict() for e in transition.downstream_effects],
        "audit": {
            "new_child_order_keys": list(audit_data.new_child_order_keys) if audit_data.new_child_order_keys else [],
            "testcases": list(audit_data.testcases) if audit_data.testcases else [],
        }
    }) + "\n"


class StoreTransitions:
    """
    Stores transitions to files for later analysis.

    This class captures transition data and writes it to files with automatic
    rotation based on the number of transitions per file.

    Usage:
        store = StoreTransitions(
            output_folder="output/transitions",
            transitions_per_file=1000
        )

        # In your processing loop:
        store.store(exchange, transition, exchange_next, audit_data)

        # When done:
        store.close()

    Attributes:
        output_folder: Directory where transition files will be stored
        transitions_per_file: Number of transitions to store in each file before rotating
        formatter: Custom function to format transition data
        file_prefix: Prefix for output files
        file_extension: Extension for output files
    """

    def __init__(
        self,
        output_folder: str,
        transitions_per_file: int = 1000,
        formatter: Optional[Callable[[ModelExchange, ModelStateTransition, ModelExchange, ExchangeTransitionAudit, dict], str]] = None,
        file_prefix: str = "state_transitions",
        file_extension: str = ".txt",
    ):
        """
        Initialize the StoreTransitions instance.

        :param output_folder: Directory where transition files will be stored
        :param transitions_per_file: Number of transitions per file before rotating (default: 1000)
        :param formatter: Custom formatter function (default: default_transition_formatter)
        :param file_prefix: Prefix for output files (default: "state_transitions")
        :param file_extension: File extension (default: ".txt")
        """
        self.output_folder = output_folder
        self.transitions_per_file = transitions_per_file
        self.formatter = formatter or default_transition_formatter
        self.file_prefix = file_prefix
        self.file_extension = file_extension

        # Internal state
        self._transition_count = 0
        self._file_index = 0
        self._current_file = None

        # Ensure output folder exists
        Path(output_folder).mkdir(parents=True, exist_ok=True)

    def _get_current_file_path(self) -> str:
        """Get the path for the current output file."""
        if self.transitions_per_file:
            filename = f"{self.file_prefix}_{self._file_index:04d}{self.file_extension}"
        else:
            filename = f"{self.file_prefix}{self.file_extension}"
        return os.path.join(self.output_folder, filename)

    def _open_new_file(self) -> None:
        """Open a new output file."""
        if self._current_file is not None:
            self._current_file.close()

        file_path = self._get_current_file_path()
        self._current_file = open(file_path, "w", encoding='utf-8')

    def _ensure_file_open(self) -> None:
        """Ensure a file is open for writing."""
        if self._current_file is None:
            self._open_new_file()

    def store(
        self,
        exchange: ModelExchange,
        transition: ModelStateTransition,
        exchange_next: ModelExchange,
        audit_data: ExchangeTransitionAudit,
        rules: dict[str, list[ReportedRuleData] | NoRelevantCheckClass]
    ) -> None:
        """
        Store the transition data to file.

        This method formats the transition data using the configured formatter
        and writes it to the current output file. Files are rotated automatically
        when the transition limit is reached.

        :param exchange: The exchange state before the transition
        :param transition: The state transition being applied
        :param exchange_next: The exchange state after the transition
        :param audit_data: Audit data from the transition
        """
        self._ensure_file_open()

        # Format the transition data
        formatted_data = self.formatter(exchange, transition, exchange_next, audit_data, rules)

        # Write to file first
        self._current_file.write(formatted_data)
        self._transition_count += 1

        # Rotate AFTER writing if we've hit the limit (0 means no rotation)
        if self.transitions_per_file and self._transition_count >= self.transitions_per_file:
            self._current_file.close()
            self._current_file = None
            self._file_index += 1
            self._transition_count = 0

    def close(self) -> None:
        """Close the current output file."""
        if self._current_file is not None:
            self._current_file.close()
            self._current_file = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

    def __del__(self):
        """Ensure file is closed when object is garbage collected."""
        self.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored transitions."""
        total_transitions = self._file_index * self.transitions_per_file + self._transition_count
        return {
            "total_transitions": total_transitions,
            "files_created": self._file_index + (1 if self._current_file else 0),
            "current_file_transitions": self._transition_count,
            "output_folder": self.output_folder,
        }