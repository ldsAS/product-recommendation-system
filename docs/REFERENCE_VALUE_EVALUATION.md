# 推薦可參考價值評估文檔

## 概述

推薦可參考價值（Reference Value）是衡量推薦結果對用戶決策幫助程度的綜合指標。本文檔詳細說明可參考價值的評估方法、計算公式和使用指南。

## 核心概念

推薦可參考價值評估體系包含四個維度：

1. **相關性（Relevance）**: 推薦產品與會員偏好的匹配程度
2. **新穎性（Novelty）**: 推薦中新產品或新類別的比例
3. **可解釋性（Explainability）**: 推薦理由的清晰度和說服力
4. **多樣性（Diversity）**: 推薦產品在類別、品牌、價格等維度的分散程度

## 評分體系

### 綜合分數計算

綜合可參考價值分數（Overall Score）是四個維度分數的加權平均：

```
Overall Score = Relevance × 40% + Novelty × 25% + Explainability × 20% + Diversity × 15%
```

**權重說明**:
- **相關性（40%）**: 最重要的維度，確保推薦與用戶需求相關
- **新穎性（25%）**: 次重要，避免推薦過於保守
- **可解釋性（20%）**: 幫助用戶理解推薦理由
- **多樣性（15%）**: 提供多樣化選擇

### 品質等級劃分

根據綜合分數劃分品質等級：

| 等級 | 分數範圍 | 說明 |
|------|----------|------|
| Excellent（優秀） | ≥ 80 | 推薦品質優秀，高度相關且多樣化 |
| Good（良好） | 60-79 | 推薦品質良好，符合預期 |
| Acceptable（可接受） | 40-59 | 推薦品質可接受，但有改進空間 |
| Poor（較差） | < 40 | 推薦品質較差，需要優化或降級 |

---

## 維度詳解

### 1. 相關性分數（Relevance Score）

**定義**: 推薦產品與會員偏好的匹配程度

**計算方法**:

相關性分數由三個子維度組成：

```
Relevance = Purchase History Match × 33% + Browsing Preference Match × 33% + Consumption Level Match × 34%
```

#### 1.1 購買歷史匹配度（Purchase History Match）

評估推薦產品與會員購買歷史的匹配程度。

**計算公式**:

```
Purchase History Match = (Category Match Ratio × 50% + Brand Match Ratio × 50%)

其中:
- Category Match Ratio = 推薦中匹配歷史類別的產品數 / 推薦總數
- Brand Match Ratio = 推薦中匹配歷史品牌的產品數 / 推薦總數
```

**範例**:

假設會員購買過「保健」和「美妝」類別的產品，推薦5個產品：
- 3個屬於「保健」類別
- 1個屬於「美妝」類別
- 1個屬於「食品」類別（新類別）

```
Category Match Ratio = 4/5 = 0.8
假設 Brand Match Ratio = 0.6
Purchase History Match = (0.8 × 0.5 + 0.6 × 0.5) = 0.7
```

#### 1.2 瀏覽偏好匹配度（Browsing Preference Match）

評估推薦產品與會員瀏覽偏好的相似度。

**計算方法**:

對每個推薦產品，計算其與會員瀏覽過的產品的最大相似度，然後取平均值。

**產品相似度計算**:

```
Product Similarity = Category Similarity × 60% + Price Similarity × 40%

其中:
- Category Similarity = 1（類別相同）或 0（類別不同）
- Price Similarity = max(0, 1 - |price1 - price2| / max(price1, price2))
```

#### 1.3 消費水平匹配度（Consumption Level Match）

評估推薦產品價格與會員消費水平的匹配程度。

**計算方法**:

使用高斯分布計算價格匹配分數：

```
Consumption Level Match = exp(-(price_diff²) / (2 × price_std²))

其中:
- price_diff = |產品價格 - 會員平均消費|
- price_std = 會員消費價格標準差
```

**解釋**: 產品價格越接近會員平均消費，匹配分數越高。

---

### 2. 新穎性分數（Novelty Score）

**定義**: 推薦中新產品或新類別的比例

**計算方法**:

