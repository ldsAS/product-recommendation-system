# 性能追蹤使用指南

## 概述

性能追蹤系統（Performance Tracker）用於監控推薦系統各個環節的反應時間，幫助識別性能瓶頸並優化用戶體驗。本文檔詳細說明性能追蹤的使用方法和最佳實踐。

## 核心功能

1. **階段追蹤**: 記錄推薦流程中每個階段的耗時
2. **統計分析**: 計算百分位數（P50、P95、P99）
3. **慢查詢檢測**: 自動識別超過閾值的慢查詢
4. **性能報告**: 生成詳細的性能分析報告

---

## 追蹤階段

推薦流程包含以下追蹤階段：

| 階段 | 說明 | 目標耗時 |
|------|------|----------|
| request_received | 請求接收 | - |
| feature_loading | 特徵載入 | < 100ms |
| model_inference | 模型推理 | < 200ms |
| recommendation_merging | 推薦合併 | < 50ms |
| reason_generation | 理由生成 | < 50ms |
| quality_evaluation | 品質評估 | < 50ms |
| response_sent | 回應發送 | - |

**總反應時間目標**:
- P50 < 200ms
- P95 < 500ms
- P99 < 1000ms

---

## 使用方法

### 1. 基本使用

```python
from src.utils.performance_tracker import PerformanceTracker

# 初始化追蹤器
tracker = PerformanceTracker()

# 開始追蹤
request_id = "req_001"
tracker.start_tracking(request_id)

# 記錄各階段
tracker.track_stage(request_id, "feature_loading")
# ... 執行特徵載入 ...

tracker.track_stage(request_id, "model_inference")
# ... 執行模型推理 ...

tracker.track_stage(request_id, "reason_generation")
# ... 生成推薦理由 ...

tracker.track_stage(request_id, "quality_evaluation")
# ... 評估品質 ...

# 結束追蹤
metrics = tracker.end_tracking(request_id)

# 查看結果
print(f"總耗時: {metrics.total_time_ms:.2f}ms")
print(f"是否慢查詢: {metrics.is_slow_query}")
for stage, time_ms in metrics.stage_times.items():
    print(f"  {stage}: {time_ms:.2f}ms")
```

### 2. 在推薦引擎中使用

```python
from src.models.enhanced_recommendation_engine import EnhancedRecommendationEngine

# 推薦引擎自動使用性能追蹤
engine = EnhancedRecommendationEngine()

# 生成推薦（自動追蹤性能）
response = engine.recommend(
    member_info=member_info,
    n=5,
    strategy='hybrid'
)

# 查看性能指標
metrics = response.performance_metrics
print(f"總耗時: {metrics.total_time_ms:.2f}ms")
print(f"特徵載入: {metrics.stage_times['feature_loading']:.2f}ms")
print(f"模型推理: {metrics.stage_times['model_inference']:.2f}ms")
print(f"理由生成: {metrics.stage_times['reason_generation']:.2f}ms")
print(f"品質評估: {metrics.stage_times['quality_evaluation']:.2f}ms")
```

### 3. 獲取統計數據

```python
from datetime import timedelta

# 獲取最近1小時的統計數據
stats = tracker.get_statistics(time_window=timedelta(hours=1))

print(f"總請求數: {stats.total_requests}")
print(f"平均反應時間: {stats.avg_time_ms:.2f}ms")
print(f"P50: {stats.p50_time_ms:.2f}ms")
print(f"P95: {stats.p95_time_ms:.2f}ms")
print(f"P99: {stats.p99_time_ms:.2f}ms")
print(f"慢查詢數: {stats.slow_query_count}")
print(f"慢查詢比例: {stats.slow_query_rate:.1%}")

# 查看各階段平均耗時
print("\n各階段平均耗時:")
for stage, avg_time in stats.stage_avg_times.items():
    print(f"  {stage}: {avg_time:.2f}ms")
```

---

## 性能指標

### PerformanceMetrics 資料結構

```python
@dataclass
class PerformanceMetrics:
    request_id: str              # 請求ID
    total_time_ms: float         # 總耗時（毫秒）
    stage_times: Dict[str, float]  # 各階段耗時
    is_slow_query: bool          # 是否為慢查詢
    timestamp: datetime          # 時間戳記
```

### PerformanceStats 資料結構

```python
@dataclass
class PerformanceStats:
    time_window: timedelta       # 統計時間窗口
    total_requests: int          # 總請求數
    p50_time_ms: float          # P50反應時間
    p95_time_ms: float          # P95反應時間
    p99_time_ms: float          # P99反應時間
    avg_time_ms: float          # 平均反應時間
    slow_query_count: int       # 慢查詢數量
    slow_query_rate: float      # 慢查詢比例
    stage_avg_times: Dict[str, float]  # 各階段平均耗時
    timestamp: datetime         # 統計時間戳記
```

