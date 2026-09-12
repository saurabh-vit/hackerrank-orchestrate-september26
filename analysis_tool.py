import os
import sys
from decimal import Decimal
from datetime import date

sys.path.insert(0, 'code')
import loaders
import fx
import extraction
import events
import policy
import verify
import explain

def run_analysis():
    dataset_dir = 'dataset'
    ds = loaders.load_all(dataset_dir)
    fx_graph = fx.FXGraph(ds.exchange_rates)
    img_res = extraction.extract_all_images(ds.images, dataset_dir)
    msg_res = extraction.extract_all_messages(ds.messages)
    
    samples = loaders.load_samples(dataset_dir)
    
    results = []
    for s in samples:
        p = ds.profiles[s.user_id]
        user_events = ds.events_by_user.get(s.user_id, [])
        user_messages = ds.messages_by_user.get(s.user_id, [])
        user_images = ds.images_by_event
        options = ds.options_by_request.get(s.request_id, [])
        
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
            req.user_id, p, user_events, user_messages, user_images,
            img_res, msg_res, fx_graph, req.request_date, ds.global_reference_date
        )
        
        decision = policy.evaluate_request(req, ledger, options)
        validated = verify.verify_output_row(req, ledger, options, decision)
        exp = explain.generate_explanation(req, ledger, validated)
        validated['decision_explanation'] = exp
        
        # Normalize amounts for comparison
        def norm_amt(val):
            if val is None: return "None"
            if isinstance(val, Decimal):
                return f"{val:.2f}".rstrip('0').rstrip('.')
            return str(val)

        actual = {
            'amount_safe_to_pay': norm_amt(validated['amount_safe_to_pay']),
            'affordability_status': validated['affordability_status'],
            'recommended_payment_method': validated['recommended_payment_method'],
            'payment_plan': validated['payment_plan'],
            'earliest_date_for_full_payment': validated['earliest_date_for_full_payment'],
            'spending_changes_needed': validated['spending_changes_needed'],
        }
        
        expected = {
            'amount_safe_to_pay': norm_amt(s.amount_safe_to_pay),
            'affordability_status': s.affordability_status,
            'recommended_payment_method': s.recommended_payment_method,
            'payment_plan': s.payment_plan,
            'earliest_date_for_full_payment': s.earliest_date_for_full_payment,
            'spending_changes_needed': s.spending_changes_needed,
        }
        
        # Full row match ignores amount_safe_to_pay
        match_all_but_amt = True
        for k in expected:
            if k == 'amount_safe_to_pay': continue
            if expected[k] != actual[k]:
                match_all_but_amt = False
                break
        
        results.append({
            'request_id': s.request_id,
            'expected': expected,
            'actual': actual,
            'match': match_all_but_amt,
            'ledger': ledger,
            'req': req,
            'profile': p
        })
        
    return results

if __name__ == '__main__':
    results = run_analysis()
    failures = [r for r in results if not r['match']]
    print(f"Total Failures: {len(failures)}")
    for r in results:
        status = "PASS" if r['match'] else "FAIL"
        print(f"{r['request_id']}: {status}")
        if not r['match']:
            for k in r['expected']:
                print(f"  {k}: Exp={r['expected'][k]}, Act={r['actual'][k]}")
