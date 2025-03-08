import torch
import torch.optim as optim
from torch.nn import CrossEntropyLoss,NLLLoss
from config.params import config
from modules.data_loader import MedicalNERDataset, create_data_loader
from modules.model import BiLSTM_CRF
from utils.helpers import save_vocab
from modules.metrics import batch_evaluate, print_report
from tqdm import tqdm

# 初始化数据集
train_dataset = MedicalNERDataset(config.train_data)
word2id, tag2id = train_dataset.word2id, train_dataset.tag2id
id2tag = {v:k for k,v in tag2id.items()}

# 保存词汇表
save_vocab(word2id, tag2id, id2tag, config.vocab_save_path)

# 创建数据加载器
train_loader = create_data_loader(config.train_data, word2id, tag2id, config.batch_size)
dev_loader = create_data_loader(config.dev_data, word2id, tag2id, config.batch_size)
test_loader = create_data_loader(config.test_data, word2id, tag2id, config.batch_size)


# 初始化模型
model = BiLSTM_CRF(
    vocab_size=len(word2id),
    tag_size=len(tag2id),
    embedding_dim=config.embedding_dim,
    hidden_dim=config.hidden_dim
).to(config.device)

optimizer = optim.Adam(model.parameters(), lr=config.learning_rate)
criterion = CrossEntropyLoss(ignore_index=0)  # 忽略padding标签
best_f1 = 0.0
early_stop_counter = 0

# 训练循环
for epoch in range(config.num_epochs):
    model.train()
    total_loss = 0
    
    for batch in tqdm(train_loader):
        inputs, targets = batch
        inputs = inputs.to(config.device)
        targets = targets.to(config.device)
        
        # 前向计算
        emissions, mask = model(inputs, targets)
        loss = criterion(emissions.view(-1, emissions.size(-1)), targets.view(-1))
        
        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)  # 梯度裁剪
        optimizer.step()
        
        total_loss += loss.item()
    
    # 验证集评估
    raw_metrics = batch_evaluate(model, dev_loader, id2tag, config.device)
    current_f1 = raw_metrics['macro']['f1']
    
    # 保存最佳模型
    if current_f1 > best_f1:
        best_f1 = current_f1
        torch.save(model.state_dict(), config.model_save_path)
        early_stop_counter = 0
    else:
        early_stop_counter += 1
    
    print(f"Epoch {epoch+1}/{config.num_epochs} | Loss: {total_loss/len(train_loader):.4f} | Val F1: {current_f1:.4f}")
    
    # 早停机制
    if early_stop_counter >= config.early_stop_patience:
        print("Early stopping triggered")
        break
# 在测试集上进行评估并打印报告
test_metrics = batch_evaluate(model, test_loader, id2tag, config.device)
print("Test set evaluation:")
print_report(test_metrics)

print("Training completed. Best validation F1:", best_f1)