import base64
import socket
import sys
import time
import json
import tkinter.messagebox
from subprocess import run as command
from tkinter import *
from tkinter import simpledialog
import platform
import hashlib
import random

# import uuid

import machineid

from link import Link
from login import Login

version = "Release 1.0.0"
host = '127.0.0.1'
port = 7788
save_username = ""
save_password = ""
save_push_deer_id = ""
save_ding_id = ""
save_ding_key = ""
first_open = True

closing_remarks = ("尊敬的各位用户："
                "\n我是这个软件的开发者，一位2020级的学生。当你看到这条消息时，我已经临近毕业"
                "\n这个软件的维护周期也即将停止，我会尝试将这个项目转交给下一个人，我也不知道交接是否能够成功"
                "\n这个项目，从2021年开始，陪着大家走过了两个年头。在这两个年头里，软件至少迎来了13个版本更新"
                "\n这些更新，让这个软件的体系更加完善，机制也更加完整。"
                "\n我也通过这个小项目受益匪，在这即将毕业之际，我要感谢各位用户，使用我的这个软件，并提交各种反馈"
                "\n正是因为有了这些反馈，我的软件才能从最开始的一个单机的小黑窗，主键发展成现在三段分离，有着半成熟数据库，图形UI的体系。"
                "\n最后，在这里，我还是再次感谢各位用户。在我离开这个学校之前，我会继续维护这个软件的运营"
                "\n祝大家前程似锦，我们有机会，江湖再见。")

if True:
    # 初始化获取管理员权限
    if platform.system() == 'Windows':
        import ctypes
    

        def is_admin():
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except:
                return False


        if not is_admin():
            # 如果当前操作系统为Windows，且不是管理员，则使用ctypes.windll.shell32.ShellExecuteW()函数以管理员身份重新启动程序
            params = f'"{sys.executable}" "{__file__}"'
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
            sys.exit()

if platform.system() == 'Windows':
    import win32com.client


def enable_firewall():
    if platform.system() == 'Windows':
        fw_manager = win32com.client.Dispatch('HNetCfg.FwMgr')
        fw_policy = fw_manager.LocalPolicy.CurrentProfile

        if not fw_policy.FirewallEnabled:
            print('防火墙未开启，正在开启...')
            fw_policy.FirewallEnabled = True
            print('防火墙已开启')
        else:
            print('防火墙已开启')


def del_firewall():
    if platform.system() == 'Windows':

        # 创建 FwPolicy2 对象
        fw_policy = win32com.client.Dispatch("HNetCfg.FwPolicy2")

        # 获取防火墙策略中所有的规则对象
        fw_rules = fw_policy.Rules

        # 遍历所有规则，查找符合条件的规则
        for fw_rule in fw_rules:
            if fw_rule.Protocol == 6 and fw_rule.RemotePorts == "8080" \
                    and fw_rule.RemoteAddresses.find("172.30.0.2") != -1:
                # 如果找到了符合条件的规则，则将其从防火墙策略中删除
                print(f"删除了防火墙规则{fw_rule.Name}")
                fw_rules.Remove(fw_rule.Name)


def add_firewall():
    for i in range(1):
        if platform.system() == 'Windows':
            # 创建 FwPolicy2 对象
            fw_policy = win32com.client.Dispatch("HNetCfg.FwPolicy2")
            name = hashlib.md5()
            name.update(str(random.random()).encode("utf-8"))
            # 创建新规则
            fw_rule = win32com.client.Dispatch("HNetCfg.FWRule")
            fw_rule.Name = name.hexdigest()
            fw_rule.Grouping = ""
            fw_rule.Protocol = 6
            fw_rule.Direction = 2  # 1为入站规则，2为出站规则
            fw_rule.Action = 0  # 0为阻止，1为允许
            fw_rule.RemoteAddresses = "172.30.0.2"
            fw_rule.RemotePorts = "8080"
            fw_rule.Enabled = True

            # 添加规则到防火墙策略
            fw_rules = fw_policy.Rules
            fw_rules.Add(fw_rule)


