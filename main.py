from link import Link
from login import Login

if __name__ == '__main__':
    while 1:
        username = input("Username: ")
        password = input("Password: ")
        online = Link(username, password)
        # 如果启用这个，那么程序就不会报密码错误，能增加效率
        # noinspection PyUnreachableCode
        if False:
            online_num = online.any_online()
        else:
            online_num = online.any_online_error()
        if online_num == -1:
            print("密码错误")
        elif not online_num:
            print("没人在线")
            # 这个选项是是否启用确认登录，如果为FALSE就会不请求是否登录直接进行登录
            # noinspection PyUnreachableCode
            if True:
                while 1:
                    try:
                        choice = input("是否要登录（y,n）：")
                        if choice not in ['y', 'n']:
                            raise RuntimeError
                    except RuntimeError:
                        print("输入错误")
                        continue
                    else:
                        if choice == 'y':
                            user = Login(username, password)
                            user.login()
                        exit()
            else:
                user = Login(username, password)
                user.login()
                exit()
        else:
            print("有%s个用户在登录%s" % (online_num, username))
