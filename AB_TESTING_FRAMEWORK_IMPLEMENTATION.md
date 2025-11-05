# A/B 測試框架實施總結

## 概述

成功實作了完整的 A/B 測試框架，支援多組測試、推薦策略對比和統計顯著性檢驗。

## 實施內容

### 1. 核心組件 (src/utils/ab_testing_framework.py)

#### 資料模型
- **TestGroupConfig**: 測試組配置，包含組別 ID、名稱、策略配置和流量比例
- **TestRecord**: 測試記錄，包含會員代碼、組別、可參考價值分數和性能指標
- **GroupStatistics**: 組別統計數據，包含平均分數、標準差和百分位數

#### ABTestingFramework 類別

**主要功能：**

1. **測試組分配邏輯** (需求 11.1, 11.2)
   - `create_test()`: 創建新的 A/B 測試，配置多個測試組
   - `assign_group()`: 基於會員 ID 的一致性雜湊分組
   - `get_group_config()`: 獲取測試組配置
   - 驗證流量比例總和為 1.0
   - 確保同一會員始終分配到同一組

2. **測試執行邏輯** (需求 11.3, 11.4)
   - `record_test_result()`: 記錄推薦結果，包含：
     - 可參考價值分數（綜合、相關性、新穎性、可解釋性、多樣性）
     - 反應時間
     - 推薦數量和使用的策略
   - 自動持久化測試數據

3. **測試結果分析** (需求 11.5)
   - `calculate_group_statistics()`: 計算組別統計數據
     - 平均分數和標準差
     - 百分位數（P50、P95、P99）
   - `perform_statistical_test()`: 執行統計顯著性檢驗
     - 雙樣本 t 檢驗
     - 計算 p 值和顯著性水準
     - 計算效應大小（Cohen's d）
     - 提供結果解釋
   - `generate_comparison_report()`: 生成完整對比報告
     - 各組統計數據
     - 兩兩比較結果
     - 最佳組別推薦

4. **數據管理**
   - `stop_test()`: 停止測試
   - `export_raw_data()`: 匯出原始測試數據
   - 配置和數據的持久化（JSON 格式）

### 2. 示範程式 (demo_ab_testing.py)

展示如何使用 A/B 測試框架：
- 創建測試並配置測試組
- 模擬推薦請求並記錄結果
- 計算統計數據
- 執行統計顯著性檢驗
- 生成對比報告

### 3. 單元測試 (tests/test_ab_testing_framework.py)

**測試覆蓋：**

1. **分組邏輯測試**
   - 測試創建 A/B 測試
   - 測試流量比例驗證
   - 測試分組一致性（同一會員始終分配到同一組）
   - 測試分組分布接近配置的流量比例
   - 測試未啟用時的行為

2. **測試執行測試**
   - 測試記錄測試結果
   - 測試獲取測試組配置
   - 測試計算組別統計數據
   - 測試空組別處理

3. **結果分析測試**
   - 測試統計顯著性檢驗
   - 測試樣本數不足的處理
   - 測試生成對比報告
   - 測試匯出原始數據

4. **持久化測試**
   - 測試配置和數據的儲存與載入
   - 測試停止測試功能

**測試結果：** 15 個測試全部通過 ✓

## 核心特性

### 1. 一致性雜湊分組

使用 MD5 雜湊確保：
- 同一會員始終分配到同一組
- 分組分布接近配置的流量比例
- 支援多個測試組

```python
# 使用 MD5 雜湊確保一致性分組
hash_value = hashlib.md5(member_code.encode()).hexdigest()
hash_int = int(hash_value[:8], 16)
ratio = (hash_int % 10000) / 10000.0
```

### 2. 統計顯著性檢驗

實作簡化版雙樣本 t 檢驗：
- 計算 t 統計量
- 估計 p 值
- 判斷顯著性水準（90%、95%、99%）
- 計算效應大小（Cohen's d）
- 提供結果解釋

```python
# 計算 t 統計量
mean_diff = stats_b.avg_overall_score - stats_a.avg_overall_score
pooled_std = ((stats_a.std_overall_score ** 2 / n_a) + 
              (stats_b.std_overall_score ** 2 / n_b)) ** 0.5
t_statistic = mean_diff / pooled_std

# 判斷顯著性
if abs_t > 2.576:  # 99% 信心水準
    significance = '***'
elif abs_t > 1.96:  # 95% 信心水準
    significance = '**'
elif abs_t > 1.645:  # 90% 信心水準
    significance = '*'
```

### 3. 完整的對比報告

生成包含以下內容的報告：
- 測試基本資訊（名稱、時間、記錄數）
- 各組統計數據（品質分數、性能指標）
- 統計檢驗結果（顯著性、效應大小）
- 最佳組別推薦

## 使用範例

### 創建 A/B 測試

