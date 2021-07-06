"""
爬虫-企业预警通官网
网站名：https://www.qyyjt.cn/
用户名：15629963624
密码：12345678
"""

from selenium import webdriver
from requests import Session
from time import sleep
import json
import requests
import numpy as np
import re
import pandas as pd


def login(username,password):
    """
    :param username:
    :param password:
    :return: token，cookie，userID
    'userID'：跟账号一一对应
    'cookie':进入后台的凭证（长时间不变）
    'token':进入后台的凭证（动态变化，大概10分钟更新一次）
    """
    global cookie
    req = Session()
    req.headers.clear()

    # 填写谷歌驱动的位置（而不是google.exe的位置）
    chromePath = r"C:/Users/Dan Cheng/Downloads/AirtestIDE-win-1.2.9/AirtestIDE/chromedriver.exe"
    wd = webdriver.Chrome(executable_path=chromePath)
    # sleep(10)
    # 进入登录界面
    LogInUrl = 'https://www.qyyjt.cn/user/login'
    wd.get(LogInUrl)
    wd.find_element_by_xpath('//*[@id="username"]').send_keys(username)
    wd.find_element_by_xpath('//*[@id="password"]').send_keys(password)
    wd.find_element_by_xpath('//*[@id="validatecode"]').submit()
    sleep(10)  # 手动输入验证码
    # 点击登陆按钮
    wd.find_element_by_xpath('//*[@id="rc-tabs-0-panel-0"]/form/div[5]/div/div/div/button/span').click()  # 若是按钮
    sleep(10)  # 等待Cookies加载
    cookies = wd.get_cookies()
    for cookie in cookies:
        req.cookies.set(cookie['name'], cookie['value'])
    
    wd.get('https://www.qyyjt.cn/area/areaDebt')
    # 获取token, userid, cookies
    access_token  = wd.execute_script('return localStorage.getItem("s_tk");')
    userID        = wd.execute_script('return localStorage.getItem("u_info");')
    refresh_token = wd.execute_script('return localStorage.getItem("r_tk");')
    param = {}
    
    param['token'] = re.sub('"','',access_token)
    param['user'] = json.loads(userID)['user']
    param['cookie'] = cookie

    ## 关闭浏览器和webdriver
    wd.quit()
    return param


def requestData(param, url, filename):
    """
    输入: 省的名字，比如’安徽省‘
    输出: 该省内的所有市，县的地区代码 (地区代码是一个数字，代表该地区，可供后台识别)
    在过程中，把网页中，包含地区名称和地区代码数据集保存下来，可供下次使用，被保存的文件的名称为 filename
    该函数只适用于提供RegionCode的网页
    """
    # 进入企业预警通网站，用刚刚获取到的param通过网页后台的身份验证，获得RegionCode的数据，并且保存下来
    # 填写谷歌驱动的位置（而不是google.exe的位置）

    headers = {
        "Accept":"*/*",
        "Accept-Encoding":"gzip, deflate, br",
        "Accept-Language":'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6',
        "Connection":"keep-alive",
        "Content-Length":"0",
        "dataId":param['dataId'],
        "Host":"www.qyyjt.cn",
        "Origin":"https://www.qyyjt.cn",
        "PCUSS": param['token'],
        "sec-ch-ua":'"Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
        "sec-ch-ua-mobile":"?0",
        "Sec-Fetch-Dest":"empty",
        "Sec-Fetch-Mode":"cors",
        "Sec-Fetch-Site":"same-origin",
        "system":"new",
        "user":param['user'],
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36",
        'cookie':str(param['cookie'])
    }


    DATA = requests.get(url, headers=headers)
    print(json.loads(DATA.content))

    # Save
    np.save(filename, json.loads(DATA.content))


