"""Шифр Гронсфельда: ключі, просування ключа, модуль алфавіту."""
import unittest

from polybius_gronsfeld import gronsfeld
from polybius_gronsfeld.alphabets import LATIN, UKRAINIAN
from polybius_gronsfeld.errors import InvalidKeyError


class KeyTest(unittest.TestCase):
    def test_leading_zero_is_preserved(self):
        self.assertEqual(gronsfeld.parse_key("0123"), [0, 1, 2, 3])
        self.assertNotEqual(gronsfeld.encrypt("AAAA", "0123", LATIN),
                            gronsfeld.encrypt("AAAA", "123", LATIN))
        self.assertEqual(gronsfeld.encrypt("AAAA", "0123", LATIN), "ABCD")

    def test_single_digit_nine(self):
        self.assertEqual(gronsfeld.encrypt("AZ", "9", LATIN), "JI")
        self.assertEqual(gronsfeld.encrypt("АЯ", "9", UKRAINIAN), "ЗЖ")

    def test_long_key(self):
        key = "31415926535897932384626433832795"
        text = "СЛАВА УКРАЇНІ ГЕРОЯМ СЛАВА"
        encrypted = gronsfeld.encrypt(text, key, UKRAINIAN)
        self.assertEqual(gronsfeld.decrypt(encrypted, key, UKRAINIAN), text)

    def test_key_longer_than_text(self):
        self.assertEqual(gronsfeld.encrypt("AB", "12345", LATIN), "BD")

    def test_empty_key(self):
        for key in ("", "  "):
            with self.assertRaisesRegex(InvalidKeyError, "порожній"):
                gronsfeld.parse_key(key)

    def test_only_zeros(self):
        for key in ("0", "0000"):
            with self.assertRaisesRegex(InvalidKeyError, "лише з нулів"):
                gronsfeld.parse_key(key)

    def test_non_digit_characters(self):
        for key in ("31a15", "3 1", "-1", "3.14", "²", "١٢", "１２"):
            with self.subTest(key=key), self.assertRaisesRegex(InvalidKeyError, "лише цифри"):
                gronsfeld.parse_key(key)


class ShiftTest(unittest.TestCase):
    def test_key_advances_only_on_alphabet_letters(self):
        self.assertEqual(gronsfeld.encrypt("A A", "12", LATIN), "B C")
        self.assertEqual(gronsfeld.encrypt("A, 7\nA", "12", LATIN), "B, 7\nC")

    def test_digits_and_punctuation_unchanged(self):
        self.assertEqual(gronsfeld.encrypt("2026 — рік!", "5", UKRAINIAN), "2026 — ХМП!")

    def test_wraps_modulo_alphabet_size(self):
        self.assertEqual(gronsfeld.encrypt("Я", "1", UKRAINIAN), "А")  # m = 33
        self.assertEqual(gronsfeld.encrypt("Z", "1", LATIN), "A")      # m = 26
        self.assertEqual(gronsfeld.decrypt("А", "1", UKRAINIAN), "Я")
        self.assertEqual(gronsfeld.decrypt("A", "1", LATIN), "Z")

    def test_specific_ukrainian_letters(self):
        self.assertEqual(gronsfeld.encrypt("ґєії", "1", UKRAINIAN), "ДЖЇЙ")

    def test_same_key_different_alphabets(self):
        # Вибір алфавіту визначає модуль і множину змінюваних літер.
        self.assertEqual(gronsfeld.encrypt("ABC", "1", LATIN), "BCD")
        with self.assertRaises(Exception):
            gronsfeld.encrypt("ABC", "1", UKRAINIAN)


if __name__ == "__main__":
    unittest.main()
