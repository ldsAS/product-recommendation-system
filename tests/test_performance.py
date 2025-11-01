"""
效能測試
測試 API 回應時間、並發處理能力和記憶體使用
"""
import pytest
import sys
import time
import psutil
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestPerformance:
    """效能測試類別"""
    
    @pytest.fixture
    def sample_request(self):
        """範例推薦請求"""
        return {
            "member_code": "CU000001",
            "total_consumption": 10000.0,
            "accumulated_bonus": 300.0,
            "top_k": 5
        }
    
    def test_api_response_time(self, sample_request):
        """測試 API 回應時間（目標 < 3秒）"""
        start_time = time.time()
        
        response = client.post("/api/v1/recommendations", json=sample_request)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"\n回應時間: {response_time:.3f} 秒")
        
        # 如果模型已訓練，檢查回應時間
        if response.status_code == 200:
            assert response_time < 3.0, f"回應時間 {response_time:.3f}s 超過 3 秒"
    
    def test_health_check_response_time(self):
        """測試健康檢查回應時間"""
        start_time = time.time()
        
        response = client.get("/health")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"\n健康檢查回應時間: {response_time:.3f} 秒")
        
        assert response.status_code == 200
        assert response_time < 0.1, f"健康檢查回應時間 {response_time:.3f}s 過長"
    
    def test_concurrent_requests(self, sample_request):
        """測試並發請求處理能力"""
        num_requests = 10
        max_workers = 5
        
        def make_request():
            """發送單個請求"""
            start_time = time.time()
            response = client.post("/api/v1/recommendations", json=sample_request)
            end_time = time.time()
            return {
                'status_code': response.status_code,
                'response_time': end_time - start_time
            }
        
        # 並發執行請求
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 統計結果
        successful_requests = sum(1 for r in results if r['status_code'] in [200, 503])
        avg_response_time = sum(r['response_time'] for r in results) / len(results)
        
        print(f"\n並發測試結果:")
        print(f"  總請求數: {num_requests}")
        print(f"  成功請求: {successful_requests}")
        print(f"  總時間: {total_time:.3f} 秒")
        print(f"  平均回應時間: {avg_response_time:.3f} 秒")
        print(f"  吞吐量: {num_requests / total_time:.2f} req/s")
        
        assert successful_requests == num_requests
    
    def test_memory_usage(self, sample_request):
        """測試記憶體使用量"""
        process = psutil.Process()
        
        # 記錄初始記憶體
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 執行多次請求
        num_requests = 20
        for _ in range(num_requests):
            client.post("/api/v1/recommendations", json=sample_request)
        
        # 記錄最終記憶體
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"\n記憶體使用:")
        print(f"  初始記憶體: {initial_memory:.2f} MB")
        print(f"  最終記憶體: {final_memory:.2f} MB")
        print(f"  記憶體增加: {memory_increase:.2f} MB")
        
        # 記憶體增加不應超過 100MB
        assert memory_increase < 100, f"記憶體增加 {memory_increase:.2f}MB 過多"
    
    def test_sustained_load(self, sample_request):
        """測試持續負載"""
        duration = 5  # 秒
        request_count = 0
        errors = 0
        
        start_time = time.time()
        end_time = start_time + duration
        
        while time.time() < end_time:
            try:
                response = client.post("/api/v1/recommendations", json=sample_request)
                request_count += 1
                
                if response.status_code not in [200, 503]:
                    errors += 1
            except Exception as e:
                errors += 1
        
        actual_duration = time.time() - start_time
        throughput = request_count / actual_duration
        error_rate = errors / request_count if request_count > 0 else 0
        
        print(f"\n持續負載測試:")
        print(f"  持續時間: {actual_duration:.2f} 秒")
        print(f"  總請求數: {request_count}")
        print(f"  錯誤數: {errors}")
        print(f"  吞吐量: {throughput:.2f} req/s")
        print(f"  錯誤率: {error_rate:.2%}")
        
        assert error_rate < 0.05, f"錯誤率 {error_rate:.2%} 過高"
    
    def test_response_time_percentiles(self, sample_request):
        """測試回應時間百分位數"""
        num_requests = 50
        response_times = []
        
        for _ in range(num_requests):
            start_time = time.time()
            response = client.post("/api/v1/recommendations", json=sample_request)
            end_time = time.time()
            
            if response.status_code in [200, 503]:
                response_times.append(end_time - start_time)
        
        if response_times:
            response_times.sort()
            
            p50 = response_times[int(len(response_times) * 0.50)]
            p95 = response_times[int(len(response_times) * 0.95)]
            p99 = response_times[int(len(response_times) * 0.99)]
            
            print(f"\n回應時間百分位數:")
            print(f"  P50: {p50:.3f} 秒")
            print(f"  P95: {p95:.3f} 秒")
            print(f"  P99: {p99:.3f} 秒")
            
            # P95 應該在 3 秒內
            if any(client.post("/api/v1/recommendations", json=sample_request).status_code == 200 for _ in range(3)):
                assert p95 < 3.0, f"P95 回應時間 {p95:.3f}s 超過 3 秒"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
