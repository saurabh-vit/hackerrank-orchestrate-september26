"""
loaders.py — CSV parsing, schema validation, and index building.

All monetary fields are parsed as Decimal. Builds lookup indexes by
user_id, request_id, event_id for fast access throughout the pipeline.
"""

import csv
import os
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import date, datetime


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Profile:
    user_id: str
    home_currency: str
    current_available_balance: Decimal
    minimum_balance_to_keep: Decimal
    financial_priorities: List[str]
    expense_categories_to_protect: List[str]
    expense_categories_willing_to_reduce: List[str]
    expense_categories_willing_to_stop: List[str]
    payment_methods_user_will_consider: List[str]
    max_installment_months: Optional[int]  # None = user rejects installments


@dataclass
class FinancialEvent:
    event_id: str
    user_id: str
    event_type: str
    description: str
    category: str
    direction: str  # credit, debit, non_cash
    amount: Optional[Decimal]  # None if blank (needs image extraction)
    currency: str
    event_date: date
    settlement_date: Optional[date]
    status: str  # settled, pending, scheduled, unrealized, failed, cancelled
    linked_event_id: str  # empty string if none
    flexibility: str  # fixed, reducible, stoppable, reducible_or_stoppable, or empty
    minimum_allowed_amount: Optional[Decimal]
    # Added during processing
    amount_home: Optional[Decimal] = None  # amount in home currency
    is_recurring: bool = False
    recurrence_interval_days: Optional[int] = None


@dataclass
class Request:
    request_id: str
    user_id: str
    request_date: date
    request_type: str
    requested_amount: Decimal
    desired_completion_date: date
    allows_partial_payment: bool
    request_text: str


@dataclass
class PaymentOption:
    payment_option_id: str
    request_id: str
    payment_method: str  # full_payment or installments
    payment_amount: Decimal
    number_of_payments: int
    first_payment_date: date
    payment_frequency_days: Optional[int]  # None for full_payment
    financing_fee: Decimal
    total_payable_amount: Decimal


@dataclass
class ExchangeRate:
    rate_date: date
    from_currency: str
    to_currency: str
    rate: Decimal


@dataclass
class Message:
    message_id: str
    user_id: str
    request_id: str  # may be empty
    related_event_id: str  # may be empty
    sent_at: datetime
    source_type: str  # employer, service_provider, bank, merchant, financial_service
    message_text: str


@dataclass
class ImageRef:
    image_id: str
    user_id: str
    request_id: str
    related_event_id: str


@dataclass
class SampleRequest:
    """A sample request with known-good output fields for validation."""
    request_id: str
    user_id: str
    request_date: date
    request_type: str
    requested_amount: Decimal
    desired_completion_date: date
    allows_partial_payment: bool
    request_text: str
    # Output fields
    amount_safe_to_pay: Decimal
    affordability_status: str
    recommended_payment_method: str
    payment_plan: str
    earliest_date_for_full_payment: str  # may be empty
    spending_changes_needed: str
    decision_explanation: str


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_date(s: str) -> date:
    """Parse YYYY-MM-DD date string."""
    return datetime.strptime(s.strip(), "%Y-%m-%d").date()


def _parse_optional_date(s: str) -> Optional[date]:
    """Parse YYYY-MM-DD date string, returning None for empty."""
    s = s.strip()
    if not s:
        return None
    return datetime.strptime(s, "%Y-%m-%d").date()


def _parse_datetime(s: str) -> datetime:
    """Parse ISO-8601 datetime string."""
    s = s.strip()
    # Handle Z suffix
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'
    return datetime.fromisoformat(s)


def _parse_decimal(s: str) -> Optional[Decimal]:
    """Parse a decimal string, returning None for empty strings."""
    s = s.strip()
    if not s:
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        raise ValueError(f"Cannot parse decimal: '{s}'")


def _parse_bool(s: str) -> bool:
    return s.strip().lower() == 'true'


def _parse_pipe_list(s: str) -> List[str]:
    """Parse pipe-delimited list, returning empty list for empty string."""
    s = s.strip()
    if not s:
        return []
    return [item.strip() for item in s.split('|') if item.strip()]