def load():
    global save_username, save_password, save_push_deer_id, save_ding_id, save_ding_key, first_open
    # noinspection PyBroadException
    try:
        with open(file="config.json", mode='r', encoding='utf-8') as f:
            config = json.load(f)
            save_username = config['username']
            save_password = config['password']
            # save_push_deer_id = config['push_deer_id']
            save_ding_id = config["ding_id"]
            save_ding_key = config["ding_key"]
            first_open = config["first_open"]
            print(config)
    except json.decoder.JSONDecodeError:
        pass
    except FileNotFoundError:
        pass
    except:
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
        # self.push_deer_id = StringVar()
        self.ding_id = StringVar()
        self.ding_key = StringVar()
        self.root.resizable(False, False)
        self.main_window()
        self.closing_remarks()
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
        # Label(self.root, text="从PushDeer获取的秘钥").grid(row=3, column=0)
        Label(self.root, text="第一个空填写钉钉机器人ID，第二个填写key").grid(row=3, column=0)
        Label(self.root, text="具体教程见下载地址里的视频").grid(row=3, column=1)
        # e3 = Entry(self.root, textvariable=self.push_deer_id)
        # e3.grid(row=4, column=0, columnspan=2)
        # e3.insert(0, save_push_deer_id)
        e3 = Entry(self.root, textvariable=self.ding_id)
        e3.grid(row=4, column=0)
        e3.insert(0, save_ding_id)
        e3 = Entry(self.root, textvariable=self.ding_key)
        e3.grid(row=4, column=1)
        e3.insert(0, save_ding_key)

    @staticmethod
    def closing_remarks():
        global first_open
        if first_open:
            tkinter.messagebox.showinfo("完结感言", closing_remarks)
            with open("readme.txt", "w", encoding="utf-8") as f:
                f.write(closing_remarks + "\n\nQQ群号：511358840\n点击链接加入群聊【FSN】：https://jq.qq.com/?_wv=1027&k=Q6rNIq9F")
            first_open = False

    # @staticmethod
    # def get_mac_address():
    #     node = uuid.getnode()
    #     mac = uuid.UUID(int=node).hex[-12:]
    #     return mac

    # def ver_key(self):
    # +y(self.ver_window, textvariable=self.key).grid(row=0, column=1)

    def save(self):
        global first_open
        datas = {
            "username": str(self.username),
            "password": str(self.password),
            "ding_id": str(self.ding_id),
            "ding_key": str(self.ding_key),
            "first_open": first_open
        }
        with open(file="config.json", mode="w", encoding="utf-8") as f:
            f.write(json.dumps(obj=datas, indent=2, ensure_ascii=False, separators=(',', ': ')))

    def login(self):
        # noinspection PyBroadException
        try:
            enable_firewall()
            del_firewall()
            uid = machineid.id()
            global version, host, port
            ping_ser = "ping " + host + " -n 1 > nul"
            exit_code = command(ping_ser, shell=True).returncode
            self.username = self.username.get()
            self.password = self.password.get()
            self.ding_id = self.ding_id.get()
            self.ding_key = self.ding_key.get()
            # self.push_deer_id = self.push_deer_id.get()
            ding_talk = f"{self.ding_key}@{self.ding_id}"
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
                msg = self.username + "$&^" + self.password + "$&^" + version + "$&^" + uid + "$&^" + ding_talk
                client.send(msg.encode('utf-8'))
                while 1:
                    try:
                        get_info = client.recv(1024)
                        user = base64.b64decode(get_info).decode('utf-8')
                        print(user)
                        if user == "-1":
                            tkinter.messagebox.showwarning("封禁", "您的账号被管理员或自动风控封禁\n请联系管理员，请勿登录其他账号，防止连坐封禁")
                            self.root.destroy()
                            return -1
                        elif user == "-200":
                            self.key = simpledialog.askstring(title='验证码', prompt='请输入验证码')
                            client.send(self.key.upper().encode('utf-8'))
                            get_info = client.recv(1024)
                            print(user)
                        elif user == "-10":
                            tkinter.messagebox.showerror("版本错误", "请进行版本更新")
                            self.root.destroy()
                            return -1
                    except TimeoutError:
                        tkinter.messagebox.showerror("连接超时", "请检查与校园网之间的畅通\n或检查客户端版本是否正确")
                        self.root.destroy()
                        return -1
                    else:
                        del user
                        user = get_info.decode("utf-8")
                        if base64.b64decode(user).decode("utf-8") == "-100":
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
                add_firewall()
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
        except FileNotFoundError:
            sys.exit()
        except:
            sys.exit()


if __name__ == '__main__':
    gui = My_Gui()
    gui.root.mainloop()
