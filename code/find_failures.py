import csv
from decimal import Decimal

def analyze_failures():
    samples = []
    with open('dataset/sample_requests.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            samples.append(row)

    outputs = {}
    with open('dataset/output.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            outputs[row['request_id']] = row

    failures = []
    for s in samples:
        rid = s['request_id']
        o = outputs.get(rid)
        if not o:
            continue

        diffs = []
        # Compare amount_safe_to_pay (tolerance 1.0)
        try:
            s_amt = Decimal(s['amount_safe_to_pay'])
            o_amt = Decimal(o['amount_safe_to_pay'])
            if abs(s_amt - o_amt) >= Decimal('1.00'):
                diffs.append(('amount_safe_to_pay', s['amount_safe_to_pay'], o['amount_safe_to_pay']))
        except:
            diffs.append(('amount_safe_to_pay', s['amount_safe_to_pay'], o['amount_safe_to_pay']))

        if s['affordability_status'] != o['affordability_status']:
            diffs.append(('affordability_status', s['affordability_status'], o['affordability_status']))
        if s['recommended_payment_method'] != o['recommended_payment_method']:
            diffs.append(('recommended_payment_method', s['recommended_payment_method'], o['recommended_payment_method']))
        if s['payment_plan'] != o['payment_plan']:
            diffs.append(('payment_plan', s['payment_plan'], o['payment_plan']))
        if s['earliest_date_for_full_payment'] != o['earliest_date_for_full_payment']:
            diffs.append(('earliest_date_for_full_payment', s['earliest_date_for_full_payment'], o['earliest_date_for_full_payment']))
        if s['spending_changes_needed'] != o['spending_changes_needed']:
            diffs.append(('spending_changes_needed', s['spending_changes_needed'], o['spending_changes_needed']))

        if diffs:
            failures.append({'request_id': rid, 'diffs': diffs})

    return failures

if __name__ == '__main__':
    fails = analyze_failures()
    print(f"Total failures: {len(fails)}")
    for f in fails:
        print(f"Request {f['request_id']}: {len(f['diffs'])} diffs")
        for d in f['diffs']:
            print(f"  {d[0]}: Exp {d[1]}, Act {d[2]}")
