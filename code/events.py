"""
events.py — Event normalization, conflict resolution, message integration, and recurrence detection.

Builds a normalized, deduplicated financial ledger for each user and identifies
recurring income/expense streams for forecasting.
"""

import re
from decimal import Decimal
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from collections import defaultdict

from loaders import Profile, FinancialEvent, Message, ImageRef
from fx import FXGraph


@dataclass
class RecurringStream:
    """A detected recurring financial stream."""
    stream_id: str
    user_id: str
    category: str
    direction: str  # credit or debit
    base_amount: Decimal  # in home currency
    interval_days: int  # e.g., 30 for monthly, 7 for weekly, 14 for biweekly, etc.
    anchor_date: date  # the last observed settlement date
    day_of_month: Optional[int]  # for monthly streams
    flexibility: str  # fixed, reducible, stoppable, reducible_or_stoppable
    minimum_allowed_amount: Optional[Decimal]
    representative_event_id: str
    description: str
    start_date: Optional[date] = None
    is_active: bool = True
    source_type: str = 'detected'  # 'detected' or 'scheduled'


@dataclass
class UserLedger:
    """Normalized ledger and financial state for a single user."""
    user_id: str
    profile: Profile
    balance_at_eval_date: Decimal
    events: List[FinancialEvent]
    pending_debits: List[FinancialEvent]
    scheduled_events: List[FinancialEvent]
    recurring_expense_streams: List[RecurringStream]
    salary_streams: List[RecurringStream]
    event_lookup: Dict[str, FinancialEvent]


