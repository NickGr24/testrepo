products = ['laptop', 'phone', 'tablet'] 

money = 10000

while money > 0:
    user_choice = input("Ce produs doriti? (laptop/phone/tablet) sau 'exit' pentru a iesi: ")
    if user_choice == 'exit':
        print("La revedere!")
        break
    elif user_choice == 'laptop':
        money -= 4000
        print("Ati cumparat un laptop. Bani ramasi:", money)
    elif user_choice == 'phone':
        money -= 3000
        print("Ati cumparat un telefon. Bani ramasi:", money)
    elif user_choice == 'tablet':
        money -= 3000
        print("Ati cumparat o tableta. Bani ramasi:", money)
    else:
        print("Produsul acesta nu il avem in magazin.")
        