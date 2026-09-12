# CURRENT BENCHMARK FAILURES

## Request 1: request_06

### Expected

* amount_safe_to_pay: 603.3
* affordability_status: affordable_with_plan
* recommended_payment_method: full_payment
* payment_plan: 2026-01-03:620.40
* earliest_date_for_full_payment: 2026-01-15
* spending_changes_needed: stop:event_476

### Actual

* amount_safe_to_pay: 528.795719146728515625
* affordability_status: affordable_later
* recommended_payment_method: wait
* payment_plan: 2026-01-15:620.40
* earliest_date_for_full_payment: 2026-01-15
* spending_changes_needed: none

### Field differences

* amount_safe_to_pay: Expected 603.3, Actual 528.795719146728515625
* affordability_status: Expected affordable_with_plan, Actual affordable_later
* recommended_payment_method: Expected full_payment, Actual wait
* payment_plan: Expected 2026-01-03:620.40, Actual 2026-01-15:620.40
* spending_changes_needed: Expected stop:event_476, Actual none

### Root cause

* [To be analyzed]

### Upstream calculation where divergence begins

* [To be analyzed]

---

## Request 2: request_08

### Expected

* amount_safe_to_pay: 284.57
* affordability_status: affordable_later
* recommended_payment_method: wait
* payment_plan: 2025-04-15:996.60
* earliest_date_for_full_payment: 2025-04-15
* spending_changes_needed: none

### Actual

* amount_safe_to_pay: 285.19702777862548828125
* affordability_status: not_affordable
* recommended_payment_method: not_recommended
* payment_plan: none
* earliest_date_for_full_payment: 
* spending_changes_needed: none

### Field differences

* affordability_status: Expected affordable_later, Actual not_affordable
* recommended_payment_method: Expected wait, Actual not_recommended
* payment_plan: Expected 2025-04-15:996.60, Actual none
* earliest_date_for_full_payment: Expected 2025-04-15, Actual 

### Root cause

* [To be analyzed]

### Upstream calculation where divergence begins

* [To be analyzed]

---

## Request 3: request_10

### Expected

* amount_safe_to_pay: 12700
* affordability_status: not_affordable
* recommended_payment_method: not_recommended
* payment_plan: none
* earliest_date_for_full_payment: 
* spending_changes_needed: none

### Actual

* amount_safe_to_pay: 266700
* affordability_status: not_affordable
* recommended_payment_method: not_recommended
* payment_plan: none
* earliest_date_for_full_payment: 2024-12-06
* spending_changes_needed: none

### Field differences

* amount_safe_to_pay: Expected 12700, Actual 266700
* earliest_date_for_full_payment: Expected , Actual 2024-12-06

### Root cause

* [To be analyzed]

### Upstream calculation where divergence begins

* [To be analyzed]

---

## Request 4: request_11

### Expected

* amount_safe_to_pay: 12510645
* affordability_status: affordable_with_plan
* recommended_payment_method: full_payment
* payment_plan: 2025-05-03:13110000
* earliest_date_for_full_payment: 2025-07-15
* spending_changes_needed: reduce_to:event_989:665950

### Actual

* amount_safe_to_pay: 12361002.5310516357421875
* affordability_status: affordable_later
* recommended_payment_method: wait
* payment_plan: 2025-05-15:13110000
* earliest_date_for_full_payment: 2025-05-15
* spending_changes_needed: none

### Field differences

* amount_safe_to_pay: Expected 12510645, Actual 12361002.5310516357421875
* affordability_status: Expected affordable_with_plan, Actual affordable_later
* recommended_payment_method: Expected full_payment, Actual wait
* payment_plan: Expected 2025-05-03:13110000, Actual 2025-05-15:13110000
* earliest_date_for_full_payment: Expected 2025-07-15, Actual 2025-05-15
* spending_changes_needed: Expected reduce_to:event_989:665950, Actual none

### Root cause

* [To be analyzed]

### Upstream calculation where divergence begins

* [To be analyzed]

---

## Request 5: request_12

### Expected

* amount_safe_to_pay: 65164
* affordability_status: affordable_with_plan
* recommended_payment_method: installments
* payment_plan: 2026-04-19:22590.19|2026-05-20:22590.19|2026-06-20:22590.19
* earliest_date_for_full_payment: 2026-04-05
* spending_changes_needed: none

