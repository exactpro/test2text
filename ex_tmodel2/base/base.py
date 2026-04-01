# class StateUpdater:
#class OrderBookStateUpdater(StateUpdater):

#   update(State state, transaction : Transaction): State


#List of ideas
# 1) To have Signal class with field type and direction. Enum Type: OrderExecuted (ExecutionReport in FIX), OrderAdded (ExecutionReport in FIX), OrderCancelled (ExecutionReport in FIX)
# 2) To have Transaction class it is one input Signal and List of output signals
# 3) To Converter that can convert Message to Signal classes and its child classes for each protocol (FIX, ouch and etc)
# 4) There is need to have StateUpdater class probably for each State its own (for example class that build OrderBookState using signals)
# 5) Transaction splitter class that can split message flows into Transactions, probably specific for each protocol and project
# 6) ErrorCheck class with problem description
# 7) RuleCheck as class with check method and Transaction as input and outputs list of ErrorChecks, probably it needs old states as well and new states.
# 8) Engine  - init receives List of States, reader for messages, List of Converters, List of StateUpdaters. In run reads messages, splits into transactions, converts to signals,
        # updates States, and then run all checks, collects ErrorChecks and outputs it using ProblemCollector
# 9) Probably - we need to keep history of states for each Transaction
# 10) Each state has Save and Restore methods to store history and has possibility to start Engine from any state



from __future__ import annotations

from collections.abc import MutableMapping
from typing import Dict, List, Optional, Any, Iterable, Callable, Literal, Tuple, Set, Type
import json
import threading
import weakref

Event = Dict[str, Any]

# Registry mapping effect_type to effect class - populated by @register_effect decorator
EFFECT_TYPE_REGISTRY: Dict[str, Type["DownstreamEffect"]] = {}
EventLog = Iterable[Event]
MaterializedEventLog = List[Event]
SortDirection = Literal["asc", "desc"]

