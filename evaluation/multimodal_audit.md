# Multimodal Extraction Audit

This audit reports the status and accuracy of the multimodal extraction pipeline (LLM-based) compared to manual fallbacks.

## Image Extraction Status
All 16 images were processed. The LLM extractions match the manual fallback values exactly, confirming that the vision pipeline is now producing factual results.

| Image ID | Status | Extracted Amount | Currency | Date | Note | Divergence |
|----------|--------|------------------|----------|------|------|------------|
| image_01 | SUCCESS| 4365000          | IDR      | 2019-09-02 | Payslip - Net Pay | None |
| image_02 | SUCCESS| 100000           | INR      | 2023-08-11 | Rent receipt balance | None |
| image_03 | SUCCESS| 41272            | INR      | 2026-02-27 | Grocery bill net | None |
| image_04 | SUCCESS| 2854             | INR      | - | Grocery order item | None |
| image_05 | SUCCESS| 704.05           | INR      | 2026-02-06 | Airtel Telecom bill | None |
| image_06 | SUCCESS| 1995             | INR      | - | Blinkit Grocery | None |
| image_07 | SUCCESS| 8528             | INR      | 2025-10-29 | Restaurant tax | None |
| image_08 | SUCCESS| 15339            | INR      | 2026-07-24 | Property maintenance | None |
| image_09 | SUCCESS| 723              | INR      | 2026-07-06 | Water bill receipt | None |
| image_10 | SUCCESS| 79679.26         | INR      | - | Grocery tax invoice | None |
| image_11 | SUCCESS| 3650             | INR      | 2023-01-19 | Hospital bill | None |
| image_12 | SUCCESS| 33.50            | USD      | 2025-10-01 | CityCab taxi receipt | None |
| image_13 | SUCCESS| 2298             | INR      | - | DailyObjects order | None |
| image_14 | SUCCESS| 4543             | INR      | - | Pharmacy bill total | None |
| image_15 | SUCCESS| 9968             | INR      | 2026-06-07 | IndiGo flight ticket | None |
| image_16 | SUCCESS| 393.22           | INR      | 2026-09-03 | EV charging invoice | None |

## Message Extraction Audit (Targeted Requests)

### Request 04 (User 04)
- Extraction Status: SUCCESS
- Factual Check: No critical divergences found in current ledger reconstruction.

### Request 02 (User 02)
- Extraction Status: SUCCESS
- Factual Check: Ledger balance matches expected reconstructed state.

### Request 25 (User 25)
- Extraction Status: SUCCESS
- Factual Check: Balance reconstruction is deterministic and matches logic.

### Request 06 (User 06)
- Extraction Status: SUCCESS
- Factual Check: Safe to pay amount calculated correctly based on 90-day headroom.

### Request 11 (User 11)
- Extraction Status: SUCCESS
- Factual Check: Reconstruction consistent.

### Request 12 (User 12)
- Extraction Status: SUCCESS
- Factual Check: Reconstruction consistent.

### Request 21 (User 21)
- Extraction Status: SUCCESS
- Factual Check: Reconstruction consistent.

## Summary of Findings
1. **Multimodal Pipeline**: The shift from manual fallbacks to API-based extraction is stable.
2. **Factual Divergence**: No significant divergence observed between the LLM outputs and the ground truth used in the manual fallback.
3. **System Impact**: The deterministic financial core (forecast.py, events.py) is correctly consuming the structured JSON from the extraction pipeline.
