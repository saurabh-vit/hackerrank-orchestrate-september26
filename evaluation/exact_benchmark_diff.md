# EXACT BENCHMARK DIFFERENCE ANALYSIS

## All Requests

| request_id | Match | amount_safe_to_pay | affordability_status | recommended_payment_method | payment_plan | earliest_date_for_full_payment | spending_changes_needed |
|---|---|---|---|---|---|---|---|
| request_01 | YES | 25256 / 25256 | affordable_now / affordable_now | full_payment / full_payment | 2024-03-03:25256 / 2024-03-03:25256 | 2024-03-03 / 2024-03-03 | none / none |
| request_02 | NO | 17229139.2 / 18231198.84 | affordable_with_plan / affordable_with_plan | installments / installments | Match / Match | 2025-09-15 / 2025-09-15 | none / none |
| request_03 | NO | 873000 / 982082.02 | affordable_later / affordable_later | wait / wait | Match / Match | 2019-11-15 / 2019-11-15 | none / none |
| request_04 | NO | 8401800 / 10761903.35 | affordable_later / affordable_later | wait / wait | Match / Match | 2024-06-15 / 2024-06-15 | none / none |
| request_05 | NO | 737 / 0 | not_affordable / not_affordable | not_recommended / not_recommended | Match / Match | / | none / none |
| request_06 | NO | 603.3 / 528.8 | affordable_with_plan / affordable_later | full_payment / wait | 2026-01-03:620.40 / 2026-01-15:620.40 | 2026-01-15 / 2026-01-15 | stop:event_476 / none |
| request_07 | NO | 87170.56 / 86816.95 | affordable_with_plan / affordable_with_plan | installments / installments | Match / Match | 2024-10-23 / 2024-10-23 | none / none |
| request_08 | NO | 284.57 / 285.2 | affordable_later / not_affordable | wait / not_recommended | 2025-04-15:996.60 / none | 2025-04-15 / | none / none |
| request_09 | YES | 166.61 / 166.61 | affordable_now / affordable_now | full_payment / full_payment | 2026-07-04:166.61 / 2026-07-04:166.61 | 2026-07-04 / 2026-07-04 | none / none |
| request_10 | NO | 12700 / 266700 | not_affordable / not_affordable | not_recommended / not_recommended | Match / Match | / 2024-12-06 | none / none |
| request_11 | NO | 12510645 / 12361002.53 | affordable_with_plan / affordable_later | full_payment / wait | 2025-05-03:13110000 / 2025-05-15:13110000 | 2025-07-15 / 2025-05-15 | reduce_to:event_989:665950 / none |
| request_12 | NO | 65164 / 60340.16 | affordable_with_plan / affordable_with_plan | installments / installments | Match / Match | 2026-04-05 / | none / stop:event_1016\|reduce_to:event_1054:1072.50 |
| request_13 | NO | 433.4 / 941.6 | affordable_later / affordable_now | wait / full_payment | 2024-05-15:941.60 / 2024-03-07:941.60 | 2024-05-15 / 2024-03-07 | none / none |
| request_14 | NO | 597.74 / 0 | not_affordable / not_affordable | not_recommended / not_recommended | Match / Match | / | none / none |
| request_15 | NO | 83.05 / 7.07 | not_affordable / not_affordable | not_recommended / not_recommended | Match / Match | / | none / none |
| request_16 | YES | 122500 / 122500 | affordable_now / affordable_now | full_payment / full_payment | 2023-08-12:122500 / 2023-08-12:122500 | 2023-08-12 / 2023-08-12 | none / none |
| request_17 | NO | 243849.58 / 241691.77 | affordable_with_plan / affordable_with_plan | installments / installments | Match / Match | 2026-03-15 / 2026-03-15 | none / none |
| request_18 | NO | 462 / 557.34 | affordable_later / affordable_later | wait / wait | Match / Match | 2026-09-15 / 2026-09-15 | none / none |
| request_19 | NO | 28820 / 30415.14 | affordable_with_plan / affordable_with_plan | partial_payment / partial_payment | 2024-09-04:28820\|2024-09-15:10840 / 2024-09-04:30415.14\|2024-09-15:9244.86 | 2024-09-15 / 2024-09-15 | none / none |
| request_20 | NO | 5400 / 8703.12 | not_affordable / not_affordable | not_recommended / not_recommended | Match / Match | / | none / none |
| request_21 | NO | 1543.35 / 1574.4 | affordable_with_plan / affordable_now | full_payment / full_payment | 2026-04-03:1574.40 / 2026-04-03:1574.40 | 2026-04-15 / 2026-04-03 | stop:event_1815\|reduce_to:event_1816:23.50 / none |
| request_22 | NO | 475.46 / 467.83 | affordable_with_plan / affordable_with_plan | installments / installments | Match / Match | 2025-01-15 / 2025-01-15 | none / none |
| request_23 | NO | 9152 / 8452.46 | affordable_later / affordable_later | wait / wait | Match / Match | 2025-07-15 / 2025-07-15 | none / none |
| request_24 | NO | 13420 / 13336.78 | not_affordable / not_affordable | not_recommended / not_recommended | Match / Match | / | none / none |
| request_25 | NO | 1425000 / 419835.46 | not_affordable / not_affordable | not_recommended / not_recommended | Match / Match | / | none / none |

