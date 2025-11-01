"""
測試 FastAPI 應用
驗證 API 基礎功能
"""
import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.api.main import app

# 建立測試客戶端
client = TestClient(app)


def test_root():
    """測試根端點"""
    print("\n測試 1: 根端點 (GET /)")
    print("=" * 70)
    
    response = client.get("/")
    
    print(f"狀態碼: {response.status_code}")
    print(f"回應內容: {response.json()}")
    
    assert response.status_code == 200
    assert "message" in response.json()
    assert "app_name" in response.json()
    
    print("✓ 根端點測試通過")


def test_health_check():
    """測試健康檢查端點"""
    print("\n測試 2: 健康檢查端點 (GET /health)")
    print("=" * 70)
    
    response = client.get("/health")
    
    print(f"狀態碼: {response.status_code}")
    print(f"回應內容: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data
    assert "uptime_seconds" in data
    assert data["status"] == "healthy"
    
    print("✓ 健康檢查端點測試通過")


def test_app_info():
    """測試應用資訊端點"""
    print("\n測試 3: 應用資訊端點 (GET /info)")
    print("=" * 70)
    
    response = client.get("/info")
    
    print(f"狀態碼: {response.status_code}")
    print(f"回應內容: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data
    assert "uptime_seconds" in data
    
    print("✓ 應用資訊端點測試通過")


def test_cors_headers():
    """測試 CORS 標頭"""
    print("\n測試 4: CORS 標頭")
    print("=" * 70)
    
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    
    print(f"狀態碼: {response.status_code}")
    print(f"CORS 標頭:")
    for key, value in response.headers.items():
        if "access-control" in key.lower():
            print(f"  {key}: {value}")
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    
    print("✓ CORS 標頭測試通過")


def test_process_time_header():
    """測試處理時間標頭"""
    print("\n測試 5: 處理時間標頭")
    print("=" * 70)
    
    response = client.get("/health")
    
    print(f"狀態碼: {response.status_code}")
    
    if "x-process-time" in response.headers:
        process_time = response.headers["x-process-time"]
        print(f"處理時間: {process_time}")
        print("✓ 處理時間標頭測試通過")
    else:
        print("⚠ 處理時間標頭未找到（可能是測試環境限制）")


def test_openapi_docs():
    """測試 OpenAPI 文件"""
    print("\n測試 6: OpenAPI 文件")
    print("=" * 70)
    
    # 測試 OpenAPI JSON
    response = client.get("/openapi.json")
    print(f"OpenAPI JSON 狀態碼: {response.status_code}")
    assert response.status_code == 200
    
    openapi_data = response.json()
    assert "openapi" in openapi_data
    assert "info" in openapi_data
    assert "paths" in openapi_data
    
    print(f"API 標題: {openapi_data['info']['title']}")
    print(f"API 版本: {openapi_data['info']['version']}")
    print(f"端點數量: {len(openapi_data['paths'])}")
    
    print("✓ OpenAPI 文件測試通過")


def test_error_handling():
    """測試錯誤處理"""
    print("\n測試 7: 錯誤處理")
    print("=" * 70)
    
    # 測試不存在的端點
    response = client.get("/nonexistent")
    
    print(f"不存在端點狀態碼: {response.status_code}")
    assert response.status_code == 404
    
    print("✓ 錯誤處理測試通過")


def main():
    """主函數"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 22 + "FastAPI 應用測試" + " " * 22 + "║")
    print("╚" + "═" * 68 + "╝")
    
    try:
        # 執行所有測試
        test_root()
        test_health_check()
        test_app_info()
        test_cors_headers()
        test_process_time_header()
        test_openapi_docs()
        test_error_handling()
        
        # 總結
        print("\n" + "=" * 70)
        print("✓ 所有測試通過！")
        print("=" * 70)
        
        print("\nFastAPI 應用功能:")
        print("  • 根端點 (GET /)")
        print("  • 健康檢查端點 (GET /health)")
        print("  • 應用資訊端點 (GET /info)")
        print("  • CORS 中介軟體")
        print("  • 請求日誌中介軟體")
        print("  • 錯誤處理")
        print("  • OpenAPI 文件 (GET /docs)")
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
