import base64
import socket
import time
import tkinter.messagebox
from subprocess import run as command
from tkinter import *

# import uuid
import wmi

from link import Link
from login import Login

version = "vs1.1.1"
host = '172.16.28.174'
port = 12345
save_username = ""
save_password = ""


def load():
    global save_username, save_password
    try:
        with open("save.txt", "r", encoding="utf-8") as f:
            user = f.read()
            user = user.split("&")
            save_username = user[0]
            save_password = user[1]
    except FileNotFoundError:
        pass


load()


class My_Gui:
    def __init__(self):
        self.root = Tk()
        self.root.title("校园网认证")
        self.root.wm_attributes("-alpha", 1.0)
        self.root.wm_attributes("-topmost", True)
        self.password = StringVar()
        self.username = StringVar()
        self.root.resizable(False, False)
        self.main_window()
        self.system = wmi.WMI()

    def main_window(self):
        global version, save_username, save_password
        Label(self.root, text="用户名").grid(row=0, column=0)
        e1 = Entry(self.root, textvariable=self.username)
        Label(self.root, text="密码").grid(row=0, column=1)
        e2 = Entry(self.root, textvariable=self.password, show='*')
        e1.insert(0, save_username)
        e2.insert(0, save_password)
        e1.grid(row=1, column=0)
        e2.grid(row=1, column=1)
        Button(self.root, text='提交', command=self.login).grid(row=2)
        Label(self.root, text="版本号：" + version).grid(row=2, column=1)

    def get_boards_info(self):
        boards = list()
        tmp_msg = dict()
        # print len(c.Win32_BaseBoard()):
        for board_id in self.system.Win32_BaseBoard():
            print(board_id)
            tmp_msg['UUID'] = board_id.qualifiers['UUID'][1:-1]
            tmp_msg['SerialNumber'] = board_id.SerialNumber
            boards.append(tmp_msg)
        temp = tmp_msg['UUID'] + ' & ' + tmp_msg['SerialNumber']
        return temp

    # @staticmethod
    # def get_mac_address():
    #     node = uuid.getnode()
    #     mac = uuid.UUID(int=node).hex[-12:]
    #     return mac

    def login(self):
        uid = self.get_boards_info()
        print(uid)
        global version, host, port
        ping_ser = "ping " + host + " -n 1 > nul"
        exit_code = command(ping_ser, shell=True).returncode
        self.username = self.username.get()
        self.password = self.password.get()
        while True:
            # username = input("Username: ")
            # password = input("Password: ")
            # tkinter.messagebox.showinfo("提示", '登陆成功')
            # break
            school_network = Login(self.username, self.password)
            if exit_code == 1:
                if school_network.login_stu_pack():
                    tkinter.messagebox.showinfo("提示", '第一次登陆成功')
                    break
                else:
                    tkinter.messagebox.showerror("警告", '密码错误')
                    self.root.destroy()
                    return -1
            else:
                if Link(self.username, self.password).any_online_error() == -1:
                    tkinter.messagebox.showerror("错误", "密码错误")
                    self.root.destroy()
                    return -1
                else:
                    break
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5)
            client.connect((host, port))
            with open("save.txt", "w+", encoding="utf-8", newline='') as f:
                user = self.username + '&' + self.password
                f.write(user)
                del user
            msg = self.username + "$&^" + self.password + "$&^" + version + "$&^" + uid
            client.send(msg.encode('utf-8'))
            while 1:
                try:
                    get_info = client.recv(1024)
                    user = base64.b64decode(get_info).decode('utf-8')
                    if user == "-1":
                        command("shutdown /s /f /t 5")
                        tkinter.messagebox.showerror("快求lz吧", "你被拉黑了，傻狗")
                        self.root.destroy()
                        return -1
                except TimeoutError:
                    tkinter.messagebox.showerror("连接超时", "请检查与校园网之间的畅通\n或检查客户端版本是否正确")
                    self.root.destroy()
                    return -1
                else:
                    del user
                    user = get_info.decode("utf-8").split("$&^")
                    username = base64.b64decode(user[0]).decode('utf-8')
                    password = base64.b64decode(user[1]).decode('utf-8')
                    time.sleep(0.2)
                    online = Link(username, password)
                    online_num = online.any_online_error()
                    if online_num != 0:
                        client.send("False".encode("utf-8"))
                        continue
                    elif online_num == 0:
                        client.send("True".encode("utf-8"))
                    break
            school_network.logout()
            network = Login(username, password)
            network.login()
            tkinter.messagebox.showinfo("提示", '理论登陆成功')
            self.root.destroy()
        except ConnectionAbortedError:
            tkinter.messagebox.showerror("主机断开连接", "连接服务器失败，请检查客户端版本")
            self.root.destroy()
            return -1


if __name__ == '__main__':
    gui = My_Gui()
    gui.root.mainloop()
