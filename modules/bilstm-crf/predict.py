import torch
from config.params import config
from modules.model import BiLSTM_CRF
from utils.helpers import load_vocab

class MedicalNerPredictor:
    """医疗实体预测器"""
    
    def __init__(self, model_path, vocab_path):
        # 加载词汇表
        word2id, tag2id, self.id2tag = load_vocab(vocab_path)
        self.word2id = word2id
        
        # 初始化模型
        self.model = BiLSTM_CRF(
            vocab_size=len(word2id),
            tag_size=len(tag2id),
            embedding_dim=config.embedding_dim,
            hidden_dim=config.hidden_dim
        ).to(config.device)
        self.model.load_state_dict(torch.load(model_path))
        self.model.eval()
        
    def predict(self, text):
        """预测输入文本中的医疗实体"""
        # 文本转ID序列
        tokens = [self.word2id.get(char, 1) for char in text]  # 1表示UNK
        input_tensor = torch.tensor([tokens], dtype=torch.long).to(config.device)
        
        # 模型预测
        with torch.no_grad():
            tag_ids = self.model(input_tensor)[0]  # 取第一个样本
            
        # 转换为标签
        tags = [self.id2tag[id] for id in tag_ids.cpu().numpy()[:len(text)]]
        
        # 解析实体
        return self._parse_entities(text, tags)
    
    def _parse_entities(self, text, tags):
        """解析标签序列为实体列表"""
        entities = []
        current_entity = None
        
        for idx, (char, tag) in enumerate(zip(text, tags)):
            if tag.startswith('B_'):
                if current_entity:
                    entities.append(current_entity)
                current_entity = {
                    'start': idx,
                    'end': idx+1,
                    'type': tag[2:],
                    'text': char
                }
            elif tag.startswith('I_'):
                if current_entity and current_entity['type'] == tag[2:]:
                    current_entity['end'] = idx+1
                    current_entity['text'] += char
                else:
                    current_entity = None
            else:
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None
        return entities

# 使用示例
if __name__ == "__main__":
    predictor = MedicalNerPredictor(config.model_save_path, config.vocab_save_path)
    sample_text = "患者出现持续头痛和发热症状，牙齿蛀牙严重，进食困难而且便秘？"
    entities = predictor.predict(sample_text)
    print("识别到的实体：")
    for ent in entities:
        print(f"{ent['text']} ({ent['type']})")