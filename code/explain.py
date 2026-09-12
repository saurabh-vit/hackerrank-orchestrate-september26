"""
explain.py — Explanation generation for Buy or Wait? decisions.

Generates concise (1–2 sentences), grounded, mathematically consistent explanations
matching the challenge's exact voice and style.
"""

from decimal import Decimal
from datetime import date
from typing import Dict, Any, Optional

from loaders import Request, Profile
from events import UserLedger


def _format_currency(amt: Decimal, curr: str) -> str:
    """Format monetary amount with currency code and comma separators."""
    if amt == amt.to_integral():
        return f"{curr} {int(amt):,}"
    else:
        formatted = f"{amt:,.2f}"
        if formatted.endswith('.00'):
            return f"{curr} {int(amt):,}"
        return f"{curr} {formatted}"


def _format_date(d: date) -> str:
    """Format date in UK / international style e.g. '15 November 2019'."""
    return d.strftime("%d %B %Y").lstrip('0')


def generate_explanation(
    request: Request,
    ledger: UserLedger,
    decision: Dict[str, Any],
) -> str:
    """
    Generate a concise, grounded explanation for the decision.
    """
    profile = ledger.profile
    home_curr = profile.home_currency
    req_amt = request.requested_amount
    req_amt_str = _format_currency(req_amt, home_curr)
    min_bal_str = _format_currency(profile.minimum_balance_to_keep, home_curr)
    deadline_str = _format_date(request.desired_completion_date)

    status = decision['affordability_status']
    method = decision['recommended_payment_method']
    plan_str = decision['payment_plan']
    earliest_str = decision.get('earliest_date_for_full_payment', '').strip()
    spending_changes_str = decision.get('spending_changes_needed', 'none').strip()

    # 1. affordable_now
    if status == 'affordable_now':
        return (
            f"Pay {req_amt_str} today. This leaves at least {min_bal_str} available over the next 90 days."
        )

    # 2. affordable_with_plan
    if status == 'affordable_with_plan':
        # Check if spending changes needed
        if spending_changes_str != 'none':
            # Describe spending changes
            changes_desc = []
            for sc in spending_changes_str.split('|'):
                parts = sc.split(':')
                action = parts[0]
                ev_id = parts[1]
                ev = ledger.event_lookup.get(ev_id)
                desc = ev.description.lower() if ev else ev_id
                if action == 'stop':
                    changes_desc.append(f"stop the {desc}")
                elif action == 'reduce_to':
                    new_amt = Decimal(parts[2])
                    new_amt_str = _format_currency(new_amt, home_curr)
                    changes_desc.append(f"reduce the {desc} to {new_amt_str}")

            joined_changes = " and ".join(changes_desc).capitalize()

            if method == 'full_payment':
                return (
                    f"{joined_changes}, then pay {req_amt_str} today. This leaves at least {min_bal_str} available."
                )
            elif method == 'partial_payment':
                plan_parts = plan_str.split('|')
                amt1 = Decimal(plan_parts[0].split(':')[1])
                amt2 = Decimal(plan_parts[1].split(':')[1])
                date2 = date.fromisoformat(plan_parts[1].split(':')[0])
                amt1_str = _format_currency(amt1, home_curr)
                amt2_str = _format_currency(amt2, home_curr)
                date2_str = _format_date(date2)
                return (
                    f"{joined_changes}, then pay {amt1_str} today and the remaining {amt2_str} on {date2_str}. "
                    f"This keeps the {min_bal_str} minimum protected."
                )

        # Partial payment without spending changes
        if method == 'partial_payment':
            plan_parts = plan_str.split('|')
            amt1 = Decimal(plan_parts[0].split(':')[1])
            amt2 = Decimal(plan_parts[1].split(':')[1])
            date2 = date.fromisoformat(plan_parts[1].split(':')[0])
            amt1_str = _format_currency(amt1, home_curr)
            amt2_str = _format_currency(amt2, home_curr)
            date2_str = _format_date(date2)
            return (
                f"Pay {amt1_str} today and the remaining {amt2_str} on {date2_str}. "
                f"This completes the full request and keeps the {min_bal_str} minimum protected."
            )

        # Installments without spending changes
        if method == 'installments':
            plan_parts = plan_str.split('|')
            num_inst = len(plan_parts)
            first_p = plan_parts[0].split(':')
            inst_amt = Decimal(first_p[1])
            inst_amt_str = _format_currency(inst_amt, home_curr)
            first_d = date.fromisoformat(first_p[0])
            first_d_str = _format_date(first_d)
            return (
                f"Use {num_inst} installments of {inst_amt_str}, starting {first_d_str}. "
                f"This leaves at least {min_bal_str} available."
            )

    # 3. affordable_later (wait)
    if status == 'affordable_later':
        if earliest_str:
            earliest_d = date.fromisoformat(earliest_str)
            earliest_d_str = _format_date(earliest_d)
            return (
                f"Pay {req_amt_str} in full on {earliest_d_str}. "
                f"Paying earlier would take the balance below the {min_bal_str} minimum."
            )

    # 4. not_affordable
    safe_amt = decision.get('amount_safe_to_pay', Decimal('0'))
    if safe_amt > Decimal('0') and not earliest_str:
        safe_str = _format_currency(safe_amt, home_curr)
        return (
            f"Do not proceed with the {req_amt_str} request. "
            f"Although {safe_str} is available today, the full amount cannot be completed safely within 90 days."
        )
    else:
        return (
            f"Do not make this payment by {deadline_str}. "
            f"None of the available options keeps the {min_bal_str} minimum protected."
        )
