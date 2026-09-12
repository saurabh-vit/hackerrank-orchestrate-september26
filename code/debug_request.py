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

def debug_request(request_id='request_06'):
    ds = loaders.load_all('dataset')
    fx_graph = fx.FXGraph(ds.exchange_rates)
    img_res = extraction.extract_all_images(ds.images, 'dataset')
    msg_res = extraction.extract_all_messages(ds.messages)

    sample = ds.samples_by_id[request_id]
    p = ds.profiles[sample.user_id]
    evs = ds.events_by_user[sample.user_id]
    msgs = ds.messages_by_user.get(sample.user_id, [])
    imgs = ds.images_by_event

    ledger = events.normalize_and_build_ledger(
        sample.user_id, p, evs, msgs, imgs, img_res, msg_res, fx_graph, sample.request_date, ds.global_reference_date
    )

    print(f"Request: {request_id}")
    print(f"User: {sample.user_id}")
    print(f"Request Date: {sample.request_date}")
    print(f"Balance at Eval Date: {ledger.balance_at_eval_date}")
    print(f"Min Balance to Keep: {p.minimum_balance_to_keep}")

    forecast_res = forecast.compute_forecast(ledger, sample.request_date, sample.requested_amount)
    print(f"Amount Safe to Pay: {forecast_res.amount_safe_to_pay}")
    print(f"Min Headroom: {forecast_res.min_headroom_today}")

    print("\nDaily Balances (first 10 days):")
    for d, bal, hr in forecast_res.daily_balances[:10]:
        print(f"{d}: Bal={bal}, Headroom={hr}")

    print("\nRecurring Expense Streams:")
    for rs in ledger.recurring_expense_streams:
        print(f"ID: {rs.stream_id}, Cat: {rs.category}, Amt: {rs.base_amount}, Interval: {rs.interval_days}, Day: {rs.day_of_month}")

if __name__ == '__main__':
    debug_request()
