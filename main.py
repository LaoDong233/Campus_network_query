from link import Link


if __name__ == '__main__':
    while 1:
        username = input("Username: ")
        password = input("Password: ")
        online = Link(username, password)
        # 如果启用这个，那么程序就不会报密码错误，能增加效率
        if False:
            # noinspection PyUnreachableCode
            online_num = online.any_online()
        else:
            online_num = online.any_online_error()
        if online_num == -1:
            print("密码错误")
        elif not online_num:
            print("没人在线")
        else:
            print("有%s个用户在登录%s" % (online_num, username))
