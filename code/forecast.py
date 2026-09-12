"""
forecast.py — 90-day day-by-day balance simulation and safety analysis.

Uses Decimal exclusively for monetary values to avoid floating-point errors.
Simulates day-by-day cash balance from request_date through request_date + 90 days.
"""

from decimal import Decimal
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from events import UserLedger, RecurringStream


@dataclass
class ForecastResult:
    """Outcome of 90-day balance forecast."""
    amount_safe_to_pay: Decimal
    earliest_date_for_full_payment: Optional[date]
    min_headroom_today: Decimal
    daily_balances: List[Tuple[date, Decimal, Decimal]]  # (date, balance, headroom)


def simulate_balance_timeline(
    ledger: UserLedger,
    start_date: date,
    num_days: int = 90,
    spending_changes: Optional[Dict[str, Any]] = None,
    plan_payments: Optional[Dict[date, Decimal]] = None,
) -> List[Tuple[date, Decimal, Decimal]]:
    """
    Simulate day-by-day balance from start_date to start_date + num_days.
    
    Returns list of (date, balance, headroom_above_minimum).
    """
    if spending_changes is None:
        spending_changes = {}
    if plan_payments is None:
        plan_payments = {}

    daily_credits: Dict[date, Decimal] = {}
    daily_debits: Dict[date, Decimal] = {}
    end_date = start_date + timedelta(days=num_days)

    # 1. Pending debits (reserve debits immediately on their settlement date)
    for pd in ledger.pending_debits:
        d = pd.settlement_date or pd.event_date
        if start_date <= d <= end_date:
            daily_debits[d] = daily_debits.get(d, Decimal('0')) + pd.amount_home

    # 2. Scheduled events
    for se in ledger.scheduled_events:
        d = se.settlement_date or se.event_date
        if start_date <= d <= end_date:
            if se.direction == 'credit':
                daily_credits[d] = daily_credits.get(d, Decimal('0')) + se.amount_home
            elif se.direction == 'debit':
                daily_debits[d] = daily_debits.get(d, Decimal('0')) + se.amount_home

    # 3. Active recurring salary streams
    for ss in ledger.salary_streams:
        if not ss.is_active:
            continue
        dom = ss.day_of_month or 15
        amt = ss.base_amount
        for day_offset in range(num_days + 1):
            cur_d = start_date + timedelta(days=day_offset)
            if ss.start_date and cur_d < ss.start_date:
                continue
            if cur_d.day == dom:
                if cur_d not in daily_credits:
                    daily_credits[cur_d] = daily_credits.get(cur_d, Decimal('0')) + amt

    # 4. Recurring expense streams
    for rs in ledger.recurring_expense_streams:
        ev_id = rs.representative_event_id
        if spending_changes.get(ev_id) == 'stop':
            continue
        
        amt = rs.base_amount
        if ev_id in spending_changes and isinstance(spending_changes[ev_id], Decimal):
            amt = spending_changes[ev_id]

        for day_offset in range(num_days + 1):
            cur_d = start_date + timedelta(days=day_offset)
            match = False
            if rs.day_of_month:
                if cur_d.day == rs.day_of_month:
                    match = True
            elif rs.interval_days:
                diff = (cur_d - rs.anchor_date).days
                if diff > 0 and diff % rs.interval_days == 0:
                    match = True

            if match:
                daily_debits[cur_d] = daily_debits.get(cur_d, Decimal('0')) + amt

    # 5. Day-by-day balance calculation
    bal = ledger.profile.current_available_balance
    min_bal = ledger.profile.minimum_balance_to_keep
    timeline: List[Tuple[date, Decimal, Decimal]] = []

    for day_offset in range(num_days + 1):
        cur_d = start_date + timedelta(days=day_offset)
        bal += daily_credits.get(cur_d, Decimal('0'))
        bal -= daily_debits.get(cur_d, Decimal('0'))
        bal -= plan_payments.get(cur_d, Decimal('0'))
        headroom = bal - min_bal
        timeline.append((cur_d, bal, headroom))

    return timeline


def compute_forecast(
    ledger: UserLedger,
    request_date: date,
    requested_amount: Decimal,
    spending_changes: Optional[Dict[str, Any]] = None,
) -> ForecastResult:
    """
    Run 90-day forecast to compute:
    1. amount_safe_to_pay on request_date
    2. earliest_date_for_full_payment within the 90-day window
    """
    base_timeline = simulate_balance_timeline(
        ledger, request_date, num_days=90, spending_changes=spending_changes
    )

    min_headroom_today = min(entry[2] for entry in base_timeline)
    amount_safe_today = max(Decimal('0'), min(requested_amount, min_headroom_today))

    earliest_date = None
    for day_offset in range(91):
        candidate_date = request_date + timedelta(days=day_offset)
        test_payments = {candidate_date: requested_amount}
        test_timeline = simulate_balance_timeline(
            ledger, request_date, num_days=90,
            spending_changes=spending_changes,
            plan_payments=test_payments
        )
        is_safe = all(
            entry[2] >= Decimal('0')
            for entry in test_timeline
            if entry[0] >= candidate_date
        )
        if is_safe:
            earliest_date = candidate_date
            break

    return ForecastResult(
        amount_safe_to_pay=amount_safe_today,
        earliest_date_for_full_payment=earliest_date,
        min_headroom_today=min_headroom_today,
        daily_balances=base_timeline,
    )


def is_plan_safe(
    ledger: UserLedger,
    request_date: date,
    plan_payments: Dict[date, Decimal],
    spending_changes: Optional[Dict[str, Any]] = None,
    num_days: int = 90,
) -> bool:
    """
    Check if a proposed payment plan is 100% safe across the 90-day forecast window.
    """
    timeline = simulate_balance_timeline(
        ledger, request_date, num_days=num_days,
        spending_changes=spending_changes,
        plan_payments=plan_payments
    )
    return all(entry[2] >= Decimal('0') for entry in timeline)
