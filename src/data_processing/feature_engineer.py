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
        增強版：包含 RFM 分數和分段（需求 3.1）
        
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
            
            # Monetary: 平均訂單金額和總消費金額（需求 3.1）
            if 'actualTotal' in group.columns:
                monetary_avg = group['actualTotal'].mean()
                monetary_total = group['actualTotal'].sum()
            else:
                monetary_avg = 0.0
                monetary_total = 0.0
            
            rfm_features.append({
                'member_id': member_id,
                'recency': max(0, recency),  # 確保非負
                'frequency': frequency,
                'monetary': monetary_avg,
                'monetary_total': monetary_total  # 需求 3.1: 總消費金額
            })
        
        rfm_df = pd.DataFrame(rfm_features)
        
        # 需求 3.1: 計算 RFM 分數（1-5 分）
        # Recency: 越小越好（最近購買）
        rfm_df['recency_score'] = pd.qcut(rfm_df['recency'], q=5, labels=[5, 4, 3, 2, 1], duplicates='drop')
        # Frequency: 越大越好（購買頻率高）
        rfm_df['frequency_score'] = pd.qcut(rfm_df['frequency'], q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
        # Monetary: 越大越好（消費金額高）
        rfm_df['monetary_score'] = pd.qcut(rfm_df['monetary'], q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
        
        # 轉換為數值類型
        rfm_df['recency_score'] = pd.to_numeric(rfm_df['recency_score'], errors='coerce').fillna(3)
        rfm_df['frequency_score'] = pd.to_numeric(rfm_df['frequency_score'], errors='coerce').fillna(3)
        rfm_df['monetary_score'] = pd.to_numeric(rfm_df['monetary_score'], errors='coerce').fillna(3)
        
        # 需求 3.1: 計算綜合 RFM 分數
        rfm_df['rfm_score'] = (
            rfm_df['recency_score'] * 0.3 +
            rfm_df['frequency_score'] * 0.3 +
            rfm_df['monetary_score'] * 0.4
        )
        
        logger.info(f"RFM 特徵計算完成，共 {len(rfm_df)} 個會員")
        logger.info(f"  平均 Recency: {rfm_df['recency'].mean():.1f} 天")
        logger.info(f"  平均 Frequency: {rfm_df['frequency'].mean():.1f} 次")
        logger.info(f"  平均 Monetary: ${rfm_df['monetary'].mean():.2f}")
        logger.info(f"  平均 RFM Score: {rfm_df['rfm_score'].mean():.2f}")
        
        return rfm_df
    
    def extract_product_preferences(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        提取產品偏好特徵
        增強版：包含產品多樣性指標（需求 3.4）
        
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
            
            # 需求 3.4: 產品多樣性指標
            if 'stock_id' in group.columns:
                unique_products = group['stock_id'].nunique()
                total_purchases = len(group)
                product_diversity = unique_products  # 購買不同產品的數量
                product_diversity_ratio = unique_products / total_purchases if total_purchases > 0 else 0
                # 計算產品重複購買率
                repeat_purchase_ratio = 1 - product_diversity_ratio
            else:
                product_diversity = 0
                product_diversity_ratio = 0
                repeat_purchase_ratio = 0
            
            # 平均每單商品數
            if 'quantity' in group.columns:
                avg_items_per_order = group['quantity'].mean()
                total_items = group['quantity'].sum()
            else:
                avg_items_per_order = 0.0
                total_items = 0
            
            # 需求 3.4: 類別多樣性（如果有類別資訊）
            if 'category' in group.columns or 'stock_description' in group.columns:
                category_col = 'category' if 'category' in group.columns else 'stock_description'
                unique_categories = group[category_col].nunique()
                category_diversity_ratio = unique_categories / total_purchases if total_purchases > 0 else 0
            else:
                unique_categories = 0
                category_diversity_ratio = 0
            
            product_features.append({
                'member_id': member_id,
                'favorite_products': favorite_products,
                'product_diversity': product_diversity,  # 需求 3.4
                'product_diversity_ratio': product_diversity_ratio,  # 需求 3.4
                'repeat_purchase_ratio': repeat_purchase_ratio,  # 需求 3.4
                'unique_categories': unique_categories,  # 需求 3.4
                'category_diversity_ratio': category_diversity_ratio,  # 需求 3.4
                'avg_items_per_order': avg_items_per_order,
                'total_items_purchased': total_items
            })
        
        product_df = pd.DataFrame(product_features)
        logger.info(f"產品偏好特徵提取完成，共 {len(product_df)} 個會員")
        logger.info(f"  平均產品多樣性: {product_df['product_diversity'].mean():.1f} 個不同產品")
        logger.info(f"  平均多樣性比例: {product_df['product_diversity_ratio'].mean():.2%}")
        
        return product_df
    
    def extract_time_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        提取時間模式特徵
        增強版：包含購買時段、日期偏好、購買間隔等（需求 3.2）
        
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
            # 需求 3.2: 偏好購買時段（小時）
            if 'date' in group.columns:
                hours = group['date'].dt.hour
                if len(hours) > 0 and hours.notna().any():
                    purchase_hour_preference = hours.mode().iloc[0] if len(hours.mode()) > 0 else 12
                    # 計算時段分布
                    morning_purchases = ((hours >= 6) & (hours < 12)).sum()  # 早上
                    afternoon_purchases = ((hours >= 12) & (hours < 18)).sum()  # 下午
                    evening_purchases = ((hours >= 18) & (hours < 24)).sum()  # 晚上
                    night_purchases = ((hours >= 0) & (hours < 6)).sum()  # 深夜
                else:
                    purchase_hour_preference = 12
                    morning_purchases = afternoon_purchases = evening_purchases = night_purchases = 0
            else:
                purchase_hour_preference = 12
                morning_purchases = afternoon_purchases = evening_purchases = night_purchases = 0
            
            # 需求 3.2: 偏好購買星期
            if 'date' in group.columns:
                days = group['date'].dt.dayofweek
                if len(days) > 0 and days.notna().any():
                    purchase_day_preference = days.mode().iloc[0] if len(days.mode()) > 0 else 3
                    # 計算工作日 vs 週末
                    weekday_purchases = (days < 5).sum()
                    weekend_purchases = (days >= 5).sum()
                else:
                    purchase_day_preference = 3
                    weekday_purchases = weekend_purchases = 0
            else:
                purchase_day_preference = 3
                weekday_purchases = weekend_purchases = 0
            
            # 需求 3.2: 購買間隔統計
            if 'date' in group.columns and len(group) > 1:
                sorted_dates = group['date'].sort_values()
                purchase_intervals = sorted_dates.diff().dt.days.dropna()
                avg_purchase_interval = purchase_intervals.mean() if len(purchase_intervals) > 0 else 0
                std_purchase_interval = purchase_intervals.std() if len(purchase_intervals) > 0 else 0
            else:
                avg_purchase_interval = 0
                std_purchase_interval = 0
            
            # 距離上次購買天數
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
                'days_since_last_purchase': max(0, days_since_last_purchase),
                # 需求 3.2: 新增時段特徵
                'morning_purchase_ratio': morning_purchases / len(group) if len(group) > 0 else 0,
                'afternoon_purchase_ratio': afternoon_purchases / len(group) if len(group) > 0 else 0,
                'evening_purchase_ratio': evening_purchases / len(group) if len(group) > 0 else 0,
                'weekday_purchase_ratio': weekday_purchases / len(group) if len(group) > 0 else 0,
                'weekend_purchase_ratio': weekend_purchases / len(group) if len(group) > 0 else 0,
                # 需求 3.2: 購買間隔特徵
                'avg_purchase_interval_days': avg_purchase_interval,
                'std_purchase_interval_days': std_purchase_interval
            })
        
        time_df = pd.DataFrame(time_features)
        logger.info(f"時間模式特徵提取完成，共 {len(time_df)} 個會員")
        logger.info(f"  平均購買間隔: {time_df['avg_purchase_interval_days'].mean():.1f} 天")
        
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
    
    def create_price_matching_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        創建會員消費水平與產品價格匹配特徵（需求 3.5）
        
        Args:
            df: 包含會員和產品資訊的 DataFrame
            
        Returns:
            包含價格匹配特徵的 DataFrame
        """
        logger.info("創建價格匹配特徵...")
        
        price_features = []
        
        for member_id, group in df.groupby('member_id'):
            # 計算會員的消費水平
            if 'actualTotal' in group.columns:
                avg_spending = group['actualTotal'].mean()
                min_spending = group['actualTotal'].min()
                max_spending = group['actualTotal'].max()
                std_spending = group['actualTotal'].std()
            elif 'price' in group.columns:
                avg_spending = group['price'].mean()
                min_spending = group['price'].min()
                max_spending = group['price'].max()
                std_spending = group['price'].std()
            else:
                avg_spending = min_spending = max_spending = std_spending = 0.0
            
            # 需求 3.5: 定義價格區間偏好
            # 低價: < 平均消費 * 0.7
            # 中價: 平均消費 * 0.7 ~ 平均消費 * 1.3
            # 高價: > 平均消費 * 1.3
            if avg_spending > 0:
                low_price_threshold = avg_spending * 0.7
                high_price_threshold = avg_spending * 1.3
                
                if 'actualTotal' in group.columns:
                    prices = group['actualTotal']
                elif 'price' in group.columns:
                    prices = group['price']
                else:
                    prices = pd.Series([])
                
                if len(prices) > 0:
                    low_price_purchases = (prices < low_price_threshold).sum()
                    mid_price_purchases = ((prices >= low_price_threshold) & (prices <= high_price_threshold)).sum()
                    high_price_purchases = (prices > high_price_threshold).sum()
                    
                    total = len(prices)
                    low_price_ratio = low_price_purchases / total
                    mid_price_ratio = mid_price_purchases / total
                    high_price_ratio = high_price_purchases / total
                else:
                    low_price_ratio = mid_price_ratio = high_price_ratio = 0
            else:
                low_price_threshold = high_price_threshold = 0
                low_price_ratio = mid_price_ratio = high_price_ratio = 0
            
            # 需求 3.5: 消費穩定性（標準差/平均值）
            spending_stability = 1 - (std_spending / avg_spending) if avg_spending > 0 else 0
            spending_stability = max(0, min(1, spending_stability))  # 限制在 0-1 之間
            
            price_features.append({
                'member_id': member_id,
                'avg_spending': avg_spending,
                'min_spending': min_spending,
                'max_spending': max_spending,
                'std_spending': std_spending,
                'spending_stability': spending_stability,  # 需求 3.5
                'low_price_threshold': low_price_threshold,  # 需求 3.5
                'high_price_threshold': high_price_threshold,  # 需求 3.5
                'low_price_ratio': low_price_ratio,  # 需求 3.5
                'mid_price_ratio': mid_price_ratio,  # 需求 3.5
                'high_price_ratio': high_price_ratio  # 需求 3.5
            })
        
        price_df = pd.DataFrame(price_features)
        logger.info(f"價格匹配特徵創建完成，共 {len(price_df)} 個會員")
        logger.info(f"  平均消費水平: ${price_df['avg_spending'].mean():.2f}")
        logger.info(f"  平均消費穩定性: {price_df['spending_stability'].mean():.2%}")
        
        return price_df
    
    def create_feature_matrix(
        self,
        df: pd.DataFrame,
        include_rfm: bool = True,
        include_product: bool = True,
        include_time: bool = True,
        include_location: bool = True,
        include_basic: bool = True,
        include_price_matching: bool = True
    ) -> pd.DataFrame:
        """
        建立完整的特徵矩陣
        增強版：包含所有優化後的特徵（需求 3.1-3.5）
        
        Args:
            df: 輸入 DataFrame
            include_rfm: 是否包含 RFM 特徵（需求 3.1）
            include_product: 是否包含產品偏好特徵（需求 3.4）
            include_time: 是否包含時間模式特徵（需求 3.2）
            include_location: 是否包含地點特徵
            include_basic: 是否包含會員基礎特徵
            include_price_matching: 是否包含價格匹配特徵（需求 3.5）
            
        Returns:
            完整的特徵矩陣 DataFrame
        """
        logger.info("=" * 60)
        logger.info("建立完整特徵矩陣（增強版）")
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
            rfm_df = self.calculate_rfm(df)  # 需求 3.1
            if not rfm_df.empty:
                feature_dfs.append(rfm_df)
        
        if include_product:
            product_df = self.extract_product_preferences(df)  # 需求 3.4
            if not product_df.empty:
                feature_dfs.append(product_df)
        
        if include_time:
            time_df = self.extract_time_patterns(df)  # 需求 3.2
            if not time_df.empty:
                feature_dfs.append(time_df)
        
        if include_location:
            location_df = self.extract_location_features(df)
            if not location_df.empty:
                feature_dfs.append(location_df)
        
        if include_price_matching:
            price_df = self.create_price_matching_features(df)  # 需求 3.5
            if not price_df.empty:
                feature_dfs.append(price_df)
        
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
        logger.info(f"特徵矩陣建立完成（增強版）")
        logger.info(f"  會員數: {len(feature_matrix)}")
        logger.info(f"  特徵數: {len(feature_matrix.columns)}")
        logger.info(f"  ✓ RFM 特徵: 已包含（需求 3.1）")
        logger.info(f"  ✓ 時間特徵: 已包含（需求 3.2）")
        logger.info(f"  ✓ 產品多樣性: 已包含（需求 3.4）")
        logger.info(f"  ✓ 價格匹配: 已包含（需求 3.5）")
        logger.info("=" * 60)
        
        return feature_matrix
    
    def create_product_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        建立產品特徵
        增強版：包含產品熱門度分數（需求 3.3）
        
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
                min_price = group['price'].min()
                max_price = group['price'].max()
            elif 'actualTotal' in group.columns and 'quantity' in group.columns:
                prices = group['actualTotal'] / group['quantity'].replace(0, 1)
                avg_price = prices.mean()
                min_price = prices.min()
                max_price = prices.max()
            else:
                avg_price = min_price = max_price = 0.0
            
            # 總銷售數量
            total_sales = group['quantity'].sum() if 'quantity' in group.columns else len(group)
            
            # 不重複購買人數
            unique_buyers = group['member_id'].nunique() if 'member_id' in group.columns else 0
            
            # 平均每單購買數量
            avg_quantity_per_order = group['quantity'].mean() if 'quantity' in group.columns else 1.0
            
            # 需求 3.3: 計算產品熱門度相關指標
            purchase_frequency = len(group)  # 購買次數
            repurchase_rate = unique_buyers / purchase_frequency if purchase_frequency > 0 else 0
            
            product_features.append({
                'stock_id': stock_id,
                'stock_description': stock_description,
                'avg_price': avg_price,
                'min_price': min_price,
                'max_price': max_price,
                'total_sales': total_sales,
                'unique_buyers': unique_buyers,
                'purchase_frequency': purchase_frequency,  # 需求 3.3
                'repurchase_rate': repurchase_rate,
                'avg_quantity_per_order': avg_quantity_per_order
            })
        
        product_df = pd.DataFrame(product_features)
        
        # 需求 3.3: 計算產品熱門度分數（基於購買次數和購買人數）
        if len(product_df) > 0:
            # 標準化銷售數量
            max_sales = product_df['total_sales'].max()
            if max_sales > 0:
                sales_score = product_df['total_sales'] / max_sales
            else:
                sales_score = 0.0
            
            # 標準化購買人數
            max_buyers = product_df['unique_buyers'].max()
            if max_buyers > 0:
                buyers_score = product_df['unique_buyers'] / max_buyers
            else:
                buyers_score = 0.0
            
            # 標準化購買頻率
            max_frequency = product_df['purchase_frequency'].max()
            if max_frequency > 0:
                frequency_score = product_df['purchase_frequency'] / max_frequency
            else:
                frequency_score = 0.0
            
            # 需求 3.3: 綜合熱門度分數（銷售量 40% + 購買人數 40% + 購買頻率 20%）
            product_df['popularity_score'] = (
                sales_score * 0.4 +
                buyers_score * 0.4 +
                frequency_score * 0.2
            )
        
        logger.info(f"產品特徵建立完成，共 {len(product_df)} 個產品")
        logger.info(f"  平均熱門度分數: {product_df['popularity_score'].mean():.3f}")
        logger.info(f"  平均購買人數: {product_df['unique_buyers'].mean():.1f}")
        logger.info(f"  平均購買頻率: {product_df['purchase_frequency'].mean():.1f}")
        
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