class Node:
    """
    Base class for all domain entities (Instrument, Order, Trade, DigitalTwin, etc.).

    A Node:
      • has a string key (unique in some context),
      • can belong to multiple collections,
      • can own named child collections,
      • can hold named unidirectional links to other nodes.

    Terminology:
    - "membership collections":
        Collections this node belongs to.
        Tracked in _member_of as {collection_name -> Collection}.

    - "child collections":
        Collections owned by this node and accessible via attributes,
        e.g. instrument.orders or twin.instruments.

    - "links":
        Named unidirectional references to other nodes,
        e.g. order.instrument.
    """

    def __init__(self, key: str) -> None:
        self.key: str = key

        # Collections this node is a member of:
        #   { collection_name : List[Collection] }
        # Multiple collections can have the same name (e.g., two different
        # "child_orders" collections from different owners)
        self._member_of: Dict[str, List[Collection]] = {}

        # Child collections owned by this node:
        #   { child_collection_name : Collection }
        self._children: Dict[str, Collection] = {}

        # Outbound unidirectional links:
        #   { link_name : Node }
        # example: order._links["instrument"] = instrument_node
        self._links: Dict[str, Node] = {}

    # ----------------------------------------------------------------------
    # Membership inspection
    # ----------------------------------------------------------------------
    @property
    def member_of(self) -> Dict[str, Collection]:
        """
        Return a flattened membership map:
            {collection_name: Collection}

        For backward compatibility, returns only the first collection for each name.
        If you need all collections with the same name, access _member_of directly.

        We return a copy so callers don't mutate our internal state directly.
        """
        return {name: collections[0] for name, collections in self._member_of.items() if collections}

    # ----------------------------------------------------------------------
    # Child collections management
    # ----------------------------------------------------------------------
    def create_child_collection(self, name: str) -> Collection:
        """
        Create a named child collection owned by this node.

        After creation, it becomes available as an attribute:
            instrument.orders
            twin.instruments
            order.children
        """
        if name in self._children:
            raise ValueError(
                f"Child collection '{name}' already exists on {self.key}"
            )

        col = Collection(name=name, owner=self)
        self._children[name] = col
        return col

    def get_child_collection(self, name: str) -> Collection:
        """
        Retrieve an existing child collection by name.
        """
        return self._children[name]

    # ----------------------------------------------------------------------
    # Link management (unidirectional only)
    # ----------------------------------------------------------------------
    def link_to(self, rel_name: str, target_node: Node) -> None:
        """
        Create or overwrite a named unidirectional link.

        Example:
            order.link_to("instrument", aapl)
            order.instrument  -> aapl
        """
        if not isinstance(target_node, Node):
            raise TypeError("link_to requires a Node target")
        self._links[rel_name] = target_node

    # ----------------------------------------------------------------------
    # Dynamic attribute access
    # ----------------------------------------------------------------------
    def __getattr__(self, name: str):
        """
        Fallback attribute resolution:
          1. child collections (e.g. instrument.orders, twin.instruments)
          2. named links      (e.g. order.instrument)

        This lets you write natural code like:
            twin.instruments["AAPL"] = aapl_node
            order.instrument         # -> instrument node
        """
        # child collections take priority
        if name in self._children:
            return self._children[name]

        # then named unidirectional links
        if name in self._links:
            return self._links[name]

        raise AttributeError(
            f"{name!r} not found on {self.__class__.__name__}({self.key})"
        )

    # ----------------------------------------------------------------------
    # Key management
    # ----------------------------------------------------------------------
    def change_key(self, new_key: str) -> None:
        """
        Change the key of this node and update it in all collections it belongs to.

        This method:
        1. Removes the node from all collections using the old key
        2. Updates the node's key
        3. Re-adds the node to all collections using the new key

        Args:
            new_key: The new key for this node

        Raises:
            ValueError: If new_key already exists in any of the collections
        """
        if new_key == self.key:
            # No change needed
            return

        old_key = self.key

        # First, check if new_key already exists in any collection
        for collection_name, collection_list in self._member_of.items():
            for collection in collection_list:
                if new_key in collection._items:
                    raise ValueError(
                        f"Cannot change key from '{old_key}' to '{new_key}': "
                        f"key '{new_key}' already exists in collection '{collection_name}'"
                    )

        # Collect all collections this node belongs to
        # We need to copy because we'll be modifying _member_of during the updates
        collections_to_update: List[Collection] = []
        for collection_list in self._member_of.values():
            collections_to_update.extend(collection_list)

        # Remove from all collections (using old key)
        for collection in collections_to_update:
            # Remove from the collection's internal dict
            # but preserve the membership record temporarily
            del collection._items[old_key]

        # Update the node's key
        self.key = new_key

        # Re-add to all collections (using new key)
        for collection in collections_to_update:
            # Add back with new key
            collection._items[new_key] = self
            # Membership was already set, so no need to update _member_of

    # ----------------------------------------------------------------------
    # Representation
    # ----------------------------------------------------------------------
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.key})"


