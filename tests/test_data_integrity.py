"""Data-integrity checks over the JSON dictionaries.

These are cheap and catch the class of bug that does not show up until a
specific phrase is spoken: a Hindi alias pointing at an item that was renamed,
a translation table that has drifted out of sync with the English source, a
category on an item that no longer exists. They fail loudly at test time
instead of silently mistranslating in production.
"""
import json
import os
import sys
import unittest

# Put server/ on the path so this file runs standalone as well as under
# `unittest discover` and pytest. Modules import as `nlp`, `state`, ... exactly
# as they do under gunicorn, whose working directory is /app/server.
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server"))

import i18n
from datastore import ITEMS, CATEGORIES, CATALOG, data_path


def _load(name):
    with open(data_path(name), encoding="utf-8") as handle:
        return json.load(handle)


class HindiAliases(unittest.TestCase):
    def setUp(self):
        self.aliases = _load("aliases_hi.json")

    def test_every_item_alias_maps_to_a_known_item(self):
        """If a Hindi word points at an English key that is not in items.json,
        the command silently fails to find a product. Enforce the join."""
        item_set = set(ITEMS)
        unknown = {
            alias: target
            for alias, target in self.aliases.get("items", {}).items()
            if target not in item_set
        }
        self.assertEqual(unknown, {}, "Hindi aliases point at unknown items: %s" % unknown)

    def test_intents_are_valid_labels(self):
        """aliases_hi.json is keyed intent -> [verb, ...]."""
        valid = {"ADD", "REMOVE", "SEARCH_ITEM", "SEARCH_FILTER"}
        for intent, verbs in self.aliases.get("intents", {}).items():
            self.assertIn(intent, valid)
            self.assertTrue(verbs, "%s has no verbs" % intent)

    def test_remove_is_declared_before_add(self):
        """Order is load-bearing: "नहीं चाहिए" (do not want) contains "चाहिए"
        (want), so if ADD were scanned first every negated request would be
        read as an add."""
        keys = list(self.aliases.get("intents", {}))
        self.assertLess(keys.index("REMOVE"), keys.index("ADD"))


class Translations(unittest.TestCase):
    def test_ui_strings_cover_every_english_key(self):
        """A missing Hindi UI key means a control renders in English on an
        otherwise-Hindi screen. Every key in the English source must exist in
        the Hindi table."""
        hi = _load("ui_hi.json")
        missing = set(i18n.EN["ui"]) - set(hi.get("ui", {}))
        self.assertEqual(missing, set(), "ui_hi.json is missing: %s" % missing)

    def test_messages_cover_every_english_key(self):
        hi = _load("ui_hi.json")
        missing = set(i18n.EN["messages"]) - set(hi.get("messages", {}))
        self.assertEqual(missing, set(), "ui_hi.json messages missing: %s" % missing)

    def test_no_message_uses_an_undeclared_placeholder(self):
        """t() swallows KeyError from str.format, so a message template that
        references {item} where the caller passes none would silently render
        the literal braces. Catch templates whose placeholders are not in the
        small set the code actually supplies."""
        supplied = {"item", "qty", "max", "count"}
        import string
        for lang in ("en", "hi"):
            table = i18n.EN["messages"] if lang == "en" else _load("ui_hi.json")["messages"]
            for key, template in table.items():
                fields = {name for _, name, _, _ in string.Formatter().parse(template) if name}
                extra = fields - supplied
                self.assertEqual(extra, set(), "%s/%s uses %s" % (lang, key, extra))


class CatalogIntegrity(unittest.TestCase):
    def test_every_product_has_an_item_key(self):
        """search() hard-filters on the item key; a product without one can
        never be found."""
        missing = [p.get("name") for p in CATALOG if not p.get("item")]
        self.assertEqual(missing, [], "catalog products without an item key: %s" % missing)

    def test_every_product_item_is_a_known_item(self):
        item_set = set(ITEMS)
        unknown = sorted({p["item"] for p in CATALOG
                          if p.get("item") and p["item"] not in item_set})
        self.assertEqual(unknown, [], "catalog items absent from items.json: %s" % unknown)

    def test_every_item_has_a_category(self):
        uncategorised = [item for item in ITEMS if item not in CATEGORIES]
        self.assertEqual(uncategorised, [], "items with no category: %s" % uncategorised)


if __name__ == "__main__":
    unittest.main()
