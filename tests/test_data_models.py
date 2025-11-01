"""
測試資料模型
"""
import pytest
from datetime import datetime
from src.models.data_models import (
    MemberFeatures,
    MemberInfo,
    Product,
    Recommendation,
    RecommendationRequest,
    RecommendationResponse,
    ModelMetrics,
    ModelMetadata,
    ModelType,
    RecommendationSource,
    example_recommendation_request,
    example_recommendation_response,
)


class TestMemberModels:
    """測試會員相關模型"""
    
    def test_member_features_creation(self):
        """測試會員特徵建立"""
        features = MemberFeatures(
            member_code="CU000001",
            total_consumption=17400.0,
            accumulated_bonus=500.0,
            recency=5,
            frequency=10,
            monetary=1740.0
        )
        
        assert features.member_code == "CU000001"
        assert features.total_consumption == 17400.0
        assert features.recency == 5
        assert features.frequency == 10
        assert features.monetary == 1740.0
    
    def test_member_info_validation(self):
        """測試會員資訊驗證"""
        # 正常情況
        info = MemberInfo(
            member_code="CU000001",
            phone="0937024682",
            total_consumption=17400.0
        )
        assert info.member_code == "CU000001"
        
        # 測試電話號碼驗證
        with pytest.raises(ValueError):
            MemberInfo(
                member_code="CU000001",
                phone="invalid_phone",
                total_consumption=17400.0
            )


class TestProductModels:
    """測試產品相關模型"""
    
    def test_product_creation(self):
        """測試產品建立"""
        product = Product(
            stock_id="30463",
            stock_description="蓉憶記小瓶 10顆裝",
            avg_price=315.0,
            popularity_score=0.85
        )
        
        assert product.stock_id == "30463"
        assert product.stock_description == "蓉憶記小瓶 10顆裝"
        assert product.avg_price == 315.0
        assert product.popularity_score == 0.85


class TestRecommendationModels:
    """測試推薦相關模型"""
    
    def test_recommendation_creation(self):
        """測試推薦建立"""
        rec = Recommendation(
            product_id="30469",
            product_name="杏輝蓉憶記膠囊",
            confidence_score=85.5,
            explanation="基於您購買過的蓉憶記系列產品",
            rank=1
        )
        
        assert rec.product_id == "30469"
        assert rec.confidence_score == 85.5
        assert rec.rank == 1
    
    def test_recommendation_request(self):
        """測試推薦請求"""
        request = RecommendationRequest(
            member_code="CU000001",
            phone="0937024682",
            total_consumption=17400.0,
            accumulated_bonus=500.0,
            recent_purchases=["30463", "31033"]
        )
        
        assert request.member_code == "CU000001"
        assert len(request.recent_purchases) == 2
        assert request.top_k == 5  # 預設值
    
    def test_recommendation_response(self):
        """測試推薦回應"""
        recommendations = [
            Recommendation(
                product_id="30469",
                product_name="杏輝蓉憶記膠囊",
                confidence_score=85.5,
                explanation="基於您購買過的蓉憶記系列產品",
                rank=1
            )
        ]
        
        response = RecommendationResponse(
            recommendations=recommendations,
            response_time_ms=245.5,
            model_version="v1.0.0",
            member_code="CU000001"
        )
        
        assert len(response.recommendations) == 1
        assert response.response_time_ms == 245.5
        assert response.model_version == "v1.0.0"


class TestModelMetadata:
    """測試模型元資料"""
    
    def test_model_metrics(self):
        """測試模型指標"""
        metrics = ModelMetrics(
            accuracy=0.75,
            precision=0.72,
            recall=0.68,
            f1_score=0.70,
            precision_at_5=0.75,
            recall_at_5=0.68,
            ndcg_at_5=0.82
        )
        
        assert metrics.accuracy == 0.75
        assert metrics.precision_at_5 == 0.75
    
    def test_model_metadata(self):
        """測試模型元資料"""
        metrics = ModelMetrics(
            accuracy=0.75,
            precision=0.72,
            recall=0.68,
            f1_score=0.70,
            precision_at_5=0.75,
            recall_at_5=0.68,
            ndcg_at_5=0.82
        )
        
        metadata = ModelMetadata(
            version="v1.0.0",
            model_type=ModelType.LIGHTGBM,
            trained_at=datetime.now(),
            training_samples=10000,
            validation_samples=2000,
            test_samples=2000,
            metrics=metrics
        )
        
        assert metadata.version == "v1.0.0"
        assert metadata.model_type == ModelType.LIGHTGBM
        assert metadata.training_samples == 10000


class TestExampleFunctions:
    """測試範例函數"""
    
    def test_example_recommendation_request(self):
        """測試範例推薦請求"""
        request = example_recommendation_request()
        assert request.member_code == "CU000001"
        assert request.top_k == 5
    
    def test_example_recommendation_response(self):
        """測試範例推薦回應"""
        response = example_recommendation_response()
        assert len(response.recommendations) == 2
        assert response.model_version == "v1.0.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
