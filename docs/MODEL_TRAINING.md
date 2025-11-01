# 模型訓練指南

## 目錄

1. [訓練流程概述](#訓練流程概述)
2. [資料準備](#資料準備)
3. [特徵工程](#特徵工程)
4. [模型訓練](#模型訓練)
5. [模型評估](#模型評估)
6. [模型部署](#模型部署)
7. [進階主題](#進階主題)

## 訓練流程概述

### 完整流程

```
資料載入 → 資料清理 → 特徵工程 → 訓練資料準備 → 模型訓練 → 模型評估 → 模型部署
```

### 訓練腳本

```bash
# 完整訓練流程
python src/train.py

# 指定配置
python src/train.py --config config/training_config.json

# 僅訓練特定模型
python src/train.py --model lightgbm

# 快速訓練（使用較少資料）
python src/train.py --quick
```

## 資料準備

### 資料格式

系統需要三個 CSV 檔案：

#### 1. member.csv - 會員資料

```csv
會員編號,電話,總消費金額,累積紅利,註冊日期
CU000001,0937024682,17400,500,2023-01-15
CU000002,0912345678,25600,800,2023-02-20
```

必要欄位：
- `會員編號`: 唯一識別碼
- `總消費金額`: 數值型，>= 0
- `累積紅利`: 數值型，>= 0

可選欄位：
- `電話`: 字串型
- `註冊日期`: 日期型 (YYYY-MM-DD)

#### 2. sales.csv - 銷售訂單

```csv
訂單編號,會員編號,訂單日期,訂單金額,門市代碼
S000001,CU000001,2024-01-10,1200,STORE01
S000002,CU000001,2024-01-15,800,STORE01
```

必要欄位：
- `訂單編號`: 唯一識別碼
- `會員編號`: 關聯到 member.csv
- `訂單日期`: 日期型 (YYYY-MM-DD)
- `訂單金額`: 數值型，>= 0

#### 3. salesdetails.csv - 訂單明細

```csv
訂單編號,產品ID,產品名稱,數量,單價,小計
S000001,30469,杏輝蓉憶記膠囊,2,600,1200
S000002,31033,健康產品B,1,800,800
```

必要欄位：
- `訂單編號`: 關聯到 sales.csv
- `產品ID`: 產品唯一識別碼
- `數量`: 整數型，> 0
- `單價`: 數值型，>= 0

### 資料載入

```python
from src.data_processing.data_loader import DataLoader

# 建立資料載入器
loader = DataLoader(data_dir='data/raw')

# 載入資料
member_df = loader.load_member_data()
sales_df = loader.load_sales_data()
details_df = loader.load_salesdetails_data()

# 合併資料
merged_df = loader.merge_all_data()
print(f"合併後資料: {len(merged_df)} 筆記錄")
```

### 資料清理

```python
from src.data_processing.data_cleaner import DataCleaner

# 建立資料清理器
cleaner = DataCleaner()

# 清理資料
cleaned_df = cleaner.clean(merged_df)

# 檢查清理結果
print(f"清理前: {len(merged_df)} 筆")
print(f"清理後: {len(cleaned_df)} 筆")
print(f"移除: {len(merged_df) - len(cleaned_df)} 筆")
```

清理步驟包括：
1. 移除重複記錄
2. 處理缺失值
3. 修正異常值
4. 統一日期格式
5. 標準化文字編碼

## 特徵工程

### RFM 特徵

```python
from src.data_processing.feature_engineer import FeatureEngineer

# 建立特徵工程器
engineer = FeatureEngineer()

# 計算 RFM 特徵
member_features = engineer.calculate_rfm_features(
    sales_df,
    reference_date='2024-12-31'
)

print("RFM 特徵:")
print(member_features[['member_code', 'recency', 'frequency', 'monetary']].head())
```

RFM 特徵說明：
- **Recency (R)**: 最近一次購買距今天數
- **Frequency (F)**: 購買訂單次數
- **Monetary (M)**: 平均訂單金額

### 產品偏好特徵

```python
# 提取產品偏好
product_features = engineer.extract_product_preferences(
    details_df,
    top_n=5
)

print("產品偏好特徵:")
print(product_features[['member_code', 'favorite_products', 'product_diversity']].head())
```

產品偏好特徵：
- `favorite_products`: 最常購買的產品 ID 列表
- `product_diversity`: 購買不同產品的數量
- `avg_items_per_order`: 平均每單商品數

### 時間模式特徵

```python
# 提取時間模式
time_features = engineer.extract_time_patterns(sales_df)

print("時間模式特徵:")
print(time_features[['member_code', 'purchase_hour_preference', 'purchase_day_preference']].head())
```

時間模式特徵：
- `purchase_hour_preference`: 偏好購買時段 (0-23)
- `purchase_day_preference`: 偏好購買星期 (0-6)
- `days_since_last_purchase`: 距離上次購買天數

### 完整特徵矩陣

```python
# 建立完整特徵矩陣
feature_matrix = engineer.build_feature_matrix(
    member_df,
    sales_df,
    details_df
)

print(f"特徵矩陣形狀: {feature_matrix.shape}")
print(f"特徵數量: {feature_matrix.shape[1]}")
print("\n特徵列表:")
print(feature_matrix.columns.tolist())
```

## 模型訓練

### 訓練資料準備

```python
from src.models.training_data_builder import TrainingDataBuilder

# 建立訓練資料建構器
builder = TrainingDataBuilder()

# 建立訓練樣本
X_train, y_train, X_val, y_val, X_test, y_test = builder.build_training_data(
    feature_matrix,
    test_size=0.2,
    val_size=0.1,
    random_state=42
)

print(f"訓練集: {X_train.shape}")
print(f"驗證集: {X_val.shape}")
print(f"測試集: {X_test.shape}")
```

### LightGBM 模型

```python
from src.models.ml_recommender import MLRecommender

# 建立推薦器
recommender = MLRecommender(model_type='lightgbm')

# 訓練模型
recommender.train(
    X_train, y_train,
    X_val, y_val,
    params={
        'num_leaves': 31,
        'learning_rate': 0.05,
        'n_estimators': 100,
        'max_depth': -1,
        'min_child_samples': 20
    }
)

# 儲存模型
recommender.save_model('data/models/lightgbm_v1.0.0.pkl')
```

### 協同過濾模型

```python
from src.models.collaborative_filtering import CollaborativeFiltering

# 建立協同過濾模型
cf_model = CollaborativeFiltering(algorithm='SVD')

# 訓練模型
cf_model.train(
    user_item_matrix,
    params={
        'n_factors': 100,
        'n_epochs': 20,
        'lr_all': 0.005,
        'reg_all': 0.02
    }
)

# 儲存模型
cf_model.save_model('data/models/cf_svd_v1.0.0.pkl')
```

### 混合模型

```python
# 組合多個模型
from src.models.recommendation_engine import RecommendationEngine

engine = RecommendationEngine()

# 載入多個模型
engine.load_model('lightgbm', 'data/models/lightgbm_v1.0.0.pkl')
engine.load_model('cf', 'data/models/cf_svd_v1.0.0.pkl')

# 設置權重
engine.set_weights({
    'lightgbm': 0.6,
    'cf': 0.4
})
```

## 模型評估

### 評估指標

```python
from src.models.model_evaluator import ModelEvaluator

# 建立評估器
evaluator = ModelEvaluator()

# 評估模型
metrics = evaluator.evaluate(
    model=recommender,
    X_test=X_test,
    y_test=y_test,
    k=5  # Top-5 推薦
)

print("評估指標:")
print(f"Accuracy: {metrics.accuracy:.4f}")
print(f"Precision@5: {metrics.precision_at_5:.4f}")
print(f"Recall@5: {metrics.recall_at_5:.4f}")
print(f"NDCG@5: {metrics.ndcg_at_5:.4f}")
print(f"F1 Score: {metrics.f1_score:.4f}")
```

### 指標說明

#### 1. Precision@K
衡量推薦列表中相關項目的比例。

```
Precision@K = (推薦列表中相關項目數) / K
```

#### 2. Recall@K
衡量推薦列表覆蓋了多少相關項目。

```
Recall@K = (推薦列表中相關項目數) / (總相關項目數)
```

#### 3. NDCG@K
考慮排名位置的評估指標，排名越前的相關項目權重越高。

```
NDCG@K = DCG@K / IDCG@K
```

#### 4. MAP@K
平均精確率，綜合考慮精確率和召回率。

### 交叉驗證

```python
from sklearn.model_selection import cross_val_score

# 5 折交叉驗證
scores = cross_val_score(
    recommender.model,
    X_train,
    y_train,
    cv=5,
    scoring='accuracy'
)

print(f"交叉驗證分數: {scores}")
print(f"平均分數: {scores.mean():.4f} (+/- {scores.std() * 2:.4f})")
```

### 特徵重要性分析

```python
# 獲取特徵重要性
feature_importance = recommender.get_feature_importance()

# 顯示前 10 個重要特徵
print("\n前 10 個重要特徵:")
for feature, importance in feature_importance[:10]:
    print(f"{feature}: {importance:.4f}")

# 視覺化
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.barh(
    [f[0] for f in feature_importance[:10]],
    [f[1] for f in feature_importance[:10]]
)
plt.xlabel('重要性')
plt.title('特徵重要性 Top 10')
plt.tight_layout()
plt.savefig('feature_importance.png')
```

## 模型部署

### 儲存模型

```python
from src.models.model_manager import ModelManager

# 建立模型管理器
manager = ModelManager(models_dir='data/models')

# 儲存模型和元資料
manager.save_model(
    model=recommender.model,
    version='v1.0.0',
    model_type='lightgbm',
    metrics=metrics,
    feature_names=feature_matrix.columns.tolist(),
    description='基於 LightGBM 的產品推薦模型'
)
```

### 載入模型

```python
# 載入最新模型
model, metadata = manager.load_latest_model()

print(f"模型版本: {metadata.version}")
print(f"模型類型: {metadata.model_type}")
print(f"訓練時間: {metadata.trained_at}")
print(f"準確率: {metadata.metrics.accuracy:.4f}")
```

### 版本管理

```python
# 列出所有模型版本
versions = manager.list_versions()
print("可用模型版本:")
for version in versions:
    print(f"  - {version}")

# 載入特定版本
model, metadata = manager.load_model('v1.0.0')

# 設置當前版本
manager.set_current_version('v1.0.0')
```

## 進階主題

### 超參數調優

```python
from sklearn.model_selection import GridSearchCV

# 定義參數網格
param_grid = {
    'num_leaves': [31, 50, 70],
    'learning_rate': [0.01, 0.05, 0.1],
    'n_estimators': [50, 100, 200],
    'max_depth': [-1, 10, 20]
}

# 網格搜索
grid_search = GridSearchCV(
    recommender.model,
    param_grid,
    cv=5,
    scoring='accuracy',
    n_jobs=-1,
    verbose=2
)

grid_search.fit(X_train, y_train)

print("最佳參數:")
print(grid_search.best_params_)
print(f"最佳分數: {grid_search.best_score_:.4f}")
```

### 增量學習

```python
# 載入現有模型
model, metadata = manager.load_latest_model()

# 使用新資料進行增量訓練
recommender.model = model
recommender.incremental_train(
    X_new, y_new,
    n_iterations=10
)

# 儲存更新後的模型
manager.save_model(
    model=recommender.model,
    version='v1.0.1',
    model_type='lightgbm',
    metrics=new_metrics,
    description='增量訓練更新'
)
```

### 模型融合

```python
from sklearn.ensemble import VotingClassifier

# 建立投票分類器
ensemble = VotingClassifier(
    estimators=[
        ('lgb', lightgbm_model),
        ('xgb', xgboost_model),
        ('rf', random_forest_model)
    ],
    voting='soft',
    weights=[0.5, 0.3, 0.2]
)

# 訓練融合模型
ensemble.fit(X_train, y_train)

# 評估
ensemble_metrics = evaluator.evaluate(ensemble, X_test, y_test)
print(f"融合模型準確率: {ensemble_metrics.accuracy:.4f}")
```

### 自動化訓練流程

```python
# 建立訓練管道
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('feature_selection', SelectKBest(k=50)),
    ('classifier', recommender.model)
])

# 訓練管道
pipeline.fit(X_train, y_train)

# 儲存管道
import joblib
joblib.dump(pipeline, 'data/models/pipeline_v1.0.0.pkl')
```

### 監控模型效能

```python
from src.utils.metrics import PerformanceTracker

# 建立效能追蹤器
tracker = PerformanceTracker()

# 追蹤預測效能
for member_code, features in test_data:
    start_time = time.time()
    predictions = model.predict(features)
    response_time = (time.time() - start_time) * 1000
    
    tracker.track_recommendation(
        member_code=member_code,
        num_recommendations=len(predictions),
        response_time_ms=response_time,
        model_version='v1.0.0'
    )

# 獲取效能指標
metrics = tracker.get_recommendation_metrics('v1.0.0')
print(f"平均回應時間: {metrics['response_time']['avg_ms']:.2f} ms")
```

## 最佳實踐

### 1. 資料品質

- 定期檢查資料完整性
- 處理異常值和缺失值
- 保持資料格式一致
- 記錄資料清理過程

### 2. 特徵工程

- 嘗試多種特徵組合
- 分析特徵重要性
- 移除冗餘特徵
- 標準化數值特徵

### 3. 模型訓練

- 使用交叉驗證
- 調優超參數
- 防止過擬合
- 記錄訓練過程

### 4. 模型評估

- 使用多個評估指標
- 在測試集上評估
- 分析錯誤案例
- 比較不同模型

### 5. 模型部署

- 版本控制
- 記錄元資料
- 監控效能
- 定期更新

## 故障排除

### 訓練失敗

**問題**: 訓練過程中出現錯誤

**解決方法**:
1. 檢查資料格式
2. 確認記憶體充足
3. 調整批次大小
4. 查看錯誤日誌

### 效能不佳

**問題**: 模型準確率低於預期

**解決方法**:
1. 增加訓練資料
2. 改進特徵工程
3. 調整模型參數
4. 嘗試不同模型

### 過擬合

**問題**: 訓練集表現好，測試集表現差

**解決方法**:
1. 增加正則化
2. 減少模型複雜度
3. 使用更多訓練資料
4. 應用 Dropout

---

**文檔版本**: v1.0.0  
**最後更新**: 2025-01-15  
**維護者**: 資料科學團隊
