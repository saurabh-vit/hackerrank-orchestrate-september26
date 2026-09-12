# Benchmark Failure Matrix Report

- **Total Benchmark Samples**: 25
- **Full Row PASS**: 17 / 25 (68.0%)
- **Full Row FAIL**: 8 / 25 (32.0%)

## Field Error Matrix

| Request ID | Full Row | Amount Safe | Affordability Status | Payment Method | Payment Plan | Earliest Date | Spending Changes |
|---|---|---|---|---|---|---|---|
| `request_01` | **PASS** | PASS | PASS | PASS | PASS | PASS | PASS |
| `request_02` | **PASS** | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_03` | **PASS** | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_04` | **PASS** | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_05` | **PASS** | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_06` | **FAIL** | FAIL | FAIL | FAIL | FAIL | PASS | FAIL |
| `request_07` | **PASS** | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_08` | **FAIL** | FAIL | FAIL | FAIL | FAIL | FAIL | PASS |
| `request_09` | **PASS** | PASS | PASS | PASS | PASS | PASS | PASS |
| `request_10` | **FAIL** | FAIL | PASS | PASS | PASS | FAIL | PASS |
| `request_11` | **FAIL** | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL |
| `request_12` | **FAIL** | FAIL | PASS | PASS | PASS | FAIL | FAIL |
| `request_13` | **FAIL** | FAIL | FAIL | FAIL | FAIL | FAIL | PASS |
| `request_14` | **PASS** | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_15` | **PASS** | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_16` | **PASS** | PASS | PASS | PASS | PASS | PASS | PASS |
| `request_17` | **PASS** | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_18` | **PASS** | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_19` | **FAIL** | FAIL | PASS | PASS | FAIL | PASS | PASS |
| `request_20` | **PASS** | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_21` | **FAIL** | FAIL | FAIL | PASS | PASS | FAIL | FAIL |
| `request_22` | **PASS** | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_23` | **PASS** | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_24` | **PASS** | FAIL | PASS | PASS | PASS | PASS | PASS |
| `request_25` | **PASS** | FAIL | PASS | PASS | PASS | PASS | PASS |

---

## Detailed Analysis of Non-Passing Rows

### `request_06` (User: `user_06`)
- **Request Text**: *"I want to put EUR 620.40 into an investment. I need to complete it by 14 January 2026. Is it safer to invest now, invest a smaller amount, or wait?"*
- **Request Specs**: Date `2026-01-03`, Amount `620.4`, Type `investment`, Deadline `2026-01-14`, Partial `False`

**EXPECTED:**
- `amount_safe_to_pay`: `603.3`
- `affordability_status`: `affordable_with_plan`
- `recommended_payment_method`: `full_payment`
- `payment_plan`: `2026-01-03:620.40`
- `earliest_date_for_full_payment`: `2026-01-15`
- `spending_changes_needed`: `stop:event_476`

**ACTUAL:**
- `amount_safe_to_pay`: `529.506`
- `affordability_status`: `affordable_later`
- `recommended_payment_method`: `wait`
- `payment_plan`: `2026-01-15:620.40`
- `earliest_date_for_full_payment`: `2026-01-15`
- `spending_changes_needed`: `none`

### `request_08` (User: `user_08`)
- **Request Text**: *"The repair I need is priced at EUR 996.60. Can I cover the full repair now and still manage my essential expenses?"*
- **Request Specs**: Date `2025-02-07`, Amount `996.6`, Type `emergency_expense`, Deadline `2025-04-15`, Partial `False`

**EXPECTED:**
- `amount_safe_to_pay`: `284.57`
- `affordability_status`: `affordable_later`
- `recommended_payment_method`: `wait`
- `payment_plan`: `2025-04-15:996.60`
- `earliest_date_for_full_payment`: `2025-04-15`
- `spending_changes_needed`: `none`

**ACTUAL:**
- `amount_safe_to_pay`: `289.328`
- `affordability_status`: `not_affordable`
- `recommended_payment_method`: `not_recommended`
- `payment_plan`: `none`
- `earliest_date_for_full_payment`: ``
- `spending_changes_needed`: `none`

### `request_10` (User: `user_10`)
- **Request Text**: *"The price of the laptop is INR 266,700. I need to complete it by 10 February 2025. How much of the laptop price can I safely cover today?"*
- **Request Specs**: Date `2024-12-06`, Amount `266700`, Type `purchase`, Deadline `2025-02-10`, Partial `True`

**EXPECTED:**
- `amount_safe_to_pay`: `12700`
- `affordability_status`: `not_affordable`
- `recommended_payment_method`: `not_recommended`
- `payment_plan`: `none`
- `earliest_date_for_full_payment`: ``
- `spending_changes_needed`: `none`

**ACTUAL:**
- `amount_safe_to_pay`: `266700`
- `affordability_status`: `not_affordable`
- `recommended_payment_method`: `not_recommended`
- `payment_plan`: `none`
- `earliest_date_for_full_payment`: `2024-12-06`
- `spending_changes_needed`: `none`

