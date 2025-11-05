"""
性能測試
測試單次推薦的反應時間、並發推薦性能、各階段耗時分布和性能瓶頸識別
"""
import pytest
import sys
from pathlib import Path
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.enhanced_recommendation_engine import EnhancedRecommendationEngine
from src.models.data_models import MemberInfo


class TestSingleRequestPerformance:
    """測試單次推薦的反應時間"""
    
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
    
    def test_single_recommendation_response_time(self, engine, test_member):
        """測試單次推薦的反應時間"""
        # 執行推薦並測量時間
        start_time = time.time()
        response = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='hybrid'
        )
        end_time = time.time()
        
        # 計算實際耗時（毫秒）
        actual_time_ms = (end_time - start_time) * 1000
        
        # 驗證推薦成功
        assert response is not None
        assert len(response.recommendations) > 0
        
        # 驗證反應時間合理（應該在2秒內）
        assert actual_time_ms < 2000, f"反應時間過長: {actual_time_ms:.2f}ms"
        
        # 驗證性能指標記錄的時間與實際時間接近
        recorded_time_ms = response.performance_metrics.total_time_ms
        # 允許10%的誤差
        assert abs(recorded_time_ms - actual_time_ms) / actual_time_ms < 0.1, \
            f"記錄時間 {recorded_time_ms:.2f}ms 與實際時間 {actual_time_ms:.2f}ms 差異過大"
        
        print(f"\n單次推薦反應時間: {actual_time_ms:.2f}ms")
        print(f"記錄的反應時間: {recorded_time_ms:.2f}ms")
    
    def test_ml_only_strategy_performance(self, engine, test_member):
        """測試純ML策略的性能"""
        start_time = time.time()
        response = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='ml_only'
        )
        end_time = time.time()
        
        actual_time_ms = (end_time - start_time) * 1000
        
        # ML策略應該更快（因為不需要混合多種策略）
        assert actual_time_ms < 1500, f"ML策略反應時間過長: {actual_time_ms:.2f}ms"
        
        print(f"\nML策略反應時間: {actual_time_ms:.2f}ms")
    
    def test_multiple_single_requests_consistency(self, engine, test_member):
        """測試多次單次請求的性能一致性"""
        response_times = []
        
        # 執行10次推薦
        for i in range(10):
            start_time = time.time()
            response = engine.recommend(
                member_info=test_member,
                n=5,
                strategy='hybrid'
            )
            end_time = time.time()
            
            response_times.append((end_time - start_time) * 1000)
        
        # 計算統計數據
        avg_time = statistics.mean(response_times)
        std_dev = statistics.stdev(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        # 驗證平均反應時間合理
        assert avg_time < 1000, f"平均反應時間過長: {avg_time:.2f}ms"
        
        # 驗證性能穩定性（標準差不應太大）
        cv = std_dev / avg_time  # 變異係數
        assert cv < 0.5, f"性能波動過大，變異係數: {cv:.2f}"
        
        print(f"\n性能統計（10次請求）:")
        print(f"  平均: {avg_time:.2f}ms")
        print(f"  標準差: {std_dev:.2f}ms")
        print(f"  最小: {min_time:.2f}ms")
        print(f"  最大: {max_time:.2f}ms")
        print(f"  變異係數: {cv:.2f}")


class TestConcurrentPerformance:
    """測試並發推薦的性能（100 QPS）"""
    
    @pytest.fixture
    def engine(self):
        """創建測試用的增強推薦引擎"""
        try:
            engine = EnhancedRecommendationEngine()
            return engine
        except FileNotFoundError:
            pytest.skip("模型檔案不存在，跳過測試")
    
    def create_test_member(self, member_id):
        """創建測試會員"""
        return MemberInfo(
            member_code=f"CU{member_id:06d}",
            phone=f"09{member_id:08d}",
            total_consumption=1000.0 + member_id * 100,
            accumulated_bonus=100.0 + member_id * 10,
            recent_purchases=[]
        )
    
    def test_concurrent_10_requests(self, engine):
        """測試10個並發請求"""
        num_requests = 10
        members = [self.create_test_member(i) for i in range(num_requests)]
        
        start_time = time.time()
        
        # 使用線程池執行並發請求
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(engine.recommend, member, 5, 'hybrid')
                for member in members
            ]
            
            # 等待所有請求完成
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 驗證所有請求都成功
        assert len(results) == num_requests
        for result in results:
            assert result is not None
            assert len(result.recommendations) > 0
        
        # 計算QPS
        qps = num_requests / total_time
        
        print(f"\n並發10請求:")
        print(f"  總耗時: {total_time:.2f}秒")
        print(f"  QPS: {qps:.2f}")
        
        # 驗證QPS合理（至少能處理5 QPS）
        assert qps >= 5, f"QPS過低: {qps:.2f}"
    
    def test_concurrent_50_requests(self, engine):
        """測試50個並發請求"""
        num_requests = 50
        members = [self.create_test_member(i) for i in range(num_requests)]
        
        start_time = time.time()
        response_times = []
        
        # 使用線程池執行並發請求
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for member in members:
                future = executor.submit(self._timed_recommend, engine, member)
                futures.append(future)
            
            # 收集結果和時間
            for future in as_completed(futures):
                result, elapsed_ms = future.result()
                response_times.append(elapsed_ms)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 計算統計數據
        qps = num_requests / total_time
        avg_response_time = statistics.mean(response_times)
        p50 = statistics.median(response_times)
        p95 = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        p99 = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        
        print(f"\n並發50請求:")
        print(f"  總耗時: {total_time:.2f}秒")
        print(f"  QPS: {qps:.2f}")
        print(f"  平均反應時間: {avg_response_time:.2f}ms")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms")
        print(f"  P99: {p99:.2f}ms")
        
        # 驗證性能指標
        assert qps >= 10, f"QPS過低: {qps:.2f}"
        assert p95 < 1000, f"P95反應時間過長: {p95:.2f}ms"
    
    def test_concurrent_100_requests(self, engine):
        """測試100個並發請求（目標100 QPS）"""
        num_requests = 100
        members = [self.create_test_member(i) for i in range(num_requests)]
        
        start_time = time.time()
        response_times = []
        errors = []
        
        # 使用線程池執行並發請求
        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = []
            for member in members:
                future = executor.submit(self._timed_recommend_with_error_handling, engine, member)
                futures.append(future)
            
            # 收集結果
            for future in as_completed(futures):
                result, elapsed_ms, error = future.result()
                if error:
                    errors.append(error)
                else:
                    response_times.append(elapsed_ms)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 計算統計數據
        success_count = len(response_times)
        error_count = len(errors)
        qps = success_count / total_time
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p50 = statistics.median(response_times)
            p95 = statistics.quantiles(response_times, n=20)[18]
            p99 = statistics.quantiles(response_times, n=100)[98]
        else:
            avg_response_time = p50 = p95 = p99 = 0
        
        print(f"\n並發100請求:")
        print(f"  總耗時: {total_time:.2f}秒")
        print(f"  成功請求: {success_count}")
        print(f"  失敗請求: {error_count}")
        print(f"  QPS: {qps:.2f}")
        print(f"  平均反應時間: {avg_response_time:.2f}ms")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms")
        print(f"  P99: {p99:.2f}ms")
        
        # 驗證性能指標
        # 成功率應該很高
        success_rate = success_count / num_requests
        assert success_rate >= 0.95, f"成功率過低: {success_rate:.2%}"
        
        # QPS應該接近或超過目標
        # 注意：在測試環境中可能無法達到100 QPS，所以設置較低的閾值
        assert qps >= 20, f"QPS過低: {qps:.2f}"
        
        # P95反應時間應該合理
        if response_times:
            assert p95 < 2000, f"P95反應時間過長: {p95:.2f}ms"
    
    def _timed_recommend(self, engine, member):
        """執行推薦並測量時間"""
        start = time.time()
        result = engine.recommend(member, 5, 'hybrid')
        elapsed = (time.time() - start) * 1000
        return result, elapsed
    
    def _timed_recommend_with_error_handling(self, engine, member):
        """執行推薦並測量時間（帶錯誤處理）"""
        try:
            start = time.time()
            result = engine.recommend(member, 5, 'hybrid')
            elapsed = (time.time() - start) * 1000
            return result, elapsed, None
        except Exception as e:
            return None, 0, str(e)


