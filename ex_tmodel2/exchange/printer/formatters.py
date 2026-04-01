"""
Transition Formatters Module

This module contains formatter functions for use with StoreTransitions.
Each formatter takes (exchange, transition, exchange_next, audit_data, rules) and returns a string.
"""

import json
from dataclasses import asdict
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List

from ex_tmodel2.base.base import DownstreamEffect
from ex_tmodel2.base.rule_base import ReportedRuleData, NoRelevantCheckClass
from ex_tmodel2.exchange import ModelExchange
from ex_tmodel2.exchange.downstream_effects import (
    OrderAcceptedEffect,
    OrderCanceledEffect,
    OrderReplacedEffect,
    OrderExecutedEffect,
    TradeEffect, InstrumentStatusEffect, IcebergReplenishmentExtraChildOrder,
)
from ex_tmodel2.exchange.exchange import ExchangeTransitionAudit
from ex_tmodel2.exchange.model_base import ModelStateTransition

class ExchangeFormatterConfig:
    OUTPUT_RAW_DATA=False

def format_downstream_effect(transition: ModelStateTransition, lines,
        exchange_next: ModelExchange
    ) -> None:
    """
    Format a DownstreamEffect based on its type.
    """
    current_instrument = ""

    # Downstream effects
    if transition.downstream_effects:
        lines.append(f"Effects({len(transition.downstream_effects)}):")
        for effect in transition.downstream_effects:
            if isinstance(effect, OrderExecutedEffect):
                parts = [f"Execute {effect.key}"]
                parts.append(f"price={effect.price}")
                parts.append(f"qty={effect.quantity}")
                if effect.trade_match_id is not None:
                    parts.append(f"match_id={effect.trade_match_id}")
                if effect.printable is not None:
                    parts.append(f"printable={effect.printable.name}")
                if effect.last_liquidity_indicator is not None:
                    parts.append(f"liquidity={effect.last_liquidity_indicator.name}")
                if effect.timestamp is not None:
                    parts.append(f"ts={effect.timestamp}")
                lines.append(" ".join(parts))

            elif isinstance(effect, OrderAcceptedEffect):
                underlying = exchange_next.instruments[effect.instrument_key].underlying

                if underlying != current_instrument:
                    if current_instrument != "":
                        lines.append(f"Instrument: {underlying}")

                    current_instrument = underlying

                parts = [f"Add {effect.key}"]
                if effect.memo is not None:
                    parts.append(f"memo={effect.memo}")
                if effect.side is not None:
                    parts.append(f"side={effect.side.name}")
                if effect.price is not None:
                    parts.append(f"price={effect.price}")
                if effect.quantity is not None:
                    parts.append(f"qty={effect.quantity}")
                if effect.ordtype is not None:
                    parts.append(f"type={effect.ordtype.name}")
                if effect.visible_quantity is not None:
                    parts.append(f"visible_qty={effect.visible_quantity}")
                if effect.tif is not None:
                    parts.append(f"tif={effect.tif.name}")
                if effect.peg_offset_value is not None:
                    parts.append(f"peg_offset={effect.peg_offset_value}")
                if effect.peg_price_type is not None:
                    parts.append(f"peg_type={effect.peg_price_type.name}")
                if effect.min_quantity is not None:
                    parts.append(f"min_qty={effect.min_quantity}")
                if effect.display_price is not None:
                    parts.append(f"display_price={effect.display_price}")
                if effect.rank_price is not None:
                    parts.append(f"rank_price={effect.rank_price}")
                if effect.book_names is not None:
                    parts.append(f"books={effect.book_names}")
                if effect.timestamp is not None:
                    parts.append(f"ts={effect.timestamp}")
                if effect.parent_order_key is not None and effect.parent_order_key != effect.key:
                    parts.append(f"parent={effect.parent_order_key}")

                lines.append(" ".join(parts))

            elif isinstance(effect, OrderCanceledEffect):
                parts = [f"Cancel {effect.key}"]
                if effect.reason is not None:
                    parts.append(f"reason={effect.reason.name}")
                if effect.timestamp is not None:
                    parts.append(f"ts={effect.timestamp}")
                if effect.parent_order_key is not None and effect.parent_order_key != effect.key:
                    parts.append(f"parent={effect.parent_order_key}")
                lines.append(" ".join(parts))

            elif isinstance(effect, OrderReplacedEffect):
                parts = [f"Replace {effect.key}"]
                if effect.new_key is not None:
                    parts.append(f"new_key={effect.new_key}")
                if effect.price is not None:
                    parts.append(f"price={effect.price}")
                if effect.quantity is not None:
                    parts.append(f"qty={'' if effect.quantity_sign is None else effect.quantity_sign}{effect.quantity}")
                if effect.leaves_quantity is not None:
                    parts.append(f"leaves_qty={effect.leaves_quantity}")
                if effect.side is not None:
                    parts.append(f"side={effect.side.name}")
                if effect.ordtype is not None:
                    parts.append(f"type={effect.ordtype.name}")
                if effect.book_names is not None:
                    parts.append(f"books={effect.book_names}")
                if effect.visible_quantity is not None:
                    parts.append(f"visible_qty={effect.visible_quantity}")
                if effect.peg_offset_value is not None:
                    parts.append(f"peg_offset={effect.peg_offset_value}")
                if effect.peg_price_type is not None:
                    parts.append(f"peg_type={effect.peg_price_type.name}")
                if effect.min_quantity is not None:
                    parts.append(f"min_qty={effect.min_quantity}")
                if effect.display_price is not None:
                    parts.append(f"display_price={effect.display_price}")
                if effect.rank_price is not None:
                    parts.append(f"rank_price={effect.rank_price}")
                if effect.timestamp is not None:
                    parts.append(f"ts={effect.timestamp}")
                if effect.parent_order_key is not None and effect.parent_order_key != effect.key:
                    parts.append(f"parent={effect.parent_order_key}")
                lines.append(" ".join(parts))

            elif isinstance(effect, TradeEffect):
                parts = [f"Trade {effect.instrument_key}"]
                if effect.memo is not None:
                    parts.append(f"memo={effect.memo}")
                if effect.side is not None:
                    parts.append(f"side={effect.side.name}")
                parts.append(f"price={effect.price}")
                parts.append(f"qty={effect.quantity}")
                if effect.trade_match_id is not None:
                    parts.append(f"match_id={effect.trade_match_id}")
                if effect.testcase is not None:
                    parts.append(f"testcase={effect.testcase}")
                if effect.session is not None:
                    parts.append(f"session={effect.session.name}")
                if effect.printable is not None:
                    parts.append(f"printable={effect.printable.name}")
                lines.append(" ".join(parts))

            elif isinstance(effect, InstrumentStatusEffect):
                parts = [f"InstrumentStatus {effect.instrument_key}"]
                if effect.session is not None:
                    parts.append(f"session={effect.session}")
                if effect.nbb is not None:
                    parts.append(f"nbb={effect.nbb}")
                if effect.nbo is not None:
                    parts.append(f"nbo={effect.nbo}")
                lines.append(" ".join(parts))

            elif isinstance(effect, IcebergReplenishmentExtraChildOrder):
                parts = [f"IcebergReplenishmentExtraChildOrder"]
                if effect.new_key is not None:
                    parts.append(f"new_key={effect.new_key}")
                if effect.replenished_quantity is not None:
                    parts.append(f"qty={effect.replenished_quantity}")
                if effect.parent_order_key is not None:
                    parts.append(f"parent={effect.parent_order_key}")
                lines.append(" ".join(parts))

            else:
                # Generic fallback for unknown effect types
                effect_dict = effect.to_dict()
                effect_type = effect_dict.pop('effect_type', 'UNKNOWN')
                non_none = {k: v for k, v in effect_dict.items() if v is not None}
                lines.append(f"{effect_type} {non_none}")