```
Novelty = New Category Ratio × 50% + New Brand Ratio × 30% + New Product Ratio × 20%
```

#### 2.1 新類別比例（New Category Ratio）

```
New Category Ratio = 推薦中新類別產品數 / 推薦總數
```

**範例**: 推薦5個產品，其中2個屬於會員未購買過的新類別
```
New Category Ratio = 2/5 = 0.4 = 40%
```

#### 2.2 新品牌比例（New Brand Ratio）

```
New Brand Ratio = 推薦中新品牌產品數 / 推薦總數
```

#### 2.3 新產品比例（New Product Ratio）

```
New Product Ratio = 推薦中完全未購買過的產品數 / 推薦總數
```

**目標值**: 新穎性分數建議保持在 30% 左右，既能提供新選擇，又不會過於激進。

---

### 3. 可解釋性分數（Explainability Score）

**定義**: 推薦理由的清晰度和說服力

**計算方法**:

```
Explainability = Reason Completeness × 40% + Reason Relevance × 40% + Reason Diversity × 20%
```

#### 3.1 理由完整性（Reason Completeness）

```
Reason Completeness = 有理由的推薦數 / 推薦總數
```

**要求**: 每個推薦都應該有明確的理由。

#### 3.2 理由相關性（Reason Relevance）

評估理由與會員特徵的相關度。

**評估方法**: 檢查理由中是否包含相關關鍵詞：
- 購買、偏好、喜愛、消費、品牌、類別
- 相似、適合、推薦、選擇、健康、美容

**計分規則**:
- 包含 1 個關鍵詞: 0.5 分
- 包含 2 個或以上關鍵詞: 1.0 分

#### 3.3 理由多樣性（Reason Diversity）

```
Reason Diversity = 不重複理由數 / 理由總數
```

**要求**: 避免所有推薦使用相同理由。

**範例**:

5個推薦的理由：
- "基於您購買過的蓉憶記系列產品"
- "符合您的高端消費偏好"
- "基於您購買過的蓉憶記系列產品"（重複）
- "適合您的品質要求"
- "維護健康的好選擇"

```
不重複理由數 = 4
Reason Diversity = 4/5 = 0.8 = 80%
```

---

### 4. 多樣性分數（Diversity Score）

**定義**: 推薦產品在類別、品牌、價格等維度的分散程度

**計算方法**:

```
Diversity = Category Diversity × 40% + Price Diversity × 30% + Brand Diversity × 30%
```

#### 4.1 類別多樣性（Category Diversity）

```
Category Diversity = 不同類別數 / min(推薦總數, 總類別數)
```

**範例**: 推薦5個產品，涵蓋3個不同類別
```
Category Diversity = 3/5 = 0.6 = 60%
```

#### 4.2 價格多樣性（Price Diversity）

使用變異係數（Coefficient of Variation）衡量價格分散度：

```
Price Diversity = min(1.0, CV / 0.5)

其中:
CV = 價格標準差 / 價格平均值
```

**解釋**: CV > 0.5 表示高度多樣性，得分 1.0。

**範例**: 推薦產品價格為 [100, 150, 200, 250, 300]
```
平均價格 = 200
標準差 = 70.7
CV = 70.7 / 200 = 0.354
Price Diversity = 0.354 / 0.5 = 0.708 = 70.8%
```

#### 4.3 品牌多樣性（Brand Diversity）

```
Brand Diversity = 不同品牌數 / min(推薦總數, 總品牌數)
```

---

## 使用指南

### 1. 評估推薦品質

```python
from src.models.reference_value_evaluator import ReferenceValueEvaluator
from src.models.enhanced_data_models import MemberHistory

# 初始化評估器
evaluator = ReferenceValueEvaluator()

# 準備會員歷史資料
member_history = MemberHistory(
    member_code="CU000001",
    purchased_products=["30469", "30470"],
    purchased_categories=["保健", "美妝"],
    purchased_brands=["杏輝", "台塑"],
    avg_purchase_price=500.0,
    price_std=150.0
)

# 評估推薦
score = evaluator.evaluate(
    recommendations=recommendations,
    member_info=member_info,
    member_history=member_history,
    products_info=products_dict
)

# 查看結果
print(f"綜合分數: {score.overall_score:.1f}")
print(f"相關性: {score.relevance_score:.1f}")
print(f"新穎性: {score.novelty_score:.1f}")
print(f"可解釋性: {score.explainability_score:.1f}")
print(f"多樣性: {score.diversity_score:.1f}")
```

