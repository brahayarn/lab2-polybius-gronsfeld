"""Шість обов'язкових контрольних векторів (розділ 7): прямий результат і відновлення."""
import unittest

from polybius_gronsfeld import gronsfeld, polybius
from polybius_gronsfeld.alphabets import LATIN, UKRAINIAN

from .helpers import EN_SQUARE, UK_SQUARE


class ControlVectorsTest(unittest.TestCase):
    def test_coordinates_ukrainian(self):
        self.assertEqual(polybius.encrypt_coordinates("СЛАВА", UK_SQUARE), "44 35 16 21 16")
        self.assertEqual(polybius.decrypt_coordinates("44 35 16 21 16", UK_SQUARE), "СЛАВА")

    def test_coordinates_latin(self):
        self.assertEqual(polybius.encrypt_coordinates("HELLO", EN_SQUARE), "32 12 35 35 42")
        self.assertEqual(polybius.decrypt_coordinates("32 12 35 35 42", EN_SQUARE), "HELLO")

    def test_row_shift_ukrainian(self):
        self.assertEqual(polybius.encrypt_row_shift("СЛАВА", UK_SQUARE), "ЧТЖИЖ")
        self.assertEqual(polybius.decrypt_row_shift("ЧТЖИЖ", UK_SQUARE), "СЛАВА")

    def test_row_shift_latin(self):
        self.assertEqual(polybius.encrypt_row_shift("HELLO", EN_SQUARE), "OYVVZ")
        self.assertEqual(polybius.decrypt_row_shift("OYVVZ", EN_SQUARE), "HELLO")

    def test_gronsfeld_ukrainian(self):
        self.assertEqual(gronsfeld.encrypt("СЛАВА УКРАЇНІ", "31415", UKRAINIAN), "ФМҐГД ЦЛФБНРЇ")
        self.assertEqual(gronsfeld.decrypt("ФМҐГД ЦЛФБНРЇ", "31415", UKRAINIAN), "СЛАВА УКРАЇНІ")

    def test_gronsfeld_latin(self):
        self.assertEqual(gronsfeld.encrypt("HELLO WORLD", "2718", LATIN), "JLMTQ DPZNK")
        self.assertEqual(gronsfeld.decrypt("JLMTQ DPZNK", "2718", LATIN), "HELLO WORLD")

    def test_lowercase_input_gives_same_vectors(self):
        self.assertEqual(polybius.encrypt_coordinates("слава", UK_SQUARE), "44 35 16 21 16")
        self.assertEqual(polybius.encrypt_row_shift("hello", EN_SQUARE), "OYVVZ")
        self.assertEqual(gronsfeld.encrypt("hello world", "2718", LATIN), "JLMTQ DPZNK")


if __name__ == "__main__":
    unittest.main()
