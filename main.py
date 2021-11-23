import socket
import base64
from link import Link
# import time
from login import Login
from tkinter import *
import tkinter.messagebox


class My_Gui:
    def __init__(self):
        self.root = Tk()
        self.root.title("校园网认证")
        self.root.wm_attributes("-alpha", 1.0)
        self.root.wm_attributes("-topmost", True)
        self.password = StringVar()
        self.username = StringVar()
        self.main_window()

    def main_window(self):
        Label(self.root, text="用户名").grid(row=0, column=0)
        Entry(self.root, textvariable=self.username).grid(row=1, column=0)
        Label(self.root, text="密码").grid(row=0, column=1)
        Entry(self.root, textvariable=self.password).grid(row=1, column=1)
        Button(self.root, text='提交', command=self.login).grid(row=2)

    def login(self):
        self.username = self.username.get()
        self.password = self.password.get()
        while True:
            # username = input("Username: ")
            # password = input("Password: ")
            # tkinter.messagebox.showinfo("提示", '登陆成功')
            # break
            school_network = Login(self.username, self.password)
            if school_network.login_stu_pack():
                tkinter.messagebox.showinfo("提示", '第一次登陆成功')
                break
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = '127.0.0.1'
        port = 12345
        client.connect((host, port))
        msg = "['" + self.username + "','" + self.password + "']"
        client.send(msg.encode('utf-8'))
        while 1:
            num = 0
            password = None
            username = None
            while num < 2:
                if num == 0:
                    username = base64.b64decode(client.recv(1024)).decode('utf-8')
                elif num == 1:
                    password = base64.b64decode(client.recv(1024)).decode('utf-8')
                num += 1
            if password is None or username is None:
                continue
            else:
                online = Link(username, password)
                online_num = online.any_online_error()
                if online_num != -1:
                    client.send("False".encode("utf-8"))
                    continue
                elif online_num == 0:
                    client.send("True".encode("utf-8"))
                client.close()
                break
        school_network.logout()
        network = Login(username, password)
        network.login()
        tkinter.messagebox.showinfo("提示", '理论登陆成功')


if __name__ == '__main__':
    gui = My_Gui()
    gui.root.mainloop()
