"""
API 端點單元測試
"""
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.main import app

client = TestClient(app)


class TestAPIEndpoints:
    """API 端點測試類別"""
    
    def test_root_endpoint(self):
        """測試根端點"""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_api_root_endpoint(self):
        """測試 API 根端點"""
        response = client.get("/api")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_health_check_endpoint(self):
        """測試健康檢查端點"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "uptime_seconds" in data
    
    def test_info_endpoint(self):
        """測試資訊端點"""
        response = client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert "app_name" in data
        assert "version" in data
    
    def test_recommendations_endpoint_valid_request(self):
        """測試推薦端點 - 有效請求"""
        request_data = {
            "member_code": "CU000001",
            "total_consumption": 10000.0,
            "accumulated_bonus": 300.0,
            "top_k": 5
        }
        
        response = client.post("/api/v1/recommendations", json=request_data)
        
        # 如果模型未訓練，應該返回 503
        # 如果模型已訓練，應該返回 200
        assert response.status_code in [200, 503]
    
    def test_recommendations_endpoint_invalid_request(self):
        """測試推薦端點 - 無效請求"""
        request_data = {
            # 缺少必填欄位 member_code
            "total_consumption": 10000.0,
            "accumulated_bonus": 300.0
        }
        
        response = client.post("/api/v1/recommendations", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_recommendations_endpoint_invalid_top_k(self):
        """測試推薦端點 - 無效的 top_k"""
        request_data = {
            "member_code": "CU000001",
            "total_consumption": 10000.0,
            "accumulated_bonus": 300.0,
            "top_k": 25  # 超過限制
        }
        
        response = client.post("/api/v1/recommendations", json=request_data)
        assert response.status_code in [400, 422]
    
    def test_model_info_endpoint(self):
        """測試模型資訊端點"""
        response = client.get("/api/v1/model/info")
        
        # 如果模型未訓練，應該返回 503
        # 如果模型已訓練，應該返回 200
        assert response.status_code in [200, 503]
    
    def test_recommendations_health_endpoint(self):
        """測試推薦服務健康檢查端點"""
        response = client.get("/api/v1/recommendations/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
