"""
特徵工程器
從原始資料中提取和構建特徵
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import logging

from src.config import settings

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """特徵工程器類別"""
    
    def __init__(self, reference_date: Optional[datetime] = None):
        """
        初始化特徵工程器
        
        Args:
            reference_date: RFM 計算的參考日期，None 表示使用當前日期
        """
        self.reference_date = reference_date or datetime.now()
        logger.info(f"特徵工程器初始化，參考日期: {self.reference_date}")
    
    def calculate_rfm(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        計算 RFM 特徵 (Recency, Frequency, Monetary)
        
        Args:
            df: 包含會員和交易資訊的 DataFrame
            
        Returns:
            包含 RFM 特徵的 DataFrame
        """
        logger.info("計算 RFM 特徵...")
        
        # 確保必要欄位存在
        required_columns = ['member_id', 'date', 'actualTotal']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            # 嘗試使用替代欄位
            if 'member_id' not in df.columns and 'id_member' in df.columns:
                df['member_id'] = df['id_member']
            if 'actualTotal' not in df.columns and 'total' in df.columns:
                df['actualTotal'] = df['total']
        
        # 確保 date 是 datetime 類型
        if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # 按會員分組計算 RFM
        rfm_features = []
        
        for member_id, group in df.groupby('member_id'):
            # Recency: 最近一次購買距今天數
            if 'date' in group.columns:
                last_purchase = group['date'].max()
                if pd.notna(last_purchase):
                    recency = (self.reference_date - last_purchase).days
                else:
                    recency = 9999  # 預設值
            else:
                recency = 9999
            
            # Frequency: 購買訂單次數
            frequency = len(group)
            
            # Monetary: 平均訂單金額
            if 'actualTotal' in group.columns:
                monetary = group['actualTotal'].mean()
            else:
                monetary = 0.0
            
            rfm_features.append({
                'member_id': member_id,
                'recency': max(0, recency),  # 確保非負
                'frequency': frequency,
                'monetary': monetary
            })
        
        rfm_df = pd.DataFrame(rfm_features)
        logger.info(f"RFM 特徵計算完成，共 {len(rfm_df)} 個會員")
        
        return rfm_df
    
    def extract_product_preferences(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        提取產品偏好特徵
        
        Args:
            df: 包含會員和產品資訊的 DataFrame
            
        Returns:
            包含產品偏好特徵的 DataFrame
        """
        logger.info("提取產品偏好特徵...")
        
        product_features = []
        
        for member_id, group in df.groupby('member_id'):
            # 最常購買的產品
            if 'stock_id' in group.columns:
                favorite_products = group['stock_id'].value_counts().head(
                    settings.TOP_N_PRODUCTS
                ).index.tolist()
            else:
                favorite_products = []
            
            # 產品多樣性：購買不同產品的數量
            if 'stock_id' in group.columns:
                product_diversity = group['stock_id'].nunique()
            else:
                product_diversity = 0
            
            # 平均每單商品數
            if 'quantity' in group.columns:
                avg_items_per_order = group['quantity'].mean()
            else:
                avg_items_per_order = 0.0
            
            product_features.append({
                'member_id': member_id,
                'favorite_products': favorite_products,
                'product_diversity': product_diversity,
                'avg_items_per_order': avg_items_per_order
            })
        
        product_df = pd.DataFrame(product_features)
        logger.info(f"產品偏好特徵提取完成，共 {len(product_df)} 個會員")
        
        return product_df
    
    def extract_time_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        提取時間模式特徵
        
        Args:
            df: 包含會員和時間資訊的 DataFrame
            
        Returns:
            包含時間模式特徵的 DataFrame
        """
        logger.info("提取時間模式特徵...")
        
        # 確保 date 是 datetime 類型
        if 'date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        time_features = []
        
        for member_id, group in df.groupby('member_id'):
            # 偏好購買時段（小時）
            if 'date' in group.columns:
                hours = group['date'].dt.hour
                if len(hours) > 0 and hours.notna().any():
                    purchase_hour_preference = hours.mode().iloc[0] if len(hours.mode()) > 0 else None
                else:
                    purchase_hour_preference = None
            else:
                purchase_hour_preference = None
            
            # 偏好購買星期
            if 'date' in group.columns:
                days = group['date'].dt.dayofweek
                if len(days) > 0 and days.notna().any():
                    purchase_day_preference = days.mode().iloc[0] if len(days.mode()) > 0 else None
                else:
                    purchase_day_preference = None
            else:
                purchase_day_preference = None
            
            # 距離上次購買天數（與 recency 相同，但這裡單獨計算）
            if 'date' in group.columns:
                last_purchase = group['date'].max()
                if pd.notna(last_purchase):
                    days_since_last_purchase = (self.reference_date - last_purchase).days
                else:
                    days_since_last_purchase = 9999
            else:
                days_since_last_purchase = 9999
            
            time_features.append({
                'member_id': member_id,
                'purchase_hour_preference': purchase_hour_preference,
                'purchase_day_preference': purchase_day_preference,
                'days_since_last_purchase': max(0, days_since_last_purchase)
            })
        
        time_df = pd.DataFrame(time_features)
        logger.info(f"時間模式特徵提取完成，共 {len(time_df)} 個會員")
        
        return time_df
    
    def extract_location_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        提取地點特徵
        
        Args:
            df: 包含會員和地點資訊的 DataFrame
            
        Returns:
            包含地點特徵的 DataFrame
        """
        logger.info("提取地點特徵...")
        
        location_features = []
        
        for member_id, group in df.groupby('member_id'):
            # 偏好購買地點
            if 'loccode' in group.columns:
                preferred_location = group['loccode'].mode().iloc[0] if len(group['loccode'].mode()) > 0 else None
            else:
                preferred_location = None
            
            location_features.append({
                'member_id': member_id,
                'preferred_location': preferred_location
            })
        
        location_df = pd.DataFrame(location_features)
        logger.info(f"地點特徵提取完成，共 {len(location_df)} 個會員")
        
        return location_df
    
    def extract_member_basic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        提取會員基礎特徵
        
        Args:
            df: 包含會員資訊的 DataFrame
            
        Returns:
            包含會員基礎特徵的 DataFrame
        """
        logger.info("提取會員基礎特徵...")
        
        # 選擇會員相關欄位
        member_columns = [
            'member_id', 'member_code', 'member_name', 'phone',
            'total_consumption', 'accumulated_bonus', 'created_at', 'create_time'
        ]
        
        available_columns = [col for col in member_columns if col in df.columns]
        
        if not available_columns:
            logger.warning("沒有找到會員基礎欄位")
            return pd.DataFrame()
        
        # 去重，每個會員只保留一筆記錄
        member_df = df[available_columns].drop_duplicates(subset=['member_id']).copy()
        
        # 計算會員註冊天數
        if 'created_at' in member_df.columns:
            date_col = 'created_at'
        elif 'create_time' in member_df.columns:
            date_col = 'create_time'
        else:
            date_col = None
        
        if date_col:
            member_df[date_col] = pd.to_datetime(member_df[date_col], errors='coerce')
            member_df['member_age_days'] = (
                self.reference_date - member_df[date_col]
            ).dt.days
            member_df['member_age_days'] = member_df['member_age_days'].fillna(0).clip(lower=0)
        else:
            member_df['member_age_days'] = 0
        
        logger.info(f"會員基礎特徵提取完成，共 {len(member_df)} 個會員")
        
        return member_df
    
    def create_feature_matrix(
        self,
        df: pd.DataFrame,
        include_rfm: bool = True,
        include_product: bool = True,
        include_time: bool = True,
        include_location: bool = True,
        include_basic: bool = True
    ) -> pd.DataFrame:
        """
        建立完整的特徵矩陣
        
        Args:
            df: 輸入 DataFrame
            include_rfm: 是否包含 RFM 特徵
            include_product: 是否包含產品偏好特徵
            include_time: 是否包含時間模式特徵
            include_location: 是否包含地點特徵
            include_basic: 是否包含會員基礎特徵
            
        Returns:
            完整的特徵矩陣 DataFrame
        """
        logger.info("=" * 60)
        logger.info("建立完整特徵矩陣")
        logger.info("=" * 60)
        
        # 確保有 member_id 欄位
        if 'member_id' not in df.columns:
            if 'id_member' in df.columns:
                df['member_id'] = df['id_member']
            elif 'id' in df.columns and 'member_code' in df.columns:
                df['member_id'] = df['id']
            else:
                raise ValueError("找不到會員 ID 欄位")
        
        feature_dfs = []
        
        # 提取各類特徵
        if include_basic:
            basic_df = self.extract_member_basic_features(df)
            if not basic_df.empty:
                feature_dfs.append(basic_df)
        
        if include_rfm:
            rfm_df = self.calculate_rfm(df)
            if not rfm_df.empty:
                feature_dfs.append(rfm_df)
        
        if include_product:
            product_df = self.extract_product_preferences(df)
            if not product_df.empty:
                feature_dfs.append(product_df)
        
        if include_time:
            time_df = self.extract_time_patterns(df)
            if not time_df.empty:
                feature_dfs.append(time_df)
        
        if include_location:
            location_df = self.extract_location_features(df)
            if not location_df.empty:
                feature_dfs.append(location_df)
        
        # 合併所有特徵
        if not feature_dfs:
            logger.error("沒有提取到任何特徵")
            return pd.DataFrame()
        
        logger.info(f"合併 {len(feature_dfs)} 個特徵集...")
        feature_matrix = feature_dfs[0]
        
        for feature_df in feature_dfs[1:]:
            feature_matrix = pd.merge(
                feature_matrix,
                feature_df,
                on='member_id',
                how='outer'
            )
        
        # 填補缺失值
        numeric_columns = feature_matrix.select_dtypes(include=[np.number]).columns
        feature_matrix[numeric_columns] = feature_matrix[numeric_columns].fillna(0)
        
        logger.info("=" * 60)
        logger.info(f"特徵矩陣建立完成")
        logger.info(f"  會員數: {len(feature_matrix)}")
        logger.info(f"  特徵數: {len(feature_matrix.columns)}")
        logger.info(f"  特徵列表: {list(feature_matrix.columns)}")
        logger.info("=" * 60)
        
        return feature_matrix
    
    def create_product_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        建立產品特徵
        
        Args:
            df: 包含產品資訊的 DataFrame
            
        Returns:
            產品特徵 DataFrame
        """
        logger.info("建立產品特徵...")
        
        if 'stock_id' not in df.columns:
            logger.warning("找不到 stock_id 欄位")
            return pd.DataFrame()
        
        product_features = []
        
        for stock_id, group in df.groupby('stock_id'):
            # 產品名稱
            stock_description = group['stock_description'].iloc[0] if 'stock_description' in group.columns else ''
            
            # 平均價格
            if 'price' in group.columns:
                avg_price = group['price'].mean()
            elif 'actualTotal' in group.columns and 'quantity' in group.columns:
                avg_price = (group['actualTotal'] / group['quantity'].replace(0, 1)).mean()
            else:
                avg_price = 0.0
            
            # 總銷售數量
            total_sales = group['quantity'].sum() if 'quantity' in group.columns else len(group)
            
            # 不重複購買人數
            unique_buyers = group['member_id'].nunique() if 'member_id' in group.columns else 0
            
            # 平均每單購買數量
            avg_quantity_per_order = group['quantity'].mean() if 'quantity' in group.columns else 1.0
            
            product_features.append({
                'stock_id': stock_id,
                'stock_description': stock_description,
                'avg_price': avg_price,
                'total_sales': total_sales,
                'unique_buyers': unique_buyers,
                'avg_quantity_per_order': avg_quantity_per_order
            })
        
        product_df = pd.DataFrame(product_features)
        
        # 計算熱門度分數（標準化）
        if len(product_df) > 0:
            max_sales = product_df['total_sales'].max()
            if max_sales > 0:
                product_df['popularity_score'] = product_df['total_sales'] / max_sales
            else:
                product_df['popularity_score'] = 0.0
        
        logger.info(f"產品特徵建立完成，共 {len(product_df)} 個產品")
        
        return product_df
    
    def get_feature_summary(self, feature_matrix: pd.DataFrame) -> Dict[str, Any]:
        """
        獲取特徵摘要
        
        Args:
            feature_matrix: 特徵矩陣
            
        Returns:
            特徵摘要字典
        """
        summary = {
            'total_members': len(feature_matrix),
            'total_features': len(feature_matrix.columns),
            'feature_names': feature_matrix.columns.tolist(),
            'numeric_features': feature_matrix.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical_features': feature_matrix.select_dtypes(include=['object']).columns.tolist(),
            'missing_values': feature_matrix.isnull().sum().to_dict(),
        }
        
        # 數值特徵統計
        numeric_stats = {}
        for col in summary['numeric_features']:
            numeric_stats[col] = {
                'mean': float(feature_matrix[col].mean()),
                'std': float(feature_matrix[col].std()),
                'min': float(feature_matrix[col].min()),
                'max': float(feature_matrix[col].max()),
            }
        summary['numeric_stats'] = numeric_stats
        
        return summary


def main():
    """測試特徵工程器"""
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
    print("測試特徵工程器")
    print("=" * 60)
    
    # 載入和清理資料
    print("\n載入資料...")
    loader = DataLoader()
    df = loader.merge_data(max_rows=500)
    
    if df.empty:
        print("✗ 資料載入失敗")
        return
    
    print(f"原始資料: {len(df)} 筆記錄")
    
    print("\n清理資料...")
    cleaner = DataCleaner()
    df = cleaner.clean_all(df)
    print(f"清理後資料: {len(df)} 筆記錄")
    
    # 建立特徵工程器
    print("\n建立特徵...")
    engineer = FeatureEngineer()
    
    # 建立特徵矩陣
    feature_matrix = engineer.create_feature_matrix(df)
    
    print(f"\n特徵矩陣:")
    print(f"  會員數: {len(feature_matrix)}")
    print(f"  特徵數: {len(feature_matrix.columns)}")
    print(f"  特徵: {list(feature_matrix.columns)}")
    
    # 顯示範例
    print(f"\n範例特徵（前 3 個會員）:")
    print(feature_matrix.head(3))
    
    # 建立產品特徵
    print("\n建立產品特徵...")
    product_features = engineer.create_product_features(df)
    print(f"產品數: {len(product_features)}")
    
    print("\n" + "=" * 60)
    print("✓ 特徵工程器測試完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
