import csv
from link import Link

while 1:
    with open("users.csv", "a+", encoding="utf-8", newline='') as f:
        users = csv.writer(f)
        username = input("Username: ")
        password = input("Password: ")
        if not Link(username, password):
            print("密码错误")
            continue
        else:
            users.writerow([username, password])
