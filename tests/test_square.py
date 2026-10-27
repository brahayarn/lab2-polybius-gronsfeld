"""Побудова ключового квадрата і перевірка ключового слова."""
import unittest

from polybius_gronsfeld.alphabets import LATIN, UKRAINIAN, get_alphabet
from polybius_gronsfeld.errors import CipherError, InvalidKeyError
from polybius_gronsfeld.square import Square, build_square

from .helpers import EN_SQUARE, UK_SQUARE


class SquareConstructionTest(unittest.TestCase):
    def test_base_sets_have_36_symbols(self):
        for alphabet in (UKRAINIAN, LATIN):
            with self.subTest(alphabet=alphabet.code):
                self.assertEqual(len(alphabet.square_symbols), 36)
                self.assertEqual(len(set(alphabet.square_symbols)), 36)
        self.assertEqual((UKRAINIAN.size, LATIN.size), (33, 26))

    def test_ukrainian_square_from_manual(self):
        self.assertEqual(UK_SQUARE.rows, ["БЕЗПКА", "ВГҐДЄЖ", "ИІЇЙЛМ", "НОРСТУ", "ФХЦЧШЩ", "ЬЮЯ012"])

    def test_latin_square_from_manual(self):
        self.assertEqual(EN_SQUARE.rows, ["SECURI", "TYABDF", "GHJKLM", "NOPQVW", "XZ0123", "456789"])

    def test_size_and_uniqueness(self):
        for square in (UK_SQUARE, EN_SQUARE):
            self.assertEqual([len(row) for row in square.rows], [6] * 6)
            self.assertEqual(len(set(square.symbols)), 36)
            self.assertEqual(set(square.symbols), set(square.alphabet.square_symbols))

    def test_repeats_removed_keeping_first_occurrence(self):
        self.assertTrue(build_square(LATIN, "BANANA").symbols.startswith("BANC"))
        self.assertTrue(build_square(UKRAINIAN, "ЇЖАЧОКЇЖАК").symbols.startswith("ЇЖАЧОКБ"))

    def test_keyword_is_normalized(self):
        self.assertEqual(build_square(UKRAINIAN, "  безпека ").symbols, UK_SQUARE.symbols)
        self.assertEqual(build_square(UKRAINIAN, "Й").symbols[0], "Й")

    def test_keyword_may_contain_square_digits(self):
        self.assertTrue(build_square(UKRAINIAN, "КЛЮЧ2021").symbols.startswith("КЛЮЧ201"))
        self.assertTrue(build_square(LATIN, "KEY2026").symbols.startswith("KEY206"))

    def test_lookup_tables(self):
        self.assertEqual(UK_SQUARE.coordinates["Б"], (1, 1))
        self.assertEqual(UK_SQUARE.coordinates["2"], (6, 6))
        self.assertEqual(UK_SQUARE.at(4, 4), "С")
        for symbol, (row, column) in UK_SQUARE.coordinates.items():
            self.assertEqual(UK_SQUARE.at(row, column), symbol)


class KeywordValidationTest(unittest.TestCase):
    def test_empty(self):
        for keyword in ("", "   "):
            with self.assertRaisesRegex(InvalidKeyError, "порожнє"):
                build_square(UKRAINIAN, keyword)

    def test_symbol_outside_square(self):
        cases = [(UKRAINIAN, "КЛЮЧ3"), (UKRAINIAN, "KEY"), (UKRAINIAN, "ДВА СЛОВА"),
                 (LATIN, "КЛЮЧ"), (LATIN, "KEY!"), (UKRAINIAN, "ЫЭ")]
        for alphabet, keyword in cases:
            with self.subTest(keyword=keyword), self.assertRaisesRegex(InvalidKeyError, "немає в квадраті"):
                build_square(alphabet, keyword)

    def test_keyword_without_letters(self):
        with self.assertRaisesRegex(InvalidKeyError, "щонайменше одну літеру"):
            build_square(UKRAINIAN, "2021")
        with self.assertRaisesRegex(InvalidKeyError, "щонайменше одну літеру"):
            build_square(LATIN, "123")

    def test_invalid_square_rejected(self):
        with self.assertRaises(InvalidKeyError):
            Square(LATIN, LATIN.square_symbols[:-1])
        with self.assertRaises(InvalidKeyError):
            Square(LATIN, LATIN.square_symbols[:-1] + "A")

    def test_unknown_alphabet(self):
        with self.assertRaisesRegex(CipherError, "невідомий алфавіт"):
            get_alphabet("ru")
        with self.assertRaises(CipherError):
            get_alphabet("auto")


if __name__ == "__main__":
    unittest.main()
