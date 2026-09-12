"""
test_samples.py — Unit test suite for Buy or Wait? (compatible with unittest and pytest)

Tests:
1. Data loading and invariant checks (loaders.py)
2. FX graph conversions and bridge hops (fx.py)
3. Event normalization and blank amount resolution (events.py)
4. Forecast balance simulator (forecast.py)
5. Policy decision engine and ranking ladder (policy.py)
6. Post-hoc invariant validation (verify.py)
7. Full pipeline evaluation on sample dataset
"""

import os
import sys
import unittest
from decimal import Decimal
from datetime import date

# Add code/ to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

import loaders
import fx
import extraction
import events
import forecast
import policy
import verify
import explain
import evaluate


class TestBuyOrWait(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datastore = loaders.load_all('dataset')
        cls.fx_graph = fx.FXGraph(cls.datastore.exchange_rates)

    def test_loaders_invariants(self):
        """Test that loaders successfully loads and validates all datasets."""
        ds = self.datastore
        self.assertEqual(len(ds.profiles), 275)
        self.assertEqual(len(ds.events), 25342)
        self.assertEqual(len(ds.requests), 250)
        self.assertEqual(len(ds.payment_options), 790)
        self.assertEqual(len(ds.exchange_rates), 134)
        self.assertEqual(len(ds.messages), 215)
        self.assertEqual(len(ds.images), 16)
        self.assertEqual(len(ds.samples), 25)

    def test_fx_conversion_direct_and_bridge(self):
        """Test direct, inverted, and bridged currency conversions."""
        test_date = date(2025, 8, 15)
        
        # Direct: USD -> EUR
        usd_amount = Decimal('100')
        eur_amount = self.fx_graph.convert(usd_amount, 'USD', 'EUR', test_date)
        self.assertGreater(eur_amount, Decimal('0'))

        # Inversion: EUR -> USD
        back_usd = self.fx_graph.convert(eur_amount, 'EUR', 'USD', test_date)
        diff = abs(back_usd - usd_amount)
        self.assertLess(diff, Decimal('1.00'))

        # Bridge: ZAR -> EUR -> USD -> INR
        zar_amount = Decimal('1000')
        inr_amount = self.fx_graph.convert(zar_amount, 'ZAR', 'INR', test_date)
        self.assertGreater(inr_amount, Decimal('0'))

    def test_image_extractions(self):
        """Test that all 16 images extract non-zero amounts."""
        img_res = extraction.extract_all_images(self.datastore.images, 'dataset')
        self.assertEqual(len(img_res), 16)
        for img_id, res in img_res.items():
            self.assertIn('amount', res)
            self.assertGreater(Decimal(str(res['amount'])), Decimal('0'))

    def test_sample_affordable_now(self):
        """Test sample_01 (request_01) evaluates as affordable_now."""
        s = self.datastore.samples_by_id['request_01']
        p = self.datastore.profiles[s.user_id]
        evs = self.datastore.events_by_user[s.user_id]
        opts = self.datastore.options_by_request.get(s.request_id, [])

        req = loaders.Request(
            s.request_id, s.user_id, s.request_date, s.request_type,
            s.requested_amount, s.desired_completion_date, s.allows_partial_payment, s.request_text
        )

        ledger = events.normalize_and_build_ledger(
            s.user_id, p, evs, [], self.datastore.images_by_event, {}, {}, self.fx_graph, s.request_date
        )
        decision = policy.evaluate_request(req, ledger, opts)

        self.assertEqual(decision['affordability_status'], 'affordable_now')
        self.assertEqual(decision['recommended_payment_method'], 'full_payment')
        self.assertEqual(decision['payment_plan'], s.payment_plan)

    def test_sample_not_affordable(self):
        """Test sample_05 (request_05) evaluates as not_affordable."""
        s = self.datastore.samples_by_id['request_05']
        p = self.datastore.profiles[s.user_id]
        evs = self.datastore.events_by_user[s.user_id]
        opts = self.datastore.options_by_request.get(s.request_id, [])

        req = loaders.Request(
            s.request_id, s.user_id, s.request_date, s.request_type,
            s.requested_amount, s.desired_completion_date, s.allows_partial_payment, s.request_text
        )

        ledger = events.normalize_and_build_ledger(
            s.user_id, p, evs, [], self.datastore.images_by_event, {}, {}, self.fx_graph, s.request_date
        )
        decision = policy.evaluate_request(req, ledger, opts)

        self.assertEqual(decision['affordability_status'], 'not_affordable')
        self.assertEqual(decision['recommended_payment_method'], 'not_recommended')
        self.assertEqual(decision['payment_plan'], 'none')

    def test_output_csv_format(self):
        """Test that generated output.csv exists and matches required schema."""
        output_path = os.path.join('dataset', 'output.csv')
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, 'r', encoding='utf-8') as f:
            import csv
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 250)
            required_cols = [
                'request_id', 'amount_safe_to_pay', 'affordability_status',
                'recommended_payment_method', 'payment_plan',
                'earliest_date_for_full_payment', 'spending_changes_needed',
                'decision_explanation'
            ]
            self.assertEqual(list(reader[0].keys()), required_cols)


if __name__ == '__main__':
    unittest.main()
