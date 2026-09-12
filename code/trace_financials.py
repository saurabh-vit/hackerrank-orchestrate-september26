import os
import sys
from decimal import Decimal
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))

import loaders
import fx
import extraction
import events
import forecast
import policy

def trace_financials(request_id):
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
    opts = ds.options_by_request.get(sample.request_id, [])

    req = loaders.Request(
        request_id=sample.request_id,
        user_id=sample.user_id,
        request_date=sample.request_date,
        request_type=sample.request_type,
        requested_amount=sample.requested_amount,
        desired_completion_date=sample.desired_completion_date,
        allows_partial_payment=sample.allows_partial_payment,
        request_text=sample.request_text,
    )

    ledger = events.normalize_and_build_ledger(
        sample.user_id, p, evs, msgs, imgs, img_res, msg_res, fx_graph, sample.request_date, ds.global_reference_date
    )

    print(f"--- TRACE: {request_id} ---")
    print(f"User: {sample.user_id} | Req Date: {sample.request_date}")
    print(f"Balance at Eval Date: {ledger.balance_at_eval_date}")
    print(f"Min Balance: {p.minimum_balance_to_keep}")

    # Check for salary
    for ss in ledger.salary_streams:
        print(f"Salary Stream: {ss.base_amount} on day {ss.day_of_month} of month")

    # Check for recurring expenses
    for rs in ledger.recurring_expense_streams:
        print(f"Expense Stream: {rs.category} | {rs.base_amount} | Int: {rs.interval_days} | Day: {rs.day_of_month}")

    # Forecast
    res = forecast.compute_forecast(ledger, sample.request_date, sample.requested_amount)
    print(f"Safe Amount: {res.amount_safe_to_pay}")
    print(f"Earliest Date: {res.earliest_date_for_full_payment}")

    # Daily balances for the first few days
    for d, bal, hr in res.daily_balances[:15]:
        print(f"{d}: {bal} (HR: {hr})")

if __name__ == '__main__':
    for rid in ['request_06', 'request_08', 'request_10', 'request_11', 'request_12', 'request_13', 'request_19', 'request_21']:
        trace_financials(rid)
