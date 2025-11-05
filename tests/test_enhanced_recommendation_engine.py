"""
增強推薦引擎整合測試
測試完整推薦流程、性能追蹤、價值評估、混合推薦策略
"""
import pytest
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.enhanced_recommendation_engine import (
    EnhancedRecommendationEngine,
    EnhancedRecommendationResponse
)
from src.models.data_models import MemberInfo, RecommendationSource
from src.models.enhanced_data_models import QualityLevel


class TestEnhancedRecommendationEngine:
    """增強推薦引擎測試類別"""
    
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
    
    def test_engine_initialization(self, engine):
        """測試引擎初始化"""
        assert engine is not None
        assert engine.performance_tracker is not None
        assert engine.value_evaluator is not None
        assert engine.reason_generator is not None
    
    def test_health_check(self, engine):
        """測試健康檢查"""
        health = engine.health_check()
        
        assert 'status' in health
        assert 'ml_model_loaded' in health
        assert 'performance_tracker_active' in health
        assert 'value_evaluator_active' in health
        assert 'reason_generator_active' in health
        
        # 至少 ML 模型應該載入
        assert health['ml_model_loaded'] is True
    
    def test_get_model_info(self, engine):
        """測試獲取模型資訊"""
        info = engine.get_model_info()
        
        assert 'model_version' in info
        assert 'strategy_weights' in info
        assert 'total_products' in info
        assert 'total_members' in info
        
        # 檢查策略權重總和為 1.0
        weights = info['strategy_weights']
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.01
    
    def test_hybrid_recommendation_flow(self, engine, test_member):
        """測試完整混合推薦流程"""
        # 生成推薦
        response = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='hybrid'
        )
        
        # 驗證回應類型
        assert isinstance(response, EnhancedRecommendationResponse)
        
        # 驗證推薦列表
        assert len(response.recommendations) > 0
        assert len(response.recommendations) <= 5
        
        # 驗證每個推薦
        for rec in response.recommendations:
            assert rec.product_id is not None
            assert rec.product_name is not None
            assert 0 <= rec.confidence_score <= 100
            assert rec.explanation is not None
            assert len(rec.explanation) > 0
            assert rec.rank > 0
            assert rec.source in RecommendationSource
        
        # 驗證排名連續
        ranks = [rec.rank for rec in response.recommendations]
        assert ranks == list(range(1, len(response.recommendations) + 1))
    
    def test_performance_tracking(self, engine, test_member):
        """測試性能追蹤功能"""
        response = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='hybrid'
        )
        
        # 驗證性能指標存在
        assert response.performance_metrics is not None
        
        # 驗證總耗時
        assert response.performance_metrics.total_time_ms > 0
        assert response.performance_metrics.total_time_ms < 10000  # 應該在 10 秒內
        
        # 驗證階段耗時
        stage_times = response.performance_metrics.stage_times
        assert len(stage_times) > 0
        
        # 檢查關鍵階段
        expected_stages = [
            'feature_loading',
            'model_inference',
            'reason_generation',
            'quality_evaluation'
        ]
        
        for stage in expected_stages:
            if stage in stage_times:
                # 階段耗時應該是非負數（可能為 0 如果執行非常快）
                assert stage_times[stage] >= 0
        
        # 驗證慢查詢標記
        assert isinstance(response.performance_metrics.is_slow_query, bool)
    
    def test_reference_value_evaluation(self, engine, test_member):
        """測試可參考價值評估功能"""
        response = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='hybrid'
        )
        
        # 驗證可參考價值分數存在
        assert response.reference_value_score is not None
        
        # 驗證綜合分數
        score = response.reference_value_score
        assert 0 <= score.overall_score <= 100
        
        # 驗證各維度分數
        assert 0 <= score.relevance_score <= 100
        assert 0 <= score.novelty_score <= 100
        assert 0 <= score.explainability_score <= 100
        assert 0 <= score.diversity_score <= 100
        
        # 驗證分數拆解
        assert score.score_breakdown is not None
        assert 'relevance' in score.score_breakdown
        assert 'novelty' in score.score_breakdown
        assert 'explainability' in score.score_breakdown
        assert 'diversity' in score.score_breakdown
        
        # 驗證加權計算
        expected_overall = (
            score.relevance_score * 0.40 +
            score.novelty_score * 0.25 +
            score.explainability_score * 0.20 +
            score.diversity_score * 0.15
        )
        assert abs(score.overall_score - expected_overall) < 0.1
    
    def test_quality_level_determination(self, engine, test_member):
        """測試品質等級判定"""
        response = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='hybrid'
        )
        
        # 驗證品質等級
        assert response.quality_level in QualityLevel
        
        # 驗證品質等級與分數的對應關係
        score = response.reference_value_score.overall_score
        
        if score >= 80:
            assert response.quality_level == QualityLevel.EXCELLENT
        elif score >= 60:
            assert response.quality_level == QualityLevel.GOOD
        elif score >= 40:
            assert response.quality_level == QualityLevel.ACCEPTABLE
        else:
            assert response.quality_level == QualityLevel.POOR
    
    def test_ml_only_strategy(self, engine, test_member):
        """測試純 ML 推薦策略"""
        response = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='ml_only'
        )
        
        assert response is not None
        assert response.strategy_used == 'ml_only'
        
        # 所有推薦應該來自 ML 模型
        for rec in response.recommendations:
            assert rec.source == RecommendationSource.ML_MODEL
    
    def test_hybrid_strategy_diversity(self, engine, test_member):
        """測試混合策略的多樣性"""
        response = engine.recommend(
            member_info=test_member,
            n=10,
            strategy='hybrid'
        )
        
        assert response is not None
        assert response.strategy_used == 'hybrid'
        
        # 統計不同來源的推薦數量
        sources = [rec.source for rec in response.recommendations]
        unique_sources = set(sources)
        
        # 混合策略應該包含多種來源（如果模型都可用）
        # 至少應該有 ML 模型的推薦
        assert RecommendationSource.ML_MODEL in unique_sources or \
               RecommendationSource.POPULARITY in unique_sources
    
    def test_recommendation_deduplication(self, engine, test_member):
        """測試推薦去重"""
        response = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='hybrid'
        )
        
        # 檢查是否有重複的產品 ID
        product_ids = [rec.product_id for rec in response.recommendations]
        unique_product_ids = set(product_ids)
        
        assert len(product_ids) == len(unique_product_ids), "推薦列表中存在重複產品"
    
    def test_recommendation_sorting(self, engine, test_member):
        """測試推薦排序"""
        response = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='hybrid'
        )
        
        # 檢查推薦是否按信心分數降序排列
        confidence_scores = [rec.confidence_score for rec in response.recommendations]
        
        for i in range(len(confidence_scores) - 1):
            assert confidence_scores[i] >= confidence_scores[i + 1], \
                "推薦未按信心分數降序排列"
    
    def test_response_to_dict(self, engine, test_member):
        """測試回應轉換為字典"""
        response = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='hybrid'
        )
        
        # 轉換為字典
        response_dict = response.to_dict()
        
        # 驗證字典結構
        assert 'member_code' in response_dict
        assert 'recommendations' in response_dict
        assert 'reference_value_score' in response_dict
        assert 'performance_metrics' in response_dict
        assert 'quality_level' in response_dict
        assert 'strategy_used' in response_dict
        
        # 驗證推薦列表
        assert isinstance(response_dict['recommendations'], list)
        assert len(response_dict['recommendations']) > 0
        
        # 驗證第一個推薦的結構
        first_rec = response_dict['recommendations'][0]
        assert 'product_id' in first_rec
        assert 'product_name' in first_rec
        assert 'confidence_score' in first_rec
        assert 'explanation' in first_rec
        assert 'rank' in first_rec
        assert 'source' in first_rec
    
    def test_member_without_purchase_history(self, engine):
        """測試沒有購買歷史的會員"""
        new_member = MemberInfo(
            member_code="CU999999",
            phone="0900000000",
            total_consumption=0.0,
            accumulated_bonus=0.0,
            recent_purchases=[]
        )
        
        response = engine.recommend(
            member_info=new_member,
            n=5,
            strategy='hybrid'
        )
        
        # 應該仍然能生成推薦
        assert response is not None
        assert len(response.recommendations) > 0
    
    def test_performance_statistics(self, engine, test_member):
        """測試性能統計"""
        # 生成多個推薦以累積統計數據
        for _ in range(3):
            engine.recommend(
                member_info=test_member,
                n=5,
                strategy='hybrid'
            )
        
        # 獲取性能統計
        from datetime import timedelta
        stats = engine.performance_tracker.get_statistics(
            time_window=timedelta(minutes=5)
        )
        
        # 驗證統計數據
        assert stats.total_requests >= 3
        assert stats.p50_time_ms > 0
        assert stats.p95_time_ms > 0
        assert stats.p99_time_ms > 0
        assert stats.avg_time_ms > 0
        
        # P95 應該大於等於 P50
        assert stats.p95_time_ms >= stats.p50_time_ms
        # P99 應該大於等於 P95
        assert stats.p99_time_ms >= stats.p95_time_ms


def test_main_function():
    """測試主函數"""
    from src.models.enhanced_recommendation_engine import main
    
    try:
        main()
    except FileNotFoundError:
        pytest.skip("模型檔案不存在，跳過測試")
    except Exception as e:
        pytest.fail(f"主函數執行失敗: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
