import os
import sys
from decimal import Decimal
sys.path.insert(0, 'code')
import loaders

ds = loaders.load_all('dataset')
evs = ds.events_by_user['user_10']
credits = Decimal('0')
for e in evs:
    if e.status == 'settled' and e.amount and e.direction == 'credit':
        credits += e.amount
print(f"Total credits: {credits}")
