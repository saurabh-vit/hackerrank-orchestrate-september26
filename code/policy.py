"""
policy.py — Decision engine for Buy or Wait?

Implements:
1. Candidate payment plan generation (full_payment, partial_payment, installments, wait, not_recommended).
2. Spending changes generation (up to 3 changes on flexible recurring events).
3. Ranking plans according to the strict tie-breaking ladder in §6.3 / problem statement.
"""

from decimal import Decimal
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

from loaders import Request, PaymentOption, Profile
from events import UserLedger, RecurringStream
from forecast import compute_forecast, is_plan_safe, simulate_balance_timeline


@dataclass
class CandidatePlan:
    """A candidate payment plan for a request."""
    method: str  # full_payment, partial_payment, installments, wait, not_recommended
    affordability_status: str  # affordable_now, affordable_with_plan, affordable_later, not_affordable
    payment_plan_str: str  # e.g., '2024-03-03:25256' or 'none'
    payments: Dict[date, Decimal]  # date -> amount
    first_payment_date: Optional[date]
    completion_date: Optional[date]
    total_paid: Decimal
    num_payments: int
    spending_changes_str: str  # e.g., 'stop:event_476' or 'none'
    spending_changes_dict: Dict[str, Any]
    payment_option_id: Optional[str] = None
    completes_by_deadline: bool = True
    is_safe: bool = True


def format_payment_plan(payments: Dict[date, Decimal]) -> str:
    """Format payments dict as chronological pipe-delimited YYYY-MM-DD:amount string."""
    if not payments:
        return 'none'
    sorted_items = sorted(payments.items(), key=lambda x: x[0])
    parts = []
    for d, amt in sorted_items:
        if amt == amt.to_integral():
            amt_str = f"{int(amt)}"
        else:
            amt_str = f"{amt:.2f}"
        parts.append(f"{d.isoformat()}:{amt_str}")
    return '|'.join(parts)


def format_spending_changes(changes: Dict[str, Any]) -> str:
    """Format spending changes dict into pipe-separated string."""
    if not changes:
        return 'none'
    parts = []
    for ev_id, action in changes.items():
        if action == 'stop':
            parts.append(f"stop:{ev_id}")
        elif isinstance(action, Decimal):
            if action == action.to_integral():
                amt_str = f"{int(action)}"
            else:
                amt_str = f"{action:.2f}"
            parts.append(f"reduce_to:{ev_id}:{amt_str}")
    return '|'.join(parts) if parts else 'none'


def get_possible_spending_changes(ledger: UserLedger) -> List[Dict[str, Any]]:
    """
    Generate valid candidate combinations of spending changes (up to 3 changes).
    Only targets flexible recurring streams where category is in user's willing list.
    """
    p = ledger.profile
    single_changes: List[Tuple[str, Any]] = []

    for rs in ledger.recurring_expense_streams:
        ev_id = rs.representative_event_id
        cat = rs.category
        flex = rs.flexibility

        if flex in ('stoppable', 'reducible_or_stoppable') and cat in p.expense_categories_willing_to_stop:
            single_changes.append((ev_id, 'stop'))

        if flex in ('reducible', 'reducible_or_stoppable') and cat in p.expense_categories_willing_to_reduce:
            if rs.minimum_allowed_amount is not None and rs.minimum_allowed_amount < rs.base_amount:
                single_changes.append((ev_id, rs.minimum_allowed_amount))

    combinations: List[Dict[str, Any]] = [{}]
    
    for c1 in single_changes:
        combinations.append({c1[0]: c1[1]})

    for i in range(len(single_changes)):
        for j in range(i + 1, len(single_changes)):
            c1, c2 = single_changes[i], single_changes[j]
            if c1[0] != c2[0]:
                combinations.append({c1[0]: c1[1], c2[0]: c2[1]})

    for i in range(len(single_changes)):
        for j in range(i + 1, len(single_changes)):
            for k in range(j + 1, len(single_changes)):
                c1, c2, c3 = single_changes[i], single_changes[j], single_changes[k]
                if len({c1[0], c2[0], c3[0]}) == 3:
                    combinations.append({c1[0]: c1[1], c2[0]: c2[1], c3[0]: c3[1]})

    return combinations


