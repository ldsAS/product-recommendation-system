# 設計文件

## 概述

本系統是一個基於機器學習的產品推薦系統，旨在為銷售員提供智能化的產品推薦工具。系統將分析會員資料、銷售訂單和產品明細，訓練推薦模型，並提供 API 介面讓銷售員輸入顧客資訊後獲得 Top 5 產品推薦。

## 系統架構

### 整體架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                        使用者介面層                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Web UI       │  │ CLI Tool     │  │ REST API     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        應用服務層                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           推薦服務 (Recommendation Service)           │  │
│  │  - 輸入驗證                                           │  │
│  │  - 特徵提取                                           │  │
│  │  - 模型推論                                           │  │
│  │  - 結果排序與解釋                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           模型訓練服務 (Training Service)             │  │
│  │  - 資料載入與清理                                     │  │
│  │  - 特徵工程                                           │  │
│  │  - 模型訓練與評估                                     │  │
│  │  - 模型儲存與版本管理                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        資料處理層                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 資料載入器   │  │ 特徵工程     │  │ 資料驗證     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        資料儲存層                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 原始資料     │  │ 處理後資料   │  │ 模型檔案     │      │
│  │ (JSON Lines) │  │ (Parquet)    │  │ (Pickle)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## 核心組件設計

### 1. 資料處理模組 (Data Processing Module)

#### 1.1 資料載入器 (Data Loader)

**職責**: 讀取原始 JSON Lines 格式的資料檔案

**類別設計**:
```python
class DataLoader:
    def load_members(file_path: str) -> pd.DataFrame
    def load_sales(file_path: str) -> pd.DataFrame
    def load_sales_details(file_path: str) -> pd.DataFrame
    def merge_data() -> pd.DataFrame
```

**資料合併邏輯**:
```
member ← sales (on member.id = sales.member)
       ← salesdetails (on sales.id = salesdetails.sales_id)
```

#### 1.2 資料清理器 (Data Cleaner)

**職責**: 處理缺失值、異常值和資料品質問題

**處理規則**:
- 移除金額為 0 且無產品的訂單
- 填補缺失的會員資訊
- 處理重複記錄
- 統一日期時間格式
- 處理編碼問題 (UTF-8)

**類別設計**:
```python
class DataCleaner:
    def remove_invalid_orders(df: pd.DataFrame) -> pd.DataFrame
    def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame
    def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame
    def standardize_dates(df: pd.DataFrame) -> pd.DataFrame
```

#### 1.3 特徵工程器 (Feature Engineer)

**職責**: 從原始資料中提取和構建特徵

**特徵類別**:

1. **會員基礎特徵**:
   - member_code: 會員編號
   - total_consumption: 總消費金額
   - accumulated_bonus: 累積紅利
   - member_age_days: 會員註冊天數

2. **RFM 特徵**:
   - recency: 最近一次購買距今天數
   - frequency: 購買訂單次數
   - monetary: 平均訂單金額

3. **產品偏好特徵**:
   - favorite_products: 最常購買的前 3 個產品
   - product_diversity: 購買不同產品的數量
   - avg_items_per_order: 平均每單商品數

4. **時間模式特徵**:
   - purchase_hour_preference: 偏好購買時段
   - purchase_day_preference: 偏好購買星期
   - days_since_last_purchase: 距離上次購買天數

5. **地點特徵**:
   - preferred_location: 偏好購買地點 (loccode)

**類別設計**:
```python
class FeatureEngineer:
    def calculate_rfm(df: pd.DataFrame) -> pd.DataFrame
    def extract_product_preferences(df: pd.DataFrame) -> pd.DataFrame
    def extract_time_patterns(df: pd.DataFrame) -> pd.DataFrame
    def create_feature_matrix(df: pd.DataFrame) -> pd.DataFrame
```

### 2. 模型訓練模組 (Model Training Module)

#### 2.1 推薦模型架構

**模型選擇**: 混合推薦系統

**方法 1: 協同過濾 (Collaborative Filtering)**
- 使用 Surprise 庫實現 SVD 或 ALS 算法
- 基於會員-產品交互矩陣
- 適合找出相似會員的購買模式

