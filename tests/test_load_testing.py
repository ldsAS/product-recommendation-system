"""
負載測試
模擬高負載場景（1000+ 並發請求）、測試系統穩定性和降級機制的有效性
"""
import pytest
import sys
from pathlib import Path
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.enhanced_recommendation_engine import EnhancedRecommendationEngine
from src.models.data_models import MemberInfo
from src.utils.quality_monitor import QualityMonitor
from src.models.enhanced_data_models import AlertLevel


class TestHighLoadScenarios:
    """測試高負載場景"""
    
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
            total_consumption=random.uniform(1000, 50000),
            accumulated_bonus=random.uniform(100, 5000),
            recent_purchases=[]
        )
    
    def _execute_recommendation(self, engine, member):
        """執行推薦並返回結果"""
        try:
            start_time = time.time()
            response = engine.recommend(
                member_info=member,
                n=5,
                strategy='hybrid'
            )
            elapsed_ms = (time.time() - start_time) * 1000
            
            return {
                'success': True,
                'response': response,
                'elapsed_ms': elapsed_ms,
                'error': None
            }
        except Exception as e:
            return {
                'success': False,
                'response': None,
                'elapsed_ms': 0,
                'error': str(e)
            }
    
    @pytest.mark.slow
    def test_load_200_concurrent_requests(self, engine):
        """測試200個並發請求"""
        num_requests = 200
        members = [self.create_test_member(i) for i in range(num_requests)]
        
        print(f"\n開始負載測試: {num_requests}個並發請求")
        start_time = time.time()
        
        results = []
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [
                executor.submit(self._execute_recommendation, engine, member)
                for member in members
            ]
            
            for future in as_completed(futures):
                results.append(future.result())
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 分析結果
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        success_rate = len(successful) / num_requests
        qps = len(successful) / total_time
        
        if successful:
            response_times = [r['elapsed_ms'] for r in successful]
            avg_time = statistics.mean(response_times)
            p50 = statistics.median(response_times)
            p95 = statistics.quantiles(response_times, n=20)[18]
            p99 = statistics.quantiles(response_times, n=100)[98]
        else:
            avg_time = p50 = p95 = p99 = 0
        
        print(f"\n負載測試結果（200並發）:")
        print(f"  總耗時: {total_time:.2f}秒")
        print(f"  成功請求: {len(successful)}")
        print(f"  失敗請求: {len(failed)}")
        print(f"  成功率: {success_rate:.2%}")
        print(f"  QPS: {qps:.2f}")
        print(f"  平均反應時間: {avg_time:.2f}ms")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms")
        print(f"  P99: {p99:.2f}ms")
        
        # 驗證系統穩定性
        assert success_rate >= 0.90, f"成功率過低: {success_rate:.2%}"
        assert qps >= 15, f"QPS過低: {qps:.2f}"
        
        if successful:
            assert p95 < 3000, f"P95反應時間過長: {p95:.2f}ms"
    
    @pytest.mark.slow
    def test_load_500_concurrent_requests(self, engine):
        """測試500個並發請求"""
        num_requests = 500
        members = [self.create_test_member(i) for i in range(num_requests)]
        
        print(f"\n開始負載測試: {num_requests}個並發請求")
        start_time = time.time()
        
        results = []
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [
                executor.submit(self._execute_recommendation, engine, member)
                for member in members
            ]
            
            completed = 0
            for future in as_completed(futures):
                results.append(future.result())
                completed += 1
                if completed % 100 == 0:
                    print(f"  已完成: {completed}/{num_requests}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 分析結果
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        success_rate = len(successful) / num_requests
        qps = len(successful) / total_time
        
        if successful:
            response_times = [r['elapsed_ms'] for r in successful]
            avg_time = statistics.mean(response_times)
            p50 = statistics.median(response_times)
            p95 = statistics.quantiles(response_times, n=20)[18]
            p99 = statistics.quantiles(response_times, n=100)[98]
        else:
            avg_time = p50 = p95 = p99 = 0
        
        print(f"\n負載測試結果（500並發）:")
        print(f"  總耗時: {total_time:.2f}秒")
        print(f"  成功請求: {len(successful)}")
        print(f"  失敗請求: {len(failed)}")
        print(f"  成功率: {success_rate:.2%}")
        print(f"  QPS: {qps:.2f}")
        print(f"  平均反應時間: {avg_time:.2f}ms")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms")
        print(f"  P99: {p99:.2f}ms")
        
        # 驗證系統穩定性（在高負載下允許較低的成功率）
        assert success_rate >= 0.85, f"成功率過低: {success_rate:.2%}"
        assert qps >= 10, f"QPS過低: {qps:.2f}"
    
    @pytest.mark.slow
    def test_load_1000_concurrent_requests(self, engine):
        """測試1000個並發請求（極限負載）"""
        num_requests = 1000
        members = [self.create_test_member(i) for i in range(num_requests)]
        
        print(f"\n開始極限負載測試: {num_requests}個並發請求")
        start_time = time.time()
        
        results = []
        with ThreadPoolExecutor(max_workers=150) as executor:
            futures = [
                executor.submit(self._execute_recommendation, engine, member)
                for member in members
            ]
            
            completed = 0
            for future in as_completed(futures):
                results.append(future.result())
                completed += 1
                if completed % 200 == 0:
                    print(f"  已完成: {completed}/{num_requests}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 分析結果
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        success_rate = len(successful) / num_requests
        qps = len(successful) / total_time
        
        if successful:
            response_times = [r['elapsed_ms'] for r in successful]
            avg_time = statistics.mean(response_times)
            p50 = statistics.median(response_times)
            p95 = statistics.quantiles(response_times, n=20)[18]
            p99 = statistics.quantiles(response_times, n=100)[98]
            max_time = max(response_times)
        else:
            avg_time = p50 = p95 = p99 = max_time = 0
        
        print(f"\n極限負載測試結果（1000並發）:")
        print(f"  總耗時: {total_time:.2f}秒")
        print(f"  成功請求: {len(successful)}")
        print(f"  失敗請求: {len(failed)}")
        print(f"  成功率: {success_rate:.2%}")
        print(f"  QPS: {qps:.2f}")
        print(f"  平均反應時間: {avg_time:.2f}ms")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms")
        print(f"  P99: {p99:.2f}ms")
        print(f"  最大反應時間: {max_time:.2f}ms")
        
        # 在極限負載下，系統應該仍然保持基本穩定
        assert success_rate >= 0.80, f"成功率過低: {success_rate:.2%}"
        
        # 打印失敗原因統計
        if failed:
            error_types = {}
            for f in failed:
                error = f['error']
                error_types[error] = error_types.get(error, 0) + 1
            
            print(f"\n失敗原因統計:")
            for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {error}: {count}次")


class TestSystemStability:
    """測試系統穩定性"""
    
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
            total_consumption=random.uniform(1000, 50000),
            accumulated_bonus=random.uniform(100, 5000),
            recent_purchases=[]
        )
    
    @pytest.mark.slow
    def test_sustained_load(self, engine):
        """測試持續負載（模擬真實場景）"""
        duration_seconds = 30  # 持續30秒
        target_qps = 20  # 目標QPS
        
        print(f"\n開始持續負載測試: {duration_seconds}秒，目標QPS: {target_qps}")
        
        start_time = time.time()
        request_count = 0
        successful_count = 0
        failed_count = 0
        response_times = []
        
        while time.time() - start_time < duration_seconds:
            batch_start = time.time()
            
            # 每批次發送一定數量的請求
            batch_size = 5
            members = [self.create_test_member(request_count + i) for i in range(batch_size)]
            
            for member in members:
                try:
                    req_start = time.time()
                    response = engine.recommend(
                        member_info=member,
                        n=5,
                        strategy='hybrid'
                    )
                    req_time = (time.time() - req_start) * 1000
                    
                    response_times.append(req_time)
                    successful_count += 1
                except Exception:
                    failed_count += 1
                
                request_count += 1
            
            # 控制QPS
            batch_time = time.time() - batch_start
            expected_batch_time = batch_size / target_qps
            if batch_time < expected_batch_time:
                time.sleep(expected_batch_time - batch_time)
        
        total_time = time.time() - start_time
        actual_qps = successful_count / total_time
        success_rate = successful_count / request_count if request_count > 0 else 0
        
        if response_times:
            avg_time = statistics.mean(response_times)
            p50 = statistics.median(response_times)
            p95 = statistics.quantiles(response_times, n=20)[18]
        else:
            avg_time = p50 = p95 = 0
        
        print(f"\n持續負載測試結果:")
        print(f"  測試時長: {total_time:.2f}秒")
        print(f"  總請求數: {request_count}")
        print(f"  成功請求: {successful_count}")
        print(f"  失敗請求: {failed_count}")
        print(f"  成功率: {success_rate:.2%}")
        print(f"  實際QPS: {actual_qps:.2f}")
        print(f"  平均反應時間: {avg_time:.2f}ms")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms")
        
        # 驗證系統穩定性
        assert success_rate >= 0.95, f"成功率過低: {success_rate:.2%}"
        assert actual_qps >= target_qps * 0.8, f"實際QPS過低: {actual_qps:.2f}"
        
        if response_times:
            assert p95 < 2000, f"P95反應時間過長: {p95:.2f}ms"
    
    @pytest.mark.slow
    def test_memory_stability(self, engine):
        """測試記憶體穩定性（防止記憶體洩漏）"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # 記錄初始記憶體使用
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"\n開始記憶體穩定性測試")
        print(f"  初始記憶體: {initial_memory:.2f} MB")
        
        # 執行大量請求
        num_requests = 200
        members = [self.create_test_member(i) for i in range(num_requests)]
        
        for i, member in enumerate(members):
            try:
                engine.recommend(
                    member_info=member,
                    n=5,
                    strategy='hybrid'
                )
            except Exception:
                pass
            
            # 每50個請求檢查一次記憶體
            if (i + 1) % 50 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                print(f"  請求 {i+1}: {current_memory:.2f} MB")
        
        # 記錄最終記憶體使用
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        memory_increase_rate = memory_increase / initial_memory
        
        print(f"\n記憶體穩定性測試結果:")
        print(f"  初始記憶體: {initial_memory:.2f} MB")
        print(f"  最終記憶體: {final_memory:.2f} MB")
        print(f"  記憶體增長: {memory_increase:.2f} MB ({memory_increase_rate:.1%})")
        
        # 驗證記憶體增長在合理範圍內（不超過50%）
        assert memory_increase_rate < 0.5, f"記憶體增長過大: {memory_increase_rate:.1%}"


class TestDegradationEffectiveness:
    """測試降級機制的有效性"""
    
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
    
    def create_test_member(self, member_id):
        """創建測試會員"""
        return MemberInfo(
            member_code=f"CU{member_id:06d}",
            phone=f"09{member_id:08d}",
            total_consumption=random.uniform(0, 50000),
            accumulated_bonus=random.uniform(0, 5000),
            recent_purchases=[]
        )
    
    def test_degradation_under_load(self, engine, monitor):
        """測試負載下的降級機制"""
        num_requests = 100
        members = [self.create_test_member(i) for i in range(num_requests)]
        
        print(f"\n測試降級機制（{num_requests}個請求）")
        
        degraded_count = 0
        normal_count = 0
        
        for member in members:
            try:
                response = engine.recommend(
                    member_info=member,
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
                
                if response.is_degraded:
                    degraded_count += 1
                else:
                    normal_count += 1
                    
            except Exception as e:
                print(f"  錯誤: {e}")
        
        degradation_rate = degraded_count / num_requests if num_requests > 0 else 0
        
        print(f"\n降級機制測試結果:")
        print(f"  正常推薦: {normal_count}")
        print(f"  降級推薦: {degraded_count}")
        print(f"  降級率: {degradation_rate:.2%}")
        
        # 生成報告
        report = monitor.generate_hourly_report()
        print(f"\n品質報告:")
        print(f"  平均可參考價值分數: {report.avg_overall_score:.2f}")
        print(f"  平均反應時間: {report.avg_response_time_ms:.2f}ms")
        print(f"  告警數量: {report.total_alerts}")
        
        # 驗證降級機制運作
        # 降級率應該在合理範圍內（不應該太高）
        assert degradation_rate < 0.3, f"降級率過高: {degradation_rate:.2%}"
    
    def test_degradation_maintains_availability(self, engine):
        """測試降級機制維持系統可用性"""
        # 創建可能觸發降級的會員（新會員，無購買歷史）
        new_members = [
            MemberInfo(
                member_code=f"NEW{i:06d}",
                phone=f"09{i:08d}",
                total_consumption=0.0,
                accumulated_bonus=0.0,
                recent_purchases=[]
            )
            for i in range(50)
        ]
        
        print(f"\n測試降級機制維持可用性（50個新會員）")
        
        successful = 0
        degraded = 0
        
        for member in new_members:
            try:
                response = engine.recommend(
                    member_info=member,
                    n=5,
                    strategy='hybrid'
                )
                
                # 驗證即使降級也能返回推薦
                assert response is not None
                assert len(response.recommendations) > 0
                
                successful += 1
                if response.is_degraded:
                    degraded += 1
                    
            except Exception as e:
                print(f"  錯誤: {e}")
        
        success_rate = successful / len(new_members)
        degradation_rate = degraded / successful if successful > 0 else 0
        
        print(f"\n可用性測試結果:")
        print(f"  成功請求: {successful}/{len(new_members)}")
        print(f"  成功率: {success_rate:.2%}")
        print(f"  降級請求: {degraded}")
        print(f"  降級率: {degradation_rate:.2%}")
        
        # 驗證系統保持高可用性
        assert success_rate >= 0.95, f"成功率過低: {success_rate:.2%}"
        
        # 對於新會員，降級是正常的
        print(f"  ✓ 降級機制正常運作，維持系統可用性")


if __name__ == "__main__":
    # 運行負載測試時使用 -m slow 標記
    pytest.main([__file__, "-v", "--tb=short", "-s", "-m", "slow"])
