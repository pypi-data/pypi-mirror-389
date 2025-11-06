import json
import hashlib
import requests

def login(username:str, password:str, proxy_server:str=None):
    def md5_encrypt(text):
        """MD5加密函数"""
        # 创建md5对象
        md5 = hashlib.md5()
        # 更新加密内容（需要先编码为bytes）
        md5.update(text.encode('utf-8'))
        # 返回32位十六进制字符串
        return md5.hexdigest()

    cookies = {
    }

    headers = {
        'accept': 'application/json',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'no-cache',
        'client': 'pc-web;pro',
        'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'dataid': '2',
        'origin': 'https://www.qyyjt.cn',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://www.qyyjt.cn/user/login',
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'system': 'new',
        'system1': 'Macintosh; Intel Mac OS X 10_15_7;Chrome;140.0.0.0',
        'terminal': 'pc-web;pro',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
    }

    params = {
        '_t': '2',
    }

    data = {
        'phone': username,
        'password': md5_encrypt(password),
    }

    url = f'{proxy_server}/getData.action' if proxy_server else 'https://www.qyyjt.cn/getData.action'

    response = requests.post(url, params=params, cookies=cookies, headers=headers, data=data)
    resp_json = json.loads(response.content)

    return {
        "accessToken": resp_json.get("data").get("token").get("accessToken"),
        "user": resp_json.get("data").get("basic_info").get("user"),
        "resp_json": resp_json
    }