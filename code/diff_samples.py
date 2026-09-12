"""
diff_samples.py — Field-by-field diff comparison for all 25 sample requests.
"""

import os
import sys
from decimal import Decimal
from typing import Dict, List, Any

sys.path.insert(0, os.path.dirname(__file__))

import loaders
import fx
import extraction
import events
import forecast
import policy
import verify
import explain


def run_diff(dataset_dir: str = 'dataset'):
    ds = loaders.load_all(dataset_dir)
    fx_graph = fx.FXGraph(ds.exchange_rates)
    img_res = extraction.extract_all_images(ds.images, dataset_dir)
    msg_res = extraction.extract_all_messages(ds.messages)

    print("=" * 80)
    print("           SAMPLE REQUESTS FIELD-BY-FIELD ACCURACY & DIFF TABLE           ")
    print("=" * 80)

    mismatch_count = 0
    full_match_count = 0

    for idx, s in enumerate(ds.samples, 1):
        p = ds.profiles[s.user_id]
        evs = ds.events_by_user[s.user_id]
        msgs = ds.messages_by_user.get(s.user_id, [])
        imgs = ds.images_by_event
        opts = ds.options_by_request.get(s.request_id, [])

        req = loaders.Request(
            request_id=s.request_id,
            user_id=s.user_id,
            request_date=s.request_date,
            request_type=s.request_type,
            requested_amount=s.requested_amount,
            desired_completion_date=s.desired_completion_date,
            allows_partial_payment=s.allows_partial_payment,
            request_text=s.request_text,
        )

        ledger = events.normalize_and_build_ledger(
            s.user_id, p, evs, msgs, imgs, img_res, msg_res, fx_graph, s.request_date
        )
        decision = policy.evaluate_request(req, ledger, opts)
        validated = verify.verify_output_row(req, ledger, opts, decision)
        exp = explain.generate_explanation(req, ledger, validated)
        validated['decision_explanation'] = exp

        # Compare fields
        safe_amt_act = validated['amount_safe_to_pay']
        safe_amt_tgt = s.amount_safe_to_pay
        diff_safe = abs(Decimal(str(safe_amt_act)) - safe_amt_tgt)
        safe_match = (diff_safe < Decimal('1.00'))

        status_match = (validated['affordability_status'] == s.affordability_status)
        method_match = (validated['recommended_payment_method'] == s.recommended_payment_method)
        plan_match = (validated['payment_plan'] == s.payment_plan)
        earliest_match = (validated['earliest_date_for_full_payment'] == s.earliest_date_for_full_payment)
        changes_match = (validated['spending_changes_needed'] == s.spending_changes_needed)

        is_full_match = (safe_match and status_match and method_match and plan_match and earliest_match and changes_match)

        if is_full_match:
            full_match_count += 1
            print(f"[{idx:02d}/25] {s.request_id} (User: {s.user_id}) -> [PERFECT MATCH]")
        else:
            mismatch_count += 1
            print(f"\n[{idx:02d}/25] {s.request_id} (User: {s.user_id}) -> [MISMATCH]")
            print(f"  Req: Amount={req.requested_amount} {p.home_currency} Date={req.request_date} Deadline={req.desired_completion_date} PartialAllowed={req.allows_partial_payment}")
            print(f"  User: AvailBalance={p.current_available_balance} MinKeep={p.minimum_balance_to_keep} MaxInst={p.max_installment_months} Prefs={p.payment_methods_user_will_consider}")

            # Print raw forecast trace for mismatched rows
            print("\n    RAW FORECAST TRACE")
            print("    " + "-" * 40)
            base_timeline = forecast.simulate_balance_timeline(ledger, s.request_date, num_days=90)
            last_bal = None
            for d, bal, headroom in base_timeline:
                if bal != last_bal or d == s.request_date or d == base_timeline[-1][0]:
                    print(f"    {d.isoformat():<12} Balance: {bal:>12.2f}   Headroom: {headroom:>12.2f}")
                    last_bal = bal

            # Field comparisons
            def fmt_field(name, actual, expected, match):
                status = "[OK]" if match else "[DIFF]"
                print(f"    {name:<30} {status}")
                if not match:
                    print(f"      Expected : {expected}")
                    print(f"      Actual   : {actual}")

            fmt_field('amount_safe_to_pay', str(safe_amt_act), str(safe_amt_tgt), safe_match)
            fmt_field('affordability_status', validated['affordability_status'], s.affordability_status, status_match)
            fmt_field('recommended_payment_method', validated['recommended_payment_method'], s.recommended_payment_method, method_match)
            fmt_field('payment_plan', validated['payment_plan'], s.payment_plan, plan_match)
            fmt_field('earliest_date_for_full_payment', validated['earliest_date_for_full_payment'], s.earliest_date_for_full_payment, earliest_match)
            fmt_field('spending_changes_needed', validated['spending_changes_needed'], s.spending_changes_needed, changes_match)

    print("\n" + "=" * 80)
    print(f"Summary: Full Matches = {full_match_count}/25 ({full_match_count/25*100:.1f}%), Mismatches = {mismatch_count}/25 ({mismatch_count/25*100:.1f}%)")
    print("=" * 80)


if __name__ == '__main__':
    run_diff()
