"""
性能優化驗證測試
驗證快取、批次處理等優化措施的效果
"""
import pytest
import sys
from pathlib import Path
import time
import statistics

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.enhanced_recommendation_engine import EnhancedRecommendationEngine
from src.models.data_models import MemberInfo


class TestCacheOptimization:
    """測試快取優化"""
    
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
    
    def test_product_name_cache(self, engine):
        """測試產品名稱快取"""
        # 驗證快取已建立
        assert len(engine._product_name_cache) > 0
        
        # 測試快取命中
        product_id = list(engine._product_name_cache.keys())[0]
        
        # 第一次查詢（快取命中）
        start = time.time()
        name1 = engine._get_product_name(product_id)
        time1 = (time.time() - start) * 1000
        
        # 第二次查詢（快取命中）
        start = time.time()
        name2 = engine._get_product_name(product_id)
        time2 = (time.time() - start) * 1000
        
        # 驗證結果一致
        assert name1 == name2
        
        # 快取查詢應該非常快（< 0.1ms）
        assert time2 < 0.1, f"快取查詢時間過長: {time2:.4f}ms"
        
        print(f"\n產品名稱快取測試:")
        print(f"  快取大小: {len(engine._product_name_cache)}")
        print(f"  第一次查詢: {time1:.4f}ms")
        print(f"  第二次查詢: {time2:.4f}ms")
        print(f"  ✓ 快取優化有效")
    
    def test_member_history_cache(self, engine, test_member):
        """測試會員歷史快取"""
        # 第一次構建會員歷史
        start = time.time()
        history1 = engine._build_member_history(test_member)
        time1 = (time.time() - start) * 1000
        
        # 第二次構建會員歷史（應該使用快取）
        start = time.time()
        history2 = engine._build_member_history(test_member)
        time2 = (time.time() - start) * 1000
        
        # 驗證結果一致
        assert history1.member_code == history2.member_code
        assert history1.purchased_products == history2.purchased_products
        
        # 快取查詢應該更快或相同
        assert time2 <= time1, f"快取未生效: time1={time1:.4f}ms, time2={time2:.4f}ms"
        
        # 驗證快取大小
        assert len(engine._member_history_cache) > 0
        
        print(f"\n會員歷史快取測試:")
        print(f"  第一次構建: {time1:.4f}ms")
        print(f"  第二次構建: {time2:.4f}ms")
        if time2 > 0:
            print(f"  加速比: {time1/time2:.2f}x")
        else:
            print(f"  加速比: 極快（< 0.001ms）")
        print(f"  快取大小: {len(engine._member_history_cache)}")
        print(f"  ✓ 快取優化有效")
    
    def test_cache_lru_eviction(self, engine):
        """測試快取 LRU 淘汰策略"""
        # 記錄初始快取大小
        initial_cache_size = len(engine._member_history_cache)
        
        # 創建大量不同的會員以填滿快取
        for i in range(engine._cache_max_size + 10):
            member = MemberInfo(
                member_code=f"TEST{i:06d}",
                phone=f"09{i:08d}",
                total_consumption=1000.0,
                accumulated_bonus=100.0,
                recent_purchases=[]
            )
            engine._build_member_history(member)
        
        # 驗證快取大小不超過最大值
        final_cache_size = len(engine._member_history_cache)
        assert final_cache_size <= engine._cache_max_size, \
            f"快取大小超過限制: {final_cache_size} > {engine._cache_max_size}"
        
        print(f"\n快取 LRU 淘汰測試:")
        print(f"  初始快取大小: {initial_cache_size}")
        print(f"  最終快取大小: {final_cache_size}")
        print(f"  快取上限: {engine._cache_max_size}")
        print(f"  ✓ LRU 淘汰策略正常運作")


class TestBatchProcessing:
    """測試批次處理優化"""
    
    @pytest.fixture
    def engine(self):
        """創建測試用的增強推薦引擎"""
        try:
            engine = EnhancedRecommendationEngine()
            return engine
        except FileNotFoundError:
            pytest.skip("模型檔案不存在，跳過測試")
    
    def test_batch_member_history_building(self, engine):
        """測試批次構建會員歷史的性能"""
        # 創建有多個購買記錄的會員
        member_with_many_purchases = MemberInfo(
            member_code="CU000001",
            phone="0937024682",
            total_consumption=17400.0,
            accumulated_bonus=500.0,
            recent_purchases=["30463", "31033", "30464", "31034", "30465"]
        )
        
        # 測量構建時間
        start = time.time()
        history = engine._build_member_history(member_with_many_purchases)
        elapsed_ms = (time.time() - start) * 1000
        
        # 驗證歷史資料正確
        assert history.member_code == member_with_many_purchases.member_code
        assert len(history.purchased_products) == 5
        
        # 批次處理應該很快（< 50ms）
        assert elapsed_ms < 50, f"批次處理時間過長: {elapsed_ms:.2f}ms"
        
        print(f"\n批次會員歷史構建測試:")
        print(f"  購買產品數: {len(member_with_many_purchases.recent_purchases)}")
        print(f"  構建時間: {elapsed_ms:.2f}ms")
        print(f"  ✓ 批次處理優化有效")


