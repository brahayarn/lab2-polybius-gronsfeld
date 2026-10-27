"""Додаткове завдання: частоти тексту та обох режимів Полібія."""
import unittest

from polybius_gronsfeld.analysis import compare_polybius_modes

from .helpers import UK_SQUARE


class FrequencyTest(unittest.TestCase):
    def test_both_modes_preserve_frequency_profile(self):
        plain, shifted, tokens = compare_polybius_modes("Слава, слава Україні!", UK_SQUARE, limit=36)
        counts = [sorted(count for _, count in table) for table in (plain, shifted, tokens)]
        self.assertEqual(counts[0], counts[1])
        self.assertEqual(counts[0], counts[2])

    def test_most_frequent_symbol_maps_consistently(self):
        plain, shifted, tokens = compare_polybius_modes("АААБ", UK_SQUARE)
        self.assertEqual(plain[0], ("А", 3))
        self.assertEqual(shifted[0], ("Ж", 3))
        self.assertEqual(tokens[0], ("16", 3))


if __name__ == "__main__":
    unittest.main()