**方法 2: 內容基礎推薦 (Content-Based)**
- 基於產品特徵相似度
- 使用 TF-IDF 或 Word2Vec 處理產品描述
- 推薦與歷史購買產品相似的商品

**方法 3: 機器學習分類模型 (主要方法)**
- 使用 LightGBM 或 XGBoost
- 預測會員對每個產品的購買機率
- 特徵: 會員特徵 + 產品特徵 + 交互特徵

**模型架構**:
```python
class RecommendationModel:
    def __init__(self):
        self.cf_model = None  # 協同過濾模型
        self.cb_model = None  # 內容基礎模型
        self.ml_model = None  # 機器學習模型
        
    def train_collaborative_filtering(X, y)
    def train_content_based(X, y)
    def train_ml_model(X, y)
    def predict(member_features) -> List[Tuple[product_id, score]]
```

#### 2.2 訓練資料準備

**正樣本**: 會員實際購買的產品
**負樣本**: 會員未購買但其他會員購買的產品 (負採樣)

**資料分割**:
- 訓練集: 70% (2021-2024年資料)
- 驗證集: 15% (2024年後期資料)
- 測試集: 15% (2025年資料)

**類別設計**:
```python
class TrainingDataBuilder:
    def create_interaction_matrix() -> scipy.sparse.csr_matrix
    def generate_negative_samples(ratio: float = 4.0) -> pd.DataFrame
    def split_data(test_size: float = 0.15) -> Tuple[X_train, X_test, y_train, y_test]
```

#### 2.3 模型評估

**評估指標**:
- Precision@5: Top 5 推薦的準確率
- Recall@5: Top 5 推薦的召回率
- NDCG@5: 歸一化折損累積增益
- MAP@5: 平均精度均值

**類別設計**:
```python
class ModelEvaluator:
    def calculate_precision_at_k(y_true, y_pred, k=5) -> float
    def calculate_recall_at_k(y_true, y_pred, k=5) -> float
    def calculate_ndcg_at_k(y_true, y_pred, k=5) -> float
    def evaluate_model(model, X_test, y_test) -> Dict[str, float]
```

### 3. 推薦服務模組 (Recommendation Service Module)

#### 3.1 推薦引擎 (Recommendation Engine)

**職責**: 接收會員資訊，返回 Top 5 產品推薦

**推薦流程**:
```
1. 輸入驗證
2. 特徵提取 (從會員資訊計算特徵)
3. 模型推論 (獲得所有產品的分數)
4. 結果排序 (選取 Top 5)
5. 生成推薦理由
6. 返回結果
```

**類別設計**:
```python
class RecommendationEngine:
    def __init__(self, model_path: str):
        self.model = self.load_model(model_path)
        self.feature_engineer = FeatureEngineer()
        
    def recommend(member_info: Dict) -> List[Recommendation]
    def extract_features(member_info: Dict) -> np.ndarray
    def generate_explanation(member_info: Dict, product: Product) -> str
```

#### 3.2 推薦結果結構

**資料模型**:
```python
@dataclass
class Recommendation:
    product_id: str
    product_name: str
    confidence_score: float  # 0-100
    explanation: str
    rank: int  # 1-5
```

#### 3.3 推薦理由生成器

**規則基礎的解釋**:
- "基於您購買過的 {product_category} 系列產品"
- "與您相似的會員也購買了此產品"
- "此產品與您常購的 {product_name} 搭配效果好"
- "根據您的消費習慣推薦"

**類別設計**:
```python
class ExplanationGenerator:
    def generate_explanation(
        member_features: Dict,
        product: Product,
        reason_type: str
    ) -> str
```

### 4. API 服務模組 (API Service Module)

#### 4.1 REST API 設計

**端點 1: 獲取推薦**
```
POST /api/v1/recommendations
Request Body:
{
    "member_code": "CU000001",
    "phone": "0937024682",
    "total_consumption": 17400,
    "accumulated_bonus": 500,
    "recent_purchases": ["30463", "31033"]
}

Response:
{
    "recommendations": [
        {
            "product_id": "30469",
            "product_name": "杏輝蓉憶記膠囊",
            "confidence_score": 85.5,
            "explanation": "基於您購買過的蓉憶記系列產品",
            "rank": 1
        },
        ...
    ],
    "response_time_ms": 245
}
```

