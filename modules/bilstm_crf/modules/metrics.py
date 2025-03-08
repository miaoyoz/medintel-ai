import numpy as np
import torch
from collections import defaultdict

def get_entities(seq, id2tag):
    """从标签序列中提取实体"""
    entities = []
    current_entity = None
    
    for pos, tag_id in enumerate(seq):
        # 跳过padding位置
        if tag_id == 0: 
            continue
        
        tag = id2tag[tag_id]
        
        # 处理B标签
        if tag.startswith('B_'):
            if current_entity is not None:
                entities.append(current_entity)
            current_entity = {
                'start': pos,
                'end': pos + 1,
                'type': tag[2:]
            }
        # 处理I标签
        elif tag.startswith('I_'):
            if current_entity is not None and current_entity['type'] == tag[2:]:
                current_entity['end'] = pos + 1
            else:
                # 无效的I标签，重置当前实体
                if current_entity is not None:
                    entities.append(current_entity)
                current_entity = None
        # 处理O标签
        else:
            if current_entity is not None:
                entities.append(current_entity)
            current_entity = None
            
    # 处理最后一个实体
    if current_entity is not None:
        entities.append(current_entity)
        
    return entities

def compute_metrics(true_seqs, pred_seqs, id2tag):
    """计算实体级别的评估指标"""
    # 统计各类型的TP、FP、FN
    stats = defaultdict(lambda: {'TP': 0, 'FP': 0, 'FN': 0})
    
    for true_seq, pred_seq in zip(true_seqs, pred_seqs):
        true_entities = get_entities(true_seq, id2tag)
        pred_entities = get_entities(pred_seq, id2tag)
        
        # 统计真实实体
        for ent in true_entities:
            stats[ent['type']]['FN'] += 1  # 先假设未匹配
            
        # 统计预测实体
        for ent in pred_entities:
            stats[ent['type']]['FP'] += 1  # 先假设未匹配
            
        # 寻找匹配的实体
        for pred_ent in pred_entities:
            for true_ent in true_entities:
                if (pred_ent['start'] == true_ent['start'] and 
                    pred_ent['end'] == true_ent['end'] and 
                    pred_ent['type'] == true_ent['type']):
                    stats[pred_ent['type']]['TP'] += 1
                    stats[pred_ent['type']]['FP'] -= 1
                    stats[true_ent['type']]['FN'] -= 1
                    break
                
    # 计算宏平均
    total_tp = total_fp = total_fn = 0
    for cat in stats:
        total_tp += stats[cat]['TP']
        total_fp += stats[cat]['FP']
        total_fn += stats[cat]['FN']
        
    precision = total_tp / (total_tp + total_fp + 1e-10)
    recall = total_tp / (total_tp + total_fn + 1e-10)
    f1 = 2 * precision * recall / (precision + recall + 1e-10)
    
    # 计算微平均（按类别）
    micro_metrics = {}
    for cat in stats:
        tp = stats[cat]['TP']
        fp = stats[cat]['FP']
        fn = stats[cat]['FN']
        
        micro_precision = tp / (tp + fp + 1e-10)
        micro_recall = tp / (tp + fn + 1e-10)
        micro_f1 = 2 * micro_precision * micro_recall / (micro_precision + micro_recall + 1e-10)
        
        micro_metrics[cat] = {
            'precision': round(micro_precision, 4),
            'recall': round(micro_recall, 4),
            'f1': round(micro_f1, 4),
            'support': tp + fn
        }
    
    return {
        'macro': {
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1': round(f1, 4)
        },
        'micro': micro_metrics
    }

def batch_evaluate(model, data_loader, id2tag, device='cuda'):
    """批量评估模型
    
    Args:
        model: 训练好的模型
        data_loader: 数据加载器
        id2tag (dict): ID到标签的映射
        device: 计算设备
        
    Returns:
        dict: 评估指标结果
    """
    model.eval()
    true_seqs = []
    pred_seqs = []
    
    with torch.no_grad():
        for inputs, targets in data_loader:
            inputs = inputs.to(device)
            targets = targets.cpu().numpy().tolist()
            
            # 获取预测结果
            preds = model(inputs).cpu().numpy().tolist()
            
            # 收集结果
            true_seqs.extend(targets)
            pred_seqs.extend(preds)
    
    # 计算指标
    return compute_metrics(true_seqs, pred_seqs, id2tag)

def print_report(metrics):
    """打印格式化的评估报告"""
    print("\n=== Macro Metrics ===")
    print(f"Precision: {metrics['macro']['precision']:.4f}")
    print(f"Recall:    {metrics['macro']['recall']:.4f}")
    print(f"F1 Score:  {metrics['macro']['f1']:.4f}")
    
    print("\n=== Micro Metrics ===")
    print("{:<15} {:<10} {:<10} {:<10} {:<10}".format(
        "Category", "Precision", "Recall", "F1", "Support"))
    
    for cat in metrics['micro']:
        print("{:<15} {:<10.4f} {:<10.4f} {:<10.4f} {:<10}".format(
            cat,
            metrics['micro'][cat]['precision'],
            metrics['micro'][cat]['recall'],
            metrics['micro'][cat]['f1'],
            metrics['micro'][cat]['support']
        ))