import pickle
import sys
import os

# 将上级目录的config文件夹添加到系统路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../config'))
# 现在可以导入params模块
from params import config



def save_vocab(word2id, tag2id, id2tag, save_path):
    """保存词汇表映射"""
    with open(save_path, 'wb') as f:
        pickle.dump((word2id, tag2id, id2tag), f)

def load_vocab(vocab_path):
    """加载词汇表映射"""
    with open(vocab_path, 'rb') as f:
        return pickle.load(f)



