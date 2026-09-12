import os
import sys
from decimal import Decimal
from datetime import date
import csv

sys.path.insert(0, os.path.dirname(__file__))

import loaders
import fx
import extraction
import events
import forecast
import policy
import verify
import explain

def run_forensics():
    dataset_dir = 'dataset'
    ds = loaders.load_all(dataset_dir)
    fx_graph = fx.FXGraph(ds.exchange_rates)
    img_res = extraction.extract_all_images(ds.images, dataset_dir)
    msg_res = extraction.extract_all_messages(ds.messages)

    failures = []

    for s in ds.samples:
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
            s.user_id, p, evs, msgs, imgs, img_res, msg_res, fx_graph, s.request_date, ds.global_reference_date
        )
        decision = policy.evaluate_request(req, ledger, opts)
        validated = verify.verify_output_row(req, ledger, opts, decision)
        exp = explain.generate_explanation(req, ledger, validated)
        validated['decision_explanation'] = exp

        # Compare
        diffs = []
        # amount_safe_to_pay
        diff_safe = abs(Decimal(str(validated['amount_safe_to_pay'])) - s.amount_safe_to_pay)
        safe_match = diff_safe < Decimal('1.00')
        if not safe_match:
            diffs.append(('amount_safe_to_pay', s.amount_safe_to_pay, validated['amount_safe_to_pay']))

        status_match = (validated['affordability_status'] == s.affordability_status)
        if not status_match:
            diffs.append(('affordability_status', s.affordability_status, validated['affordability_status']))

        method_match = (validated['recommended_payment_method'] == s.recommended_payment_method)
        if not method_match:
            diffs.append(('recommended_payment_method', s.recommended_payment_method, validated['recommended_payment_method']))

        plan_match = (validated['payment_plan'] == s.payment_plan)
        if not plan_match:
            diffs.append(('payment_plan', s.payment_plan, validated['payment_plan']))

        earliest_match = (validated['earliest_date_for_full_payment'] == s.earliest_date_for_full_payment)
        if not earliest_match:
            diffs.append(('earliest_date_for_full_payment', s.earliest_date_for_full_payment, validated['earliest_date_for_full_payment']))

        changes_match = (validated['spending_changes_needed'] == s.spending_changes_needed)
        if not changes_match:
            diffs.append(('spending_changes_needed', s.spending_changes_needed, validated['spending_changes_needed']))

        # Full match according to evaluate.py (ignores amount_safe_to_pay)
        is_full_match = (status_match and method_match and plan_match and earliest_match and changes_match)

        if not is_full_match:
            failures.append({
                'request_id': s.request_id,
                'expected': s,
                'actual': validated,
                'diffs': diffs,
                'ledger': ledger,
                'req': req
            })

    return failures

def generate_report(failures):
    with open('evaluation/current_failures.md', 'w', encoding='utf-8') as f:
        f.write("# CURRENT BENCHMARK FAILURES\n\n")

        field_fail_counts = {
            'amount_safe_to_pay': 0,
            'affordability_status': 0,
            'recommended_payment_method': 0,
            'payment_plan': 0,
            'earliest_date_for_full_payment': 0,
            'spending_changes_needed': 0,
        }

        for i, fail in enumerate(failures, 1):
            s = fail['expected']
            a = fail['actual']
            rid = fail['request_id']

            f.write(f"## Request {i}: {rid}\n\n")

            f.write("### Expected\n\n")
            f.write(f"* amount_safe_to_pay: {s.amount_safe_to_pay}\n")
            f.write(f"* affordability_status: {s.affordability_status}\n")
            f.write(f"* recommended_payment_method: {s.recommended_payment_method}\n")
            f.write(f"* payment_plan: {s.payment_plan}\n")
            f.write(f"* earliest_date_for_full_payment: {s.earliest_date_for_full_payment}\n")
            f.write(f"* spending_changes_needed: {s.spending_changes_needed}\n\n")

            f.write("### Actual\n\n")
            f.write(f"* amount_safe_to_pay: {a['amount_safe_to_pay']}\n")
            f.write(f"* affordability_status: {a['affordability_status']}\n")
            f.write(f"* recommended_payment_method: {a['recommended_payment_method']}\n")
            f.write(f"* payment_plan: {a['payment_plan']}\n")
            f.write(f"* earliest_date_for_full_payment: {a['earliest_date_for_full_payment']}\n")
            f.write(f"* spending_changes_needed: {a['spending_changes_needed']}\n\n")

            f.write("### Field differences\n\n")
            for field, exp, act in fail['diffs']:
                f.write(f"* {field}: Expected {exp}, Actual {act}\n")
                field_fail_counts[field] += 1

            f.write("\n### Root cause\n\n")
            f.write("* [To be analyzed]\n\n")

            f.write("### Upstream calculation where divergence begins\n\n")
            f.write("* [To be analyzed]\n\n")
            f.write("---\n\n")

        f.write("## Failure frequency by field:\n\n")
        for field, count in field_fail_counts.items():
            f.write(f"{field}: {count}\n")

        f.write("\nRoot causes:\n\n")
        f.write("1. [Pending Analysis]\n\n")
        f.write("Highest-impact root cause:\n\n")
        f.write("[Pending Analysis]\n\n")
        f.write("Expected potential improvement:\n\n")
        f.write("[Pending Analysis]\n")

if __name__ == '__main__':
    fails = run_forensics()
    generate_report(fails)
    print(f"Report generated with {len(fails)} failures.")
