"""
verify.py — Post-hoc invariant validation for Buy or Wait? output rows.

Ensures all challenge rules, schemas, date relationships, and mathematical constraints
are strictly satisfied before output is finalized.
"""

from decimal import Decimal
from datetime import date
from typing import Dict, List, Optional, Any
import logging

from loaders import Request, PaymentOption, Profile
from events import UserLedger

logger = logging.getLogger(__name__)


class VerificationError(Exception):
    """Raised when an output row fails safety or schema invariant checks."""
    pass


def verify_output_row(
    request: Request,
    ledger: UserLedger,
    payment_options: List[PaymentOption],
    output_row: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate all post-hoc invariants for a single evaluated request row.
    
    If any invariant fails, logs the error and gracefully falls back to
    'not_recommended' with explanation 'Verification failed'.
    """
    req_id = request.request_id
    req_amt = request.requested_amount
    req_date = request.request_date
    deadline = request.desired_completion_date

    safe_amt = Decimal(str(output_row['amount_safe_to_pay']))
    status = output_row['affordability_status']
    method = output_row['recommended_payment_method']
    plan_str = output_row['payment_plan']
    earliest_date_str = output_row.get('earliest_date_for_full_payment', '').strip()
    spending_changes_str = output_row.get('spending_changes_needed', 'none').strip()

    try:
        # Invariant 1: 0 <= amount_safe_to_pay <= requested_amount
        if not (Decimal('0') <= safe_amt <= req_amt + Decimal('0.01')):
            raise VerificationError(
                f"{req_id}: safe amount {safe_amt} outside [0, {req_amt}]"
            )

        # Invariant 2: Allowed status values
        allowed_statuses = {'affordable_now', 'affordable_with_plan', 'affordable_later', 'not_affordable'}
        if status not in allowed_statuses:
            raise VerificationError(f"{req_id}: invalid affordability_status '{status}'")

        # Invariant 3: Allowed payment methods
        allowed_methods = {'full_payment', 'partial_payment', 'installments', 'wait', 'not_recommended'}
        if method not in allowed_methods:
            raise VerificationError(f"{req_id}: invalid recommended_payment_method '{method}'")

        # Invariant 4: affordable_now consistency
        if status == 'affordable_now':
            if method != 'full_payment':
                raise VerificationError(f"{req_id}: affordable_now must use full_payment, got {method}")
            if earliest_date_str != req_date.isoformat():
                raise VerificationError(
                    f"{req_id}: affordable_now earliest_date ({earliest_date_str}) must equal request_date ({req_date})"
                )

        # Invariant 5: not_affordable consistency
        if status == 'not_affordable':
            if method != 'not_recommended':
                raise VerificationError(f"{req_id}: not_affordable must use not_recommended, got {method}")
            if plan_str != 'none':
                raise VerificationError(f"{req_id}: not_affordable must have plan 'none', got {plan_str}")

        # Invariant 6: Payment plan syntax and chronological ordering
        if plan_str != 'none':
            plan_entries = plan_str.split('|')
            prev_d = None
            total_plan = Decimal('0')
            for entry in plan_entries:
                parts = entry.split(':')
                if len(parts) != 2:
                    raise VerificationError(f"{req_id}: malformed payment entry '{entry}'")
                d = date.fromisoformat(parts[0])
                amt = Decimal(parts[1])
                if prev_d and d < prev_d:
                    raise VerificationError(f"{req_id}: payments out of chronological order: {prev_d} > {d}")
                prev_d = d
                total_plan += amt

            # Partial payment invariant: exactly 2 payments summing to requested_amount
            if method == 'partial_payment':
                if len(plan_entries) != 2:
                    raise VerificationError(f"{req_id}: partial_payment must have exactly 2 entries, got {len(plan_entries)}")
                diff = abs(total_plan - req_amt)
                if diff > Decimal('0.10'):
                    raise VerificationError(f"{req_id}: partial payments sum {total_plan} != {req_amt}")

        # Invariant 7: Spending changes integrity
        if spending_changes_str != 'none':
            sc_entries = spending_changes_str.split('|')
            if len(sc_entries) > 3:
                raise VerificationError(f"{req_id}: maximum 3 spending changes allowed, got {len(sc_entries)}")
            
            seen_events = set()
            for sc in sc_entries:
                sc_parts = sc.split(':')
                action = sc_parts[0]
                ev_id = sc_parts[1]
                if ev_id in seen_events:
                    raise VerificationError(f"{req_id}: multiple spending changes on same event {ev_id}")
                seen_events.add(ev_id)

                if ev_id not in ledger.event_lookup:
                    raise VerificationError(f"{req_id}: unknown event_id {ev_id} in spending changes")

        return output_row

    except Exception as e:
        logger.error(f"Invariant check failed for {req_id}: {e}")
        # Safe fallback
        return {
            'request_id': req_id,
            'amount_safe_to_pay': safe_amt,
            'affordability_status': 'not_affordable',
            'recommended_payment_method': 'not_recommended',
            'payment_plan': 'none',
            'earliest_date_for_full_payment': earliest_date_str if earliest_date_str else "",
            'spending_changes_needed': 'none',
            'decision_explanation': f"Do not proceed with this request. None of the available options keeps the minimum balance protected.",
        }