def RegionNameDA(filename):
    # 加载数据
    RegionNames = np.load(filename, allow_pickle=True, encoding="latin1").item()
    RegionNames_data = RegionNames['data']

    ## Get the region codes for the provinces
    provinceCodeDict = {}
    puredata = []
    for province_index in range( (len(RegionNames_data['return1'])-1) ):
        provinceCodeValues = set()
        provinceData = RegionNames_data['return1'][province_index+1]
        puredata.append(provinceData[:5])
        provinceCodeValues.add( int(provinceData[0]) )
        cityData = provinceData[5]
        # print(provinceData[0])
        for city_index in range( len(cityData) ):
            puredata.append(cityData[city_index][:5])
            provinceCodeValues.add(  int(cityData[city_index][0]) )
            # print(cityData[city_index][0])
            if cityData[city_index][5]:
                countyData = cityData[city_index][5]
                for county_index in range( len(countyData) ):
                    puredata.append(countyData[county_index][:5])
                    provinceCodeValues.add( int(countyData[county_index][0]) )
                    # print(countyData[county_index][0])
        print(provinceCodeValues)
        list(provinceCodeValues).sort()

        provinceCodeDict[provinceData[1]] = ','.join(str(i) for i in provinceCodeValues)


    return provinceCodeDict


def RegionEconomyDA(filename_npy,filename_xlsx):
    """
    该函数目的是将.npy文件转化成excel文件，供习惯用excel文件的人使用
    :param filename_npy:
    :param filename_xlsx:
    :return: excel file
    """
    # 加载数据
    RegionEconomydata = np.load(filename_npy, allow_pickle=True, encoding="latin1").item()
    RegionEconomyData = RegionEconomydata['data']

    all_indices = set()
    for _ in range(len(RegionEconomyData)):
        all_indices.update(set(RegionEconomyData[_].keys()))

    mylist = {}
    for index in tuple(all_indices):
        print(index)
        dict_index = []
        for i in range(len(RegionEconomyData)):
            if index in RegionEconomyData[i].keys():
                dict_index.append(RegionEconomyData[i][index])
                print(RegionEconomyData[i][index])
            else:
                dict_index.append(pd.NA)
        mylist[index] = dict_index

    df = pd.DataFrame(mylist, columns=all_indices)
    df.to_excel(excel_writer=filename_xlsx, index=False, encoding='utf-8')



if __name__ == '__main__':
    # 根据用户名：'15629963624'， 密码：'12345678'登录企业预警通官网
    # 然后返回参数，该参数需要传输到后台，被识别后才允许被下载数据
    # 第一步：使用用户名，密码登录，获取可供后台识别的userID， cookie，token
    param = login('13997510728', '12345678')

    chromePath = r"C:/Users/Dan Cheng/Downloads/AirtestIDE-win-1.2.9/AirtestIDE/chromedriver.exe"
    wd = webdriver.Chrome(executable_path=chromePath)
    # 爬取所有省市区（县）的RegionCode
    urlRegionName = 'https://www.qyyjt.cn/getData.action'
    param['dataId'] = '154'
    requestData(param, urlRegionName, 'RegionName.npy')

    # 将所有省市区县的代码转化成: 不同省所涵盖的所有省市区县的代码
    provinceCodeDict = RegionNameDA('RegionName.npy')
    yangtzeRiverEconomicBelt = ['上海市','江苏省','浙江省','安徽省','江西省','湖北省','湖南省','重庆市','四川省','云南省','贵州省']
    for item in yangtzeRiverEconomicBelt:
        # 输入经济性指标
        indicName = '地区生产总值,人均地区生产总值,GDP增速,工业总产值,固定资产投资,进出口总额,社会消费品零售总额,社会消费品零售总额增速,城镇居民人均可支配收入,一般公共预算收入,一般公共预算支出,地方政府债务余额,地方政府债务限额,负债率,债务率1'
        datetime = '2020'
        regionCode = provinceCodeDict[item]
        # 获得该经济性指标所对营的数据
        urlRegionEconomy = f'https://www.qyyjt.cn/getData.action?keyword=&func=/app/regionalEconomic2&module_' \
              f'type=area_economy_and_debt&dateQueryType=1&size=10000&indicName={indicName}' \
              f'&datetime={datetime}&regionCode={regionCode}'
        param['dataId'] = "486"
        filename_npy = item+'RegionEconomy.npy'
        filename_xlsx = item+'RegionEconomy.xlsx'
        requestData(param, urlRegionEconomy, filename_npy)
        RegionEconomyDA(filename_npy,filename_xlsx)






