"""Консольний інтерфейс: вектори, коди завершення, повідомлення, файли."""
import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from polybius_gronsfeld.cli import EXIT_ERROR, EXIT_OK, main


def run(*argv, stdin=""):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
            mock.patch("sys.stdin", io.StringIO(stdin)):
        try:
            code = main(list(argv))
        except SystemExit as exit_:
            code = exit_.code
    return code, out.getvalue(), err.getvalue()


VECTORS = [
    ("uk", "coordinates", "БЕЗПЕКА", "СЛАВА", "44 35 16 21 16"),
    ("en", "coordinates", "SECURITY", "HELLO", "32 12 35 35 42"),
    ("uk", "row-shift", "БЕЗПЕКА", "СЛАВА", "ЧТЖИЖ"),
    ("en", "row-shift", "SECURITY", "HELLO", "OYVVZ"),
    ("uk", "gronsfeld", "31415", "СЛАВА УКРАЇНІ", "ФМҐГД ЦЛФБНРЇ"),
    ("en", "gronsfeld", "2718", "HELLO WORLD", "JLMTQ DPZNK"),
]


class CliCommandsTest(unittest.TestCase):
    def test_all_vectors(self):
        for alphabet, cipher, key, plain, expected in VECTORS:
            with self.subTest(alphabet=alphabet, cipher=cipher):
                options = ["-a", alphabet, "-c", cipher, "-k", key]
                self.assertEqual(run("encrypt", *options, "-t", plain), (EXIT_OK, expected + "\n", ""))
                self.assertEqual(run("decrypt", *options, "-t", expected), (EXIT_OK, plain + "\n", ""))

    def test_square_command_and_show_square(self):
        code, out, _ = run("square", "-a", "uk", "-k", "БЕЗПЕКА")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("6   Ь Ю Я 0 1 2", out)
        code, _, err = run("encrypt", "-a", "en", "-c", "row-shift", "-k", "SECURITY",
                           "--show-square", "-t", "HELLO")
        self.assertIn("1   S E C U R I", err)

    def test_strip_reports_removed_characters(self):
        code, out, err = run("encrypt", "-a", "uk", "-c", "coordinates", "-k", "БЕЗПЕКА",
                             "--strip", "-t", "Слава Україні!")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out, "44 35 16 21 16 46 15 43 16 33 41 32\n")
        self.assertIn("вилучено символів — 2", err)

    def test_escape_round_trip(self):
        options = ["-a", "uk", "-c", "coordinates", "-k", "БЕЗПЕКА", "--escape"]
        _, out, _ = run("encrypt", *options, "-t", "Слава Україні!")
        self.assertIn("U+0020", out)
        self.assertEqual(run("decrypt", *options, "-t", out)[1], "СЛАВА УКРАЇНІ!\n")

    def test_stdin_rules_help_version(self):
        self.assertEqual(run("encrypt", "-a", "en", "-c", "gronsfeld", "-k", "1", stdin="abc\n")[1],
                         "BCD\n")
        self.assertIn("NFC", run("rules")[1])
        code, out, _ = run("--help")
        self.assertEqual(code, 0)
        self.assertIn("encrypt", out)

    def test_analyze(self):
        code, out, _ = run("analyze", "-a", "uk", "-k", "БЕЗПЕКА", "-t", "ААА ББ")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Row shift", out)


class CliErrorsTest(unittest.TestCase):
    def assert_error(self, *argv, message):
        code, out, err = run(*argv)
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(out, "")
        self.assertIn("Помилка:", err)
        self.assertIn(message, err)
        self.assertNotIn("Traceback", err)

    def test_invalid_keys(self):
        self.assert_error("encrypt", "-a", "uk", "-c", "gronsfeld", "-k", "", "-t", "А", message="порожній")
        self.assert_error("encrypt", "-a", "uk", "-c", "gronsfeld", "-k", "000", "-t", "А", message="нулів")
        self.assert_error("encrypt", "-a", "uk", "-c", "row-shift", "-k", "KEY", "-t", "А",
                          message="немає в квадраті")
        self.assert_error("encrypt", "-a", "en", "-c", "coordinates", "-k", "123", "-t", "A",
                          message="літеру")

    def test_invalid_ciphertext_and_text(self):
        self.assert_error("decrypt", "-a", "uk", "-c", "coordinates", "-k", "БЕЗПЕКА", "-t", "44 67",
                          message="токен №2")
        self.assert_error("encrypt", "-a", "uk", "-c", "coordinates", "-k", "БЕЗПЕКА", "-t", "А Б",
                          message="позиції 2")
        self.assert_error("encrypt", "-a", "uk", "-c", "gronsfeld", "-k", "1", "-t", "Hello",
                          message="U+0048")

    def test_mode_options_validated(self):
        self.assert_error("encrypt", "-a", "uk", "-c", "gronsfeld", "-k", "1", "--escape", "-t", "А",
                          message="лише до coordinates")
        self.assert_error("encrypt", "-a", "uk", "-c", "gronsfeld", "-k", "1", "--show-square",
                          "-t", "А", message="немає квадрата")

    def test_usage_errors(self):
        for argv in (["encrypt", "-c", "gronsfeld", "-k", "1", "-t", "A"],      # без алфавіту
                     ["encrypt", "-a", "ru", "-c", "gronsfeld", "-k", "1"],
                     ["encrypt", "-a", "en", "-c", "caesar", "-k", "1"],
                     ["decrypt", "-a", "en", "-c", "coordinates", "-k", "A", "--strip"]):
            with self.subTest(argv=argv):
                self.assertEqual(run(*argv)[0], 2)


class CliFilesTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.plain, self.cipher, self.back = (os.path.join(self.directory.name, name)
                                              for name in ("plain.txt", "cipher.txt", "back.txt"))

    def test_file_round_trip_for_every_mode(self):
        text = "Рядок один: Ґанок.\nРядок два — Їжак, Єнот, Іволга!\n"
        with open(self.plain, "w", encoding="utf-8", newline="") as file:
            file.write(text)
        for options in (["-c", "coordinates", "-k", "ШИФР", "--escape"],
                        ["-c", "row-shift", "-k", "ШИФР"],
                        ["-c", "gronsfeld", "-k", "0271828"]):
            with self.subTest(cipher=options[1]):
                self.assertEqual(run("encrypt", "-a", "uk", *options, "-i", self.plain, "-o", self.cipher)[0],
                                 EXIT_OK)
                self.assertEqual(run("decrypt", "-a", "uk", *options, "-i", self.cipher, "-o", self.back)[0],
                                 EXIT_OK)
                with open(self.back, encoding="utf-8", newline="") as file:
                    self.assertEqual(file.read(), text.upper())

    def test_error_does_not_create_output(self):
        with open(self.cipher, "w", encoding="utf-8") as file:
            file.write("44 35 99")
        code, _, _ = run("decrypt", "-a", "uk", "-c", "coordinates", "-k", "БЕЗПЕКА",
                         "-i", self.cipher, "-o", self.back)
        self.assertEqual(code, EXIT_ERROR)
        self.assertFalse(os.path.exists(self.back))


if __name__ == "__main__":
    unittest.main()
