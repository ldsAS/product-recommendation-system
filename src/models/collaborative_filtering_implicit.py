"""
協同過濾模型 - 使用 Implicit 庫實作
這是 collaborative_filtering.py 的替代版本，使用 implicit 而非 surprise
"""
import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Optional
import logging
import pickle
from pathlib import Path
from scipy.sparse import csr_matrix

try:
    from implicit.als import AlternatingLeastSquares
    from implicit.bpr import BayesianPersonalizedRanking
    IMPLICIT_AVAILABLE = True
except ImportError:
    IMPLICIT_AVAILABLE = False
    logging.warning("Implicit 庫未安裝，協同過濾功能將不可用")

from src.config import settings

logger = logging.getLogger(__name__)


class CollaborativeFilteringModel:
    """協同過濾模型類別 - 使用 Implicit 實作"""
    
    def __init__(
        self,
        algorithm: str = 'als',
        n_factors: int = 100,
        n_epochs: int = 20,
        lr_all: float = 0.005,  # 保留參數以相容舊 API
        reg_all: float = 0.02,   # 保留參數以相容舊 API
        random_state: Optional[int] = None
    ):
        """
        初始化協同過濾模型
        
        Args:
            algorithm: 算法類型 ('als' 或 'bpr')
            n_factors: 潛在因子數量
            n_epochs: 訓練輪數
            lr_all: 學習率（僅用於相容性）
            reg_all: 正則化參數
            random_state: 隨機種子
        """
        if not IMPLICIT_AVAILABLE:
            raise ImportError("請安裝 implicit: pip install implicit")
        
        self.algorithm = algorithm.lower()
        self.n_factors = n_factors
        self.n_epochs = n_epochs
        self.lr_all = lr_all
        self.reg_all = reg_all
        self.random_state = random_state or settings.RANDOM_SEED
        
        # 初始化模型
        if self.algorithm == 'als' or self.algorithm == 'svd':  # svd 映射到 als
            self.model = AlternatingLeastSquares(
                factors=n_factors,
                iterations=n_epochs,
                regularization=reg_all,
                random_state=self.random_state
            )
        elif self.algorithm == 'bpr' or self.algorithm == 'nmf':  # nmf 映射到 bpr
            self.model = BayesianPersonalizedRanking(
                factors=n_factors,
                iterations=n_epochs,
                regularization=reg_all,
                random_state=self.random_state
            )
        else:
            raise ValueError(f"不支援的算法: {algorithm}")
        
        self.is_trained = False
        self.member_ids = []
        self.product_ids = []
        self.member_id_map = {}  # member_id -> index
        self.product_id_map = {}  # product_id -> index
        self.user_item_matrix = None
        
        logger.info(f"協同過濾模型初始化 ({self.algorithm.upper()})")
        logger.info(f"  潛在因子數: {n_factors}")
        logger.info(f"  訓練輪數: {n_epochs}")
    
    def prepare_data(
        self,
        df: pd.DataFrame,
        member_col: str = 'member_id',
        product_col: str = 'stock_id',
        rating_col: Optional[str] = None
    ) -> csr_matrix:
        """
        準備稀疏矩陣格式的資料
        
        Args:
            df: 輸入 DataFrame
            member_col: 會員 ID 欄位
            product_col: 產品 ID 欄位
            rating_col: 評分欄位（None 表示使用隱式反饋）
            
        Returns:
            稀疏矩陣 (user x item)
        """
        logger.info("準備協同過濾資料...")
        
        # 如果沒有評分欄位，使用隱式反饋（設為 1）
        if rating_col is None or rating_col not in df.columns:
            df = df.copy()
            df['rating'] = 1.0
            rating_col = 'rating'
        
        # 選擇必要欄位
        data_df = df[[member_col, product_col, rating_col]].copy()
        data_df = data_df.dropna()
        
        # 建立 ID 映射
        self.member_ids = data_df[member_col].unique().tolist()
        self.product_ids = data_df[product_col].unique().tolist()
        
        self.member_id_map = {mid: idx for idx, mid in enumerate(self.member_ids)}
        self.product_id_map = {pid: idx for idx, pid in enumerate(self.product_ids)}
        
        logger.info(f"  會員數: {len(self.member_ids)}")
        logger.info(f"  產品數: {len(self.product_ids)}")
        logger.info(f"  交互數: {len(data_df)}")
        
        # 轉換為索引
        data_df['user_idx'] = data_df[member_col].map(self.member_id_map)
        data_df['item_idx'] = data_df[product_col].map(self.product_id_map)
        
        # 建立稀疏矩陣
        user_item_matrix = csr_matrix(
            (data_df[rating_col].values,
             (data_df['user_idx'].values, data_df['item_idx'].values)),
            shape=(len(self.member_ids), len(self.product_ids))
        )
        
        return user_item_matrix
    
    def train(
        self,
        train_df: pd.DataFrame,
        member_col: str = 'member_id',
        product_col: str = 'stock_id',
        rating_col: Optional[str] = None
    ):
        """
        訓練模型
        
        Args:
            train_df: 訓練資料 DataFrame
            member_col: 會員 ID 欄位
            product_col: 產品 ID 欄位
            rating_col: 評分欄位
        """
        logger.info("=" * 60)
        logger.info("開始訓練協同過濾模型")
        logger.info("=" * 60)
        
        # 準備資料
        self.user_item_matrix = self.prepare_data(
            train_df, member_col, product_col, rating_col
        )
        
        # 訓練模型
        logger.info("訓練中...")
        self.model.fit(self.user_item_matrix)
        
        self.is_trained = True
        
        logger.info("=" * 60)
        logger.info("協同過濾模型訓練完成")
        logger.info("=" * 60)
    
    def predict(
        self,
        member_id: str,
        product_id: str
    ) -> float:
        """
        預測單個會員對單個產品的評分
        
        Args:
            member_id: 會員 ID
            product_id: 產品 ID
            
        Returns:
            預測評分
        """
        if not self.is_trained:
            raise ValueError("模型尚未訓練")
        
        # 檢查 ID 是否存在
        if member_id not in self.member_id_map:
            return 0.0
        if product_id not in self.product_id_map:
            return 0.0
        
        user_idx = self.member_id_map[member_id]
        item_idx = self.product_id_map[product_id]
        
        # 計算預測分數
        user_vector = self.model.user_factors[user_idx]
        item_vector = self.model.item_factors[item_idx]
        score = np.dot(user_vector, item_vector)
        
        return float(score)
    
    def recommend(
        self,
        member_id: str,
        n: int = 5,
        exclude_known: bool = True,
        known_products: Optional[List[str]] = None
    ) -> List[Tuple[str, float]]:
        """
        為會員推薦產品
        
        Args:
            member_id: 會員 ID
            n: 推薦數量
            exclude_known: 是否排除已知產品
            known_products: 已知產品列表
            
        Returns:
            [(產品ID, 預測分數), ...]
        """
        if not self.is_trained:
            raise ValueError("模型尚未訓練")
        
        if member_id not in self.member_id_map:
            logger.warning(f"會員 {member_id} 不在訓練資料中")
            return []
        
        user_idx = self.member_id_map[member_id]
        
        # 使用 implicit 的推薦功能
        # filter_already_liked_items 參數控制是否過濾已知項目
        ids, scores = self.model.recommend(
            user_idx,
            self.user_item_matrix[user_idx],
            N=n * 2,  # 多取一些以便過濾
            filter_already_liked_items=exclude_known
        )
        
        # 轉換回原始 ID
        recommendations = []
        for item_idx, score in zip(ids, scores):
            product_id = self.product_ids[item_idx]
            
            # 額外過濾已知產品
            if exclude_known and known_products and product_id in known_products:
                continue
            
            recommendations.append((product_id, float(score)))
            
            if len(recommendations) >= n:
                break
        
        return recommendations
    
    def batch_recommend(
        self,
        member_ids: List[str],
        n: int = 5,
        exclude_known: bool = True,
        known_products_dict: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        批次推薦
        
        Args:
            member_ids: 會員 ID 列表
            n: 每個會員的推薦數量
            exclude_known: 是否排除已知產品
            known_products_dict: 會員已知產品字典
            
        Returns:
            {會員ID: [(產品ID, 分數), ...]}
        """
        logger.info(f"批次推薦 {len(member_ids)} 個會員...")
        
        recommendations = {}
        
        for member_id in member_ids:
            known_products = None
            if known_products_dict and member_id in known_products_dict:
                known_products = known_products_dict[member_id]
            
            try:
                recs = self.recommend(
                    member_id,
                    n=n,
                    exclude_known=exclude_known,
                    known_products=known_products
                )
                recommendations[member_id] = recs
            except Exception as e:
                logger.warning(f"會員 {member_id} 推薦失敗: {e}")
                recommendations[member_id] = []
        
        logger.info(f"批次推薦完成")
        
        return recommendations
    
    def save(self, file_path: Path):
        """
        儲存模型
        
        Args:
            file_path: 儲存路徑
        """
        logger.info(f"儲存模型到 {file_path}")
        
        model_data = {
            'model': self.model,
            'algorithm': self.algorithm,
            'n_factors': self.n_factors,
            'n_epochs': self.n_epochs,
            'is_trained': self.is_trained,
            'member_ids': self.member_ids,
            'product_ids': self.product_ids,
            'member_id_map': self.member_id_map,
            'product_id_map': self.product_id_map,
            'user_item_matrix': self.user_item_matrix,
        }
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info("模型儲存完成")
    
    @classmethod
    def load(cls, file_path: Path) -> 'CollaborativeFilteringModel':
        """
        載入模型
        
        Args:
            file_path: 模型檔案路徑
            
        Returns:
            CollaborativeFilteringModel 實例
        """
        logger.info(f"載入模型從 {file_path}")
        
        with open(file_path, 'rb') as f:
            model_data = pickle.load(f)
        
        # 建立實例
        instance = cls(
            algorithm=model_data['algorithm'],
            n_factors=model_data['n_factors'],
            n_epochs=model_data['n_epochs']
        )
        
        # 恢復狀態
        instance.model = model_data['model']
        instance.is_trained = model_data['is_trained']
        instance.member_ids = model_data['member_ids']
        instance.product_ids = model_data['product_ids']
        instance.member_id_map = model_data['member_id_map']
        instance.product_id_map = model_data['product_id_map']
        instance.user_item_matrix = model_data['user_item_matrix']
        
        logger.info("模型載入完成")
        
        return instance


def main():
    """測試協同過濾模型"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from src.data_processing.data_loader import DataLoader
    from src.data_processing.data_cleaner import DataCleaner
    from src.models.training_data_builder import TrainingDataBuilder
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("測試協同過濾模型 (Implicit)")
    print("=" * 60)
    
    if not IMPLICIT_AVAILABLE:
        print("\n✗ Implicit 庫未安裝")
        print("請執行: pip install implicit")
        return
    
    # 載入資料
    print("\n載入資料...")
    loader = DataLoader()
    df = loader.merge_data(max_rows=1000)
    
    if df.empty:
        print("✗ 資料載入失敗")
        return
    
    # 清理資料
    print("\n清理資料...")
    cleaner = DataCleaner()
    df = cleaner.clean_all(df)
    
    # 準備訓練資料
    print("\n準備訓練資料...")
    builder = TrainingDataBuilder()
    data_dict = builder.prepare_training_data(df)
    
    # 建立模型
    print("\n建立協同過濾模型...")
    cf_model = CollaborativeFilteringModel(
        algorithm='als',
        n_factors=50,
        n_epochs=10
    )
    
    # 訓練模型
    print("\n訓練模型...")
    train_df = data_dict['train']
    # 只使用正樣本訓練協同過濾
    train_positive = train_df[train_df['label'] == 1]
    cf_model.train(train_positive)
    
    # 測試推薦
    print("\n測試推薦...")
    if len(cf_model.member_ids) > 0:
        test_member = cf_model.member_ids[0]
        recommendations = cf_model.recommend(test_member, n=5)
        
        print(f"\n為會員 {test_member} 推薦:")
        for i, (product_id, score) in enumerate(recommendations, 1):
            print(f"  {i}. 產品 {product_id}: {score:.4f}")
    
    print("\n" + "=" * 60)
    print("✓ 協同過濾模型測試完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
