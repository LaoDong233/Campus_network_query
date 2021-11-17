import requests.utils


class Link:
    def __init__(self, link, username, password):
        self.data = {
            'name': username,
            'password': password
        }
        self.link = link
        self.login = "module/scgroup/web/login_judge.jsf"
        self.query = "module/webcontent/web/onlinedevice_list.jsf"
        self.header = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; PCRT00 Build/N2G48H; wv) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Version/4.0 Chrome/68.0.3440.70 Mobile Safari/537.36",
            "X-Requested-With": "com.android.browser"
        }

    def get_online_page(self):
        sion = requests.session()
        sion.post(self.link+self.login,
                  headers=self.header, data=self.data)
        page = sion.get(self.link+self.query,
                        headers=self.header)
        return page

    def any_online(self):
        page = self.get_online_page()
        num = 0
        online_user = 0
        for a in page.text:
            if a == '上':
                num += 1
            elif a == '线' and num == 1:
                num += 1
            elif a != '线' and num == 1:
                num = 0
            elif a == '时' and num == 2:
                num += 1
            elif a != '时' and num == 2:
                num = 0
            elif a == '间' and num == 3:
                num += 1
                online_user += 1
            elif a != '间' and num == 3:
                num = 0
        return online_user
