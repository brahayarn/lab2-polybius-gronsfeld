# Лабораторна робота 2 — квадрат Полібія та шифр Гронсфельда

Консольна програма, яка зашифровує й розшифровує український і латинський текст трьома
режимами:

- `coordinates` — квадрат Полібія, кожен символ замінюється координатами «рядок стовпець»;
- `row-shift` — квадрат Полібія, символ замінюється символом із наступного рядка (циклічно);
- `gronsfeld` — шифр Гронсфельда з цифровим ключем.

> Навчальні алгоритми: зберігають частоти символів і не забезпечують цілісності.
> Не використовуйте їх для паролів, персональних чи службових даних.

## Вимоги

- Python 3.8+ (перевірено на CPython 3.9.6 і 3.15.0, macOS 15 arm64)
- Зовнішніх залежностей немає — лише стандартна бібліотека (`unicodedata`, `argparse`, `unittest`)

## Запуск

Усі команди виконуються з кореня проєкту. Алфавіт (`-a uk` або `-a en`) обов'язковий —
програма не вгадує мову.

```bash
python3 -m polybius_gronsfeld --help
python3 -m polybius_gronsfeld rules                     # правила підготовки тексту
python3 -m polybius_gronsfeld square -a uk -k БЕЗПЕКА   # показати ключовий квадрат

# Контрольні вектори з методички
python3 -m polybius_gronsfeld encrypt -a uk -c coordinates -k БЕЗПЕКА -t СЛАВА       # 44 35 16 21 16
python3 -m polybius_gronsfeld encrypt -a en -c coordinates -k SECURITY -t HELLO      # 32 12 35 35 42
python3 -m polybius_gronsfeld encrypt -a uk -c row-shift   -k БЕЗПЕКА -t СЛАВА       # ЧТЖИЖ
python3 -m polybius_gronsfeld encrypt -a en -c row-shift   -k SECURITY -t HELLO      # OYVVZ
python3 -m polybius_gronsfeld encrypt -a uk -c gronsfeld   -k 31415 -t "СЛАВА УКРАЇНІ"  # ФМҐГД ЦЛФБНРЇ
python3 -m polybius_gronsfeld encrypt -a en -c gronsfeld   -k 2718  -t "HELLO WORLD"    # JLMTQ DPZNK

# Розшифрування
python3 -m polybius_gronsfeld decrypt -a uk -c coordinates -k БЕЗПЕКА -t "44 35 16 21 16"

# Координати для тексту з пробілами: вилучити (видимо) або екранувати
python3 -m polybius_gronsfeld encrypt -a uk -c coordinates -k БЕЗПЕКА --strip  -t "Слава Україні!"
python3 -m polybius_gronsfeld encrypt -a uk -c coordinates -k БЕЗПЕКА --escape -t "Слава Україні!"
python3 -m polybius_gronsfeld decrypt -a uk -c coordinates -k БЕЗПЕКА --escape -i cipher.txt

# UTF-8 файли
python3 -m polybius_gronsfeld encrypt -a uk -c gronsfeld -k 0271828 -i samples/message_uk.txt -o cipher.txt
python3 -m polybius_gronsfeld decrypt -a uk -c gronsfeld -k 0271828 -i cipher.txt -o plain.txt

# Ручне введення: без -t та -i текст читається зі стандартного вводу (завершити Ctrl-D)
python3 -m polybius_gronsfeld encrypt -a en -c row-shift -k SECURITY --show-square

# Додатково: частоти тексту, row shift і координат
python3 -m polybius_gronsfeld analyze -a uk -k ШИФРОГРАМА -i samples/message_uk.txt
```

Параметри `encrypt` / `decrypt`:

| Параметр | Призначення |
|---|---|
| `-a, --alphabet` | `uk` або `en` (обов'язковий) |
| `-c, --cipher` | `coordinates`, `row-shift`, `gronsfeld` |
| `-k, --key` | ключове слово квадрата або рядок цифр Гронсфельда |
| `--strip` | coordinates encrypt: вилучити символи поза квадратом; що саме вилучено, виводиться у stderr |
| `--escape` | coordinates: символи поза квадратом кодуються токенами `U+XXXX` |
| `--show-square` | показати активний квадрат (stderr) |
| `-t` / `-i` | текст у командному рядку / вхідний файл |
| `-o` | вихідний файл (атомарний запис; при помилці не створюється) |

Коди завершення: `0` — успіх, `1` — некоректний ключ, текст, координати чи файл
(повідомлення `Помилка: …` у stderr, без трасування), `2` — неправильні аргументи.

## Тести

```bash
python3 -m unittest             # 97 тестів
python3 -m unittest -v
python3 experiments/run_experiment.py   # відтворюваний експеримент → experiments/results/
```

## Специфікація обробки тексту

| Аспект | Правило |
|---|---|
| Алфавіти | uk: `АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ` (m = 33); en: `A…Z` (m = 26) |
| Квадрати 6×6 | uk: 33 літери + `0 1 2`; en: 26 літер + `0…9` |
| Кодування | UTF-8; BOM на вході ігнорується; `\n` і `\r\n` зберігаються |
| Нормалізація | Unicode NFC перед перевіркою ключа і тексту |
| Регістр | до верхнього регістру переводяться лише літери вибраного алфавіту |
| Сторонні літери | літери іншої абетки (зокрема латинська `I` серед українських) і окремі комбіновані знаки — помилка |
| coordinates | `strict` (типово): лише символи квадрата; `--strip`: видиме вилучення решти; `--escape`: `U+XXXX` |
| Розбір координат | токени розділені пробільними символами; кожен — дві ASCII-цифри 1…6 (або канонічний `U+XXXX` з `--escape`) |
| row-shift | символи квадрата (включно з цифрами квадрата) зсуваються на рядок униз, 6-й → 1-й; решта без змін |
| gronsfeld | змінюються лише літери алфавіту; пробіли, цифри, розділові знаки не змінюються і не споживають цифру ключа |
| Цифровий ключ | рядок ASCII-цифр, не порожній, не лише нулі; початкові нулі зберігаються |

## Структура

```
polybius_gronsfeld/
  alphabets.py   набори символів uk / en, явний вибір
  text.py        NFC, регістр, перевірка сторонніх літер
  square.py      побудова квадрата 6×6 і таблиць пошуку
  polybius.py    coordinates (strict / strip / escape) та row-shift
  gronsfeld.py   шифр Гронсфельда
  analysis.py    частоти (додаткове завдання)
  fileio.py      читання / атомарний запис UTF-8
  errors.py      класи передбачуваних помилок
  cli.py         командний рядок
tests/           97 тестів unittest
samples/         власні тексти (український і латинський)
experiments/     скрипт відтворюваного експерименту та результати
docs/            звіт
```
