import requests
import json


def multipleSearch(keyword:str, accessToken:str, user:str, proxy_server:str=None):
    cookies = {
    }

    headers = {
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'no-cache',
        'client': 'pc-web;pro',
        'pcuss': accessToken,
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://www.qyyjt.cn/',
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'system': 'new',
        'system1': 'Macintosh; Intel Mac OS X 10_15_7;Chrome;140.0.0.0',
        'terminal': 'pc-web;pro',
        'user': user,
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'ver': '20250918',
        # 'x-request-id': 'PuAn0gqHG6dDSUdWeDT3l',
        'x-request-url': '%2F',
        # 'cookie': 'HWWAFSESID=825a073f813c64a11e; HWWAFSESTIME=1758598050538',
    }

    params = {
        'pagesize': '15',
        'skip': '0',
        'text': keyword,
        'type': '1',
        'template': 'listNoLabel',
        'source': '',
        'isRelationSearch': '0',
    }

    url = f'{proxy_server}/finchinaAPP/v1/finchina-search/v1/multipleSearch' if proxy_server else 'https://www.qyyjt.cn/finchinaAPP/v1/finchina-search/v1/multipleSearch'

    response = requests.get(
        url,
        params=params,
        cookies=cookies,
        headers=headers,
    )

    return json.loads(response.content)
