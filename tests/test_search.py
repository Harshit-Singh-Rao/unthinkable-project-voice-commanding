"""Catalog search.

Search was classified correctly by the model and then answered with the
literal string "Searching for X (not fully implemented in backend yet)", which
reached real users. These tests cover the behaviour that replaced it.
"""
import os
import sys
import unittest

# Put server/ on the path so this file runs standalone as well as under
# `unittest discover` and pytest. Modules import as `nlp`, `state`, ... exactly
# as they do under gunicorn, whose working directory is /app/server.
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server"))

import nlp
import search


def find(text):
    return search.search(nlp.extract_entities(text), text)


class HardItemFilter(unittest.TestCase):
    def test_wrong_product_is_never_returned(self):
        """The regression that motivated the rewrite: with every constraint
        scored softly, "apples under $3" returned Tata Salt ($0.50) and Nestle
        Yogurt ($0.99), because matching the price outscored being the right
        product. Nobody asking for cheap apples wants salt."""
        results, meta = find("find apples under $3")
        self.assertTrue(results, "expected the apples to be offered")
        for product in results:
            self.assertEqual(product["item"], "apples", product.get("name"))

    def test_unstocked_item_returns_nothing(self):
        """A word we do not recognise at all must report nothing rather than
        substituting unrelated products. "find caviar" used to return Tata Salt
        because every slot came back empty and the whole catalog scored
        equally."""
        results, meta = find("find caviar")
        self.assertEqual(results, [])

    def test_constraint_only_query_still_searches(self):
        """The no-constraint guard must not break legitimate searches that
        name no product."""
        results, _ = find("show me anything under $2")
        self.assertTrue(results)
        for product in results:
            self.assertLessEqual(product["price"], 2.0)


class SoftConstraints(unittest.TestCase):
    def test_exact_match_is_flagged_exact(self):
        results, meta = find("find milk")
        self.assertTrue(results)
        self.assertTrue(meta["exact"])

    def test_over_constrained_degrades_to_closest(self):
        """"apples under $3" when the cheapest is $3.99 should show the $3.99
        apples flagged as approximate, not an empty panel."""
        results, meta = find("find apples under $3")
        self.assertTrue(results)
        self.assertFalse(meta["exact"])

    def test_price_range_filters(self):
        results, meta = find("find milk between $1 and $3")
        self.assertEqual(meta["price"], {"min": 1.0, "max": 3.0})
        if meta["exact"]:
            for product in results:
                self.assertGreaterEqual(product["price"], 1.0)
                self.assertLessEqual(product["price"], 3.0)

    def test_brand_filter(self):
        results, meta = find("find amul milk")
        self.assertEqual(meta["brand"], "amul")
        self.assertTrue(results)
        if meta["exact"]:
            self.assertEqual(results[0]["brand"].lower(), "amul")

    def test_results_are_capped(self):
        results, _ = find("find milk")
        self.assertLessEqual(len(results), search.MAX_RESULTS)

    def test_cheaper_ranks_first_among_equals(self):
        results, meta = find("find milk")
        if meta["exact"] and len(results) > 1:
            prices = [p["price"] for p in results]
            self.assertEqual(prices, sorted(prices))


class Describe(unittest.TestCase):
    def test_mentions_item_and_constraint(self):
        _, meta = find("find apples under $3")
        phrase = search.describe(meta)
        self.assertIn("apples", phrase)
        self.assertIn("under", phrase)

    def test_handles_empty_meta(self):
        self.assertTrue(search.describe({}))


if __name__ == "__main__":
    unittest.main()
