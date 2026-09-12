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
import forecast

def trace_request(request_id):
    dataset_dir = 'dataset'
    ds = loaders.load_all(dataset_dir)
    fx_graph = fx.FXGraph(ds.exchange_rates)
    img_res = extraction.extract_all_images(ds.images, dataset_dir)
    msg_res = extraction.extract_all_messages(ds.messages)

    sample = ds.samples_by_id[request_id]
    p = ds.profiles[sample.user_id]
    evs = ds.events_by_user[sample.user_id]
    msgs = ds.messages_by_user.get(sample.user_id, [])
    imgs = ds.images_by_event

    ledger = events.normalize_and_build_ledger(
        sample.user_id, p, evs, msgs, imgs, img_res, msg_res, fx_graph, sample.request_date, ds.global_reference_date
    )
    
    # Mock payment options
    payment_options = []
    for opt in ds.options_by_request.get(request_id, []):
        payment_options.append(opt)

    print(f"\n=== TRACE: {request_id} ===")
    print(f"Request Amount: {sample.requested_amount}")
    
    res = policy.evaluate_request(sample, ledger, payment_options)
    
    # Trace baseline
    base_forecast = forecast.compute_forecast(ledger, sample.request_date, sample.requested_amount)
    print(f"Baseline amount_safe_to_pay: {base_forecast.amount_safe_to_pay}")
    print(f"Baseline min headroom: {base_forecast.min_headroom_today}")
    
    # Trace candidates
    candidates = policy.get_possible_spending_changes(ledger)
    print(f"Flexible candidates found: {len(candidates)}")
    for c in candidates:
        print(f" - {c.event_id} ({c.category}): original={c.original_amount}, new={c.new_amount}")
    
    combinations = policy.generate_change_combinations(candidates)
    print(f"Total combinations to test: {len(combinations)}")
    
    # Check if a specific expected change is in the candidates
    # This is for our internal debugging
    return res

if __name__ == '__main__':
    for rid in ['request_06', 'request_11', 'request_12', 'request_21']:
        trace_request(rid)
