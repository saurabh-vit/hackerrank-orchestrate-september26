"""
debug_request.py — Deep dive debugger for a single financial request.
Provides a fully traceable path from raw data to final decision.
"""

import os
import sys
from decimal import Decimal
from datetime import date, timedelta
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(__file__))

import loaders
import fx
import extraction
import events
import forecast
import policy
import verify
import explain

def debug_request(request_id: str, dataset_dir: str = 'dataset'):
    # 1. Load data
    ds = loaders.load_all(dataset_dir)
    fx_graph = fx.FXGraph(ds.exchange_rates)
    img_res = extraction.extract_all_images(ds.images, dataset_dir)
    msg_res = extraction.extract_all_messages(ds.messages)

    # Find request in requests or samples
    req = next((r for r in ds.requests if r.request_id == request_id), None)
    if not req:
        sample = next((s for s in ds.samples if s.request_id == request_id), None)
        if sample:
            req = loaders.Request(
                request_id=sample.request_id,
                user_id=sample.user_id,
                request_date=sample.request_date,
                request_type=sample.request_type,
                requested_amount=sample.requested_amount,
                desired_completion_date=sample.desired_completion_date,
                allows_partial_payment=sample.allows_partial_payment,
                request_text=sample.request_text,
            )

    if not req:
        print(f"Error: Request {request_id} not found in requests or samples.")
        return

    profile = ds.profiles[req.user_id]
    user_events = ds.events_by_user.get(req.user_id, [])
    user_messages = ds.messages_by_user.get(req.user_id, [])
    user_images = ds.images_by_event
    options = ds.options_by_request.get(req.request_id, [])

    print(f"\n{'='*80}")
    print(f" DEBUG TRACE FOR REQUEST: {request_id}")
    print(f"{'='*80}")

    print("\nREQUEST")
    print("-" * 10)
    print(f"Amount: {req.requested_amount} {profile.home_currency}   Date: {req.request_date}   Deadline: {req.desired_completion_date}")
    print(f"Type: {req.request_type}   Partial Allowed: {req.allows_partial_payment}")
    print(f"Text: {req.request_text}")

    print("\nUSER PROFILE")
    print("-" * 15)
    print(f"Balance: {profile.current_available_balance}   Min Keep: {profile.minimum_balance_to_keep}   Currency: {profile.home_currency}")
    print(f"Preferences: {profile.payment_methods_user_will_consider}")
    print(f"Max Installment Months: {profile.max_installment_months}")

    # Build Ledger
    ledger = events.normalize_and_build_ledger(
        req.user_id, profile, user_events, user_messages, user_images,
        img_res, msg_res, fx_graph, req.request_date
    )

    print("\nRELEVANT CASH FLOWS (In-Scope for this forecast)")
    print("-" * 50)

    # Collect all potential flow items
    flows = []
    for e in ledger.pending_debits:
        flows.append((e.settlement_date or e.event_date, f"PENDING DEBIT: {e.description}", -e.amount_home))
    for e in ledger.scheduled_events:
        dir_sign = 1 if e.direction == 'credit' else -1
        flows.append((e.settlement_date or e.event_date, f"SCHEDULED {e.direction.upper()}: {e.description}", dir_sign * e.amount_home))
    for s in ledger.salary_streams:
        flows.append(("STREAM", f"SALARY STREAM: {s.description}", s.base_amount))
    for rs in ledger.recurring_expense_streams:
        flows.append(("STREAM", f"EXPENSE STREAM: {rs.description} ({rs.flexibility})", -rs.base_amount))

    for f in sorted(flows, key=lambda x: str(x[0])):
        print(f"{str(f[0]):<12} {f[1]:<40} {f[2]:>15.2f}")

    # Add event ID trace for recurring streams
    print("\nRECURRING STREAM DETAILS")
    print("-" * 30)
    for rs in ledger.recurring_expense_streams:
        print(f"ID: {rs.representative_event_id:<12} Cat: {rs.category:<15} Flex: {rs.flexibility:<15} Amt: {rs.base_amount:>10.2f}")
    for ss in ledger.salary_streams:
        print(f"ID: {ss.representative_event_id:<12} Cat: {ss.category:<15} Amt: {ss.base_amount:>10.2f}")

    # Baseline Forecast
    print("\nBASELINE 90-DAY FORECAST (No candidate payment applied)")
    print("-" * 60)
    base_forecast = forecast.compute_forecast(ledger, req.request_date, req.requested_amount)

    timeline = forecast.simulate_balance_timeline(ledger, req.request_date, num_days=90)
    # Print only key dates: start, end, and dates where balance changes
    last_bal = None
    for d, bal, headroom in timeline:
        if bal != last_bal or d == req.request_date or d == timeline[-1][0]:
            print(f"{d.isoformat():<12} Balance: {bal:>12.2f}   Headroom: {headroom:>12.2f}")
            last_bal = bal

    print(f"\nSafe to pay today (Baseline): {base_forecast.amount_safe_to_pay:.2f}")
    print(f"Earliest safe full-payment date: {base_forecast.earliest_date_for_full_payment}")

    # Safety Tests for Payment Options
    print("\nPAYMENT OPTIONS CONSIDERED")
    print("-" * 30)
    for opt in options:
        is_eligible = (opt.payment_method in profile.payment_methods_user_will_consider)
        if opt.payment_method == 'installments':
            if profile.max_installment_months is not None and opt.number_of_payments > profile.max_installment_months:
                is_eligible = False

        # Test safety
        plan_payments = {}
        if opt.payment_method == 'full_payment':
            plan_payments = {req.request_date: req.requested_amount}
        elif opt.payment_method == 'installments':
            freq = opt.payment_frequency_days or 30
            cur_d = opt.first_payment_date
            for _ in range(opt.number_of_payments):
                plan_payments[cur_d] = plan_payments.get(cur_d, Decimal('0')) + opt.payment_amount
                cur_d += timedelta(days=freq)

        safe = forecast.is_plan_safe(ledger, req.request_date, plan_payments) if plan_payments else False

        print(f"{opt.payment_option_id:<10} {opt.payment_method:<18} Total={opt.total_payable_amount:>10.2f} Eligible={str(is_eligible):<5} Safe={str(safe):<5}")

    # Final Decision
    decision = policy.evaluate_request(req, ledger, options)
    validated = verify.verify_output_row(req, ledger, options, decision)

    print("\nFINAL DECISION")
    print("-" * 20)
    print(f"affordability_status: {validated['affordability_status']}")
    print(f"recommended_payment_method: {validated['recommended_payment_method']}")
    print(f"payment_plan: {validated['payment_plan']}")
    print(f"earliest_date_for_full_payment: {validated['earliest_date_for_full_payment']}")
    print(f"spending_changes_needed: {validated['spending_changes_needed']}")
    print(f"amount_safe_to_pay: {validated['amount_safe_to_pay']}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python code/debug_request.py <request_id>")
    else:
        debug_request(sys.argv[1])
