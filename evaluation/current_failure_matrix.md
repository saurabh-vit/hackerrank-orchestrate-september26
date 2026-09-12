# Current Failure Matrix

| request_id | full_row_match | amount_safe_to_pay | affordability_status | recommended_payment_method | payment_plan | earliest_date_for_full_payment | spending_changes_needed |
|---|---|---|---|---|---|---|---|
| request_01 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| request_02 | PASS | FAIL (Exp: 17229139.2, Act: 17964019.75250244140625) | PASS | PASS | PASS | PASS | PASS |
| request_03 | PASS | FAIL (Exp: 873000, Act: 952824.9874114990234375) | PASS | PASS | PASS | PASS | PASS |
| request_04 | PASS | FAIL (Exp: 8401800, Act: 10750161.51523590087890625) | PASS | PASS | PASS | PASS | PASS |
| request_05 | PASS | FAIL (Exp: 737, Act: 0) | PASS | PASS | PASS | PASS | PASS |
| request_06 | FAIL | FAIL (Exp: 603.3, Act: 529.505710601806640625) | FAIL (Exp: affordable_with_plan, Act: affordable_later) | FAIL (Exp: full_payment, Act: wait) | FAIL (Exp: 2026-01-03:620.40, Act: 2026-01-15:620.40) | PASS | FAIL (Exp: stop:event_476, Act: none) |
| request_07 | PASS | FAIL (Exp: 87170.56, Act: 87341.61586761474609375) | PASS | PASS | PASS | PASS | PASS |
| request_08 | FAIL | FAIL (Exp: 284.57, Act: 289.32760448455810546875) | FAIL (Exp: affordable_later, Act: not_affordable) | FAIL (Exp: wait, Act: not_recommended) | FAIL (Exp: 2025-04-15:996.60, Act: none) | FAIL (Exp: 2025-04-15, Act: ) | PASS |
| request_09 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| request_10 | FAIL | FAIL (Exp: 12700, Act: 266700) | PASS | PASS | PASS | FAIL (Exp: , Act: 2024-12-06) | PASS |
| request_11 | FAIL | FAIL (Exp: 12510645, Act: 12419740.0760650634765625) | FAIL (Exp: affordable_with_plan, Act: affordable_later) | FAIL (Exp: full_payment, Act: wait) | FAIL (Exp: 2025-05-03:13110000, Act: 2025-05-15:13110000) | FAIL (Exp: 2025-07-15, Act: 2025-05-15) | FAIL (Exp: reduce_to:event_989:665950, Act: none) |
| request_12 | FAIL | FAIL (Exp: 65164, Act: 58217.6544189453125) | PASS | PASS | PASS | FAIL (Exp: 2026-04-05, Act: ) | FAIL (Exp: none, Act: stop:event_1016|reduce_to:event_1017:511.28|reduce_to:event_1054:1072.50) |
| request_13 | FAIL | FAIL (Exp: 433.4, Act: 941.6) | FAIL (Exp: affordable_later, Act: affordable_now) | FAIL (Exp: wait, Act: full_payment) | FAIL (Exp: 2024-05-15:941.60, Act: 2024-03-07:941.60) | FAIL (Exp: 2024-05-15, Act: 2024-03-07) | PASS |
| request_14 | PASS | FAIL (Exp: 597.74, Act: 0) | PASS | PASS | PASS | PASS | PASS |
| request_15 | PASS | FAIL (Exp: 83.05, Act: 6.677150726318359375) | PASS | PASS | PASS | PASS | PASS |
| request_16 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| request_17 | PASS | FAIL (Exp: 243849.58, Act: 230115.143585205078125) | PASS | PASS | PASS | PASS | PASS |
| request_18 | PASS | FAIL (Exp: 462, Act: 559.047184658050537109375) | PASS | PASS | PASS | PASS | PASS |
| request_19 | FAIL | FAIL (Exp: 28820, Act: 30665.264682769775390625) | PASS | PASS | FAIL (Exp: 2024-09-04:28820|2024-09-15:10840, Act: 2024-09-04:30665.26|2024-09-15:8994.74) | PASS | PASS |
| request_20 | PASS | FAIL (Exp: 5400, Act: 8322.833251953125) | PASS | PASS | PASS | PASS | PASS |
| request_21 | FAIL | FAIL (Exp: 1543.35, Act: 1574.4) | FAIL (Exp: affordable_with_plan, Act: affordable_now) | PASS | PASS | FAIL (Exp: 2026-04-15, Act: 2026-04-03) | FAIL (Exp: stop:event_1815|reduce_to:event_1816:23.50, Act: none) |
| request_22 | PASS | FAIL (Exp: 475.46, Act: 467.063603878021240234375) | PASS | PASS | PASS | PASS | PASS |
| request_23 | PASS | FAIL (Exp: 9152, Act: 8824.1121826171875) | PASS | PASS | PASS | PASS | PASS |
| request_24 | PASS | FAIL (Exp: 13420, Act: 13397.09320068359375) | PASS | PASS | PASS | PASS | PASS |
| request_25 | PASS | FAIL (Exp: 1425000, Act: 333352.935791015625) | PASS | PASS | PASS | PASS | PASS |
