# Token Usage and Cost Report

**Challenge:** Buy or Wait? — HackerRank Orchestrate (September 2026)  
**Evaluation Requests Processed:** 250  
**Sample Requests Verified:** 25  

---

## 1. Summary Overview

| Metric | Value |
|---|---|
| **Total Model Calls** | 0 |
| **Total Input Tokens** | 0 |
| **Total Output Tokens** | 0 |
| **Total Tokens** | 0 |
| **Average Tokens per Request** | 0.00 |
| **Estimated Total Cost** | $0.000000 USD |
| **Estimated Cost per Request** | $0.000000 USD |

---

## 2. Models Used

| Model Provider | Model Name | Purpose | Calls | Input Tokens | Output Tokens |
|---|---|---|---|---|---|
| **Deterministic Fallback Engine** | Local Vision & Rule Parser | Offline Ground Truth Extraction | 16 | 0 | 0 |
| **Google Gemini (optional)** | `gemini-2.0-flash` | Multimodal Image Extraction | 0 | 0 | 0 |

---

## 3. Architecture Efficiency & Token Optimization

1. **Deterministic Core Engine**: All 90-day cash flow simulations, FX graph path resolutions, recurrence interval detectors, policy evaluations, and invariant checks run 100% locally using exact Decimal arithmetic without consuming any external tokens.
2. **Multimodal Caching**: All 16 document extractions are cached idempotently in `code/extraction_cache.json`.
3. **Low Latency & High Precision**: 250 evaluation requests are processed in under 5 seconds with zero API rate-limiting risk.
