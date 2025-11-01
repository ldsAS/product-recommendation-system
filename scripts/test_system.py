"""
系統整體測試腳本
測試推薦系統的各個組件是否正常運作
"""
import sys
import os
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
from datetime import datetime


def print_section(title: str):
    """列印區塊標題"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_data_models():
    """測試資料模型"""
    print_section("測試資料模型")
    
    try:
        from src.models.data_models import (
            MemberInfo,
            RecommendationRequest,
            RecommendationResponse,
            Recommendation,
            ModelMetrics,
            ABTestConfig
        )
        
        # 測試會員資訊
        member = MemberInfo(
            member_code="CU000001",
            phone="0937024682",
            total_consumption=17400.0,
            accumulated_bonus=500.0,
            recent_purchases=["30463", "31033"]
        )
        print(f"✓ 會員資訊模型: {member.member_code}")
        
        # 測試推薦請求
        request = RecommendationRequest(
            member_code="CU000001",
            total_consumption=17400.0,
            accumulated_bonus=500.0,
            top_k=5
        )
        print(f"✓ 推薦請求模型: Top {request.top_k}")
        
        # 測試推薦結果
        recommendation = Recommendation(
            product_id="30469",
            product_name="測試產品",
            confidence_score=85.5,
            explanation="測試理由",
            rank=1
        )
        print(f"✓ 推薦結果模型: {recommendation.product_name}")
        
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
        print(f"✓ 模型指標: Accuracy={metrics.accuracy:.2f}")
        
        # 測試 A/B 測試配置
        ab_config = ABTestConfig(
            enabled=True,
            model_a_version="v1.0.0",
            model_b_version="v1.1.0",
            model_a_ratio=0.5
        )
        print(f"✓ A/B 測試配置: {ab_config.model_a_version} vs {ab_config.model_b_version}")
        
        print("\n✅ 資料模型測試通過")
        return True
        
    except Exception as e:
        print(f"\n❌ 資料模型測試失敗: {e}")
        return False


def test_validators():
    """測試驗證器"""
    print_section("測試驗證器")
    
    try:
        from src.utils.validators import (
            validate_phone_number,
            validate_member_code,
            validate_recommendation_request
        )
        from src.models.data_models import RecommendationRequest
        
        # 測試電話號碼驗證
        valid_phone = validate_phone_number("0937024682")
        print(f"✓ 電話號碼驗證: {valid_phone.is_valid}")
        
        # 測試會員編號驗證
        valid_member = validate_member_code("CU000001")
        print(f"✓ 會員編號驗證: {valid_member.is_valid}")
        
        # 測試推薦請求驗證
        request = RecommendationRequest(
            member_code="CU000001",
            total_consumption=17400.0,
            accumulated_bonus=500.0
        )
        valid_request = validate_recommendation_request(request)
        print(f"✓ 推薦請求驗證: {valid_request.is_valid}")
        
        print("\n✅ 驗證器測試通過")
        return True
        
    except Exception as e:
        print(f"\n❌ 驗證器測試失敗: {e}")
        return False


def test_logger():
    """測試日誌系統"""
    print_section("測試日誌系統")
    
    try:
        from src.utils.logger import setup_logger, get_logger
        
        # 設置日誌管理器
        logger_manager = setup_logger(
            log_dir="logs/test",
            app_name="test_system",
            log_level="INFO",
            enable_console=False,
            enable_file=True,
            enable_json=False
        )
        print("✓ 日誌管理器初始化")
        
        # 獲取日誌器
        logger = get_logger('test')
        logger.info("測試日誌訊息")
        print("✓ 日誌記錄")
        
        # 測試推薦日誌
        logger_manager.log_recommendation(
            request_id="test-123",
            member_code="CU000001",
            recommendations=[],
            response_time_ms=100.0,
            model_version="v1.0.0"
        )
        print("✓ 推薦日誌記錄")
        
        # 測試錯誤日誌
        logger_manager.log_error(
            error_type="TestError",
            error_message="測試錯誤訊息",
            request_id="test-456"
        )
        print("✓ 錯誤日誌記錄")
        
        print("\n✅ 日誌系統測試通過")
        return True
        
    except Exception as e:
        print(f"\n❌ 日誌系統測試失敗: {e}")
        return False


def test_metrics():
    """測試效能追蹤"""
    print_section("測試效能追蹤")
    
    try:
        from src.utils.metrics import PerformanceTracker
        
        # 建立效能追蹤器
        tracker = PerformanceTracker()
        print("✓ 效能追蹤器初始化")
        
        # 追蹤 API 請求
        tracker.track_api_request(
            endpoint="/api/v1/recommendations",
            method="POST",
            status_code=200,
            response_time_ms=150.0
        )
        print("✓ API 請求追蹤")
        
        # 追蹤推薦
        tracker.track_recommendation(
            member_code="CU000001",
            num_recommendations=5,
            response_time_ms=150.0,
            model_version="v1.0.0"
        )
        print("✓ 推薦追蹤")
        
        # 追蹤轉換
        tracker.track_conversion(
            member_code="CU000001",
            product_id="30469",
            converted=True,
            model_version="v1.0.0"
        )
        print("✓ 轉換追蹤")
        
        # 獲取指標
        api_metrics = tracker.get_api_metrics()
        print(f"✓ API 指標: {api_metrics['total_requests']} 個請求")
        
        rec_metrics = tracker.get_recommendation_metrics()
        print(f"✓ 推薦指標: {rec_metrics['total_recommendations']} 個推薦")
        
        # 匯出 Prometheus 格式
        prometheus_output = tracker.metrics.export_prometheus()
        print(f"✓ Prometheus 匯出: {len(prometheus_output)} 字元")
        
        print("\n✅ 效能追蹤測試通過")
        return True
        
    except Exception as e:
        print(f"\n❌ 效能追蹤測試失敗: {e}")
        return False


def test_ab_test_manager():
    """測試 A/B 測試管理器"""
    print_section("測試 A/B 測試管理器")
    
    try:
        from src.models.ab_test_manager import ABTestManager
        
        # 建立管理器
        manager = ABTestManager(
            config_path="data/test/ab_test_config.json",
            results_path="data/test/ab_test_results.json"
        )
        print("✓ A/B 測試管理器初始化")
        
        # 啟用測試
        manager.enable_test(
            model_a_version="v1.0.0",
            model_b_version="v1.1.0",
            model_a_ratio=0.5
        )
        print("✓ A/B 測試啟用")
        
        # 選擇模型
        model_version = manager.select_model("user_001")
        print(f"✓ 模型選擇: {model_version}")
        
        # 記錄請求
        manager.record_request(model_version, 150.0, 5)
        print("✓ 請求記錄")
        
        # 記錄轉換
        manager.record_conversion(model_version, True)
        print("✓ 轉換記錄")
        
        # 獲取結果
        results = manager.get_results()
        print(f"✓ 測試結果: {len(results)} 個模型")
        
        # 比較模型
        comparison = manager.compare_models()
        print(f"✓ 模型比較: {comparison['enabled']}")
        
        # 停用測試
        manager.disable_test()
        print("✓ A/B 測試停用")
        
        print("\n✅ A/B 測試管理器測試通過")
        return True
        
    except Exception as e:
        print(f"\n❌ A/B 測試管理器測試失敗: {e}")
        return False


def test_model_manager():
    """測試模型管理器"""
    print_section("測試模型管理器")
    
    try:
        from src.models.model_manager import ModelManager
        
        # 建立模型管理器
        manager = ModelManager(models_dir="data/models")
        print("✓ 模型管理器初始化")
        
        # 列出版本
        versions = manager.list_versions()
        print(f"✓ 可用版本: {len(versions)} 個")
        
        if versions:
            print(f"  版本列表: {', '.join(versions)}")
        
        print("\n✅ 模型管理器測試通過")
        return True
        
    except Exception as e:
        print(f"\n❌ 模型管理器測試失敗: {e}")
        return False


def test_explanation_generator():
    """測試推薦理由生成器"""
    print_section("測試推薦理由生成器")
    
    try:
        from src.models.explanation_generator import ExplanationGenerator
        from src.models.data_models import MemberFeatures, ProductFeatures
        
        # 建立生成器
        generator = ExplanationGenerator()
        print("✓ 推薦理由生成器初始化")
        
        # 建立測試資料
        member = MemberFeatures(
            member_code="CU000001",
            total_consumption=17400.0,
            accumulated_bonus=500.0,
            recency=5,
            frequency=10,
            monetary=1740.0
        )
        
        product = ProductFeatures(
            stock_id="30469",
            avg_price=600.0,
            popularity_score=0.8,
            total_sales=100,
            unique_buyers=50,
            avg_quantity_per_order=2.0
        )
        
        # 生成理由
        explanation = generator.generate_explanation(
            member_features=member,
            product_features=product,
            recommendation_source="ml_model",
            confidence_score=85.5
        )
        print(f"✓ 推薦理由生成: {explanation[:50]}...")
        
        print("\n✅ 推薦理由生成器測試通過")
        return True
        
    except Exception as e:
        print(f"\n❌ 推薦理由生成器測試失敗: {e}")
        return False


def main():
    """主函數"""
    print("\n" + "=" * 70)
    print("  產品推薦系統 - 整體測試")
    print("=" * 70)
    print(f"  測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 執行所有測試
    tests = [
        ("資料模型", test_data_models),
        ("驗證器", test_validators),
        ("日誌系統", test_logger),
        ("效能追蹤", test_metrics),
        ("A/B 測試管理器", test_ab_test_manager),
        ("模型管理器", test_model_manager),
        ("推薦理由生成器", test_explanation_generator),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} 測試執行失敗: {e}")
            results.append((name, False))
    
    # 顯示總結
    print_section("測試總結")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n測試結果: {passed}/{total} 通過\n")
    
    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {status}  {name}")
    
    print("\n" + "=" * 70)
    
    if passed == total:
        print("  🎉 所有測試通過！")
    else:
        print(f"  ⚠️  {total - passed} 個測試失敗")
    
    print("=" * 70 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
