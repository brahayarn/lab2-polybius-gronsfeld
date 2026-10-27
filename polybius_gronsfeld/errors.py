"""Ієрархія помилок, які інтерфейс показує користувачу без трасування стека."""


class CipherError(ValueError):
    """Базова передбачувана помилка: некоректний ключ, режим, текст або файл."""


class InvalidKeyError(CipherError):
    """Ключове слово або цифровий ключ не відповідає умовам прийняття."""


class UnsupportedCharacterError(CipherError):
    """Текст містить символ, недопустимий у вибраному режимі."""


class InvalidCiphertextError(CipherError):
    """Координатний шифротекст містить некоректний токен."""


class TextFileError(CipherError):
    """Файл неможливо прочитати чи записати як UTF-8 текст."""
