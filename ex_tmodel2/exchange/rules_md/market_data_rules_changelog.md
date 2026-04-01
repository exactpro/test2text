# MarketDataCompareMDvsSIPPrintableVolumes - Development Log

## Request 1: Implement the rule

**Request:** Write rule `MarketDataCompareMDvsSIPPrintableVolumes` in `market_data_rules.py` - for every price level compare the trading volume for instruments that start with `MD:` to trade volume for instruments that start with `SIP:`.

**Response:** Implemented the rule with the following logic:

1. **Guards**: Checks that both `MD:` and `SIP:` instruments are present in the affected instruments, returning early if either is missing.
2. **Collects volumes by price**: Iterates through `audit_data.trades`, and for each printable trade side, accumulates the quantity into `md_volume_by_price` or `sip_volume_by_price` dictionaries keyed by price.
3. **Compares at each price level**: For every price seen across both `MD:` and `SIP:` trades, compares the aggregated volumes. Reports a mismatch (fail) if they differ, or a match (pass, verbose only) if they're equal.

## Request 2: Remove price from annotation strings

**Request:** Parameters such as price that do not represent equivalence classes should only be referred in description, not in annotation itself.

**Response:** Removed `at price {price}` from the annotation strings (the second argument to `report_rule`). The price remains only in the `description` parameter. Changed:

- `f"MD vs SIP printable volume match at price {price}"` -> `f"MD vs SIP printable volume match"`
- `f"MD vs SIP printable volume mismatch at price {price}"` -> `f"MD vs SIP printable volume mismatch"`

## Generated Code

```python
@rule_check(
    rule_description="SIPMarketDataComparePrintableVolumes",
    rule_tags=["trades"],
)
class SIPMarketDataComparePrintableVolumes(RuleCheck):
    def check(
            self,
            exchange: ModelExchange,
            transition: ModelStateTransition,
            exchange_next: ModelExchange,
            audit_data: ExchangeTransitionAudit
    ) -> Iterator[ReportedRuleData] | NoRelevantCheckClass:

        # Apply this rule only when MD: instruments are available
        if not is_market_data_relevant(exchange, audit_data):
            return

        # Also check that SIP: instruments are available
        sip_instruments_found = False
        for instrument in audit_data.affected_instruments:
            if instrument.key.startswith("SIP:"):
                sip_instruments_found = True
                break
        if not sip_instruments_found:
            return

        # Collect printable volumes by price for MD: and SIP: trades
        md_volume_by_price = {}
        sip_volume_by_price = {}

        for trade in audit_data.trades.values():
            for trade_side in trade.trade_sides:
                if trade_side.printable == Printable.NO:
                    continue

                price = trade_side.price
                quantity = trade_side.quantity

                if trade.key.startswith("MD:"):
                    md_volume_by_price[price] = md_volume_by_price.get(price, 0) + quantity
                elif trade.key.startswith("SIP:"):
                    sip_volume_by_price[price] = sip_volume_by_price.get(price, 0) + quantity

        # Compare volumes at each price level
        all_prices = set(md_volume_by_price.keys()) | set(sip_volume_by_price.keys())

        for price in sorted(all_prices):
            md_vol = md_volume_by_price.get(price, 0)
            sip_vol = sip_volume_by_price.get(price, 0)

            if md_vol == sip_vol:
                if RuleRunner.is_verbose():
                    yield self.report_rule(transition,
                        f"MD vs SIP printable volume match",
                        True,
                        description=f"price={price} md={md_vol} sip={sip_vol}")
            else:
                yield self.report_rule(transition,
                    f"MD vs SIP printable volume mismatch",
                    False,
                    description=f"price={price} md={md_vol} sip={sip_vol}")
```
