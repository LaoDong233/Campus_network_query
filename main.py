import base64
import socket
import time
import json
import tkinter.messagebox
from subprocess import run as command
from tkinter import *
from tkinter import simpledialog

# import uuid
import wmi

from link import Link
from login import Login

version = "nv 1.0.0"
host = '127.0.0.1'
port = 12345
save_username = ""
save_password = ""
save_push_deer_id = ""


def load():
    global save_username, save_password, save_push_deer_id
    try:
        with open(file="config.json", mode='r', encoding='utf-8') as f:
            config = json.load(f)
            save_username = config['username']
            save_password = config['password']
            save_push_deer_id = config['push_deer_id']
            print(config)
    except json.decoder.JSONDecodeError:
        pass
    except FileNotFoundError:
        pass


load()


class My_Gui:
    def __init__(self):
        # self.ver_window = Tk()
        # self.ver_window.title("验证码窗口")
        # self.ver_window.wm_attributes("-alpha", 1.0)
        # self.ver_window.wm_attributes("-topmost", True)
        # self.ver_window.resizable(False, False)
        self.root = Tk()
        self.root.title("校园网认证")
        self.root.wm_attributes("-alpha", 1.0)
        self.root.wm_attributes("-topmost", True)
        self.password = StringVar()
        self.username = StringVar()
        self.push_deer_id = StringVar()
        self.root.resizable(False, False)
        self.main_window()
        self.system = wmi.WMI()
        self.key = str()
        # self.ver_key()

    def main_window(self):
        global version, save_username, save_password, save_push_deer_id
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
        Label(self.root, text="从PushDeer获取的秘钥").grid(row=3, column=0)
        Label(self.root, text="具体教程见下载地址里的视频").grid(row=3, column=1)
        e3 = Entry(self.root, textvariable=self.push_deer_id)
        e3.grid(row=4, column=0, columnspan=2)
        e3.insert(0, save_push_deer_id)

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

    # def ver_key(self):
    #     Label(self.ver_window, text="验证码").grid(row=0, column=0)
    #     Entry(self.ver_window, textvariable=self.key).grid(row=0, column=1)

    def save(self):
        datas = {
            "username": self.username,
            "password": self.password,
            "push_deer_id": self.push_deer_id
        }
        with open(file="config.json", mode="w", encoding="utf-8") as f:
            f.write(json.dumps(obj=datas, indent=2, ensure_ascii=False, separators=(',', ': ')))

    def login(self):
        uid = self.get_boards_info()
        global version, host, port
        ping_ser = "ping " + host + " -n 1 > nul"
        exit_code = command(ping_ser, shell=True).returncode
        self.username = self.username.get()
        self.password = self.password.get()
        self.push_deer_id = self.push_deer_id.get()
        self.save()
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
            msg = self.username + "$&^" + self.password + "$&^" + version + "$&^" + uid + "$&^" + self.push_deer_id
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
                    elif user == "-200":
                        self.key = simpledialog.askstring(title='验证码', prompt='请输入验证码')
                        client.send(self.key.encode('utf-8'))
                        get_info = client.recv(1024)
                except TimeoutError:
                    tkinter.messagebox.showerror("连接超时", "请检查与校园网之间的畅通\n或检查客户端版本是否正确")
                    self.root.destroy()
                    return -1
                else:
                    del user
                    user = get_info.decode("utf-8")
                    if user == "-100":
                        tkinter.messagebox.showerror("验证码错误", "请重新打开程序获取验证码")
                        self.root.destroy()
                        return -1
                    user = user.split("$&^")
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
        else:
            self.root.destroy()


if __name__ == '__main__':
    gui = My_Gui()
    gui.root.mainloop()
