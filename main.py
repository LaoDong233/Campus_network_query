from link import Link


if __name__ == '__main__':
    username = input("Username: ")
    password = input("Password: ")
    online = Link(username, password)
    online_num = online.any_online()
    if online_num == -1:
        print("密码错误")
    elif not online_num:
        print("没人在线")
    else:
        print("有%s个用户在登录%s" % (online_num, username))
