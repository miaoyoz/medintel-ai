import argparse
import py2neo
import pymongo
import os
from tqdm import tqdm

def loge(text):
    print(f"\033[91m{text}\033[0m")

def logd(text):
    print(f"\033[92m{text}\033[0m")

def logw(text):
    print(f"\033[93m{text}\033[0m")   

class MedicalKG:
    def __init__(self,client:py2neo.Graph):
        # 共8类节点
        self.diseases = set()  # 疾病
        self.symptoms = set()  # 症状
        self.drugs = set()  # 药品
        self.producers = set()  # 药企
        self.foods = set()  # 食物
        self.checks = set()  # 检查
        self.departments = set()  # 科室
        self.treatments=set() #治疗方案
        self.client = client #neo4j客户端
        self.datas = []  # 存储所有数据
    
    
    #加载mongodb数据并构建图谱
    def build_graph(self):
        try:
            conn = pymongo.MongoClient('localhost', 27017) 
            db = conn['medintel'] 
            col = db['data'] 
            datas = col.find()
            self.datas = list(datas)
        except Exception as e:
            loge("数据库查找失败，请检查数据库服务是否开启")
            
        # datas = {
        #     "_id": "",  
        #     "diseases": self.diseases,
        #     "symptoms": self.symptoms,
        #     "drugs": self.drugs,
        #     "producers": self.producers,
        #     "foods": self.foods,
        #     "checks": self.checks,
        #     "departments": self.departments,
        #     "treatments": self.treatments
        # }
        for item in tqdm(self.datas, desc="构建疾病相关节点和关系", unit="疾病"):
            # diseases = { "name": "", "description":"","category": "", "symptoms": [],
            # "symptom_des":"", "causes": "", "prevention": "", "drugs":[], "checks": [], 
            # "recommended_foods": [], "avoided_foods": [], "complications": [], "reference_url": ""}
            disease = item['diseases']
            # symptoms = [] # {"name": "", "description": ""}
            symptoms = item['symptoms']
            # self.drugs = [] # { "name": "", "ingredients": "", "usage": "", "side_effects": "", "contraindications": "",producer:""}
            drugs = item['drugs']
            # self.producers = [] # { "name": ""}
            producers = item['producers']
            # self.foods = [] # { "name": ""}
            foods = item['foods']
            # self.checks = [] # { "name": "", "description":"", "recommend": ""}
            checks = item['checks']
            # self.departments = [] # {"name": ""}
            departments = item['departments']
            # self.treatments = [] # {"name": "", "description": ""}
            treatments = item['treatments']
            
            #判断disease字典是否为空
            if not disease:
                continue
            name = disease["name"]
            self.diseases.add(name)
            #如果里面有了这个节点则不添加
            if self.client.nodes.match("Disease",name = name).first():
                continue
            #创建Disease节点
            disease_node = py2neo.Node("Disease",name = name,description = disease["description"],category = disease["category"],symptom_des = disease["symptom_des"],
                                causes=disease["causes"],prevention = disease["prevention"],reference_url = disease["reference_url"])
            self.client.create(disease_node)
            
            #构建Symptom节点
            #找到与这个病有关的症状名字
            symptom_names = disease["symptoms"]
            #这里由于原本爬虫的时候未将请求失败的症状创建一个没有数值的字典，导致某些症状在disease的symptoms里面有，而symptoms里面没有
            #disease的symptoms的所有症状名字集合
            for symptom_name in symptom_names:
                is_find = False
                #如果症状名字已经存在了就不添加了,但是创建关系
                if symptom_name in self.symptoms:
                    symptom_node = self.client.nodes.match("Symptom", name=symptom_name).first()
                    rel_symptom = py2neo.Relationship(disease_node,"have_symptom",symptom_node)
                    self.client.create(rel_symptom)
                    continue
                self.symptoms.add(symptom_name)
                for symptom in symptoms: 
                    if symptom["name"]==symptom_name:
                        symptom_node = py2neo.Node("Symptom",name = symptom["name"],description=symptom["description"])
                        rel_symptom = py2neo.Relationship(disease_node,"have_symptom",symptom_node)
                        self.client.create(symptom_node|rel_symptom)
                        is_find = True
                        break
                if is_find:
                    continue    
                symptom_node = py2neo.Node("Symptom",name = symptom_name,description="暂无")
                rel_symptom = py2neo.Relationship(disease_node,"have_symptom",symptom_node)
                self.client.create(symptom_node|rel_symptom)    
            
            #构建Check节点    
            check_names = disease["checks"]    
            for check_name in check_names:
                is_find = False
                if check_name in self.checks:
                    check_node = self.client.nodes.match("Check", name=check_name).first()
                    rel_check = py2neo.Relationship(disease_node,"do_check",check_node)
                    self.client.create(rel_check)
                    continue
                self.checks.add(check_name)
                for check in checks: 
                    if check["name"]==check_name:
                        check_node = py2neo.Node("Check",name = check["name"],description=check["description"],recommend=check["recommend"])
                        rel_check = py2neo.Relationship(disease_node,"do_check",check_node)
                        self.client.create(check_node|rel_check)
                        is_find = True
                        break
                if is_find:
                    continue    
                check_node = py2neo.Node("Check",name = check_name,description="暂无",recommend="暂无")
                rel_check = py2neo.Relationship(disease_node,"do_check",check_node)
                self.client.create(check_node|rel_check)
             
            #构建Food节点
            for food in foods:
                food_name = food["name"] 
                if food_name in self.foods:
                    food_node  = self.client.nodes.match("Food", name=food_name).first()
                    if food_name in disease["recommended_foods"]:
                        rel_doeat = py2neo.Relationship(disease_node,"do_eat",food_node)
                        self.client.create(rel_doeat)
                    elif food_name in disease["avoided_foods"]:    
                        rel_noteat = py2neo.Relationship(disease_node,"not_eat",food_node)
                        self.client.create(rel_noteat)
                    continue    
                self.foods.add(food_name)
                food_node = py2neo.Node("Food",name = food_name)
                if food_name in disease["recommended_foods"]:
                    rel_doeat = py2neo.Relationship(disease_node,"do_eat",food_node)
                    self.client.create(rel_doeat)
                elif food_name in disease["avoided_foods"]:    
                    rel_noteat = py2neo.Relationship(disease_node,"not_eat",food_node)
                    self.client.create(rel_noteat)
                
            #构建Department节点
            for department in departments:
                department_name = department["name"]
                if department_name in self.departments:
                    department_node  = self.client.nodes.match("Department", name=department_name).first()
                    rel_category = py2neo.Relationship(disease_node,"category",department_node)
                    self.client.create(rel_category)
                    continue
                self.departments.add(department_name)
                department_node  = py2neo.Node("Department",name = department_name)
                rel_category = py2neo.Relationship(disease_node,"category",department_node)
                self.client.create(rel_category)    
 
            #构建Treatment节点
            for treatment in treatments:
                treatment_name = treatment["name"]+"的治疗方法"
                if treatment_name in self.treatments:
                    treatment_node  = self.client.nodes.match("Treatment", name=treatment_name).first()
                    rel_treat = py2neo.Relationship(disease_node,"treat",treatment_node)
                    self.client.create(rel_treat)
                    continue
                self.treatments.add(treatment_name)
                treatment_node  = py2neo.Node("Treatment",name = treatment_name,description=treatment["description"])
                rel_treat = py2neo.Relationship(disease_node,"treat",treatment_node)
                self.client.create(rel_treat)  

            #构建Drug和Producer节点
            for drug in drugs: 
                drug_name = drug["name"]
                if drug_name in self.drugs:
                    drug_node = self.client.nodes.match("Drug", name=drug_name).first()
                    rel_drug = py2neo.Relationship(disease_node,"recommend_drug",drug_node)
                    self.client.create(rel_drug)
                    continue
                self.drugs.add(drug_name)
                producer = drug["producer"]
                drug_node = py2neo.Node("Drug",name = drug["name"],ingredients=drug["ingredients"],usage=drug["usage"]
                                        ,side_effects=drug["side_effects"],contraindications=drug["contraindications"],producer=producer)
                rel_drug = py2neo.Relationship(disease_node,"recommend_drug",drug_node)
                self.client.create(drug_node|rel_drug)
                if producer:
                    self.producers.add(producer)
                    producer_node = self.client.nodes.match("Producer", name=producer).first()
                    if not producer_node:
                        producer_node = py2neo.Node("Producer",name=producer)
                    rel_producer =  py2neo.Relationship(drug_node,"producer",producer_node)
                    self.client.create(producer_node|rel_producer)
                
                
        self.save_all()
        self.build_accompany_relation()
        
        
        
    #构建并发症图谱关系
    def build_accompany_relation(self):   
        for item in tqdm(self.datas, desc="构建并发症图谱关系", unit="疾病"):
            disease = item["diseases"]
            name = disease["name"]
            disease_node = self.client.nodes.match("Disease",name=name).first()
            accompanies = disease["complications"]
            if not accompanies:
                continue
            for accompany in accompanies:
                accompany_node = self.client.nodes.match("Disease",name=str(accompany)).first()
                if accompany_node:
                    rel_accompany = py2neo.Relationship(disease_node,"accompany",accompany_node)
                    self.client.create(rel_accompany)
    
    #将节点都写入txt文件中
    def save_all(self):
        # 定义集合与文件的映射关系
        data_to_file = {
            "diseases": ("dataset/data/疾病.txt", self.diseases),
            "symptoms": ("dataset/data/症状.txt", self.symptoms),
            "drugs": ("dataset/data/药品.txt", self.drugs),
            "producers": ("dataset/data/药企.txt", self.producers),
            "foods": ("dataset/data/食物.txt", self.foods),
            "checks": ("dataset/data/检查.txt", self.checks),
            "departments": ("dataset/data/科室.txt", self.departments),
            "treatments": ("dataset/data/治疗方案.txt", self.treatments),
        }

        # 遍历映射关系，将数据写入文件
        for name, (filename, data) in data_to_file.items():
            with open(filename, "a", encoding="utf-8") as file:  # 使用追加模式
                for item in data:
                    file.write(str(item) + "\n")  # 每个数据占一行
            print(f"已写入 {len(data)} 条数据到 {filename}")
        
        

