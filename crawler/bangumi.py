# coding: utf-8
# 从bangumi获得原始数据，包括画师的性别和推特
# 由于推特需要另外打开页面才能得到，先爬取所有有性别标注的画师
import urllib.request, time
from bs4 import BeautifulSoup
import re, progressbar

from DBAccess.DBAccess import getDBClient

class GetEshiInfo:
    def __init__(self, start_page, end_page, DB_ADDR, DB_PORT):
        self.start_page = start_page
        self.end_page = end_page
        self.db_client = getDBClient(DB_ADDR, DB_PORT)


    def getEshiWithGenderTagged(self):

        for page_number in range(self.start_page, self.end_page+1):
            print("正在爬取第{}个网页".format(page_number))
            url = "https://bangumi.tv/person?type=7&page={}".format(page_number)
            response = urllib.request.urlopen(url)
            originalHtml = response.read().decode("utf-8")  # 获取到页面的源代码
            soup = BeautifulSoup(originalHtml)

            # 存有画师信息的div列表
            result = soup.find_all("div", {"class": "light_odd"})
            for div_item in result:
                # 画师名和href
                eshi_name_info = div_item.find("a", {"class": "l"})
                eshi_name = eshi_name_info.string
                eshi_href = "https://bangumi.tv" + eshi_name_info["href"]
                print(eshi_name, eshi_href)
                eshi_info = \
                    {
                        "name": eshi_name,
                        "href": eshi_href,
                        "gender": -1
                    }
                # 画师性别
                eshi_gender_div = div_item.find("span", {"class": "tip"})
                if(eshi_gender_div.string.find("男") != -1):
                    # print("男性画师")
                    eshi_info["gender"] = 1
                elif(eshi_gender_div.string.find("女") != -1):
                    # print("女性画师")
                    eshi_info["gender"] = 0

                eshi_analysis_db = self.db_client["eshi_analysis"]
                eshi_info_collection = eshi_analysis_db["eshi_info"]
                eshi_info_collection.insert_one(eshi_info)
            time.sleep(10)

    def isURL(self, input_string):
        # 判断输入的字符串是不是URL
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return re.match(regex, input_string) is not None


    def getEshiTwitter(self):
        eshi_analysis_db = self.db_client["eshi_analysis"]
        eshi_info_collection = eshi_analysis_db["eshi_info"]
        female_eshi_collection = eshi_analysis_db["female_eshi_info"]
        male_eshi_collection = eshi_analysis_db["male_eshi_info"]
        exception_collection = eshi_analysis_db["exception_eshi_info"]
        total_eshi_number = 2165
        print("总共有{}个画师".format(total_eshi_number))
        bar = progressbar.ProgressBar(max_value=total_eshi_number)
        index = 0

        for single_document in eshi_info_collection.find():
            bar.update(index)
            index += 1

            gender = single_document["gender"]
            eshi_href = single_document["href"]

            if gender == 0 or gender == 1:
                response = urllib.request.urlopen(eshi_href)
                original_HTML = response.read().decode("utf-8")
                soup = BeautifulSoup(original_HTML, features="html.parser")

                eshi_info_box = soup.find("ul", {"id": "infobox"}).find_all("li")
                for item in eshi_info_box:
                    eshi_info = item.text
                    if eshi_info.find("Twitter") != -1 or eshi_info.find("twitter") != -1 or eshi_info.find("推特") != -1:
                        print(eshi_info)
                        twitter_ID_or_URL = eshi_info.split(" ")[1]

                        # 记载方法有的是ID有的是URL，使用正则表达式的区分URL和ID
                        eshi_twitter_info = \
                            {
                                "_id": single_document["_id"],
                                "name": single_document["name"],
                                "gender": single_document["gender"],
                                "twitter_info": twitter_ID_or_URL,
                                "twitter_is_URL": 1 if self.isURL(twitter_ID_or_URL) else 0
                            }
                        try:
                            if gender == 1:
                                male_eshi_collection.insert_one(eshi_twitter_info)
                            elif gender == 0:
                                female_eshi_collection.insert_one(eshi_twitter_info)
                        except:
                            error_eshi_info = \
                            {
                                "name": single_document["name"],
                                "gender": single_document["gender"],
                                "twitter_info": twitter_ID_or_URL,
                                "href": single_document["href"]
                            }
                            exception_collection.insert_one(error_eshi_info)



if __name__ == "__main__":
    # getEshiWithGenderTagged(1, 109)
    bangumu_crawler = GetEshiInfo(start_page=1, end_page=109, DB_ADDR="localhost", DB_PORT=27017)
    bangumu_crawler.getEshiTwitter()

