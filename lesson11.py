from pathlib import Path
from shutil import rmtree

file_path = input('Enter file path: ')

p = Path(file_path)

if p.exists():
    print('File or folder exists')
    if p.is_dir():
        rmtree(p)
    elif p.is_file():
        p.unlink()
else:
    print('File does not exist')
    
    
    
# with open ('lesson12.py', 'r') as file:
#     content = file.read()
#     print(content)
    
    
# file = open('lesson11.py', 'r')
# content = file.read()
# print(content)  
# file.close()