if __name__ == "__main__":
    #连接neo4j数据库的一些参数
    parser = argparse.ArgumentParser(description="通过medical.json文件,创建一个知识图谱")
    parser.add_argument('--website', type=str, default='bolt://localhost:7687', help='neo4j的连接网站')
    parser.add_argument('--user', type=str, default='neo4j', help='neo4j的用户名')
    parser.add_argument('--password', type=str, default='Myz@13861927214', help='neo4j的密码')
    parser.add_argument('--dbname', type=str, default='neo4j', help='数据库名称')
    args = parser.parse_args()
    
     #连接...
    client = py2neo.Graph(args.website, user=args.user, password=args.password, name=args.dbname)

    #将数据库中的内容删光
    is_delete = input('注意:是否删除neo4j上的所有实体 (y/n):')
    if is_delete=='y':
        client.run("match (n) detach delete (n)")
    
    # 遍历目录中的所有文件
    data_dir = "dataset/data/"
    for filename in os.listdir(data_dir):
        file_path = os.path.join(data_dir, filename)
        
        # 检查是否是文件（排除目录）
        if os.path.isfile(file_path):
            # 清空文件内容
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("")
            print(f"已清空文件: {file_path}")
            
    graph = MedicalKG(client)
    graph.build_graph()
        
        