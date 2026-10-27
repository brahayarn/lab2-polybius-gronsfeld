"""Читання і запис UTF-8 файлів."""
import os
import tempfile
import unittest
from unittest import mock

from polybius_gronsfeld import gronsfeld, polybius
from polybius_gronsfeld.alphabets import UKRAINIAN
from polybius_gronsfeld.errors import TextFileError
from polybius_gronsfeld.fileio import read_text, write_text_atomic
from polybius_gronsfeld.polybius import ESCAPE

from .helpers import UK_SQUARE

MULTILINE = "Перший рядок: Ґ, Є, І, Ї.\nДругий — 2026 рік.\r\nТретій із завершальним переносом\n"


class FileIOTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def path(self, name):
        return os.path.join(self.directory.name, name)

    def test_round_trip_preserves_bytes(self):
        write_text_atomic(self.path("a.txt"), MULTILINE)
        self.assertEqual(read_text(self.path("a.txt")), MULTILINE)
        with open(self.path("a.txt"), "rb") as file:
            self.assertEqual(file.read(), MULTILINE.encode("utf-8"))

    def test_bom_is_ignored(self):
        with open(self.path("bom.txt"), "wb") as file:
            file.write(b"\xef\xbb\xbf" + "Їжак".encode("utf-8"))
        self.assertEqual(read_text(self.path("bom.txt")), "Їжак")

    def test_gronsfeld_multiline_file(self):
        write_text_atomic(self.path("plain.txt"), MULTILINE)
        encrypted = gronsfeld.encrypt(read_text(self.path("plain.txt")), "31415", UKRAINIAN)
        write_text_atomic(self.path("cipher.txt"), encrypted)
        decrypted = gronsfeld.decrypt(read_text(self.path("cipher.txt")), "31415", UKRAINIAN)
        self.assertEqual(decrypted, MULTILINE.upper())
        self.assertTrue(decrypted.endswith("\n"))

    def test_coordinates_escape_file_keeps_line_breaks(self):
        ciphertext = polybius.encrypt_coordinates(MULTILINE, UK_SQUARE, ESCAPE)
        write_text_atomic(self.path("coords.txt"), ciphertext + "\n")
        restored = polybius.decrypt_coordinates(read_text(self.path("coords.txt")), UK_SQUARE, True)
        self.assertEqual(restored, MULTILINE.upper())

    def test_invalid_utf8(self):
        with open(self.path("cp1251.txt"), "wb") as file:
            file.write("Привіт".encode("cp1251"))
        with self.assertRaisesRegex(TextFileError, "UTF-8"):
            read_text(self.path("cp1251.txt"))

    def test_missing_file(self):
        with self.assertRaisesRegex(TextFileError, "не знайдено"):
            read_text(self.path("missing.txt"))

    def test_failed_write_leaves_existing_file_untouched(self):
        target = self.path("out.txt")
        write_text_atomic(target, "СТАРИЙ ВМІСТ")
        with mock.patch("polybius_gronsfeld.fileio.os.replace", side_effect=OSError(28, "No space")):
            with self.assertRaises(TextFileError):
                write_text_atomic(target, "НОВИЙ ВМІСТ")
        self.assertEqual(read_text(target), "СТАРИЙ ВМІСТ")
        self.assertEqual(os.listdir(self.directory.name), ["out.txt"])


if __name__ == "__main__":
    unittest.main()