### Actual

* amount_safe_to_pay: 60340.16271209716796875
* affordability_status: affordable_with_plan
* recommended_payment_method: installments
* payment_plan: 2026-04-19:22590.19|2026-05-20:22590.19|2026-06-20:22590.19
* earliest_date_for_full_payment: 
* spending_changes_needed: stop:event_1016|reduce_to:event_1054:1072.50

### Field differences

* amount_safe_to_pay: Expected 65164, Actual 60340.16271209716796875
* earliest_date_for_full_payment: Expected 2026-04-05, Actual 
* spending_changes_needed: Expected none, Actual stop:event_1016|reduce_to:event_1054:1072.50

### Root cause

* [To be analyzed]

### Upstream calculation where divergence begins

* [To be analyzed]

---

## Request 6: request_13

### Expected

* amount_safe_to_pay: 433.4
* affordability_status: affordable_later
* recommended_payment_method: wait
* payment_plan: 2024-05-15:941.60
* earliest_date_for_full_payment: 2024-05-15
* spending_changes_needed: none

### Actual

* amount_safe_to_pay: 941.6
* affordability_status: affordable_now
* recommended_payment_method: full_payment
* payment_plan: 2024-03-07:941.60
* earliest_date_for_full_payment: 2024-03-07
* spending_changes_needed: none

### Field differences

* amount_safe_to_pay: Expected 433.4, Actual 941.6
* affordability_status: Expected affordable_later, Actual affordable_now
* recommended_payment_method: Expected wait, Actual full_payment
* payment_plan: Expected 2024-05-15:941.60, Actual 2024-03-07:941.60
* earliest_date_for_full_payment: Expected 2024-05-15, Actual 2024-03-07

### Root cause

* [To be analyzed]

### Upstream calculation where divergence begins

* [To be analyzed]

---

## Request 7: request_19

### Expected

* amount_safe_to_pay: 28820
* affordability_status: affordable_with_plan
* recommended_payment_method: partial_payment
* payment_plan: 2024-09-04:28820|2024-09-15:10840
* earliest_date_for_full_payment: 2024-09-15
* spending_changes_needed: none

### Actual

* amount_safe_to_pay: 30415.14301300048828125
* affordability_status: affordable_with_plan
* recommended_payment_method: partial_payment
* payment_plan: 2024-09-04:30415.14|2024-09-15:9244.86
* earliest_date_for_full_payment: 2024-09-15
* spending_changes_needed: none

### Field differences

* amount_safe_to_pay: Expected 28820, Actual 30415.14301300048828125
* payment_plan: Expected 2024-09-04:28820|2024-09-15:10840, Actual 2024-09-04:30415.14|2024-09-15:9244.86

### Root cause

* [To be analyzed]

### Upstream calculation where divergence begins

* [To be analyzed]

---

## Request 8: request_21

### Expected

* amount_safe_to_pay: 1543.35
* affordability_status: affordable_with_plan
* recommended_payment_method: full_payment
* payment_plan: 2026-04-03:1574.40
* earliest_date_for_full_payment: 2026-04-15
* spending_changes_needed: stop:event_1815|reduce_to:event_1816:23.50

### Actual

* amount_safe_to_pay: 1574.4
* affordability_status: affordable_now
* recommended_payment_method: full_payment
* payment_plan: 2026-04-03:1574.40
* earliest_date_for_full_payment: 2026-04-03
* spending_changes_needed: none

### Field differences

* amount_safe_to_pay: Expected 1543.35, Actual 1574.4
* affordability_status: Expected affordable_with_plan, Actual affordable_now
* earliest_date_for_full_payment: Expected 2026-04-15, Actual 2026-04-03
* spending_changes_needed: Expected stop:event_1815|reduce_to:event_1816:23.50, Actual none

### Root cause

* [To be analyzed]

### Upstream calculation where divergence begins

* [To be analyzed]

---

## Failure frequency by field:

amount_safe_to_pay: 7
affordability_status: 5
recommended_payment_method: 4
payment_plan: 5
earliest_date_for_full_payment: 6
spending_changes_needed: 4

Root causes:

1. [Pending Analysis]

Highest-impact root cause:

[Pending Analysis]

Expected potential improvement:

[Pending Analysis]
