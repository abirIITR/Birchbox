"""
test_data_and_models.py
Unit tests for data loader, pattern subproblem generator, and assortment constraints.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import load_data_from_directory, AssortmentProblemData
from src.pattern_generator import PatternGenerator

class TestBirchboxAssortment(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.data_dir = os.path.join(base_dir, "data")
        cls.data = load_data_from_directory(cls.data_dir)

    def test_data_loading(self):
        self.assertGreater(len(self.data.products), 0, "Products should not be empty")
        self.assertGreater(len(self.data.subscribers), 0, "Subscribers should not be empty")
        self.assertGreater(len(self.data.attributes), 0, "Attributes should not be empty")
        self.assertGreaterEqual(self.data.tau_u, self.data.tau_l)
        self.assertGreaterEqual(self.data.gamma_u, self.data.gamma_l)

    def test_pattern_generator_single_pattern(self):
        generator = PatternGenerator(self.data)
        first_sub = list(self.data.subscribers.keys())[0]
        pattern = generator.generate_pattern_for_subscriber(first_sub)
        
        self.assertIsNotNone(pattern, "Should generate a feasible pattern for subscriber")
        self.assertTrue(self.data.gamma_l <= len(pattern) <= self.data.gamma_u, 
                        f"Pattern length {len(pattern)} must be between {self.data.gamma_l} and {self.data.gamma_u}")

        # Check must-receive requirements
        must_recv = self.data.must_receive_p.get(first_sub, set())
        for p in must_recv:
            self.assertIn(p, pattern, f"Required product {p} must be present in pattern")

        # Check cannot-receive requirements
        cannot_recv = self.data.cannot_receive_p.get(first_sub, set())
        for p in cannot_recv:
            self.assertNotIn(p, pattern, f"Ineligible product {p} must not be present in pattern")

        # Check attribute rules
        for attr_name, rule in self.data.attributes.items():
            tot = sum(self.data.products[p].attributes.get(attr_name, 0.0) for p in pattern)
            self.assertGreaterEqual(tot, rule.alpha_l - 1e-4, f"Attribute {attr_name} lower bound violated")
            self.assertLessEqual(tot, rule.alpha_u + 1e-4, f"Attribute {attr_name} upper bound violated")

        # Check co-occurrence
        for p1, p2 in self.data.cooccur_pairs:
            in1 = p1 in pattern
            in2 = p2 in pattern
            self.assertEqual(in1, in2, f"Cooccurring pair ({p1}, {p2}) must appear together or not at all")

        # Check conflict
        for p1, p2 in self.data.conflict_pairs:
            self.assertFalse(p1 in pattern and p2 in pattern, f"Conflict pair ({p1}, {p2}) cannot both appear in pattern")

if __name__ == "__main__":
    unittest.main()