### 2. 解讀分數拆解

```python
# 查看詳細分數拆解
breakdown = score.score_breakdown

for dimension, details in breakdown.items():
    print(f"{dimension}:")
    print(f"  分數: {details['score']:.1f}")
    print(f"  權重: {details['weight']:.1%}")
    print(f"  貢獻: {details['contribution']:.1f}")
```

### 3. 品質閾值檢查

```python
from src.utils.quality_monitor import QualityMonitor

monitor = QualityMonitor()

# 檢查品質是否達標
result = monitor.check_quality_threshold(score)

if result.passed:
    print("✓ 品質檢查通過")
else:
    print("✗ 品質檢查未通過")
    for metric in result.failed_metrics:
        print(f"  - {metric}")
```

---

## 優化建議

### 提升相關性分數

1. **加強特徵工程**: 提取更多會員偏好特徵
2. **優化模型訓練**: 使用更多歷史資料訓練模型
3. **個性化理由**: 根據會員特徵生成更相關的推薦理由

### 提升新穎性分數

1. **增加探索比例**: 在推薦中加入更多新產品
2. **多樣性推薦**: 使用多樣性推薦策略
3. **冷啟動處理**: 對新產品給予更多曝光機會

### 提升可解釋性分數

1. **豐富理由模板**: 擴展推薦理由模板庫
2. **理由個性化**: 根據會員特徵選擇最相關的理由
3. **理由多樣化**: 避免使用重複的推薦理由

### 提升多樣性分數

1. **類別平衡**: 確保推薦涵蓋多個產品類別
2. **價格分散**: 推薦不同價格區間的產品
3. **品牌多樣**: 避免推薦過多相同品牌的產品

---

## 閾值配置

### 品質閾值

```python
QUALITY_THRESHOLDS = {
    'overall_score': {
        'critical': 40,  # 低於40分觸發嚴重告警
        'warning': 50,   # 低於50分觸發警告
        'target': 60     # 目標值
    },
    'relevance_score': {
        'critical': 50,
        'warning': 60,
        'target': 70
    },
    'novelty_score': {
        'critical': 15,
        'warning': 20,
        'target': 30
    },
    'explainability_score': {
        'critical': 60,
        'warning': 70,
        'target': 80
    },
    'diversity_score': {
        'critical': 40,
        'warning': 50,
        'target': 60
    }
}
```

### 調整閾值

可以在 `config/recommendation_config.yaml` 中調整閾值：

```yaml
quality_thresholds:
  overall_score:
    critical: 40
    warning: 50
    target: 60
  relevance_score:
    target: 70
  novelty_score:
    target: 30
  explainability_score:
    target: 80
  diversity_score:
    target: 60
```

---

## 常見問題

### Q1: 為什麼相關性分數很高但綜合分數不高？

A: 綜合分數是四個維度的加權平均。即使相關性分數很高（權重40%），如果其他維度分數較低，綜合分數也會受影響。建議檢查新穎性、可解釋性和多樣性分數。

### Q2: 新穎性分數應該設置多高？

A: 建議保持在 30% 左右。過高的新穎性可能導致推薦與用戶偏好不符，過低則推薦過於保守。

### Q3: 如何提高可解釋性分數？

A: 確保每個推薦都有理由，理由中包含相關關鍵詞，並避免使用重複的理由。

### Q4: 多樣性分數低怎麼辦？

A: 檢查推薦是否集中在少數類別或品牌，可以調整推薦策略權重，增加多樣性推薦的比例。

---

## 參考資料

- [API 文檔](API_DOCUMENTATION.md)
- [性能追蹤使用指南](PERFORMANCE_TRACKING_GUIDE.md)
- [監控儀表板使用指南](MONITORING_DASHBOARD_GUIDE.md)
- [設計文檔](.kiro/specs/recommendation-improvement/design.md)