**端點 2: 模型資訊**
```
GET /api/v1/model/info
Response:
{
    "model_version": "v1.0.0",
    "trained_at": "2025-01-15T10:30:00",
    "metrics": {
        "precision_at_5": 0.75,
        "recall_at_5": 0.68,
        "ndcg_at_5": 0.82
    }
}
```

**端點 3: 健康檢查**
```
GET /api/v1/health
Response:
{
    "status": "healthy",
    "model_loaded": true,
    "uptime_seconds": 3600
}
```

#### 4.2 API 實作框架

**技術選擇**: FastAPI (Python)

**原因**:
- 高效能 (基於 Starlette 和 Pydantic)
- 自動生成 API 文件 (Swagger UI)
- 類型檢查和驗證
- 非同步支援

**類別設計**:
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class RecommendationRequest(BaseModel):
    member_code: str
    phone: Optional[str]
    total_consumption: float
    accumulated_bonus: float
    recent_purchases: List[str]

class RecommendationAPI:
    def __init__(self, engine: RecommendationEngine):
        self.app = FastAPI()
        self.engine = engine
        self.setup_routes()
        
    def setup_routes(self)
    def get_recommendations(request: RecommendationRequest)
    def get_model_info()
    def health_check()
```

### 5. 模型管理模組 (Model Management Module)

#### 5.1 模型版本控制

**版本命名規則**: `v{major}.{minor}.{patch}`
- major: 模型架構變更
- minor: 特徵變更或重新訓練
- patch: 小幅調整

**模型儲存結構**:
```
data/models/
├── v1.0.0/
│   ├── model.pkl
│   ├── feature_config.json
│   ├── metadata.json
│   └── metrics.json
├── v1.1.0/
│   └── ...
└── current -> v1.1.0/  (符號連結)
```

**類別設計**:
```python
class ModelManager:
    def save_model(model, version: str, metadata: Dict)
    def load_model(version: str = "current") -> Model
    def list_versions() -> List[str]
    def set_current_version(version: str)
    def compare_versions(v1: str, v2: str) -> Dict
```

#### 5.2 A/B 測試支援

**流量分配**:
- 模型 A: 80% 流量
- 模型 B: 20% 流量

**效能追蹤**:
- 記錄每個請求使用的模型版本
- 追蹤推薦轉換率
- 比較不同版本的效能

**類別設計**:
```python
class ABTestManager:
    def assign_model(user_id: str) -> str  # 返回模型版本
    def log_recommendation(user_id: str, model_version: str, recommendations: List)
    def log_conversion(user_id: str, product_id: str)
    def get_metrics(model_version: str) -> Dict
```

## 資料模型

### 會員特徵向量
```python
MemberFeatures = {
    'member_code': str,
    'total_consumption': float,
    'accumulated_bonus': float,
    'recency': int,
    'frequency': int,
    'monetary': float,
    'favorite_products': List[str],
    'product_diversity': int,
    'avg_items_per_order': float,
    'days_since_last_purchase': int,
    'preferred_location': str
}
```

### 產品資訊
```python
Product = {
    'stock_id': str,
    'stock_description': str,
    'category': str,
    'avg_price': float,
    'popularity_score': float
}
```

### 訓練樣本
```python
TrainingSample = {
    'member_features': MemberFeatures,
    'product_id': str,
    'label': int,  # 1: 購買, 0: 未購買
    'timestamp': datetime
}
```

## 錯誤處理策略

### 1. 輸入驗證錯誤
- 檢查必填欄位
- 驗證資料格式和範圍
- 返回明確的錯誤訊息

### 2. 模型推論錯誤
- 捕獲模型異常
- 使用備用模型或規則基礎推薦
- 記錄錯誤日誌

### 3. 資料異常處理
- 會員資訊不完整: 使用預設值或平均值
- 產品資訊缺失: 從產品目錄補充
- 超出訓練範圍: 使用最近鄰方法

### 4. 效能降級策略
- 快取熱門推薦結果
- 使用簡化模型 (規則基礎)
- 限制並發請求數

**錯誤處理類別**:
```python
class ErrorHandler:
    def handle_validation_error(error: ValidationError) -> Response
    def handle_model_error(error: ModelError) -> Response
    def handle_data_error(error: DataError) -> Response
    def apply_fallback_strategy() -> List[Recommendation]
