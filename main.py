import socket
import base64
from link import Link
import time
from login import Login
from tkinter import *
import tkinter.messagebox
from subprocess import run as command


version = "v3"
host = '::1'
port = 12345


class My_Gui:
    def __init__(self):
        self.root = Tk()
        self.root.title("校园网认证")
        self.root.wm_attributes("-alpha", 1.0)
        self.root.wm_attributes("-topmost", True)
        self.password = StringVar()
        self.username = StringVar()
        self.root.resizable(0, 0)
        self.main_window()

    def main_window(self):
        global version
        Label(self.root, text="用户名").grid(row=0, column=0)
        Entry(self.root, textvariable=self.username).grid(row=1, column=0)
        Label(self.root, text="密码").grid(row=0, column=1)
        Entry(self.root, textvariable=self.password, show='*').grid(row=1, column=1)
        Button(self.root, text='提交', command=self.login).grid(row=2)
        Label(self.root, text="版本号：" + version).grid(row=2, column=1)

    def login(self):
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
            msg = "['" + self.username + "','" + self.password + "']"
            time.sleep(0.2)
            client.send(msg.encode('utf-8'))
            time.sleep(1)
            client.send(version.encode('utf-8'))
            while 1:
                try:
                    username = base64.b64decode(client.recv(1024)).decode('utf-8')
                except TimeoutError:
                    tkinter.messagebox.showerror("连接超时", "请检查与校园网之间的畅通\n或检查客户端版本是否正确")
                    self.root.destroy()
                    return -1
                password = base64.b64decode(client.recv(1024)).decode('utf-8')
                if password is None or username is None:
                    continue
                else:
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
