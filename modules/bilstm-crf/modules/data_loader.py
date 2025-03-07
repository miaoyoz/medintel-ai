import re
import pickle
from collections import Counter
import torch
from torch.utils.data import Dataset, DataLoader
import sys
import os

# 将上级目录的config文件夹添加到系统路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../config'))

# 现在可以导入params模块
from params import config

class MedicalNERDataset(Dataset):
    """医疗NER数据集加载器
    
    Attributes:
        word2id (dict): 词汇表映射
        tag2id (dict): 标签映射
        max_len (int): 最大序列长度
    """
    
    def __init__(self, file_path, word2id=None, tag2id=None, max_len=80):
        self.sentences, self.tags = self._load_data(file_path)
        self.max_len = max_len
        
        # 首次运行时构建词汇表和标签映射
        if word2id is None or tag2id is None:
            self.word2id, self.tag2id = self._build_vocab()
        else:
            self.word2id = word2id
            self.tag2id = tag2id
            
    def _load_data(self, file_path):
        """加载原始数据"""
        sentences, tags = [], []
        current_sentence, current_tags = [], []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:  # 空行表示句子结束
                    if current_sentence:
                        sentences.append(current_sentence)
                        tags.append(current_tags)
                        current_sentence, current_tags = [], []
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    word, tag = parts[0], parts[1]
                    current_sentence.append(word)
                    current_tags.append(tag)
        return sentences, tags
    
    def _build_vocab(self):
        """构建词汇表和标签映射"""
        # 统计词频
        all_words = [word for sentence in self.sentences for word in sentence]
        word_counts = Counter(all_words)
        vocab = [word for word, _ in word_counts.most_common(config.vocab_size-2)]
        
        # 构建映射
        word2id = {'<PAD>': 0, '<UNK>': 1}
        for idx, word in enumerate(vocab):
            word2id[word] = idx + 2
            
        # 标签映射
        all_tags = set(tag for tag_seq in self.tags for tag in tag_seq)
        tag2id = {'<PAD>': 0}
        for idx, tag in enumerate(sorted(all_tags)):
            tag2id[tag] = idx + 1
            
        return word2id, tag2id
    
    def __len__(self):
        return len(self.sentences)
    
    def __getitem__(self, idx):
        """获取单个样本并转换为Tensor"""
        sentence = [self.word2id.get(word, 1) for word in self.sentences[idx]]
        tags = [self.tag2id[tag] for tag in self.tags[idx]]
        
        # 截断/填充处理
        sentence = sentence[:self.max_len] + [0]*(self.max_len - len(sentence))
        tags = tags[:self.max_len] + [0]*(self.max_len - len(tags))
        
        return (
            torch.tensor(sentence, dtype=torch.long),
            torch.tensor(tags, dtype=torch.long)
        )

def create_data_loader(file_path, word2id, tag2id, batch_size=32):
    """创建数据加载器"""
    dataset = MedicalNERDataset(file_path, word2id, tag2id, config.max_seq_len)
    return DataLoader(dataset, batch_size=batch_size, shuffle=True)