### `request_11` (User: `user_11`)
- **Request Text**: *"Does paying for the trip now leave enough for the rest of the month? I need to decide by 12 June 2025. I'm planning a family trip that costs IDR 13,110,000."*
- **Request Specs**: Date `2025-05-03`, Amount `13110000`, Type `travel`, Deadline `2025-06-12`, Partial `False`

**EXPECTED:**
- `amount_safe_to_pay`: `12510645`
- `affordability_status`: `affordable_with_plan`
- `recommended_payment_method`: `full_payment`
- `payment_plan`: `2025-05-03:13110000`
- `earliest_date_for_full_payment`: `2025-07-15`
- `spending_changes_needed`: `reduce_to:event_989:665950`

**ACTUAL:**
- `amount_safe_to_pay`: `12419746.584`
- `affordability_status`: `affordable_later`
- `recommended_payment_method`: `wait`
- `payment_plan`: `2025-05-15:13110000`
- `earliest_date_for_full_payment`: `2025-05-15`
- `spending_changes_needed`: `none`

### `request_12` (User: `user_12`)
- **Request Text**: *"The professional course costs ZAR 65,164. Can I pay for the course before enrolment closes?"*
- **Request Specs**: Date `2026-04-05`, Amount `65164`, Type `education`, Deadline `2026-06-20`, Partial `False`

**EXPECTED:**
- `amount_safe_to_pay`: `65164`
- `affordability_status`: `affordable_with_plan`
- `recommended_payment_method`: `installments`
- `payment_plan`: `2026-04-19:22590.19|2026-05-20:22590.19|2026-06-20:22590.19`
- `earliest_date_for_full_payment`: `2026-04-05`
- `spending_changes_needed`: `none`

**ACTUAL:**
- `amount_safe_to_pay`: `58217.670`
- `affordability_status`: `affordable_with_plan`
- `recommended_payment_method`: `installments`
- `payment_plan`: `2026-04-19:22590.19|2026-05-20:22590.19|2026-06-20:22590.19`
- `earliest_date_for_full_payment`: ``
- `spending_changes_needed`: `stop:event_1016|reduce_to:event_1017:511.28|reduce_to:event_1054:1072.50`

### `request_13` (User: `user_13`)
- **Request Text**: *"Can I complete this family transfer and still keep my minimum balance? I want to send EUR 941.60 to my family."*
- **Request Specs**: Date `2024-03-07`, Amount `941.6`, Type `family_transfer`, Deadline `2024-05-15`, Partial `True`

**EXPECTED:**
- `amount_safe_to_pay`: `433.4`
- `affordability_status`: `affordable_later`
- `recommended_payment_method`: `wait`
- `payment_plan`: `2024-05-15:941.60`
- `earliest_date_for_full_payment`: `2024-05-15`
- `spending_changes_needed`: `none`

**ACTUAL:**
- `amount_safe_to_pay`: `941.6`
- `affordability_status`: `affordable_now`
- `recommended_payment_method`: `full_payment`
- `payment_plan`: `2024-03-07:941.60`
- `earliest_date_for_full_payment`: `2024-03-07`
- `spending_changes_needed`: `none`

### `request_19` (User: `user_19`)
- **Request Text**: *"Can I buy the laptop now without making next month's bills tight? I need to decide by 4 October 2024. I've been quoted INR 39,660 for the laptop."*
- **Request Specs**: Date `2024-09-04`, Amount `39660`, Type `purchase`, Deadline `2024-10-04`, Partial `True`

**EXPECTED:**
- `amount_safe_to_pay`: `28820`
- `affordability_status`: `affordable_with_plan`
- `recommended_payment_method`: `partial_payment`
- `payment_plan`: `2024-09-04:28820|2024-09-15:10840`
- `earliest_date_for_full_payment`: `2024-09-15`
- `spending_changes_needed`: `none`

**ACTUAL:**
- `amount_safe_to_pay`: `30665.28`
- `affordability_status`: `affordable_with_plan`
- `recommended_payment_method`: `partial_payment`
- `payment_plan`: `2024-09-04:30665.28|2024-09-15:8994.72`
- `earliest_date_for_full_payment`: `2024-09-15`
- `spending_changes_needed`: `none`

### `request_21` (User: `user_21`)
- **Request Text**: *"Is it safe to cover the full course fee by the deadline? Enrolment for the course comes to USD 1,574.40."*
- **Request Specs**: Date `2026-04-03`, Amount `1574.4`, Type `education`, Deadline `2026-04-14`, Partial `False`

**EXPECTED:**
- `amount_safe_to_pay`: `1543.35`
- `affordability_status`: `affordable_with_plan`
- `recommended_payment_method`: `full_payment`
- `payment_plan`: `2026-04-03:1574.40`
- `earliest_date_for_full_payment`: `2026-04-15`
- `spending_changes_needed`: `stop:event_1815|reduce_to:event_1816:23.50`

**ACTUAL:**
- `amount_safe_to_pay`: `1574.4`
- `affordability_status`: `affordable_now`
- `recommended_payment_method`: `full_payment`
- `payment_plan`: `2026-04-03:1574.40`
- `earliest_date_for_full_payment`: `2026-04-03`
- `spending_changes_needed`: `none`
