"""
增強推薦系統資料模型
定義推薦可參考價值、性能追蹤、監控記錄等相關資料結構
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ============================================================================
# 列舉類型
# ============================================================================

class AlertLevel(str, Enum):
    """告警等級"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class QualityLevel(str, Enum):
    """品質等級"""
    EXCELLENT = "excellent"  # 綜合分數 >= 80
    GOOD = "good"            # 綜合分數 >= 60
    ACCEPTABLE = "acceptable"  # 綜合分數 >= 40
    POOR = "poor"            # 綜合分數 < 40


class RecommendationStage(str, Enum):
    """推薦流程階段"""
    REQUEST_RECEIVED = "request_received"
    FEATURE_LOADING = "feature_loading"
    MODEL_INFERENCE = "model_inference"
    RECOMMENDATION_MERGING = "recommendation_merging"
    REASON_GENERATION = "reason_generation"
    QUALITY_EVALUATION = "quality_evaluation"
    RESPONSE_SENT = "response_sent"


# ============================================================================
# 性能追蹤相關資料模型
# ============================================================================

class PerformanceMetrics(BaseModel):
    """性能指標"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    request_id: str = Field(..., description="請求ID")
    total_time_ms: float = Field(..., description="總耗時（毫秒）")
    stage_times: Dict[str, float] = Field(default_factory=dict, description="各階段耗時")
    is_slow_query: bool = Field(default=False, description="是否為慢查詢")
    timestamp: datetime = Field(default_factory=datetime.now, description="時間戳記")
    
    @field_validator('total_time_ms')
    @classmethod
    def validate_total_time(cls, v: float) -> float:
        """驗證總時間必須為正數"""
        if v < 0:
            raise ValueError("時間不能為負數")
        return v
    
    @field_validator('stage_times')
    @classmethod
    def validate_stage_times(cls, v: Dict[str, float]) -> Dict[str, float]:
        """驗證階段時間必須為正數"""
        for key, value in v.items():
            if value < 0:
                raise ValueError(f"時間不能為負數: {key}={value}")
        return v


class PerformanceStats(BaseModel):
    """性能統計"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    time_window: timedelta = Field(..., description="統計時間窗口")
    total_requests: int = Field(..., description="總請求數")
    p50_time_ms: float = Field(..., description="P50反應時間")
    p95_time_ms: float = Field(..., description="P95反應時間")
    p99_time_ms: float = Field(..., description="P99反應時間")
    avg_time_ms: float = Field(..., description="平均反應時間")
    slow_query_count: int = Field(..., description="慢查詢數量")
    slow_query_rate: float = Field(..., description="慢查詢比例")
    stage_avg_times: Dict[str, float] = Field(default_factory=dict, description="各階段平均耗時")
    timestamp: datetime = Field(default_factory=datetime.now, description="統計時間戳記")


# ============================================================================
# 推薦可參考價值相關資料模型
# ============================================================================

class ReferenceValueScore(BaseModel):
    """推薦可參考價值分數"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    overall_score: float = Field(..., ge=0, le=100, description="綜合分數 (0-100)")
    relevance_score: float = Field(..., ge=0, le=100, description="相關性分數")
    novelty_score: float = Field(..., ge=0, le=100, description="新穎性分數")
    explainability_score: float = Field(..., ge=0, le=100, description="可解釋性分數")
    diversity_score: float = Field(..., ge=0, le=100, description="多樣性分數")
    score_breakdown: Dict[str, Any] = Field(default_factory=dict, description="詳細分數拆解")
    timestamp: datetime = Field(default_factory=datetime.now, description="時間戳記")
    
    @field_validator('overall_score', 'relevance_score', 'novelty_score', 'explainability_score', 'diversity_score')
    @classmethod
    def validate_score_range(cls, v: float) -> float:
        """驗證分數範圍在 0-100 之間"""
        if not 0 <= v <= 100:
            raise ValueError(f"分數必須在 0-100 之間，當前值: {v}")
        return v


class MemberHistory(BaseModel):
    """會員歷史資料"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    member_code: str = Field(..., description="會員編號")
    purchased_products: List[str] = Field(default_factory=list, description="已購買產品ID列表")
    purchased_categories: List[str] = Field(default_factory=list, description="已購買產品類別列表")
    purchased_brands: List[str] = Field(default_factory=list, description="已購買品牌列表")
    avg_purchase_price: float = Field(0.0, ge=0, description="平均購買價格")
    price_std: float = Field(0.0, ge=0, description="購買價格標準差")
    browsed_products: List[str] = Field(default_factory=list, description="瀏覽過的產品ID列表")


