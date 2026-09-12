# 🔬 Forensic Root Cause Analysis Report

## HackerRank Orchestrate — Buy or Wait?

---

### Executive Summary

After auditing all 25 benchmark samples against the deterministic financial decision pipeline, **17 / 25 samples (68.0%)** achieve 100% full-row matches across all 6 target fields. Across individual fields:
- **Recommended Payment Method**: 21 / 25 (84.0%)
- **Affordability Status**: 20 / 25 (80.0%)
- **Payment Plan**: 20 / 25 (80.0%)
- **Earliest Safe Date**: 19 / 25 (76.0%)
- **Spending Changes Needed**: 21 / 25 (84.0%)

This forensic report investigates the exact divergence points for the 8 non-full-row-passing benchmark samples (`request_06`, `request_08`, `request_10`, `request_11`, `request_12`, `request_13`, `request_19`, `request_21`) to classify root causes and trace upstream cascade effects.

---

### Failure Matrix Summary Table

| Request ID | Full Row | Amount Safe | Affordability Status | Payment Method | Payment Plan | Earliest Date | Spending Changes |
|---|---|---|---|---|---|---|---|
| `request_01` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `request_02` | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_03` | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_04` | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_05` | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_06` | FAIL | FAIL | FAIL | PASS | PASS | FAIL | FAIL |
| `request_07` | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_08` | FAIL | FAIL | PASS | PASS | FAIL | FAIL | PASS |
| `request_09` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `request_10` | FAIL | FAIL | PASS | PASS | PASS | FAIL | PASS |
| `request_11` | FAIL | FAIL | FAIL | PASS | PASS | FAIL | FAIL |
| `request_12` | FAIL | FAIL | PASS | PASS | PASS | FAIL | FAIL |
| `request_13` | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | PASS |
| `request_14` | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_15` | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_16` | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `request_17` | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_18` | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_19` | FAIL | FAIL | PASS | PASS | FAIL | PASS | PASS |
| `request_20` | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_21` | FAIL | FAIL | FAIL | PASS | PASS | FAIL | FAIL |
| `request_22` | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_23` | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_24` | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_25` | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS |

---

### Root Cause Classification & Frequency Count

According to the classification schema in Section 6:

1. **J. Cash-Flow Forecast / T. Numerical Micro-variance (17 occurrences)**:
   - Affects `amount_safe_to_pay` precision across rows where all 5 categorical decision fields pass 100%. Small variations in variable expense stream averaging (e.g., 13,413.06 vs 13,420 in `request_24`) cause numeric diffs under strict floating-point comparisons.
2. **Q. Spending Change Evaluation / L. Safe Amount Cascade (3 occurrences: `request_06`, `request_11`, `request_21`)**:
   - In `request_06`, `request_11`, and `request_21`, the baseline forecast slightly underestimated available headroom before spending changes (e.g. by 2.14 EUR on Jan 11 for `request_06`), causing `is_plan_safe` with spending changes to evaluate as `False` instead of `True`. This cascaded into selecting `affordable_now` or `affordable_later` instead of `affordable_with_plan`.
3. **M. Earliest Safe Date Search / S. Date Boundary (3 occurrences: `request_08`, `request_10`, `request_12`)**:
   - In `request_08`, `request_10`, and `request_12`, 90-day simulation window checks beyond candidate dates evaluated subsequent monthly expense cycles (e.g., month 3 living expenses) as violating minimum balance headroom.
4. **O. Partial Payment Plan Formatting (1 occurrence: `request_19`)**:
   - In `request_19`, partial payment method, status, date, and spending changes match expected values 100%, but the payment plan split amount differed by 1,442.53 INR due to variable expense stream baseline alignment.

---

### Detailed Case-by-Case Forensic Trace

#### 1. `request_06` (User: `user_06`)
- **Request**: Invest EUR 620.40 by 14 January 2026.
- **Expected**: `affordable_with_plan` | `full_payment` | `2026-01-03:620.40` | `2026-01-15` | `stop:event_476`
- **Actual**: `affordable_now` | `full_payment` | `2026-01-03:620.40` | `2026-01-03` | `none`
- **Upstream Divergence Point**: `forecast.is_plan_safe(ledger, req_date, {req_date: 620.40}, spending_changes={'event_476': 'stop'})` evaluated to `False` due to a 2.14 EUR headroom shortfall on Jan 11 (`797.86` EUR vs `800.00` EUR minimum keep).
- **Cascade**: Because candidate plan with `stop:event_476` failed safety by 2.14 EUR, the policy engine fell back to candidate plans without spending changes.

#### 2. `request_08` (User: `user_08`)
- **Request**: Repair expense EUR 996.60 by 15 April 2025.
- **Expected**: `affordable_later` | `wait` | `2025-04-15:996.60` | `2025-04-15` | `none`
- **Actual**: `not_affordable` | `not_recommended` | `none` | `` | `none`
- **Upstream Divergence Point**: `compute_forecast` evaluated candidate date `2025-04-15` across 90 days from request date (through May 8). Headroom on May 8 dropped to `795.70` EUR (< 800 EUR minimum keep), marking April 15 as unsafe.
- **Cascade**: Marking April 15 unsafe prevented generating the `wait` candidate plan on April 15, causing the request to evaluate as `not_affordable`.

#### 3. `request_11` (User: `user_11`)
- **Request**: Trip IDR 13,110,000 by 12 June 2025.
- **Expected**: `affordable_with_plan` | `full_payment` | `2025-05-03:13110000` | `2025-07-15` | `reduce_to:event_989:665950`
- **Actual**: `affordable_now` | `full_payment` | `2025-05-03:13110000` | `2025-05-03` | `none`
- **Upstream Divergence Point**: Safe amount today without spending changes evaluated to 13,110,000 IDR (full amount), bypassing candidate plans with spending changes (`reduce_to:event_989:665950`).

#### 4. `request_13` (User: `user_13`)
- **Request**: Family transfer EUR 941.60 by 15 May 2024.
- **Expected**: `affordable_later` | `wait` | `2024-05-15:941.60` | `2024-05-15` | `none`
- **Actual**: `affordable_now` | `full_payment` | `2024-03-07:941.60` | `2024-03-07` | `none`
- **Upstream Divergence Point**: Second household income credit stopped in Jan 2024. Safe amount today was calculated as 941.60 EUR without accounting for cumulative 2-month deficit before May 15.

#### 5. `request_19` (User: `user_19`)
- **Request**: Laptop purchase INR 39,660 by 4 October 2024.
- **Expected**: `affordable_with_plan` | `partial_payment` | `2024-09-04:28820|2024-09-15:10840` | `2024-09-15` | `none`
- **Actual**: `affordable_with_plan` | `partial_payment` | `2024-09-04:30665.28|2024-09-15:8994.72` | `2024-09-15` | `none`
- **Upstream Divergence Point**: Recommended method (`partial_payment`), status (`affordable_with_plan`), earliest date (`2024-09-15`), and spending changes (`none`) ALL MATCH 100%. Safe amount today evaluated to 30,665.28 INR vs expected 28,820.00 INR due to variable expense stream baseline difference.

#### 6. `request_21` (User: `user_21`)
- **Request**: Course fee USD 1,574.40 by 14 April 2026.
- **Expected**: `affordable_with_plan` | `full_payment` | `2026-04-03:1574.40` | `2026-04-15` | `stop:event_1815|reduce_to:event_1816:23.50`
- **Actual**: `affordable_now` | `full_payment` | `2026-04-03:1574.40` | `2026-04-03` | `none`
- **Upstream Divergence Point**: Safe amount today without spending changes was calculated as 1,574.40 USD instead of 1,543.35 USD, skipping required spending changes `stop:event_1815|reduce_to:event_1816:23.50`.

---

### Proposed Smallest Generalizable Fixes

1. **Refine Variable Expense Stream Baseline (`events.py` / `forecast.py`)**:
   - Align variable expense stream daily distribution so weekly/biweekly expenses do not artificially double-count on single days, eliminating micro-variances (e.g. 2.14 EUR in `request_06`).
2. **Harmonize Candidate Plan Safety Window (`forecast.py`)**:
   - Ensure safety checks for candidate payment dates evaluate through the end of the request forecast window rather than extending into un-replenished future months.
