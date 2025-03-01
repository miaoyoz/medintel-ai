
import time
import random
import requests
from bs4 import BeautifulSoup

from urllib.error import URLError, HTTPError
from urllib.request import ProxyHandler, build_opener, Request, urlopen
from lxml import etree
import pymongo
import threading
import multiprocessing
from multiprocessing import Process,Queue
from multiprocessing import cpu_count
import selenium


    
class Spider:
    def __init__(self):
        # 初始化User-Agent池
        self.user_agents = [
            # Chrome
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # Firefox
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0',
            # Safari
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
            # Edge
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        ]
        
        # 代理服务器池
        self.proxies = [
            'http://180.89.56.240:3128',  
            'http://114.115.158.22:9998',
            'http://117.122.240.82:3338',
            'http://39.106.192.29:8443',
        ]
        
        # 请求头增强参数
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Connection': 'keep-alive',
            'Referer': 'https://www.google.com/'  # 伪装来源
        }
        
    # 获取随机请求头
    def get_random_header(self):
        headers = self.base_headers.copy()
        headers['User-Agent'] = random.choice(self.user_agents)
        return headers
    
    # 获取随机代理
    def get_proxy_handler(self):
        if self.proxies:
            proxy = random.choice(self.proxies)
            return ProxyHandler({'http': proxy, 'https': proxy})
        return ProxyHandler()
    
    # 获取网页html
    def get_html(self, url, tag, retries=3, timeout=15):
        for attempt in range(retries):
            try:
                # 随机延迟（1-3秒）
                time.sleep(random.uniform(1, 3))
                
                # 动态构建请求
                req = Request(
                    url=url,
                    headers=self.get_random_header(),
                    method='GET'
                )
                
                # 配置代理
                proxy_handler = self.get_proxy_handler()
                opener = build_opener(proxy_handler)
                
                # 发起请求
                with opener.open(req, timeout=timeout) as res:
                    # 自动处理编码
                    html = res.read()
                    charset = res.headers.get_content_charset() or tag
                    return html.decode(charset)
                    
            except (URLError, HTTPError) as e:
                print(f"请求失败（尝试 {attempt+1}/{retries}）: {str(e)}")
                if attempt == retries - 1:
                    raise  # 重试次数用尽后抛出异常
                time.sleep(2 ** attempt)  # 指数退避策略
                
            except Exception as e:
                print(f"未知错误: {str(e)}")
                raise

        return None  # 所有重试失败后返回空
    
def ask_url(url):
    head = {    
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36 Edg/87.0.664.47"
    }
    try:
        r = requests.get(url, headers=head, timeout=30)
        r.raise_for_status()
        r.encoding = 'utf-8'
        return r.text
    except:
        return ""

