import os

folder_icon = '\U0001F4C1'
another_f_icon, tm, emoji, earth, smile = '\U0001F5C2', '\u2122', '\u263A', '\U0001F30D', '\U0001F60A'

def list_directory_contents(directory, indent=0, output_file=None):
    try:
        # Получаем список всех файлов и папок в указанной директории
        items = os.listdir(directory)
        items.sort()  # Сортируем элементы для лучшего отображения

        for item in items:
            path = os.path.join(directory, item)
            # Форматируем строку для вывода
            line = ' ' * indent + (f'📁  {item}' if os.path.isdir(path) else f'📄 {item}')

            # Выводим на экран
            print(line)

            # Если указан файл для записи, записываем в него
            if output_file:
                output_file.write(line + '\n')

            # Рекурсивный вызов для папок
            if os.path.isdir(path):
                list_directory_contents(path, indent + 4, output_file)  # Увеличиваем отступ

    except FileNotFoundError:
        print(f"Ошибка: Директория '{directory}' не найдена.")
    except PermissionError:
        print(f"Ошибка: Нет прав доступа к '{directory}'.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


# Укажите путь к нужной директории
directory_path = '/z_folder_app'  # Замените на ваш путь

# Открываем файл для записи
try:
    with open('directory_contents.txt', 'w', encoding='utf-8') as file:
        list_directory_contents(directory_path, output_file=file)
except IOError as e:
    print(f"Ошибка записи в файл: {e}")
finally:
    print("Завершение работы программы.")

# if __name__ == "__main__":
#     print(folder_icon, another_f_icon, tm, emoji, earth, smile)
#     print(f'\U0001f680 kgnbn')
#     print(" 😀")
#     print(u"\U0001F600")