def evaluate_request(
    request: Request,
    ledger: UserLedger,
    payment_options: List[PaymentOption],
) -> Dict[str, Any]:
    """
    Evaluate a financial request and produce the optimal decision.
    """
    profile = ledger.profile
    req_date = request.request_date
    req_amt = request.requested_amount
    deadline = request.desired_completion_date
    methods_considered = set(profile.payment_methods_user_will_consider)

    base_forecast = compute_forecast(ledger, req_date, req_amt)
    amount_safe_to_pay = base_forecast.amount_safe_to_pay
    earliest_date = base_forecast.earliest_date_for_full_payment
    earliest_date_str = earliest_date.isoformat() if earliest_date is not None else ""

    candidate_plans: List[CandidatePlan] = []

    # 1. Candidate: full_payment now
    if 'full_payment' in methods_considered and amount_safe_to_pay == req_amt:
        candidate_plans.append(CandidatePlan(
            method='full_payment',
            affordability_status='affordable_now',
            payment_plan_str=format_payment_plan({req_date: req_amt}),
            payments={req_date: req_amt},
            first_payment_date=req_date,
            completion_date=req_date,
            total_paid=req_amt,
            num_payments=1,
            spending_changes_str='none',
            spending_changes_dict={},
            completes_by_deadline=(req_date <= deadline),
            is_safe=True,
        ))

    # 2. Candidate: partial_payment
    if (
        request.allows_partial_payment
        and 'partial_payment' in methods_considered
        and Decimal('0') < amount_safe_to_pay < req_amt
        and earliest_date is not None
        and earliest_date <= deadline
    ):
        part1 = amount_safe_to_pay
        part2 = req_amt - amount_safe_to_pay
        payments = {req_date: part1, earliest_date: part2}
        
        if is_plan_safe(ledger, req_date, payments):
            candidate_plans.append(CandidatePlan(
                method='partial_payment',
                affordability_status='affordable_with_plan',
                payment_plan_str=format_payment_plan(payments),
                payments=payments,
                first_payment_date=req_date,
                completion_date=earliest_date,
                total_paid=req_amt,
                num_payments=2,
                spending_changes_str='none',
                spending_changes_dict={},
                completes_by_deadline=(earliest_date <= deadline),
                is_safe=True,
            ))

    # 3. Candidate: installments from payment_options
    if 'installments' in methods_considered:
        for opt in payment_options:
            if opt.payment_method != 'installments':
                continue
            
            if profile.max_installment_months is None or opt.number_of_payments > profile.max_installment_months:
                continue

            inst_payments: Dict[date, Decimal] = {}
            freq = opt.payment_frequency_days or 30
            cur_p_date = opt.first_payment_date
            for _ in range(opt.number_of_payments):
                inst_payments[cur_p_date] = inst_payments.get(cur_p_date, Decimal('0')) + opt.payment_amount
                cur_p_date = cur_p_date + timedelta(days=freq)

            last_payment_date = max(inst_payments.keys())

            if is_plan_safe(ledger, req_date, inst_payments):
                candidate_plans.append(CandidatePlan(
                    method='installments',
                    affordability_status='affordable_with_plan',
                    payment_plan_str=format_payment_plan(inst_payments),
                    payments=inst_payments,
                    first_payment_date=opt.first_payment_date,
                    completion_date=last_payment_date,
                    total_paid=opt.total_payable_amount,
                    num_payments=opt.number_of_payments,
                    spending_changes_str='none',
                    spending_changes_dict={},
                    payment_option_id=opt.payment_option_id,
                    completes_by_deadline=(last_payment_date <= deadline),
                    is_safe=True,
                ))

    # 4. Check plans WITH spending changes if no 0-change plan completes by deadline
    immediate_0_change_completing = [
        p for p in candidate_plans
        if p.completes_by_deadline and len(p.spending_changes_dict) == 0 and p.method in ('full_payment', 'partial_payment', 'installments')
    ]
    
    if not immediate_0_change_completing:
        spending_combinations = get_possible_spending_changes(ledger)
        for sc in spending_combinations:
            if not sc:
                continue
            
            sc_str = format_spending_changes(sc)

            if 'full_payment' in methods_considered:
                payments = {req_date: req_amt}
                if is_plan_safe(ledger, req_date, payments, spending_changes=sc):
                    candidate_plans.append(CandidatePlan(
                        method='full_payment',
                        affordability_status='affordable_with_plan',
                        payment_plan_str=format_payment_plan(payments),
                        payments=payments,
                        first_payment_date=req_date,
                        completion_date=req_date,
                        total_paid=req_amt,
                        num_payments=1,
                        spending_changes_str=sc_str,
                        spending_changes_dict=sc,
                        completes_by_deadline=(req_date <= deadline),
                        is_safe=True,
                    ))

            if request.allows_partial_payment and 'partial_payment' in methods_considered:
                sc_forecast = compute_forecast(ledger, req_date, req_amt, spending_changes=sc)
                sc_safe = sc_forecast.amount_safe_to_pay
                sc_earliest = sc_forecast.earliest_date_for_full_payment
                if Decimal('0') < sc_safe < req_amt and sc_earliest is not None and sc_earliest <= deadline:
                    payments = {req_date: sc_safe, sc_earliest: req_amt - sc_safe}
                    if is_plan_safe(ledger, req_date, payments, spending_changes=sc):
                        candidate_plans.append(CandidatePlan(
                            method='partial_payment',
                            affordability_status='affordable_with_plan',
                            payment_plan_str=format_payment_plan(payments),
                            payments=payments,
                            first_payment_date=req_date,
                            completion_date=sc_earliest,
                            total_paid=req_amt,
                            num_payments=2,
                            spending_changes_str=sc_str,
                            spending_changes_dict=sc,
                            completes_by_deadline=(sc_earliest <= deadline),
                            is_safe=True,
                        ))

            if 'installments' in methods_considered:
                for opt in payment_options:
                    if opt.payment_method != 'installments':
                        continue
                    if profile.max_installment_months is None or opt.number_of_payments > profile.max_installment_months:
                        continue

                    inst_payments: Dict[date, Decimal] = {}
                    freq = opt.payment_frequency_days or 30
                    cur_p_date = opt.first_payment_date
                    for _ in range(opt.number_of_payments):
                        inst_payments[cur_p_date] = inst_payments.get(cur_p_date, Decimal('0')) + opt.payment_amount
                        cur_p_date = cur_p_date + timedelta(days=freq)

                    last_payment_date = max(inst_payments.keys())
                    if is_plan_safe(ledger, req_date, inst_payments, spending_changes=sc):
                        candidate_plans.append(CandidatePlan(
                            method='installments',
                            affordability_status='affordable_with_plan',
                            payment_plan_str=format_payment_plan(inst_payments),
                            payments=inst_payments,
                            first_payment_date=opt.first_payment_date,
                            completion_date=last_payment_date,
                            total_paid=opt.total_payable_amount,
                            num_payments=opt.number_of_payments,
                            spending_changes_str=sc_str,
                            spending_changes_dict=sc,
                            payment_option_id=opt.payment_option_id,
                            completes_by_deadline=(last_payment_date <= deadline),
                            is_safe=True,
                        ))

    # 5. Candidate: wait (if user accepts full_payment and earliest_date exists and > req_date)
    if 'full_payment' in methods_considered and earliest_date is not None and earliest_date > req_date:
        candidate_plans.append(CandidatePlan(
            method='wait',
            affordability_status='affordable_later',
            payment_plan_str=format_payment_plan({earliest_date: req_amt}),
            payments={earliest_date: req_amt},
            first_payment_date=earliest_date,
            completion_date=earliest_date,
            total_paid=req_amt,
            num_payments=1,
            spending_changes_str='none',
            spending_changes_dict={},
            completes_by_deadline=(earliest_date <= deadline),
            is_safe=True,
        ))

    # 6. Rank plans according to tie-breaker ladder
    valid_plans = [p for p in candidate_plans if p.is_safe]

    def plan_sort_key(p: CandidatePlan):
        num_changes = len(p.spending_changes_dict)
        opt_id = p.payment_option_id or 'zzzzzz'
        method_pref = 0 if p.method in ('full_payment', 'partial_payment', 'installments') else 1
        first_d = p.first_payment_date or date(9999, 12, 31)
        return (
            0 if p.completes_by_deadline else 1,
            num_changes,
            method_pref,
            p.total_paid,
            first_d,
            p.num_payments,
            opt_id,
        )

    if valid_plans:
        valid_plans.sort(key=plan_sort_key)
        best_plan = valid_plans[0]
        
        # If best plan is wait but doesn't complete by deadline, and user didn't have any safe completion,
        # wait is still acceptable as affordable_later if earliest_date is found
    else:
        best_plan = CandidatePlan(
            method='not_recommended',
            affordability_status='not_affordable',
            payment_plan_str='none',
            payments={},
            first_payment_date=None,
            completion_date=None,
            total_paid=Decimal('0'),
            num_payments=0,
            spending_changes_str='none',
            spending_changes_dict={},
            completes_by_deadline=False,
            is_safe=True,
        )

    if best_plan.affordability_status == 'affordable_now':
        earliest_date_str = req_date.isoformat()

    return {
        'request_id': request.request_id,
        'amount_safe_to_pay': amount_safe_to_pay,
        'affordability_status': best_plan.affordability_status,
        'recommended_payment_method': best_plan.method,
        'payment_plan': best_plan.payment_plan_str,
        'earliest_date_for_full_payment': earliest_date_str,
        'spending_changes_needed': best_plan.spending_changes_str,
        'best_plan': best_plan,
    }