class MedicineSpider(Spider):
    def __init__(self):
        super().__init__()
        self.conn = pymongo.MongoClient('localhost', 27017) # 连接数据库
        self.db = self.conn['medintel'] # 建立数据库
        self.col = self.db['data'] # 建表，字典形式
        self.url = "https://jbk.39.net/bw/" # 网站url
        self.diseases = { "name": "", "description":"","category": "", "symptoms": [],"symptom_des":"", "causes": [], "prevention": [], "treatments": [], "checkups": [], "recommended_foods": [], "avoided_foods": [], "complications": []}
        self.symptoms = []
        self.drugs = { "name": "", "type": "", "category": "", "usage": "", "side_effects": [], "contraindications": []}
        self.producers = { "name": "", "country": "", "products": []}
        self.foods = { "name": "", "category": "", "benefits": "", "nutritional_info": {"carbs": 0, "protein": 0, "fat": 0}, "recommendations": ""}
        self.checks = { "name": "", "type": "", "recommended_for": []}
        self.departments = []
        self.data = {
            "diseases": self.diseases,
            "symptoms": self.symptoms,
            "drugs": self.drugs,
            "producers": self.producers,
            "foods": self.foods,
            "checks": self.checks,
            "departments": self.departments,
        }

    #解析html页面
    def spider_main(self,start = 0,page = 1):
        self.diseases = { "name": "", "description":"","category": "", "symptoms": [],"symptom_des":"", "causes": [], "prevention": [], "treatments": [], "checks": [], "recommended_foods": [], "avoided_foods": [], "complications": []}
        self.symptoms = [] #{"name": "", "description": ""}
        self.drugs = { "name": "", "type": "", "category": "", "usage": "", "side_effects": [], "contraindications": []}
        self.producers = { "name": "", "country": "", "products": []}
        self.foods = { "name": "", "category": "", "benefits": "", "nutritional_info": {"carbs": 0, "protein": 0, "fat": 0}, "recommendations": ""}
        self.checks = { "name": "", "type": "", "recommended_for": []}
        self.departments = [] #{"name": ""}
        self.data = {
            "diseases": self.diseases,
            "symptoms": self.symptoms,
            "drugs": self.drugs,
            "producers": self.producers,
            "foods": self.foods,
            "checks": self.checks,
            "departments": self.departments,
        }
        # 遍历每一页
        for i in range(start, page):
            url = self.url + f"p{i + 1}/"
            self.spider_page(url)     
                    
    
    # 爬取每一页数据
    def spider_page(self,url):
        html = ask_url(url)
        if html == "":
            return
        soup = BeautifulSoup(html, 'html.parser')
    
        try:
            # 遍历每一种疾病
            for item in soup.find_all('div', class_="result_item"):
                if item.div.p.span.string == "疾病":
                    # 疾病url
                    disease_url = item.div.p.a.attrs["href"]
                    disease_jianjie_url = disease_url + "jbzs/" # 疾病简介
                    self.spider_jianjie(disease_jianjie_url)
        except Exception as e:
            print(e)
            return
        
                
    # 爬取疾病简介
    def spider_jianjie(self,url):
        html = ask_url(url)
        if html == "":
            return
        soup = BeautifulSoup(html, 'html.parser')
        self.diseases["name"] = soup.find('div', class_="disease").h1.string
        self.diseases["description"] = soup.find('p', class_="introduction").string
        
        for disease_basic in soup.find_all('ul', class_="disease_basic"):
            for li in disease_basic.find_all('li'):
                if li.span.string == "就诊科室：":
                    span = li.find_all('span')[1]
                    category = ""
                    for a in span.find_all('a'):
                        category_name = a.string
                        self.departments.append({"name":category_name})
                        category += category_name + ","
                    category = category[:-1]
                    self.diseases["category"] = category
                elif li.span.string == "相关症状：":
                    span = li.find_all('span')[1]
                    symptom = []
                    for a in span.find_all('a'):
                        symptom_name = a.string
                        symptom.append(symptom_name)
                        # 症状url
                        symptom_url = a.attrs["href"]
                        self.spider_symptom(symptom_url, symptom_name)
                    symptom = symptom[:-1]
                    self.diseases["symptoms"] = symptom
                elif li.span.string == "相关检查：":
                    span = li.find_all('span')[1]
                    check = []
                    for a in span.find_all('a'):
                        check_name = a.string
                        check.append(check_name)
                        # 检查url
                        check_url = a.attrs["href"]
                        self.spider_check(check_url, check_name)
                    check = check[:-1]
                    print(check)
                    self.diseases["checks"] = check      
                    
     
    # 爬取症状
    def spider_symptom(self,url,name):
        html = ask_url(url)
        if html == "":
            return
        soup = BeautifulSoup(html, 'html.parser')
        ul = soup.find('ul', class_="artlink")
        # 如果找到目标标签
        if ul is not None:
            # 遍历每个<li>标签
            li = ul.find_all('li')[1]
            a = li.find('a')
            a.attrs["href"]
            detail_url = a.attrs["href"]
            detail_html = ask_url(detail_url)
            if detail_html == "":
                return
            detail_soup = BeautifulSoup(detail_html, 'html.parser')
            
            div = detail_soup.find('div', class_="item catalogItem")
            description = ""
            if div:
                # 遍历每个<p>标签
                for p in div.find_all('p'):
                    text = p.get_text(strip=True)  # 提取纯文本并去除空白字符
                    description += text + '\n'  # 在每段结束后换行
            self.symptoms.append({
                "name":name,
                "description":description
            })

    
    # 爬取检查
    def spider_check(self,url,name):
        html = ask_url(url)
        if html == "":
            return
        soup = BeautifulSoup(html, 'html.parser')
        div = soup.find('div', class_="des des1")


if __name__ == '__main__':
    spider = MedicineSpider()
    spider.spider_main(0,1)   