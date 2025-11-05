"""
性能追蹤器單元測試
測試 PerformanceTracker 的追蹤流程、統計計算和慢查詢檢測功能
"""
import pytest
import time
from datetime import timedelta
from src.utils.performance_tracker import PerformanceTracker
from src.models.enhanced_data_models import PerformanceMetrics, PerformanceStats


class TestPerformanceTracker:
    """測試 PerformanceTracker 類別"""
    
    def test_start_tracking(self):
        """測試開始追蹤功能"""
        tracker = PerformanceTracker()
        request_id = "test_001"
        
        # 開始追蹤
        tracker.start_tracking(request_id)
        
        # 驗證請求已在追蹤中
        assert request_id in tracker._tracking_requests
        assert 'start' in tracker._tracking_requests[request_id]
        
    def test_start_tracking_duplicate_request(self):
        """測試重複追蹤同一請求應拋出錯誤"""
        tracker = PerformanceTracker()
        request_id = "test_001"
        
        tracker.start_tracking(request_id)
        
        # 嘗試重複追蹤應拋出 ValueError
        with pytest.raises(ValueError, match="已經在追蹤中"):
            tracker.start_tracking(request_id)
    
    def test_track_stage(self):
        """測試記錄階段功能"""
        tracker = PerformanceTracker()
        request_id = "test_001"
        
        tracker.start_tracking(request_id)
        time.sleep(0.05)  # 等待50ms
        
        # 記錄階段
        tracker.track_stage(request_id, "feature_loading")
        
        # 驗證階段已記錄
        assert "feature_loading" in tracker._tracking_requests[request_id]
        
    def test_track_stage_without_start(self):
        """測試未開始追蹤就記錄階段應拋出錯誤"""
        tracker = PerformanceTracker()
        request_id = "test_001"
        
        # 未開始追蹤就記錄階段應拋出 ValueError
        with pytest.raises(ValueError, match="未開始追蹤"):
            tracker.track_stage(request_id, "feature_loading")
    
    def test_end_tracking(self):
        """測試結束追蹤並計算性能指標"""
        tracker = PerformanceTracker()
        request_id = "test_001"
        
        # 模擬完整追蹤流程
        tracker.start_tracking(request_id)
        time.sleep(0.05)  # 50ms
        tracker.track_stage(request_id, "feature_loading")
        time.sleep(0.05)  # 50ms
        tracker.track_stage(request_id, "model_inference")
        time.sleep(0.05)  # 50ms
        
        # 結束追蹤
        metrics = tracker.end_tracking(request_id)
        
        # 驗證返回的性能指標
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.request_id == request_id
        assert metrics.total_time_ms >= 150  # 至少150ms
        assert "feature_loading" in metrics.stage_times
        assert "model_inference" in metrics.stage_times
        assert metrics.stage_times["feature_loading"] >= 50
        assert metrics.stage_times["model_inference"] >= 50
        
        # 驗證請求已從追蹤中移除
        assert request_id not in tracker._tracking_requests
        
        # 驗證已保存到歷史記錄
        assert tracker.get_history_count() == 1
    
    def test_end_tracking_without_start(self):
        """測試未開始追蹤就結束應拋出錯誤"""
        tracker = PerformanceTracker()
        request_id = "test_001"
        
        # 未開始追蹤就結束應拋出 ValueError
        with pytest.raises(ValueError, match="未開始追蹤"):
            tracker.end_tracking(request_id)
    
    def test_slow_query_detection(self):
        """測試慢查詢檢測功能"""
        # 設置較低的慢查詢閾值以便測試
        tracker = PerformanceTracker(slow_query_threshold_ms=100)
        
        # 測試正常查詢
        request_id_1 = "test_001"
        tracker.start_tracking(request_id_1)
        time.sleep(0.05)  # 50ms
        metrics_1 = tracker.end_tracking(request_id_1)
        assert not metrics_1.is_slow_query
        
        # 測試慢查詢
        request_id_2 = "test_002"
        tracker.start_tracking(request_id_2)
        time.sleep(0.15)  # 150ms，超過閾值
        metrics_2 = tracker.end_tracking(request_id_2)
        assert metrics_2.is_slow_query
    
    def test_get_statistics_empty_history(self):
        """測試空歷史記錄的統計"""
        tracker = PerformanceTracker()
        
        stats = tracker.get_statistics()
        
        assert isinstance(stats, PerformanceStats)
        assert stats.total_requests == 0
        assert stats.p50_time_ms == 0.0
        assert stats.p95_time_ms == 0.0
        assert stats.p99_time_ms == 0.0
        assert stats.avg_time_ms == 0.0
        assert stats.slow_query_count == 0
        assert stats.slow_query_rate == 0.0
    
    def test_get_statistics_with_data(self):
        """測試有數據的統計計算"""
        tracker = PerformanceTracker(slow_query_threshold_ms=100)
        
        # 生成多個請求的追蹤數據
        for i in range(10):
            request_id = f"test_{i:03d}"
            tracker.start_tracking(request_id)
            # 不同的延遲時間
            time.sleep(0.02 + i * 0.01)  # 20ms到110ms
            tracker.end_tracking(request_id)
        
        # 獲取統計
        stats = tracker.get_statistics()
        
        # 驗證統計數據
        assert stats.total_requests == 10
        assert stats.p50_time_ms > 0
        assert stats.p95_time_ms > 0
        assert stats.p99_time_ms > 0
        assert stats.avg_time_ms > 0
        assert stats.p50_time_ms <= stats.p95_time_ms <= stats.p99_time_ms
        
        # 驗證慢查詢統計（最後幾個請求應該超過100ms）
        assert stats.slow_query_count > 0
        assert 0 < stats.slow_query_rate <= 1.0
    
    def test_get_statistics_with_time_window(self):
        """測試時間窗口統計功能"""
        tracker = PerformanceTracker()
        
        # 生成5個請求
        for i in range(5):
            request_id = f"test_{i:03d}"
            tracker.start_tracking(request_id)
            time.sleep(0.02)
            tracker.end_tracking(request_id)
        
        # 獲取最近1小時的統計
        stats = tracker.get_statistics(time_window=timedelta(hours=1))
        assert stats.total_requests == 5
        
        # 等待一小段時間，然後獲取非常短的時間窗口統計
        time.sleep(0.1)
        stats_short = tracker.get_statistics(time_window=timedelta(milliseconds=50))
        assert stats_short.total_requests == 0  # 所有請求都在50ms之前完成
    
    def test_stage_average_times(self):
        """測試各階段平均耗時計算"""
        tracker = PerformanceTracker()
        
        # 生成多個請求，每個都有相同的階段
        for i in range(5):
            request_id = f"test_{i:03d}"
            tracker.start_tracking(request_id)
            time.sleep(0.02)
            tracker.track_stage(request_id, "feature_loading")
            time.sleep(0.03)
            tracker.track_stage(request_id, "model_inference")
            time.sleep(0.02)
            tracker.end_tracking(request_id)
        
        # 獲取統計
        stats = tracker.get_statistics()
        
        # 驗證各階段平均耗時
        assert "feature_loading" in stats.stage_avg_times
        assert "model_inference" in stats.stage_avg_times
        assert stats.stage_avg_times["feature_loading"] >= 20
        assert stats.stage_avg_times["model_inference"] >= 30
    
    def test_percentile_calculation_accuracy(self):
        """測試百分位數計算的準確性"""
        tracker = PerformanceTracker()
        
        # 生成100個請求，耗時從10ms到109ms
        for i in range(100):
            request_id = f"test_{i:03d}"
            tracker.start_tracking(request_id)
            time.sleep(0.01 + i * 0.001)  # 10ms + i*1ms
            tracker.end_tracking(request_id)
        
        stats = tracker.get_statistics()
        
        # 驗證百分位數的合理性
        assert stats.total_requests == 100
        # P50應該接近中位數（約60ms）
        assert 40 < stats.p50_time_ms < 80
        # P95應該接近95%位置（約105ms）
        assert 90 < stats.p95_time_ms < 120
        # P99應該接近99%位置（約109ms）
        assert 100 < stats.p99_time_ms < 130
    
    def test_clear_history(self):
        """測試清空歷史記錄"""
        tracker = PerformanceTracker()
        
        # 生成一些數據
        for i in range(5):
            request_id = f"test_{i:03d}"
            tracker.start_tracking(request_id)
            time.sleep(0.01)
            tracker.end_tracking(request_id)
        
        assert tracker.get_history_count() == 5
        
        # 清空歷史
        tracker.clear_history()
        
        assert tracker.get_history_count() == 0
        
        # 統計應該顯示沒有數據
        stats = tracker.get_statistics()
        assert stats.total_requests == 0
    
    def test_multiple_stages_tracking(self):
        """測試多階段追蹤的完整流程"""
        tracker = PerformanceTracker()
        request_id = "test_001"
        
        # 模擬完整的推薦流程
        tracker.start_tracking(request_id)
        time.sleep(0.02)
        tracker.track_stage(request_id, "feature_loading")
        time.sleep(0.03)
        tracker.track_stage(request_id, "model_inference")
        time.sleep(0.02)
        tracker.track_stage(request_id, "recommendation_merging")
        time.sleep(0.01)
        tracker.track_stage(request_id, "reason_generation")
        time.sleep(0.01)
        tracker.track_stage(request_id, "quality_evaluation")
        
        metrics = tracker.end_tracking(request_id)
        
        # 驗證所有階段都被記錄
        expected_stages = [
            "feature_loading",
            "model_inference", 
            "recommendation_merging",
            "reason_generation",
            "quality_evaluation"
        ]
        
        for stage in expected_stages:
            assert stage in metrics.stage_times
            assert metrics.stage_times[stage] > 0
        
        # 驗證總耗時等於各階段耗時之和（允許小誤差）
        total_stage_time = sum(metrics.stage_times.values())
        assert abs(metrics.total_time_ms - total_stage_time) < 5  # 允許5ms誤差
