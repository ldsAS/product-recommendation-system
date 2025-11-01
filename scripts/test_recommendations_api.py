"""
測試推薦 API 端點
驗證推薦 API 的所有功能
"""
import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.api.main import app

# 建立測試客戶端
client = TestClient(app)


def test_recommendations_endpoint_structure():
    """測試推薦端點結構（不需要模型）"""
    print("\n測試 1: 推薦端點結構")
    print("=" * 70)
    
    # 測試有效的請求結構
    request_data = {
        "member_code": "CU000001",
        "phone": "0937024682",
        "total_consumption": 17400.0,
        "accumulated_bonus": 500.0,
        "recent_purchases": ["30463", "31033"],
        "top_k": 5,
        "min_confidence": 0.0
    }
    
    print(f"請求資料: {request_data}")
    
    # 注意：這個測試可能會失敗如果模型未訓練
    # 但我們可以檢查端點是否存在
    response = client.post("/api/v1/recommendations", json=request_data)
    
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {response.json()}")
    
    # 如果模型未載入，應該返回 503
    # 如果模型已載入，應該返回 200
    assert response.status_code in [200, 503]
    
    if response.status_code == 503:
        print("⚠ 模型未載入（預期行為，需要先訓練模型）")
    else:
        print("✓ 推薦端點測試通過")


def test_validation_errors():
    """測試驗證錯誤"""
    print("\n測試 2: 驗證錯誤")
    print("=" * 70)
    
    # 測試無效的請求（空會員編號）
    invalid_request = {
        "member_code": "",  # 空的會員編號
        "total_consumption": 10000.0,
        "accumulated_bonus": 100.0
    }
    
    print(f"無效請求: {invalid_request}")
    
    response = client.post("/api/v1/recommendations", json=invalid_request)
    
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {response.json()}")
    
    # 應該返回 400 或 422（驗證錯誤）
    assert response.status_code in [400, 422]
    
    print("✓ 驗證錯誤測試通過")


def test_invalid_phone():
    """測試無效電話號碼"""
    print("\n測試 3: 無效電話號碼")
    print("=" * 70)
    
    invalid_request = {
        "member_code": "CU000001",
        "phone": "invalid_phone",  # 無效的電話號碼
        "total_consumption": 10000.0,
        "accumulated_bonus": 100.0
    }
    
    print(f"無效請求: {invalid_request}")
    
    response = client.post("/api/v1/recommendations", json=invalid_request)
    
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {response.json()}")
    
    # 應該返回 400 或 422（驗證錯誤）
    assert response.status_code in [400, 422]
    
    print("✓ 無效電話號碼測試通過")


def test_negative_consumption():
    """測試負數消費金額"""
    print("\n測試 4: 負數消費金額")
    print("=" * 70)
    
    invalid_request = {
        "member_code": "CU000001",
        "total_consumption": -100.0,  # 負數
        "accumulated_bonus": 100.0
    }
    
    print(f"無效請求: {invalid_request}")
    
    response = client.post("/api/v1/recommendations", json=invalid_request)
    
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {response.json()}")
    
    # 應該返回 400 或 422（驗證錯誤）
    assert response.status_code in [400, 422]
    
    print("✓ 負數消費金額測試通過")


def test_invalid_top_k():
    """測試無效的 top_k"""
    print("\n測試 5: 無效的 top_k")
    print("=" * 70)
    
    invalid_request = {
        "member_code": "CU000001",
        "total_consumption": 10000.0,
        "accumulated_bonus": 100.0,
        "top_k": 25  # 超過上限
    }
    
    print(f"無效請求: {invalid_request}")
    
    response = client.post("/api/v1/recommendations", json=invalid_request)
    
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {response.json()}")
    
    # 應該返回 400（驗證錯誤）
    assert response.status_code == 400
    
    print("✓ 無效 top_k 測試通過")


def test_recommendations_health():
    """測試推薦服務健康檢查"""
    print("\n測試 6: 推薦服務健康檢查")
    print("=" * 70)
    
    response = client.get("/api/v1/recommendations/health")
    
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "service" in data
    assert data["service"] == "recommendations"
    
    print("✓ 推薦服務健康檢查測試通過")


def test_openapi_schema():
    """測試 OpenAPI 規範"""
    print("\n測試 7: OpenAPI 規範")
    print("=" * 70)
    
    response = client.get("/openapi.json")
    
    assert response.status_code == 200
    openapi_data = response.json()
    
    # 檢查推薦端點是否在規範中
    assert "/api/v1/recommendations" in openapi_data["paths"]
    
    recommendations_path = openapi_data["paths"]["/api/v1/recommendations"]
    assert "post" in recommendations_path
    
    post_spec = recommendations_path["post"]
    print(f"端點摘要: {post_spec.get('summary')}")
    print(f"端點描述: {post_spec.get('description')}")
    print(f"標籤: {post_spec.get('tags')}")
    
    print("✓ OpenAPI 規範測試通過")


def test_valid_request_minimal():
    """測試最小有效請求"""
    print("\n測試 8: 最小有效請求")
    print("=" * 70)
    
    minimal_request = {
        "member_code": "CU000001",
        "total_consumption": 10000.0,
        "accumulated_bonus": 100.0
    }
    
    print(f"最小請求: {minimal_request}")
    
    response = client.post("/api/v1/recommendations", json=minimal_request)
    
    print(f"狀態碼: {response.status_code}")
    
    # 如果模型已載入，應該返回 200
    # 如果模型未載入，應該返回 503
    assert response.status_code in [200, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert "recommendations" in data
        assert "response_time_ms" in data
        assert "model_version" in data
        assert "request_id" in data
        print("✓ 最小有效請求測試通過")
    else:
        print("⚠ 模型未載入（需要先訓練模型）")


def main():
    """主函數"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "推薦 API 端點測試" + " " * 20 + "║")
    print("╚" + "═" * 68 + "╝")
    
    try:
        # 執行所有測試
        test_recommendations_endpoint_structure()
        test_validation_errors()
        test_invalid_phone()
        test_negative_consumption()
        test_invalid_top_k()
        test_recommendations_health()
        test_openapi_schema()
        test_valid_request_minimal()
        
        # 總結
        print("\n" + "=" * 70)
        print("✓ 所有測試通過！")
        print("=" * 70)
        
        print("\n推薦 API 功能:")
        print("  • POST /api/v1/recommendations - 獲取產品推薦")
        print("  • GET /api/v1/recommendations/health - 推薦服務健康檢查")
        print("  • 輸入驗證（會員編號、電話、消費金額等）")
        print("  • 錯誤處理（驗證錯誤、模型錯誤等）")
        print("  • 回應時間監控")
        print("  • 請求 ID 追蹤")
        print("\n注意: 如果看到模型未載入的警告，請先執行訓練:")
        print("  python src/train.py")
        print("\n")
        
        return 0
        
    except AssertionError as e:
        print(f"\n✗ 測試失敗: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
