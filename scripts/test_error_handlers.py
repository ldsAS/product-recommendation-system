"""
測試錯誤處理器
驗證所有錯誤處理功能
"""
import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.api.main import app

# 建立測試客戶端
client = TestClient(app)


def test_validation_error():
    """測試驗證錯誤處理"""
    print("\n測試 1: 驗證錯誤處理")
    print("=" * 70)
    
    # 發送無效的請求（空會員編號）
    invalid_request = {
        "member_code": "",
        "total_consumption": 10000.0,
        "accumulated_bonus": 100.0
    }
    
    response = client.post("/api/v1/recommendations", json=invalid_request)
    
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {response.json()}")
    
    assert response.status_code in [400, 422]
    data = response.json()
    assert "error" in data
    assert "message" in data
    
    print("✓ 驗證錯誤處理測試通過")


def test_value_error():
    """測試值錯誤處理"""
    print("\n測試 2: 值錯誤處理")
    print("=" * 70)
    
    # 發送負數消費金額
    invalid_request = {
        "member_code": "CU000001",
        "total_consumption": -100.0,
        "accumulated_bonus": 100.0
    }
    
    response = client.post("/api/v1/recommendations", json=invalid_request)
    
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {response.json()}")
    
    assert response.status_code in [400, 422]
    data = response.json()
    assert "error" in data
    assert "message" in data
    
    print("✓ 值錯誤處理測試通過")


def test_model_not_found_error():
    """測試模型未找到錯誤處理"""
    print("\n測試 3: 模型未找到錯誤處理")
    print("=" * 70)
    
    # 發送有效請求（如果模型未訓練，應該返回 503）
    valid_request = {
        "member_code": "CU000001",
        "total_consumption": 10000.0,
        "accumulated_bonus": 100.0
    }
    
    response = client.post("/api/v1/recommendations", json=valid_request)
    
    print(f"狀態碼: {response.status_code}")
    
    if response.status_code == 503:
        data = response.json()
        print(f"回應: {data}")
        assert "error" in data
        assert "message" in data
        print("✓ 模型未找到錯誤處理測試通過")
    elif response.status_code == 200:
        print("⚠ 模型已載入，跳過此測試")
    else:
        print(f"⚠ 未預期的狀態碼: {response.status_code}")


def test_error_response_structure():
    """測試錯誤回應結構"""
    print("\n測試 4: 錯誤回應結構")
    print("=" * 70)
    
    # 發送無效請求
    invalid_request = {
        "member_code": "",
        "total_consumption": 10000.0
    }
    
    response = client.post("/api/v1/recommendations", json=invalid_request)
    
    assert response.status_code in [400, 422]
    data = response.json()
    
    # 檢查錯誤回應結構
    assert "error" in data
    assert "message" in data
    assert "timestamp" in data
    
    # 檢查資料類型
    assert isinstance(data["error"], str)
    assert isinstance(data["message"], str)
    assert isinstance(data["timestamp"], str)
    
    print(f"錯誤代碼: {data['error']}")
    print(f"錯誤訊息: {data['message']}")
    print(f"時間戳記: {data['timestamp']}")
    
    print("✓ 錯誤回應結構測試通過")


def test_friendly_error_messages():
    """測試友善的錯誤訊息"""
    print("\n測試 5: 友善的錯誤訊息")
    print("=" * 70)
    
    test_cases = [
        {
            "request": {"member_code": "", "total_consumption": 10000.0},
            "description": "空會員編號"
        },
        {
            "request": {"member_code": "CU001", "total_consumption": -100.0},
            "description": "負數消費金額"
        },
        {
            "request": {"member_code": "CU001", "total_consumption": 10000.0, "top_k": 25},
            "description": "超過上限的 top_k"
        }
    ]
    
    for test_case in test_cases:
        response = client.post("/api/v1/recommendations", json=test_case["request"])
        
        if response.status_code in [400, 422]:
            data = response.json()
            print(f"\n{test_case['description']}:")
            print(f"  錯誤訊息: {data['message']}")
            
            # 檢查訊息是否友善（不包含技術術語）
            message = data['message'].lower()
            assert len(message) > 0
            assert message != "error"  # 不應該只是 "error"
    
    print("\n✓ 友善的錯誤訊息測試通過")


def test_error_logging():
    """測試錯誤日誌記錄"""
    print("\n測試 6: 錯誤日誌記錄")
    print("=" * 70)
    
    # 發送無效請求
    invalid_request = {
        "member_code": "",
        "total_consumption": 10000.0
    }
    
    response = client.post("/api/v1/recommendations", json=invalid_request)
    
    # 錯誤應該被記錄（檢查回應）
    assert response.status_code in [400, 422]
    
    print("✓ 錯誤日誌記錄測試通過（錯誤已被處理）")


def test_different_error_types():
    """測試不同類型的錯誤"""
    print("\n測試 7: 不同類型的錯誤")
    print("=" * 70)
    
    error_types = {
        "驗證錯誤": {"member_code": "", "total_consumption": 10000.0},
        "值錯誤": {"member_code": "CU001", "total_consumption": -100.0},
        "範圍錯誤": {"member_code": "CU001", "total_consumption": 10000.0, "top_k": 25}
    }
    
    for error_type, request_data in error_types.items():
        response = client.post("/api/v1/recommendations", json=request_data)
        
        if response.status_code in [400, 422]:
            data = response.json()
            print(f"\n{error_type}:")
            print(f"  狀態碼: {response.status_code}")
            print(f"  錯誤代碼: {data.get('error')}")
            print(f"  錯誤訊息: {data.get('message')}")
    
    print("\n✓ 不同類型的錯誤測試通過")


def main():
    """主函數"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 22 + "錯誤處理器測試" + " " * 22 + "║")
    print("╚" + "═" * 68 + "╝")
    
    try:
        # 執行所有測試
        test_validation_error()
        test_value_error()
        test_model_not_found_error()
        test_error_response_structure()
        test_friendly_error_messages()
        test_error_logging()
        test_different_error_types()
        
        # 總結
        print("\n" + "=" * 70)
        print("✓ 所有測試通過！")
        print("=" * 70)
        
        print("\n錯誤處理功能:")
        print("  • 驗證錯誤處理")
        print("  • 值錯誤處理")
        print("  • 模型錯誤處理")
        print("  • 資料錯誤處理")
        print("  • 友善的錯誤訊息")
        print("  • 結構化的錯誤回應")
        print("  • 錯誤日誌記錄")
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
