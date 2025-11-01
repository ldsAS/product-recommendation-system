"""
驗證器單元測試
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.validators import (
    validate_phone_number,
    validate_member_code,
    validate_recommendation_request
)
from src.models.data_models import RecommendationRequest


class TestValidators:
    """驗證器測試類別"""
    
    def test_validate_phone_number_valid(self):
        """測試有效電話號碼"""
        # 台灣手機號碼
        result = validate_phone_number("0912345678")
        assert result.is_valid
        
        # 市話
        result = validate_phone_number("02-12345678")
        assert result.is_valid
    
    def test_validate_phone_number_invalid(self):
        """測試無效電話號碼"""
        # 包含字母
        result = validate_phone_number("09123abc78")
        assert not result.is_valid
        
        # 太短
        result = validate_phone_number("091234")
        assert not result.is_valid
    
    def test_validate_member_code_valid(self):
        """測試有效會員編號"""
        result = validate_member_code("CU000001")
        assert result.is_valid
        
        result = validate_member_code("TEST123")
        assert result.is_valid
    
    def test_validate_member_code_invalid(self):
        """測試無效會員編號"""
        # 空字串
        result = validate_member_code("")
        assert not result.is_valid
        
        # None
        result = validate_member_code(None)
        assert not result.is_valid
    
    def test_validate_recommendation_request_valid(self):
        """測試有效推薦請求"""
        request = RecommendationRequest(
            member_code="CU000001",
            total_consumption=10000.0,
            accumulated_bonus=300.0,
            top_k=5
        )
        
        result = validate_recommendation_request(request)
        assert result.is_valid
    
    def test_validate_recommendation_request_invalid_top_k(self):
        """測試無效的 top_k"""
        request = RecommendationRequest(
            member_code="CU000001",
            total_consumption=10000.0,
            accumulated_bonus=300.0,
            top_k=25  # 超過 20
        )
        
        result = validate_recommendation_request(request)
        assert not result.is_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
