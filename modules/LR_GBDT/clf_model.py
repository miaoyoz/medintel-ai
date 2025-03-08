import os
import pickle
import numpy as np

class CLFModel:
    def __init__(self, model_save_path):
        """加载模型"""
        self.model_save_path = model_save_path
        self.id2label = pickle.load(open(os.path.join(self.model_save_path,'id2label.pkl'),'rb'))
        self.vec = pickle.load(open(os.path.join(self.model_save_path,'vec.pkl'),'rb'))
        self.lr = pickle.load(open(os.path.join(self.model_save_path,'lr.pkl'),'rb'))  # Fixed variable name
        self.gbdt = pickle.load(open(os.path.join(self.model_save_path,'gbdt.pkl'),'rb'))  # Fixed variable name

    def preprocess(self, text):
        """文本预处理（保持和训练时一致）"""
        return ' '.join(list(text.lower()))

    def predict(self, text):
        """单个文本预测"""
        text = self.preprocess(text)
        text_vector = self.vec.transform([text])

        # 计算 LR 和 GBDT 预测概率
        lr_proba = self.lr.predict_proba(text_vector)
        gbdt_proba = self.gbdt.predict_proba(text_vector)

        # 进行加权平均融合
        final_proba = (lr_proba + gbdt_proba) / 2
        label_id = np.argmax(final_proba, axis=1)[0]

        return self.id2label.get(label_id, "未知标签")  # 返回预测标签

    def batch_predict(self, texts):
        """批量预测"""
        texts = [self.preprocess(text) for text in texts]
        text_vectors = self.vec.transform(texts)

        # 计算概率
        lr_proba = self.lr.predict_proba(text_vectors)
        gbdt_proba = self.gbdt.predict_proba(text_vectors)

        # 进行加权平均融合
        final_proba = (lr_proba + gbdt_proba) / 2
        label_ids = np.argmax(final_proba, axis=1)

        return [self.id2label.get(label_id, "未知标签") for label_id in label_ids]

# 示例用法
if __name__ == '__main__':
    model = CLFModel('modules/LR_GBDT/model_weights/')
    test_sentences = ["你好啊", "你是谁", "拜拜","我的头有点疼","我想要买一本书"]
    
    for text in test_sentences:
        label = model.predict(text)
        print(f"输入: {text}  ->  预测意图: {label}")
