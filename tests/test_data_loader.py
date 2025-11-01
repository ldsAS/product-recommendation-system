"""
測試資料載入器
"""
import pytest
import pandas as pd
from pathlib import Path
import json
import tempfile

from src.data_processing.data_loader import DataLoader


@pytest.fixture
def temp_data_dir(tmp_path):
    """建立臨時資料目錄"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_member_data(temp_data_dir):
    """建立範例會員資料"""
    data = [
        {"id": "m1", "member_code": "CU000001", "member_name": "測試會員1", "total_consumption": 10000},
        {"id": "m2", "member_code": "CU000002", "member_name": "測試會員2", "total_consumption": 20000},
    ]
    
    file_path = temp_data_dir / "member"
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    return file_path


@pytest.fixture
def sample_sales_data(temp_data_dir):
    """建立範例銷售資料"""
    data = [
        {"id": "s1", "member": "m1", "date": "2024-01-01T10:00:00", "total": 1000},
        {"id": "s2", "member": "m2", "date": "2024-01-02T11:00:00", "total": 2000},
    ]
    
    file_path = temp_data_dir / "sales"
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    return file_path


@pytest.fixture
def sample_sales_details_data(temp_data_dir):
    """建立範例銷售明細資料"""
    data = [
        {"id": "sd1", "sales_id": "s1", "stock_id": "30463", "stock_description": "產品A", "quantity": 1},
        {"id": "sd2", "sales_id": "s2", "stock_id": "31033", "stock_description": "產品B", "quantity": 2},
    ]
    
    file_path = temp_data_dir / "salesdetails"
    with open(file_path, 'w', encoding='utf-8') as f:
        for record in data:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    return file_path


class TestDataLoader:
    """測試資料載入器"""
    
    def test_init(self, temp_data_dir):
        """測試初始化"""
        loader = DataLoader(data_dir=temp_data_dir)
        assert loader.data_dir == temp_data_dir
    
    def test_load_json_lines(self, sample_member_data):
        """測試載入 JSON Lines"""
        loader = DataLoader(data_dir=sample_member_data.parent)
        df = loader.load_json_lines(sample_member_data)
        
        assert len(df) == 2
        assert 'id' in df.columns
        assert 'member_code' in df.columns
    
    def test_load_members(self, temp_data_dir, sample_member_data):
        """測試載入會員資料"""
        loader = DataLoader(data_dir=temp_data_dir)
        df = loader.load_members()
        
        assert len(df) == 2
        assert df['member_code'].tolist() == ['CU000001', 'CU000002']
    
    def test_load_sales(self, temp_data_dir, sample_sales_data):
        """測試載入銷售資料"""
        loader = DataLoader(data_dir=temp_data_dir)
        df = loader.load_sales()
        
        assert len(df) == 2
        assert 'date' in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df['date'])
    
    def test_load_sales_details(self, temp_data_dir, sample_sales_details_data):
        """測試載入銷售明細資料"""
        loader = DataLoader(data_dir=temp_data_dir)
        df = loader.load_sales_details()
        
        assert len(df) == 2
        assert 'stock_id' in df.columns
    
    def test_merge_data(
        self, 
        temp_data_dir, 
        sample_member_data, 
        sample_sales_data, 
        sample_sales_details_data
    ):
        """測試資料合併"""
        loader = DataLoader(data_dir=temp_data_dir)
        
        members_df = loader.load_members()
        sales_df = loader.load_sales()
        sales_details_df = loader.load_sales_details()
        
        merged_df = loader.merge_data(
            members_df=members_df,
            sales_df=sales_df,
            sales_details_df=sales_details_df
        )
        
        assert len(merged_df) == 2
        assert 'member_code' in merged_df.columns
        assert 'stock_id' in merged_df.columns
    
    def test_get_data_summary(self, temp_data_dir, sample_member_data):
        """測試資料摘要"""
        loader = DataLoader(data_dir=temp_data_dir)
        df = loader.load_members()
        
        summary = loader.get_data_summary(df)
        
        assert summary['rows'] == 2
        assert summary['columns'] == 4
        assert 'memory_usage_mb' in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
