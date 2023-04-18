import socket
import base64
import subprocess

from link import Link
import time
from subprocess import run as command
from login import Login


version = "v1"
host = '127.0.0.1'
port = 12345


def login():
    global version, host, port
    ping_ser = "ping " + host + " -n 2"
    exit_code = command(ping_ser, stdout=subprocess.PIPE, shell=True).returncode
    while True:
        username = input("Username: ")
        password = input("Password: ")
        # tkinter.messagebox.showinfo("提示", '登陆成功')
        # break
        school_network = Login(username, password)
        if exit_code:
            if school_network.login_stu_pack():
                print("提示", '第一次登陆成功')
                break
        else:
            if Link(username, password).any_online_error() == -1:
                print("错误", "密码错误")
                return -1
            break
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(5)
    client.connect((host, port))
    msg = "['" + username + "','" + password + "']"
    time.sleep(0.2)
    client.send(msg.encode('utf-8'))
    time.sleep(0.3)
    client.send(version.encode('utf-8'))
    while 1:
        try:
            username = base64.b64decode(client.recv(1024)).decode('utf-8')
        except ConnectionAbortedError:
            print("连接服务器失败，请检查客户端版本")
            return -1
        except TimeoutError:
            print("连接超时，请检查与校园网之间的畅通\n或检查客户端版本是否正确")
        password = base64.b64decode(client.recv(1024)).decode('utf-8')
        if password is None or username is None:
            continue
        else:
            print(username, password)
            online = Link(username, password)
            online_num = online.any_online_error()
            if online_num != 0:
                time.sleep(0.2)
                client.send("False".encode("utf-8"))
                continue
            elif online_num == 0:
                time.sleep(0.2)
                client.send("True".encode("utf-8"))
            break
    # school_network.logout()
    # network = Login(username, password)
    # network.login()
    print("提示", '理论登陆成功')


if __name__ == '__main__':
    login()
