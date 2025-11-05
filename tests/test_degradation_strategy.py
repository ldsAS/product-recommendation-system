"""
測試降級策略
"""
import pytest
import pandas as pd
from datetime import datetime

from src.utils.degradation_strategy import DegradationStrategy
from src.models.enhanced_data_models import (
    ReferenceValueScore,
    PerformanceMetrics
)
from src.models.data_models import (
    MemberInfo,
    RecommendationSource
)


@pytest.fixture
def sample_product_features():
    """創建測試用產品特徵"""
    return pd.DataFrame({
        'stock_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
        'stock_description': ['產品A', '產品B', '產品C', '產品D', '產品E'],
        'avg_price': [100.0, 200.0, 150.0, 300.0, 250.0],
        'popularity_score': [80.0, 70.0, 60.0, 50.0, 40.0],
        'category': ['類別1', '類別2', '類別1', '類別3', '類別2']
    })


@pytest.fixture
def degradation_strategy(sample_product_features):
    """創建降級策略實例"""
    return DegradationStrategy(product_features=sample_product_features)


@pytest.fixture
def sample_member_info():
    """創建測試用會員資訊"""
    return MemberInfo(
        member_code="TEST001",
        phone="0912345678",
        total_consumption=5000.0,
        accumulated_bonus=100.0,
        recent_purchases=["P001"]
    )


class TestDegradationJudgment:
    """測試降級判斷邏輯"""
    
    def test_should_degrade_low_quality_score(self, degradation_strategy):
        """測試品質分數過低時應該降級"""
        # 創建低品質分數
        low_quality_score = ReferenceValueScore(
            overall_score=35.0,  # 低於閾值 40
            relevance_score=40.0,
            novelty_score=30.0,
            explainability_score=35.0,
            diversity_score=35.0,
            score_breakdown={},
            timestamp=datetime.now()
        )
        
        # 判斷是否需要降級
        should_degrade = degradation_strategy.should_degrade(
            value_score=low_quality_score
        )
        
        assert should_degrade is True
    
    def test_should_degrade_high_response_time(self, degradation_strategy):
        """測試反應時間過長時應該降級"""
        # 創建高反應時間指標
        slow_performance = PerformanceMetrics(
            request_id="test_001",
            total_time_ms=2500.0,  # 超過閾值 2000ms
            stage_times={},
            is_slow_query=True,
            timestamp=datetime.now()
        )
        
        # 判斷是否需要降級
        should_degrade = degradation_strategy.should_degrade(
            performance_metrics=slow_performance
        )
        
        assert should_degrade is True
    
    def test_should_not_degrade_good_quality(self, degradation_strategy):
        """測試品質良好時不應該降級"""
        # 創建良好品質分數
        good_quality_score = ReferenceValueScore(
            overall_score=65.0,  # 高於閾值 40
            relevance_score=70.0,
            novelty_score=60.0,
            explainability_score=65.0,
            diversity_score=60.0,
            score_breakdown={},
            timestamp=datetime.now()
        )
        
        # 判斷是否需要降級
        should_degrade = degradation_strategy.should_degrade(
            value_score=good_quality_score
        )
        
        assert should_degrade is False
    
    def test_should_not_degrade_fast_response(self, degradation_strategy):
        """測試反應時間正常時不應該降級"""
        # 創建正常反應時間指標
        fast_performance = PerformanceMetrics(
            request_id="test_002",
            total_time_ms=500.0,  # 低於閾值 2000ms
            stage_times={},
            is_slow_query=False,
            timestamp=datetime.now()
        )
        
        # 判斷是否需要降級
        should_degrade = degradation_strategy.should_degrade(
            performance_metrics=fast_performance
        )
        
        assert should_degrade is False
    
    def test_should_degrade_both_conditions(self, degradation_strategy):
        """測試品質和性能都不達標時應該降級"""
        # 創建低品質分數
        low_quality_score = ReferenceValueScore(
            overall_score=30.0,
            relevance_score=35.0,
            novelty_score=25.0,
            explainability_score=30.0,
            diversity_score=30.0,
            score_breakdown={},
            timestamp=datetime.now()
        )
        
        # 創建高反應時間指標
        slow_performance = PerformanceMetrics(
            request_id="test_003",
            total_time_ms=3000.0,
            stage_times={},
            is_slow_query=True,
            timestamp=datetime.now()
        )
        
        # 判斷是否需要降級（只需一個條件滿足即可）
        should_degrade_quality = degradation_strategy.should_degrade(
            value_score=low_quality_score
        )
        should_degrade_performance = degradation_strategy.should_degrade(
            performance_metrics=slow_performance
        )
        
        assert should_degrade_quality is True
        assert should_degrade_performance is True


