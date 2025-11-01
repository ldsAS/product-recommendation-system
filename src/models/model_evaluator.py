"""
模型評估器
實作 Precision@K, Recall@K, NDCG@K 等推薦系統評估指標
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, log_loss, confusion_matrix
)
import logging

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """模型評估器類別"""
    
    def __init__(self):
        """初始化模型評估器"""
        logger.info("模型評估器初始化")
    
    def calculate_precision_at_k(
        self,
        y_true: List[List[str]],
        y_pred: List[List[str]],
        k: int = 5
    ) -> float:
        """
        計算 Precision@K
        
        Args:
            y_true: 真實相關項目列表的列表
            y_pred: 預測項目列表的列表
            k: K 值
            
        Returns:
            Precision@K 分數
        """
        precisions = []
        
        for true_items, pred_items in zip(y_true, y_pred):
            if len(pred_items) == 0:
                precisions.append(0.0)
                continue
            
            # 取前 K 個預測
            pred_k = pred_items[:k]
            
            # 計算命中數
            hits = len(set(pred_k) & set(true_items))
            
            # Precision@K = 命中數 / K
            precision = hits / min(k, len(pred_k))
            precisions.append(precision)
        
        return np.mean(precisions)
    
    def calculate_recall_at_k(
        self,
        y_true: List[List[str]],
        y_pred: List[List[str]],
        k: int = 5
    ) -> float:
        """
        計算 Recall@K
        
        Args:
            y_true: 真實相關項目列表的列表
            y_pred: 預測項目列表的列表
            k: K 值
            
        Returns:
            Recall@K 分數
        """
        recalls = []
        
        for true_items, pred_items in zip(y_true, y_pred):
            if len(true_items) == 0:
                continue
            
            # 取前 K 個預測
            pred_k = pred_items[:k]
            
            # 計算命中數
            hits = len(set(pred_k) & set(true_items))
            
            # Recall@K = 命中數 / 真實相關項目數
            recall = hits / len(true_items)
            recalls.append(recall)
        
        return np.mean(recalls) if recalls else 0.0
    
    def calculate_ndcg_at_k(
        self,
        y_true: List[List[str]],
        y_pred: List[List[str]],
        k: int = 5
    ) -> float:
        """
        計算 NDCG@K (Normalized Discounted Cumulative Gain)
        
        Args:
            y_true: 真實相關項目列表的列表
            y_pred: 預測項目列表的列表
            k: K 值
            
        Returns:
            NDCG@K 分數
        """
        ndcgs = []
        
        for true_items, pred_items in zip(y_true, y_pred):
            if len(true_items) == 0:
                continue
            
            # 取前 K 個預測
            pred_k = pred_items[:k]
            
            # 計算 DCG
            dcg = 0.0
            for i, item in enumerate(pred_k):
                if item in true_items:
                    # rel = 1 if relevant, 0 otherwise
                    # DCG = sum(rel / log2(i+2))
                    dcg += 1.0 / np.log2(i + 2)
            
            # 計算 IDCG (理想情況下的 DCG)
            idcg = 0.0
            for i in range(min(len(true_items), k)):
                idcg += 1.0 / np.log2(i + 2)
            
            # NDCG = DCG / IDCG
            ndcg = dcg / idcg if idcg > 0 else 0.0
            ndcgs.append(ndcg)
        
        return np.mean(ndcgs) if ndcgs else 0.0
    
    def calculate_map_at_k(
        self,
        y_true: List[List[str]],
        y_pred: List[List[str]],
        k: int = 5
    ) -> float:
        """
        計算 MAP@K (Mean Average Precision)
        
        Args:
            y_true: 真實相關項目列表的列表
            y_pred: 預測項目列表的列表
            k: K 值
            
        Returns:
            MAP@K 分數
        """
        aps = []
        
        for true_items, pred_items in zip(y_true, y_pred):
            if len(true_items) == 0:
                continue
            
            # 取前 K 個預測
            pred_k = pred_items[:k]
            
            # 計算 Average Precision
            hits = 0
            sum_precisions = 0.0
            
            for i, item in enumerate(pred_k):
                if item in true_items:
                    hits += 1
                    precision_at_i = hits / (i + 1)
                    sum_precisions += precision_at_i
            
            ap = sum_precisions / min(len(true_items), k) if len(true_items) > 0 else 0.0
            aps.append(ap)
        
        return np.mean(aps) if aps else 0.0
    
    def calculate_hit_rate_at_k(
        self,
        y_true: List[List[str]],
        y_pred: List[List[str]],
        k: int = 5
    ) -> float:
        """
        計算 Hit Rate@K (至少命中一個的比例)
        
        Args:
            y_true: 真實相關項目列表的列表
            y_pred: 預測項目列表的列表
            k: K 值
            
        Returns:
            Hit Rate@K 分數
        """
        hits = 0
        total = 0
        
        for true_items, pred_items in zip(y_true, y_pred):
            if len(true_items) == 0:
                continue
            
            # 取前 K 個預測
            pred_k = pred_items[:k]
            
            # 檢查是否至少命中一個
            if len(set(pred_k) & set(true_items)) > 0:
                hits += 1
            
            total += 1
        
        return hits / total if total > 0 else 0.0
    
    def calculate_classification_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_pred_proba: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        計算分類指標
        
        Args:
            y_true: 真實標籤
            y_pred: 預測標籤
            y_pred_proba: 預測機率
            
        Returns:
            指標字典
        """
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1_score': f1_score(y_true, y_pred, zero_division=0),
        }
        
        # 如果有預測機率，計算 AUC 和 Log Loss
        if y_pred_proba is not None:
            try:
                metrics['auc'] = roc_auc_score(y_true, y_pred_proba)
                metrics['log_loss'] = log_loss(y_true, y_pred_proba)
            except:
                pass
        
        return metrics
    
    def evaluate_model(
        self,
        model: Any,
        test_df: pd.DataFrame,
        member_features_df: Optional[pd.DataFrame] = None,
        product_features_df: Optional[pd.DataFrame] = None,
        k: int = 5
    ) -> Dict[str, float]:
        """
        評估模型（完整評估）
        
        Args:
            model: 模型實例
            test_df: 測試資料
            member_features_df: 會員特徵
            product_features_df: 產品特徵
            k: K 值
            
        Returns:
            評估指標字典
        """
        logger.info("=" * 60)
        logger.info("開始模型評估")
        logger.info("=" * 60)
        
        # 預測
        if hasattr(model, 'predict_proba'):
            # 機器學習模型
            y_pred_proba = model.predict_proba(
                test_df,
                member_features_df,
                product_features_df
            )
            y_pred = (y_pred_proba > 0.5).astype(int)
            y_true = test_df['label'].values
            
            # 計算分類指標
            metrics = self.calculate_classification_metrics(
                y_true, y_pred, y_pred_proba
            )
            
        else:
            # 協同過濾模型
            metrics = {}
        
        # 計算推薦指標（需要準備推薦列表）
        # 這裡簡化處理，實際應用中需要為每個會員生成推薦列表
        
        logger.info("=" * 60)
        logger.info("評估結果:")
        for metric_name, value in metrics.items():
            logger.info(f"  {metric_name}: {value:.4f}")
        logger.info("=" * 60)
        
        return metrics
    
    def evaluate_recommendations(
        self,
        recommendations: Dict[str, List[str]],
        ground_truth: Dict[str, List[str]],
        k: int = 5
    ) -> Dict[str, float]:
        """
        評估推薦結果
        
        Args:
            recommendations: {會員ID: [推薦產品ID列表]}
            ground_truth: {會員ID: [真實購買產品ID列表]}
            k: K 值
            
        Returns:
            評估指標字典
        """
        logger.info(f"評估推薦結果 (K={k})...")
        
        # 準備資料
        y_true = []
        y_pred = []
        
        for member_id in recommendations.keys():
            if member_id in ground_truth:
                y_true.append(ground_truth[member_id])
                y_pred.append(recommendations[member_id])
        
        if not y_true:
            logger.warning("沒有可評估的資料")
            return {}
        
        # 計算指標
        metrics = {
            f'precision_at_{k}': self.calculate_precision_at_k(y_true, y_pred, k),
            f'recall_at_{k}': self.calculate_recall_at_k(y_true, y_pred, k),
            f'ndcg_at_{k}': self.calculate_ndcg_at_k(y_true, y_pred, k),
            f'map_at_{k}': self.calculate_map_at_k(y_true, y_pred, k),
            f'hit_rate_at_{k}': self.calculate_hit_rate_at_k(y_true, y_pred, k),
        }
        
        logger.info("推薦評估結果:")
        for metric_name, value in metrics.items():
            logger.info(f"  {metric_name}: {value:.4f}")
        
        return metrics
    
    def generate_evaluation_report(
        self,
        metrics: Dict[str, float],
        model_name: str = "Model"
    ) -> str:
        """
        生成評估報告
        
        Args:
            metrics: 評估指標字典
            model_name: 模型名稱
            
        Returns:
            報告文字
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append(f"{model_name} 評估報告")
        report_lines.append("=" * 60)
        
        # 分類指標
        classification_metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'auc', 'log_loss']
        has_classification = any(m in metrics for m in classification_metrics)
        
        if has_classification:
            report_lines.append("\n分類指標:")
            for metric in classification_metrics:
                if metric in metrics:
                    report_lines.append(f"  {metric}: {metrics[metric]:.4f}")
        
        # 推薦指標
        recommendation_metrics = [k for k in metrics.keys() if '@' in k]
        if recommendation_metrics:
            report_lines.append("\n推薦指標:")
            for metric in recommendation_metrics:
                report_lines.append(f"  {metric}: {metrics[metric]:.4f}")
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def compare_models(
        self,
        metrics_dict: Dict[str, Dict[str, float]]
    ) -> pd.DataFrame:
        """
        比較多個模型
        
        Args:
            metrics_dict: {模型名稱: 指標字典}
            
        Returns:
            比較結果 DataFrame
        """
        logger.info("比較模型...")
        
        comparison_df = pd.DataFrame(metrics_dict).T
        
        logger.info("\n模型比較:")
        logger.info(comparison_df.to_string())
        
        return comparison_df


def main():
    """測試模型評估器"""
    import logging
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("測試模型評估器")
    print("=" * 60)
    
    # 建立評估器
    evaluator = ModelEvaluator()
    
    # 測試推薦指標
    print("\n測試推薦指標...")
    
    # 模擬資料
    y_true = [
        ['P1', 'P2', 'P3'],
        ['P4', 'P5'],
        ['P1', 'P6', 'P7']
    ]
    
    y_pred = [
        ['P1', 'P2', 'P8', 'P9', 'P10'],
        ['P4', 'P11', 'P12', 'P13', 'P14'],
        ['P15', 'P1', 'P16', 'P6', 'P17']
    ]
    
    # 計算指標
    precision = evaluator.calculate_precision_at_k(y_true, y_pred, k=5)
    recall = evaluator.calculate_recall_at_k(y_true, y_pred, k=5)
    ndcg = evaluator.calculate_ndcg_at_k(y_true, y_pred, k=5)
    map_score = evaluator.calculate_map_at_k(y_true, y_pred, k=5)
    hit_rate = evaluator.calculate_hit_rate_at_k(y_true, y_pred, k=5)
    
    print(f"\nPrecision@5: {precision:.4f}")
    print(f"Recall@5: {recall:.4f}")
    print(f"NDCG@5: {ndcg:.4f}")
    print(f"MAP@5: {map_score:.4f}")
    print(f"Hit Rate@5: {hit_rate:.4f}")
    
    # 測試分類指標
    print("\n測試分類指標...")
    y_true_binary = np.array([1, 0, 1, 1, 0, 1, 0, 0, 1, 1])
    y_pred_binary = np.array([1, 0, 1, 0, 0, 1, 1, 0, 1, 1])
    y_pred_proba = np.array([0.9, 0.1, 0.8, 0.4, 0.2, 0.7, 0.6, 0.3, 0.85, 0.75])
    
    metrics = evaluator.calculate_classification_metrics(
        y_true_binary, y_pred_binary, y_pred_proba
    )
    
    for metric_name, value in metrics.items():
        print(f"{metric_name}: {value:.4f}")
    
    print("\n" + "=" * 60)
    print("✓ 模型評估器測試完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