---

## 慢查詢檢測

### 慢查詢定義

當總反應時間超過 P99 閾值（1000ms）時，標記為慢查詢。

### 慢查詢處理流程

```python
# 檢查是否為慢查詢
if metrics.is_slow_query:
    # 記錄警告日誌
    logger.warning(f"慢查詢檢測: {metrics.total_time_ms:.2f}ms")
    
    # 分析各階段耗時
    for stage, time_ms in metrics.stage_times.items():
        if time_ms > STAGE_THRESHOLDS.get(stage, 100):
            logger.warning(f"  瓶頸階段: {stage} ({time_ms:.2f}ms)")
    
    # 觸發告警
    alert = Alert(
        level=AlertLevel.WARNING,
        metric_name="response_time",
        current_value=metrics.total_time_ms,
        threshold_value=1000.0,
        message=f"慢查詢: {metrics.total_time_ms:.2f}ms",
        timestamp=datetime.now()
    )
```

### 慢查詢優化建議

根據瓶頸階段採取不同的優化措施：

| 瓶頸階段 | 可能原因 | 優化建議 |
|----------|----------|----------|
| feature_loading | 資料庫查詢慢 | 添加索引、使用快取 |
| model_inference | 模型複雜度高 | 模型壓縮、批次處理 |
| reason_generation | 理由生成邏輯複雜 | 簡化邏輯、使用模板 |
| quality_evaluation | 評估計算量大 | 優化算法、並行計算 |

---

## 性能閾值配置

### 預設閾值

```python
PERFORMANCE_THRESHOLDS = {
    'total_time_ms': {
        'p50': 200,   # P50目標: 200ms
        'p95': 500,   # P95目標: 500ms
        'p99': 1000   # P99目標: 1000ms
    },
    'feature_loading_ms': {
        'max': 100    # 特徵載入最大耗時: 100ms
    },
    'model_inference_ms': {
        'max': 200    # 模型推理最大耗時: 200ms
    }
}
```

### 自訂閾值

在 `config/recommendation_config.yaml` 中配置：

```yaml
performance_thresholds:
  total_time_ms:
    p50: 200
    p95: 500
    p99: 1000
  feature_loading_ms:
    max: 100
  model_inference_ms:
    max: 200
```

---

## 性能監控

### 1. 通過 API 查詢

```python
import requests

# 獲取即時性能數據
response = requests.get(
    "http://localhost:8000/api/v1/monitoring/realtime",
    params={"time_window_minutes": 60}
)

data = response.json()
perf_metrics = data['performance_metrics']['response_time_ms']

print(f"平均反應時間: {perf_metrics['avg']:.2f}ms")
print(f"P50: {perf_metrics['p50']:.2f}ms")
print(f"P95: {perf_metrics['p95']:.2f}ms")
print(f"P99: {perf_metrics['p99']:.2f}ms")
```

### 2. 通過監控儀表板

訪問 `http://localhost:8000/dashboard` 查看即時性能監控：

- 反應時間趨勢圖
- 各階段耗時佔比
- 慢查詢列表
- 性能告警

---

## 性能優化最佳實踐

### 1. 特徵載入優化

```python
# 使用快取減少資料庫查詢
from functools import lru_cache

@lru_cache(maxsize=1000)
def load_member_features(member_code: str):
    # 載入會員特徵
    return features

# 批次載入
def load_features_batch(member_codes: List[str]):
    # 一次查詢多個會員的特徵
    return features_dict
```

### 2. 模型推理優化

```python
# 批次推理
def predict_batch(features_list: List[np.ndarray]):
    # 批次預測，提高效率
    return model.predict(np.vstack(features_list))

# 模型量化
# 使用量化模型減少計算量
model = lgb.Booster(model_file='model_quantized.txt')
```

### 3. 並行處理

```python
from concurrent.futures import ThreadPoolExecutor

# 並行生成推薦理由
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(generate_reason, rec, member_info)
        for rec in recommendations
    ]
    reasons = [f.result() for f in futures]
```

### 4. 資料庫優化

```sql
-- 添加索引
CREATE INDEX idx_member_code ON transactions(member_code);
CREATE INDEX idx_product_id ON products(product_id);
CREATE INDEX idx_timestamp ON monitoring_records(timestamp);

-- 使用連接池
# 在應用配置中設置連接池大小
pool_size = 20
max_overflow = 10
```