def exchange_transition_formatter(
    exchange: ModelExchange,
    transition: ModelStateTransition,
    exchange_next: ModelExchange,
    audit_data: ExchangeTransitionAudit,
    rules: dict[str, list[ReportedRuleData] | NoRelevantCheckClass]
) -> str:
    """
    Formatter that outputs detailed exchange transition information.

    Includes input signal, downstream effects, and audit data.
    """
    lines = []

    # Input signal
    signal = transition.input_signal
    lines.append(f"{signal.timestamp} {signal.signal_type}")
    lines.append(f"{signal.signal_memo} [{signal.signal_testcase}]")
    lines.append("")  # Empty line separator

    # Downstream effects
    format_downstream_effect(transition, lines, exchange_next)

    if len(audit_data.testcases) > 1:
        lines.append(f"Testcases({len(audit_data.testcases)-1}):")
        for tc in sorted(audit_data.testcases):
            lines.append(f" [{tc}]")

    sorted_instruments = sorted(audit_data.affected_instruments, key=lambda i: i.key)

    lines.append("")  # Empty line separator
    if len(audit_data.affected_instruments) > 0:
        lines.append(f"Affected Instruments({len(audit_data.affected_instruments)}):")
        for instrument in sorted_instruments:
            lines.append(f" {instrument.key}")

    lines.append("")  # Empty line separator


    for instrument in sorted_instruments:
        lines.append(f"------- BEFORE ----------")
        lines.append("")  # Empty line separator
        if instrument.key in exchange.instruments:
            for order_book in exchange.instruments[instrument.key].order_books.values():
                market_data = order_book.to_market_data()
                if market_data.is_crossed_or_locked():
                    market_data.calculate_equilibrium_data()
                lines.append(f"{order_book.print_contents()}")
                lines.append(f"{market_data.print_contents()}")
        lines.append("")  # Empty line separator
        lines.append(f"------- AFTER ----------")
        lines.append("")  # Empty line separator
        for order_book in instrument.order_books.values():
            market_data = order_book.to_market_data()
            if market_data.is_crossed_or_locked():
                market_data.calculate_equilibrium_data()
            lines.append(f"{order_book.print_contents()}")
            lines.append(f"{market_data.print_contents()}")

    lines.append("")  # Empty line separator
    lines.append(f"------- TRADES ----------")
    lines.append("")  # Empty line separator

    for trade in audit_data.trades.values():
        for trade_side in trade.trade_sides:
            lines.append(f"{trade_side}")  # Empty line separator

    lines.append("")  # Empty line separator
    lines.append(f"------- RULES ----------")
    lines.append("")  # Empty line separator
    sorted_lines = []
    for rule_key, rule_items in rules.items():
        for rule in rule_items:
            if rule.annotation == "":
                # lines.append(f"{rule.description}")
                continue
            if rule.rule_description != "":
                annotation_str = f"{rule.rule_description} {rule.annotation}"
            else:
                annotation_str = rule.annotation

            sorted_lines.append(f"{rule.status} {rule_key} {annotation_str} {rule.description} {rule.id}")
    lines.extend(sorted(sorted_lines))

    if ExchangeFormatterConfig.OUTPUT_RAW_DATA and len(transition.raw_data) > 0:
        lines.append("")  # Empty line separator
        lines.append(f"------- RAW DATA ----------")
        lines.append("")  # Empty line separator
        for event in transition.raw_data:
            o = {}
            for k, v in event.items():
                if k.startswith("#") and k != "#datetime":
                    continue
                if v == "":
                    continue
                o[k] = v
            lines.append(f"> {o}")

    lines.append("")  # Empty line separator
    lines.append("========================================================================================================================")
    lines.append("")  # Empty line separator
    lines.append("")  # Empty line separator
    return "\n".join(lines)


