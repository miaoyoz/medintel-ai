# medintel-ai
毕业设计python ai端

## 运行环境：
- neo4j 5.26.2
- mongodb 8.0.5
- ollama 

## mongoDB数据关系
以下是需要存储的 MongoDB 数据结构的详细设计，包括节点和关系的数据字段以及存储示例。

### 1. **节点集合**

#### 1.1 疾病（Diseases）

```json
{
  "_id": ObjectId("unique_id"),
  "name": "糖尿病",
  "icd_code": "E11",
  "category": "内分泌",
  "symptoms": [
    {"_id": ObjectId("symptom_id_1"), "name": "多尿"},
    {"_id": ObjectId("symptom_id_2"), "name": "口渴"}
  ],
  "causes": ["遗传", "饮食不当", "缺乏运动"],
  "prevention": ["保持健康体重", "饮食控制", "定期运动"],
  "treatments": [
    {"_id": ObjectId("treatment_id_1"), "name": "胰岛素治疗"},
    {"_id": ObjectId("treatment_id_2"), "name": "口服降糖药"}
  ],
  "checkups": [
    {"_id": ObjectId("checkup_id_1"), "name": "血糖检查"}
  ],
  "recommended_foods": [
    {"_id": ObjectId("food_id_1"), "name": "燕麦"}
  ],
  "avoided_foods": [
    {"_id": ObjectId("food_id_2"), "name": "高糖食物"}
  ],
  "complications": [
    {"_id": ObjectId("complication_id_1"), "name": "糖尿病肾病"}
  ]
}
```

#### 1.2 症状（Symptoms）

```json
{
  "_id": ObjectId("symptom_id_1"),
  "name": "多尿",
  "description": "频繁排尿"
}
```

#### 1.3 药品（Drugs）

```json
{
  "_id": ObjectId("drug_id_1"),
  "name": "胰岛素",
  "type": "注射剂",
  "category": "降糖药",
  "usage": "每日注射一次",
  "side_effects": ["低血糖", "体重增加"],
  "contraindications": ["严重过敏", "糖尿病酮症酸中毒"]
}
```

#### 1.4 药企（Producers）

```json
{
  "_id": ObjectId("producer_id_1"),
  "name": "诺和诺德",
  "country": "丹麦",
  "products": [
    {"_id": ObjectId("drug_id_1"), "name": "胰岛素"}
  ]
}
```

#### 1.5 食物（Foods）

```json
{
  "_id": ObjectId("food_id_1"),
  "name": "燕麦",
  "category": "碳水化合物",
  "benefits": "富含膳食纤维，有助于控制血糖",
  "nutritional_info": {"carbs": 20, "protein": 5, "fat": 2},
  "recommendations": "适合糖尿病患者"
}
```

#### 1.6 检查（Checks）

```json
{
  "_id": ObjectId("checkup_id_1"),
  "name": "血糖检查",
  "type": "血液检查",
  "recommended_for": [
    {"_id": ObjectId("disease_id_1"), "name": "糖尿病"}
  ]
}
```

#### 1.7 科室（Departments）

```json
{
  "_id": ObjectId("department_id_1"),
  "name": "内分泌科",
  "specialties": ["糖尿病", "甲状腺疾病"]
}
```

#### 1.8 治疗方案（Treatments）

```json
{
  "_id": ObjectId("treatment_id_1"),
  "name": "胰岛素治疗",
  "description": "通过注射胰岛素来调节血糖水平",
  "indications": ["糖尿病"]
}
```

### 2. **关系集合**

#### 2.1 疾病与症状关系（rel_symptom）

```json
{
  "_id": ObjectId("rel_symptom_id_1"),
  "disease_id": ObjectId("disease_id_1"),
  "symptom_id": ObjectId("symptom_id_1")
}
```

#### 2.2 疾病与食物关系（宜吃 / 忌吃 / 推荐吃）

- **疾病-忌吃食物关系（rel_noteat）**

```json
{
  "_id": ObjectId("rel_noteat_id_1"),
  "disease_id": ObjectId("disease_id_1"),
  "food_id": ObjectId("food_id_2")
}
```

- **疾病-宜吃食物关系（rel_doeat）**

```json
{
  "_id": ObjectId("rel_doeat_id_1"),
  "disease_id": ObjectId("disease_id_1"),
  "food_id": ObjectId("food_id_1")
}
```

- **疾病-推荐吃食物关系（rel_recommandeat）**

```json
{
  "_id": ObjectId("rel_recommandeat_id_1"),
  "disease_id": ObjectId("disease_id_1"),
  "food_id": ObjectId("food_id_1")
}
```

#### 2.3 疾病与药品关系（commondrug / recommanddrug）

- **疾病-通用药品关系（rel_commondrug）**

```json
{
  "_id": ObjectId("rel_commondrug_id_1"),
  "disease_id": ObjectId("disease_id_1"),
  "drug_id": ObjectId("drug_id_1")
}
```

- **疾病-热门药品关系（rel_recommanddrug）**

```json
{
  "_id": ObjectId("rel_recommanddrug_id_1"),
  "disease_id": ObjectId("disease_id_1"),
  "drug_id": ObjectId("drug_id_1")
}
```

#### 2.4 疾病与检查关系（rel_check）

```json
{
  "_id": ObjectId("rel_check_id_1"),
  "disease_id": ObjectId("disease_id_1"),
  "checkup_id": ObjectId("checkup_id_1")
}
```

#### 2.5 厂商与药品关系（rel_drug_producer）

```json
{
  "_id": ObjectId("rel_drug_producer_id_1"),
  "producer_id": ObjectId("producer_id_1"),
  "drug_id": ObjectId("drug_id_1")
}
```

#### 2.6 疾病与治疗关系（rel_disease_treat）

```json
{
  "_id": ObjectId("rel_disease_treat_id_1"),
  "disease_id": ObjectId("disease_id_1"),
  "treatment_id": ObjectId("treatment_id_1")
}
```

#### 2.7 疾病与并发症关系（rel_acompany）

```json
{
  "_id": ObjectId("rel_acompany_id_1"),
  "disease_id": ObjectId("disease_id_1"),
  "complication_id": ObjectId("complication_id_1")
}
```

#### 2.8 疾病与科室关系（rel_category）

```json
{
  "_id": ObjectId("rel_category_id_1"),
  "disease_id": ObjectId("disease_id_1"),
  "department_id": ObjectId("department_id_1")
}
```

