"""
端到端整合測試
測試完整推薦流程（從請求到回應）、性能追蹤、品質監控和降級機制
"""
import pytest
import sys
from pathlib import Path
import time
from datetime import timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.enhanced_recommendation_engine import EnhancedRecommendationEngine
from src.models.data_models import MemberInfo
from src.models.enhanced_data_models import QualityLevel, AlertLevel
from src.utils.quality_monitor import QualityMonitor


class TestEndToEndIntegration:
    """端到端整合測試類別"""
    
    @pytest.fixture
    def engine(self):
        """創建測試用的增強推薦引擎"""
        try:
            engine = EnhancedRecommendationEngine()
            return engine
        except FileNotFoundError:
            pytest.skip("模型檔案不存在，跳過測試")
    
    @pytest.fixture
    def test_member(self):
        """創建測試會員"""
        return MemberInfo(
            member_code="CU000001",
            phone="0937024682",
            total_consumption=17400.0,
            accumulated_bonus=500.0,
            recent_purchases=["30463", "31033"]
        )
    
    @pytest.fixture
    def new_member(self):
        """創建新會員（無購買歷史）"""
        return MemberInfo(
            member_code="CU999999",
            phone="0900000000",
            total_consumption=0.0,
            accumulated_bonus=0.0,
            recent_purchases=[]
        )
    
    def test_complete_recommendation_flow(self, engine, test_member):
        """測試完整推薦流程（從請求到回應）"""
        # 執行推薦
        response = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='hybrid'
        )
        
        # 1. 驗證推薦結果
        assert response is not None
        assert len(response.recommendations) > 0
        assert len(response.recommendations) <= 5
        
        # 2. 驗證每個推薦的完整性
        for rec in response.recommendations:
            assert rec.product_id is not None
            assert rec.product_name is not None
            assert 0 <= rec.confidence_score <= 100
            assert rec.explanation is not None
            assert len(rec.explanation) > 0
            assert rec.rank > 0
        
        # 3. 驗證性能追蹤
        assert response.performance_metrics is not None
        assert response.performance_metrics.total_time_ms > 0
        assert len(response.performance_metrics.stage_times) > 0
        
        # 4. 驗證可參考價值評估
        assert response.reference_value_score is not None
        assert 0 <= response.reference_value_score.overall_score <= 100
        assert 0 <= response.reference_value_score.relevance_score <= 100
        assert 0 <= response.reference_value_score.novelty_score <= 100
        assert 0 <= response.reference_value_score.explainability_score <= 100
        assert 0 <= response.reference_value_score.diversity_score <= 100
        
        # 5. 驗證品質等級
        assert response.quality_level in QualityLevel
        
        # 6. 驗證元資料
        assert response.member_code == test_member.member_code
        assert response.strategy_used == 'hybrid'
        assert response.model_version is not None
        assert response.timestamp is not None
    
    def test_performance_tracking_integration(self, engine, test_member):
        """測試性能追蹤功能整合"""
        # 執行推薦
        response = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='hybrid'
        )
        
        # 驗證性能指標
        metrics = response.performance_metrics
        
        # 1. 驗證總耗時合理
        assert metrics.total_time_ms > 0
        assert metrics.total_time_ms < 10000  # 應該在10秒內
        
        # 2. 驗證關鍵階段都被追蹤
        expected_stages = [
            'feature_loading',
            'model_inference',
            'reason_generation',
            'quality_evaluation'
        ]
        
        for stage in expected_stages:
            if stage in metrics.stage_times:
                assert metrics.stage_times[stage] >= 0
        
        # 3. 驗證慢查詢檢測
        assert isinstance(metrics.is_slow_query, bool)
        
        # 4. 獲取性能統計
        stats = engine.performance_tracker.get_statistics(
            time_window=timedelta(minutes=5)
        )
        assert stats.total_requests >= 1
        assert stats.avg_time_ms > 0
    
    def test_quality_monitoring_integration(self, engine, test_member):
        """測試品質監控功能整合"""
        # 創建品質監控器
        monitor = QualityMonitor()
        
        # 執行推薦
        response = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='hybrid'
        )
        
        # 記錄到監控器
        monitor.record_recommendation(
            request_id=response.performance_metrics.request_id,
            member_code=response.member_code,
            value_score=response.reference_value_score,
            performance_metrics=response.performance_metrics,
            recommendation_count=len(response.recommendations),
            strategy_used=response.strategy_used,
            is_degraded=response.is_degraded
        )
        
        # 1. 驗證記錄已保存
        assert monitor.get_record_count() == 1
        
        # 2. 檢查品質閾值
        quality_check = monitor.check_quality_threshold(
            response.reference_value_score
        )
        assert quality_check is not None
        assert isinstance(quality_check.passed, bool)
        
        # 3. 檢查性能閾值
        performance_check = monitor.check_performance_threshold(
            response.performance_metrics
        )
        assert performance_check is not None
        assert isinstance(performance_check.passed, bool)
        
        # 4. 觸發告警檢查
        alerts = monitor.trigger_alerts(
            response.reference_value_score,
            response.performance_metrics
        )
        assert isinstance(alerts, list)
        
        # 5. 生成報告
        report = monitor.generate_hourly_report()
        assert report is not None
        assert report.total_recommendations == 1
        assert report.unique_members == 1
    
    def test_degradation_mechanism(self, engine):
        """測試降級機制"""
        # 創建一個可能觸發降級的會員（新會員）
        new_member = MemberInfo(
            member_code="CU999999",
            phone="0900000000",
            total_consumption=0.0,
            accumulated_bonus=0.0,
            recent_purchases=[]
        )
        
        # 執行推薦
        response = engine.recommend(
            member_info=new_member,
            n=5,
            strategy='hybrid'
        )
        
        # 驗證推薦仍然能生成
        assert response is not None
        assert len(response.recommendations) > 0
        
        # 檢查是否使用降級策略
        if response.is_degraded:
            # 如果降級，驗證降級標記
            assert response.is_degraded is True
            # 降級推薦應該有簡單的理由
            for rec in response.recommendations:
                assert rec.explanation is not None
        else:
            # 如果沒有降級，驗證正常流程
            assert response.is_degraded is False
            assert response.reference_value_score is not None
    
    def test_multiple_requests_flow(self, engine, test_member):
        """測試多個請求的完整流程"""
        responses = []
        
        # 執行多個推薦請求
        for i in range(3):
            response = engine.recommend(
                member_info=test_member,
                n=5,
                strategy='hybrid'
            )
            responses.append(response)
            time.sleep(0.1)  # 短暫延遲
        
        # 驗證所有請求都成功
        assert len(responses) == 3
        
        for response in responses:
            assert response is not None
            assert len(response.recommendations) > 0
            assert response.performance_metrics is not None
            assert response.reference_value_score is not None
        
        # 驗證性能統計累積
        stats = engine.performance_tracker.get_statistics(
            time_window=timedelta(minutes=5)
        )
        assert stats.total_requests >= 3
    
    def test_different_strategies(self, engine, test_member):
        """測試不同推薦策略"""
        strategies = ['hybrid', 'ml_only']
        
        for strategy in strategies:
            response = engine.recommend(
                member_info=test_member,
                n=5,
                strategy=strategy
            )
            
            # 驗證策略正確應用
            assert response.strategy_used == strategy
            assert len(response.recommendations) > 0
            
            # 驗證性能和品質評估都執行
            assert response.performance_metrics is not None
            assert response.reference_value_score is not None
    
    def test_recommendation_consistency(self, engine, test_member):
        """測試推薦一致性"""
        # 執行兩次推薦
        response1 = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='ml_only'
        )
        
        response2 = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='ml_only'
        )
        
        # 驗證推薦結果的一致性（相同策略應該產生相似結果）
        products1 = set(rec.product_id for rec in response1.recommendations)
        products2 = set(rec.product_id for rec in response2.recommendations)
        
        # 至少應該有一些重疊
        overlap = products1.intersection(products2)
        assert len(overlap) > 0
    
    def test_error_handling(self, engine):
        """測試錯誤處理"""
        # 測試無效會員
        invalid_member = MemberInfo(
            member_code="INVALID",
            phone="",
            total_consumption=0.0,
            accumulated_bonus=0.0,
            recent_purchases=[]
        )
        
        # 應該仍然能生成推薦（使用降級策略）
        response = engine.recommend(
            member_info=invalid_member,
            n=5,
            strategy='hybrid'
        )
        
        assert response is not None
        # 可能使用降級策略或返回空列表
        assert isinstance(response.recommendations, list)
    
    def test_response_serialization(self, engine, test_member):
        """測試回應序列化"""
        # 執行推薦
        response = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='hybrid'
        )
        
        # 轉換為字典
        response_dict = response.to_dict()
        
        # 驗證字典結構完整
        required_keys = [
            'member_code',
            'recommendations',
            'reference_value_score',
            'performance_metrics',
            'quality_level',
            'strategy_used',
            'model_version',
            'timestamp',
            'is_degraded'
        ]
        
        for key in required_keys:
            assert key in response_dict
        
        # 驗證推薦列表可序列化
        assert isinstance(response_dict['recommendations'], list)
        if len(response_dict['recommendations']) > 0:
            first_rec = response_dict['recommendations'][0]
            assert 'product_id' in first_rec
            assert 'product_name' in first_rec
            assert 'confidence_score' in first_rec
            assert 'explanation' in first_rec
    
    def test_health_check(self, engine):
        """測試健康檢查"""
        health = engine.health_check()
        
        # 驗證健康檢查結果
        assert 'status' in health
        assert 'ml_model_loaded' in health
        assert 'performance_tracker_active' in health
        assert 'value_evaluator_active' in health
        assert 'reason_generator_active' in health
        
        # 至少模型應該載入
        assert health['ml_model_loaded'] is True
    
    def test_model_info(self, engine):
        """測試模型資訊"""
        info = engine.get_model_info()
        
        # 驗證模型資訊
        assert 'model_version' in info
        assert 'strategy_weights' in info
        assert 'total_products' in info
        assert 'total_members' in info
        
        # 驗證策略權重
        weights = info['strategy_weights']
        assert isinstance(weights, dict)
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.01


