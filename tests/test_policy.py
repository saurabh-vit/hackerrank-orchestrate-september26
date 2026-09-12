"""
Test policy on sample requests.
"""

import sys
sys.path.insert(0, 'code')
import loaders, fx, extraction, events, forecast, policy

ds = loaders.load_all('dataset')
fx_graph = fx.FXGraph(ds.exchange_rates)
img_res = extraction.extract_all_images(ds.images, 'dataset')

matches = 0
total = len(ds.samples)

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
    
    ledger = events.normalize_and_build_ledger(s.user_id, p, evs, msgs, imgs, img_res, fx_graph, s.request_date)
    decision = policy.evaluate_request(req, ledger, opts)
    
    status_match = decision['affordability_status'] == s.affordability_status
    method_match = decision['recommended_payment_method'] == s.recommended_payment_method
    plan_match = decision['payment_plan'] == s.payment_plan
    earliest_match = decision['earliest_date_for_full_payment'] == s.earliest_date_for_full_payment
    changes_match = decision['spending_changes_needed'] == s.spending_changes_needed
    
    all_fields = status_match and method_match and plan_match and earliest_match and changes_match
    st = decision['affordability_status']
    m = decision['recommended_payment_method']
    pl = decision['payment_plan']
    ed = decision['earliest_date_for_full_payment']
    sc = decision['spending_changes_needed']
    
    if all_fields:
        matches += 1
        print(f"[MATCH] {s.request_id}: {st} / {m} / plan={pl}")
    else:
        print(f"[DIFF] {s.request_id}:")
        print(f"   TARGET: status={s.affordability_status}, method={s.recommended_payment_method}, plan={s.payment_plan}, earliest={s.earliest_date_for_full_payment}, changes={s.spending_changes_needed}")
        print(f"   ACTUAL: status={st}, method={m}, plan={pl}, earliest={ed}, changes={sc}")

print(f"\nAccuracy on sample set: {matches}/{total} ({matches/total*100:.1f}%)")