## Detailed Analysis of Failures (Top 8 by Severity)

### request_06
**FIRST DIVERGENCE**: `spending_changes_needed` (Expected `stop:event_476`, Actual `none`)
**UPSTREAM INPUTS**:
- Balance: 1942.4
- Min Balance: 800
- Req Amount: 620.4
- Req Date: 2026-01-03
- Completion Date: 2026-01-14
**CALCULATION**: `amount_safe_to_pay` was calculated as 528.80, which is less than 620.4, leading to `affordable_later`.
**EXPECTED BASIS**: Stopping `event_476` increases `amount_safe_to_pay` to 603.3, making it `affordable_with_plan`.
**CATEGORY**: I

### request_08
**FIRST DIVERGENCE**: `affordability_status` (Expected `affordable_later`, Actual `not_affordable`)
**UPSTREAM INPUTS**:
- Balance: 1536.57
- Min Balance: 800
- Req Amount: 996.6
- Req Date: 2025-02-07
- Completion Date: 2025-04-15
**CALCULATION**: Forecast determined no date within 90 days where the balance stays above 800 after paying 996.6.
**EXPECTED BASIS**: Benchmark identifies 2025-04-15 as a safe date.
**CATEGORY**: C

### request_10
**FIRST DIVERGENCE**: `amount_safe_to_pay` (Expected 12700, Actual 266700)
**UPSTREAM INPUTS**:
- Balance: 750155
- Min Balance: 225400
- Req Amount: 266700
- Req Date: 2024-12-06
- Completion Date: 2025-02-10
**CALCULATION**: `amount_safe_to_pay` calculated as 266700 based on high reconstructed balance.
**EXPECTED BASIS**: Expected balance at `request_date` is significantly lower.
**CATEGORY**: B

### request_11
**FIRST DIVERGENCE**: `spending_changes_needed` (Expected `reduce_to:event_989:665950`, Actual `none`)
**UPSTREAM INPUTS**:
- Balance: 63531795
- Min Balance: 34140600
- Req Amount: 13110000
- Req Date: 2025-05-03
- Completion Date: 2025-06-12
**CALCULATION**: No spending changes were identified to make the request affordable now.
**EXPECTED BASIS**: Reducing `event_989` makes the payment affordable.
**CATEGORY**: I

### request_12
**FIRST DIVERGENCE**: `spending_changes_needed` (Expected `none`, Actual `stop:event_1016\|reduce_to:event_1054:1072.50`)
**UPSTREAM INPUTS**:
- Balance: 193089.89
- Min Balance: 43200
- Req Amount: 65164
- Req Date: 2026-04-05
- Completion Date: 2026-06-20
**CALCULATION**: System identified unnecessary spending changes to maintain minimum balance.
**EXPECTED BASIS**: Request is affordable without changes.
**CATEGORY**: I

### request_13
**FIRST DIVERGENCE**: `affordability_status` (Expected `affordable_later`, Actual `affordable_now`)
**UPSTREAM INPUTS**:
- Balance: 2789.52
- Min Balance: 1300
- Req Amount: 941.6
- Req Date: 2024-03-07
- Completion Date: 2024-05-15
**CALCULATION**: System believes user can afford full payment today (Balance 2789.52 > 1300 + 941.6).
**EXPECTED BASIS**: Expected balance is lower or future expenses are higher.
**CATEGORY**: B

### request_19
**FIRST DIVERGENCE**: `amount_safe_to_pay` (Expected 28820, Actual 30415.14)
**UPSTREAM INPUTS**:
- Balance: 199545
- Min Balance: 92800
- Req Amount: 39660
- Req Date: 2024-09-04
- Completion Date: 2024-10-04
**CALCULATION**: `amount_safe_to_pay` computed as 30415.14.
**EXPECTED BASIS**: Benchmark expected 28820.
**CATEGORY**: D

### request_21
**FIRST DIVERGENCE**: `spending_changes_needed` (Expected `stop:event_1815\|reduce_to:event_1816:23.50`, Actual `none`)
**UPSTREAM INPUTS**:
- Balance: 3911.35
- Min Balance: 1800
- Req Amount: 1574.4
- Req Date: 2026-04-03
- Completion Date: 2026-04-14
**CALCULATION**: System believes request is affordable now without changes.
**EXPECTED BASIS**: Spending changes are required to maintain min balance safely over forecast.
**CATEGORY**: I