class TestDegradationRecommendation:
    """測試降級推薦生成"""
    
    def test_execute_degradation_returns_recommendations(
        self, 
        degradation_strategy, 
        sample_member_info
    ):
        """測試降級推薦能夠返回推薦列表"""
        # 執行降級推薦
        recommendations = degradation_strategy.execute_degradation(
            member_info=sample_member_info,
            n=3
        )
        
        # 驗證返回推薦列表
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert len(recommendations) <= 3
    
    def test_degradation_excludes_purchased_products(
        self, 
        degradation_strategy, 
        sample_member_info
    ):
        """測試降級推薦排除已購買產品"""
        # 執行降級推薦
        recommendations = degradation_strategy.execute_degradation(
            member_info=sample_member_info,
            n=5
        )
        
        # 驗證不包含已購買產品
        recommended_ids = [rec.product_id for rec in recommendations]
        for purchased_id in sample_member_info.recent_purchases:
            assert purchased_id not in recommended_ids
    
    def test_degradation_uses_popularity_source(
        self, 
        degradation_strategy, 
        sample_member_info
    ):
        """測試降級推薦使用熱門推薦來源"""
        # 執行降級推薦
        recommendations = degradation_strategy.execute_degradation(
            member_info=sample_member_info,
            n=3
        )
        
        # 驗證推薦來源為熱門推薦
        for rec in recommendations:
            assert rec.source == RecommendationSource.POPULARITY
    
    def test_degradation_has_simple_explanation(
        self, 
        degradation_strategy, 
        sample_member_info
    ):
        """測試降級推薦有簡單的理由"""
        # 執行降級推薦
        recommendations = degradation_strategy.execute_degradation(
            member_info=sample_member_info,
            n=3
        )
        
        # 驗證推薦理由存在且簡單
        for rec in recommendations:
            assert rec.explanation is not None
            assert len(rec.explanation) > 0
    
    def test_degradation_assigns_ranks(
        self, 
        degradation_strategy, 
        sample_member_info
    ):
        """測試降級推薦分配排名"""
        # 執行降級推薦
        recommendations = degradation_strategy.execute_degradation(
            member_info=sample_member_info,
            n=3
        )
        
        # 驗證排名正確分配
        for i, rec in enumerate(recommendations, 1):
            assert rec.rank == i
    
    def test_degradation_with_no_products(self, sample_member_info):
        """測試沒有產品特徵時的降級推薦"""
        # 創建沒有產品特徵的降級策略
        empty_strategy = DegradationStrategy(product_features=None)
        
        # 執行降級推薦
        recommendations = empty_strategy.execute_degradation(
            member_info=sample_member_info,
            n=3
        )
        
        # 驗證返回空列表
        assert isinstance(recommendations, list)
        assert len(recommendations) == 0
    
    def test_degradation_with_empty_dataframe(self, sample_member_info):
        """測試空產品特徵時的降級推薦"""
        # 創建空產品特徵
        empty_df = pd.DataFrame()
        empty_strategy = DegradationStrategy(product_features=empty_df)
        
        # 執行降級推薦
        recommendations = empty_strategy.execute_degradation(
            member_info=sample_member_info,
            n=3
        )
        
        # 驗證返回空列表
        assert isinstance(recommendations, list)
        assert len(recommendations) == 0


class TestDegradationConfiguration:
    """測試降級配置"""
    
    def test_get_degradation_thresholds(self, degradation_strategy):
        """測試獲取降級閾值"""
        thresholds = degradation_strategy.get_degradation_thresholds()
        
        assert 'min_quality_score' in thresholds
        assert 'max_response_time_ms' in thresholds
        assert thresholds['min_quality_score'] == 40
        assert thresholds['max_response_time_ms'] == 2000
    
    def test_update_quality_threshold(self, degradation_strategy):
        """測試更新品質閾值"""
        # 更新品質閾值
        degradation_strategy.update_degradation_thresholds(
            min_quality_score=50.0
        )
        
        # 驗證閾值已更新
        thresholds = degradation_strategy.get_degradation_thresholds()
        assert thresholds['min_quality_score'] == 50.0
        
        # 測試新閾值生效
        medium_quality_score = ReferenceValueScore(
            overall_score=45.0,  # 在新閾值 50 以下
            relevance_score=50.0,
            novelty_score=40.0,
            explainability_score=45.0,
            diversity_score=45.0,
            score_breakdown={},
            timestamp=datetime.now()
        )
        
        should_degrade = degradation_strategy.should_degrade(
            value_score=medium_quality_score
        )
        assert should_degrade is True
    
    def test_update_performance_threshold(self, degradation_strategy):
        """測試更新性能閾值"""
        # 更新性能閾值
        degradation_strategy.update_degradation_thresholds(
            max_response_time_ms=1500.0
        )
        
        # 驗證閾值已更新
        thresholds = degradation_strategy.get_degradation_thresholds()
        assert thresholds['max_response_time_ms'] == 1500.0
        
        # 測試新閾值生效
        medium_performance = PerformanceMetrics(
            request_id="test_004",
            total_time_ms=1800.0,  # 在新閾值 1500 以上
            stage_times={},
            is_slow_query=False,
            timestamp=datetime.now()
        )
        
        should_degrade = degradation_strategy.should_degrade(
            performance_metrics=medium_performance
        )
        assert should_degrade is True
    
    def test_update_both_thresholds(self, degradation_strategy):
        """測試同時更新兩個閾值"""
        # 同時更新兩個閾值
        degradation_strategy.update_degradation_thresholds(
            min_quality_score=45.0,
            max_response_time_ms=1800.0
        )
        
        # 驗證閾值已更新
        thresholds = degradation_strategy.get_degradation_thresholds()
        assert thresholds['min_quality_score'] == 45.0
        assert thresholds['max_response_time_ms'] == 1800.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
