# 推薦可參考價值評估器實作總結

## 實作日期
2025-11-04

## 實作內容

### 1. 資料模型 (src/models/enhanced_data_models.py)
新增以下資料模型：
- **ReferenceValueScore**: 推薦可參考價值分數模型
  - overall_score: 綜合分數 (0-100)
  - relevance_score: 相關性分數
  - novelty_score: 新穎性分數
  - explainability_score: 可解釋性分數
  - diversity_score: 多樣性分數
  - score_breakdown: 詳細分數拆解
  
- **MemberHistory**: 會員歷史資料模型
  - purchased_products: 已購買產品列表
  - purchased_categories: 已購買類別列表
  - purchased_brands: 已購買品牌列表
  - avg_purchase_price: 平均購買價格
  - price_std: 購買價格標準差
  - browsed_products: 瀏覽過的產品列表

### 2. 評估器實作 (src/models/reference_value_evaluator.py)

#### 核心類別: ReferenceValueEvaluator

**權重配置**:
- 相關性 (Relevance): 40%
- 新穎性 (Novelty): 25%
- 可解釋性 (Explainability): 20%
- 多樣性 (Diversity): 15%

#### 主要方法:

##### 1. evaluate()
整合評估方法，計算綜合可參考價值分數
- 輸入: 推薦列表、會員資訊、會員歷史、產品資訊
- 輸出: ReferenceValueScore 物件
- 功能: 計算四個維度分數並加權合成綜合分數

##### 2. calculate_relevance()
計算相關性分數 (0-100)
- **購買歷史匹配度** (33%): 基於類別和品牌重疊度
- **瀏覽偏好匹配度** (33%): 基於產品相似度
- **消費水平匹配度** (34%): 使用高斯分布計算價格匹配

##### 3. calculate_novelty()
計算新穎性分數 (0-100)
- **新類別比例** (50%): 未購買過的類別
- **新品牌比例** (30%): 未購買過的品牌
- **新產品比例** (20%): 完全未購買過的產品

##### 4. calculate_explainability()
計算可解釋性分數 (0-100)
- **理由完整性** (40%): 每個推薦都有理由
- **理由相關性** (40%): 理由與會員特徵的匹配度
- **理由多樣性** (20%): 避免所有推薦使用相同理由

##### 5. calculate_diversity()
計算多樣性分數 (0-100)
- **類別多樣性** (40%): 不同類別數量佔比
- **價格多樣性** (30%): 價格分散度 (使用變異係數)
- **品牌多樣性** (30%): 不同品牌數量佔比

### 3. 單元測試 (tests/test_reference_value_evaluator.py)

實作了 16 個測試案例，涵蓋：

#### 基礎測試
- ✓ 評估器初始化
- ✓ 空推薦列表處理
- ✓ 完整評估流程

#### 各維度測試
- ✓ 相關性分數計算
- ✓ 相關性計算 (無產品資訊)
- ✓ 新穎性分數計算
- ✓ 新穎性計算 (全新產品)
- ✓ 可解釋性分數計算
- ✓ 可解釋性計算 (無理由)
- ✓ 多樣性分數計算
- ✓ 多樣性計算 (相同類別)

#### 進階測試
- ✓ 分數拆解結構驗證
- ✓ 加權分數計算驗證
- ✓ 邊界情況處理
- ✓ 理由完整性計算
- ✓ 理由多樣性計算

**測試結果**: 16/16 通過 ✓

## 技術特點

### 1. 靈活的評分機制
- 支援無產品資訊時的降級計算
- 使用中性分數處理缺失資料
- 多層次的分數拆解，便於分析

### 2. 數學模型
- **高斯分布**: 用於消費水平匹配度計算
- **餘弦相似度**: 用於產品相似度計算
- **變異係數**: 用於價格多樣性評估

### 3. 可擴展性
- 清晰的方法分離，易於維護
- 權重可配置，支援動態調整
- 詳細的分數拆解，支援深度分析

## 符合需求

### 需求 6.1-6.5: 推薦可參考價值評估
✓ 計算相關性分數 (基於購買歷史、瀏覽偏好、消費水平)
✓ 計算新穎性分數 (確保推薦包含新產品)
✓ 計算可解釋性分數 (基於理由的清晰度和說服力)
✓ 計算多樣性分數 (確保推薦涵蓋不同類別和價格區間)
✓ 計算綜合可參考價值分數 (加權平均，確保平均分數 > 60分)

### 需求 10.1-10.5: 推薦可參考價值核心指標體系
✓ 相關性分數基於三個維度 (購買歷史、瀏覽偏好、消費水平)
✓ 新穎性分數確保至少 30% 新產品
✓ 可解釋性分數確保每個推薦都有明確理由
✓ 多樣性分數確保推薦涵蓋至少 3 個類別和價格區間
✓ 綜合分數使用加權平均 (相關性 40%、新穎性 25%、可解釋性 20%、多樣性 15%)

## 使用範例

```python
from src.models.reference_value_evaluator import ReferenceValueEvaluator
from src.models.data_models import Recommendation, MemberInfo, Product
from src.models.enhanced_data_models import MemberHistory

# 初始化評估器
evaluator = ReferenceValueEvaluator()

# 準備資料
recommendations = [...]  # 推薦列表
member_info = MemberInfo(...)  # 會員資訊
member_history = MemberHistory(...)  # 會員歷史
products_info = {...}  # 產品資訊字典

# 評估推薦可參考價值
result = evaluator.evaluate(
    recommendations,
    member_info,
    member_history,
    products_info
)

# 查看結果
print(f"綜合分數: {result.overall_score:.1f}")
print(f"相關性: {result.relevance_score:.1f}")
print(f"新穎性: {result.novelty_score:.1f}")
print(f"可解釋性: {result.explainability_score:.1f}")
print(f"多樣性: {result.diversity_score:.1f}")
```

## 下一步

建議接續實作：
- Task 4: 優化推薦理由生成器 (ReasonGenerator)
- Task 5: 實作增強推薦引擎 (EnhancedRecommendationEngine)
- Task 6: 實作品質監控器 (QualityMonitor)

這些組件將與 ReferenceValueEvaluator 整合，形成完整的推薦品質評估系統。
