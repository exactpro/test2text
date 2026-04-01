from __future__ import annotations

from typing import Optional, Any, Callable, List

from .base import EventLogConverter, Event, EventLog, MaterializedEventLog, SortDirection

class EventLogSorter(EventLogConverter):
    """
    Sorts EventLog streams.

    This class extends EventLogConverter and provides functionality to:
    - Sort and materialize EventLog iterables into MaterializedEventLog lists
    - Manage State through the parent class

    Inherits:
        EventLogConverter: Provides state management functionality
    """

    def __init__(self) -> None:
        """Initialize the EventLogSorter by calling parent constructor."""
        super().__init__()

    def get_sort_key(
        self,
        event: Event) -> Any:
        """
        Get the sort key for a given event.

        This method can be overridden in subclasses to customize sorting behavior.

        Args:
            event: The event to get the sort key for

        Returns:
            The sort key value for the event

        Examples:
            To customize sorting, inherit from EventLogSorter and override this method:

            >>> class CustomSorter(EventLogSorter):
            ...     def get_sort_key(self, event):
            ...         # Custom sorting logic
            ...         return event.get("#custom_field", 0)
        """
        return event.get("#default_field", 0)

    def get_direction(self) -> SortDirection:
        """
        Get the sort direction.

        This method can be overridden in subclasses to customize the default
        sort direction without having to pass it as a parameter.

        Returns:
            The sort direction - "asc" for ascending or "desc" for descending

        Examples:
            To customize sort direction, inherit from EventLogSorter and override this method:

            >>> class DescendingSorter(EventLogSorter):
            ...     def get_direction(self):
            ...         return "desc"
        """
        return "asc"

    def event_log_to_materialized(
        self,
        event_log: EventLog
    ) -> MaterializedEventLog:
        """
        Sort and materialize an EventLog.

        Takes an EventLog (iterable of events) and returns a MaterializedEventLog
        (list of events), sorted according to the specified criteria.

        Args:
            event_log: An iterable of Event dictionaries
            direction: Sort direction - "asc" for ascending (default), "desc" for descending

        Returns:
            A sorted list of Event dictionaries

        Raises:
            ValueError: If direction is not "asc" or "desc"

        """
        # Materialize the event log into a list
        materialized_events: MaterializedEventLog = list(event_log)

        # Create a key function that uses get_sort_key
        def key_func(event: Event) -> Any:
            return self.get_sort_key(event)

        # Determine reverse flag from direction
        reverse_flag = (self.get_direction() == "desc")

        # Sort the materialized events
        sorted_events = sorted(materialized_events, key=key_func, reverse=reverse_flag)

        return sorted_events