def _parse_int(s: str) -> Optional[int]:
    s = s.strip()
    if not s:
        return None
    return int(s)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def _csv_rows(filepath: str) -> List[dict]:
    """Read a CSV file and return list of dicts."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_profiles(dataset_dir: str) -> Dict[str, Profile]:
    """Load financial_profiles.csv → {user_id: Profile}."""
    rows = _csv_rows(os.path.join(dataset_dir, 'financial_profiles.csv'))
    profiles = {}
    for r in rows:
        p = Profile(
            user_id=r['user_id'],
            home_currency=r['home_currency'],
            current_available_balance=Decimal(r['current_available_balance']),
            minimum_balance_to_keep=Decimal(r['minimum_balance_to_keep']),
            financial_priorities=_parse_pipe_list(r['financial_priorities']),
            expense_categories_to_protect=_parse_pipe_list(r['expense_categories_to_protect']),
            expense_categories_willing_to_reduce=_parse_pipe_list(r['expense_categories_user_is_willing_to_reduce']),
            expense_categories_willing_to_stop=_parse_pipe_list(r['expense_categories_user_is_willing_to_stop']),
            payment_methods_user_will_consider=_parse_pipe_list(r['payment_methods_user_will_consider']),
            max_installment_months=_parse_int(r['max_installment_months']),
        )
        profiles[p.user_id] = p
    return profiles


def load_events(dataset_dir: str) -> List[FinancialEvent]:
    """Load financial_events.csv → list of FinancialEvent."""
    rows = _csv_rows(os.path.join(dataset_dir, 'financial_events.csv'))
    events = []
    for r in rows:
        amt = _parse_decimal(r['amount'])
        min_amt = _parse_decimal(r['minimum_allowed_amount'])
        e = FinancialEvent(
            event_id=r['event_id'],
            user_id=r['user_id'],
            event_type=r['event_type'],
            description=r['description'],
            category=r['category'],
            direction=r['direction'],
            amount=amt,
            currency=r['currency'],
            event_date=_parse_date(r['event_date']),
            settlement_date=_parse_optional_date(r['settlement_date']),
            status=r['status'],
            linked_event_id=r['linked_event_id'].strip(),
            flexibility=r['flexibility'].strip(),
            minimum_allowed_amount=min_amt,
        )
        events.append(e)
    return events


def load_requests(dataset_dir: str) -> List[Request]:
    """Load requests.csv → list of Request."""
    rows = _csv_rows(os.path.join(dataset_dir, 'requests.csv'))
    requests = []
    for r in rows:
        req = Request(
            request_id=r['request_id'],
            user_id=r['user_id'],
            request_date=_parse_date(r['request_date']),
            request_type=r['request_type'],
            requested_amount=Decimal(r['requested_amount']),
            desired_completion_date=_parse_date(r['desired_completion_date']),
            allows_partial_payment=_parse_bool(r['allows_partial_payment']),
            request_text=r['request_text'],
        )
        requests.append(req)
    return requests


def load_payment_options(dataset_dir: str) -> List[PaymentOption]:
    """Load request_payment_options.csv → list of PaymentOption."""
    rows = _csv_rows(os.path.join(dataset_dir, 'request_payment_options.csv'))
    options = []
    for r in rows:
        freq = _parse_int(r['payment_frequency_days'])
        opt = PaymentOption(
            payment_option_id=r['payment_option_id'],
            request_id=r['request_id'],
            payment_method=r['payment_method'],
            payment_amount=Decimal(r['payment_amount']),
            number_of_payments=int(r['number_of_payments']),
            first_payment_date=_parse_date(r['first_payment_date']),
            payment_frequency_days=freq,
            financing_fee=Decimal(r['financing_fee']),
            total_payable_amount=Decimal(r['total_payable_amount']),
        )
        options.append(opt)
    return options


def load_exchange_rates(dataset_dir: str) -> List[ExchangeRate]:
    """Load exchange_rates.csv → list of ExchangeRate."""
    rows = _csv_rows(os.path.join(dataset_dir, 'exchange_rates.csv'))
    rates = []
    for r in rows:
        er = ExchangeRate(
            rate_date=_parse_date(r['rate_date']),
            from_currency=r['from_currency'].strip(),
            to_currency=r['to_currency'].strip(),
            rate=Decimal(r['rate']),
        )
        rates.append(er)
    return rates


def load_messages(dataset_dir: str) -> List[Message]:
    """Load messages.csv → list of Message."""
    rows = _csv_rows(os.path.join(dataset_dir, 'messages.csv'))
    messages = []
    for r in rows:
        m = Message(
            message_id=r['message_id'],
            user_id=r['user_id'],
            request_id=r.get('request_id', '').strip(),
            related_event_id=r.get('related_event_id', '').strip(),
            sent_at=_parse_datetime(r['sent_at']),
            source_type=r['source_type'].strip(),
            message_text=r['message_text'],
        )
        messages.append(m)
    return messages


def load_images(dataset_dir: str) -> List[ImageRef]:
    """Load images.csv → list of ImageRef."""
    rows = _csv_rows(os.path.join(dataset_dir, 'images.csv'))
    images = []
    for r in rows:
        img = ImageRef(
            image_id=r['image_id'].strip(),
            user_id=r['user_id'].strip(),
            request_id=r.get('request_id', '').strip(),
            related_event_id=r.get('related_event_id', '').strip(),
        )
        images.append(img)
    return images


def load_samples(dataset_dir: str) -> List[SampleRequest]:
    """Load sample_requests.csv → list of SampleRequest (with known-good outputs)."""
    rows = _csv_rows(os.path.join(dataset_dir, 'sample_requests.csv'))
    samples = []
    for r in rows:
        s = SampleRequest(
            request_id=r['request_id'],
            user_id=r['user_id'],
            request_date=_parse_date(r['request_date']),
            request_type=r['request_type'],
            requested_amount=Decimal(r['requested_amount']),
            desired_completion_date=_parse_date(r['desired_completion_date']),
            allows_partial_payment=_parse_bool(r['allows_partial_payment']),
            request_text=r['request_text'],
            amount_safe_to_pay=Decimal(r['amount_safe_to_pay']),
            affordability_status=r['affordability_status'],
            recommended_payment_method=r['recommended_payment_method'],
            payment_plan=r['payment_plan'],
            earliest_date_for_full_payment=r.get('earliest_date_for_full_payment', '').strip(),
            spending_changes_needed=r['spending_changes_needed'],
            decision_explanation=r['decision_explanation'],
        )
        samples.append(s)
    return samples


def load_output_template(dataset_dir: str) -> List[str]:
    """Load output.csv template → list of request_ids."""
    rows = _csv_rows(os.path.join(dataset_dir, 'output.csv'))
    return [r['request_id'] for r in rows]


# ---------------------------------------------------------------------------
# Index builders
# ---------------------------------------------------------------------------

@dataclass
class DataStore:
    """Central data store with all loaded data and indexes."""
    profiles: Dict[str, Profile] = field(default_factory=dict)
    events: List[FinancialEvent] = field(default_factory=list)
    requests: List[Request] = field(default_factory=list)
    payment_options: List[PaymentOption] = field(default_factory=list)
    exchange_rates: List[ExchangeRate] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    images: List[ImageRef] = field(default_factory=list)
    samples: List[SampleRequest] = field(default_factory=list)
    output_request_ids: List[str] = field(default_factory=list)

    # Indexes (built after loading)
    events_by_user: Dict[str, List[FinancialEvent]] = field(default_factory=dict)
    events_by_id: Dict[str, FinancialEvent] = field(default_factory=dict)
    requests_by_id: Dict[str, Request] = field(default_factory=dict)
    options_by_request: Dict[str, List[PaymentOption]] = field(default_factory=dict)
    messages_by_user: Dict[str, List[Message]] = field(default_factory=dict)
    messages_by_event: Dict[str, List[Message]] = field(default_factory=dict)
    messages_by_request: Dict[str, List[Message]] = field(default_factory=dict)
    images_by_event: Dict[str, ImageRef] = field(default_factory=dict)
    samples_by_id: Dict[str, SampleRequest] = field(default_factory=dict)

    def build_indexes(self):
        """Build all lookup indexes from loaded data."""
        # Events by user and by id
        self.events_by_user = {}
        self.events_by_id = {}
        for e in self.events:
            self.events_by_user.setdefault(e.user_id, []).append(e)
            self.events_by_id[e.event_id] = e

        # Requests by id
        self.requests_by_id = {r.request_id: r for r in self.requests}

        # Payment options by request
        self.options_by_request = {}
        for o in self.payment_options:
            self.options_by_request.setdefault(o.request_id, []).append(o)

        # Messages by user, by event, by request
        self.messages_by_user = {}
        self.messages_by_event = {}
        self.messages_by_request = {}
        for m in self.messages:
            self.messages_by_user.setdefault(m.user_id, []).append(m)
            if m.related_event_id:
                self.messages_by_event.setdefault(m.related_event_id, []).append(m)
            if m.request_id:
                self.messages_by_request.setdefault(m.request_id, []).append(m)

        # Images by event
        self.images_by_event = {}
        for img in self.images:
            if img.related_event_id:
                self.images_by_event[img.related_event_id] = img

        # Samples by id
        self.samples_by_id = {s.request_id: s for s in self.samples}


def load_all(dataset_dir: str) -> DataStore:
    """Load all datasets and build indexes. Validate invariants."""
    ds = DataStore()
    ds.profiles = load_profiles(dataset_dir)
    ds.events = load_events(dataset_dir)
    ds.requests = load_requests(dataset_dir)
    ds.payment_options = load_payment_options(dataset_dir)
    ds.exchange_rates = load_exchange_rates(dataset_dir)
    ds.messages = load_messages(dataset_dir)
    ds.images = load_images(dataset_dir)
    ds.samples = load_samples(dataset_dir)
    ds.output_request_ids = load_output_template(dataset_dir)

    ds.build_indexes()

    # -----------------------------------------------------------------------
    # Validate dataset invariants (§2.5)
    # -----------------------------------------------------------------------
    blank_events = [e for e in ds.events if e.amount is None]
    assert len(blank_events) == 16, (
        f"Expected 16 blank-amount events, got {len(blank_events)}"
    )
    for e in blank_events:
        assert e.event_id in ds.images_by_event, (
            f"Blank-amount event {e.event_id} has no matching image"
        )

    # Full payment fees all zero
    for o in ds.payment_options:
        if o.payment_method == 'full_payment':
            assert o.financing_fee == 0, (
                f"{o.payment_option_id}: full_payment fee should be 0, got {o.financing_fee}"
            )

    # Installment fees all > 0
    for o in ds.payment_options:
        if o.payment_method == 'installments':
            assert o.financing_fee > 0, (
                f"{o.payment_option_id}: installment fee should be > 0, got {o.financing_fee}"
            )

    # total_payable_amount == payment_amount * number_of_payments
    for o in ds.payment_options:
        expected = o.payment_amount * o.number_of_payments
        diff = abs(expected - o.total_payable_amount)
        assert diff < Decimal('0.01'), (
            f"{o.payment_option_id}: total {o.total_payable_amount} != "
            f"amount {o.payment_amount} * {o.number_of_payments} = {expected}"
        )

    # Currencies
    home_currencies = set(p.home_currency for p in ds.profiles.values())
    assert home_currencies == {'EUR', 'IDR', 'INR', 'USD', 'ZAR'}, (
        f"Unexpected currencies: {home_currencies}"
    )

    # Request count
    assert len(ds.requests) == 250, f"Expected 250 requests, got {len(ds.requests)}"
    assert len(ds.output_request_ids) == 250, (
        f"Expected 250 output rows, got {len(ds.output_request_ids)}"
    )

    print(f"[loaders] Loaded: {len(ds.profiles)} profiles, {len(ds.events)} events, "
          f"{len(ds.requests)} requests, {len(ds.payment_options)} options, "
          f"{len(ds.exchange_rates)} rates, {len(ds.messages)} messages, "
          f"{len(ds.images)} images, {len(ds.samples)} samples")
    print("[loaders] All dataset invariants validated [OK]")

    return ds
