import requests.utils


class Link:
    def __init__(self, username, password):
        self.data = {
            'name': username,
            'password': password
        }
        self.header = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; PCRT00 Build/N2G48H; wv) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Version/4.0 Chrome/68.0.3440.70 Mobile Safari/537.36",
            "X-Requested-With": "com.android.browser"
        }

    @staticmethod
    def is_error_psd(page):
        if page.text.find("用户不存在或") != -1:
            return True

    def get_online_page_error(self):
        sion = requests.session()
        page = sion.post("http://172.30.0.2:8080/selfservice/module/scgroup/web/login_judge.jsf",
                         headers=self.header, data=self.data)
        if self.is_error_psd(page):
            return False
        page = sion.get("http://172.30.0.2:8080/selfservice/module/webcontent/web/onlinedevice_list.jsf",
                        headers=self.header)
        return page

    def any_online_error(self):
        page = self.get_online_page_error()
        if not page:
            return -1
        online_user = page.text.count("上线时间")
        return online_user

    def get_online_page(self):
        sion = requests.session()
        sion.post("http://172.30.0.2:8080/selfservice/module/scgroup/web/login_judge.jsf",
                  headers=self.header, data=self.data)
        page = sion.get("http://172.30.0.2:8080/selfservice/module/webcontent/web/onlinedevice_list.jsf",
                        headers=self.header)
        return page

    def any_online(self):
        page = self.get_online_page()
        if not page:
            return -1
        online_user = page.text.count("上线时间")
        return online_user
