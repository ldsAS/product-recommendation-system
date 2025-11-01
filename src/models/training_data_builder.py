"""
訓練資料準備器
建立會員-產品交互矩陣、負採樣和資料分割
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, Dict
from scipy.sparse import csr_matrix
from sklearn.model_selection import train_test_split
import logging

from src.config import settings

logger = logging.getLogger(__name__)


class TrainingDataBuilder:
    """訓練資料準備器類別"""
    
    def __init__(
        self,
        test_size: float = None,
        validation_size: float = None,
        negative_sample_ratio: float = None,
        random_state: int = None
    ):
        """
        初始化訓練資料準備器
        
        Args:
            test_size: 測試集比例
            validation_size: 驗證集比例
            negative_sample_ratio: 負樣本比例
            random_state: 隨機種子
        """
        self.test_size = test_size or settings.TRAIN_TEST_SPLIT
        self.validation_size = validation_size or settings.VALIDATION_SPLIT
        self.negative_sample_ratio = negative_sample_ratio or settings.NEGATIVE_SAMPLE_RATIO
        self.random_state = random_state or settings.RANDOM_SEED
        
        logger.info(f"訓練資料準備器初始化")
        logger.info(f"  測試集比例: {self.test_size}")
        logger.info(f"  驗證集比例: {self.validation_size}")
        logger.info(f"  負樣本比例: {self.negative_sample_ratio}")
        logger.info(f"  隨機種子: {self.random_state}")
    
    def create_interaction_matrix(
        self,
        df: pd.DataFrame,
        member_col: str = 'member_id',
        product_col: str = 'stock_id'
    ) -> Tuple[csr_matrix, List[str], List[str]]:
        """
        建立會員-產品交互矩陣
        
        Args:
            df: 輸入 DataFrame
            member_col: 會員 ID 欄位名稱
            product_col: 產品 ID 欄位名稱
            
        Returns:
            (稀疏矩陣, 會員ID列表, 產品ID列表)
        """
        logger.info("建立會員-產品交互矩陣...")
        
        # 確保欄位存在
        if member_col not in df.columns or product_col not in df.columns:
            raise ValueError(f"找不到必要欄位: {member_col} 或 {product_col}")
        
        # 移除缺失值
        df_clean = df[[member_col, product_col]].dropna()
        
        # 獲取唯一的會員和產品
        unique_members = df_clean[member_col].unique()
        unique_products = df_clean[product_col].unique()
        
        logger.info(f"  會員數: {len(unique_members)}")
        logger.info(f"  產品數: {len(unique_products)}")
        
        # 建立 ID 到索引的映射
        member_to_idx = {member: idx for idx, member in enumerate(unique_members)}
        product_to_idx = {product: idx for idx, product in enumerate(unique_products)}
        
        # 建立交互矩陣
        rows = []
        cols = []
        data = []
        
        for _, row in df_clean.iterrows():
            member_idx = member_to_idx[row[member_col]]
            product_idx = product_to_idx[row[product_col]]
            rows.append(member_idx)
            cols.append(product_idx)
            data.append(1)  # 交互值設為 1
        
        # 建立稀疏矩陣
        interaction_matrix = csr_matrix(
            (data, (rows, cols)),
            shape=(len(unique_members), len(unique_products))
        )
        
        logger.info(f"交互矩陣建立完成: {interaction_matrix.shape}")
        logger.info(f"  非零元素: {interaction_matrix.nnz}")
        logger.info(f"  稀疏度: {1 - interaction_matrix.nnz / (interaction_matrix.shape[0] * interaction_matrix.shape[1]):.4f}")
        
        return interaction_matrix, unique_members.tolist(), unique_products.tolist()
    
    def generate_positive_samples(
        self,
        df: pd.DataFrame,
        member_col: str = 'member_id',
        product_col: str = 'stock_id'
    ) -> pd.DataFrame:
        """
        生成正樣本（實際購買記錄）
        
        Args:
            df: 輸入 DataFrame
            member_col: 會員 ID 欄位名稱
            product_col: 產品 ID 欄位名稱
            
        Returns:
            正樣本 DataFrame
        """
        logger.info("生成正樣本...")
        
        # 選擇必要欄位
        positive_samples = df[[member_col, product_col]].copy()
        positive_samples = positive_samples.dropna()
        positive_samples = positive_samples.drop_duplicates()
        positive_samples['label'] = 1
        
        logger.info(f"正樣本數量: {len(positive_samples)}")
        
        return positive_samples
    
    def generate_negative_samples(
        self,
        df: pd.DataFrame,
        member_col: str = 'member_id',
        product_col: str = 'stock_id',
        ratio: Optional[float] = None
    ) -> pd.DataFrame:
        """
        生成負樣本（未購買的產品）
        
        Args:
            df: 輸入 DataFrame
            member_col: 會員 ID 欄位名稱
            product_col: 產品 ID 欄位名稱
            ratio: 負樣本比例（相對於正樣本）
            
        Returns:
            負樣本 DataFrame
        """
        logger.info("生成負樣本...")
        
        ratio = ratio or self.negative_sample_ratio
        
        # 獲取所有會員和產品
        all_members = df[member_col].unique()
        all_products = df[product_col].unique()
        
        # 建立會員已購買產品的集合
        member_products = df.groupby(member_col)[product_col].apply(set).to_dict()
        
        # 計算需要的負樣本數量
        positive_count = len(df[[member_col, product_col]].drop_duplicates())
        negative_count = int(positive_count * ratio)
        
        logger.info(f"  正樣本數: {positive_count}")
        logger.info(f"  目標負樣本數: {negative_count}")
        
        # 生成負樣本
        negative_samples = []
        np.random.seed(self.random_state)
        
        samples_per_member = max(1, negative_count // len(all_members))
        
        for member in all_members:
            # 獲取該會員已購買的產品
            purchased = member_products.get(member, set())
            
            # 獲取未購買的產品
            not_purchased = list(set(all_products) - purchased)
            
            if not not_purchased:
                continue
            
            # 隨機選擇負樣本
            n_samples = min(samples_per_member, len(not_purchased))
            sampled_products = np.random.choice(not_purchased, size=n_samples, replace=False)
            
            for product in sampled_products:
                negative_samples.append({
                    member_col: member,
                    product_col: product,
                    'label': 0
                })
                
                if len(negative_samples) >= negative_count:
                    break
            
            if len(negative_samples) >= negative_count:
                break
        
        negative_df = pd.DataFrame(negative_samples)
        logger.info(f"實際生成負樣本數: {len(negative_df)}")
        
        return negative_df
    
    def combine_samples(
        self,
        positive_df: pd.DataFrame,
        negative_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        合併正負樣本
        
        Args:
            positive_df: 正樣本 DataFrame
            negative_df: 負樣本 DataFrame
            
        Returns:
            合併後的 DataFrame
        """
        logger.info("合併正負樣本...")
        
        combined_df = pd.concat([positive_df, negative_df], ignore_index=True)
        
        # 打亂順序
        combined_df = combined_df.sample(frac=1, random_state=self.random_state).reset_index(drop=True)
        
        logger.info(f"合併後總樣本數: {len(combined_df)}")
        logger.info(f"  正樣本: {(combined_df['label'] == 1).sum()}")
        logger.info(f"  負樣本: {(combined_df['label'] == 0).sum()}")
        logger.info(f"  正負比例: 1:{(combined_df['label'] == 0).sum() / (combined_df['label'] == 1).sum():.2f}")
        
        return combined_df
    
    def split_data(
        self,
        df: pd.DataFrame,
        stratify_col: Optional[str] = 'label'
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        分割資料為訓練集、驗證集和測試集
        
        Args:
            df: 輸入 DataFrame
            stratify_col: 用於分層抽樣的欄位
            
        Returns:
            (訓練集, 驗證集, 測試集)
        """
        logger.info("分割資料集...")
        
        # 第一次分割：分出測試集
        stratify = df[stratify_col] if stratify_col and stratify_col in df.columns else None
        
        train_val_df, test_df = train_test_split(
            df,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=stratify
        )
        
        # 第二次分割：從訓練集中分出驗證集
        val_size_adjusted = self.validation_size / (1 - self.test_size)
        stratify_train = train_val_df[stratify_col] if stratify_col and stratify_col in train_val_df.columns else None
        
        train_df, val_df = train_test_split(
            train_val_df,
            test_size=val_size_adjusted,
            random_state=self.random_state,
            stratify=stratify_train
        )
        
        logger.info(f"資料分割完成:")
        logger.info(f"  訓練集: {len(train_df)} ({len(train_df)/len(df)*100:.1f}%)")
        logger.info(f"  驗證集: {len(val_df)} ({len(val_df)/len(df)*100:.1f}%)")
        logger.info(f"  測試集: {len(test_df)} ({len(test_df)/len(df)*100:.1f}%)")
        
        return train_df, val_df, test_df
    
    def prepare_training_data(
        self,
        df: pd.DataFrame,
        member_col: str = 'member_id',
        product_col: str = 'stock_id'
    ) -> Dict[str, pd.DataFrame]:
        """
        準備完整的訓練資料
        
        Args:
            df: 輸入 DataFrame
            member_col: 會員 ID 欄位名稱
            product_col: 產品 ID 欄位名稱
            
        Returns:
            包含訓練、驗證、測試集的字典
        """
        logger.info("=" * 60)
        logger.info("準備訓練資料")
        logger.info("=" * 60)
        
        # 生成正樣本
        positive_df = self.generate_positive_samples(df, member_col, product_col)
        
        # 生成負樣本
        negative_df = self.generate_negative_samples(df, member_col, product_col)
        
        # 合併樣本
        combined_df = self.combine_samples(positive_df, negative_df)
        
        # 分割資料
        train_df, val_df, test_df = self.split_data(combined_df)
        
        logger.info("=" * 60)
        logger.info("訓練資料準備完成")
        logger.info("=" * 60)
        
        return {
            'train': train_df,
            'validation': val_df,
            'test': test_df,
            'all': combined_df
        }
    
    def get_data_statistics(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, any]:
        """
        獲取資料統計資訊
        
        Args:
            data_dict: 資料字典
            
        Returns:
            統計資訊字典
        """
        stats = {}
        
        for name, df in data_dict.items():
            if df is None or df.empty:
                continue
            
            stats[name] = {
                'total_samples': len(df),
                'positive_samples': int((df['label'] == 1).sum()) if 'label' in df.columns else 0,
                'negative_samples': int((df['label'] == 0).sum()) if 'label' in df.columns else 0,
                'positive_ratio': float((df['label'] == 1).mean()) if 'label' in df.columns else 0,
            }
        
        return stats


def main():
    """測試訓練資料準備器"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from src.data_processing.data_loader import DataLoader
    from src.data_processing.data_cleaner import DataCleaner
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("測試訓練資料準備器")
    print("=" * 60)
    
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
    
    # 建立訓練資料準備器
    print("\n準備訓練資料...")
    builder = TrainingDataBuilder()
    
    # 準備訓練資料
    data_dict = builder.prepare_training_data(df)
    
    # 顯示統計
    print("\n資料統計:")
    stats = builder.get_data_statistics(data_dict)
    for name, stat in stats.items():
        if name == 'all':
            continue
        print(f"\n{name}:")
        print(f"  總樣本: {stat['total_samples']}")
        print(f"  正樣本: {stat['positive_samples']}")
        print(f"  負樣本: {stat['negative_samples']}")
        print(f"  正樣本比例: {stat['positive_ratio']:.2%}")
    
    # 測試交互矩陣
    print("\n建立交互矩陣...")
    matrix, members, products = builder.create_interaction_matrix(df)
    print(f"矩陣形狀: {matrix.shape}")
    print(f"非零元素: {matrix.nnz}")
    
    print("\n" + "=" * 60)
    print("✓ 訓練資料準備器測試完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
