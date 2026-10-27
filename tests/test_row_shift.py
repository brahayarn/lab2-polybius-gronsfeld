"""Циклічний зсув за рядками: перехід 6 -> 1, розшифрування вгору, сторонні символи."""
import unittest

from polybius_gronsfeld import polybius
from polybius_gronsfeld.errors import UnsupportedCharacterError

from .helpers import EN_SQUARE, UK_SQUARE


class RowShiftTest(unittest.TestCase):
    def test_every_symbol_moves_one_row_down(self):
        for symbol, (row, column) in UK_SQUARE.coordinates.items():
            expected = UK_SQUARE.at(row % 6 + 1, column)
            self.assertEqual(polybius.encrypt_row_shift(symbol, UK_SQUARE), expected)

    def test_sixth_row_wraps_to_first(self):
        self.assertEqual(polybius.encrypt_row_shift("ЬЮЯ012", UK_SQUARE), "БЕЗПКА")
        self.assertEqual(polybius.encrypt_row_shift("456789", EN_SQUARE), "SECURI")

    def test_decrypt_moves_first_row_back_to_sixth(self):
        self.assertEqual(polybius.decrypt_row_shift("БЕЗПКА", UK_SQUARE), "ЬЮЯ012")
        self.assertEqual(polybius.decrypt_row_shift("SECURI", EN_SQUARE), "456789")

    def test_six_shifts_return_original(self):
        text = "ЇЖАК"
        result = text
        for _ in range(6):
            result = polybius.encrypt_row_shift(result, UK_SQUARE)
        self.assertEqual(result, text)

    def test_non_square_characters_are_kept(self):
        self.assertEqual(polybius.encrypt_row_shift("СЛАВА, 345!\n", UK_SQUARE), "ЧТЖИЖ, 345!\n")

    def test_square_digits_are_shifted(self):
        # У квадраті є 0 1 2, тому вони теж зсуваються (рядок 6 -> 1).
        self.assertEqual(polybius.encrypt_row_shift("2026", UK_SQUARE), "АПА6")

    def test_is_monoalphabetic_substitution(self):
        ciphertext = polybius.encrypt_row_shift("ААААББ", UK_SQUARE)
        self.assertEqual(ciphertext, "ЖЖЖЖВВ")

    def test_foreign_letters_rejected(self):
        with self.assertRaises(UnsupportedCharacterError):
            polybius.encrypt_row_shift("CЛАВА", UK_SQUARE)  # латинська C


if __name__ == "__main__":
    unittest.main()
