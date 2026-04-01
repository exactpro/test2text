"""
Market data level 2 model classes.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional, Dict

from decimal import Decimal

from ex_tmodel2.exchange import Side


@dataclass
class MDEntry:
    price: Optional[Decimal] = None
    qty: Optional[Decimal] = None
    order_id: Optional[str] = None
    side: Optional[Side] = None


class MBOBook:

    def __init__(self):
        self.entries = list[MDEntry]


    def addEntry(self, entry: MDEntry):
        pass

    def delEntry(self, entry: MDEntry):
        pass

    def amendEntry(self, entry: MDEntry):
        pass



def convertMBOBookToLelel2MarketData(MBOBook) -> Level2MarketData:
    pass


@dataclass
class PriceLevel:
    """
    Represents a single price level in the order book.

    price, bid_qty, ask_qty can all be None.
    """
    price: Optional[Decimal] = None
    bid_qty: Optional[Decimal] = None
    ask_qty: Optional[Decimal] = None
    bid_numorders: Optional[int] = None
    ask_numorders: Optional[int] = None

    executable_volume: Optional[Decimal] = None
    imbalance_volume: Optional[Decimal] = None
    bid_volume: Optional[Decimal] = None
    ask_volume: Optional[Decimal] = None


class Level2MarketData:
    """
    Represents Level 2 market data as a collection of unique price levels.
    """

    def __init__(self):
        self.levels: Dict[Optional[Decimal], PriceLevel] = {}

    def _to_decimal(self, value) -> Optional[Decimal]:
        """Helper: convert floats/ints/strings to Decimal, preserve None."""
        if value is None or value == "":
            return None
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    def add_level(self, level: PriceLevel) -> None:
        """
        Add or update a level.
        If both bid_qty and ask_qty are None, remove that level instead.
        """
        level.price = self._to_decimal(level.price)
        level.bid_qty = self._to_decimal(level.bid_qty)
        level.ask_qty = self._to_decimal(level.ask_qty)

        # Remove level if both quantities are None
        if level.bid_qty is None and level.ask_qty is None:
            self.delete_level(level.price)
            return

        # Add or update the level in the dictionary
        self.levels[level.price] = level

    def delete_level(self, price: Optional[Decimal]) -> None:
        """Remove a level with the given price."""
        price = self._to_decimal(price)
        self.levels.pop(price, None)

    def get_level(self, price: Optional[Decimal]) -> Optional[PriceLevel]:
        """Retrieve a level by price."""
        price = self._to_decimal(price)
        return self.levels.get(price)

    def keep_top_n_levels(self, n: int, descending: bool = True) -> None:
        """Keep only top N levels by price."""
        def sort_key(lvl: PriceLevel):
            return lvl.price if lvl.price is not None else Decimal("0")

        # Sort all levels and keep only top n
        sorted_levels = sorted(self.levels.values(), key=sort_key, reverse=descending)
        top_levels = sorted_levels[:n]

        # Rebuild the dict with only the top n levels
        self.levels = {lvl.price: lvl for lvl in top_levels}

    def signature(self, structure_only: bool = False) -> str:
        """
        Convert the book content into a string signature.

        Args:
            structure_only: If False (default), format for each level (sorted from lowest to highest price):
                           <price>[_B<bid_qty>][_S<ask_qty>]
                           Levels separated by pipe (|) characters.
                           If True, format shows only structure using numorders:
                           [B<bid_numorders>][S<ask_numorders>]
                           Levels separated by underscore (_) characters.

        - Quantities shown without trailing .0 if integer.
        - Price shown as entered (normalized Decimal).
        - None values skipped.
        """
        if not self.levels:
            return ""

        def fmt_decimal(value: Optional[Decimal]) -> Optional[str]:
            # integer values (e.g. 10, 10.0) → "10"
            if value == value.to_integral_value():
                return str(int(value))
            # otherwise normalize (avoid scientific notation, strip trailing zeros)
            return format(value.normalize(), "f")

        # Sort levels by price ascending (None sorted before any numeric value)
        sorted_levels = sorted(
            self.levels.values(),
            key=lambda lvl: (lvl.price is not None, lvl.price if lvl.price is not None else Decimal("-inf"))
        )

        if structure_only:
            # Structure-only format: B<bid_numorders>S<ask_numorders> separated by _
            parts = []
            for lvl in sorted_levels:
                segs = []
                if lvl.bid_numorders is not None:
                    segs.append(f"B{lvl.bid_numorders}")
                if lvl.ask_numorders is not None:
                    segs.append(f"S{lvl.ask_numorders}")
                if segs:
                    parts.append("".join(segs))
            return "_".join(parts)
        else:
            # Default format: price_B<qty>_S<qty> separated by |
            parts = []
            for lvl in sorted_levels:
                price_str = fmt_decimal(lvl.price) if lvl.price is not None else "None"
                segs = [price_str]

                if lvl.bid_qty is not None:
                    segs.append(f"B{fmt_decimal(lvl.bid_qty)}")
                if lvl.ask_qty is not None:
                    segs.append(f"S{fmt_decimal(lvl.ask_qty)}")

                parts.append("_".join(segs))

            # Join all levels with pipes
            return "|".join(parts)

    def copy(self) -> Level2MarketData:
        """
        Create a deep copy of this Level2MarketData object.

        Returns a new Level2MarketData instance with copies of all price levels,
        so modifications to the copy won't affect the original.
        """
        new_book = Level2MarketData()
        # Create a copy of each PriceLevel using dataclasses.replace
        for price, level in self.levels.items():
            new_book.levels[price] = replace(level)
        return new_book

    def keep_top_n_bid_ask_levels(self, n: int, keep_none_price: bool = False) -> None:
        """
        Keep only the top N bid levels and top N ask levels.

        For bids: top levels are those with highest prices.
        For asks: top levels are those with lowest prices.

        If a level has both bid_qty and ask_qty, it may be kept if either side
        qualifies as a top N level.

        Args:
            n: Number of top levels to keep for each side (bid and ask).
            keep_none_price: If True, keep levels with price=None regardless of N.
                           If False, levels with price=None are removed.

        Note: If requesting to keep 1 level, the result can contain 0, 1, or 2 levels,
              depending on whether the top bid and top ask are at different price levels.
        """
        # Handle None price level separately
        none_level = self.levels.get(None)

        # Collect all levels with bids and asks (excluding None price)
        bid_levels = [(price, level) for price, level in self.levels.items()
                      if price is not None and level.bid_qty is not None]
        ask_levels = [(price, level) for price, level in self.levels.items()
                      if price is not None and level.ask_qty is not None]

        # Sort and get top N
        # For bids: highest prices are best (descending)
        bid_levels.sort(key=lambda x: x[0], reverse=True)
        top_bid_prices = {price for price, _ in bid_levels[:n]}

        # For asks: lowest prices are best (ascending)
        ask_levels.sort(key=lambda x: x[0])
        top_ask_prices = {price for price, _ in ask_levels[:n]}

        # Build new levels dict
        new_levels = {}

        # Handle None price level
        if none_level is not None and keep_none_price:
            new_levels[None] = none_level

        # Process all other levels
        for price, level in self.levels.items():
            if price is None:
                continue  # Already handled above

            bid_qualifies = level.bid_qty is not None and price in top_bid_prices
            ask_qualifies = level.ask_qty is not None and price in top_ask_prices

            if bid_qualifies or ask_qualifies:
                # Create new level with only qualifying sides
                new_level = PriceLevel(
                    price=price,
                    bid_qty=level.bid_qty if bid_qualifies else None,
                    ask_qty=level.ask_qty if ask_qualifies else None
                )
                new_levels[price] = new_level

        self.levels = new_levels

    def is_locked(self) -> bool:
        """
        Check if the market is locked.

        A market is locked when:
        - There is liquidity on both bid and ask sides
        - Best bid price equals best ask price
        - Neither best bid nor best ask has price=None

        Returns:
            True if market is locked, False otherwise.
        """
        # Find best bid (highest price with bid_qty, excluding None prices)
        best_bid_price = None
        for price, level in self.levels.items():
            if price is not None and level.bid_qty is not None:
                if best_bid_price is None or price > best_bid_price:
                    best_bid_price = price

        # Find best ask (lowest price with ask_qty, excluding None prices)
        best_ask_price = None
        for price, level in self.levels.items():
            if price is not None and level.ask_qty is not None:
                if best_ask_price is None or price < best_ask_price:
                    best_ask_price = price

        # Locked if both exist and are equal
        if best_bid_price is not None and best_ask_price is not None:
            return best_bid_price == best_ask_price

        return False

    def is_crossed(self) -> bool:
        """
        Check if the market is crossed.

        A market is crossed when:
        - Best bid price is above best ask price, OR
        - There is price=None for bid side (has bid_qty), OR
        - There is price=None for ask side (has ask_qty)

        Returns:
            True if market is crossed, False otherwise.
        """
        # Check for None price with bid or ask quantity
        for price, level in self.levels.items():
            if price is None:
                if level.bid_qty is not None or level.ask_qty is not None:
                    return True

        # Find best bid (highest price with bid_qty, excluding None prices)
        best_bid_price = None
        for price, level in self.levels.items():
            if price is not None and level.bid_qty is not None:
                if best_bid_price is None or price > best_bid_price:
                    best_bid_price = price

        # Find best ask (lowest price with ask_qty, excluding None prices)
        best_ask_price = None
        for price, level in self.levels.items():
            if price is not None and level.ask_qty is not None:
                if best_ask_price is None or price < best_ask_price:
                    best_ask_price = price

        # Crossed if both exist and best bid > best ask
        if best_bid_price is not None and best_ask_price is not None:
            return best_bid_price > best_ask_price

        return False

    def is_crossed_or_locked(self) -> bool:
        """
        Check if the market is either crossed or locked.

        Returns:
            True if market is crossed or locked, False otherwise.
        """
        return self.is_locked() or self.is_crossed()

    def best_bid(self) -> Optional[Decimal]:
        """
        Get the best bid price (highest price with bid_qty).

        Returns:
            The highest bid price, or None if no bids exist.
        """
        best_bid_price = None

        for price, level in self.levels.items():
            if price is not None and level.bid_qty is not None:
                if best_bid_price is None or price > best_bid_price:
                    best_bid_price = price

        return best_bid_price

    def best_ask(self) -> Optional[Decimal]:
        """
        Get the best ask price (lowest price with ask_qty).

        Returns:
            The lowest ask price, or None if no asks exist.
        """
        best_ask_price = None

        for price, level in self.levels.items():
            if price is not None and level.ask_qty is not None:
                if best_ask_price is None or price < best_ask_price:
                    best_ask_price = price

        return best_ask_price

    def calculate_equilibrium_data(self) -> Optional[Decimal]:
        """
        Calculate equilibrium data for auction price determination.

        This method calculates for each price level:
        - bid_volume: Cumulative bid quantity from highest price down to this level
        - ask_volume: Cumulative ask quantity from lowest price up to this level
        - executable_volume: Minimum of bid_volume and ask_volume (tradeable quantity)
        - imbalance_volume: bid_volume - ask_volume (positive = buy imbalance)

        Market orders (price=None) are included at all price levels since they
        are willing to trade at any price.

        The equilibrium price is determined by:
        1. Maximum executable volume
        2. Minimum absolute imbalance (among max executable levels)
        3. If still tied, use pressure: BUY pressure → highest price,
           SELL pressure → lowest price

        Returns:
            The equilibrium price (Decimal), or None if no executable volume exists.
        """
        # Get all price levels excluding None prices, sorted by price
        priced_levels = [(price, level) for price, level in self.levels.items()
                         if price is not None]

        if not priced_levels:
            return None

        # Sort by price ascending
        priced_levels.sort(key=lambda x: x[0])

        # Get market order quantities (price=None) - these trade at any price
        market_level = self.levels.get(None)
        market_bid_qty = Decimal("0")
        market_ask_qty = Decimal("0")
        if market_level is not None:
            if market_level.bid_qty is not None:
                market_bid_qty = market_level.bid_qty
            if market_level.ask_qty is not None:
                market_ask_qty = market_level.ask_qty

        # Calculate cumulative ask volume (from lowest to highest price)
        # Start with market ask orders since they trade at any price
        cumulative_ask = market_ask_qty
        ask_cumulative_at_price = {}
        for price, level in priced_levels:
            if level.ask_qty is not None:
                cumulative_ask += level.ask_qty
            ask_cumulative_at_price[price] = cumulative_ask

        # Calculate cumulative bid volume (from highest to lowest price)
        # Start with market bid orders since they trade at any price
        cumulative_bid = market_bid_qty
        bid_cumulative_at_price = {}
        for price, level in reversed(priced_levels):
            if level.bid_qty is not None:
                cumulative_bid += level.bid_qty
            bid_cumulative_at_price[price] = cumulative_bid

        # Calculate equilibrium data for each level and find max executable
        max_executable = Decimal("0")

        for price, level in priced_levels:
            bid_vol = bid_cumulative_at_price[price]
            ask_vol = ask_cumulative_at_price[price]
            executable = min(bid_vol, ask_vol)
            imbalance = bid_vol - ask_vol

            # Update level with calculated values
            level.bid_volume = bid_vol
            level.ask_volume = ask_vol
            level.executable_volume = executable
            level.imbalance_volume = imbalance

            if executable > max_executable:
                max_executable = executable

        # If no executable volume, return None
        if max_executable == Decimal("0"):
            return None

        # Find minimum absolute imbalance among levels with max executable
        min_abs_imbalance = None
        for price, level in priced_levels:
            if level.executable_volume == max_executable:
                abs_imbalance = abs(level.imbalance_volume)
                if min_abs_imbalance is None or abs_imbalance < min_abs_imbalance:
                    min_abs_imbalance = abs_imbalance

        # Collect all candidate prices with max executable and min imbalance
        candidate_prices = []
        imbalance_sign = None
        for price, level in priced_levels:
            if (level.executable_volume == max_executable and
                abs(level.imbalance_volume) == min_abs_imbalance):
                candidate_prices.append(price)
                imbalance_sign = level.imbalance_volume

        # If only one candidate, return it
        if len(candidate_prices) == 1:
            return candidate_prices[0]

        # Multiple candidates - use pressure to determine price
        # BUY pressure (positive imbalance) → highest price
        # SELL pressure (negative imbalance) → lowest price
        # Balanced (zero imbalance) → lowest price (default)
        if imbalance_sign is not None and imbalance_sign > 0:
            return max(candidate_prices)
        else:
            return min(candidate_prices)

    def count_levels_at_max_executable_volume(self) -> int:
        """
        Count the number of price levels with maximum executable volume.

        This method assumes calculate_equilibrium_data() was called beforehand
        to populate the executable_volume field on each level.

        Returns:
            Number of levels that have the maximum executable_volume.
            Returns 0 if no levels exist or all executable_volumes are None/zero.
        """
        # Find the maximum executable volume
        max_executable = Decimal("0")
        for level in self.levels.values():
            if level.executable_volume is not None and level.executable_volume > max_executable:
                max_executable = level.executable_volume

        # If max is zero, no executable volume exists
        if max_executable == Decimal("0"):
            return 0

        # Count levels with the maximum executable volume
        count = 0
        for level in self.levels.values():
            if level.executable_volume == max_executable:
                count += 1

        return count

    def count_levels_at_max_executable_and_min_imbalance(self) -> int:
        """
        Count price levels with maximum executable volume and minimum imbalance.

        This method assumes calculate_equilibrium_data() was called beforehand
        to populate the executable_volume and imbalance_volume fields.

        Returns:
            Number of levels that have both maximum executable_volume and
            minimum absolute imbalance_volume among those max levels.
            Returns 0 if no executable volume exists.
        """
        # Find the maximum executable volume
        max_executable = Decimal("0")
        for level in self.levels.values():
            if level.executable_volume is not None and level.executable_volume > max_executable:
                max_executable = level.executable_volume

        # If max is zero, no executable volume exists
        if max_executable == Decimal("0"):
            return 0

        # Find minimum absolute imbalance among levels with max executable volume
        min_abs_imbalance = None
        for level in self.levels.values():
            if level.executable_volume == max_executable and level.imbalance_volume is not None:
                abs_imbalance = abs(level.imbalance_volume)
                if min_abs_imbalance is None or abs_imbalance < min_abs_imbalance:
                    min_abs_imbalance = abs_imbalance

        if min_abs_imbalance is None:
            return 0

        # Count levels with max executable and min absolute imbalance
        count = 0
        for level in self.levels.values():
            if (level.executable_volume == max_executable and
                level.imbalance_volume is not None and
                abs(level.imbalance_volume) == min_abs_imbalance):
                count += 1

        return count

    def get_pressure(self) -> Optional[Side]:
        """
        Get the market pressure direction based on imbalance at equilibrium.

        This method assumes calculate_equilibrium_data() was called beforehand
        to populate the executable_volume and imbalance_volume fields.

        The pressure is determined by finding the level(s) with maximum executable
        volume and minimum absolute imbalance, then checking the imbalance sign:
        - Positive imbalance (more bids than asks) → Side.BUY (buy pressure)
        - Negative imbalance (more asks than bids) → Side.SELL (sell pressure)
        - Zero imbalance (balanced) → None

        Returns:
            Side.BUY if buy pressure, Side.SELL if sell pressure, None if balanced
            or no executable volume exists.
        """
        # Find the maximum executable volume
        max_executable = Decimal("0")
        for level in self.levels.values():
            if level.executable_volume is not None and level.executable_volume > max_executable:
                max_executable = level.executable_volume

        # If max is zero, no executable volume exists
        if max_executable == Decimal("0"):
            return None

        # Find minimum absolute imbalance among levels with max executable volume
        min_abs_imbalance = None
        imbalance_at_equilibrium = None
        for level in self.levels.values():
            if level.executable_volume == max_executable and level.imbalance_volume is not None:
                abs_imbalance = abs(level.imbalance_volume)
                if min_abs_imbalance is None or abs_imbalance < min_abs_imbalance:
                    min_abs_imbalance = abs_imbalance
                    imbalance_at_equilibrium = level.imbalance_volume

        if imbalance_at_equilibrium is None:
            return None

        # Determine pressure based on imbalance sign
        if imbalance_at_equilibrium > 0:
            return Side.BUY
        elif imbalance_at_equilibrium < 0:
            return Side.SELL
        else:
            return None

    def print_contents(self) -> str:
        """
        Print the contents of market data in a human-readable format.

        Includes both raw bid/ask quantities and calculated equilibrium
        parameters (bid_volume, ask_volume, executable_volume, imbalance_volume)
        if they have been populated by calculate_equilibrium_data().

        Returns:
            String representation of the market data suitable for display.
        """
        if not self.levels:
            return ""

        lines = []
        lines.append("Level2MarketData:")
        lines.append("-" * 80)

        # Header
        header = f"{'Price':>12} | {'Bid Qty':>10} | {'Ask Qty':>10}"
        has_calc_data = any(
            level.executable_volume is not None
            for level in self.levels.values()
        )
        if has_calc_data:
            header += f" | {'Bid Vol':>10} | {'Ask Vol':>10} | {'Exec Vol':>10} | {'Imbalance':>10}"
        lines.append(header)
        lines.append("-" * 80)

        # Sort levels by price descending (highest price first, None/MKT first)
        sorted_levels = sorted(
            self.levels.values(),
            key=lambda lvl: (lvl.price is not None, -lvl.price if lvl.price is not None else Decimal("inf")),
        )

        for level in sorted_levels:
            price_str = str(level.price) if level.price is not None else "MKT"
            bid_qty_str = str(level.bid_qty) if level.bid_qty is not None else "-"
            ask_qty_str = str(level.ask_qty) if level.ask_qty is not None else "-"

            row = f"{price_str:>12} | {bid_qty_str:>10} | {ask_qty_str:>10}"

            if has_calc_data:
                bid_vol_str = str(level.bid_volume) if level.bid_volume is not None else "-"
                ask_vol_str = str(level.ask_volume) if level.ask_volume is not None else "-"
                exec_vol_str = str(level.executable_volume) if level.executable_volume is not None else "-"
                imbal_str = str(level.imbalance_volume) if level.imbalance_volume is not None else "-"
                row += f" | {bid_vol_str:>10} | {ask_vol_str:>10} | {exec_vol_str:>10} | {imbal_str:>10}"

            lines.append(row)

        lines.append("-" * 80)

        # Summary
        best_bid = self.best_bid()
        best_ask = self.best_ask()
        lines.append(f"Best Bid: {best_bid}  |  Best Ask: {best_ask}")

        if self.is_crossed():
            lines.append("Status: CROSSED")
        elif self.is_locked():
            lines.append("Status: LOCKED")
        else:
            lines.append("Status: Normal")

        if has_calc_data:
            max_exec_count = self.count_levels_at_max_executable_volume()
            min_imbal_count = self.count_levels_at_max_executable_and_min_imbalance()
            pressure = self.get_pressure()
            pressure_str = pressure.name if pressure is not None else "None"
            lines.append(f"Levels at max executable: {max_exec_count}  |  Levels at min imbalance: {min_imbal_count}")
            lines.append(f"Pressure: {pressure_str}")

        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"Level2MarketData(levels={self.levels})"

    def compare(self, other: Level2MarketData) -> Dict[str, any]:
        """
        Compare this Level2MarketData with another and return the differences.

        Args:
            other: Another Level2MarketData object to compare against.

        Returns:
            A dictionary containing:
            - 'equal': True if both objects are equivalent, False otherwise
            - 'only_in_self': List of prices that exist only in this object
            - 'only_in_other': List of prices that exist only in the other object
            - 'differences': Dict mapping prices to field differences for levels
                            that exist in both but have different values
        """
        result = {
            'equal': True,
            'only_in_self': [],
            'only_in_other': [],
            'differences': {}
        }

        self_prices = set(self.levels.keys())
        other_prices = set(other.levels.keys())

        # Find prices only in self
        only_in_self = self_prices - other_prices
        if only_in_self:
            result['only_in_self'] = sorted(
                [p for p in only_in_self],
                key=lambda x: (x is None, x if x is not None else Decimal("-inf"))
            )
            result['equal'] = False

        # Find prices only in other
        only_in_other = other_prices - self_prices
        if only_in_other:
            result['only_in_other'] = sorted(
                [p for p in only_in_other],
                key=lambda x: (x is None, x if x is not None else Decimal("-inf"))
            )
            result['equal'] = False

        # Compare levels that exist in both
        common_prices = self_prices & other_prices
        for price in common_prices:
            self_level = self.levels[price]
            other_level = other.levels[price]

            level_diffs = {}

            # Compare each field
            if self_level.bid_qty != other_level.bid_qty:
                level_diffs['bid_qty'] = {'self': self_level.bid_qty, 'other': other_level.bid_qty}
            if self_level.ask_qty != other_level.ask_qty:
                level_diffs['ask_qty'] = {'self': self_level.ask_qty, 'other': other_level.ask_qty}
            if self_level.bid_numorders != other_level.bid_numorders:
                level_diffs['bid_numorders'] = {'self': self_level.bid_numorders, 'other': other_level.bid_numorders}
            if self_level.ask_numorders != other_level.ask_numorders:
                level_diffs['ask_numorders'] = {'self': self_level.ask_numorders, 'other': other_level.ask_numorders}

            if level_diffs:
                result['differences'][price] = level_diffs
                result['equal'] = False

        return result