"""Quantity, unit and clause parsing.

These are the cases the original regex got wrong. Each test names the input
that motivated it rather than testing the implementation abstractly.
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


class ExtractQuantity(unittest.TestCase):
    def q(self, text):
        return nlp.extract_quantity(text)

    def test_digits(self):
        self.assertEqual(self.q("add 3 apples")["value"], 3)

    def test_number_words(self):
        self.assertEqual(self.q("add two apples")["value"], 2)
        self.assertEqual(self.q("add twelve eggs")["value"], 12)

    def test_decimal(self):
        self.assertEqual(self.q("add 1.5 kg rice")["value"], 1.5)

    def test_dozen(self):
        self.assertEqual(self.q("add a dozen eggs")["value"], 12)

    def test_dozen_with_multiplier(self):
        self.assertEqual(self.q("add 2 dozen eggs")["value"], 24)

    def test_half_dozen(self):
        self.assertEqual(self.q("add half a dozen eggs")["value"], 6)

    def test_half_with_unit(self):
        """"half kg" is 0.5, but a bare "half" is not a count - it is a size
        word ("half price"), so only the unit-adjacent form converts."""
        self.assertEqual(self.q("add half kg potatoes")["value"], 0.5)
        self.assertEqual(self.q("add half a kg of potatoes")["value"], 0.5)

    def test_default_is_one_and_not_explicit(self):
        result = self.q("add milk")
        self.assertEqual(result["value"], 1)
        self.assertFalse(result["explicit"])

    def test_explicit_flag_set_when_stated(self):
        self.assertTrue(self.q("add 2 milk")["explicit"])

    def test_negative(self):
        self.assertEqual(self.q("add -3 apples")["value"], -3)

    def test_price_is_not_a_quantity(self):
        """The bug: "apples under $3" parsed 3 as the quantity, so a search
        silently became "add 3 apples"."""
        self.assertFalse(self.q("find apples under $3")["explicit"])
        self.assertFalse(self.q("show me milk below 50 rupees")["explicit"])


class ExtractPrice(unittest.TestCase):
    def p(self, text):
        return nlp.extract_price_constraint(text)

    def test_under(self):
        self.assertEqual(self.p("apples under $3"), {"min": None, "max": 3.0})

    def test_under_synonyms(self):
        for phrase in ("below", "less than", "cheaper than", "within", "upto", "at most"):
            self.assertEqual(
                self.p("apples %s 3 dollars" % phrase)["max"], 3.0, phrase
            )

    def test_over(self):
        self.assertEqual(self.p("wine over $20"), {"min": 20.0, "max": None})

    def test_between(self):
        self.assertEqual(self.p("wine between $3 and $7"), {"min": 3.0, "max": 7.0})

    def test_absent(self):
        self.assertIsNone(self.p("add milk"))


class Conversions(unittest.TestCase):
    def test_metric_up_and_down(self):
        self.assertEqual(nlp.convert_quantity(500, "g", "kg"), 0.5)
        self.assertEqual(nlp.convert_quantity(2, "kg", "g"), 2000)
        self.assertEqual(nlp.convert_quantity(1500, "ml", "l"), 1.5)

    def test_imperial(self):
        self.assertAlmostEqual(nlp.convert_quantity(1, "lb", "oz"), 16, places=3)

    def test_incompatible_returns_none(self):
        """None is meaningful: it tells the caller to report a unit conflict
        rather than silently adding litres to kilograms."""
        self.assertIsNone(nlp.convert_quantity(1, "kg", "l"))
        self.assertIsNone(nlp.convert_quantity(1, "kg", "dozen"))


class Units(unittest.TestCase):
    def test_unknown_unit_flagged(self):
        entities = nlp.extract_entities("add 2 fluxes of milk")
        self.assertEqual(entities.get("unit_error"), nlp.INVALID_UNIT_UNKNOWN)

    def test_restricted_unit_flagged(self):
        """A volume unit on a dry good is physical nonsense. This is the one
        case the unit guard exists for - see unit_restrictions.json."""
        entities = nlp.extract_entities("add 2 liters of bread")
        self.assertEqual(entities.get("unit_error"), nlp.INVALID_UNIT_RESTRICTED)

    def test_ordinary_container_phrasing_is_allowed(self):
        """Regression: the old whitelist rejected every one of these."""
        for phrase in (
            "add 2 bottles of milk",
            "add a carton of eggs",
            "add 1 liter of olive oil",
            "add 5 kg flour",
            "add 1 bottle of detergent",
            "add 3 packs of pasta",
        ):
            self.assertIsNone(nlp.extract_entities(phrase).get("unit_error"), phrase)

    def test_valid_unit_passes(self):
        entities = nlp.extract_entities("add 2 liters of milk")
        self.assertIsNone(entities.get("unit_error"))
        self.assertEqual(entities["size"], "l")

    def test_spoken_unit_forms(self):
        """"two kilos of potatoes" failed because sizes.json only had "kg"."""
        for phrase, expected in (
            ("add two kilos of potatoes", "kg"),
            ("add 500 grammes of rice", "g"),
            ("add 2 litres of milk", "l"),
            ("add 3 packs of pasta", "pack"),
        ):
            self.assertEqual(nlp.extract_entities(phrase)["size"], expected, phrase)

    def test_packet_and_pack_are_one_unit(self):
        """"packet" and "pack" meant the same thing but the whitelist accepted
        only one or the other depending on the category."""
        self.assertEqual(nlp.extract_entities("add 3 packets of pasta")["size"], "pack")
        self.assertEqual(nlp.extract_entities("add 3 packs of pasta")["size"], "pack")


class Entities(unittest.TestCase):
    def test_item_brand_size(self):
        entities = nlp.extract_entities("add 2 liters of amul milk")
        self.assertEqual(entities["item"], "milk")
        self.assertEqual(entities["brand"], "amul")
        self.assertEqual(entities["size"], "l")
        self.assertEqual(entities["quantity"]["value"], 2)

    def test_category_resolved_from_item(self):
        self.assertEqual(nlp.extract_entities("add milk")["category"], "Dairy")

    def test_longest_match_wins(self):
        """"orange juice" must not be read as "orange"."""
        self.assertEqual(nlp.extract_entities("add orange juice")["item"], "orange juice")


class SplitClauses(unittest.TestCase):
    def test_and(self):
        self.assertEqual(nlp.split_clauses("add milk and bread"), ["add milk", "bread"])

    def test_comma_and_then(self):
        self.assertEqual(
            nlp.split_clauses("add milk, bread then eggs"),
            ["add milk", "bread", "eggs"],
        )

    def test_dangling_conjunction_stripped(self):
        """Produced ['add milk', 'bread', 'and 2 eggs'] before the fix."""
        self.assertEqual(
            nlp.split_clauses("add milk and bread, and 2 eggs"),
            ["add milk", "bread", "2 eggs"],
        )

    def test_multiword_item_is_not_split(self):
        """The " and " guard protects multi-word items. No entry in items.json
        currently contains " and ", so this asserts the mechanism rather than a
        specific product - "salt and pepper" is correctly two separate items on
        a shopping list."""
        self.assertEqual(
            nlp.split_clauses("add salt and pepper"), ["add salt", "pepper"]
        )

    def test_price_range_and_is_protected(self):
        """"between $3 and $7" is one constraint, not two clauses."""
        self.assertEqual(
            nlp.split_clauses("find wine between $3 and $7"),
            ["find wine between $3 and $7"],
        )

    def test_empty(self):
        self.assertEqual(nlp.split_clauses("   "), [])


if __name__ == "__main__":
    unittest.main()