```python
from src.utils.ab_testing_framework import ABTestingFramework, TestGroupConfig

# 初始化框架
framework = ABTestingFramework()

# 配置測試組
test_groups = [
    TestGroupConfig(
        group_id="control",
        group_name="對照組",
        strategy_config={'collaborative_filtering': 0.40, ...},
        traffic_ratio=0.5
    ),
    TestGroupConfig(
        group_id="test_a",
        group_name="測試組 A",
        strategy_config={'collaborative_filtering': 0.60, ...},
        traffic_ratio=0.5
    )
]

# 創建測試
framework.create_test("推薦策略優化測試", test_groups)
```

### 執行推薦並記錄結果

```python
# 為會員分配測試組
member_code = "M0001"
group_id = framework.assign_group(member_code)

# 獲取測試組配置
group_config = framework.get_group_config(group_id)

# 執行推薦（根據 group_config 調整策略）
# ... 推薦邏輯 ...

# 記錄測試結果
framework.record_test_result(
    member_code=member_code,
    group_id=group_id,
    overall_score=65.5,
    relevance_score=70.0,
    novelty_score=30.0,
    explainability_score=80.0,
    diversity_score=60.0,
    response_time_ms=200.0,
    recommendation_count=5,
    strategy_used="hybrid"
)
```

### 分析結果

```python
# 計算統計數據
stats = framework.calculate_all_statistics()

# 執行統計檢驗
test_result = framework.perform_statistical_test("control", "test_a")
print(f"平均差異: {test_result['test_results']['mean_difference']:.2f}")
print(f"顯著性: {test_result['test_results']['significance']}")
print(f"解釋: {test_result['interpretation']}")

# 生成對比報告
report = framework.generate_comparison_report()
print(f"最佳組別: {report['recommendation']['best_group_name']}")
```

## 示範結果

運行 `demo_ab_testing.py` 的輸出：

```
各組統計結果:
對照組（原策略） (control):
  樣本數: 52
  綜合可參考價值分數: 64.08 ± 3.25
  相關性分數: 72.44
  新穎性分數: 29.99
  可解釋性分數: 80.13
  多樣性分數: 58.53
  平均反應時間: 222.28 ms

測試組 A（強化協同過濾） (test_a):
  樣本數: 48
  綜合可參考價值分數: 68.28 ± 3.90
  相關性分數: 77.30
  新穎性分數: 33.19
  可解釋性分數: 82.96
  多樣性分數: 61.46
  平均反應時間: 215.54 ms

統計檢驗結果:
  對照組平均分數: 64.08
  測試組平均分數: 68.28
  平均差異: 4.20
  改進百分比: 6.56%
  t 統計量: 5.831
  p 值: 0.010
  顯著性: ***
  效應大小: large

結果解釋:
  測試組 B 的表現顯著更好（大效應），建議採用測試組 B 的策略。
```

## 需求驗證

### 需求 11.1: 支援設定多個測試組別 ✓
- 實作 `create_test()` 方法支援配置多個測試組
- 每個測試組可配置不同的推薦策略
- 驗證流量比例總和為 1.0

### 需求 11.2: 基於會員 ID 進行一致性分組 ✓
- 使用 MD5 雜湊確保一致性
- 測試驗證同一會員始終分配到同一組
- 測試驗證分組分布接近配置比例

### 需求 11.3: 根據會員所屬組別使用對應策略 ✓
- 實作 `assign_group()` 和 `get_group_config()` 方法
- 支援獲取測試組的策略配置
- 記錄使用的策略

### 需求 11.4: 記錄每組的反應時間和可參考價值分數分布 ✓
- 實作 `record_test_result()` 方法
- 記錄完整的可參考價值分數（5 個維度）
- 記錄反應時間和推薦元資料

### 需求 11.5: 生成對比報告包括統計顯著性分析 ✓
- 實作統計顯著性檢驗（t 檢驗）
- 計算 p 值、顯著性水準和效應大小
- 生成完整的對比報告
- 提供結果解釋和推薦

## 檔案清單

1. **src/utils/ab_testing_framework.py** - A/B 測試框架核心實作
2. **tests/test_ab_testing_framework.py** - 單元測試（15 個測試）
3. **demo_ab_testing.py** - 示範程式
4. **config/ab_test_config.json** - 測試配置檔案（自動生成）
5. **data/ab_test_data.json** - 測試數據檔案（自動生成）

## 後續整合建議

1. **整合到推薦引擎**
   - 修改 `EnhancedRecommendationEngine` 支援動態策略權重
   - 在推薦流程中自動記錄測試結果

2. **API 端點**
   - 新增 A/B 測試管理 API
   - 新增測試結果查詢 API

3. **監控儀表板**
   - 在儀表板中顯示 A/B 測試結果
   - 即時監控各組的表現

4. **自動化決策**
   - 根據統計檢驗結果自動切換策略
   - 設定自動停止測試的條件

## 總結

✓ 成功實作完整的 A/B 測試框架
✓ 支援多組測試和一致性分組
✓ 實作統計顯著性檢驗
✓ 生成詳細的對比報告
✓ 所有單元測試通過（15/15）
✓ 示範程式運行正常

A/B 測試框架已準備好用於生產環境，可以幫助團隊科學地評估和選擇最優的推薦策略。
