"""
測試模型資訊 API 端點
驗證模型資訊 API 的所有功能
"""
import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.api.main import app

# 建立測試客戶端
client = TestClient(app)


def test_model_info_endpoint():
    """測試模型資訊端點"""
    print("\n測試 1: 模型資訊端點 (GET /api/v1/model/info)")
    print("=" * 70)
    
    response = client.get("/api/v1/model/info")
    
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {response.json()}")
    
    # 如果模型未載入，應該返回 503
    # 如果模型已載入，應該返回 200
    assert response.status_code in [200, 503]
    
    if response.status_code == 200:
        data = response.json()
        
        # 檢查必要欄位
        assert "model_version" in data
        assert "model_type" in data
        assert "trained_at" in data
        assert "metrics" in data
        assert "total_products" in data
        assert "total_members" in data
        
        print(f"\n模型資訊:")
        print(f"  版本: {data['model_version']}")
        print(f"  類型: {data['model_type']}")
        print(f"  訓練時間: {data['trained_at']}")
        print(f"  產品數量: {data['total_products']}")
        print(f"  會員數量: {data['total_members']}")
        
        if data['metrics']:
            print(f"\n效能指標:")
            for key, value in data['metrics'].items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.4f}")
                else:
                    print(f"  {key}: {value}")
        
        print("\n✓ 模型資訊端點測試通過")
    else:
        print("⚠ 模型未載入（預期行為，需要先訓練模型）")


def test_model_info_response_structure():
    """測試模型資訊回應結構"""
    print("\n測試 2: 模型資訊回應結構")
    print("=" * 70)
    
    response = client.get("/api/v1/model/info")
    
    if response.status_code == 200:
        data = response.json()
        
        # 檢查資料類型
        assert isinstance(data['model_version'], str)
        assert isinstance(data['model_type'], str)
        assert isinstance(data['trained_at'], str)
        assert isinstance(data['metrics'], dict)
        assert isinstance(data['total_products'], int)
        assert isinstance(data['total_members'], int)
        
        # 檢查 metrics 結構
        if data['metrics']:
            expected_metrics = [
                'accuracy', 'precision', 'recall', 'f1_score',
                'precision_at_5', 'recall_at_5', 'ndcg_at_5'
            ]
            
            for metric in expected_metrics:
                if metric in data['metrics']:
                    assert isinstance(data['metrics'][metric], (int, float))
                    assert 0 <= data['metrics'][metric] <= 1
        
        print("✓ 模型資訊回應結構測試通過")
    else:
        print("⚠ 模型未載入，跳過結構測試")


def test_openapi_schema():
    """測試 OpenAPI 規範"""
    print("\n測試 3: OpenAPI 規範")
    print("=" * 70)
    
    response = client.get("/openapi.json")
    
    assert response.status_code == 200
    openapi_data = response.json()
    
    # 檢查模型資訊端點是否在規範中
    assert "/api/v1/model/info" in openapi_data["paths"]
    
    model_info_path = openapi_data["paths"]["/api/v1/model/info"]
    assert "get" in model_info_path
    
    get_spec = model_info_path["get"]
    print(f"端點摘要: {get_spec.get('summary')}")
    print(f"端點描述: {get_spec.get('description')}")
    print(f"標籤: {get_spec.get('tags')}")
    
    # 檢查回應規範
    assert "200" in get_spec["responses"]
    assert "500" in get_spec["responses"]
    assert "503" in get_spec["responses"]
    
    print("✓ OpenAPI 規範測試通過")


def test_model_info_vs_health():
    """測試模型資訊與健康檢查的一致性"""
    print("\n測試 4: 模型資訊與健康檢查的一致性")
    print("=" * 70)
    
    # 獲取健康檢查
    health_response = client.get("/api/v1/recommendations/health")
    assert health_response.status_code == 200
    health_data = health_response.json()
    
    # 獲取模型資訊
    info_response = client.get("/api/v1/model/info")
    
    # 如果健康檢查顯示模型已載入，模型資訊應該返回 200
    if health_data.get("details", {}).get("model_loaded"):
        assert info_response.status_code == 200
        print("✓ 模型已載入，兩個端點一致")
    else:
        # 如果模型未載入，模型資訊應該返回 503
        assert info_response.status_code == 503
        print("✓ 模型未載入，兩個端點一致")


def test_model_info_caching():
    """測試模型資訊的一致性（多次請求）"""
    print("\n測試 5: 模型資訊的一致性")
    print("=" * 70)
    
    # 發送多次請求
    responses = []
    for i in range(3):
        response = client.get("/api/v1/model/info")
        responses.append(response)
    
    # 檢查所有回應的狀態碼一致
    status_codes = [r.status_code for r in responses]
    assert len(set(status_codes)) == 1, "多次請求的狀態碼應該一致"
    
    # 如果模型已載入，檢查資訊一致性
    if responses[0].status_code == 200:
        data_list = [r.json() for r in responses]
        
        # 檢查版本一致
        versions = [d['model_version'] for d in data_list]
        assert len(set(versions)) == 1, "模型版本應該一致"
        
        # 檢查產品數量一致
        product_counts = [d['total_products'] for d in data_list]
        assert len(set(product_counts)) == 1, "產品數量應該一致"
        
        print(f"✓ 3 次請求的模型資訊一致")
    else:
        print("⚠ 模型未載入，跳過一致性測試")


def main():
    """主函數"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 19 + "模型資訊 API 端點測試" + " " * 19 + "║")
    print("╚" + "═" * 68 + "╝")
    
    try:
        # 執行所有測試
        test_model_info_endpoint()
        test_model_info_response_structure()
        test_openapi_schema()
        test_model_info_vs_health()
        test_model_info_caching()
        
        # 總結
        print("\n" + "=" * 70)
        print("✓ 所有測試通過！")
        print("=" * 70)
        
        print("\n模型資訊 API 功能:")
        print("  • GET /api/v1/model/info - 獲取模型資訊")
        print("  • 返回模型版本和類型")
        print("  • 返回訓練時間")
        print("  • 返回效能指標")
        print("  • 返回資料統計（產品數量、會員數量）")
        print("  • 錯誤處理（模型未載入等）")
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
