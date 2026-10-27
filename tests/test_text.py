"""Unicode NFC, регістр, мови та політика форматування."""
import unicodedata
import unittest

from polybius_gronsfeld import gronsfeld, polybius
from polybius_gronsfeld.alphabets import LATIN, UKRAINIAN
from polybius_gronsfeld.errors import UnsupportedCharacterError
from polybius_gronsfeld.text import normalize, prepare

from .helpers import EN_SQUARE, UK_SQUARE


class NormalizationTest(unittest.TestCase):
    def test_decomposed_letters_are_composed(self):
        decomposed = "ЙЇ"  # Й та Ї як база + комбінований знак
        self.assertEqual(normalize(decomposed, UKRAINIAN), "ЙЇ")
        self.assertEqual(polybius.encrypt_coordinates(decomposed, UK_SQUARE), "34 33")

    def test_only_supported_letters_are_uppercased(self):
        self.assertEqual(normalize("ґєії abc", UKRAINIAN), "ҐЄІЇ abc")
        self.assertEqual(normalize("az ґ ß ı", LATIN), "AZ ґ ß ı")

    def test_result_is_nfc(self):
        for text in ("Їжак", "É"):
            self.assertEqual(unicodedata.normalize("NFC", normalize(text, LATIN)),
                             normalize(text, LATIN))


class LanguagesTest(unittest.TestCase):
    def test_ukrainian_specific_letters(self):
        self.assertEqual(polybius.encrypt_coordinates("ҐЄІЇ", UK_SQUARE), "23 25 32 33")
        self.assertEqual(polybius.encrypt_row_shift("ҐЄІЇ", UK_SQUARE), "ЇЛОР")
        self.assertEqual(gronsfeld.decrypt(gronsfeld.encrypt("ҐЄІЇ", "7", UKRAINIAN), "7", UKRAINIAN),
                         "ҐЄІЇ")

    def test_latin_a_and_z(self):
        self.assertEqual(polybius.encrypt_coordinates("AZ", EN_SQUARE), "23 52")
        self.assertEqual(polybius.encrypt_row_shift("AZ", EN_SQUARE), "J5")
        self.assertEqual(gronsfeld.encrypt("AZ", "1", LATIN), "BA")

    def test_language_is_not_guessed(self):
        # Український текст із латинським алфавітом — помилка, а не автоперемикання.
        with self.assertRaises(UnsupportedCharacterError):
            gronsfeld.encrypt("СЛАВА", "1", LATIN)
        with self.assertRaises(UnsupportedCharacterError):
            polybius.encrypt_coordinates("HELLO", UK_SQUARE)

    def test_latin_homoglyph_in_ukrainian_text(self):
        with self.assertRaisesRegex(UnsupportedCharacterError, "U\\+0049"):
            prepare("УКРАЇНI", UKRAINIAN)  # остання I — латинська

    def test_russian_letters_rejected(self):
        for char in "ЫЭЁЪ":
            with self.subTest(char=char), self.assertRaises(UnsupportedCharacterError):
                prepare("А" + char, UKRAINIAN)

    def test_lone_combining_mark_rejected(self):
        with self.assertRaises(UnsupportedCharacterError):
            prepare("́А", UKRAINIAN)


class FormattingTest(unittest.TestCase):
    def test_gronsfeld_keeps_formatting(self):
        text = "Рядок 1,\n«рядок» 2!\r\n"
        encrypted = gronsfeld.encrypt(text, "31415", UKRAINIAN)
        for original, result in zip(prepare(text, UKRAINIAN), encrypted):
            if original not in UKRAINIAN.letters:
                self.assertEqual(original, result)

    def test_apostrophes_and_emoji_are_not_letters(self):
        self.assertEqual(prepare("сімʼя п'ять 😀", UKRAINIAN), "СІМʼЯ П'ЯТЬ 😀")


if __name__ == "__main__":
    unittest.main()
