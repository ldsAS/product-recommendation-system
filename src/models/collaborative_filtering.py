"""
協同過濾模型
使用 Surprise 庫實作 SVD 或 ALS 算法
"""
import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Optional
import logging
import pickle
from pathlib import Path

try:
    from surprise import SVD, NMF, Dataset, Reader
    from surprise.model_selection import cross_validate
    SURPRISE_AVAILABLE = True
except ImportError:
    SURPRISE_AVAILABLE = False
    logging.warning("Surprise 庫未安裝，協同過濾功能將不可用")

from src.config import settings

logger = logging.getLogger(__name__)


class CollaborativeFilteringModel:
    """協同過濾模型類別"""
    
    def __init__(
        self,
        algorithm: str = 'svd',
        n_factors: int = 100,
        n_epochs: int = 20,
        lr_all: float = 0.005,
        reg_all: float = 0.02,
        random_state: Optional[int] = None
    ):
        """
        初始化協同過濾模型
        
        Args:
            algorithm: 算法類型 ('svd' 或 'nmf')
            n_factors: 潛在因子數量
            n_epochs: 訓練輪數
            lr_all: 學習率
            reg_all: 正則化參數
            random_state: 隨機種子
        """
        if not SURPRISE_AVAILABLE:
            raise ImportError("請安裝 scikit-surprise: pip install scikit-surprise")
        
        self.algorithm = algorithm.lower()
        self.n_factors = n_factors
        self.n_epochs = n_epochs
        self.lr_all = lr_all
        self.reg_all = reg_all
        self.random_state = random_state or settings.RANDOM_SEED
        
        # 初始化模型
        if self.algorithm == 'svd':
            self.model = SVD(
                n_factors=n_factors,
                n_epochs=n_epochs,
                lr_all=lr_all,
                reg_all=reg_all,
                random_state=self.random_state
            )
        elif self.algorithm == 'nmf':
            self.model = NMF(
                n_factors=n_factors,
                n_epochs=n_epochs,
                random_state=self.random_state
            )
        else:
            raise ValueError(f"不支援的算法: {algorithm}")
        
        self.is_trained = False
        self.member_ids = []
        self.product_ids = []
        
        logger.info(f"協同過濾模型初始化 ({self.algorithm.upper()})")
        logger.info(f"  潛在因子數: {n_factors}")
        logger.info(f"  訓練輪數: {n_epochs}")
    
    def prepare_data(
        self,
        df: pd.DataFrame,
        member_col: str = 'member_id',
        product_col: str = 'stock_id',
        rating_col: Optional[str] = None
    ) -> Dataset:
        """
        準備 Surprise 格式的資料
        
        Args:
            df: 輸入 DataFrame
            member_col: 會員 ID 欄位
            product_col: 產品 ID 欄位
            rating_col: 評分欄位（None 表示使用隱式反饋）
            
        Returns:
            Surprise Dataset
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
        
        # 記錄唯一的會員和產品
        self.member_ids = data_df[member_col].unique().tolist()
        self.product_ids = data_df[product_col].unique().tolist()
        
        logger.info(f"  會員數: {len(self.member_ids)}")
        logger.info(f"  產品數: {len(self.product_ids)}")
        logger.info(f"  交互數: {len(data_df)}")
        
        # 建立 Surprise Reader
        reader = Reader(rating_scale=(0, 1))
        
        # 建立 Surprise Dataset
        dataset = Dataset.load_from_df(
            data_df[[member_col, product_col, rating_col]],
            reader
        )
        
        return dataset
    
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
        dataset = self.prepare_data(train_df, member_col, product_col, rating_col)
        
        # 建立完整訓練集
        trainset = dataset.build_full_trainset()
        
        # 訓練模型
        logger.info("訓練中...")
        self.model.fit(trainset)
        
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
        
        prediction = self.model.predict(member_id, product_id)
        return prediction.est
    
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
        
        # 獲取所有產品
        all_products = self.product_ids.copy()
        
        # 排除已知產品
        if exclude_known and known_products:
            all_products = [p for p in all_products if p not in known_products]
        
        # 預測所有產品的評分
        predictions = []
        for product_id in all_products:
            try:
                score = self.predict(member_id, product_id)
                predictions.append((product_id, score))
            except:
                continue
        
        # 排序並返回 Top N
        predictions.sort(key=lambda x: x[1], reverse=True)
        
        return predictions[:n]
    
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
    print("測試協同過濾模型")
    print("=" * 60)
    
    if not SURPRISE_AVAILABLE:
        print("\n✗ Surprise 庫未安裝")
        print("請執行: pip install scikit-surprise")
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
        algorithm='svd',
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
