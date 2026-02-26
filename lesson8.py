name = 'Nikita' # str = string
age = 21 # int = integer (numar intreg)
height = 1.75 # float = (numar zecimal)
is_student = True # bool = boolean (adevarat/fals)
hobbies = ['reading', 'gaming', 'coding'] # list = lista
info = {
    'university': 'MIT',
    'year': 3,
    'major': 'Computer Science'
} # dict = dictionar (cheie: valoare)

address = {
    'street': 'Sarmizegetuza',
    'city': 'Chisinau',
    'zip_code': '2064'
}

capitals = {
    'Franta': 'Paris',
    'Germania': 'Berlin',
    'Spania': 'Madrid',
    'Italia': 'Roma'
}

# capitals.keys() - obtine lista tarilor
# capitals.values() - obtine lista capitalelor
# capitals.items() - obtine lista perechilor (tara, capitala)

for country, capital in capitals.items():
    print('Capitala tarii', country, 'este', capital)
    
shop = {
    'banane': 20,
    'mere': 15,
    'portocale': 25,
}