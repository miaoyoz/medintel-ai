import time
import random
import requests
from bs4 import BeautifulSoup
import pymongo
import re
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, get_ident
from concurrent.futures import ThreadPoolExecutor, as_completed

def loge(text):
    print(f"\033[91m{text}\033[0m")

def logd(text):
    print(f"\033[92m{text}\033[0m")

def logw(text):
    print(f"\033[93m{text}\033[0m")
    
   
def ask_url(url):
    head = {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15"
        ])
    }
    try:
        time.sleep(random.uniform(1, 3))  # 随机延迟
        r = requests.get(url, headers=head, timeout=30)
        r.raise_for_status()
        r.encoding = 'utf-8'
        return r.text
    except Exception as e:
        logw(f"请求失败: {url}, 错误: {e}")
        return ""
    
write_lock = Lock()

class MedicineSpider():
    def __init__(self):
        self.conn = pymongo.MongoClient('localhost', 27017) # 连接数据库
        self.db = self.conn['medintel'] # 建立数据库
        self.col = self.db['data'] # 建表，字典形式
        self.url = "https://jbk.39.net/bw/" # 网站url
        self.diseases = { "name": "", "description":"","category": "", "symptoms": [],"symptom_des":"", "causes": "", "prevention": "", "drugs":[], "checks": [], "recommended_foods": [], "avoided_foods": [], "complications": [], "reference_url": ""}
        self.symptoms = [] # {"name": "", "description": ""}
        self.drugs = [] # { "name": "", "ingredients": "", "usage": "", "side_effects": "", "contraindications": "",producer:""}
        self.producers = [] # { "name": ""}
        self.foods = [] # { "name": "", "category": "", "benefits": "", "nutritional_info": {"carbs": 0, "protein": 0, "fat": 0}, "recommendations": ""}
        self.checks = [] # { "name": "", "description":"", "recommend": ""}
        self.departments = [] # {"name": ""}
        self.treatments = [] # {"name": "", "description": ""}
        self.data = {
            "_id": "",  
            "diseases": self.diseases,
            "symptoms": self.symptoms,
            "drugs": self.drugs,
            "producers": self.producers,
            "foods": self.foods,
            "checks": self.checks,
            "departments": self.departments,
            "treatments": self.treatments
        }
    
    # 生成线程安全的唯一ID    
    def generate_thread_safe_id(self):
        thread_id = get_ident()  # 获取当前线程ID
        timestamp = int(time.time() * 1000)  # 当前时间戳（毫秒）
        unique_id = f"{timestamp}_{thread_id}"  # 结合时间戳和线程ID生成唯一ID
        return unique_id    
        
    # 插入数据到MongoDB
    def save_to_mongodb(self):
        name = self.diseases["name"]
        try:
            with write_lock:
                self.data["_id"] = self.generate_thread_safe_id()  # 生成线程安全的唯一ID
                self.col.insert_one(self.data)
            print(name+" 数据已存入MongoDB！")  
        except Exception as e:
            loge(name+ f"插入数据失败: {e}")
          

    #解析html页面
    def spider_main(self,start = 1,page = 1):
        print(f"开始爬取页面 {start} 到 {page}")  # 调试信息
        self.diseases = { "name": "", "description":"","category": "", "symptoms": [],"symptom_des":"", "causes": "", "prevention": "", "drugs":[], "checks": [], "recommended_foods": [], "avoided_foods": [], "complications": [], "reference_url": ""}
        self.symptoms = [] # {"name": "", "description": ""}
        self.drugs = [] # { "name": "", "ingredients": "", "usage": "", "side_effects": "", "contraindications": "",producer:""}
        self.producers = [] # { "name": ""}
        self.foods = [] # { "name": "", "category": "", "benefits": "", "nutritional_info": {"carbs": 0, "protein": 0, "fat": 0}, "recommendations": ""}
        self.checks = [] # { "name": "", "description":"", "recommend": ""}
        self.departments = [] # {"name": ""}
        self.treatments = [] # {"name": "", "description": ""}
        self.data = {
            "_id": "",  
            "diseases": self.diseases,
            "symptoms": self.symptoms,
            "drugs": self.drugs,
            "producers": self.producers,
            "foods": self.foods,
            "checks": self.checks,
            "departments": self.departments,
            "treatments": self.treatments
        }
        # 遍历每一页
        for i in range(start, page+1):
            time.sleep(random.uniform(1, 3))
            url = self.url + f"t1_p{i + 1}/"
            print(f"开始爬取: {url}")  # 调试信息
            self.spider_page(url)
            
        
                 
                    
    
    # 爬取每一页数据
    def spider_page(self,url):
        html = ask_url(url)
        if html == "":
            return
        soup = BeautifulSoup(html, 'html.parser')

            # 遍历每一种疾病
        for item in soup.find_all('div', class_="result_item"):
            if item.div.p.span.get_text(strip=True) == "疾病":
                # 疾病url
                disease_url = item.div.p.a.attrs["href"]
                self.diseases["reference_url"] = disease_url
                disease_jianjie_url = disease_url + "jbzs/" # 疾病简介
                self.spider_jianjie(disease_jianjie_url)
                disease_zhengzhuang_url = disease_url + "zztz/" # 症状情况
                symptom_des = self.spider_article(disease_zhengzhuang_url)
                self.diseases["symptom_des"] = symptom_des
                disease_treat_url = disease_url + "yyzl/" # 治疗方法
                treatment = self.spider_article(disease_treat_url)
                self.treatments.append({
                    "name":self.diseases["name"],
                    "description":treatment
                })
                prevence_url = disease_url + "yfhl/" # 预防
                prevention = self.spider_article(prevence_url)
                self.diseases["prevention"] = prevention
                cause_url = disease_url + "blby/" # 病因
                causes = self.spider_article(cause_url)
                self.diseases["causes"] = causes
                drug_url = disease_url + "cyyp/" # 药品
                self.spider_drugs(drug_url)
                food_url = disease_url + "ysbj/" # 饮食
                self.spider_food(food_url)
            self.save_to_mongodb()
                
    # 爬取疾病简介
    def spider_jianjie(self,url):
        html = ask_url(url)
        if html == "":
            return
        soup = BeautifulSoup(html, 'html.parser')
        self.diseases["name"] = soup.find('div', class_="disease").h1.string
        print("current name: ", self.diseases["name"])
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
                    self.diseases["checks"] = check
                elif li.span.string == "并发疾病：":
                    span = li.find_all('span')[1]
                    disease = []
                    for a in span.find_all('a'):
                        disease_name = a.string
                        disease.append(disease_name)
                    disease = disease[:-1]
                    self.diseases["complications"] = disease   
     
    # 爬取症状
    def spider_symptom(self,url,name):
        description = ""
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
        description = ""
        recommend = ""
        html = ask_url(url)
        if html == "":
            return
        soup = BeautifulSoup(html, 'html.parser')
        div = soup.find('div', id="intro")
        if div is not None:
            span = div.find('span')
            if span:
                # 提取纯文本并去除空白字符
                description = span.get_text(strip=True)
        p = soup.find('p', class_="p")
        if p is not None:
            recommend = p.get_text(strip=True)
                
        self.checks.append({
            "name":name,
            "description":description,
            "recommend":recommend
        })        
          
    # 爬取全部药品
    def spider_drugs(self, url):
        try:
            html = ask_url(url)
            if html == "":
                return
            soup = BeautifulSoup(html, 'html.parser')
            ul = soup.find('ul', class_="drug-list")
            if ul is not None:
                for li in ul.find_all('li'):
                    a = li.find('h4').a
                    drug_name = a.string
                    drug_url = a.attrs["href"]
                    self.spider_drug_info(drug_url, drug_name)
        except Exception as e:
            loge(f"Error in spider_drugs: {e}")

    # 爬取药品信息
    def spider_drug_info(self, url, name):
        try:
            ingredients = ""
            usage = ""
            side_effects = ""
            contraindications = ""
            producer = ""
            url = url + "manual/"
            html = ask_url(url)
            if html == "":
                return
            soup = BeautifulSoup(html, 'html.parser')
            ul = soup.find('ul', class_="drug-explain")
            if ul is not None:
                for li in ul.find_all('li'):
                    title = li.find('p', class_="drug-explain-tit")
                    if title:
                        if li.p.string == "【成份】":
                            ingredients = li.find_all('p')[1].get_text(strip=True)
                        elif li.p.string == "【用法用量】":
                            usage = li.find_all('p')[1].get_text(strip=True)
                        elif li.p.string == "【不良反应】":
                            side_effects = li.find_all('p')[1].get_text(strip=True)
                        elif li.p.string == "【禁忌】":
                            contraindications = li.find_all('p')[1].get_text(strip=True)
                        elif li.p.string == "【生产企业】":
                            producer_content = li.find_all('p')[1].get_text(strip=False)
                            # 提取企业名称
                            match = re.search(r"企业名称：(.+?)\n", producer_content)
                            if match:
                                producer = match.group(1).strip()
                                self.producers.append({
                                    "name": producer
                                })
            self.drugs.append({
                "name": name,
                "ingredients": ingredients,
                "usage": usage,
                "side_effects": side_effects,
                "contraindications": contraindications,
                "producer": producer
            })
        except Exception as e:
            loge(f"Error in spider_drug_info: {e}")

    # 爬取文章内容        
    def spider_article(self, url):
        try:
            html = ask_url(url)
            if html == "":
                return
            soup = BeautifulSoup(html, 'html.parser')
            div = soup.find('div', class_="article_box")
            if div is not None:
                return div.get_text(strip=True, separator="\n")
        except Exception as e:
            loge(f"Error in spider_article: {e}")


    # 爬取食物
    def spider_food(self, url):
        try:
            html = ask_url(url)
            if html == "":
                return
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('div', class_="yinshi_table").find_all('table')
            if table is None:
                return

            if len(table) < 1:
                return

            # 宜吃的食物
            for index, item in enumerate(table[0].find_all('tr')):
                if index == 0:
                    continue
                food = item.find('td').string
                self.diseases["recommended_foods"].append(food)
                self.foods.append({
                    "name": food
                })

            if len(table) < 2:
                return
            # 忌吃的食物
            
            enumerate(table[1].find_all('tr'))
            for index, item in enumerate(table[1].find_all('tr')):
                if index == 0:
                    continue
                food = item.find('td').string
                self.diseases["avoided_foods"].append(food)
                self.foods.append({
                    "name": food
                })
        except Exception as e:
            name = self.diseases["name"]
            loge(f"{name}Error in spider_food: {e}")
            


if __name__ == '__main__':
    try:
        def run_spider(start, end):
            spider = MedicineSpider()
            spider.spider_main(start, end)

        # 定义线程池和任务队列
        num_threads = 5  # 假设启动5个线程
        total_pages = 134  # 总共需要爬取的页面数
        pages_per_task = 1  # 每个任务爬取1个页面

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for i in range(0, total_pages, pages_per_task):
                start = i
                end = min(i + pages_per_task, total_pages)
                futures.append(executor.submit(run_spider, start, end))

            # 等待每个任务完成
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    loge(f"Error in future: {e}")

        logd("所有任务已完成！")
    except Exception as e:
        loge(f"Error in main: {e}")