def keep_all_with_effects(
    exchange: ModelExchange,
    transition: ModelStateTransition,
    exchange_next: ModelExchange,
    audit_data: ExchangeTransitionAudit,
) -> bool:
    """
    Filter to keep state transitions
    """
    if len(transition.downstream_effects) > 0:
        return True
    else:
        return False


def keep_all_for_symbol(
    exchange: ModelExchange,
    transition: ModelStateTransition,
    exchange_next: ModelExchange,
    audit_data: ExchangeTransitionAudit,
) -> bool:
    """
    Filter to keep state transitions
    """
    if len(transition.downstream_effects) == 0:
        return False

    for instrument in audit_data.affected_instruments:
        if instrument.key in ["GIBRALTAR"]:
            return True

    return False


def _json_default(obj):
    """Handle non-JSON-serializable types."""
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.name
    if isinstance(obj, set):
        return sorted(obj)
    return str(obj)


def _order_book_to_dict(order_book) -> Dict[str, Any]:
    """Convert an OrderBook to a dict including market data price levels."""
    result = order_book.to_dict()
    market_data = order_book.to_market_data()
    if market_data.is_crossed_or_locked():
        market_data.calculate_equilibrium_data()

    levels = []
    for price in sorted(market_data.levels.keys(), key=lambda p: p if p is not None else Decimal(0)):
        level = market_data.levels[price]
        entry: Dict[str, Any] = {"price": price}
        if level.bid_qty is not None:
            entry["bid_qty"] = level.bid_qty
        if level.ask_qty is not None:
            entry["ask_qty"] = level.ask_qty
        if level.bid_numorders is not None:
            entry["bid_numorders"] = level.bid_numorders
        if level.ask_numorders is not None:
            entry["ask_numorders"] = level.ask_numorders
        if level.bid_volume is not None:
            entry["bid_volume"] = level.bid_volume
        if level.ask_volume is not None:
            entry["ask_volume"] = level.ask_volume
        if level.executable_volume is not None:
            entry["executable_volume"] = level.executable_volume
        if level.imbalance_volume is not None:
            entry["imbalance_volume"] = level.imbalance_volume
        levels.append(entry)

    result["market_data"] = {
        "best_bid": market_data.best_bid(),
        "best_ask": market_data.best_ask(),
        "is_crossed": market_data.is_crossed(),
        "is_locked": market_data.is_locked(),
        "levels": levels,
    }
    return result


