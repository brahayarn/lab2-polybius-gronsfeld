"""Координатний режим: границі квадрата, суворий розбір токенів, strip і escape."""
import unittest

from polybius_gronsfeld import polybius
from polybius_gronsfeld.errors import InvalidCiphertextError, UnsupportedCharacterError
from polybius_gronsfeld.polybius import ESCAPE, STRIP, prepare_coordinates

from .helpers import EN_SQUARE, UK_SQUARE


class CornersTest(unittest.TestCase):
    def test_first_and_last_rows(self):
        self.assertEqual(polybius.encrypt_coordinates("БЕЗПКА", UK_SQUARE), "11 12 13 14 15 16")
        self.assertEqual(polybius.encrypt_coordinates("ЬЮЯ012", UK_SQUARE), "61 62 63 64 65 66")
        self.assertEqual(polybius.decrypt_coordinates("11 66", UK_SQUARE), "Б2")
        self.assertEqual(polybius.decrypt_coordinates("11 66", EN_SQUARE), "S9")

    def test_empty_text(self):
        self.assertEqual(polybius.encrypt_coordinates("", UK_SQUARE), "")
        self.assertEqual(polybius.decrypt_coordinates("", UK_SQUARE), "")

    def test_whitespace_between_tokens_is_flexible(self):
        self.assertEqual(polybius.decrypt_coordinates(" 44  35\n16\t21 16\n", UK_SQUARE), "СЛАВА")


class StrictTokenParsingTest(unittest.TestCase):
    def assert_rejected(self, ciphertext, message):
        with self.assertRaisesRegex(InvalidCiphertextError, message):
            polybius.decrypt_coordinates(ciphertext, UK_SQUARE)

    def test_out_of_range_coordinates(self):
        for token in ("00", "17", "61x", "70", "07"):
            with self.subTest(token=token):
                self.assert_rejected(f"11 {token}", "токен №2")
        for token in ("00", "17", "67", "71"):
            with self.subTest(token=token):
                self.assert_rejected(token, "поза діапазоном")

    def test_61_is_valid_but_67_is_not(self):
        self.assertEqual(polybius.decrypt_coordinates("61", UK_SQUARE), "Ь")
        self.assert_rejected("67", "поза діапазоном")

    def test_wrong_length_and_foreign_text(self):
        self.assert_rejected("4", "1 цифр")
        self.assert_rejected("443", "3 цифр")
        self.assert_rejected("4435", "4 цифр")
        self.assert_rejected("44,35", "сторонній текст")
        self.assert_rejected("СЛАВА", "сторонній текст")
        self.assert_rejected("４４", "сторонній текст")  # повноширинні цифри

    def test_escape_token_without_escape_mode(self):
        self.assert_rejected("44 U+0020", "без режиму --escape")


class StrictEncryptTest(unittest.TestCase):
    def test_space_rejected_with_position(self):
        with self.assertRaisesRegex(UnsupportedCharacterError, "позиції 6"):
            polybius.encrypt_coordinates("СЛАВА УКРАЇНІ", UK_SQUARE)

    def test_digit_outside_ukrainian_square(self):
        with self.assertRaisesRegex(UnsupportedCharacterError, "'3'"):
            polybius.encrypt_coordinates("2023", UK_SQUARE)

    def test_square_digits_are_encoded(self):
        self.assertEqual(polybius.encrypt_coordinates("2021", UK_SQUARE), "66 64 66 65")


class StripModeTest(unittest.TestCase):
    def test_removal_is_reported(self):
        prepared = prepare_coordinates("Слава, Україні!", UK_SQUARE, STRIP)
        self.assertEqual(prepared.text, "СЛАВАУКРАЇНІ")
        self.assertEqual(prepared.removed, {",": 1, " ": 1, "!": 1})

    def test_round_trip_against_prepared_text(self):
        ciphertext = polybius.encrypt_coordinates("Слава Україні", UK_SQUARE, STRIP)
        self.assertEqual(polybius.decrypt_coordinates(ciphertext, UK_SQUARE), "СЛАВАУКРАЇНІ")


class EscapeModeTest(unittest.TestCase):
    def test_spaces_and_punctuation_are_escaped(self):
        self.assertEqual(polybius.encrypt_coordinates("HI, YO", EN_SQUARE, ESCAPE),
                         "32 16 U+002C U+0020 22 42")

    def test_full_round_trip_with_arbitrary_unicode(self):
        text = "Привіт, світ! 2026\n😀 é ß\r\n"
        ciphertext = polybius.encrypt_coordinates(text, UK_SQUARE, ESCAPE)
        self.assertNotIn(" U+20 ", ciphertext)
        self.assertIn("U+1F600", ciphertext)
        self.assertEqual(polybius.decrypt_coordinates(ciphertext, UK_SQUARE, allow_escapes=True),
                         prepare_coordinates(text, UK_SQUARE, ESCAPE).text)

    def test_non_canonical_escape_rejected(self):
        for token in ("U+20", "U+00020", "U+002c", "u+0020"):
            with self.subTest(token=token), self.assertRaises(InvalidCiphertextError):
                polybius.decrypt_coordinates(token, UK_SQUARE, allow_escapes=True)

    def test_escape_of_square_symbol_rejected(self):
        with self.assertRaisesRegex(InvalidCiphertextError, "символ квадрата"):
            polybius.decrypt_coordinates("U+0410", UK_SQUARE, allow_escapes=True)

    def test_invalid_code_points_rejected(self):
        for token in ("U+D800", "U+110000"):
            with self.subTest(token=token), self.assertRaises(InvalidCiphertextError):
                polybius.decrypt_coordinates(token, UK_SQUARE, allow_escapes=True)


if __name__ == "__main__":
    unittest.main()
