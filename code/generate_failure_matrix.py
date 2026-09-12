import os
import sys
from decimal import Decimal

# Ensure code/ is in python path
sys.path.insert(0, os.path.dirname(__file__))

import evaluate

def generate_matrix(dataset_dir='dataset', output_path='evaluation/current_failure_matrix.md'):
    os.makedirs('evaluation', exist_ok=True)

    res = evaluate.evaluate_samples(dataset_dir)
    results = res['results']

    # Header
    matrix = "| request_id | full_row_match | amount_safe_to_pay | affordability_status | recommended_payment_method | payment_plan | earliest_date_for_full_payment | spending_changes_needed |\n"
    matrix += "|---|---|---|---|---|---|---|---|\n"

    for r in results:
        rid = r['request_id']
        full_match = "PASS" if r['is_full_match'] else "FAIL"

        target = r['target']
        actual = r['actual']

        # amount_safe_to_pay
        diff_safe = abs(Decimal(str(actual['amount_safe_to_pay'])) - target.amount_safe_to_pay)
        safe_status = "PASS" if diff_safe < Decimal('1.00') else f"FAIL (Exp: {target.amount_safe_to_pay}, Act: {actual['amount_safe_to_pay']})"

        # affordability_status
        status_status = "PASS" if actual['affordability_status'] == target.affordability_status else f"FAIL (Exp: {target.affordability_status}, Act: {actual['affordability_status']})"

        # recommended_payment_method
        method_status = "PASS" if actual['recommended_payment_method'] == target.recommended_payment_method else f"FAIL (Exp: {target.recommended_payment_method}, Act: {actual['recommended_payment_method']})"

        # payment_plan
        plan_status = "PASS" if actual['payment_plan'] == target.payment_plan else f"FAIL (Exp: {target.payment_plan}, Act: {actual['payment_plan']})"

        # earliest_date_for_full_payment
        date_status = "PASS" if actual['earliest_date_for_full_payment'] == target.earliest_date_for_full_payment else f"FAIL (Exp: {target.earliest_date_for_full_payment}, Act: {actual['earliest_date_for_full_payment']})"

        # spending_changes_needed
        changes_status = "PASS" if actual['spending_changes_needed'] == target.spending_changes_needed else f"FAIL (Exp: {target.spending_changes_needed}, Act: {actual['spending_changes_needed']})"

        matrix += f"| {rid} | {full_match} | {safe_status} | {status_status} | {method_status} | {plan_status} | {date_status} | {changes_status} |\n"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Current Failure Matrix\n\n")
        f.write(matrix)

    print(f"Failure matrix generated at {output_path}")

if __name__ == '__main__':
    generate_matrix()
