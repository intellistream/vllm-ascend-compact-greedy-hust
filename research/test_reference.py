"""CPU model correctness only; no serving performance qualification."""

import importlib.util
import itertools
from fractions import Fraction as F
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "reference", Path(__file__).with_name("reference.py")
)
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)


def oracle(rows, p):
    """Independent full-sort implementation of this reference's cutoff contract."""
    ranked = sorted((item for item in rows if item[1] > 0), key=lambda x: (-x[1], x[0]))
    threshold = sum(value for _, value in ranked) * p
    for length in range(1, len(ranked) + 1):
        if sum(value for _, value in ranked[:length]) >= threshold:
            return tuple(ranked[:length])
    raise ValueError("empty distribution")


class ReferenceTests(unittest.TestCase):
    def test_exhaustive_support_and_cdf(self):
        for masses in itertools.product(range(3), repeat=5):
            if not any(masses):
                continue
            rows = tuple(enumerate(masses))
            for ranks in (1, 2, 3, 7):
                shards = tuple(rows[rank::ranks] for rank in range(ranks))
                for p in (F(1, 2), F(9, 10), F(1)):
                    with self.subTest(masses=masses, ranks=ranks, p=p):
                        result = reference.bounded_nucleus(shards, p, (1, 2, 4))
                        expected = oracle(rows, p)
                        self.assertEqual(result["support"], expected)
                        self.assertLessEqual(result["candidate_rounds"], 3)
                        total = sum(mass for _, mass in expected)
                        cuts = [
                            F(sum(m for _, m in expected[:i]), total)
                            for i in range(len(expected) + 1)
                        ]
                        for i, (token, _) in enumerate(expected):
                            for u in (cuts[i], (cuts[i] + cuts[i + 1]) / 2):
                                self.assertEqual(
                                    reference.inverse_cdf(result["support"], u), token
                                )

    def test_flat_fixed_128_is_insufficient(self):
        rows = tuple((i, 1) for i in range(512))
        result = reference.bounded_nucleus((rows[::2], rows[1::2]), F(9, 10))
        self.assertTrue(result["fallback"])
        self.assertEqual(len(result["support"]), 461)
        self.assertEqual(result["support"], oracle(rows, F(9, 10)))
        self.assertLess(F(128, 512), F(9, 10))

    def test_peak_and_exact_threshold(self):
        shards = (((7, F(9, 10)), (1, F(1, 10)), (99, 0)), ())
        fast = reference.bounded_nucleus(shards, F(9, 10), (1,))
        self.assertFalse(fast["fallback"])
        self.assertEqual(fast["support"], ((7, F(9, 10)),))
        above = reference.bounded_nucleus(shards, F(9001, 10000), (1,))
        self.assertTrue(above["fallback"])
        self.assertEqual(len(above["support"]), 2)

    def test_invalid_inputs(self):
        for shards in (
            (),
            ((),),
            (((0, 0),),),
            (((0, -1),),),
            (((0, 1),), ((0, 2),)),
            (((0, float("nan")),),),
            (((0, float("inf")),),),
            (((0, 0.5),),),
            (((True, 1),),),
        ):
            with self.assertRaises(ValueError):
                reference.bounded_nucleus(shards, F(1, 2))
        for p in (0, -1, 2, 0.9, True):
            with self.assertRaises(ValueError):
                reference.bounded_nucleus((((0, 1),),), p)
        for budgets in ((), (0,), (2, 1), (1, 1), (True,), (1.0,)):
            with self.assertRaises(ValueError):
                reference.bounded_nucleus((((0, 1),),), F(1), budgets)
        for u in (-1, 1, 0.5, True):
            with self.assertRaises(ValueError):
                reference.inverse_cdf(((0, 1),), u)


if __name__ == "__main__":
    unittest.main()