class TestIntegrationWithMonitoring:
    """測試與監控系統的整合"""
    
    @pytest.fixture
    def engine(self):
        """創建測試用的增強推薦引擎"""
        try:
            engine = EnhancedRecommendationEngine()
            return engine
        except FileNotFoundError:
            pytest.skip("模型檔案不存在，跳過測試")
    
    @pytest.fixture
    def monitor(self):
        """創建品質監控器"""
        return QualityMonitor()
    
    @pytest.fixture
    def test_member(self):
        """創建測試會員"""
        return MemberInfo(
            member_code="CU000001",
            phone="0937024682",
            total_consumption=17400.0,
            accumulated_bonus=500.0,
            recent_purchases=["30463", "31033"]
        )
    
    def test_monitoring_workflow(self, engine, monitor, test_member):
        """測試完整監控工作流程"""
        # 1. 執行推薦
        response = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='hybrid'
        )
        
        # 2. 記錄到監控器
        monitor.record_recommendation(
            request_id=response.performance_metrics.request_id,
            member_code=response.member_code,
            value_score=response.reference_value_score,
            performance_metrics=response.performance_metrics,
            recommendation_count=len(response.recommendations),
            strategy_used=response.strategy_used,
            is_degraded=response.is_degraded
        )
        
        # 3. 檢查品質和性能
        quality_check = monitor.check_quality_threshold(
            response.reference_value_score
        )
        performance_check = monitor.check_performance_threshold(
            response.performance_metrics
        )
        
        # 4. 觸發告警（如果需要）
        alerts = monitor.trigger_alerts(
            response.reference_value_score,
            response.performance_metrics
        )
        
        # 5. 生成報告
        report = monitor.generate_hourly_report()
        
        # 驗證工作流程完整性
        assert monitor.get_record_count() >= 1
        assert quality_check is not None
        assert performance_check is not None
        assert isinstance(alerts, list)
        assert report is not None
        assert report.total_recommendations >= 1
    
    def test_alert_triggering(self, engine, monitor):
        """測試告警觸發機制"""
        # 創建多個會員並執行推薦
        members = [
            MemberInfo(
                member_code=f"CU{i:06d}",
                phone=f"09{i:08d}",
                total_consumption=1000.0 * i,
                accumulated_bonus=100.0 * i,
                recent_purchases=[]
            )
            for i in range(1, 6)
        ]
        
        alert_count_before = monitor.get_alert_count()
        
        for member in members:
            response = engine.recommend(
                member_info=member,
                n=5,
                strategy='hybrid'
            )
            
            # 記錄並檢查告警
            monitor.record_recommendation(
                request_id=response.performance_metrics.request_id,
                member_code=response.member_code,
                value_score=response.reference_value_score,
                performance_metrics=response.performance_metrics,
                recommendation_count=len(response.recommendations),
                strategy_used=response.strategy_used,
                is_degraded=response.is_degraded
            )
            
            monitor.trigger_alerts(
                response.reference_value_score,
                response.performance_metrics
            )
        
        # 驗證告警系統運作
        alert_count_after = monitor.get_alert_count()
        # 告警數量可能增加（取決於品質）
        assert alert_count_after >= alert_count_before
    
    def test_report_generation(self, engine, monitor, test_member):
        """測試報告生成"""
        # 執行多個推薦
        for i in range(5):
            response = engine.recommend(
                member_info=test_member,
                n=5,
                strategy='hybrid'
            )
            
            monitor.record_recommendation(
                request_id=response.performance_metrics.request_id,
                member_code=response.member_code,
                value_score=response.reference_value_score,
                performance_metrics=response.performance_metrics,
                recommendation_count=len(response.recommendations),
                strategy_used=response.strategy_used,
                is_degraded=response.is_degraded
            )
            
            time.sleep(0.05)
        
        # 生成小時報告
        hourly_report = monitor.generate_hourly_report()
        
        # 驗證報告內容
        assert hourly_report.report_type == "hourly"
        assert hourly_report.total_recommendations >= 5
        assert hourly_report.unique_members >= 1
        assert hourly_report.avg_overall_score > 0
        assert hourly_report.avg_response_time_ms > 0
        
        # 生成日報
        daily_report = monitor.generate_daily_report()
        
        # 驗證日報內容
        assert daily_report.report_type == "daily"
        assert daily_report.total_recommendations >= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
