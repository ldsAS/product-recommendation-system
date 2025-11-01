"""
推薦引擎單元測試
"""
import pytest
import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.data_models import MemberInfo, Recommendation
from src.models.recommendation_engine import RecommendationEngine


class TestRecommendationEngine:
    """推薦引擎測試類別"""
    
    @pytest.fixture
    def sample_member_info(self):
        """範例會員資訊"""
        return MemberInfo(
            member_code="TEST001",
            phone="0912345678",
            total_consumption=10000.0,
            accumulated_bonus=300.0,
            recent_purchases=["P001", "P002"]
        )
    
    def test_member_info_creation(self, sample_member_info):
        """測試會員資訊建立"""
        assert sample_member_info.member_code == "TEST001"
        assert sample_member_info.total_consumption == 10000.0
        assert len(sample_member_info.recent_purchases) == 2
    
    def test_member_info_validation(self):
        """測試會員資訊驗證"""
        # 測試必填欄位
        with pytest.raises(Exception):
            MemberInfo(
                member_code="",  # 空字串應該失敗
                total_consumption=10000.0,
                accumulated_bonus=300.0
            )
        
        # 測試負數驗證
        with pytest.raises(Exception):
            MemberInfo(
                member_code="TEST001",
                total_consumption=-100.0,  # 負數應該失敗
                accumulated_bonus=300.0
            )
    
    def test_recommendation_creation(self):
        """測試推薦物件建立"""
        rec = Recommendation(
            product_id="P001",
            product_name="測試產品",
            confidence_score=85.5,
            explanation="測試理由",
            rank=1
        )
        
        assert rec.product_id == "P001"
        assert rec.confidence_score == 85.5
        assert rec.rank == 1
    
    def test_recommendation_score_range(self):
        """測試推薦分數範圍"""
        # 測試分數上限
        with pytest.raises(Exception):
            Recommendation(
                product_id="P001",
                product_name="測試產品",
                confidence_score=150.0,  # 超過 100
                explanation="測試理由",
                rank=1
            )
        
        # 測試分數下限
        with pytest.raises(Exception):
            Recommendation(
                product_id="P001",
                product_name="測試產品",
                confidence_score=-10.0,  # 負數
                explanation="測試理由",
                rank=1
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
