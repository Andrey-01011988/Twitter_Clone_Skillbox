import importlib.util
import os

module_name = 'depencies'  # Имя вашего модуля
module_path = '/project/server/application/api/depencies.py'  # Укажите правильный путь к файлу

if importlib.util.find_spec(module_name) is not None:
    print(f"Модуль {module_name} доступен для импорта.")
else:
    print(f"Модуль {module_name} не найден.")

# Проверка существования файла
if os.path.exists(module_path):
    print(f"Файл {module_path} существует.")
else:
    print(f"Файл {module_path} не найден.")