class DirtyRegistry:
    """
    A lightweight utility designed to track objects whose internal state has changed,
    without duplicating entries or preventing those objects from being garbage-collected.

    It is especially useful in simulations, model frameworks, or testing systems where:
    - Only a small subset of entities change frequently (e.g., orders, instruments, sessions).
    - You want to later process or persist only the changed ones.
    - You need to avoid memory leaks and unnecessary scans over all states.

    Key Responsibilities
    - Collect changes efficiently - Each changed object is recorded once.
    - Avoid duplication - Adding the same object multiple times has no effect.
    - Auto-clean stale entries - Objects disappear when they are deleted elsewhere.
    - Provide snapshots - You can inspect all currently changed objects.
    - Support "drain" operation - You can consume and reset the registry in one call.
    """

    def __init__(self) -> None:
        self._dirty = weakref.WeakSet()
        self._counts: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()
        self._seq: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()
        self._counter = 0
        self._lock = threading.Lock()

    def mark(self, obj: "State") -> None:
        """
        Adds an object to the dirty set.
        Records optional metadata such as change count or last modification order.
        Thread-safe.

        Args:
            obj: The object to mark as dirty
        """
        with self._lock:
            self._dirty.add(obj)  # dedup by identity
            self._counts[obj] = self._counts.get(obj, 0) + 1
            self._counter += 1
            self._seq[obj] = self._counter  # last change order

    def snapshot(self) -> tuple:
        """
        Returns a tuple of all currently dirty objects, without clearing the registry.

        Returns:
            Tuple of all currently dirty objects
        """
        with self._lock:
            return tuple(self._dirty)

    def consume(self) -> Tuple[Tuple["State", int, int], ...]:
        """
        Returns all dirty objects and resets the registry.
        Optionally includes metadata (change count, sequence number).

        Returns:
            Tuple of tuples (obj, change_count, sequence_number) for all dirty objects before reset
        """
        with self._lock:
            items = tuple((obj, self._counts.get(obj, 0), self._seq.get(obj, 0)) for obj in self._dirty)
            # reset
            self._dirty = weakref.WeakSet()
            self._counts = weakref.WeakKeyDictionary()
            self._seq = weakref.WeakKeyDictionary()
            self._counter = 0
            return items

    def __len__(self) -> int:
        """
        Returns how many currently dirty objects are being tracked.

        Returns:
            Number of dirty objects
        """
        with self._lock:
            return sum(1 for _ in self._dirty)


