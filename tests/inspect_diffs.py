"""
Inspect differences in detail.
"""

import sys
sys.path.insert(0, 'code')
import loaders, fx, extraction, events, forecast, policy

ds = loaders.load_all('dataset')
fx_graph = fx.FXGraph(ds.exchange_rates)
img_res = extraction.extract_all_images(ds.images, 'dataset')

for req_id in ['request_03', 'request_04', 'request_05', 'request_08', 'request_11', 'request_13', 'request_17', 'request_18', 'request_19', 'request_21', 'request_22']:
    s = ds.samples_by_id[req_id]
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
    
    st = decision['affordability_status']
    m = decision['recommended_payment_method']
    ed = decision['earliest_date_for_full_payment']
    safe = decision['amount_safe_to_pay']
    
    print('========================================')
    print(f"{req_id} ({s.user_id}, {p.home_currency}):")
    print(f"  TARGET: status={s.affordability_status} method={s.recommended_payment_method} earliest={s.earliest_date_for_full_payment} safe={s.amount_safe_to_pay}")
    print(f"  ACTUAL: status={st} method={m} earliest={ed} safe={safe}")
    print(f"  Target explanation: {s.decision_explanation}")
    print(f"  Profile: bal={p.current_available_balance}, min_bal={p.minimum_balance_to_keep}, consider={p.payment_methods_user_will_consider}")
    if msgs:
        for msg in msgs:
            print(f"  Message ({msg.source_type}): {msg.message_text}")
    print(f"  Salary stream: {ledger.active_salary_stream}")
    print(f"  Recurring streams count: {len(ledger.recurring_streams)}")
    for rs in ledger.recurring_streams[:5]:
        print(f"     {rs.category} {rs.direction} {rs.base_amount} (dom={rs.day_of_month}, int={rs.interval_days}, anchor={rs.anchor_date})")
