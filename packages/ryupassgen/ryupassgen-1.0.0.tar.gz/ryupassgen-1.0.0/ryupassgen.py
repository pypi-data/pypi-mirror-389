import random

chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890@#_&-*"
    
def gen(i):
    password = ""
    count = 0
    while True:
        rand = random.choice(chars)
        password += rand
        count += 1
        if count == i:
            return password
            count = 0
            break