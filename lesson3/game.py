import random

lifes = 5
number_to_guess = random.randint(1, 100) # generează un număr aleator între 1 și 10, randint = random integer
print("Ghiceste numărul între 1 și 10. Ai 3 vieți.")
while lifes > 0:
    guess = int(input("Introdu numărul tău: "))
    if guess == number_to_guess:
        print("Felicitări! Ai ghicit numărul!")
        break
    elif guess < number_to_guess:
        lifes -= 1
        print(f"Numărul este prea mic. Îți mai rămân {lifes} vieți.")
    elif guess > number_to_guess:
        lifes -= 1
        print(f"Numărul este prea mare. Îți mai rămân {lifes} vieți.")
