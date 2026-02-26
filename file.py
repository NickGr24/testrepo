from random import shuffle
# Lista de întrebări și răspunsuri
intrebari = [
    {"q": "Care este capitala Franței?", "a": "Paris"},
    {"q": "Cât face 228 + 1488?", "a": "1716"},
    {"q": "Ce limbaj folosim aici?", "a": "Python"},
    {"q": "Culoarea cerului într-o zi senină?", "a": "Albastru"},
    {"q": "Cine a scris 'Romeo și Julieta'?", "a": "Shakespeare"}
]

def quiz():
    print("\nBine ai venit la Mini Quiz! Scrie 'exit' ca să ieși.\n")
    scor = 0
    shuffle(intrebari)
    for intrebare in intrebari:
        raspuns = input(intrebare["q"] + " ")
        if raspuns.lower() == "exit":
            break
        if raspuns.strip().lower() == intrebare["a"].lower():
            print("Corect! :)")
            scor += 1
        else:
            print(f"Gresit! Răspunsul corect este: {intrebare['a']}")
    print(f"\nQuiz terminat! Scorul tău: {scor}/{len(intrebari)}\n")

def salut_personalizat():
    nume = input("Cum te cheamă? ")
    print(f"Salut, {nume}! Pregătește-te pentru provocare!")

#Meniu jocului

def meniu():
    while True:
        print("\n=== MENIU MINI QUIZ ===")
        print("1. Start Quiz")
        print("2. Salut personalizat")
        print("3. Ieșire")
        alegere = input("Alege o opțiune (1-3): ")
        if alegere == "1":
            quiz()
        elif alegere == "2":
            salut_personalizat()
        elif alegere == "3":
            print("La revedere!")
            break
        else:
            print("Opțiune invalidă. Alege 1, 2 sau 3.")

meniu()