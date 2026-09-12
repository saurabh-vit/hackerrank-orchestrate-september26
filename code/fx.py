"""
fx.py — Currency conversion using a directed graph with inversion and bridging.

The exchange_rates.csv only provides 5 direct pairs:
  EUR→ZAR, EUR→USD, USD→EUR, USD→IDR, USD→INR

For conversions like ZAR→USD, we must invert (ZAR→EUR using 1/EUR→ZAR rate)
and then bridge (EUR→USD). This module builds a graph that handles all of that
automatically, with exact-date matching first and nearest-earlier-date fallback.
"""

from decimal import Decimal
from datetime import date
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class FXGraph:
    """
    Directed graph of exchange rates with inversion and bridge-hop support.
    
    Usage:
        graph = FXGraph(exchange_rates_list)
        amount_usd = graph.convert(Decimal('1000'), 'ZAR', 'USD', date(2025, 8, 15))
    """

    def __init__(self, rates):
        """
        Build the FX graph from a list of ExchangeRate objects.
        
        Args:
            rates: List of ExchangeRate (rate_date, from_currency, to_currency, rate)
        """
        # Store rates indexed by (from, to) → sorted list of (date, rate)
        self._direct_rates: Dict[Tuple[str, str], List[Tuple[date, Decimal]]] = defaultdict(list)
        
        for r in rates:
            self._direct_rates[(r.from_currency, r.to_currency)].append(
                (r.rate_date, r.rate)
            )
        
        # Sort each pair's rates by date for binary search
        for key in self._direct_rates:
            self._direct_rates[key].sort(key=lambda x: x[0])
        
        # Build the set of all currencies and direct pairs for path finding
        self._currencies = set()
        self._direct_pairs = set()
        for (fc, tc) in self._direct_rates:
            self._currencies.add(fc)
            self._currencies.add(tc)
            self._direct_pairs.add((fc, tc))
        
        # Pre-compute conversion paths for all currency pairs
        self._paths: Dict[Tuple[str, str], List[Tuple[str, str, bool]]] = {}
        self._build_paths()

    def _build_paths(self):
        """
        Pre-compute conversion paths for every possible currency pair.
        
        A path is a list of (from, to, inverted) steps.
        We support: direct, inverted, and up to 2-hop bridges.
        """
        all_currencies = sorted(self._currencies)
        
        for src in all_currencies:
            for dst in all_currencies:
                if src == dst:
                    self._paths[(src, dst)] = []  # identity
                    continue
                
                path = self._find_path(src, dst)
                if path is not None:
                    self._paths[(src, dst)] = path
                else:
                    logger.warning(f"No FX path found: {src} → {dst}")

    def _find_path(self, src: str, dst: str) -> Optional[List[Tuple[str, str, bool]]]:
        """
        Find a conversion path from src to dst using direct rates,
        inversions, and up to 2 bridge hops.
        
        Returns list of (from_currency, to_currency, is_inverted) steps,
        or None if no path exists.
        """
        # 1. Direct rate exists
        if (src, dst) in self._direct_pairs:
            return [(src, dst, False)]
        
        # 2. Inverted rate exists (dst→src in the table)
        if (dst, src) in self._direct_pairs:
            return [(dst, src, True)]
        
        # 3. One-hop bridge: src→mid→dst
        for mid in self._currencies:
            if mid == src or mid == dst:
                continue
            step1 = self._get_step(src, mid)
            step2 = self._get_step(mid, dst)
            if step1 is not None and step2 is not None:
                return [step1, step2]
        
        # 4. Two-hop bridge: src→mid1→mid2→dst
        for mid1 in self._currencies:
            if mid1 == src or mid1 == dst:
                continue
            step1 = self._get_step(src, mid1)
            if step1 is None:
                continue
            for mid2 in self._currencies:
                if mid2 == src or mid2 == dst or mid2 == mid1:
                    continue
                step2 = self._get_step(mid1, mid2)
                step3 = self._get_step(mid2, dst)
                if step2 is not None and step3 is not None:
                    return [step1, step2, step3]
        
        return None

    def _get_step(self, src: str, dst: str) -> Optional[Tuple[str, str, bool]]:
        """Check if a direct or inverted rate exists for src→dst."""
        if (src, dst) in self._direct_pairs:
            return (src, dst, False)
        if (dst, src) in self._direct_pairs:
            return (dst, src, True)
        return None

    def _lookup_rate(self, from_curr: str, to_curr: str, target_date: date) -> Tuple[Decimal, bool]:
        """
        Look up the rate for (from_curr, to_curr) on target_date.
        
        Strategy:
        1. Exact date match → use it
        2. No exact match → nearest earlier date (and log the fallback)
        
        Returns (rate, used_fallback).
        Raises ValueError if no rate is available at all.
        """
        rates = self._direct_rates.get((from_curr, to_curr), [])
        if not rates:
            raise ValueError(
                f"No rates at all for {from_curr}→{to_curr}"
            )
        
        # Binary search for exact or nearest earlier date
        best_rate = None
        best_date = None
        exact = False
        
        for rd, rv in rates:
            if rd == target_date:
                return (rv, False)  # exact match
            if rd < target_date:
                if best_date is None or rd > best_date:
                    best_date = rd
                    best_rate = rv
        
        if best_rate is not None:
            logger.debug(
                f"FX fallback: {from_curr}→{to_curr} on {target_date} "
                f"→ using {best_date} rate {best_rate}"
            )
            return (best_rate, True)
        
        # If no earlier date, use the earliest available
        earliest_date, earliest_rate = rates[0]
        logger.warning(
            f"FX: No rate on or before {target_date} for {from_curr}→{to_curr}, "
            f"using earliest {earliest_date} rate {earliest_rate}"
        )
        return (earliest_rate, True)

    def convert(self, amount: Decimal, from_curr: str, to_curr: str,
                settlement_date: date) -> Decimal:
        """
        Convert an amount from one currency to another using the rate
        closest to the settlement_date.
        
        Args:
            amount: The amount to convert
            from_curr: Source currency (e.g. 'ZAR')
            to_curr: Target currency (e.g. 'USD')
            settlement_date: The date to look up the rate for
            
        Returns:
            The converted amount as Decimal
        """
        if from_curr == to_curr:
            return amount
        
        key = (from_curr, to_curr)
        if key not in self._paths:
            raise ValueError(
                f"No conversion path from {from_curr} to {to_curr}"
            )
        
        path = self._paths[key]
        if not path:
            return amount  # identity (same currency)
        
        result = amount
        for (fc, tc, inverted) in path:
            rate, used_fallback = self._lookup_rate(fc, tc, settlement_date)
            if inverted:
                # We have the rate for tc→fc (or stored as fc→tc but we need
                # the inverse direction), so divide instead of multiply
                result = result / rate
            else:
                result = result * rate
        
        return result

    def get_available_pairs(self) -> set:
        """Return all currency pairs that have a conversion path."""
        return set(self._paths.keys())
