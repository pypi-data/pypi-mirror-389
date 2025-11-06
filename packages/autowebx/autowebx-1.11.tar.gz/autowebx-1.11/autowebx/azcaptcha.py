from time import time

from requests import post, get


class HCaptcha:
    def __init__(self, api_key, site_key, url):
        self.api_key = api_key
        self.site_key = site_key
        response = post(f'https://azcaptcha.com/in.php?key={api_key}&method=hcaptcha&sitekey={site_key}&pageurl={url}&json=1').json()
        if response['status'] == 1:
            self.captcha_id = response['request']
            self.start = time()
        else:
            print(response)
            raise Exception('Error')

    def result(self):
        while time() < self.start + 5: pass
        url = f'https://azcaptcha.com/res.php?key={self.api_key}&action=get&id={self.captcha_id}&json=1'
        response = get(url).json()
        pass


if __name__ == '__main__':
    HCaptcha(
        'jb2x3znkwpdym4pgryjd6fmvtckxqlqb',
        '94a1c95b-2705-49ee-bb7a-d506f95c5603',
        'https://medal.tv/login'
    ).result()