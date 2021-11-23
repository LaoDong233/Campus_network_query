# from link import Link
import base64
import csv
import threading
import socket
import time


stu_list = list()
user_list = list()
stu_user_list = list()
with open("users.csv", "r", encoding="UTF-8") as f:
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
            time.sleep(60)
            stu_list.remove(self.address)


class Server(threading.Thread):
    def __init__(self, socked, add):
        threading.Thread.__init__(self)
        self.sock = socked
        self.address = add

    def run(self):
        is_dos = Stu(self.sock, self.address[0])
        stu_usr = self.sock.recv(1024).decode('utf-8')
        print(stu_usr)
        try:
            stu_user_list.index(eval(stu_usr))
        except ValueError:
            stu_user_list.append(eval(stu_usr))
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
            print("尝试将%s 分配给%s" % (username, self.address))
            self.sock.send(base64.b64encode(username.encode("utf-8")))
            self.sock.send(base64.b64encode(password.encode("utf-8")))
            can_use = self.sock.recv(1024).decode('utf-8')
            if eval(can_use):
                print("成功将%s 分配给%s" % (username, self.address))
                is_dos.start()
                self.sock.close()
                break
            else:
                user_list.append(username)
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
                a = int(input(": "))
            except ValueError:
                pass
            else:
                print(stu_user_list)
                if a == -1:
                    with open("stu_list.csv", "w+", newline='', encoding='utf-8') as file:
                        stu_users = csv.writer(file)
                        for stu in stu_user_list:
                            stu_users.writerow(stu)


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ex = Exit()
ex.start()
host = ''
port = 12345
server.bind((host, port))
server.listen(1)
while True:
    sock, address = server.accept()
    print("%s正在请求用户" % str(address))
    thread = Server(sock, address)
    thread.start()
