"""
驗證資料模型是否正常運作
"""
import sys
from pathlib import Path

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

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
from datetime import datetime


def test_member_models():
    """測試會員模型"""
    print("測試會員模型...")
    
    # 測試會員特徵
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
    print("  ✓ MemberFeatures 正常")
    
    # 測試會員資訊
    info = MemberInfo(
        member_code="CU000001",
        phone="0937024682",
        total_consumption=17400.0
    )
    assert info.member_code == "CU000001"
    print("  ✓ MemberInfo 正常")
    
    # 測試電話驗證
    try:
        MemberInfo(
            member_code="CU000001",
            phone="invalid_phone",
            total_consumption=17400.0
        )
        print("  ✗ 電話驗證失敗")
        return False
    except ValueError:
        print("  ✓ 電話驗證正常")
    
    return True


def test_product_models():
    """測試產品模型"""
    print("\n測試產品模型...")
    
    product = Product(
        stock_id="30463",
        stock_description="蓉憶記小瓶 10顆裝",
        avg_price=315.0,
        popularity_score=0.85
    )
    assert product.stock_id == "30463"
    assert product.avg_price == 315.0
    print("  ✓ Product 正常")
    
    return True


def test_recommendation_models():
    """測試推薦模型"""
    print("\n測試推薦模型...")
    
    # 測試推薦
    rec = Recommendation(
        product_id="30469",
        product_name="杏輝蓉憶記膠囊",
        confidence_score=85.5,
        explanation="基於您購買過的蓉憶記系列產品",
        rank=1
    )
    assert rec.product_id == "30469"
    assert rec.confidence_score == 85.5
    print("  ✓ Recommendation 正常")
    
    # 測試推薦請求
    request = RecommendationRequest(
        member_code="CU000001",
        phone="0937024682",
        total_consumption=17400.0,
        accumulated_bonus=500.0,
        recent_purchases=["30463", "31033"]
    )
    assert request.member_code == "CU000001"
    assert len(request.recent_purchases) == 2
    print("  ✓ RecommendationRequest 正常")
    
    # 測試推薦回應
    response = RecommendationResponse(
        recommendations=[rec],
        response_time_ms=245.5,
        model_version="v1.0.0",
        member_code="CU000001"
    )
    assert len(response.recommendations) == 1
    assert response.model_version == "v1.0.0"
    print("  ✓ RecommendationResponse 正常")
    
    return True


def test_model_metadata():
    """測試模型元資料"""
    print("\n測試模型元資料...")
    
    # 測試模型指標
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
    print("  ✓ ModelMetrics 正常")
    
    # 測試模型元資料
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
    print("  ✓ ModelMetadata 正常")
    
    return True


def test_example_functions():
    """測試範例函數"""
    print("\n測試範例函數...")
    
    request = example_recommendation_request()
    assert request.member_code == "CU000001"
    print("  ✓ example_recommendation_request 正常")
    
    response = example_recommendation_response()
    assert len(response.recommendations) == 2
    print("  ✓ example_recommendation_response 正常")
    
    return True


def main():
    """主函數"""
    print("=" * 60)
    print("驗證資料模型")
    print("=" * 60)
    
    all_passed = True
    
    try:
        all_passed &= test_member_models()
        all_passed &= test_product_models()
        all_passed &= test_recommendation_models()
        all_passed &= test_model_metadata()
        all_passed &= test_example_functions()
        
        print("\n" + "=" * 60)
        if all_passed:
            print("✓ 所有測試通過！")
            print("=" * 60)
            return 0
        else:
            print("✗ 部分測試失敗")
            print("=" * 60)
            return 1
            
    except Exception as e:
        print(f"\n✗ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