# ============================================================================
# 品質監控相關資料模型
# ============================================================================

class MonitoringRecord(BaseModel):
    """監控記錄"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    request_id: str = Field(..., description="請求ID")
    member_code: str = Field(..., description="會員編號")
    timestamp: datetime = Field(default_factory=datetime.now, description="時間戳記")
    
    # 品質指標
    overall_score: float = Field(..., ge=0, le=100, description="綜合可參考價值分數")
    relevance_score: float = Field(..., ge=0, le=100, description="相關性分數")
    novelty_score: float = Field(..., ge=0, le=100, description="新穎性分數")
    explainability_score: float = Field(..., ge=0, le=100, description="可解釋性分數")
    diversity_score: float = Field(..., ge=0, le=100, description="多樣性分數")
    
    # 性能指標
    total_time_ms: float = Field(..., ge=0, description="總反應時間（毫秒）")
    feature_loading_ms: float = Field(0.0, ge=0, description="特徵載入時間（毫秒）")
    model_inference_ms: float = Field(0.0, ge=0, description="模型推理時間（毫秒）")
    reason_generation_ms: float = Field(0.0, ge=0, description="理由生成時間（毫秒）")
    quality_evaluation_ms: float = Field(0.0, ge=0, description="品質評估時間（毫秒）")
    
    # 推薦元資料
    recommendation_count: int = Field(..., ge=0, description="推薦數量")
    strategy_used: str = Field(..., description="使用的推薦策略")
    is_degraded: bool = Field(default=False, description="是否使用降級策略")


class QualityCheckResult(BaseModel):
    """品質檢查結果"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    passed: bool = Field(..., description="是否通過檢查")
    overall_score: float = Field(..., description="綜合分數")
    failed_metrics: List[str] = Field(default_factory=list, description="未達標的指標列表")
    warnings: List[str] = Field(default_factory=list, description="警告訊息列表")
    timestamp: datetime = Field(default_factory=datetime.now, description="檢查時間")


class PerformanceCheckResult(BaseModel):
    """性能檢查結果"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    passed: bool = Field(..., description="是否通過檢查")
    total_time_ms: float = Field(..., description="總反應時間")
    failed_metrics: List[str] = Field(default_factory=list, description="未達標的指標列表")
    warnings: List[str] = Field(default_factory=list, description="警告訊息列表")
    timestamp: datetime = Field(default_factory=datetime.now, description="檢查時間")


class Alert(BaseModel):
    """告警"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    level: AlertLevel = Field(..., description="告警等級")
    metric_name: str = Field(..., description="指標名稱")
    current_value: float = Field(..., description="當前值")
    threshold_value: float = Field(..., description="閾值")
    message: str = Field(..., description="告警訊息")
    timestamp: datetime = Field(default_factory=datetime.now, description="告警時間")


class MonitoringReport(BaseModel):
    """監控報告"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    report_type: str = Field(..., description="報告類型（hourly/daily）")
    start_time: datetime = Field(..., description="報告開始時間")
    end_time: datetime = Field(..., description="報告結束時間")
    
    # 推薦量統計
    total_recommendations: int = Field(..., description="總推薦次數")
    unique_members: int = Field(..., description="唯一會員數")
    avg_recommendations_per_member: float = Field(..., description="每會員平均推薦次數")
    
    # 品質統計
    avg_overall_score: float = Field(..., description="平均綜合分數")
    avg_relevance_score: float = Field(..., description="平均相關性分數")
    avg_novelty_score: float = Field(..., description="平均新穎性分數")
    avg_explainability_score: float = Field(..., description="平均可解釋性分數")
    avg_diversity_score: float = Field(..., description="平均多樣性分數")
    
    # 性能統計
    avg_response_time_ms: float = Field(..., description="平均反應時間")
    p50_response_time_ms: float = Field(..., description="P50反應時間")
    p95_response_time_ms: float = Field(..., description="P95反應時間")
    p99_response_time_ms: float = Field(..., description="P99反應時間")
    
    # 異常統計
    total_alerts: int = Field(..., description="總告警數")
    critical_alerts: int = Field(..., description="嚴重告警數")
    warning_alerts: int = Field(..., description="警告數")
    degradation_count: int = Field(..., description="降級次數")
    
    # 趨勢分析
    score_trend: str = Field(..., description="分數趨勢（improving/stable/declining）")
    performance_trend: str = Field(..., description="性能趨勢（improving/stable/declining）")
    
    # 建議
    recommendations_for_improvement: List[str] = Field(default_factory=list, description="改進建議")
    
    timestamp: datetime = Field(default_factory=datetime.now, description="報告生成時間")
