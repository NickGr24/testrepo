username = input("Enter username: ")

def check_password(username, password):
    if len(password) < 8:
        return "Password too short"
    return "Password accepted for user " + username + " with password " + password
print(check_password(username, "mypasd"))