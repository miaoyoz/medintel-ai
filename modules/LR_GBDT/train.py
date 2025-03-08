import os
import random
import numpy as np
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

# 设置随机种子
seed = 222
random.seed(seed)
np.random.seed(seed)

def load_data(data_path):
    X, y = [], []
    with open(data_path, 'r', encoding='utf8') as f:
        for line in f.readlines():
            text, label = line.strip().split(',')
            text = ' '.join(list(text.lower()))  # 字符级分词
            X.append(text)
            y.append(label)
    return X, y

def save_model(obj, path):
    with open(path, 'wb') as f:
        pickle.dump(obj, f)

def load_model(path):
    with open(path, 'rb') as f:
        return pickle.load(f)

def run(data_path, model_save_path):
    """训练 LR + GBDT 模型"""
    # 加载数据
    X, y = load_data(data_path)

    # 构建标签映射
    label_set = sorted(list(set(y)))
    label2id = {label: idx for idx, label in enumerate(label_set)}
    id2label = {idx: label for label, idx in label2id.items()}
    y = [label2id[i] for i in y]

    # 划分训练集和测试集
    train_X, test_X, train_y, test_y = train_test_split(X, y, test_size=0.15, random_state=42)

    # TF-IDF 特征提取
    vec = TfidfVectorizer(
        ngram_range=(1, 3),
        min_df=1,
        max_df=0.9,
        analyzer='char',
        use_idf=True,
        smooth_idf=True,
        sublinear_tf=True
    )
    train_X = vec.fit_transform(train_X)
    test_X = vec.transform(test_X)

    # 训练 Logistic Regression
    lr = LogisticRegression(
        C=8,
        dual=False,
        n_jobs=None,
        max_iter=400,
        random_state=122
    )
    lr.fit(train_X, train_y)

    # 训练 GBDT
    gbdt = GradientBoostingClassifier(
        n_estimators=450,
        learning_rate=0.01,
        max_depth=8,
        random_state=24
    )
    gbdt.fit(train_X, train_y)

    # 评估模型
    print("Logistic Regression 分类报告：")
    print(classification_report(test_y, lr.predict(test_X), target_names=label_set[:len(set(test_y))])) 
    print("GBDT 分类报告：")
    print(classification_report(test_y, gbdt.predict(test_X), target_names=label_set[:len(set(test_y))]))

    # 保存模型
    os.makedirs(model_save_path, exist_ok=True)
    save_model(id2label, os.path.join(model_save_path, 'id2label.pkl'))
    save_model(vec, os.path.join(model_save_path, 'vec.pkl'))
    save_model(lr, os.path.join(model_save_path, 'lr.pkl'))
    save_model(gbdt, os.path.join(model_save_path, 'gbdt.pkl'))

if __name__ == '__main__':
    run("modules/LR_GBDT/intent_recog_data.txt", "modules/LR_GBDT/model_weights/")