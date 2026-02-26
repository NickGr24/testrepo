import os
import sys
import io

# path = путь
# current_path = os.getcwd()  # getcwd - получить текущую рабочую папку
# file_path = os.path.join(current_path, sys.argv[1], sys.argv[2])  # Join  в зависимости от ОС ставит необходимый слеш \ или /
# print(file_path)
# if os.path.exists(file_path): #exists, isdir, isfile
#     print("File exists.")
# else:
#     print("File does not exist.")

file1 = io.StringIO()  # StringIO - файловый объект в памяти
file1.write("Hello, World!\n")
file1.write("This is a test file.\n")
file1.write("Goodbye!\n")
file1.seek(0)  # Перемещаем указатель в начало файла
content = file1.read()
print("File content:", content)    