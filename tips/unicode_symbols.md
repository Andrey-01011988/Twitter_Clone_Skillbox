Чтобы представить эмодзи в escape-кодировке в Python, вы можете использовать специальные escape-последовательности для Unicode. Вот как это сделать:

### 1. Формат Escape-последовательностей для Unicode

В Python есть два формата для представления символов Unicode:

- **`\uXXXX`**: используется для символов с кодами до `U+FFFF`. Здесь `XXXX` — это четырехзначный шестнадцатеричный код символа.
- **`\UXXXXXXXX`**: используется для символов с кодами выше `U+FFFF`. Здесь `XXXXXXXX` — это восьмизначный шестнадцатеричный код символа.

### 2. Примеры использования

#### Пример с использованием `\U` для эмодзи

Для эмодзи, например, "😊" (U+1F60A), вы можете использовать следующий код:

```python
# Эмодзи "Улыбающееся лицо с закрытыми глазами"
smiling_face = '\U0001F60A'
print(smiling_face)  # Вывод: 😊
```

#### Пример с использованием `\u` для символа ниже U+FFFF

Для символа "α" (U+03B1), вы можете использовать:

```python
# Греческая буква альфа
greek_alpha = '\u03B1'
print(greek_alpha)  # Вывод: α
```

### 3. Как найти коды Unicode для эмодзи

Чтобы узнать коды Unicode для различных эмодзи, вы можете воспользоваться следующими ресурсами:

- **Unicode Consortium**: [Unicode Character Database](https://www.unicode.org/ucd/)
- **Unicode Table**: [Unicode Character Table](https://unicode-table.com/en/)
- **Wikipedia**: [List of Unicode Characters](https://en.wikipedia.org/wiki/List_of_Unicode_characters)

Эти ресурсы содержат полные таблицы всех доступных символов Unicode и их кодовые точки.

### Заключение

Используя escape-последовательности, вы можете легко вставлять эмодзи и другие символы Unicode в ваши строки в Python. Убедитесь, что ваш файл сохранен в кодировке UTF-8, чтобы избежать проблем с отображением символов.

Citations:
[1] https://javarush.com/quests/lectures/ru.javarush.python.core.lecture.level06.lecture12
[2] https://www.manhunter.ru/assembler/873_rabota_s_escape_posledovatelnostyami_na_assemblere.html
[3] https://learn.microsoft.com/ru-ru/cpp/c-language/octal-and-hexadecimal-character-specifications?view=msvc-170
[4] https://code-basics.com/ru/languages/javascript/lessons/escape-characters
[5] https://javarush.com/quests/lectures/questsyntaxpro.level09.lecture02