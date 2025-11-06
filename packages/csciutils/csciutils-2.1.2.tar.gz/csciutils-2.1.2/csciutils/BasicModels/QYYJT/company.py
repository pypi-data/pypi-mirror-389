import requests
import json




def company_info(accessToken:str, user:str, code:str, proxy_server:str=None):

    cookies = {}

    headers = {
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'cache-control': 'no-cache',
        'client': 'pc-web;pro',
        # 'content-length': '0',
        'dataid': '869',
        'origin': 'https://www.qyyjt.cn',
        'pcuss': accessToken,
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        # 'referer': 'https://www.qyyjt.cn/detail/enterprise/overview?code=A733F729FE8B1F5F9834AC0196F76986&type=company',
        'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'system': 'new',
        'system1': 'Macintosh; Intel Mac OS X 10_15_7;Chrome;141.0.0.0',
        'terminal': 'pc-web;pro',
        'user': user,
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        # 'ver': '20251022',
        # 'x-request-id': 'Mu-xTife8zPUc-ksJxFsS',
        # 'x-request-url': '%2Fdetail%2Fenterprise%2Foverview%3Fcode%3DA733F729FE8B1F5F9834AC0196F76986%26type%3Dcompany%23%25E4%25BC%2581%25E4%25B8%259A%25E9%2580%259F%25E8%25A7%2588',
        # 'cookie': 'HWWAFSESID=d746b733c1d53f0914; HWWAFSESTIME=1760513620484',
    }

    params = {
        'code': code,
        'type': 'company',
        'child_type': 'companyInfo',
        '_t': '869',
    }
    url = f'{proxy_server}/getData.action' if proxy_server else 'https://www.qyyjt.cn/getData.action'
    response = requests.post(url, params=params, cookies=cookies, headers=headers)

    return response.json()



import requests

def manager_info(accessToken:str, user:str, code:str, proxy_server:str=None)->dict:
    cookies = {}
    headers = {
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'cache-control': 'no-cache',
        'client': 'pc-web;pro',
        'pcuss': accessToken,
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': f'https://www.qyyjt.cn/detail/enterprise/overview?code={code}&type=company',
        'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'system': 'new',
        'system1': 'Macintosh; Intel Mac OS X 10_15_7;Chrome;141.0.0.0',
        'terminal': 'pc-web;pro',
        'user': user,
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        # 'ver': '20251015',
        # 'x-request-id': 'VOy_2rKo3Y94bEck1q4Qq',
        # 'x-request-url': '%2Fdetail%2Fenterprise%2Foverview%3Fcode%3D4DAF0CAC0B8151253E3611EB403C0C92%26type%3Dcompany%23%25E8%2591%25A3%25E7%259B%2591%25E9%25AB%2598%25E4%25BF%25A1%25E6%2581%25AF',
        # 'cookie': 'HWWAFSESID=d746b733c1d53f0914; HWWAFSESTIME=1760513620484',
    }
    all_managers = {}
    url = f'{proxy_server}/finchinaAPP/v1/finchina-enterprise/senior-executive/manager-info' if proxy_server else 'https://www.qyyjt.cn/finchinaAPP/v1/finchina-enterprise/senior-executive/manager-info'
    for peoType in ['1', '2', '3']: # 1董事会，2监事会，3高管人员
        skip = 0
        managers = []
        while True:
            params = {
                'peoType': peoType,
                'skip': str(skip),
                'sort': '',
                'pageSize': '12',
                'staJobCode': '',
                'code': code,
                'type': 'company',
                'empStatus': '2,5',
            }
            response = requests.get(
                url,
                params=params,
                cookies=cookies,
                headers=headers,
            )
            returncode = response.json().get("returncode")
            if returncode == 0:
                data = response.json().get("data")
                total = data.get("total")
                data_list = data.get("data")
                managers += data_list
                if len(data_list) + skip >= total:
                    break
                else:
                    skip += len(data_list)
            else:
                break
        key = {
            "1": "董事会",
            "2": "监事会",
            "3": "高管人员"
        }.get(peoType)
        all_managers.update({
            key: managers
        })
    return all_managers


def holder(accessToken:str, user:str, code:str, prct_limit:float=None, proxy_server:str=None)->list:
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
        # 'referer': 'https://www.qyyjt.cn/detail/enterprise/overview?code=4DAF0CAC0B8151253E3611EB403C0C92&type=company',
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
        # 'ver': '20250924',
        # 'x-request-id': 'IRwoK7GCx5Uk1zQIBcQmj',
        # 'x-request-url': '%2Fdetail%2Fenterprise%2Foverview%3Fcode%3D4DAF0CAC0B8151253E3611EB403C0C92%26type%3Dcompany%23%25E8%2582%25A1%25E4%25B8%259C(%25E5%2590%25AB%25E9%2597%25B4%25E6%258E%25A5)',
        # 'cookie': 'HWWAFSESID=dcbeb73ed30eab39b1; HWWAFSESTIME=1758683306852',
    }

    params = {
        # 'code': '4DAF0CAC0B8151253E3611EB403C0C92',
        'code': code,
        'type': 'company',
        'typePercent': 'weight',
        'page': '1',
        'pagesize': '50',
        'overview': '1',
        'selected': '',
    }

    url = f'{proxy_server}/finchinaAPP/v1/finchina-enterprise/stock/holder' if proxy_server else 'https://www.qyyjt.cn/finchinaAPP/v1/finchina-enterprise/stock/holder'

    try:
        response = requests.get(
            url,
            params=params,
            cookies=cookies,
            headers=headers,
        )
        holders = json.loads(response.content).get("data").get("data")
        reserve_holders = []
        if prct_limit:
            for holder in holders:
                if float(holder.get("percent")) >= prct_limit:
                    reserve_holders.append(holder)
        else:
            reserve_holders = holders
        
        return reserve_holders
    except:
        return []

    