def normalize_and_build_ledger(
    user_id: str,
    profile: Profile,
    user_events: List[FinancialEvent],
    user_messages: List[Message],
    user_images: Dict[str, ImageRef],
    image_extractions: Dict[str, Dict[str, str]],
    message_extractions: Dict[str, Dict[str, Any]],
    fx_graph: FXGraph,
    eval_date: date,
    global_reference_date: date,
) -> UserLedger:
    """
    Build a cleaned, normalized, deduplicated ledger for a user as of eval_date.
    """
    home_curr = profile.home_currency
    event_lookup: Dict[str, FinancialEvent] = {}

    # 1. Fill missing amounts from images and convert to home currency
    cleaned_events: List[FinancialEvent] = []
    for raw_e in user_events:
        e = FinancialEvent(
            event_id=raw_e.event_id,
            user_id=raw_e.user_id,
            event_type=raw_e.event_type,
            description=raw_e.description,
            category=raw_e.category,
            direction=raw_e.direction,
            amount=raw_e.amount,
            currency=raw_e.currency or home_curr,
            event_date=raw_e.event_date,
            settlement_date=raw_e.settlement_date,
            status=raw_e.status,
            linked_event_id=raw_e.linked_event_id,
            flexibility=raw_e.flexibility,
            minimum_allowed_amount=raw_e.minimum_allowed_amount,
        )

        if e.amount is None and e.event_id in user_images:
            img_ref = user_images[e.event_id]
            extr = image_extractions.get(img_ref.image_id, {})
            if 'amount' in extr and extr['amount']:
                e.amount = Decimal(str(extr['amount']))
                if 'currency' in extr and extr['currency']:
                    e.currency = extr['currency']

        eff_date = e.settlement_date or e.event_date

        if e.amount is not None:
            e.amount_home = fx_graph.convert(e.amount, e.currency, home_curr, eff_date)
        else:
            e.amount_home = Decimal('0')

        if e.minimum_allowed_amount is not None:
            e.minimum_allowed_amount = fx_graph.convert(
                e.minimum_allowed_amount, e.currency, home_curr, eff_date
            )

        event_lookup[e.event_id] = e
        cleaned_events.append(e)

    # 2. Process Messages for Amendments, Cancellations, Delays
    cancelled_event_ids: Set[str] = set()
    employment_ended = False
    salary_resumes_date: Optional[date] = None
    salary_resumes_amount: Optional[Decimal] = None
    remaining_household_salary: Optional[Decimal] = None

    for msg in user_messages:
        text = msg.message_text.lower()

        # Use pre-extracted deltas from extraction.py
        delta = message_extractions.get(msg.message_id, {})
        delta_type = delta.get('type', 'unknown')
        details = delta.get('details', {})

        if msg.related_event_id and msg.related_event_id in event_lookup:
            target_ev = event_lookup[msg.related_event_id]
            if delta_type == 'cancellation' or 'cancel' in text or 'dibatalkan' in text or 'batal' in text:
                cancelled_event_ids.add(target_ev.event_id)
                target_ev.status = 'cancelled'

        if msg.source_type == 'employer':
            if 'employment has ended' in text or 'contract has ended' in text:
                employment_ended = True

            if delta_type == 'salary_amendment':
                if 'new_amount' in details:
                    amt_str = details['new_amount']
                    curr = details.get('currency', home_curr)
                    eff_date_str = details.get('effective_date')
                    try:
                        eff_date = date.fromisoformat(eff_date_str) if eff_date_str else eval_date
                        salary_resumes_amount = fx_graph.convert(Decimal(amt_str), curr, home_curr, eff_date)
                        salary_resumes_date = eff_date
                    except Exception:
                        pass
            else:
                # Fallback to manual regex for cases not caught by extraction.py
                rem_m = re.search(r'remaining confirmed monthly salary is\s*(?:(?:IDR|INR|USD|EUR|ZAR)\s*)?([0-9,]+(?:\.[0-9]+)?)', msg.message_text, re.IGNORECASE)
                if rem_m:
                    amt_str = rem_m.group(1).replace(',', '')
                    try:
                        curr_m = re.search(r'\b(IDR|INR|USD|EUR|ZAR)\b', msg.message_text)
                        m_curr = curr_m.group(1).upper() if curr_m else home_curr
                        remaining_household_salary = fx_graph.convert(Decimal(amt_str), m_curr, home_curr, eval_date)
                    except Exception:
                        pass

    # 3. Deduplication and linked event chains
    linked_to_settled: Set[str] = set()
    for e in cleaned_events:
        if e.status == 'settled' and e.linked_event_id:
            linked_to_settled.add(e.linked_event_id)

    # 4. Filter future events
    pending_debits: List[FinancialEvent] = []
    scheduled_events: List[FinancialEvent] = []

    for e in cleaned_events:
        if e.event_id in cancelled_event_ids or e.status in ('failed', 'cancelled', 'unrealized'):
            continue
        if e.event_id in linked_to_settled:
            continue
        if e.direction == 'non_cash':
            continue

        eff_date = e.settlement_date or e.event_date

        if eff_date >= eval_date:
            if e.status == 'pending':
                if e.direction == 'debit':
                    pending_debits.append(e)
            elif e.status == 'scheduled':
                scheduled_events.append(e)

    # 5. Detect Recurring Streams from Historical Settled Events (< eval_date)
    hist_settled = [
        e for e in cleaned_events
        if e.status == 'settled'
        and (e.settlement_date or e.event_date) <= eval_date
        and e.direction in ('credit', 'debit')
        and e.amount_home is not None
        and e.amount_home > 0
    ]

    # Variable categories: group by category
    # Fixed categories: group by (category, normalized_description)
    variable_categories = {'groceries', 'dining', 'transport'}

    groups: Dict[Tuple[str, str, str], List[FinancialEvent]] = defaultdict(list)
    for e in hist_settled:
        if e.category in variable_categories and e.direction == 'debit':
            groups[(e.category, e.direction, 'variable')].append(e)
        else:
            desc_key = e.description.strip().lower()
            desc_key = re.sub(r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\b', '', desc_key)
            desc_key = re.sub(r'\b\d{4}\b', '', desc_key).strip()
            groups[(e.category, e.direction, desc_key)].append(e)

    recurring_expense_streams: List[RecurringStream] = []
    salary_streams: List[RecurringStream] = []

    for (cat, direction, desc_key), ev_list in groups.items():
        if len(ev_list) < 2:
            continue
        ev_list.sort(key=lambda x: (x.settlement_date or x.event_date))

        intervals = []
        for i in range(1, len(ev_list)):
            d1 = ev_list[i-1].settlement_date or ev_list[i-1].event_date
            d2 = ev_list[i].settlement_date or ev_list[i].event_date
            days = (d2 - d1).days
            if days > 0:
                intervals.append(days)

        if not intervals:
            continue

        import statistics
        median_interval = statistics.median(intervals)
        avg_interval = median_interval

        last_ev = ev_list[-1]
        last_date = last_ev.settlement_date or last_ev.event_date
        days_since_last = (eval_date - last_date).days

        # Determine stream frequency and interval
        is_monthly = 25 <= avg_interval <= 35
        is_weekly = 6 <= avg_interval <= 8
        is_biweekly = 13 <= avg_interval <= 16
        is_frequent = avg_interval < 6 or (8 < avg_interval < 13) or (16 < avg_interval < 25)

        # Freshness filter
        if is_monthly and days_since_last > 40:
            continue
        if is_weekly and days_since_last > 14:
            continue
        if is_biweekly and days_since_last > 21:
            continue
        if is_frequent and days_since_last > round(avg_interval * 2.5):
            continue

        # Calculate base amount
        if desc_key == 'variable':
            # For variable expenses (groceries/dining/transport): use average of all detected events
            base_amt = sum(e.amount_home for e in ev_list) / Decimal(len(ev_list))
            if 6 <= median_interval <= 8:
                interval_days = 7
                dom = None
            elif 13 <= median_interval <= 16:
                interval_days = 14
                dom = None
            elif 25 <= median_interval <= 35:
                interval_days = 30
                dom = last_date.day
            else:
                interval_days = max(1, round(median_interval))
                dom = None
            flex = last_ev.flexibility or 'fixed'
            min_allowed = last_ev.minimum_allowed_amount
        else:
            base_amt = last_ev.amount_home
            interval_days = 30 if is_monthly else max(1, round(avg_interval))
            dom = last_date.day if is_monthly else None
            flex = last_ev.flexibility or 'fixed'
            min_allowed = last_ev.minimum_allowed_amount

        # Check if terminated payroll
        if 'final employer payroll' in last_ev.description.lower() or employment_ended:
            if cat == 'salary' and direction == 'credit':
                continue

        stream = RecurringStream(
            stream_id=f"stream_{last_ev.event_id}",
            user_id=user_id,
            category=cat,
            direction=direction,
            base_amount=base_amt,
            interval_days=interval_days,
            anchor_date=last_date,
            day_of_month=dom,
            flexibility=flex,
            minimum_allowed_amount=min_allowed,
            representative_event_id=last_ev.event_id,
            description=last_ev.description,
        )

        if cat == 'salary' and direction == 'credit':
            if remaining_household_salary is not None:
                stream.base_amount = remaining_household_salary
            if salary_resumes_amount is not None:
                stream.base_amount = salary_resumes_amount
                if salary_resumes_date and salary_resumes_date > eval_date:
                    stream.start_date = salary_resumes_date
            salary_streams.append(stream)
        else:
            recurring_expense_streams.append(stream)

    # Check scheduled salary events in future
    scheduled_salaries = [
        e for e in scheduled_events
        if e.category == 'salary' and e.direction == 'credit'
    ]
    if scheduled_salaries and not salary_streams and not employment_ended:
        for sal_ev in scheduled_salaries:
            eff_d = sal_ev.settlement_date or sal_ev.event_date
            salary_streams.append(RecurringStream(
                stream_id=f"stream_{sal_ev.event_id}",
                user_id=user_id,
                category='salary',
                direction='credit',
                base_amount=sal_ev.amount_home,
                interval_days=30,
                anchor_date=eff_d,
                day_of_month=eff_d.day,
                flexibility='fixed',
                minimum_allowed_amount=None,
                representative_event_id=sal_ev.event_id,
                description=sal_ev.description,
                source_type='scheduled',
            ))

    # 6. Adjust balance from the global reference date to eval_date
    # The profile's current_available_balance is assumed to be as of global_reference_date
    ref_date = global_reference_date
    bal = profile.current_available_balance
    for e in cleaned_events:
        eff_date = e.settlement_date or e.event_date
        if eff_date is None or e.status != 'settled':
            continue
        if e.event_id in cancelled_event_ids or e.event_id in linked_to_settled:
            continue

        if eval_date >= ref_date:
            if ref_date < eff_date <= eval_date:
                if e.direction == 'credit': bal += e.amount_home
                elif e.direction == 'debit': bal -= e.amount_home
        else:
            if eval_date < eff_date <= ref_date:
                if e.direction == 'credit': bal -= e.amount_home
                elif e.direction == 'debit': bal += e.amount_home

    return UserLedger(
        user_id=user_id,
        profile=profile,
        balance_at_eval_date=bal,
        events=cleaned_events,
        pending_debits=pending_debits,
        scheduled_events=scheduled_events,
        recurring_expense_streams=recurring_expense_streams,
        salary_streams=salary_streams,
        event_lookup=event_lookup,
    )
