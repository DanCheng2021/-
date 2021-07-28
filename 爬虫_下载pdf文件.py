"""
@author: Dan Cheng
@file: 爬虫_下载pdf格式论文.py
"""

'''
首页
列表
详情
'''

import requests
from lxml import etree

def main():
    # 1. 定义页面URL和解析规则
    url = "http://pages.stern.nyu.edu/~ealtman/papers.html"
    # 2. 发起HTTP请求
    response = requests.get(url)
    pNodeLen = int(etree.HTML(response.text).xpath('count(//tr[2]/td/p)'))
    listUrl = []
    for i in range(1,pNodeLen):
        # 数据清洗规则
        parse_rule = "//tr[2]/td/p[{}]/span/a/@href".format(i)

        # 3. 解析HTML
        result = etree.HTML(response.text).xpath(parse_rule)
        # flt = lambda x: x[0] if x else x
        if result:
            if '.pdf' in result[0]:
                listUrl.append(result[0])


    for i in range(len(listUrl)):
        if 'http://' not in listUrl[i]:
            listUrl[i] = 'http://www.stern.nyu.edu/~ealtman/' + listUrl[i]
            # print(listUrl[i])
        try:
            res = requests.get(listUrl[i],stream=True)
            # 保存结果
            with open(str(i)+'.pdf', "wb") as pdf_file:
                for content in res.iter_content():
                    pdf_file.write(content)
            print(listUrl[i] + ' is downloaded successfully ' + str(i))
        except IOError:
            print("Error: 没有找到文件或读取文件失败")
            print(listUrl[i],i)


if __name__ == '__main__':
    main()