class TestDeduplicationOptimization:
    """測試去重優化"""
    
    @pytest.fixture
    def engine(self):
        """創建測試用的增強推薦引擎"""
        try:
            engine = EnhancedRecommendationEngine()
            return engine
        except FileNotFoundError:
            pytest.skip("模型檔案不存在，跳過測試")
    
    def test_deduplication_keeps_highest_score(self, engine):
        """測試去重保留最高分數"""
        from src.models.data_models import Recommendation, RecommendationSource
        
        # 創建重複的推薦（不同分數）
        recommendations = [
            Recommendation(
                product_id="P001",
                product_name="產品A",
                confidence_score=70.0,
                explanation="理由1",
                rank=1,
                source=RecommendationSource.ML_MODEL,
                raw_score=0.7
            ),
            Recommendation(
                product_id="P001",
                product_name="產品A",
                confidence_score=85.0,  # 更高分數
                explanation="理由2",
                rank=2,
                source=RecommendationSource.COLLABORATIVE_FILTERING,
                raw_score=0.85
            ),
            Recommendation(
                product_id="P002",
                product_name="產品B",
                confidence_score=60.0,
                explanation="理由3",
                rank=3,
                source=RecommendationSource.POPULARITY,
                raw_score=0.6
            )
        ]
        
        # 執行去重
        unique_recs = engine._deduplicate_recommendations(recommendations)
        
        # 驗證結果
        assert len(unique_recs) == 2, "去重後應該只有2個產品"
        
        # 找到 P001 的推薦
        p001_rec = next(r for r in unique_recs if r.product_id == "P001")
        
        # 驗證保留了最高分數
        assert p001_rec.confidence_score == 85.0, "應該保留最高分數的推薦"
        
        print(f"\n去重優化測試:")
        print(f"  原始推薦數: {len(recommendations)}")
        print(f"  去重後推薦數: {len(unique_recs)}")
        print(f"  P001 保留分數: {p001_rec.confidence_score}")
        print(f"  ✓ 去重優化正確保留最高分數")


class TestOverallPerformanceImprovement:
    """測試整體性能改進"""
    
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
    
    def test_p95_response_time_target(self, engine, test_member):
        """測試 P95 反應時間是否達標（< 500ms）"""
        num_requests = 50
        response_times = []
        
        print(f"\n測試 P95 反應時間目標（{num_requests}次請求）...")
        
        for i in range(num_requests):
            start = time.time()
            response = engine.recommend(
                member_info=test_member,
                n=5,
                strategy='hybrid'
            )
            elapsed_ms = (time.time() - start) * 1000
            response_times.append(elapsed_ms)
            
            if (i + 1) % 10 == 0:
                print(f"  已完成: {i+1}/{num_requests}")
        
        # 計算統計數據
        avg_time = statistics.mean(response_times)
        p50 = statistics.median(response_times)
        p95 = statistics.quantiles(response_times, n=20)[18]
        p99 = statistics.quantiles(response_times, n=100)[98]
        min_time = min(response_times)
        max_time = max(response_times)
        
        print(f"\n性能統計:")
        print(f"  平均反應時間: {avg_time:.2f}ms")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms")
        print(f"  P99: {p99:.2f}ms")
        print(f"  最小: {min_time:.2f}ms")
        print(f"  最大: {max_time:.2f}ms")
        
        # 驗證 P95 達標
        assert p95 < 500, f"P95 反應時間未達標: {p95:.2f}ms > 500ms"
        
        print(f"\n  ✓ P95 反應時間達標！")
    
    def test_repeated_requests_performance(self, engine, test_member):
        """測試重複請求的性能（驗證快取效果）"""
        # 第一次請求（冷啟動）
        start = time.time()
        response1 = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='hybrid'
        )
        time1 = (time.time() - start) * 1000
        
        # 第二次請求（應該使用快取）
        start = time.time()
        response2 = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='hybrid'
        )
        time2 = (time.time() - start) * 1000
        
        # 第三次請求（應該使用快取）
        start = time.time()
        response3 = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='hybrid'
        )
        time3 = (time.time() - start) * 1000
        
        # 計算平均快取命中時間
        avg_cached_time = (time2 + time3) / 2
        
        print(f"\n重複請求性能測試:")
        print(f"  第一次請求（冷啟動）: {time1:.2f}ms")
        print(f"  第二次請求（快取）: {time2:.2f}ms")
        print(f"  第三次請求（快取）: {time3:.2f}ms")
        print(f"  平均快取命中時間: {avg_cached_time:.2f}ms")
        print(f"  加速比: {time1/avg_cached_time:.2f}x")
        
        # 快取命中應該更快
        assert avg_cached_time <= time1, "快取命中應該不慢於冷啟動"
        
        print(f"  ✓ 快取優化有效")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
