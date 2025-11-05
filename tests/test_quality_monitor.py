"""
品質監控器單元測試
測試 QualityMonitor 的監控記錄、閾值檢查、告警觸發和報告生成功能
"""
import pytest
import time
from datetime import datetime, timedelta
from src.utils.quality_monitor import QualityMonitor
from src.models.enhanced_data_models import (
    ReferenceValueScore,
    PerformanceMetrics,
    MonitoringRecord,
    QualityCheckResult,
    PerformanceCheckResult,
    Alert,
    AlertLevel,
    MonitoringReport
)


class TestQualityMonitor:
    """測試 QualityMonitor 類別"""
    
    def test_record_recommendation(self):
        """測試監控記錄功能"""
        monitor = QualityMonitor()
        
        # 創建測試數據
        value_score = ReferenceValueScore(
            overall_score=65.0,
            relevance_score=70.0,
            novelty_score=35.0,
            explainability_score=85.0,
            diversity_score=60.0,
            score_breakdown={}
        )
        
        performance_metrics = PerformanceMetrics(
            request_id="test_001",
            total_time_ms=250.0,
            stage_times={
                "feature_loading": 50.0,
                "model_inference": 120.0,
                "reason_generation": 40.0,
                "quality_evaluation": 40.0
            },
            is_slow_query=False
        )
        
        # 記錄推薦
        monitor.record_recommendation(
            request_id="test_001",
            member_code="M001",
            value_score=value_score,
            performance_metrics=performance_metrics,
            recommendation_count=5,
            strategy_used="hybrid",
            is_degraded=False
        )
        
        # 驗證記錄已保存
        assert monitor.get_record_count() == 1
        
        # 獲取記錄並驗證
        records = monitor.get_records()
        assert len(records) == 1
        
        record = records[0]
        assert record.request_id == "test_001"
        assert record.member_code == "M001"
        assert record.overall_score == 65.0
        assert record.relevance_score == 70.0
        assert record.total_time_ms == 250.0
        assert record.feature_loading_ms == 50.0
        assert record.model_inference_ms == 120.0
        assert record.recommendation_count == 5
        assert record.strategy_used == "hybrid"
        assert not record.is_degraded
    
    def test_get_records_with_time_window(self):
        """測試時間窗口數據查詢"""
        monitor = QualityMonitor()
        
        # 創建測試數據
        value_score = ReferenceValueScore(
            overall_score=65.0,
            relevance_score=70.0,
            novelty_score=35.0,
            explainability_score=85.0,
            diversity_score=60.0,
            score_breakdown={}
        )
        
        performance_metrics = PerformanceMetrics(
            request_id="test_001",
            total_time_ms=250.0,
            stage_times={},
            is_slow_query=False
        )
        
        # 記錄多個推薦
        for i in range(5):
            monitor.record_recommendation(
                request_id=f"test_{i:03d}",
                member_code=f"M{i:03d}",
                value_score=value_score,
                performance_metrics=performance_metrics,
                recommendation_count=5
            )
            time.sleep(0.01)
        
        # 獲取所有記錄
        all_records = monitor.get_records()
        assert len(all_records) == 5
        
        # 獲取最近1小時的記錄
        recent_records = monitor.get_records(time_window=timedelta(hours=1))
        assert len(recent_records) == 5
        
        # 獲取非常短時間窗口的記錄（應該為空）
        old_records = monitor.get_records(time_window=timedelta(milliseconds=1))
        assert len(old_records) == 0
    
    def test_get_records_by_member(self):
        """測試按會員查詢記錄"""
        monitor = QualityMonitor()
        
        value_score = ReferenceValueScore(
            overall_score=65.0,
            relevance_score=70.0,
            novelty_score=35.0,
            explainability_score=85.0,
            diversity_score=60.0,
            score_breakdown={}
        )
        
        performance_metrics = PerformanceMetrics(
            request_id="test_001",
            total_time_ms=250.0,
            stage_times={},
            is_slow_query=False
        )
        
        # 記錄不同會員的推薦
        for i in range(3):
            monitor.record_recommendation(
                request_id=f"test_M001_{i}",
                member_code="M001",
                value_score=value_score,
                performance_metrics=performance_metrics,
                recommendation_count=5
            )
        
        for i in range(2):
            monitor.record_recommendation(
                request_id=f"test_M002_{i}",
                member_code="M002",
                value_score=value_score,
                performance_metrics=performance_metrics,
                recommendation_count=5
            )
        
        # 查詢特定會員的記錄
        m001_records = monitor.get_records(member_code="M001")
        assert len(m001_records) == 3
        assert all(r.member_code == "M001" for r in m001_records)
        
        m002_records = monitor.get_records(member_code="M002")
        assert len(m002_records) == 2
        assert all(r.member_code == "M002" for r in m002_records)

    
    def test_check_quality_threshold_pass(self):
        """測試品質檢查通過的情況"""
        monitor = QualityMonitor()
        
        # 創建高品質分數
        value_score = ReferenceValueScore(
            overall_score=75.0,
            relevance_score=80.0,
            novelty_score=40.0,
            explainability_score=90.0,
            diversity_score=70.0,
            score_breakdown={}
        )
        
        # 檢查品質
        result = monitor.check_quality_threshold(value_score)
        
        # 驗證通過檢查
        assert isinstance(result, QualityCheckResult)
        assert result.passed
        assert result.overall_score == 75.0
        assert len(result.failed_metrics) == 0
        assert len(result.warnings) == 0
    
    def test_check_quality_threshold_warning(self):
        """測試品質檢查警告的情況"""
        monitor = QualityMonitor()
        
        # 創建接近警告線的分數（低於警告線但高於嚴重線）
        value_score = ReferenceValueScore(
            overall_score=48.0,  # 低於警告線(50)但高於嚴重線(40)
            relevance_score=58.0,  # 低於警告線(60)但高於嚴重線(50)
            novelty_score=18.0,  # 低於警告線(20)但高於嚴重線(15)
            explainability_score=68.0,  # 低於警告線(70)但高於嚴重線(60)
            diversity_score=48.0,  # 低於警告線(50)但高於嚴重線(40)
            score_breakdown={}
        )
        
        # 檢查品質
        result = monitor.check_quality_threshold(value_score)
        
        # 驗證有警告但通過檢查
        assert result.passed
        assert len(result.failed_metrics) == 0
        assert len(result.warnings) > 0
    
    def test_check_quality_threshold_fail(self):
        """測試品質檢查失敗的情況"""
        monitor = QualityMonitor()
        
        # 創建低品質分數
        value_score = ReferenceValueScore(
            overall_score=35.0,  # 低於嚴重線(40)
            relevance_score=45.0,  # 低於嚴重線(50)
            novelty_score=10.0,  # 低於嚴重線(15)
            explainability_score=55.0,  # 低於嚴重線(60)
            diversity_score=35.0,  # 低於嚴重線(40)
            score_breakdown={}
        )
        
        # 檢查品質
        result = monitor.check_quality_threshold(value_score)
        
        # 驗證未通過檢查
        assert not result.passed
        assert len(result.failed_metrics) > 0
        assert "綜合分數過低" in result.failed_metrics[0]
    
    def test_check_performance_threshold_pass(self):
        """測試性能檢查通過的情況"""
        monitor = QualityMonitor()
        
        # 創建良好的性能指標
        performance_metrics = PerformanceMetrics(
            request_id="test_001",
            total_time_ms=180.0,  # 低於P50閾值(200ms)
            stage_times={
                "feature_loading": 40.0,  # 低於閾值(100ms)
                "model_inference": 80.0,  # 低於閾值(200ms)
            },
            is_slow_query=False
        )
        
        # 檢查性能
        result = monitor.check_performance_threshold(performance_metrics)
        
        # 驗證通過檢查
        assert isinstance(result, PerformanceCheckResult)
        assert result.passed
        assert result.total_time_ms == 180.0
        assert len(result.failed_metrics) == 0
        assert len(result.warnings) == 0
    
    def test_check_performance_threshold_warning(self):
        """測試性能檢查警告的情況"""
        monitor = QualityMonitor()
        
        # 創建接近閾值的性能指標
        performance_metrics = PerformanceMetrics(
            request_id="test_001",
            total_time_ms=550.0,  # 超過P95閾值(500ms)但低於P99(1000ms)
            stage_times={
                "feature_loading": 110.0,  # 超過閾值(100ms)
                "model_inference": 220.0,  # 超過閾值(200ms)
            },
            is_slow_query=False
        )
        
        # 檢查性能
        result = monitor.check_performance_threshold(performance_metrics)
        
        # 驗證有警告但通過檢查
        assert result.passed
        assert len(result.failed_metrics) == 0
        assert len(result.warnings) > 0
    
    def test_check_performance_threshold_fail(self):
        """測試性能檢查失敗的情況"""
        monitor = QualityMonitor()
        
        # 創建超過閾值的性能指標
        performance_metrics = PerformanceMetrics(
            request_id="test_001",
            total_time_ms=1200.0,  # 超過P99閾值(1000ms)
            stage_times={
                "feature_loading": 150.0,
                "model_inference": 800.0,
            },
            is_slow_query=True
        )
        
        # 檢查性能
        result = monitor.check_performance_threshold(performance_metrics)
        
        # 驗證未通過檢查
        assert not result.passed
        assert len(result.failed_metrics) > 0
        assert "總反應時間過長" in result.failed_metrics[0]
    
    def test_trigger_alerts_quality(self):
        """測試品質告警觸發"""
        monitor = QualityMonitor()
        
        # 創建低品質分數
        value_score = ReferenceValueScore(
            overall_score=35.0,  # 觸發嚴重告警
            relevance_score=55.0,  # 觸發警告
            novelty_score=30.0,
            explainability_score=80.0,
            diversity_score=60.0,
            score_breakdown={}
        )
        
        performance_metrics = PerformanceMetrics(
            request_id="test_001",
            total_time_ms=200.0,
            stage_times={},
            is_slow_query=False
        )
        
        # 觸發告警
        alerts = monitor.trigger_alerts(value_score, performance_metrics)
        
        # 驗證告警
        assert len(alerts) > 0
        assert monitor.get_alert_count() > 0
        
        # 檢查是否有嚴重告警
        critical_alerts = [a for a in alerts if a.level == AlertLevel.CRITICAL]
        assert len(critical_alerts) > 0
        
        # 檢查是否有警告
        warning_alerts = [a for a in alerts if a.level == AlertLevel.WARNING]
        assert len(warning_alerts) > 0
    
    def test_trigger_alerts_performance(self):
        """測試性能告警觸發"""
        monitor = QualityMonitor()
        
        # 創建正常品質但性能差的指標
        value_score = ReferenceValueScore(
            overall_score=65.0,
            relevance_score=70.0,
            novelty_score=35.0,
            explainability_score=85.0,
            diversity_score=60.0,
            score_breakdown={}
        )
        
        performance_metrics = PerformanceMetrics(
            request_id="test_001",
            total_time_ms=1200.0,  # 觸發嚴重告警
            stage_times={
                "feature_loading": 110.0,  # 觸發警告
                "model_inference": 900.0,
            },
            is_slow_query=True
        )
        
        # 觸發告警
        alerts = monitor.trigger_alerts(value_score, performance_metrics)
        
        # 驗證告警
        assert len(alerts) > 0
        
        # 檢查性能相關告警
        performance_alerts = [a for a in alerts if "時間" in a.message]
        assert len(performance_alerts) > 0
    
    def test_get_alerts_with_filters(self):
        """測試告警查詢過濾功能"""
        monitor = QualityMonitor()
        
        # 觸發多個告警
        value_score_low = ReferenceValueScore(
            overall_score=35.0,
            relevance_score=45.0,
            novelty_score=10.0,
            explainability_score=55.0,
            diversity_score=35.0,
            score_breakdown={}
        )
        
        performance_metrics = PerformanceMetrics(
            request_id="test_001",
            total_time_ms=200.0,
            stage_times={},
            is_slow_query=False
        )
        
        monitor.trigger_alerts(value_score_low, performance_metrics)
        
        # 獲取所有告警
        all_alerts = monitor.get_alerts()
        assert len(all_alerts) > 0
        
        # 獲取嚴重告警
        critical_alerts = monitor.get_alerts(level=AlertLevel.CRITICAL)
        assert len(critical_alerts) > 0
        assert all(a.level == AlertLevel.CRITICAL for a in critical_alerts)
        
        # 獲取最近1小時的告警
        recent_alerts = monitor.get_alerts(time_window=timedelta(hours=1))
        assert len(recent_alerts) == len(all_alerts)

    
    def test_generate_hourly_report_empty(self):
        """測試空數據的小時報告生成"""
        monitor = QualityMonitor()
        
        # 生成報告
        report = monitor.generate_hourly_report()
        
        # 驗證報告
        assert isinstance(report, MonitoringReport)
        assert report.report_type == "hourly"
        assert report.total_recommendations == 0
        assert report.unique_members == 0
        assert report.avg_overall_score == 0.0
    
    def test_generate_daily_report_empty(self):
        """測試空數據的日報生成"""
        monitor = QualityMonitor()
        
        # 生成報告
        report = monitor.generate_daily_report()
        
        # 驗證報告
        assert isinstance(report, MonitoringReport)
        assert report.report_type == "daily"
        assert report.total_recommendations == 0
    
    def test_generate_report_with_data(self):
        """測試有數據的報告生成"""
        monitor = QualityMonitor()
        
        # 創建測試數據
        value_scores = [
            ReferenceValueScore(
                overall_score=65.0 + i * 2,
                relevance_score=70.0 + i,
                novelty_score=35.0 + i,
                explainability_score=85.0 - i,
                diversity_score=60.0 + i,
                score_breakdown={}
            )
            for i in range(10)
        ]
        
        performance_metrics_list = [
            PerformanceMetrics(
                request_id=f"test_{i:03d}",
                total_time_ms=200.0 + i * 20,
                stage_times={
                    "feature_loading": 50.0 + i * 5,
                    "model_inference": 100.0 + i * 10,
                },
                is_slow_query=False
            )
            for i in range(10)
        ]
        
        # 記錄推薦
        for i in range(10):
            monitor.record_recommendation(
                request_id=f"test_{i:03d}",
                member_code=f"M{i % 3:03d}",  # 3個不同會員
                value_score=value_scores[i],
                performance_metrics=performance_metrics_list[i],
                recommendation_count=5,
                strategy_used="hybrid",
                is_degraded=False
            )
        
        # 生成報告
        report = monitor.generate_hourly_report()
        
        # 驗證推薦量統計
        assert report.total_recommendations == 10
        assert report.unique_members == 3
        assert report.avg_recommendations_per_member > 0
        
        # 驗證品質統計
        assert report.avg_overall_score > 0
        assert report.avg_relevance_score > 0
        assert report.avg_novelty_score > 0
        assert report.avg_explainability_score > 0
        assert report.avg_diversity_score > 0
        
        # 驗證性能統計
        assert report.avg_response_time_ms > 0
        assert report.p50_response_time_ms > 0
        assert report.p95_response_time_ms > 0
        assert report.p99_response_time_ms > 0
        assert report.p50_response_time_ms <= report.p95_response_time_ms <= report.p99_response_time_ms
        
        # 驗證異常統計
        assert report.total_alerts >= 0
        assert report.critical_alerts >= 0
        assert report.warning_alerts >= 0
        assert report.degradation_count == 0
        
        # 驗證趨勢分析
        assert report.score_trend in ["improving", "stable", "declining"]
        assert report.performance_trend in ["improving", "stable", "declining"]
    
    def test_report_with_alerts(self):
        """測試包含告警的報告生成"""
        monitor = QualityMonitor()
        
        # 創建低品質數據並觸發告警
        for i in range(5):
            value_score = ReferenceValueScore(
                overall_score=35.0,  # 觸發嚴重告警
                relevance_score=45.0,
                novelty_score=10.0,
                explainability_score=55.0,
                diversity_score=35.0,
                score_breakdown={}
            )
            
            performance_metrics = PerformanceMetrics(
                request_id=f"test_{i:03d}",
                total_time_ms=1200.0,  # 觸發性能告警
                stage_times={},
                is_slow_query=True
            )
            
            monitor.record_recommendation(
                request_id=f"test_{i:03d}",
                member_code=f"M{i:03d}",
                value_score=value_score,
                performance_metrics=performance_metrics,
                recommendation_count=5,
                strategy_used="hybrid",
                is_degraded=True
            )
            
            monitor.trigger_alerts(value_score, performance_metrics)
        
        # 生成報告
        report = monitor.generate_hourly_report()
        
        # 驗證告警統計
        assert report.total_alerts > 0
        assert report.critical_alerts > 0
        assert report.degradation_count == 5
        
        # 驗證改進建議
        assert len(report.recommendations_for_improvement) > 0
    
    def test_score_trend_analysis(self):
        """測試分數趨勢分析"""
        monitor = QualityMonitor()
        
        # 創建遞增的分數趨勢
        for i in range(20):
            value_score = ReferenceValueScore(
                overall_score=50.0 + i * 2,  # 從50增加到88
                relevance_score=60.0 + i,
                novelty_score=30.0 + i,
                explainability_score=70.0 + i,
                diversity_score=50.0 + i,
                score_breakdown={}
            )
            
            performance_metrics = PerformanceMetrics(
                request_id=f"test_{i:03d}",
                total_time_ms=200.0,
                stage_times={},
                is_slow_query=False
            )
            
            monitor.record_recommendation(
                request_id=f"test_{i:03d}",
                member_code=f"M{i:03d}",
                value_score=value_score,
                performance_metrics=performance_metrics,
                recommendation_count=5
            )
        
        # 生成報告
        report = monitor.generate_hourly_report()
        
        # 驗證趨勢為改善
        assert report.score_trend == "improving"
    
    def test_performance_trend_analysis(self):
        """測試性能趨勢分析"""
        monitor = QualityMonitor()
        
        # 創建遞減的反應時間趨勢（性能改善）
        for i in range(20):
            value_score = ReferenceValueScore(
                overall_score=65.0,
                relevance_score=70.0,
                novelty_score=35.0,
                explainability_score=85.0,
                diversity_score=60.0,
                score_breakdown={}
            )
            
            performance_metrics = PerformanceMetrics(
                request_id=f"test_{i:03d}",
                total_time_ms=400.0 - i * 10,  # 從400ms減少到210ms
                stage_times={},
                is_slow_query=False
            )
            
            monitor.record_recommendation(
                request_id=f"test_{i:03d}",
                member_code=f"M{i:03d}",
                value_score=value_score,
                performance_metrics=performance_metrics,
                recommendation_count=5
            )
        
        # 生成報告
        report = monitor.generate_hourly_report()
        
        # 驗證趨勢為改善
        assert report.performance_trend == "improving"
    
    def test_improvement_recommendations(self):
        """測試改進建議生成"""
        monitor = QualityMonitor()
        
        # 創建各維度都有問題的數據
        value_score = ReferenceValueScore(
            overall_score=45.0,  # 低於目標值(60)
            relevance_score=55.0,  # 低於目標值(70)
            novelty_score=20.0,  # 低於目標值(30)
            explainability_score=65.0,  # 低於目標值(80)
            diversity_score=45.0,  # 低於目標值(60)
            score_breakdown={}
        )
        
        performance_metrics = PerformanceMetrics(
            request_id="test_001",
            total_time_ms=600.0,  # 超過P95閾值(500ms)
            stage_times={},
            is_slow_query=False
        )
        
        monitor.record_recommendation(
            request_id="test_001",
            member_code="M001",
            value_score=value_score,
            performance_metrics=performance_metrics,
            recommendation_count=5,
            strategy_used="hybrid",
            is_degraded=False
        )
        
        # 觸發告警
        monitor.trigger_alerts(value_score, performance_metrics)
        
        # 生成報告
        report = monitor.generate_hourly_report()
        
        # 驗證改進建議
        recommendations = report.recommendations_for_improvement
        assert len(recommendations) > 0
        
        # 檢查是否包含各維度的建議
        recommendation_text = " ".join(recommendations)
        assert "綜合可參考價值分數" in recommendation_text or "相關性" in recommendation_text
    
    def test_clear_history(self):
        """測試清空歷史記錄"""
        monitor = QualityMonitor()
        
        # 創建一些數據（包含低品質分數以觸發告警）
        value_score = ReferenceValueScore(
            overall_score=35.0,  # 觸發告警
            relevance_score=45.0,
            novelty_score=10.0,
            explainability_score=55.0,
            diversity_score=35.0,
            score_breakdown={}
        )
        
        performance_metrics = PerformanceMetrics(
            request_id="test_001",
            total_time_ms=200.0,
            stage_times={},
            is_slow_query=False
        )
        
        for i in range(5):
            monitor.record_recommendation(
                request_id=f"test_{i:03d}",
                member_code=f"M{i:03d}",
                value_score=value_score,
                performance_metrics=performance_metrics,
                recommendation_count=5
            )
        
        # 觸發一些告警
        monitor.trigger_alerts(value_score, performance_metrics)
        
        assert monitor.get_record_count() == 5
        assert monitor.get_alert_count() > 0
        
        # 清空歷史
        monitor.clear_history()
        
        assert monitor.get_record_count() == 0
        assert monitor.get_alert_count() == 0
        
        # 報告應該顯示沒有數據
        report = monitor.generate_hourly_report()
        assert report.total_recommendations == 0