def _trade_side_to_dict(trade_side) -> Dict[str, Any]:
    """Convert a TradeSide to a dict, skipping None values and circular refs."""
    fields = [
        "side", "price", "quantity", "printable", "session",
        "instrument_key", "memo", "testcase", "contra_broker",
        "last_liquidity_indicator", "order_key", "leaves_quantity",
        "cumulative_quantity", "limit_price", "rank_price",
    ]
    result = {}
    for field in fields:
        val = getattr(trade_side, field, None)
        if val is not None:
            result[field] = val
    return result


def exchange_transition_json_formatter(
    exchange: ModelExchange,
    transition: ModelStateTransition,
    exchange_next: ModelExchange,
    audit_data: ExchangeTransitionAudit,
    rules: dict[str, list[ReportedRuleData] | NoRelevantCheckClass]
) -> str:
    """
    Formatter that outputs a single JSON line per transition (for JSONL output).
    """
    record: Dict[str, Any] = {}

    # Input signal
    record["input_signal"] = transition.input_signal.to_dict()

    # Downstream effects
    record["effects"] = [e.to_dict() for e in transition.downstream_effects]

    # Testcases
    record["testcases"] = sorted(audit_data.testcases) if audit_data.testcases else []

    # Affected instruments - before/after order books
    sorted_instruments = sorted(audit_data.affected_instruments, key=lambda i: i.key)
    affected = []
    for instrument in sorted_instruments:
        instr_data: Dict[str, Any] = {"key": instrument.key, "before": {}, "after": {}}

        if instrument.key in exchange.instruments:
            for book_name, order_book in exchange.instruments[instrument.key].order_books.items():
                instr_data["before"][book_name] = _order_book_to_dict(order_book)

        for book_name, order_book in instrument.order_books.items():
            instr_data["after"][book_name] = _order_book_to_dict(order_book)

        affected.append(instr_data)
    record["affected_instruments"] = affected

    # Trades
    trades = []
    for trade in audit_data.trades.values():
        trade_record = {
            "key": trade.key,
            "timestamp": trade.timestamp,
            "testcase": trade.testcase,
            "sides": [_trade_side_to_dict(ts) for ts in trade.trade_sides],
        }
        trades.append(trade_record)
    record["trades"] = trades

    # Rules
    rule_entries = []
    for rule_key, rule_items in rules.items():
        if isinstance(rule_items, NoRelevantCheckClass):
            continue
        for rule in rule_items:
            if rule.annotation == "":
                continue
            rule_entries.append(asdict(rule) | {"rule_key": rule_key})
    record["rules"] = rule_entries

    # Raw data
    if ExchangeFormatterConfig.OUTPUT_RAW_DATA and len(transition.raw_data) > 0:
        raw = []
        for event in transition.raw_data:
            o = {k: v for k, v in event.items()
                 if v != "" and (not k.startswith("#") or k == "#datetime")}
            raw.append(o)
        record["raw_data"] = raw

    return json.dumps(record, default=_json_default) + "\n"