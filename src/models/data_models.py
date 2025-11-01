"""
資料模型定義
使用 Pydantic 定義所有資料結構，提供類型檢查和驗證
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator, ConfigDict


# ============================================================================
# 列舉類型
# ============================================================================

class ModelType(str, Enum):
    """模型類型"""
    LIGHTGBM = "lightgbm"
    XGBOOST = "xgboost"
    COLLABORATIVE_FILTERING = "collaborative_filtering"
    HYBRID = "hybrid"


class RecommendationSource(str, Enum):
    """推薦來源"""
    ML_MODEL = "ml_model"
    COLLABORATIVE_FILTERING = "collaborative_filtering"
    CONTENT_BASED = "content_based"
    RULE_BASED = "rule_based"
    FALLBACK = "fallback"


# ============================================================================
# 會員相關模型
# ============================================================================

class MemberFeatures(BaseModel):
    """會員特徵向量"""
    model_config = ConfigDict(from_attributes=True)
    
    # 基礎資訊
    member_code: str = Field(..., description="會員編號")
    phone: Optional[str] = Field(None, description="電話號碼")
    
    # 消費統計
    total_consumption: float = Field(0.0, ge=0, description="總消費金額")
    accumulated_bonus: float = Field(0.0, ge=0, description="累積紅利")
    
    # RFM 特徵
    recency: int = Field(0, ge=0, description="最近一次購買距今天數")
    frequency: int = Field(0, ge=0, description="購買訂單次數")
    monetary: float = Field(0.0, ge=0, description="平均訂單金額")
    
    # 產品偏好
    favorite_products: List[str] = Field(default_factory=list, description="最常購買的產品ID列表")
    product_diversity: int = Field(0, ge=0, description="購買不同產品的數量")
    avg_items_per_order: float = Field(0.0, ge=0, description="平均每單商品數")
    
    # 時間模式
    days_since_last_purchase: int = Field(0, ge=0, description="距離上次購買天數")
    purchase_hour_preference: Optional[int] = Field(None, ge=0, le=23, description="偏好購買時段")
    purchase_day_preference: Optional[int] = Field(None, ge=0, le=6, description="偏好購買星期")
    
    # 地點偏好
    preferred_location: Optional[str] = Field(None, description="偏好購買地點")
    
    # 會員年齡
    member_age_days: int = Field(0, ge=0, description="會員註冊天數")


class MemberInfo(BaseModel):
    """會員基本資訊（用於 API 請求）"""
    model_config = ConfigDict(from_attributes=True)
    
    member_code: str = Field(..., description="會員編號", min_length=1)
    phone: Optional[str] = Field(None, description="電話號碼")
    total_consumption: float = Field(0.0, ge=0, description="總消費金額")
    accumulated_bonus: float = Field(0.0, ge=0, description="累積紅利")
    recent_purchases: List[str] = Field(default_factory=list, description="最近購買的產品ID列表")
    
    @validator('phone')
    def validate_phone(cls, v):
        """驗證電話號碼格式"""
        if v and not v.replace('-', '').replace(' ', '').isdigit():
            raise ValueError('電話號碼格式不正確')
        return v


# ============================================================================
# 產品相關模型
# ============================================================================

class Product(BaseModel):
    """產品資訊"""
    model_config = ConfigDict(from_attributes=True)
    
    stock_id: str = Field(..., description="產品ID")
    stock_description: str = Field(..., description="產品名稱/描述")
    category: Optional[str] = Field(None, description="產品類別")
    avg_price: float = Field(0.0, ge=0, description="平均價格")
    popularity_score: float = Field(0.0, ge=0, le=1, description="熱門度分數 (0-1)")
    
    # 額外資訊
    total_sales: int = Field(0, ge=0, description="總銷售數量")
    unique_buyers: int = Field(0, ge=0, description="不重複購買人數")


class ProductFeatures(BaseModel):
    """產品特徵向量"""
    model_config = ConfigDict(from_attributes=True)
    
    stock_id: str = Field(..., description="產品ID")
    avg_price: float = Field(0.0, ge=0, description="平均價格")
    popularity_score: float = Field(0.0, ge=0, le=1, description="熱門度分數")
    total_sales: int = Field(0, ge=0, description="總銷售數量")
    unique_buyers: int = Field(0, ge=0, description="不重複購買人數")
    avg_quantity_per_order: float = Field(0.0, ge=0, description="平均每單購買數量")


# ============================================================================
# 推薦相關模型
# ============================================================================

class Recommendation(BaseModel):
    """推薦結果"""
    model_config = ConfigDict(from_attributes=True)
    
    product_id: str = Field(..., description="產品ID")
    product_name: str = Field(..., description="產品名稱")
    confidence_score: float = Field(..., ge=0, le=100, description="推薦信心分數 (0-100)")
    explanation: str = Field(..., description="推薦理由")
    rank: int = Field(..., ge=1, le=5, description="推薦排名 (1-5)")
    
    # 額外資訊
    source: RecommendationSource = Field(RecommendationSource.ML_MODEL, description="推薦來源")
    raw_score: Optional[float] = Field(None, description="原始模型分數")


class RecommendationRequest(BaseModel):
    """推薦請求"""
    model_config = ConfigDict(from_attributes=True)
    
    member_code: str = Field(..., description="會員編號", min_length=1)
    phone: Optional[str] = Field(None, description="電話號碼")
    total_consumption: float = Field(0.0, ge=0, description="總消費金額")
    accumulated_bonus: float = Field(0.0, ge=0, description="累積紅利")
    recent_purchases: List[str] = Field(default_factory=list, description="最近購買的產品ID列表")
    
    # 可選參數
    top_k: Optional[int] = Field(5, ge=1, le=20, description="推薦產品數量")
    min_confidence: Optional[float] = Field(0.0, ge=0, le=100, description="最低信心分數")
    
    @validator('phone')
    def validate_phone(cls, v):
        """驗證電話號碼格式"""
        if v and not v.replace('-', '').replace(' ', '').isdigit():
            raise ValueError('電話號碼格式不正確')
        return v


class RecommendationResponse(BaseModel):
    """推薦回應"""
    model_config = ConfigDict(from_attributes=True)
    
    recommendations: List[Recommendation] = Field(..., description="推薦列表")
    response_time_ms: float = Field(..., ge=0, description="回應時間（毫秒）")
    model_version: str = Field(..., description="模型版本")
    request_id: Optional[str] = Field(None, description="請求ID")
    
    # 元資料
    member_code: str = Field(..., description="會員編號")
    timestamp: datetime = Field(default_factory=datetime.now, description="時間戳記")


# ============================================================================
# 訓練相關模型
# ============================================================================

class TrainingSample(BaseModel):
    """訓練樣本"""
    model_config = ConfigDict(from_attributes=True)
    
    member_id: str = Field(..., description="會員ID")
    product_id: str = Field(..., description="產品ID")
    label: int = Field(..., ge=0, le=1, description="標籤 (1: 購買, 0: 未購買)")
    
    # 特徵
    member_features: Dict[str, Any] = Field(default_factory=dict, description="會員特徵")
    product_features: Dict[str, Any] = Field(default_factory=dict, description="產品特徵")
    
    # 時間資訊
    timestamp: Optional[datetime] = Field(None, description="時間戳記")


class ModelMetrics(BaseModel):
    """模型評估指標"""
    model_config = ConfigDict(from_attributes=True)
    
    # 基礎指標
    accuracy: float = Field(..., ge=0, le=1, description="準確率")
    precision: float = Field(..., ge=0, le=1, description="精確率")
    recall: float = Field(..., ge=0, le=1, description="召回率")
    f1_score: float = Field(..., ge=0, le=1, description="F1 分數")
    
    # 推薦指標
    precision_at_5: float = Field(..., ge=0, le=1, description="Precision@5")
    recall_at_5: float = Field(..., ge=0, le=1, description="Recall@5")
    ndcg_at_5: float = Field(..., ge=0, le=1, description="NDCG@5")
    map_at_5: Optional[float] = Field(None, ge=0, le=1, description="MAP@5")
    
    # 額外資訊
    auc: Optional[float] = Field(None, ge=0, le=1, description="AUC")
    log_loss: Optional[float] = Field(None, ge=0, description="Log Loss")


class ModelMetadata(BaseModel):
    """模型元資料"""
    model_config = ConfigDict(from_attributes=True)
    
    version: str = Field(..., description="模型版本")
    model_type: ModelType = Field(..., description="模型類型")
    trained_at: datetime = Field(..., description="訓練時間")
    
    # 訓練資訊
    training_samples: int = Field(..., ge=0, description="訓練樣本數")
    validation_samples: int = Field(..., ge=0, description="驗證樣本數")
    test_samples: int = Field(..., ge=0, description="測試樣本數")
    
    # 效能指標
    metrics: ModelMetrics = Field(..., description="評估指標")
    
    # 特徵資訊
    feature_names: List[str] = Field(default_factory=list, description="特徵名稱列表")
    feature_importance: Optional[Dict[str, float]] = Field(None, description="特徵重要性")
    
    # 訓練配置
    hyperparameters: Dict[str, Any] = Field(default_factory=dict, description="超參數")
    
    # 額外資訊
    description: Optional[str] = Field(None, description="模型描述")
    tags: List[str] = Field(default_factory=list, description="標籤")


# ============================================================================
# API 相關模型
# ============================================================================

class HealthCheckResponse(BaseModel):
    """健康檢查回應"""
    model_config = ConfigDict(from_attributes=True)
    
    status: str = Field(..., description="狀態")
    model_loaded: bool = Field(..., description="模型是否已載入")
    uptime_seconds: float = Field(..., ge=0, description="運行時間（秒）")
    timestamp: datetime = Field(default_factory=datetime.now, description="時間戳記")


class ModelInfoResponse(BaseModel):
    """模型資訊回應"""
    model_config = ConfigDict(from_attributes=True)
    
    model_version: str = Field(..., description="模型版本")
    model_type: str = Field(..., description="模型類型")
    trained_at: datetime = Field(..., description="訓練時間")
    metrics: ModelMetrics = Field(..., description="評估指標")
    
    # 統計資訊
    total_products: int = Field(..., ge=0, description="產品總數")
    total_members: int = Field(..., ge=0, description="會員總數")
    
    # 額外資訊
    description: Optional[str] = Field(None, description="模型描述")


class ErrorResponse(BaseModel):
    """錯誤回應"""
    model_config = ConfigDict(from_attributes=True)
    
    error: str = Field(..., description="錯誤類型")
    message: str = Field(..., description="錯誤訊息")
    detail: Optional[str] = Field(None, description="詳細資訊")
    timestamp: datetime = Field(default_factory=datetime.now, description="時間戳記")
    request_id: Optional[str] = Field(None, description="請求ID")


# ============================================================================
# 日誌相關模型
# ============================================================================

class RecommendationLog(BaseModel):
    """推薦日誌"""
    model_config = ConfigDict(from_attributes=True)
    
    request_id: str = Field(..., description="請求ID")
    member_code: str = Field(..., description="會員編號")
    recommendations: List[Recommendation] = Field(..., description="推薦列表")
    response_time_ms: float = Field(..., ge=0, description="回應時間（毫秒）")
    model_version: str = Field(..., description="模型版本")
    timestamp: datetime = Field(default_factory=datetime.now, description="時間戳記")
    
    # 額外資訊
    user_agent: Optional[str] = Field(None, description="User Agent")
    ip_address: Optional[str] = Field(None, description="IP 地址")


class ConversionLog(BaseModel):
    """轉換日誌"""
    model_config = ConfigDict(from_attributes=True)
    
    request_id: str = Field(..., description="請求ID")
    member_code: str = Field(..., description="會員編號")
    product_id: str = Field(..., description="產品ID")
    converted: bool = Field(..., description="是否轉換")
    timestamp: datetime = Field(default_factory=datetime.now, description="時間戳記")
    
    # 額外資訊
    conversion_value: Optional[float] = Field(None, ge=0, description="轉換價值")
    notes: Optional[str] = Field(None, description="備註")


# ============================================================================
# A/B 測試相關模型
# ============================================================================

class ABTestConfig(BaseModel):
    """A/B 測試配置"""
    model_config = ConfigDict(from_attributes=True)
    
    enabled: bool = Field(False, description="是否啟用")
    model_a_version: str = Field(..., description="模型 A 版本")
    model_b_version: str = Field(..., description="模型 B 版本")
    model_a_ratio: float = Field(0.8, ge=0, le=1, description="模型 A 流量比例")
    
    @validator('model_a_ratio')
    def validate_ratio(cls, v):
        """驗證流量比例"""
        if not 0 <= v <= 1:
            raise ValueError('流量比例必須在 0 到 1 之間')
        return v


class ABTestMetrics(BaseModel):
    """A/B 測試指標"""
    model_config = ConfigDict(from_attributes=True)
    
    model_version: str = Field(..., description="模型版本")
    total_requests: int = Field(0, ge=0, description="總請求數")
    total_conversions: int = Field(0, ge=0, description="總轉換數")
    conversion_rate: float = Field(0.0, ge=0, le=1, description="轉換率")
    avg_response_time_ms: float = Field(0.0, ge=0, description="平均回應時間（毫秒）")
    
    # 時間範圍
    start_time: datetime = Field(..., description="開始時間")
    end_time: datetime = Field(..., description="結束時間")


# ============================================================================
# 輔助函數
# ============================================================================

def example_recommendation_request() -> RecommendationRequest:
    """範例推薦請求"""
    return RecommendationRequest(
        member_code="CU000001",
        phone="0937024682",
        total_consumption=17400.0,
        accumulated_bonus=500.0,
        recent_purchases=["30463", "31033"],
        top_k=5,
        min_confidence=0.0
    )


def example_recommendation_response() -> RecommendationResponse:
    """範例推薦回應"""
    return RecommendationResponse(
        recommendations=[
            Recommendation(
                product_id="30469",
                product_name="杏輝蓉憶記膠囊",
                confidence_score=85.5,
                explanation="基於您購買過的蓉憶記系列產品",
                rank=1,
                source=RecommendationSource.ML_MODEL
            ),
            Recommendation(
                product_id="31463",
                product_name="杏輝南極磷蝦油軟膠囊",
                confidence_score=78.2,
                explanation="與您相似的會員也購買了此產品",
                rank=2,
                source=RecommendationSource.COLLABORATIVE_FILTERING
            ),
        ],
        response_time_ms=245.5,
        model_version="v1.0.0",
        member_code="CU000001"
    )


if __name__ == "__main__":
    # 測試資料模型
    print("測試推薦請求模型...")
    request = example_recommendation_request()
    print(f"✓ 推薦請求: {request.member_code}")
    
    print("\n測試推薦回應模型...")
    response = example_recommendation_response()
    print(f"✓ 推薦回應: {len(response.recommendations)} 個推薦")
    
    print("\n測試會員特徵模型...")
    features = MemberFeatures(
        member_code="CU000001",
        total_consumption=17400.0,
        recency=5,
        frequency=10,
        monetary=1740.0
    )
    print(f"✓ 會員特徵: {features.member_code}, RFM=({features.recency}, {features.frequency}, {features.monetary})")
    
    print("\n所有資料模型測試通過！✓")
