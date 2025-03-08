import torch
import torch.nn as nn
import torch.nn.functional as F

class BiLSTM_CRF(nn.Module):
    """双向LSTM + CRF模型"""
    def __init__(self, vocab_size, tag_size, embedding_dim, hidden_dim, num_layers=3, dropout=0.5):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.lstm = nn.LSTM(
            embedding_dim,
            hidden_dim // 2,
            num_layers=num_layers,
            bidirectional=True,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        self.hidden2tag = nn.Linear(hidden_dim, tag_size)
        self.dropout = nn.Dropout(dropout)
        self.crf = CRF(tag_size)
        
    def forward(self, x, tags=None):
        # 生成mask（非padding位置为1）
        mask = (x != 0).float().to(x.device)
        
        # 词嵌入
        embeds = self.embedding(x)  # (batch_size, seq_len, embedding_dim)
        embeds = self.dropout(embeds)
        # LSTM编码
        lstm_out, _ = self.lstm(embeds)  # (batch_size, seq_len, hidden_dim)
        lstm_out = self.dropout(lstm_out)
        # 发射分数
        emissions = self.hidden2tag(lstm_out)  # (batch_size, seq_len, num_tags)
        # 训练模式
        if tags is not None:
            return emissions, mask
        
        # 预测模式
        return self.crf.decode(emissions, mask)

class CRF(nn.Module):
    """PyTorch实现的CRF层，支持CUDA加速"""
    def __init__(self, num_tags):
        super().__init__()
        self.num_tags = num_tags
        self.transitions = nn.Parameter(torch.empty(num_tags, num_tags))
        self.start_transitions = nn.Parameter(torch.empty(num_tags))
        self.end_transitions = nn.Parameter(torch.empty(num_tags))
        
        nn.init.xavier_normal_(self.transitions)
        nn.init.normal_(self.start_transitions)
        nn.init.normal_(self.end_transitions)

    def forward(self, emissions, tags, mask):
        """计算负对数似然损失"""
        batch_size, seq_length, _ = emissions.shape
        
        # 将输入转换为适合CUDA的类型
        emissions = emissions.float()
        tags = tags.long()
        mask = mask.float()
        
        # 计算配分函数（前向算法）
        log_Z = self._compute_log_partition(emissions, mask)
        
        # 计算目标路径得分
        score = self._compute_score(emissions, tags, mask)
        
        # 负对数似然
        nll = (log_Z - score) / batch_size
        return nll.mean()

    def _compute_score(self, emissions, tags, mask):
        """计算目标路径得分"""
        batch_size, seq_length, _ = emissions.shape
        
        # 初始得分
        score = self.start_transitions[tags[:, 0]]
        
        # 转移得分 + 发射得分
        for t in range(seq_length - 1):
            current_tag = tags[:, t]
            next_tag = tags[:, t+1]
            score += self.transitions[current_tag, next_tag] * mask[:, t+1]
            score += emissions[:, t].gather(1, current_tag.unsqueeze(1)).squeeze(1) * mask[:, t]
        
        # 最后一步的发射得分和结束转移
        last_tag = tags[:, seq_length - 1]
        score += emissions[:, -1].gather(1, last_tag.unsqueeze(1)).squeeze(1) * mask[:, -1]
        score += self.end_transitions[last_tag] * mask[:, -1]
        return score.sum()

    def _compute_log_partition(self, emissions, mask):
        """前向算法计算配分函数"""
        batch_size, seq_length, num_tags = emissions.shape
        
        # 初始化
        log_alpha = self.start_transitions + emissions[:, 0]
        
        for t in range(1, seq_length):
            emit_scores = emissions[:, t].unsqueeze(2)  # (batch_size, num_tags, 1)
            trans_scores = self.transitions.unsqueeze(0)  # (1, num_tags, num_tags)
            
            # 数值稳定的logsumexp
            combined = log_alpha.unsqueeze(2) + emit_scores + trans_scores
            log_alpha = torch.logsumexp(combined, dim=1)
            
            # 应用mask
            mask_t = mask[:, t].unsqueeze(1)
            log_alpha = log_alpha * mask_t + (1 - mask_t) * log_alpha.detach()
        
        # 添加结束转移
        log_Z = torch.logsumexp(log_alpha + self.end_transitions.unsqueeze(0), dim=1)
        return log_Z.sum()

    def decode(self, emissions, mask):
        """维特比解码最佳路径"""
        batch_size, seq_length, _ = emissions.shape
        emissions = emissions.float()
        mask = mask.float()
        
        # 初始化
        viterbi = torch.zeros(batch_size, seq_length, self.num_tags).to(emissions.device)
        pointers = torch.zeros(batch_size, seq_length, self.num_tags).long().to(emissions.device)
        
        # 初始步
        viterbi[:, 0] = self.start_transitions + emissions[:, 0]
        
        # 递推步
        for t in range(1, seq_length):
            trans_scores = self.transitions.unsqueeze(0)  # (1, num_tags, num_tags)
            scores = viterbi[:, t-1].unsqueeze(2) + trans_scores  # (batch_size, num_tags, num_tags)
            max_scores, pointers[:, t] = torch.max(scores, dim=1)
            viterbi[:, t] = max_scores + emissions[:, t] * mask[:, t].unsqueeze(-1)
        
        # 回溯路径
        best_paths = []
        max_score, best_tag = torch.max(viterbi[:, -1] + self.end_transitions, dim=1)
        
        for b in range(batch_size):
            path = [best_tag[b].item()]
            for t in reversed(range(1, seq_length)):
                path.append(pointers[b, t, path[-1]].item())
            path.reverse()
            best_paths.append(path)
        
        return torch.tensor(best_paths, dtype=torch.long, device=emissions.device)
