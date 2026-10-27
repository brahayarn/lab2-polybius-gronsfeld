"""Відтворюваний експеримент: контрольні вектори та власні тексти для звіту.

Запуск з кореня проєкту:  python3 experiments/run_experiment.py
Результати: experiments/results/ (шифротексти, розшифрування, summary.md).
"""
from __future__ import annotations

import hashlib
import os
import platform
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from polybius_gronsfeld import __version__, analysis, gronsfeld, polybius  # noqa: E402
from polybius_gronsfeld.alphabets import LATIN, UKRAINIAN  # noqa: E402
from polybius_gronsfeld.fileio import read_text, write_text_atomic  # noqa: E402
from polybius_gronsfeld.polybius import ESCAPE, STRIP, prepare_coordinates  # noqa: E402
from polybius_gronsfeld.square import build_square  # noqa: E402
from polybius_gronsfeld.text import prepare  # noqa: E402

RESULTS = os.path.join(ROOT, "experiments", "results")
SAMPLES = [
    (UKRAINIAN, "message_uk.txt", "ШИФРОГРАМА", "0271828"),
    (LATIN, "message_en.txt", "CRYPTOGRAPHY", "0271828"),
]


def status(ok: bool) -> str:
    return "OK" if ok else "FAIL"


def vectors_table() -> list:
    uk = build_square(UKRAINIAN, "БЕЗПЕКА")
    en = build_square(LATIN, "SECURITY")
    vectors = [
        ("Полібій coordinates, укр.", "БЕЗПЕКА", "СЛАВА", "44 35 16 21 16",
         lambda t: polybius.encrypt_coordinates(t, uk), lambda c: polybius.decrypt_coordinates(c, uk)),
        ("Полібій coordinates, лат.", "SECURITY", "HELLO", "32 12 35 35 42",
         lambda t: polybius.encrypt_coordinates(t, en), lambda c: polybius.decrypt_coordinates(c, en)),
        ("Полібій row shift, укр.", "БЕЗПЕКА", "СЛАВА", "ЧТЖИЖ",
         lambda t: polybius.encrypt_row_shift(t, uk), lambda c: polybius.decrypt_row_shift(c, uk)),
        ("Полібій row shift, лат.", "SECURITY", "HELLO", "OYVVZ",
         lambda t: polybius.encrypt_row_shift(t, en), lambda c: polybius.decrypt_row_shift(c, en)),
        ("Гронсфельд, укр.", "31415", "СЛАВА УКРАЇНІ", "ФМҐГД ЦЛФБНРЇ",
         lambda t: gronsfeld.encrypt(t, "31415", UKRAINIAN),
         lambda c: gronsfeld.decrypt(c, "31415", UKRAINIAN)),
        ("Гронсфельд, лат.", "2718", "HELLO WORLD", "JLMTQ DPZNK",
         lambda t: gronsfeld.encrypt(t, "2718", LATIN), lambda c: gronsfeld.decrypt(c, "2718", LATIN)),
    ]
    lines = ["| Алгоритм і алфавіт | Ключ | Відкритий текст | Очікуваний | Фактичний | Розшифровано | Статус |",
             "|---|---|---|---|---|---|---|"]
    for name, key, plain, expected, encrypt, decrypt in vectors:
        actual = encrypt(plain)
        restored = decrypt(actual)
        lines.append(f"| {name} | {key} | {plain} | {expected} | {actual} | {restored} | "
                     f"{status(actual == expected and restored == plain)} |")
    return lines


def run_sample(alphabet, filename, keyword, digits) -> list:
    text = read_text(os.path.join(ROOT, "samples", filename))
    square = build_square(alphabet, keyword)
    runs = {
        "coordinates-strip": (
            polybius.encrypt_coordinates(text, square, STRIP),
            lambda c: polybius.decrypt_coordinates(c, square),
            prepare_coordinates(text, square, STRIP).text),
        "coordinates-escape": (
            polybius.encrypt_coordinates(text, square, ESCAPE),
            lambda c: polybius.decrypt_coordinates(c, square, allow_escapes=True),
            prepare(text, alphabet)),
        "row-shift": (
            polybius.encrypt_row_shift(text, square),
            lambda c: polybius.decrypt_row_shift(c, square),
            prepare(text, alphabet)),
        "gronsfeld": (
            gronsfeld.encrypt(text, digits, alphabet),
            lambda c: gronsfeld.decrypt(c, digits, alphabet),
            prepare(text, alphabet)),
    }
    removed = prepare_coordinates(text, square, STRIP).removed
    lines = [
        f"### {alphabet.name.capitalize()} текст: samples/{filename}",
        "",
        f"- SHA-256: `{hashlib.sha256(text.encode('utf-8')).hexdigest()}`",
        f"- Символів: {len(text)}, літер алфавіту: {sum(c in alphabet.letters for c in prepare(text, alphabet))}",
        f"- Ключове слово квадрата: {keyword}; цифровий ключ Гронсфельда: {digits}",
        f"- Режим strip вилучив символів: {sum(removed.values())}",
        "",
        "```",
        square.format(),
        "```",
        "",
        "| Режим | SHA-256 результату (16 символів) | D(E(x)) = prepare(x) |",
        "|---|---|---|",
    ]
    for mode, (encrypted, decrypt, expected) in runs.items():
        restored = decrypt(encrypted)
        base = f"{alphabet.code}.{mode}"
        write_text_atomic(os.path.join(RESULTS, f"{base}.enc.txt"), encrypted)
        write_text_atomic(os.path.join(RESULTS, f"{base}.dec.txt"), restored)
        digest = hashlib.sha256(encrypted.encode("utf-8")).hexdigest()[:16]
        lines.append(f"| {mode} | `{digest}` | {status(restored == expected)} |")
    plain, shifted, tokens = analysis.compare_polybius_modes(text, square, limit=8)
    lines += ["", "Частоти (8 найчастіших):", "",
              "| Ранг | Текст | Row shift | Координати |", "|---|---|---|---|"]
    for rank, (p, s, t) in enumerate(zip(plain, shifted, tokens), start=1):
        lines.append(f"| {rank} | {p[0]} — {p[1]} | {s[0]} — {s[1]} | {t[0]} — {t[1]} |")
    return lines + [""]


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    report = [
        "# Результати експерименту",
        "",
        f"- Версія програми: {__version__}",
        f"- Python: {platform.python_version()} ({platform.python_implementation()})",
        f"- Платформа: {platform.system()} {platform.release()} {platform.machine()}",
        "",
        "## Контрольні вектори",
        "",
        *vectors_table(),
        "",
        "## Власні тексти",
        "",
    ]
    for sample in SAMPLES:
        report += run_sample(*sample)
    write_text_atomic(os.path.join(RESULTS, "summary.md"), "\n".join(report))
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
