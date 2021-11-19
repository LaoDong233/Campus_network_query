import csv
from link import Link


nums = 0
with open("users_database.csv", 'r', encoding='UTF-8') as old:
    old_users = csv.reader(old)
    for user in old_users:
        and_user, md5 = user
        if len(md5) == 39:
            continue
        username = and_user[:7]
        password_list = md5.split(' ')
        num = 0
        for value in password_list:
            if num == 0:
                num = 1
                pass
            else:
                password = value
        print("U: %s\nP: %s" % (username, password))
        nums += 1
        if Link(username, password).get_online_page_error():
            with open("users.csv", 'a+', encoding='UTF-8', newline='') as new_user_list:
                new_users = csv.writer(new_user_list)
                new_users.writerow([username, password])
        # if nums == 10:
        #     exit()