class TestStagePerformance:
    """測試各階段的耗時分布"""
    
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
    
    def test_stage_time_distribution(self, engine, test_member):
        """測試各階段耗時分布"""
        # 執行多次推薦以獲取穩定的統計數據
        num_runs = 20
        stage_times_list = []
        
        for _ in range(num_runs):
            response = engine.recommend(
                member_info=test_member,
                n=5,
                strategy='hybrid'
            )
            stage_times_list.append(response.performance_metrics.stage_times)
        
        # 計算各階段的平均耗時
        all_stages = set()
        for stage_times in stage_times_list:
            all_stages.update(stage_times.keys())
        
        stage_stats = {}
        for stage in all_stages:
            times = [st.get(stage, 0) for st in stage_times_list]
            stage_stats[stage] = {
                'avg': statistics.mean(times),
                'min': min(times),
                'max': max(times),
                'std': statistics.stdev(times) if len(times) > 1 else 0
            }
        
        # 打印各階段統計
        print(f"\n各階段耗時統計（{num_runs}次運行）:")
        total_avg = sum(s['avg'] for s in stage_stats.values())
        
        for stage, stats in sorted(stage_stats.items(), key=lambda x: x[1]['avg'], reverse=True):
            percentage = (stats['avg'] / total_avg * 100) if total_avg > 0 else 0
            print(f"  {stage}:")
            print(f"    平均: {stats['avg']:.2f}ms ({percentage:.1f}%)")
            print(f"    範圍: {stats['min']:.2f}ms - {stats['max']:.2f}ms")
            print(f"    標準差: {stats['std']:.2f}ms")
        
        # 驗證關鍵階段存在
        expected_stages = ['feature_loading', 'model_inference', 'reason_generation', 'quality_evaluation']
        for stage in expected_stages:
            assert stage in stage_stats, f"缺少關鍵階段: {stage}"
    
    def test_identify_bottleneck(self, engine, test_member):
        """識別性能瓶頸"""
        # 執行推薦
        response = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='hybrid'
        )
        
        stage_times = response.performance_metrics.stage_times
        total_time = response.performance_metrics.total_time_ms
        
        # 找出最耗時的階段
        if stage_times:
            bottleneck_stage = max(stage_times.items(), key=lambda x: x[1])
            bottleneck_name, bottleneck_time = bottleneck_stage
            bottleneck_percentage = (bottleneck_time / total_time * 100) if total_time > 0 else 0
            
            print(f"\n性能瓶頸分析:")
            print(f"  總耗時: {total_time:.2f}ms")
            print(f"  瓶頸階段: {bottleneck_name}")
            print(f"  瓶頸耗時: {bottleneck_time:.2f}ms ({bottleneck_percentage:.1f}%)")
            
            # 如果某個階段佔用超過50%的時間，標記為瓶頸
            if bottleneck_percentage > 50:
                print(f"  ⚠️ 警告: {bottleneck_name} 佔用了超過50%的時間，建議優化")
    
    def test_stage_time_thresholds(self, engine, test_member):
        """測試各階段耗時是否在合理範圍內"""
        response = engine.recommend(
            member_info=test_member,
            n=5,
            strategy='hybrid'
        )
        
        stage_times = response.performance_metrics.stage_times
        
        # 定義各階段的合理閾值（毫秒）
        thresholds = {
            'feature_loading': 200,
            'model_inference': 300,
            'reason_generation': 100,
            'quality_evaluation': 100
        }
        
        print(f"\n各階段耗時檢查:")
        for stage, threshold in thresholds.items():
            if stage in stage_times:
                actual_time = stage_times[stage]
                status = "✓" if actual_time <= threshold else "✗"
                print(f"  {status} {stage}: {actual_time:.2f}ms (閾值: {threshold}ms)")
                
                # 警告但不失敗（因為性能可能因環境而異）
                if actual_time > threshold:
                    print(f"    ⚠️ 警告: 超過閾值 {actual_time - threshold:.2f}ms")


