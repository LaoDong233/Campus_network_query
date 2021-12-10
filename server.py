# from link import Link
import base64
import csv
import threading
import socket
import time

blacklist = list()
whitelist = list()
stu_list = list()
users_drivers = list()
stu_user_list = list()
user_list = list()
server_version = ['vs1.1.0', 'android_v2']


def load():
    global blacklist, whitelist, user_list, users_drivers, stu_user_list
    blacklist = list()
    whitelist = list()
    user_list = list()
    users_drivers = list()
    stu_user_list = list()
    with open("users_drivers.csv", "r", encoding="UTF-8") as f:
        users = csv.reader(f)
        for u in users:
            if len(u) < 2:
                continue
            else:
                users_drivers.append(u)
    with open("users_run.csv", "r", encoding="UTF-8") as f:
        users = csv.reader(f)
        for u in users:
            if len(u) != 2:
                continue
            else:
                user_list.append(u)
    with open("stu_list.csv", "r", encoding="UTF-8") as f:
        users = csv.reader(f)
        for u in users:
            if len(u) != 2:
                continue
            else:
                stu_user_list.append(u)
    with open("blacklist.csv", "r", encoding="UTF-8") as f:
        users = csv.reader(f)
        for u in users:
            blacklist.append(u)
    with open("whitelist.csv", "r", encoding="UTF-8") as f:
        users = csv.reader(f)
        for u in users:
            whitelist.append(u)


def save():
    with open("stu_list.csv", "w+", newline='', encoding='utf-8') as file:
        stu_users = csv.writer(file)
        for stu in stu_user_list:
            stu_users.writerow(stu)
    with open("users_run.csv", "w+", newline='', encoding='utf-8') as file:
        tea_users = csv.writer(file)
        for tea in user_list:
            tea_users.writerow(tea)
    with open("users_drivers.csv", "w+", newline='', encoding='utf-8') as file:
        drivers = csv.writer(file)
        for driver in users_drivers:
            drivers.writerow(driver)
    with open("blacklist.csv", "w+", newline='', encoding='utf-8') as file:
        aa = csv.writer(file)
        for usr in blacklist:
            aa.writerow(usr)
    with open("whitelist.csv", "w+", newline='', encoding='utf-8') as file:
        aa = csv.writer(file)
        for usr in whitelist:
            aa.writerow(usr)


class UserLog(threading.Thread):
    def __init__(self, username, cpu_id):
        threading.Thread.__init__(self)
        self.username = username
        self.id = cpu_id

    def search(self):
        for user in users_drivers:
            if user[0] == self.username:
                for drivers in user:
                    if drivers == self.id:
                        return 0
                else:
                    user.append(self.id)
                    return len(user) - 1
        else:
            users_drivers.append([self.username, self.id])

    def run(self):
        re_num = self.search()
        if [self.username] in whitelist:
            pass
        else:
            if isinstance(re_num, int):
                if re_num > 2:
                    print("%s有%s台设备登陆过" % (self.username, re_num))


class Stu(threading.Thread):
    def __init__(self, socked, add):
        threading.Thread.__init__(self)
        self.address = add
        self.sock = socked

    def run(self):
        if stu_list.count(self.address) >= 2:
            self.sock.close()
        else:
            stu_list.append(self.address)
            time.sleep(600)
            stu_list.remove(self.address)


class Server(threading.Thread):
    def __init__(self, socked, add):
        threading.Thread.__init__(self)
        self.sock = socked
        self.address = add

    def run(self):
        is_dos = Stu(self.sock, self.address[0])
        msg = self.sock.recv(1024).decode('utf-8')
        msg = msg.split("$&^")
        try:
            stu_usr = [msg[0], msg[1]]
        except IndexError:
            print(msg, "用户正在使用v3.x版本")
            self.sock.close()
            return -1
        version = msg[2]
        user_cpu_id = msg[3]
        print("%s 正在请求登录" % stu_usr)
        try:
            stu_user_list.index(stu_usr)
        except ValueError:
            stu_user_list.append(stu_usr)
        version = str(version)
        global server_version
        if version in server_version:
            pass
        else:
            print("%s 正在使用过时的客户端" % self.address[0])
            self.sock.close()
            return -1
        user_cpu_id = str(user_cpu_id)
        UserLog(stu_usr[0], user_cpu_id).start()
        user = None
        for user in user_list:
            if len(user) != 2:
                continue
            else:
                user_list.remove(user)
                username, password = user
            # print("将%s 分配给%s" % (username, self.address))
            # self.sock.send(base64.b64encode(username.encode("utf-8")))
            # self.sock.send(base64.b64encode(password.encode("utf-8")))
            # self.sock.close()
            # break
            if [stu_usr[0]] in blacklist or user_cpu_id in blacklist:
                if [user_cpu_id] not in blacklist:
                    blacklist.append([user_cpu_id])
                if [stu_usr[0]] not in blacklist:
                    blacklist.append([stu_usr[0]])
                print("黑名单中的%s正在请求连接" % stu_usr[0])
                self.sock.send(base64.b64encode("-1".encode('utf-8')))
                return 0
            print("尝试将%s 分配给%s" % (username, self.address))
            user = base64.b64encode(username.encode("utf-8")) + "$&^".encode("utf-8") + base64.b64encode(password.encode("utf-8"))
            self.sock.send(user)
            can_use = self.sock.recv(1024).decode('utf-8')
            if eval(can_use):
                print("成功将%s 分配给%s" % (username, self.address))
                is_dos.start()
                self.sock.close()
                break
            else:
                user_list.append(user)
                continue
            # self.sock.close(
        time.sleep(20)
        user_list.append(user)
        print("已释放%s" % str(self.address))


class Exit(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while 1:
            try:
                a = input(": ")
                if a == '':
                    continue
            except ValueError:
                pass
            else:
                if a == "-1":
                    save()
                    print("保存成功")
                elif a == "help":
                    print("说明：\n-2：从配置文件重新读取\n-1：保存到配置文件\n1：打印用户列表"
                          "\n2：打印可发送用户列表\n3：打印黑名单\n4：添加黑名单")
                elif a == "-2":
                    load()
                    print("从配置文件重新读取成功")
                elif a == "1":
                    print(stu_user_list)
                elif a == '2':
                    print(user_list)
                elif a == '3':
                    print(blacklist)
                elif a == '4':
                    b = input("新封禁id: ")
                    if b != "-1":
                        blacklist.append([b])
                    del b


class AutoSave(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while 1:
            save()
            print("自动保存成功")
            time.sleep(1800)


load()
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ex = Exit()
auto_save = AutoSave()
ex.start()
auto_save.start()
host = ''
port = 12345
server.bind((host, port))
server.listen(1)
while True:
    sock, address = server.accept()
    print("%s正在请求用户" % str(address))
    thread = Server(sock, address)
    thread.start()
