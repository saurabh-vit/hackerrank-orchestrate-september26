import os
import sys
from decimal import Decimal
from datetime import date
import csv

sys.path.insert(0, os.path.dirname(__file__))

import loaders
import fx
import extraction
import events

def reconstruct_balance_detailed(request_id):
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

    # We want to see exactly how normalize_and_build_ledger works
    # but we'll do it manually here for the report

    home_curr = p.home_currency
    cleaned_events = []
    for raw_e in evs:
        e = loaders.FinancialEvent(
            event_id=raw_e.event_id,
            user_id=raw_e.user_id,
            event_type=raw_e.event_type,
            description=raw_e.description,
            category=raw_e.category,
            direction=raw_e.direction,
            amount=raw_e.amount,
            currency=raw_e.currency or home_curr,
            event_date=raw_e.event_date,
            settlement_date=raw_e.settlement_date,
            status=raw_e.status,
            linked_event_id=raw_e.linked_event_id,
            flexibility=raw_e.flexibility,
            minimum_allowed_amount=raw_e.minimum_allowed_amount,
        )
        if e.amount is None and e.event_id in imgs:
            img_ref = imgs[e.event_id]
            extr = img_res.get(img_ref.image_id, {})
            if 'amount' in extr and extr['amount']:
                e.amount = Decimal(str(extr['amount']))
                if 'currency' in extr and extr['currency']:
                    e.currency = extr['currency']

        eff_date = e.settlement_date or e.event_date
        if e.amount is not None:
            e.amount_home = fx_graph.convert(e.amount, e.currency, home_curr, eff_date)
        else:
            e.amount_home = Decimal('0')
        cleaned_events.append(e)

    # Process messages for cancellations
    cancelled_ids = set()
    for msg in msgs:
        if msg.related_event_id and msg.related_event_id in {e.event_id: e for e in cleaned_events}:
            # Simplified cancellation check
            if 'cancel' in msg.message_text.lower() or 'batal' in msg.message_text.lower():
                cancelled_ids.add(msg.related_event_id)

    # Linked to settled
    linked_to_settled = set()
    for e in cleaned_events:
        if e.status == 'settled' and e.linked_event_id:
            linked_to_settled.add(e.linked_event_id)

    # Filter events for balance reconstruction
    # The code now uses global_reference_date as the anchor.
    ref_date = ds.global_reference_date
    eval_date = sample.request_date

    print(f"--- BALANCE LEDGER: {request_id} ---")
    print(f"User: {sample.user_id} | Home Currency: {home_curr}")
    print(f"Request Date: {eval_date}")
    print(f"Global Ref Date: {ref_date}")
    print(f"Opening Balance (from profile): {p.current_available_balance}")
    print("-" * 40)

    current_bal = p.current_available_balance

    # Sort all settled events to show the flow
    settled_events = [e for e in cleaned_events if e.status == 'settled']
    settled_events.sort(key=lambda x: (x.settlement_date or x.event_date))

    for e in settled_events:
        eff_date = e.settlement_date or e.event_date
        if eff_date is None: continue

        included = False
        reason = "Not in adjustment window"

        if eval_date >= ref_date:
            if ref_date < eff_date <= eval_date:
                included = True
                reason = "Post-ref, pre-eval"
        else:
            if eval_date < eff_date <= ref_date:
                included = True
                reason = "Post-eval, pre-ref"

        # Overrides
        if e.event_id in cancelled_ids:
            included = False
            reason = "Cancelled by message"
        if e.event_id in linked_to_settled:
            included = False
            reason = "Linked to later settlement"

        change = Decimal('0')
        if included:
            if e.direction == 'credit':
                change = e.amount_home
            elif e.direction == 'debit':
                change = -e.amount_home

            # If eval_date < ref_date, we are subtracting these from the final balance to go back in time
            if eval_date < ref_date:
                current_bal -= change
            else:
                current_bal += change

        print(f"{eff_date} | {e.event_id:10} | {e.status:10} | {e.direction:7} | {e.amount_home:12.2f} | Incl: {str(included):5} | {reason:20} | Bal: {current_bal:.2f}")

    print("-" * 40)
    print(f"FINAL RECONSTRUCTED BALANCE: {current_bal:.2f}")
    print(f"EXPECTED safe_to_pay (benchmark): {sample.amount_safe_to_pay}")

if __name__ == '__main__':
    for rid in ['request_10', 'request_13']:
        reconstruct_balance_detailed(rid)
