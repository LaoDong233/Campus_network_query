# from link import Link
import base64
# import sys
import os
from typing import Union

import pymysql
import threading
import socket
import time
import apprise
import json
import random
import string

# pushdeer连接不上，暂时更改推送方式为钉钉
# from pypushdeer import PushDeer

"""
并没有写完,数据库结构还可能更改
主动初始化，学艺不精，直接用的全局变量
本项目使用http://www.pushdeer.com/
作为验证码API，门槛较高，但是相对安全
"""
with open("server_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
conn = pymysql.connect(
    host=config['mysql_host'],
    port=config['mysql_port'],
    user=config['mysql_username'],
    password=config['mysql_password'],
    database=config['mysql_database']
)
authorization_code = list(config["authorization_code"].split(","))
teacher_cursor = conn.cursor(pymysql.cursors.DictCursor)
teacher_cursor.execute('''select * from teacher_info''')
user_cursor = conn.cursor()
teacher_change_cursor = conn.cursor()
security_cursor = conn.cursor()
security_android_cursor = conn.cursor()
server_version = config["server_versions"].split("$%^")
server_android_version = config["server_android_version"].split("$%^")
ant_hung = list()
first_time = time.strftime("%Y-%m-%d-%H:%M:%S秒")

"""
防止他人攻击获取教师账号
暂时弃用，待重写
"""


# class Stu(threading.Thread):
#     def __init__(self, socked, add):
#         threading.Thread.__init__(self)
#         self.address = add
#         self.sock = socked
#
#     def run(self):
#         if stu_list.count(self.address) >= 2:
#             self.sock.close()
#         else:
#             stu_list.append(self.address)
#             time.sleep(600)
#             stu_list.remove(self.address)

# 防止冲突，定义一个自定义报错：用户已经被封禁


class UserIsBanned(Exception):
    pass


# 服务器主类
class Server(threading.Thread):
    def __init__(self, socked, add) -> None:
        # 内部变量主动初始化
        threading.Thread.__init__(self)
        self.user_uuid = None
        self.sock = socked
        self.not_ban = False
        self.address = add
        self.username = None
        self.push_key = None
        self.password = None

    # 饿死人攻击风控模块
    # 从下面的模块中分离出来
    # 方便阅读和修改
    def ant_hung(self) -> bool:
        """
        饿死人攻击防范模块
        两分钟内登录三次后执行封号
        :return: 如果触发风控返回True，否则返回False
        """
        global ant_hung
        for i in ant_hung:
            if self.username in i:
                ant = i
                ant_hung.remove(i)
                break
        else:
            ant = [self.username, int(time.time()), 0]
        # 获取次数是否超过三次，如果超过触发风控封禁用户
        print(f'{self.username}登陆了{ant[2]}次，{time.strftime("%Y年%m月%d日%H时%M分%S秒")}')
        if int(time.time()) - ant[1] <= 120 and ant[2] >= 3:
            if self.not_ban is False:
                self.ban_this_user()
                return True
        elif int(time.time()) - ant[1] <= 120:
            ant[2] += 1
        else:
            ant[2] = 0
            ant[1] = int(time.time())
        ant_hung.append(ant)
        return False

    # 获取验证码
    def send_verification_code(self, ver_code: str) -> None:
        print(f'{self.username}的验证码是{ver_code}')
        print(self.push_key)
        pusher = apprise.Apprise()
        pusher.add(f"dingtalk://{self.push_key}")
        pusher.notify(title="Fuck School Network验证码 (试运行)",
                      body=f"{self.username}的验证码为{ver_code}")

    # 验证码生成器
    @staticmethod
    def generate_code(bit_num: int) -> str:
        """
        :param bit_num: 生成验证码位数
        :return: 返回生成的验证码
        """
        all_str = string.printable.split('A')[0]
        val_code = ''.join([random.choice(all_str) for _ in range(bit_num)])

        return val_code

    # 用户状态检查器
    def check_user(self) -> bool:
        """
        用来检测当前服务器中登陆的用户的状态
        :return:
        """
        # 从数据库中读取是否存在这个用户，如果存在则检查用户名和密码是否一致
        # 检查出不一致后替换密码
        conn.ping(reconnect=True)
        if user_cursor.execute(
                '''select * 
                from user_info 
                where username=%s''',
                self.username
        ) == 1:
            if user_cursor.execute(
                    '''select * 
                    from user_info 
                    where username=%s 
                    and password=%s''',
                    (self.username, self.password)
            ) == 0:
                user_cursor.execute(
                    '''update user_info 
                    set password = %s 
                    where username = %s''',
                    (self.password, self.username)
                )
        # 如果数据库中没有这个用户，那么将这个用户存入数据库中
        else:
            user_cursor.execute(
                '''insert into user_info(username, password)
                 VALUE 
                 (%s, %s)''',
                (self.username, self.password)
            )
        print(f'{self.username}封禁状态为{self.check_user_is_banned()}')
        # 判断该用户是否被封禁，如果被封禁返回FALSE
        if self.check_user_is_banned():
            conn.commit()
            return False
        else:
            user_cursor.execute(
                '''update user_info 
                set usage_time = usage_time + 1 
                where username = %s''',
                self.username
            )
            conn.commit()
            return True

    # 简单的时间判断模块，传入一个旧的时间戳，传出是否和当前时间相差24小时
    @staticmethod
    def time_differ_day(org_time: int) -> bool:
        try:
            if int(time.time()) - int(org_time) >= 86400:
                return True
            else:
                return False
        except TypeError:
            return True

    # 网络监测模块，用于记录用户登录时使用的IP地址
    def ver_network(self) -> None:
        conn.ping(reconnect=True)
        # 初始化记忆的地址和数量
        memory_addr = str()
        addr = self.address[0]
        memory_addr_number = 0
        security_cursor.execute(
            '''select address, address_number 
            from user_security 
            where username = %s''',
            self.username
        )
        # 判断该用户是否存在
        if security_cursor.execute(
                '''select address, address_number 
                from user_security 
                where username = %s''',
                self.username
        ) != 0:
            # 将数据库中存储的用户登录IP解包
            memory_info = security_cursor.fetchone()
            memory_addr = memory_info[0]
            memory_addr_number = memory_info[1]
        # 一套奇怪的操作解包并且打包网络数据，并且记录
        # 慢慢看吧，这一块shi我懒得写注释了
        if not memory_addr_number == 0:
            memory_addr = memory_addr.split('$%^')
            if addr not in memory_addr:
                memory_addr_number += 1
                old_memory = memory_addr
                memory_addr = ""
                for i in range(len(old_memory)):
                    if i != 0:
                        memory_addr = memory_addr + "$%^" + old_memory[i]
                    else:
                        memory_addr = old_memory[i]
                else:
                    memory_addr = memory_addr + "$%^" + addr
            else:
                return
        else:
            memory_addr = addr
            memory_addr_number += 1
        # 将上面打好包的IP地址存储进数据库中
        print(memory_addr, memory_addr_number, self.username)
        security_cursor.execute(
            '''update user_security 
            set address = %s, 
            address_number = %s 
            where username = %s''',
            (memory_addr, memory_addr_number, self.username)
        )
        # 提交
        conn.commit()

    # 查询用户是否处于封禁白名单
    def get_user_in_not_ban(self):
        conn.ping(reconnect=True)
        security_cursor.execute('''select ban from user_security where username = %s''', self.username)
        try:
            info = security_cursor.fetchone()[0]
        except TypeError:
            return
        if info == -1:
            self.not_ban = True

    # 封禁用户模块
    def ban_this_user(self) -> None:
        """
        BAN值为-1则是封禁白名单
        :return:
        """
        conn.ping(reconnect=True)
        if self.not_ban:
            return
        security_cursor.execute('''update user_security set ban = 1 where username = %s''', self.username)
        conn.commit()

    # 检查用户是否被封禁模块
    def check_user_is_banned(self) -> bool:
        """
        检查当前线程的用户是否被封禁
        :return: 封禁返回TRUE，否则返回FALSE
        """
        conn.ping(reconnect=True)
        if self.not_ban:
            return False
        security_cursor.execute('''select ban from user_security where username = %s''', self.username)
        try:
            if security_cursor.fetchone()[0] == 1:
                return True
            else:
                return False
        except TypeError:
            return False

    def verification_android(self) -> bool:
        conn.ping(reconnect=True)
        global security_android_cursor
        if security_android_cursor.execute(
                '''select authorization_code from user_android_security where username = %s''', self.username
        ) == 1:
            security_android_cursor.execute(
                '''update user_android_security 
                set authorization_code = %s,
                times = 0 where username = %s''',
                (self.push_key, self.username)
            )
            print(f"已更新安卓用户{self.username}的授权码")
            conn.commit()
        # 未找到用户则在表内添加新用户
        else:
            security_android_cursor.execute(
                '''insert into 
                user_android_security(username, authorization_code) 
                VALUE 
                (%s, %s)''',
                (self.username, self.push_key)
            )
            self.ver_network()
            conn.commit()
        # 更新时间并允许登录
        security_android_cursor.execute(
            '''update user_android_security set times = %s where username = %s''',
            (int(time.time()), self.username)
        )
        self.ver_network()
        login = True
        return login

    def save_user_driver_id(self):
        conn.ping(reconnect=True)
        security_cursor.execute(
            """select user_uuid from user_security where username = %s""", self.username)
        user_uuid = security_cursor.fetchone()[0]
        if user_uuid is None:
            self.user_uuid = f"{self.user_uuid}$&^"
        else:
            for i in user_uuid.split("$&"):
                if i == self.user_uuid:
                    return None
            else:
                self.user_uuid = user_uuid + f"{self.user_uuid}$&^"
        security_cursor.execute(
            """update user_security set user_uuid = %s where username = %s""",
            (self.user_uuid, self.username)
        )
        conn.commit()

    # 验证码验证模块
    def verification_code(self, is_android) -> Union[bool, int]:
        """
        从外部获取一个PushDeer的key并传入，在内部进行存储并且进行发包
        :return: TRUE成功，FALSE失败
        """
        conn.ping(reconnect=True)
        """
        弃用，重写新方法
        # 防范饿死人攻击
        # 饿死人攻击：疯狂给服务器发送请求包来获取大量的用户数据
        # 数据模板：ant = [self.username, int(time.time()), 0]
        # 从饿死人攻击列表中寻找用户，如果这个用户存在，那么把用户取出并删除，否则创建新用户
        for i in ant_hung:
            if self.username in i:
                ant = i
                ant_hung.remove(i)
                break
        else:
            ant = [self.username, int(time.time()), 0]
        # 获取次数是否超过三次，如果超过触发风控封禁用户
        if ant[1] - int(time.time()) <= 120 and ant[2] >= 3:
            if self.not_ban is False:
                self.ban_this_user()
                return False
        elif ant[1] - int(time.time()) <= 120:
            ant[2] += 1
        elif ant[1] - int(time.time()) <= 120:
            ant[2] = 0
            ant[1] = int(time.time())
        ant_hung.append(ant)
        """
        # 新地防饿死人攻击方法
        if self.ant_hung():
            return False
        # 根据传入的是否为安卓键入安卓核验方法
        if is_android:
            return self.verification_android()
        # 将获取来的key存入类全局方便调用
        # 寻找用户，并对比用户的key是否相同
        if security_cursor.execute(
                '''select PushDeer_id, times 
                from user_security 
                where username = %s''', self.username
        ) == 1:
            usr_security = security_cursor.fetchone()
            # 如果两次key相同则判断距离上次登录是否超过一天，如果未超过直接返回TRUE
            if self.push_key == usr_security[0]:
                if not self.time_differ_day(usr_security[1]):
                    self.ver_network()
                    return True
            # 两次key不同时将用户的key变更为最新key，并且将用户的changes_times+1，用于风控
            else:
                security_cursor.execute(
                    '''update user_security 
                    set changes_times = changes_times + 1 ,
                    PushDeer_id = %s,
                    times = 0 where username = %s''',
                    (self.push_key, self.username)
                )
                print(f'{self.username}已变更key')
                conn.commit()
        # 未找到用户则在表内添加新用户
        else:
            security_cursor.execute(
                '''insert into 
                user_security(username, PushDeer_id) 
                VALUE 
                (%s, %s)''',
                (self.username, self.push_key)
            )
            self.ver_network()
            conn.commit()
        # 生成并发送验证码
        ver = self.generate_code(6).upper()
        self.sock.send(base64.b64encode("-200".encode('utf-8')))
        self.send_verification_code(ver)
        self.sock.settimeout(120)
        try:
            recode = self.sock.recv(1024).decode('utf-8')
        except socket.timeout:
            self.sock.close()
            return False
        if not recode == ver:
            print(recode)
            self.sock.send(base64.b64encode("-100".encode('utf-8')))
            login = False
        else:
            login = True
            security_cursor.execute(
                '''update user_security 
                set times = %s 
                where username = %s''',
                (int(time.time()), self.username)
            )
            conn.commit()
        self.ver_network()
        self.check_verification_banned()
        conn.commit()
        return login

    # 检查用户是否key变更次数过多模块
    def check_verification_banned(self) -> None:
        """
        检测用户是否频繁变更自己的认证key，如果变更次数超过四次直接封禁
        :return:
        """
        conn.ping(reconnect=True)
        security_cursor.execute('''select changes_times from user_security where username = %s''', self.username)
        if int(security_cursor.fetchone()[0]) >= 3:
            self.ban_this_user()

    # 账户获取模块，用来返回字典
    # noinspection PyTypeChecker
    @staticmethod
    def get_teacher() -> dict:
        """
        获取一个教师账户
        :return: 返回一个字典
        """
        conn.ping(reconnect=True)
        user = teacher_cursor.fetchone()
        if user['id'] == 291:
            teacher_cursor.execute('''select * from teacher_info''')
        teacher_change_cursor.execute(
            '''update teacher_info 
            set usage_time = usage_time + 1 
            where id = %s''', user['id']
        )
        conn.commit()
        return user

    # 登录记录模块，用来记录用户上次使用的账户
    def log_user_log(self, user: dict) -> None:
        """
        传入一个账户，用户名记录到当前用户的last_use字段中
        :param user: 上个方法获取的用户字典
        :return: None
        """
        conn.ping(reconnect=True)
        user_cursor.execute(
            '''update user_info 
            set last_use = %s 
            where username = %s''',
            (user['username'], self.username)
        )
        conn.commit()

    # 记录登录错误
    @staticmethod
    def log_teacher_error(user: dict) -> None:
        """
        如果客户端返回用户无法使用，则将其记录
        :param user: 上方函数获取的用户字典
        :return:
        """
        conn.ping(reconnect=True)
        teacher_change_cursor.execute(
            '''update teacher_info
            set error_time = error_time + 1
            where username = %s''', user['username']
        )

    def run(self) -> int:
        # 引用防御机制，老版本机制，已弃用
        # is_dos = Stu(self.sock, self.address[0])
        # 从客户端接收数据包，存储到msg里面，客户端数据使用$&^分割
        msg = self.sock.recv(1024).decode('utf-8')
        msg = msg.split("$&^")
        # 尝试解包，用于排除不同的包的客户端
        try:
            try:
                stu_usr = [msg[0], msg[1]]
            except IndexError:
                print(msg, "用户正在使用早期版本")
                self.sock.close()
                return -1
            self.username = msg[0]
            self.password = msg[1]
            version = msg[2]
            self.user_uuid = msg[3]
            self.push_key = msg[4]
            # 获取用户设备信息，暂时弃用，待重写
            # user_cpu_id = msg[3]
            print("%s 正在请求登录" % stu_usr)
            self.get_user_in_not_ban()
            # 与数据库进行比对，比对是否有相同用户，如果有的话则允许程序继续进行，并且检测用户是否被封禁
            if not self.check_user():
                raise UserIsBanned("该用户%s已被封禁" % msg[0])
            # 将客户端传的版本号与服务器版本号比对，如果不同禁止连接（用于压缩用户数量）
            # 如果不需要也不要删除，这种设计方式对于更新打包算法比较友好
            # 如果需要大用户量可以在设置文件里的Server_Version中添加更多的版本
            # 版本号以$%^分割【我觉得在正常情况下出现这三个符号连用】
            version = str(version)
            global server_version, server_android_version
            if version in server_version:
                is_android = False
            elif version in server_android_version:
                is_android = True
            else:
                print("%s 正在使用过时的客户端" % self.address[0])
                self.sock.send(base64.b64encode("-10".encode("utf-8")))
                self.sock.close()
                return -1
            # 用户数据安全算法，原校验mac等信息，暂时弃用
            # user_cpu_id = str(user_cpu_id)
            # UserLog(stu_usr[0], user_cpu_id).start()
            # 新用户安全算法，调用API发送验证码，存储API作为校验，每天验证一次
            ver_con = self.verification_code(is_android)
            if ver_con is False:
                raise TimeoutError("%s验证码错误" % self.username)
            self.save_user_driver_id()
            while True:
                # print("将%s 分配给%s" % (username, self.address))
                # self.sock.send(base64.b64encode(username.encode("utf-8")))
                # self.sock.send(base64.b64encode(password.encode("utf-8")))
                # self.sock.close()
                # break
                # 老的黑名单算法，已弃用
                # if [stu_usr[0]] in blacklist or user_cpu_id in blacklist:
                #     if [user_cpu_id] not in blacklist:
                #         blacklist.append([user_cpu_id])
                #     if [stu_usr[0]] not in blacklist:
                #         blacklist.append([stu_usr[0]])
                #     print("黑名单中的%s正在请求连接" % stu_usr[0])
                #     self.sock.send(base64.b64encode("-1".encode('utf-8')))
                #     return 0
                # 取得一个权限账户，并且拆包后重新打包发给客户端
                tea_user = self.get_teacher()
                username = tea_user['username']
                password = tea_user['password']
                print("尝试将%s 分配给%s" % (username, self.address))
                user = \
                    base64.b64encode(username.encode("utf-8")) + "$&^".encode("utf-8") + \
                    base64.b64encode(password.encode("utf-8"))
                self.sock.send(user)
                # 等待客户端返回该用户是否可用
                can_use = self.sock.recv(1024).decode('utf-8')
                if eval(can_use):
                    # 如果可用在控制台打印分配成功
                    # 并将最后分配记录下来
                    print("成功将%s 分配给%s" % (username, self.address))
                    # is_dos.start()
                    self.log_user_log(tea_user)
                    self.sock.close()
                    break
                else:
                    # 否则记录一次用户错误
                    self.log_teacher_error(tea_user)
                    continue
        except UserIsBanned:
            # 如果被封禁直接关闭连接
            self.sock.send(base64.b64encode("-1".encode('utf-8')))
            self.sock.close()
            return 0
        except TimeoutError:
            print('%s客户端主动关闭连接' % self.username)
            return 0
        except ValueError:
            print("%s未填写push秘钥" % self.username)


class SqlSave(threading.Thread):
    def __init__(self):
        self.conn = conn
        threading.Thread.__init__(self)

    def run(self):
        global ant_hung
        while 1:
            try:
                a = input(": ")
                if a == '':
                    continue
            except ValueError:
                pass
            else:
                if a == "help":
                    print(
                        "说明：\n"
                        "1：提交事务\n"
                        "2：放弃事务\n"
                        "3: 打印临时列表\n"
                        "e: 退出程序 os._exit(0)"
                    )
                elif a == "1":
                    conn.ping(reconnect=True)
                    conn.commit()
                elif a == "2":
                    conn.ping(reconnect=True)
                    conn.rollback()
                elif a == "3":
                    print(ant_hung)
                elif a == "e":
                    os._exit(0)


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sql_saver = SqlSave()
sql_saver.start()
host = config['host']
port = config['port']
server.bind((host, port))
server.listen(1)
while True:
    sock, address = server.accept()
    print("%s正在请求用户" % str(address))
    thread = Server(sock, address)
    thread.start()

# noinspection PyUnreachableCode
'''
if False:
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
'''
