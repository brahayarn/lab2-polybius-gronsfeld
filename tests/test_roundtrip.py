"""Зворотність D(E(x)) = підготовлений x для всіх режимів і обох мов."""
import random
import unittest

from polybius_gronsfeld import gronsfeld, polybius
from polybius_gronsfeld.alphabets import LATIN, UKRAINIAN
from polybius_gronsfeld.polybius import ESCAPE, STRIP, prepare_coordinates
from polybius_gronsfeld.square import build_square
from polybius_gronsfeld.text import prepare

from .helpers import EN_MESSAGES, EN_SQUARE, UK_MESSAGES, UK_SQUARE

SEED = 20261027
CASES = [(UKRAINIAN, UK_SQUARE, UK_MESSAGES), (LATIN, EN_SQUARE, EN_MESSAGES)]


class FixedMessagesTest(unittest.TestCase):
    def test_at_least_ten_messages_per_language(self):
        self.assertGreaterEqual(len(UK_MESSAGES), 10)
        self.assertGreaterEqual(len(EN_MESSAGES), 10)

    def test_coordinates_strip(self):
        for alphabet, square, messages in CASES:
            for message in messages:
                with self.subTest(alphabet=alphabet.code, message=message):
                    ciphertext = polybius.encrypt_coordinates(message, square, STRIP)
                    self.assertEqual(polybius.decrypt_coordinates(ciphertext, square),
                                     prepare_coordinates(message, square, STRIP).text)

    def test_coordinates_escape(self):
        for alphabet, square, messages in CASES:
            for message in messages:
                with self.subTest(alphabet=alphabet.code, message=message):
                    ciphertext = polybius.encrypt_coordinates(message, square, ESCAPE)
                    self.assertEqual(polybius.decrypt_coordinates(ciphertext, square, True),
                                     prepare_coordinates(message, square, ESCAPE).text)

    def test_row_shift(self):
        for alphabet, square, messages in CASES:
            for message in messages:
                with self.subTest(alphabet=alphabet.code, message=message):
                    ciphertext = polybius.encrypt_row_shift(message, square)
                    self.assertEqual(polybius.decrypt_row_shift(ciphertext, square),
                                     prepare(message, alphabet))

    def test_gronsfeld(self):
        for alphabet, _, messages in CASES:
            for message in messages:
                with self.subTest(alphabet=alphabet.code, message=message):
                    ciphertext = gronsfeld.encrypt(message, "0271828", alphabet)
                    self.assertEqual(gronsfeld.decrypt(ciphertext, "0271828", alphabet),
                                     prepare(message, alphabet))


class PropertyBasedTest(unittest.TestCase):
    """Генеративні тести з фіксованим зерном — випадкові ключові слова, ключі й тексти."""

    ITERATIONS = 300

    def setUp(self):
        self.rng = random.Random(SEED)

    def random_keyword(self, alphabet):
        length = self.rng.randint(1, 12)
        keyword = "".join(self.rng.choice(alphabet.square_symbols) for _ in range(length))
        return keyword + self.rng.choice(alphabet.letters)  # гарантована літера

    def random_text(self, alphabet, pool_extra=" ,.!?-\n"):
        pool = alphabet.square_symbols + alphabet.letters.lower() + pool_extra
        return "".join(self.rng.choice(pool) for _ in range(self.rng.randint(0, 60)))

    def test_random_squares_are_valid(self):
        for _ in range(self.ITERATIONS):
            alphabet = self.rng.choice((UKRAINIAN, LATIN))
            square = build_square(alphabet, self.random_keyword(alphabet))
            self.assertEqual(sorted(square.symbols), sorted(alphabet.square_symbols))

    def test_polybius_modes(self):
        for _ in range(self.ITERATIONS):
            alphabet = self.rng.choice((UKRAINIAN, LATIN))
            square = build_square(alphabet, self.random_keyword(alphabet))
            strict_text = self.random_text(alphabet, pool_extra="")
            text = self.random_text(alphabet)
            self.assertEqual(polybius.decrypt_coordinates(
                polybius.encrypt_coordinates(strict_text, square), square),
                prepare(strict_text, alphabet))
            self.assertEqual(polybius.decrypt_coordinates(
                polybius.encrypt_coordinates(text, square, ESCAPE), square, True),
                prepare(text, alphabet))
            self.assertEqual(polybius.decrypt_row_shift(
                polybius.encrypt_row_shift(text, square), square), prepare(text, alphabet))

    def test_gronsfeld(self):
        for _ in range(self.ITERATIONS):
            alphabet = self.rng.choice((UKRAINIAN, LATIN))
            key = "".join(self.rng.choice("0123456789") for _ in range(self.rng.randint(1, 10)))
            if set(key) == {"0"}:
                key += "1"
            text = self.random_text(alphabet)
            self.assertEqual(gronsfeld.decrypt(gronsfeld.encrypt(text, key, alphabet), key, alphabet),
                             prepare(text, alphabet))


if __name__ == "__main__":
    unittest.main()
