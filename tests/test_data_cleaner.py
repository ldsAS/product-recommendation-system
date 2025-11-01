"""
測試資料清理器
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.data_processing.data_cleaner import DataCleaner


@pytest.fixture
def sample_data():
    """建立範例資料"""
    return pd.DataFrame({
        'id': ['1', '2', '3', '4', '5', '5'],  # 包含重複
        'member_code': ['CU001', 'CU002', 'CU003', None, 'CU005', 'CU005'],
        'total_consumption': [1000, 2000, None, 3000, 4000, 4000],
        'actualTotal': [100, 200, 0, 300, 400, 400],
        'stock_id': ['P1', 'P2', None, 'P4', 'P5', 'P5'],
        'date': ['2024-01-01', '2024-01-02', 'invalid', '2024-01-04', '2024-01-05', '2024-01-05'],
        'member_name': ['  張三  ', 'nan', '李四', 'None', '王五', '王五'],
    })


class TestDataCleaner:
    """測試資料清理器"""
    
    def test_init(self):
        """測試初始化"""
        cleaner = DataCleaner()
        assert cleaner.cleaning_report is not None
    
    def test_remove_invalid_orders(self, sample_data):
        """測試移除無效訂單"""
        cleaner = DataCleaner()
        cleaned = cleaner.remove_invalid_orders(sample_data)
        
        # 應該移除 actualTotal=0 且 stock_id 為空的記錄
        assert len(cleaned) < len(sample_data)
    
    def test_handle_missing_values(self, sample_data):
        """測試處理缺失值"""
        cleaner = DataCleaner()
        cleaned = cleaner.handle_missing_values(sample_data)
        
        # total_consumption 的缺失值應該被填補為 0
        assert cleaned['total_consumption'].isna().sum() == 0
    
    def test_remove_duplicates(self, sample_data):
        """測試移除重複記錄"""
        cleaner = DataCleaner()
        cleaned = cleaner.remove_duplicates(sample_data, subset=['id'])
        
        # 應該移除重複的 id='5'
        assert len(cleaned) == 5
        assert cleaned['id'].nunique() == 5
    
    def test_standardize_dates(self, sample_data):
        """測試標準化日期"""
        cleaner = DataCleaner()
        cleaned = cleaner.standardize_dates(sample_data, date_columns=['date'])
        
        # date 欄位應該被轉換為 datetime 類型
        assert pd.api.types.is_datetime64_any_dtype(cleaned['date'])
    
    def test_clean_text_fields(self, sample_data):
        """測試清理文字欄位"""
        cleaner = DataCleaner()
        cleaned = cleaner.clean_text_fields(sample_data, text_columns=['member_name'])
        
        # 應該移除前後空白
        assert cleaned.loc[0, 'member_name'] == '張三'
        # 'nan' 應該被替換為空字串
        assert cleaned.loc[1, 'member_name'] == ''
    
    def test_clean_all(self, sample_data):
        """測試完整清理流程"""
        cleaner = DataCleaner()
        cleaned = cleaner.clean_all(sample_data)
        
        # 應該有清理報告
        report = cleaner.get_cleaning_report()
        assert 'removed_rows' in report
        assert 'filled_values' in report
        
        # 資料應該被清理
        assert len(cleaned) <= len(sample_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