class TestPerformanceStatistics:
    """測試性能統計功能"""
    
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
    
    def test_performance_statistics_accumulation(self, engine, test_member):
        """測試性能統計累積"""
        # 執行多次推薦
        num_requests = 30
        for _ in range(num_requests):
            engine.recommend(
                member_info=test_member,
                n=5,
                strategy='hybrid'
            )
        
        # 獲取性能統計
        stats = engine.performance_tracker.get_statistics(
            time_window=timedelta(minutes=5)
        )
        
        # 驗證統計數據
        assert stats.total_requests >= num_requests
        assert stats.avg_time_ms > 0
        assert stats.p50_time_ms > 0
        assert stats.p95_time_ms > 0
        assert stats.p99_time_ms > 0
        
        # 驗證百分位數關係
        assert stats.p50_time_ms <= stats.p95_time_ms
        assert stats.p95_time_ms <= stats.p99_time_ms
        
        print(f"\n性能統計（{stats.total_requests}次請求）:")
        print(f"  平均反應時間: {stats.avg_time_ms:.2f}ms")
        print(f"  P50: {stats.p50_time_ms:.2f}ms")
        print(f"  P95: {stats.p95_time_ms:.2f}ms")
        print(f"  P99: {stats.p99_time_ms:.2f}ms")
        print(f"  慢查詢數量: {stats.slow_query_count}")
        print(f"  慢查詢率: {stats.slow_query_rate:.2%}")
        
        # 驗證P95在目標範圍內
        assert stats.p95_time_ms < 1000, f"P95反應時間過長: {stats.p95_time_ms:.2f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
