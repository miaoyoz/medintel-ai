import argparse
import py2neo

class MedicalKG:
    def __init__(self):
        # 共8类节点
        self.diseases = []  # 疾病
        self.symptoms = []  # 症状
        self.drugs = []  # 药品
        self.producers = []  # 药企
        self.foods = []  # 食物
        self.checks = []  # 检查
        self.departments = []  # 科室
        self.treats=[] #治疗方案
        
        # 构建节点实体关系
        self.rel_department = []  # 科室－科室关系
        self.rel_noteat = []  # 疾病－忌吃食物关系
        self.rel_doeat = []  # 疾病－宜吃食物关系
        self.rel_recommandeat = []  # 疾病－推荐吃食物关系
        self.rel_commondrug = []  # 疾病－通用药品关系
        self.rel_recommanddrug = []  # 疾病－热门药品关系
        self.rel_check = []  # 疾病－检查关系
        self.rel_drug_producer = []  # 厂商－药物关系
        self.rel_disease_treat=[] #疾病-治疗关系
        self.rel_symptom = []  # 疾病症状关系
        self.rel_acompany = []  # 疾病并发关系
        self.rel_category = []  # 疾病与科室之间的关系
        

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