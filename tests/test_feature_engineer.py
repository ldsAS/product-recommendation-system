"""
測試特徵工程器
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta

from src.data_processing.feature_engineer import FeatureEngineer


@pytest.fixture
def sample_transaction_data():
    """建立範例交易資料"""
    base_date = datetime(2024, 1, 1)
    
    return pd.DataFrame({
        'member_id': ['m1', 'm1', 'm1', 'm2', 'm2'],
        'member_code': ['CU001', 'CU001', 'CU001', 'CU002', 'CU002'],
        'date': [
            base_date,
            base_date + timedelta(days=10),
            base_date + timedelta(days=20),
            base_date + timedelta(days=5),
            base_date + timedelta(days=15),
        ],
        'stock_id': ['P1', 'P2', 'P1', 'P3', 'P1'],
        'stock_description': ['產品A', '產品B', '產品A', '產品C', '產品A'],
        'quantity': [1, 2, 1, 3, 2],
        'actualTotal': [100, 200, 100, 300, 200],
        'loccode': ['loc1', 'loc1', 'loc2', 'loc1', 'loc1'],
        'total_consumption': [400, 400, 400, 500, 500],
        'accumulated_bonus': [50, 50, 50, 60, 60],
    })


class TestFeatureEngineer:
    """測試特徵工程器"""
    
    def test_init(self):
        """測試初始化"""
        engineer = FeatureEngineer()
        assert engineer.reference_date is not None
    
    def test_calculate_rfm(self, sample_transaction_data):
        """測試 RFM 計算"""
        engineer = FeatureEngineer(reference_date=datetime(2024, 2, 1))
        rfm_df = engineer.calculate_rfm(sample_transaction_data)
        
        assert len(rfm_df) == 2  # 2 個會員
        assert 'recency' in rfm_df.columns
        assert 'frequency' in rfm_df.columns
        assert 'monetary' in rfm_df.columns
    
    def test_extract_product_preferences(self, sample_transaction_data):
        """測試產品偏好提取"""
        engineer = FeatureEngineer()
        product_df = engineer.extract_product_preferences(sample_transaction_data)
        
        assert len(product_df) == 2
        assert 'favorite_products' in product_df.columns
        assert 'product_diversity' in product_df.columns
    
    def test_extract_time_patterns(self, sample_transaction_data):
        """測試時間模式提取"""
        engineer = FeatureEngineer()
        time_df = engineer.extract_time_patterns(sample_transaction_data)
        
        assert len(time_df) == 2
        assert 'days_since_last_purchase' in time_df.columns
    
    def test_create_feature_matrix(self, sample_transaction_data):
        """測試特徵矩陣建立"""
        engineer = FeatureEngineer()
        feature_matrix = engineer.create_feature_matrix(sample_transaction_data)
        
        assert len(feature_matrix) == 2
        assert 'member_id' in feature_matrix.columns
        assert 'recency' in feature_matrix.columns
        assert 'frequency' in feature_matrix.columns
    
    def test_create_product_features(self, sample_transaction_data):
        """測試產品特徵建立"""
        engineer = FeatureEngineer()
        product_df = engineer.create_product_features(sample_transaction_data)
        
        assert len(product_df) == 3  # 3 個產品
        assert 'stock_id' in product_df.columns
        assert 'avg_price' in product_df.columns
        assert 'popularity_score' in product_df.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
