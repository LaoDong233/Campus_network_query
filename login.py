import requests.utils
import requests.sessions
from PIL import Image
import pytesseract
from cnocr import CnOcr


class Login:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.services_choice = {
            "移动pppoe": "%E7%A7%BB%E5%8A%A8pppoe",
            "电信专线": "%E8%81%94%E9%80%9A%E4%B8%93%E7%BA%BF",
            "联通专线": "%E7%94%B5%E4%BF%A1%E4%B8%93%E7%BA%BF"
        }
        self.services = None
        self.url1 = "http://172.30.0.11/"
        self.url2 = "http://123.123.123.123/"
        self.send_cookie = None
        self.cookie = None
        self.query_string = None
        self.userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko" \
                         ") Chrome/89.0.4389.90 Safari/537.36 Edg/89.0.774.54"
        self.post_url = "http://172.30.0.11/eportal/InterFace.do?method=login"
        self.validcode = ""
        self.validcodeurl = ''

    def get_send_cookie(self):
        session = requests.session()
        session.get(self.url1)
        requests.utils.dict_from_cookiejar(session.cookies)
        self.send_cookie = session.cookies['JSESSIONID']

    def get_query_string(self):
        back = requests.get(self.url2)
        query_string = back.text
        st = query_string.find("index.jsp?") + 10
        end = query_string.find("'</script>")
        self.query_string = query_string[st:end]

    def check_service(self):
        post_header = {
            "Host": "172.30.0.11",
            "Content-Length": "20",
            "User-Agent": self.userAgent,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        post_data = {
            "username": self.username
        }
        page = requests.post("http://172.30.0.11/eportal/userV2.do?method=getServices",
                             headers=post_header, data=post_data)
        for name, ser in self.services_choice.items():
            if page.text.find(name):
                self.services = ser

    def is_valid(self):
        post_header = {
            "Host": "172.30.0.11",
            "Connection": "keep-alive",
            "Origin": "172.30.0.11",
            'User-Agent': self.userAgent,
            "Cookie": "EPORTAL_COOKIE_USERNAME="+self.username+"; EPORTAL_COOKIE_PASSWORD="
                      + self.password+"; EPORTAL_COOKIE_SERVER="+self.services+"; EPORTAL_COOKIE_SERVER_NAME="
                      + self.services+" JESSIONID="+self.send_cookie+"; JSESSIONID="+self.send_cookie
        }
        post_data = {
            "queryString": self.query_string
        }
        page = requests.post("http://172.30.0.11/eportal/InterFace.do?method=pageInfo",
                             data=post_data, headers=post_header)
        if page.text.find('"validCodeUrl":""') == -1:
            st = page.text.find('"validCodeUrl":"') + 17
            end = page.text.find('","loginText"')
            self.validcodeurl = self.url1 + page.text[st:end]
            return True

    def get_valid(self):
        get_header = {
            "Host": "172.30.0.11",
            "Connection": "keep-alive",
            "Origin": "172.30.0.11",
            'User-Agent': self.userAgent,
            "Cookie": "EPORTAL_COOKIE_USERNAME="+self.username+"; EPORTAL_COOKIE_PASSWORD="
                      + self.password+"; EPORTAL_COOKIE_SERVER="+self.services+"; EPORTAL_COOKIE_SERVER_NAME="
                      + self.services+" JESSIONID="+self.send_cookie+"; JSESSIONID="+self.send_cookie
        }
        page = requests.get(self.validcodeurl, headers=get_header)
        with open("validcode.png", "wb") as f:
            f.write(page.content)

    def get_valid_code(self):
        while 1:
            self.get_valid()
            # 两款ocr切换开关，False为使用cnocr，True使用tesseract ocr
            # noinspection PyUnreachableCode
            if False:
                img = Image.open('validcode.png')
                text = pytesseract.image_to_string(img, lang='eng')
                if not len(text) == 1:
                    self.validcode = text[:4]
                    print(text[:4])
                    break
            else:
                ocr = CnOcr()
                img = "validcode.png"
                res = ocr.ocr_for_single_line(img)
                if len(res[0]) == 4:
                    self.validcode = ''.join(res[0])
                    break

    def login_pack(self):
        post_header = {
            "Host": "172.30.0.11",
            "Connection": "keep-alive",
            "Content-Length": "926",
            "Origin": "172.30.0.11",
            'User-Agent': self.userAgent,
            "Cookie": "EPORTAL_COOKIE_USERNAME="+self.username+"; EPORTAL_COOKIE_PASSWORD="
                      + self.password+"; EPORTAL_COOKIE_SERVER="+self.services+"; EPORTAL_COOKIE_SERVER_NAME="
                      + self.services+" JESSIONID="+self.send_cookie+"; JSESSIONID="+self.send_cookie
        }
        post_data = {
            "userId": self.username,
            "password": self.password,
            "service": self.services,
            "queryString": self.query_string,
            "operatorPwd": "",
            "operatorUserId": "",
            "validcode": self.validcode
        }
        print('使用Cookie: ' + post_header["Cookie"])
        response_res = requests.post(self.post_url, data=post_data, headers=post_header)
        response_res.encoding = "utf-8"
        repack = response_res.json()
        if repack["message"] != "":
            print(repack["message"])
            if repack["message"].count("您的账户已欠费"):
                return True
        else:
            if repack["result"] == "success":
                print("理论上登录成功了")
            else:
                print("没有登录成功，但没有网络，没办法提醒")

    def login(self):
        self.get_send_cookie()
        self.get_query_string()
        self.check_service()
        if self.is_valid():
            self.get_valid_code()
        if self.login_pack():
            print("登录失败")
            return True


if __name__ == '__main__':
    a = Login("20105010494", "170011")
    a.login()