```

## 測試策略

### 1. 單元測試
- 資料載入和清理功能
- 特徵工程函數
- 推薦邏輯
- API 端點

### 2. 整合測試
- 端到端推薦流程
- 資料庫連接
- 模型載入和推論

### 3. 效能測試
- API 回應時間 (目標: < 3秒)
- 並發請求處理能力
- 記憶體使用量

### 4. 模型測試
- 離線評估指標
- A/B 測試結果
- 推薦品質人工評估

## 部署架構

### 開發環境
```
本地開發機
├── Python 3.9+
├── Jupyter Notebook (資料探索)
└── VS Code / PyCharm
```

### 生產環境 (建議)
```
應用伺服器
├── FastAPI 應用 (Uvicorn)
├── Nginx (反向代理)
└── Docker 容器化

資料儲存
├── 檔案系統 (原始資料、模型)
└── Redis (快取)

監控
├── Prometheus (指標收集)
└── Grafana (視覺化)
```

## 效能優化

### 1. 快取策略
- 快取熱門會員的推薦結果 (TTL: 1小時)
- 快取產品資訊 (TTL: 24小時)
- 使用 Redis 作為快取層

### 2. 模型優化
- 模型量化 (減少模型大小)
- 批次推論 (處理多個請求)
- 特徵預計算 (離線計算部分特徵)

### 3. 資料庫優化
- 建立索引 (member_code, product_id)
- 資料分區 (按時間分區)
- 使用 Parquet 格式 (列式儲存)

## 安全性考量

### 1. 資料隱私
- 會員資料加密儲存
- API 使用 HTTPS
- 敏感資訊脫敏 (電話號碼部分隱藏)

### 2. API 安全
- API Key 認證
- 請求速率限制 (Rate Limiting)
- 輸入驗證和清理

### 3. 模型安全
- 模型檔案訪問控制
- 防止模型逆向工程
- 定期更新和審計

## 監控與日誌

### 1. 應用監控
- API 請求數量和回應時間
- 錯誤率和異常追蹤
- 系統資源使用 (CPU, 記憶體)

### 2. 業務監控
- 推薦轉換率
- Top 推薦產品分布
- 使用者滿意度

### 3. 日誌記錄
- 請求日誌 (輸入、輸出、時間)
- 錯誤日誌 (異常堆疊)
- 模型推論日誌 (特徵、分數)

**日誌格式**:
```json
{
    "timestamp": "2025-01-15T10:30:00Z",
    "request_id": "uuid",
    "member_code": "CU000001",
    "recommendations": [...],
    "response_time_ms": 245,
    "model_version": "v1.0.0"
}
```

## 技術棧總結

**程式語言**: Python 3.9+

**核心函式庫**:
- pandas: 資料處理
- numpy: 數值計算
- scikit-learn: 機器學習基礎
- lightgbm / xgboost: 梯度提升模型
- surprise: 協同過濾

**Web 框架**:
- FastAPI: REST API
- Uvicorn: ASGI 伺服器

**資料儲存**:
- JSON Lines: 原始資料格式
- Parquet: 處理後資料格式
- Pickle: 模型序列化

**開發工具**:
- pytest: 單元測試
- black: 程式碼格式化
- mypy: 類型檢查
- jupyter: 資料探索

## 未來擴展

### 短期 (1-3個月)
- 增加更多特徵 (季節性、促銷活動)
- 實作 A/B 測試框架
- 建立推薦效果儀表板

### 中期 (3-6個月)
- 深度學習模型 (Neural Collaborative Filtering)
- 即時推薦 (串流處理)
- 多目標優化 (轉換率 + 利潤)

### 長期 (6-12個月)
- 個人化推薦解釋
- 跨產品推薦 (Bundle)
- 強化學習優化推薦策略