---

## 性能測試

### 1. 單次推薦性能測試

```python
import time

def test_single_recommendation():
    engine = EnhancedRecommendationEngine()
    member_info = create_test_member()
    
    start = time.time()
    response = engine.recommend(member_info, n=5)
    elapsed = (time.time() - start) * 1000
    
    print(f"反應時間: {elapsed:.2f}ms")
    assert elapsed < 500, f"反應時間過長: {elapsed:.2f}ms"
```

### 2. 並發性能測試

```python
from concurrent.futures import ThreadPoolExecutor
import numpy as np

def test_concurrent_recommendations(num_requests=100):
    engine = EnhancedRecommendationEngine()
    
    def make_request():
        member_info = create_test_member()
        start = time.time()
        response = engine.recommend(member_info, n=5)
        return (time.time() - start) * 1000
    
    # 並發執行
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(num_requests)]
        response_times = [f.result() for f in futures]
    
    # 統計結果
    p50 = np.percentile(response_times, 50)
    p95 = np.percentile(response_times, 95)
    p99 = np.percentile(response_times, 99)
    
    print(f"並發請求數: {num_requests}")
    print(f"P50: {p50:.2f}ms")
    print(f"P95: {p95:.2f}ms")
    print(f"P99: {p99:.2f}ms")
    
    assert p95 < 500, f"P95反應時間過長: {p95:.2f}ms"
```

### 3. 負載測試

```python
def test_load(duration_seconds=60, qps=100):
    """
    負載測試
    
    Args:
        duration_seconds: 測試持續時間（秒）
        qps: 每秒查詢數
    """
    engine = EnhancedRecommendationEngine()
    start_time = time.time()
    request_count = 0
    response_times = []
    
    while time.time() - start_time < duration_seconds:
        batch_start = time.time()
        
        # 發送一批請求
        for _ in range(qps):
            member_info = create_test_member()
            req_start = time.time()
            response = engine.recommend(member_info, n=5)
            response_times.append((time.time() - req_start) * 1000)
            request_count += 1
        
        # 控制 QPS
        elapsed = time.time() - batch_start
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
    
    # 統計結果
    print(f"總請求數: {request_count}")
    print(f"平均 QPS: {request_count / duration_seconds:.1f}")
    print(f"P50: {np.percentile(response_times, 50):.2f}ms")
    print(f"P95: {np.percentile(response_times, 95):.2f}ms")
    print(f"P99: {np.percentile(response_times, 99):.2f}ms")
```

---

## 性能分析工具

### 1. 使用 cProfile

```python
import cProfile
import pstats

def profile_recommendation():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # 執行推薦
    engine = EnhancedRecommendationEngine()
    response = engine.recommend(member_info, n=5)
    
    profiler.disable()
    
    # 輸出統計
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # 顯示前20個最耗時的函數
```

### 2. 使用 line_profiler

```python
# 安裝: pip install line_profiler

# 在函數上添加裝飾器
@profile
def recommend(self, member_info, n=5):
    # 推薦邏輯
    pass

# 執行: kernprof -l -v script.py
```

### 3. 使用 memory_profiler

```python
# 安裝: pip install memory_profiler

from memory_profiler import profile

@profile
def recommend(self, member_info, n=5):
    # 推薦邏輯
    pass

# 執行: python -m memory_profiler script.py
```

---

## 常見問題

### Q1: 為什麼反應時間突然變慢？

A: 可能原因：
1. 資料庫連接數不足
2. 模型載入到記憶體失敗
3. 系統資源不足（CPU、記憶體）
4. 網路延遲

建議檢查系統資源使用情況和日誌。

### Q2: 如何降低 P99 反應時間？

A: 優化建議：
1. 使用快取減少資料庫查詢
2. 優化慢查詢（添加索引）
3. 使用批次處理
4. 增加系統資源

### Q3: 慢查詢比例多少算正常？

A: 建議慢查詢比例 < 1%。如果超過 5%，需要立即優化。

### Q4: 如何監控生產環境性能？

A: 建議：
1. 使用監控儀表板實時查看
2. 設置告警（P95 > 500ms 時告警）
3. 定期查看性能報告
4. 記錄慢查詢日誌

---

## 參考資料

- [API 文檔](API_DOCUMENTATION.md)
- [推薦可參考價值評估文檔](REFERENCE_VALUE_EVALUATION.md)
- [監控儀表板使用指南](MONITORING_DASHBOARD_GUIDE.md)
- [性能優化實施報告](../TASK_13_2_PERFORMANCE_TEST_REPORT.md)
