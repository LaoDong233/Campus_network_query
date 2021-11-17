from link import Link


if __name__ == '__main__':
    link = input("输入校园网认证页面<自助服务>网址\n"
                 "类似http://172.30.0.2:8080/selfservice/\n一定要加上http和selfservice\nInput: ")
    username = input("Username: ")
    password = input("Password: ")
    online = Link(link, username, password)
    online_num = online.any_online()
    if not online_num:
        print("没人在线")
    else:
        print("有%s个用户在登录%s" % (online_num, username))
