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
    
    def test_enhanced_recommendations_response_format(self):
        """測試增強推薦 API 的新回應格式"""
        request_data = {
            "member_code": "CU000001",
            "total_consumption": 10000.0,
            "accumulated_bonus": 300.0,
            "top_k": 5
        }
        
        response = client.post("/api/v1/recommendations?use_enhanced=true", json=request_data)
        
        # 如果模型未訓練，跳過測試
        if response.status_code == 503:
            pytest.skip("模型未訓練")
        
        assert response.status_code == 200
        data = response.json()
        
        # 檢查原有欄位（向後兼容）
        assert "recommendations" in data
        assert "response_time_ms" in data
        assert "model_version" in data
        assert "request_id" in data
        assert "member_code" in data
        assert "timestamp" in data
        
        # 檢查新增欄位
        assert "reference_value_score" in data
        assert "performance_metrics" in data
        assert "quality_level" in data
        assert "is_degraded" in data
        
        # 檢查可參考價值分數結構
        ref_score = data["reference_value_score"]
        assert "overall_score" in ref_score
        assert "relevance_score" in ref_score
        assert "novelty_score" in ref_score
        assert "explainability_score" in ref_score
        assert "diversity_score" in ref_score
        assert "score_breakdown" in ref_score
        
        # 檢查性能指標結構
        perf_metrics = data["performance_metrics"]
        assert "request_id" in perf_metrics
        assert "total_time_ms" in perf_metrics
        assert "stage_times" in perf_metrics
        assert "is_slow_query" in perf_metrics
        
        # 檢查分數範圍
        assert 0 <= ref_score["overall_score"] <= 100
        assert 0 <= ref_score["relevance_score"] <= 100
        assert 0 <= ref_score["novelty_score"] <= 100
        assert 0 <= ref_score["explainability_score"] <= 100
        assert 0 <= ref_score["diversity_score"] <= 100
        
        # 檢查品質等級
        assert data["quality_level"] in ["excellent", "good", "acceptable", "poor"]
        
        # 檢查降級標記
        assert isinstance(data["is_degraded"], bool)
    
    def test_legacy_recommendations_response_format(self):
        """測試原有推薦 API 的回應格式（向後兼容）"""
        request_data = {
            "member_code": "CU000001",
            "total_consumption": 10000.0,
            "accumulated_bonus": 300.0,
            "top_k": 5
        }
        
        response = client.post("/api/v1/recommendations?use_enhanced=false", json=request_data)
        
        # 如果模型未訓練，跳過測試
        if response.status_code == 503:
            pytest.skip("模型未訓練")
        
        assert response.status_code == 200
        data = response.json()
        
        # 檢查原有欄位
        assert "recommendations" in data
        assert "response_time_ms" in data
        assert "model_version" in data
        assert "request_id" in data
        assert "member_code" in data
        assert "timestamp" in data
    
    def test_monitoring_realtime_endpoint(self):
        """測試即時監控數據端點"""
        response = client.get("/api/v1/monitoring/realtime")
        assert response.status_code == 200
        data = response.json()
        
        assert "time_window_minutes" in data
        assert "total_records" in data
        assert "timestamp" in data
        
        # 如果有記錄，檢查數據結構
        if data["total_records"] > 0:
            assert "unique_members" in data
            assert "quality_metrics" in data
            assert "performance_metrics" in data
            assert "degradation_count" in data
            
            # 檢查品質指標結構
            quality = data["quality_metrics"]
            assert "overall_score" in quality
            assert "relevance_score" in quality
            assert "novelty_score" in quality
            assert "explainability_score" in quality
            assert "diversity_score" in quality
            
            # 檢查性能指標結構
            performance = data["performance_metrics"]
            assert "response_time_ms" in performance
    
    def test_monitoring_realtime_with_time_window(self):
        """測試即時監控數據端點 - 自訂時間窗口"""
        response = client.get("/api/v1/monitoring/realtime?time_window_minutes=30")
        assert response.status_code == 200
        data = response.json()
        assert data["time_window_minutes"] == 30
    
    def test_monitoring_realtime_with_member_filter(self):
        """測試即時監控數據端點 - 會員過濾"""
        response = client.get("/api/v1/monitoring/realtime?member_code=CU000001")
        assert response.status_code == 200
        data = response.json()
        assert "total_records" in data
    
    def test_monitoring_statistics_hourly(self):
        """測試歷史統計數據端點 - 小時報告"""
        response = client.get("/api/v1/monitoring/statistics?report_type=hourly")
        assert response.status_code == 200
        data = response.json()
        
        assert data["report_type"] == "hourly"
        assert "start_time" in data
        assert "end_time" in data
        assert "recommendation_stats" in data
        assert "quality_stats" in data
        assert "performance_stats" in data
        assert "alert_stats" in data
        assert "trends" in data
        assert "recommendations_for_improvement" in data
        assert "timestamp" in data
        
        # 檢查推薦統計結構
        rec_stats = data["recommendation_stats"]
        assert "total_recommendations" in rec_stats
        assert "unique_members" in rec_stats
        assert "avg_recommendations_per_member" in rec_stats
        
        # 檢查品質統計結構
        quality_stats = data["quality_stats"]
        assert "avg_overall_score" in quality_stats
        assert "avg_relevance_score" in quality_stats
        assert "avg_novelty_score" in quality_stats
        assert "avg_explainability_score" in quality_stats
        assert "avg_diversity_score" in quality_stats
        
        # 檢查性能統計結構
        perf_stats = data["performance_stats"]
        assert "avg_response_time_ms" in perf_stats
        assert "p50_response_time_ms" in perf_stats
        assert "p95_response_time_ms" in perf_stats
        assert "p99_response_time_ms" in perf_stats
        
        # 檢查告警統計結構
        alert_stats = data["alert_stats"]
        assert "total_alerts" in alert_stats
        assert "critical_alerts" in alert_stats
        assert "warning_alerts" in alert_stats
        assert "degradation_count" in alert_stats
        
        # 檢查趨勢結構
        trends = data["trends"]
        assert "score_trend" in trends
        assert "performance_trend" in trends
        assert trends["score_trend"] in ["improving", "stable", "declining"]
        assert trends["performance_trend"] in ["improving", "stable", "declining"]
    
    def test_monitoring_statistics_daily(self):
        """測試歷史統計數據端點 - 日報"""
        response = client.get("/api/v1/monitoring/statistics?report_type=daily")
        assert response.status_code == 200
        data = response.json()
        assert data["report_type"] == "daily"
    
    def test_monitoring_statistics_invalid_type(self):
        """測試歷史統計數據端點 - 無效報告類型"""
        response = client.get("/api/v1/monitoring/statistics?report_type=weekly")
        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"]
    
    def test_monitoring_alerts_endpoint(self):
        """測試告警記錄端點"""
        response = client.get("/api/v1/monitoring/alerts")
        assert response.status_code == 200
        data = response.json()
        
        assert "time_window_minutes" in data
        assert "filter_level" in data
        assert "total_alerts" in data
        assert "alert_counts" in data
        assert "alerts" in data
        assert "timestamp" in data
        
        # 檢查告警計數結構
        alert_counts = data["alert_counts"]
        assert "info" in alert_counts
        assert "warning" in alert_counts
        assert "critical" in alert_counts
        
        # 如果有告警，檢查告警結構
        if data["total_alerts"] > 0:
            alert = data["alerts"][0]
            assert "level" in alert
            assert "metric_name" in alert
            assert "current_value" in alert
            assert "threshold_value" in alert
            assert "message" in alert
            assert "timestamp" in alert
            assert alert["level"] in ["info", "warning", "critical"]
    
    def test_monitoring_alerts_with_time_window(self):
        """測試告警記錄端點 - 自訂時間窗口"""
        response = client.get("/api/v1/monitoring/alerts?time_window_minutes=30")
        assert response.status_code == 200
        data = response.json()
        assert data["time_window_minutes"] == 30
    
    def test_monitoring_alerts_with_level_filter(self):
        """測試告警記錄端點 - 等級過濾"""
        response = client.get("/api/v1/monitoring/alerts?level=critical")
        assert response.status_code == 200
        data = response.json()
        assert data["filter_level"] == "critical"
        
        # 檢查所有告警都是 critical 等級
        for alert in data["alerts"]:
            assert alert["level"] == "critical"
    
    def test_monitoring_alerts_invalid_level(self):
        """測試告警記錄端點 - 無效等級"""
        response = client.get("/api/v1/monitoring/alerts?level=invalid")
        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"]
    
    def test_api_error_handling(self):
        """測試 API 錯誤處理"""
        # 測試無效的 JSON
        response = client.post(
            "/api/v1/recommendations",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
        
        # 測試缺少必填欄位
        response = client.post("/api/v1/recommendations", json={})
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