class InputSignal:
    """
    Represents an input signal that triggers a state transition.

    An InputSignal encapsulates the information about an external event
    or message that causes a State to change. This could represent things
    like order executions, order additions, cancellations, market data updates, etc.

    Attributes:
        signal_type: A string identifier for the type of signal
        signal_memo: Optional string comment for the signal
        signal_testcase: Optional string identifier for the test case this signal belongs to
        timestamp: Optional string timestamp for when the signal occurred
    """

    def __init__(
        self,
        signal_type: str,
        signal_memo: Optional[str] = None,
        signal_testcase: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> None:
        self.signal_type: str = signal_type
        self.signal_memo: Optional[str] = signal_memo
        self.signal_testcase: Optional[str] = signal_testcase
        self.timestamp: Optional[str] = timestamp

    def __repr__(self) -> str:
        return (
            f"InputSignal(signal_type={self.signal_type!r}, "
            f"signal_memo={self.signal_memo!r}, signal_testcase={self.signal_testcase!r}, "
            f"timestamp={self.timestamp!r})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: Dict[str, Any] = {
            "signal_type": self.signal_type,
        }
        if self.signal_memo is not None:
            result["signal_memo"] = self.signal_memo
        if self.signal_testcase is not None:
            result["signal_testcase"] = self.signal_testcase
        if self.timestamp is not None:
            result["timestamp"] = self.timestamp
        return result


class DownstreamEffect:
    """
    Represents a downstream effect produced by a state transition.

    A DownstreamEffect encapsulates information about side effects or
    output signals that result from processing an InputSignal. These could
    represent things like outbound messages, notifications, or changes
    to other states.

    Attributes:
        effect_type: A string identifier for the type of effect
        state_transition_timestamp: Optional timestamp for when the state transition occurred
        Additional attributes can be added and will be preserved during serialization.
    """

    def __init__(self, effect_type: str, state_transition_timestamp: Optional[str] = None, **kwargs) -> None:
        self.effect_type: str = effect_type
        self.state_transition_timestamp: Optional[str] = state_transition_timestamp
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        attrs = ', '.join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"DownstreamEffect({attrs})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization. Preserves all attributes."""
        result = dict(self.__dict__)
        # Only include state_transition_timestamp if it has a value
        if self.state_transition_timestamp is None:
            result.pop("state_transition_timestamp", None)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DownstreamEffect":
        """Create a DownstreamEffect from a dictionary."""
        return cls(**data)


def register_effect(effect_type):
    """
    Decorator to auto-register effect classes in EFFECT_TYPE_REGISTRY.

    Usage:
        @register_effect(DownstreamEffectType.ORDER_ACCEPTED)
        class OrderAcceptedEffect(DownstreamEffect):
            ...
    """
    def decorator(cls: Type[DownstreamEffect]) -> Type[DownstreamEffect]:
        EFFECT_TYPE_REGISTRY[effect_type.value] = cls
        return cls
    return decorator


def create_effect_from_dict(data: Dict[str, Any]) -> DownstreamEffect:
    """
    Factory function to create a typed effect from a dictionary.

    Args:
        data: Dictionary containing effect data with 'effect_type' key

    Returns:
        The appropriate typed effect instance

    Raises:
        ValueError: If effect_type is not recognized
    """
    effect_type = data.get("effect_type")
    if effect_type is None:
        raise ValueError("Missing 'effect_type' in effect data")

    effect_class = EFFECT_TYPE_REGISTRY.get(effect_type)
    if effect_class is None:
        raise ValueError(f"Unknown effect_type: {effect_type}")

    try:
        effect = effect_class.from_dict(data)
        return effect
    except Exception as e:
        print(f"create_effect_from_dict {data}")
        raise e


class StateTransition:
    """
    Represents a complete state transition consisting of an input signal
    and its resulting downstream effects.

    A StateTransition is the fundamental unit of state change. It encapsulates:
    - The InputSignal that triggered the transition
    - A list of DownstreamEffects that resulted from processing the signal
    - Optional raw data (events) that were used to construct this transition

    Eventually, State objects will be updated only through receiving
    StateTransition objects, ensuring all state changes are traceable
    and auditable.

    Attributes:
        input_signal: The InputSignal that triggered this transition
        downstream_effects: List of DownstreamEffect objects produced by this transition
        raw_data: The raw events that were used to construct this transition
    """

    def __init__(
        self,
        input_signal: InputSignal,
        downstream_effects: Optional[List[DownstreamEffect]] = None,
        raw_data: Optional[MaterializedEventLog] = None
    ) -> None:
        self.input_signal: InputSignal = input_signal
        self.downstream_effects: List[DownstreamEffect] = (
            downstream_effects if downstream_effects is not None else []
        )
        self.raw_data: MaterializedEventLog = (
            raw_data if raw_data is not None else []
        )

    def add_effect(self, effect: DownstreamEffect) -> None:
        """Add a downstream effect to this transition."""
        self.downstream_effects.append(effect)

    def __repr__(self) -> str:
        return (
            f"StateTransition(input_signal={self.input_signal!r}, "
            f"downstream_effects={self.downstream_effects!r})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "input_signal": self.input_signal.to_dict(),
            "downstream_effects": [e.to_dict() for e in self.downstream_effects],
        }


def write_transitions_to_file(
    transitions: List[StateTransition],
    file_path: str,
    skip_no_effects: bool = False,
) -> None:
    """
    Write a list of StateTransitions to a file as JSON lines.

    Each transition is written as a separate JSON object on its own line,
    making the file easy to read and process line by line.

    Args:
        transitions: List of StateTransition objects to serialize
        file_path: Path to the output file
        skip_no_effects: If True, skip transitions without effects
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        for transition in transitions:
            if skip_no_effects and not transition.downstream_effects:
                continue
            try:
                json_line = json.dumps(transition.to_dict(), ensure_ascii=False)
                f.write(json_line + '\n')
            except Exception as e:
                print(f"Error serializing transition: {transition}")
                raise e


def read_transitions_from_file(
    file_path: str,
    use_typed_effects: bool = True
) -> List[StateTransition]:
    """
    Read a list of StateTransitions from a JSON lines file.

    Args:
        file_path: Path to the input file
        use_typed_effects: If True, deserialize effects into their proper typed
                          classes (OrderAcceptedEffect, etc.). If False, use
                          generic DownstreamEffect. Default is True.

    Returns:
        List of StateTransition objects
    """
    if use_typed_effects:
        effect_factory = create_effect_from_dict
    else:
        effect_factory = DownstreamEffect.from_dict

    transitions = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            signal_data = data["input_signal"]
            input_signal = InputSignal(
                signal_type=signal_data["signal_type"],
                signal_memo=signal_data.get("signal_memo"),
                signal_testcase=signal_data.get("signal_testcase"),
                timestamp=signal_data.get("timestamp")
            )
            effects = [
                effect_factory(e)
                for e in data.get("downstream_effects", [])
            ]
            transitions.append(StateTransition(input_signal, effects))
    return transitions


class TransitionAudit:
    """
    Represents the result/audit of applying a state transition.

    A TransitionAudit captures information about what happened when a
    StateTransition was applied to a State object. This can include
    validation results, warnings, errors, or any other audit information.

    Subclasses can extend this to provide domain-specific audit information.
    """

    def __init__(self) -> None:
        pass


class State(Node):
    """
    Base class for nodes that represent stateful entities like OrderBook and Exchange.

    This class extends Node and is intended for nodes that maintain state
    and may require additional state management functionality.
    """
    _registry: DirtyRegistry = DirtyRegistry()

    def __init__(self, key: str) -> None:
        super().__init__(key)

    def signature(self) -> str:
        """
        Return a string signature representing the current state.

        This method should be overridden by subclasses to provide a meaningful
        state representation. The default implementation returns an empty string.

        Returns:
            String representation of the current state
        """
        return ""

    def mark_dirty(self) -> None:
        """
        Mark this state object as dirty in the shared registry.

        This method registers the current state instance in the DirtyRegistry,
        indicating that its internal state has changed and may need to be
        processed, persisted, or synchronized.

        The registry uses weak references, so marking an object as dirty
        does not prevent it from being garbage collected.
        """
        self._registry.mark(self)

    def transition(self, state_transition: StateTransition) -> TransitionAudit:
        """
        Apply a state transition to this state object.

        This method is the primary mechanism for updating state. It receives
        a StateTransition object containing an InputSignal and processes it
        to update the state accordingly.

        Subclasses should override this method to implement domain-specific
        state transition logic based on the input signal type.

        Args:
            state_transition: The StateTransition object containing the input
                            signal and any downstream effects to apply.

        Returns:
            TransitionAudit object containing audit information about the transition.

        Example:
            class OrderBookState(State):
                def transition(self, state_transition: StateTransition) -> TransitionAudit:
                    signal = state_transition.input_signal
                    if signal.signal_type == "order_added":
                        self._handle_order_added(signal)
                    elif signal.signal_type == "order_cancelled":
                        self._handle_order_cancelled(signal)
                    self.mark_dirty()
                    return TransitionAudit()
        """
        return TransitionAudit()


class Collection(MutableMapping):
    """
    Dictionary-like container mapping keys -> Node.

    Behavior:
    - You can treat it like a dict:
        collection[node.key] = node
        node2 = collection["ORD-001"]

    - When you insert a node:
        - The node becomes retrievable from this collection by that key.
        - The node records that it is a member of this collection's name.

      So if:
          twin.instruments["AAPL"] = instrument_node
      then:
          instrument_node.member_of
      will include:
          { "instruments": <that same Collection instance> }

    - When you remove a node:
        - The node is removed from this collection.
        - The node's membership record for this collection name is removed.
    """

    def __init__(self, name: str, owner: Optional[Node] = None) -> None:
        self.name: str = name
        self._items: Dict[str, Node] = {}
        # The node that 'owns' this collection, e.g. a DigitalTwin or Instrument
        self.owner: Optional[Node] = owner

    # ------------------------------------------------------------------
    # MutableMapping required interface
    # ------------------------------------------------------------------
    def __getitem__(self, key: str) -> Node:
        return self._items[key]

    def __setitem__(self, key: str, node: Node) -> None:
        if not isinstance(node, Node):
            raise TypeError("Collection can only store Node instances")

        # Check if this is an amendment (key already exists) or addition (new key)
        is_amendment = key in self._items
        old_node = self._items.get(key) if is_amendment else None

        self._items[key] = node
        # Track membership on the node, keyed by this collection's name
        # Append to the list if it exists, otherwise create a new list
        if self.name not in node._member_of:
            node._member_of[self.name] = []

        # Check if this exact collection object is already in the list
        # Note: We use identity check (is) not equality check (==) because
        # Collection inherits from MutableMapping which implements __eq__
        # to compare by contents, not identity
        already_in_list = any(c is self for c in node._member_of[self.name])
        if not already_in_list:
            node._member_of[self.name].append(self)

        # Call appropriate callback on owner if it exists
        if self.owner:
            singular_name = self._singularize_name(self.name)

            if is_amendment:
                # For collection "child_orders", look for "on_child_order_replaced" method
                callback_name = f"on_{singular_name}_replaced"
                callback = getattr(self.owner, callback_name, None)
                if callable(callback):
                    callback(old_node, node)
            else:
                # For collection "child_orders", look for "on_child_order_added" method
                callback_name = f"on_{singular_name}_added"
                callback = getattr(self.owner, callback_name, None)
                if callable(callback):
                    callback(node)

    def __delitem__(self, key: str) -> None:
        node = self._items.pop(key)
        # Remove this exact collection object from the node's membership list
        if self.name in node._member_of:
            # Find and remove this collection using identity comparison
            node._member_of[self.name] = [c for c in node._member_of[self.name] if c is not self]
            # Clean up empty lists
            if not node._member_of[self.name]:
                del node._member_of[self.name]

        # Call callback on owner if it exists
        # For collection "child_orders", look for "on_child_order_deleted" method
        if self.owner:
            singular_name = self._singularize_name(self.name)
            callback_name = f"on_{singular_name}_deleted"
            callback = getattr(self.owner, callback_name, None)
            if callable(callback):
                callback(node)

    def _singularize_name(self, name: str) -> str:
        """
        Convert a collection name to its singular form for callback naming.

        Simple implementation: removes trailing 's' if present.
        Examples:
            "child_orders" -> "child_order"
            "instruments" -> "instrument"
            "trades" -> "trade"

        Note: This is a simple heuristic. For more complex cases,
        override this method or use a proper pluralization library.
        """
        if name.endswith('s'):
            return name[:-1]
        return name

    def __iter__(self):
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    # ------------------------------------------------------------------
    # Convenience helpers (not required by MutableMapping, but nice)
    # ------------------------------------------------------------------
    def keys(self):
        return self._items.keys()

    def values(self):
        return self._items.values()

    def items(self):
        return self._items.items()

    def get_default_node(self):
        return next(iter(self._items.values()))

    def filter_present_keys(self, keys: Iterable[str]) -> Set[str]:
        """
        Return the set of keys from the given iterable that are present in this collection.

        Args:
            keys: An iterable of keys to check

        Returns:
            A set containing only the keys that exist in this collection
        """
        return {key for key in keys if key in self._items}

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        owner_part = f", owner={self.owner.key}" if self.owner else ""
        return (
            f"Collection({self.name}{owner_part}, "
            f"keys={list(self._items.keys())})"
        )

class EventLogConverter:
    """
    Base class for processing EventLog streams with optional State tracking.

    This class provides:
    - State object management for event processing context
    - Conversion methods between different event log formats
    """

    def __init__(self) -> None:
        """Initialize the EventLogConverter with no State set."""
        self._state: Optional[State] = None

    def set_state(self, state: State) -> None:
        """
        Set the State object for this converter.

        Args:
            state: The State object to use for event processing
        """
        self._state = state

    def event_log_to_materialized(self, event_log: EventLog) -> MaterializedEventLog:
        """
        Convert an EventLog to a MaterializedEventLog.

        Takes an EventLog (iterable of events) and materializes it into a list.
        Uses event_log_to_event_log as the basis, so any transformations applied
        in that method will be included.

        Args:
            event_log: An iterable of Event dictionaries

        Returns:
            A MaterializedEventLog (list of events)

        Examples:
            >>> converter = EventLogConverter()
            >>> def event_generator():
            ...     yield {"id": 1, "value": "A"}
            ...     yield {"id": 2, "value": "B"}
            >>> materialized = converter.event_log_to_materialized(event_generator())
            >>> len(materialized)
            2
        """
        return list(self.event_log_to_event_log(event_log))

    def event_log_to_event_log(self, event_log: EventLog) -> EventLog:
        """
        Convert an EventLog to an EventLog (identity transformation).

        This method can be overridden in subclasses to apply transformations
        to the event stream, such as filtering, mapping, or enriching events.

        Args:
            event_log: An iterable of Event dictionaries

        Returns:
            An EventLog (iterable of events)

        Examples:
            >>> class FilteringConverter(EventLogConverter):
            ...     def event_log_to_event_log(self, event_log):
            ...         # Filter events based on some criteria
            ...         for event in event_log:
            ...             if event.get("status") == "active":
            ...                 yield event
        """
        for event in event_log:
            yield event

    def streams_to_event_log(self, streams: Dict[str, EventLog]) -> EventLog:
        """
        Merge multiple named event streams into a single EventLog.

        Takes a dictionary of named event streams and merges them into a single
        iterable. Default implementation adds a "#stream" tag to each event, then
        passes through event_log_to_event_log for any additional transformations.

        Args:
            streams: Dictionary mapping stream names to EventLog iterables

        Returns:
            A merged EventLog (iterable of events with "#stream" tags)

        Examples:
            >>> converter = EventLogConverter()
            >>> streams = {
            ...     "stream1": [{"id": 1, "value": "A"}],
            ...     "stream2": [{"id": 2, "value": "B"}]
            ... }
            >>> merged = list(converter.streams_to_event_log(streams))
            >>> merged[0]["#stream"]
            'stream1'
            >>> len(merged)
            2

            Override for custom merging logic:
            >>> class CustomConverter(EventLogConverter):
            ...     def streams_to_event_log(self, streams):
            ...         # Custom interleaving or filtering logic
            ...         for stream_name, event_log in streams.items():
            ...             for event in event_log:
            ...                 yield event  # No stream tag
        """
        # Helper generator to merge streams and add tags
        def merge_streams():
            for stream_name, event_log in streams.items():
                for event in event_log:
                    tagged_event = event.copy()
                    tagged_event["#stream"] = stream_name
                    yield tagged_event

        # Pass through event_log_to_event_log for any transformations
        for event in self.event_log_to_event_log(merge_streams()):
            yield event

    def streams_to_materialized(self, streams: Dict[str, EventLog]) -> MaterializedEventLog:
        """
        Merge multiple named event streams into a MaterializedEventLog.

        Takes a dictionary of named event streams and merges them into a single
        materialized list. This is a convenience method that combines
        streams_to_event_log and to_materialized.

        Args:
            streams: Dictionary mapping stream names to EventLog iterables

        Returns:
            A merged MaterializedEventLog (list of events)

        Examples:
            >>> converter = EventLogConverter()
            >>> streams = {
            ...     "orders": [{"id": 1, "type": "order"}],
            ...     "trades": [{"id": 2, "type": "trade"}]
            ... }
            >>> merged = converter.streams_to_materialized(streams)
            >>> len(merged)
        """
        return self.event_log_to_materialized(self.streams_to_event_log(streams))