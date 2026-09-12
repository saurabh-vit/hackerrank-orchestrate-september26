"""
main.py — Main executable pipeline for Buy or Wait?

Full end-to-end execution:
1. Loads all CSV datasets and validates invariants (§2.5).
2. Extracts image amounts and message deltas.
3. Evaluates all 250 evaluation requests in dataset/requests.csv.
4. Generates predictions, invariant-validates them, and writes dataset/output.csv.
5. Generates evaluation/usage_report.md.
"""

import os
import sys
import csv
import time
from decimal import Decimal
from typing import Dict, List, Any, Optional

# Add code/ to path
sys.path.insert(0, os.path.dirname(__file__))

import loaders
import fx
import extraction
import events
import forecast
import policy
import verify
import explain
import evaluate


def run_pipeline(dataset_dir: str = 'dataset', output_csv_path: Optional[str] = None):
    """Run full evaluation pipeline."""
    start_time = time.time()
    print("=" * 70)
    print("      BUY OR WAIT? — AI FINANCIAL DECISION AGENT (HACKERRANK)        ")
    print("=" * 70)

    # 1. Load data
    print("\n[1/5] Loading datasets and validating schema invariants...")
    ds = loaders.load_all(dataset_dir)
    fx_graph = fx.FXGraph(ds.exchange_rates)

    # 2. Extraction
    print("\n[2/5] Running multimodal extraction (images + messages)...")
    img_res = extraction.extract_all_images(ds.images, dataset_dir)
    msg_res = extraction.extract_all_messages(ds.messages)

    # 3. Evaluate requests
    print(f"\n[3/5] Evaluating {len(ds.requests)} financial requests...")
    output_rows = []
    status_counts = {'affordable_now': 0, 'affordable_with_plan': 0, 'affordable_later': 0, 'not_affordable': 0}
    method_counts = {'full_payment': 0, 'partial_payment': 0, 'installments': 0, 'wait': 0, 'not_recommended': 0}

    for req in ds.requests:
        profile = ds.profiles[req.user_id]
        user_events = ds.events_by_user.get(req.user_id, [])
        user_messages = ds.messages_by_user.get(req.user_id, [])
        user_images = ds.images_by_event
        options = ds.options_by_request.get(req.request_id, [])

        # Build ledger
        ledger = events.normalize_and_build_ledger(
            req.user_id, profile, user_events, user_messages, user_images,
            img_res, fx_graph, req.request_date
        )

        # Policy decision
        decision = policy.evaluate_request(req, ledger, options)

        # Post-hoc invariant check
        validated = verify.verify_output_row(req, ledger, options, decision)

        # Explanation
        exp = explain.generate_explanation(req, ledger, validated)
        validated['decision_explanation'] = exp

        # Format row
        # Ensure Decimal formatting is clean
        safe_amt = validated['amount_safe_to_pay']
        if safe_amt == safe_amt.to_integral():
            safe_amt_str = f"{int(safe_amt)}"
        else:
            safe_amt_str = f"{safe_amt:.2f}".rstrip('0').rstrip('.') if f"{safe_amt:.2f}".endswith('.00') else f"{safe_amt:.2f}"

        row_dict = {
            'request_id': req.request_id,
            'amount_safe_to_pay': safe_amt_str,
            'affordability_status': validated['affordability_status'],
            'recommended_payment_method': validated['recommended_payment_method'],
            'payment_plan': validated['payment_plan'],
            'earliest_date_for_full_payment': validated['earliest_date_for_full_payment'],
            'spending_changes_needed': validated['spending_changes_needed'],
            'decision_explanation': validated['decision_explanation'],
        }

        status_counts[validated['affordability_status']] += 1
        method_counts[validated['recommended_payment_method']] += 1
        output_rows.append(row_dict)

    # 4. Write output.csv
    print(f"\n[4/5] Writing output.csv...")
    if output_csv_path is None:
        output_csv_path = os.path.join(dataset_dir, 'output.csv')

    fieldnames = [
        'request_id',
        'amount_safe_to_pay',
        'affordability_status',
        'recommended_payment_method',
        'payment_plan',
        'earliest_date_for_full_payment',
        'spending_changes_needed',
        'decision_explanation',
    ]

    with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    # Also write a copy to root if output_csv is in dataset/
    root_output = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output.csv')
    if root_output != output_csv_path:
        with open(root_output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(output_rows)

    print(f"  -> Written {len(output_rows)} rows to {output_csv_path}")

    # 5. Generate usage report
    print(f"\n[5/5] Generating evaluation/usage_report.md...")
    evaluate.generate_usage_report('evaluation')

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"PIPELINE COMPLETED SUCCESSFULLY IN {elapsed:.2f}s")
    print("=" * 70)
    print("Status Distribution:")
    for st, count in status_counts.items():
        print(f"  - {st:25s}: {count:4d} ({count/len(output_rows)*100:.1f}%)")
    print("Method Distribution:")
    for mt, count in method_counts.items():
        print(f"  - {mt:25s}: {count:4d} ({count/len(output_rows)*100:.1f}%)")
    print("=" * 70)


if __name__ == '__main__':
    run_pipeline()
