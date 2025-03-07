import torch

class Config:
    # 数据路径
    train_data = "modules/bilstm-crf/data/train.txt"
    dev_data = "modules/bilstm-crf/data/dev.txt"
    test_data = "modules/bilstm-crf/data/test.txt"
    
    # 模型参数
    max_seq_len = 80        # 最大序列长度
    vocab_size = 3000       # 词汇表大小（含padding和OOV）
    embedding_dim = 200     # 词向量维度
    hidden_dim = 128        # BiLSTM隐藏层维度
    num_tags = 24           # 实体标签类别数
    
    # 训练参数
    batch_size = 32
    num_epochs = 500
    learning_rate = 0.001
    early_stop_patience = 10 # 早停耐心值
    
    # 设备配置
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # 路径配置
    model_save_path = "modules/bilstm-crf/saved_models/best_model.pth"
    vocab_save_path = "modules/bilstm-crf/saved_models/vocab_tags.pkl"

config = Config()