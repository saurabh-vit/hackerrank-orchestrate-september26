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
    failing_ids = ['request_06', 'request_08', 'request_10', 'request_11', 'request_12', 'request_13', 'request_19', 'request_21']
    
    for s in samples:
        if s.request_id not in failing_ids:
            continue
            
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
        
        print(f"--- {s.request_id} ---")
        print(f"Inputs:")
        print(f"  Balance: {ledger.balance_at_eval_date}")
        print(f"  Min Balance: {p.minimum_balance_to_keep}")
        print(f"  Req Amount: {req.requested_amount}")
        print(f"  Req Date: {req.request_date}")
        print(f"  Completion Date: {req.desired_completion_date}")
        
        print(f"Salary Streams: {[f'{ss.base_amount} on {ss.day_of_month}' for ss in ledger.salary_streams]}")
        print(f"Expense Streams: {[f'{rs.category}:{rs.base_amount} on {rs.day_of_month}' for rs in ledger.recurring_expense_streams]}")
        
        print(f"Actual Safe Amount: {validated['amount_safe_to_pay']}")
        print(f"Expected Safe Amount: {s.amount_safe_to_pay}")
        print(f"Actual Status: {validated['affordability_status']}")
        print(f"Expected Status: {s.affordability_status}")

if __name__ == '__main__':
    run_analysis()
