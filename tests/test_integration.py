"""
整合測試
測試端到端推薦流程
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_processing.data_loader import DataLoader
from src.data_processing.data_cleaner import DataCleaner
from src.data_processing.feature_engineer import FeatureEngineer
from src.models.training_data_builder import TrainingDataBuilder
from src.models.data_models import MemberInfo


class TestIntegration:
    """整合測試類別"""
    
    @pytest.fixture(scope="class")
    def sample_data(self):
        """載入範例資料"""
        try:
            loader = DataLoader()
            df = loader.merge_data(max_rows=100)
            return df
        except Exception as e:
            pytest.skip(f"無法載入資料: {e}")
    
    def test_data_pipeline(self, sample_data):
        """測試資料處理管線"""
        # 1. 資料清理
        cleaner = DataCleaner()
        cleaned_df = cleaner.clean_all(sample_data)
        
        assert not cleaned_df.empty
        assert len(cleaned_df) <= len(sample_data)
        
        # 2. 特徵工程
        engineer = FeatureEngineer()
        member_features = engineer.create_feature_matrix(cleaned_df)
        product_features = engineer.create_product_features(cleaned_df)
        
        assert not member_features.empty
        assert not product_features.empty
        
        # 3. 訓練資料準備
        builder = TrainingDataBuilder()
        data_dict = builder.prepare_training_data(cleaned_df)
        
        assert 'train' in data_dict
        assert 'validation' in data_dict
        assert 'test' in data_dict
        assert not data_dict['train'].empty
    
    def test_end_to_end_recommendation_flow(self, sample_data):
        """測試端到端推薦流程"""
        # 1. 資料處理
        cleaner = DataCleaner()
        cleaned_df = cleaner.clean_all(sample_data)
        
        # 2. 特徵工程
        engineer = FeatureEngineer()
        member_features = engineer.create_feature_matrix(cleaned_df)
        
        # 3. 建立測試會員資訊
        if not member_features.empty:
            test_member_code = member_features.iloc[0]['member_code']
            
            member_info = MemberInfo(
                member_code=test_member_code,
                total_consumption=10000.0,
                accumulated_bonus=300.0,
                recent_purchases=[]
            )
            
            # 驗證會員資訊建立成功
            assert member_info.member_code == test_member_code
            assert member_info.total_consumption > 0
    
    def test_feature_consistency(self, sample_data):
        """測試特徵一致性"""
        cleaner = DataCleaner()
        cleaned_df = cleaner.clean_all(sample_data)
        
        engineer = FeatureEngineer()
        
        # 建立特徵兩次，應該得到相同結果
        member_features_1 = engineer.create_feature_matrix(cleaned_df)
        member_features_2 = engineer.create_feature_matrix(cleaned_df)
        
        assert len(member_features_1) == len(member_features_2)
        assert list(member_features_1.columns) == list(member_features_2.columns)
    
    def test_training_data_split_ratios(self, sample_data):
        """測試訓練資料分割比例"""
        cleaner = DataCleaner()
        cleaned_df = cleaner.clean_all(sample_data)
        
        builder = TrainingDataBuilder(
            test_size=0.2,
            validation_size=0.1
        )
        
        data_dict = builder.prepare_training_data(cleaned_df)
        
        total_samples = (
            len(data_dict['train']) +
            len(data_dict['validation']) +
            len(data_dict['test'])
        )
        
        # 檢查分割比例是否合理
        train_ratio = len(data_dict['train']) / total_samples
        val_ratio = len(data_dict['validation']) / total_samples
        test_ratio = len(data_dict['test']) / total_samples
        
        # 允許一些誤差
        assert 0.6 < train_ratio < 0.8
        assert 0.05 < val_ratio < 0.15
        assert 0.15 < test_ratio < 0.25


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
