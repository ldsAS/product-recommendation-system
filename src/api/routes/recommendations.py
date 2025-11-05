"""
推薦 API 端點
實作 POST /api/v1/recommendations，整合推薦引擎和輸入驗證
"""
import time
import uuid
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse

from src.models.data_models import (
    RecommendationRequest,
    RecommendationResponse,
    ErrorResponse,
    ModelInfoResponse,
    MemberInfo
)
from src.models.recommendation_engine import RecommendationEngine
from src.models.enhanced_recommendation_engine import EnhancedRecommendationEngine
from src.utils.validators import validate_recommendation_request
from src.utils.quality_monitor import QualityMonitor
from src.config import settings

logger = logging.getLogger(__name__)

# 建立路由器
router = APIRouter(
    prefix="/api/v1",
    tags=["Recommendations"]
)

# 全域推薦引擎實例（延遲初始化）
_recommendation_engine: Optional[RecommendationEngine] = None
_enhanced_recommendation_engine: Optional[EnhancedRecommendationEngine] = None
_quality_monitor: Optional[QualityMonitor] = None


def get_recommendation_engine() -> RecommendationEngine:
    """
    獲取推薦引擎實例（單例模式）
    
    Returns:
        RecommendationEngine: 推薦引擎實例
        
    Raises:
        HTTPException: 如果推薦引擎初始化失敗
    """
    global _recommendation_engine
    
    if _recommendation_engine is None:
        try:
            logger.info("初始化推薦引擎...")
            _recommendation_engine = RecommendationEngine()
            logger.info("✓ 推薦引擎初始化完成")
        except FileNotFoundError as e:
            logger.error(f"推薦引擎初始化失敗: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "model_not_found",
                    "message": "推薦模型未找到，請先訓練模型",
                    "detail": str(e)
                }
            )
        except Exception as e:
            logger.error(f"推薦引擎初始化失敗: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "initialization_error",
                    "message": "推薦引擎初始化失敗",
                    "detail": str(e)
                }
            )
    
    return _recommendation_engine


def get_enhanced_recommendation_engine() -> EnhancedRecommendationEngine:
    """
    獲取增強推薦引擎實例（單例模式）
    
    Returns:
        EnhancedRecommendationEngine: 增強推薦引擎實例
        
    Raises:
        HTTPException: 如果推薦引擎初始化失敗
    """
    global _enhanced_recommendation_engine
    
    if _enhanced_recommendation_engine is None:
        try:
            logger.info("初始化增強推薦引擎...")
            _enhanced_recommendation_engine = EnhancedRecommendationEngine()
            logger.info("✓ 增強推薦引擎初始化完成")
        except FileNotFoundError as e:
            logger.error(f"增強推薦引擎初始化失敗: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "model_not_found",
                    "message": "推薦模型未找到，請先訓練模型",
                    "detail": str(e)
                }
            )
        except Exception as e:
            logger.error(f"增強推薦引擎初始化失敗: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "initialization_error",
                    "message": "增強推薦引擎初始化失敗",
                    "detail": str(e)
                }
            )
    
    return _enhanced_recommendation_engine


def get_quality_monitor() -> QualityMonitor:
    """
    獲取品質監控器實例（單例模式）
    
    Returns:
        QualityMonitor: 品質監控器實例
    """
    global _quality_monitor
    
    if _quality_monitor is None:
        logger.info("初始化品質監控器...")
        _quality_monitor = QualityMonitor()
        logger.info("✓ 品質監控器初始化完成")
    
    return _quality_monitor


@router.post(
    "/recommendations",
    status_code=status.HTTP_200_OK,
    summary="獲取產品推薦",
    description="根據會員資訊返回 Top K 產品推薦，包含可參考價值分數和性能指標",
    responses={
        200: {
            "description": "成功返回推薦結果",
            "content": {
                "application/json": {
                    "example": {
                        "recommendations": [
                            {
                                "product_id": "30469",
                                "product_name": "杏輝蓉憶記膠囊",
                                "confidence_score": 85.5,
                                "explanation": "基於您購買過的蓉憶記系列產品",
                                "rank": 1,
                                "source": "ml_model",
                                "raw_score": 0.855
                            }
                        ],
                        "reference_value_score": {
                            "overall_score": 65.2,
                            "relevance_score": 72.5,
                            "novelty_score": 32.1,
                            "explainability_score": 85.3,
                            "diversity_score": 58.7,
                            "score_breakdown": {}
                        },
                        "performance_metrics": {
                            "request_id": "req_CU000001_1234567890",
                            "total_time_ms": 245.5,
                            "stage_times": {
                                "feature_loading": 45.2,
                                "model_inference": 120.3,
                                "reason_generation": 35.1,
                                "quality_evaluation": 44.9
                            },
                            "is_slow_query": False
                        },
                        "response_time_ms": 245.5,
                        "model_version": "v1.0.0",
                        "request_id": "550e8400-e29b-41d4-a716-446655440000",
                        "member_code": "CU000001",
                        "timestamp": "2025-01-15T10:30:00",
                        "quality_level": "good",
                        "is_degraded": False
                    }
                }
            }
        },
        400: {
            "description": "請求驗證失敗",
            "model": ErrorResponse
        },
        500: {
            "description": "伺服器內部錯誤",
            "model": ErrorResponse
        },
        503: {
            "description": "服務不可用（模型未載入）",
            "model": ErrorResponse
        }
    }
)
async def get_recommendations(
    request: RecommendationRequest,
    http_request: Request,
    use_enhanced: bool = True
) -> dict:
    """
    獲取產品推薦
    
    根據會員資訊返回 Top K 產品推薦，包含推薦理由、信心分數、可參考價值分數和性能指標。
    
    Args:
        request: 推薦請求，包含會員資訊和推薦參數
        http_request: HTTP 請求物件
        use_enhanced: 是否使用增強推薦引擎（包含可參考價值評估和性能追蹤）
        
    Returns:
        dict: 推薦回應，包含推薦列表、可參考價值分數、性能指標和元資料
        
    Raises:
        HTTPException: 如果驗證失敗或推薦生成失敗
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    logger.info(f"[{request_id}] 收到推薦請求: 會員 {request.member_code}")
    
    try:
        # 1. 驗證請求
        logger.debug(f"[{request_id}] 驗證請求...")
        validation_result = validate_recommendation_request(request)
        
        if not validation_result.is_valid:
            logger.warning(
                f"[{request_id}] 請求驗證失敗: {len(validation_result.errors)} 個錯誤"
            )
            
            error_response = ErrorResponse(
                error="validation_error",
                message="請求資料驗證失敗",
                detail=validation_result.errors,
                timestamp=datetime.now(),
                request_id=request_id
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response.model_dump()
            )
        
        logger.debug(f"[{request_id}] ✓ 請求驗證通過")
        
        # 2. 轉換為 MemberInfo
        member_info = MemberInfo(
            member_code=request.member_code,
            phone=request.phone,
            total_consumption=request.total_consumption,
            accumulated_bonus=request.accumulated_bonus,
            recent_purchases=request.recent_purchases
        )
        
        # 3. 根據參數選擇推薦引擎
        if use_enhanced:
            # 使用增強推薦引擎（包含可參考價值評估和性能追蹤）
            logger.debug(f"[{request_id}] 使用增強推薦引擎...")
            enhanced_engine = get_enhanced_recommendation_engine()
            quality_monitor = get_quality_monitor()
            
            # 生成增強推薦
            enhanced_response = enhanced_engine.recommend(
                member_info=member_info,
                n=request.top_k or settings.TOP_K_RECOMMENDATIONS,
                strategy='hybrid'
            )
            
            # 過濾低信心分數的推薦
            recommendations = enhanced_response.recommendations
            if request.min_confidence and request.min_confidence > 0:
                recommendations = [
                    rec for rec in recommendations
                    if rec.confidence_score >= request.min_confidence
                ]
                logger.debug(
                    f"[{request_id}] 過濾後剩餘 {len(recommendations)} 個推薦"
                )
            
            # 記錄到品質監控器
            quality_monitor.record_recommendation(
                request_id=enhanced_response.performance_metrics.request_id,
                member_code=member_info.member_code,
                value_score=enhanced_response.reference_value_score,
                performance_metrics=enhanced_response.performance_metrics,
                recommendation_count=len(recommendations),
                strategy_used=enhanced_response.strategy_used,
                is_degraded=enhanced_response.is_degraded
            )
            
            # 觸發告警（如果需要）
            alerts = quality_monitor.trigger_alerts(
                value_score=enhanced_response.reference_value_score,
                performance_metrics=enhanced_response.performance_metrics
            )
            
            if alerts:
                logger.warning(f"[{request_id}] 觸發 {len(alerts)} 個告警")
                for alert in alerts:
                    logger.warning(f"  [{alert.level.value}] {alert.message}")
            
            # 構建回應（包含新的欄位，同時保持向後兼容）
            response_dict = {
                # 原有欄位（向後兼容）
                "recommendations": [
                    {
                        "product_id": rec.product_id,
                        "product_name": rec.product_name,
                        "confidence_score": rec.confidence_score,
                        "explanation": rec.explanation,
                        "rank": rec.rank,
                        "source": rec.source.value,
                        "raw_score": rec.raw_score
                    }
                    for rec in recommendations
                ],
                "response_time_ms": enhanced_response.performance_metrics.total_time_ms,
                "model_version": enhanced_response.model_version,
                "request_id": request_id,
                "member_code": member_info.member_code,
                "timestamp": enhanced_response.timestamp.isoformat(),
                
                # 新增欄位
                "reference_value_score": {
                    "overall_score": enhanced_response.reference_value_score.overall_score,
                    "relevance_score": enhanced_response.reference_value_score.relevance_score,
                    "novelty_score": enhanced_response.reference_value_score.novelty_score,
                    "explainability_score": enhanced_response.reference_value_score.explainability_score,
                    "diversity_score": enhanced_response.reference_value_score.diversity_score,
                    "score_breakdown": enhanced_response.reference_value_score.score_breakdown
                },
                "performance_metrics": {
                    "request_id": enhanced_response.performance_metrics.request_id,
                    "total_time_ms": enhanced_response.performance_metrics.total_time_ms,
                    "stage_times": enhanced_response.performance_metrics.stage_times,
                    "is_slow_query": enhanced_response.performance_metrics.is_slow_query
                },
                "quality_level": enhanced_response.quality_level.value,
                "is_degraded": enhanced_response.is_degraded
            }
            
            logger.info(
                f"[{request_id}] ✓ 增強推薦生成完成: {len(recommendations)} 個推薦, "
                f"回應時間: {enhanced_response.performance_metrics.total_time_ms:.2f}ms, "
                f"品質等級: {enhanced_response.quality_level.value}"
            )
            
            return response_dict
            
        else:
            # 使用原有推薦引擎（向後兼容）
            logger.debug(f"[{request_id}] 使用原有推薦引擎...")
            engine = get_recommendation_engine()
            
            # 生成推薦
            recommendations = engine.recommend(
                member_info=member_info,
                n=request.top_k or settings.TOP_K_RECOMMENDATIONS
            )
            
            # 過濾低信心分數的推薦
            if request.min_confidence and request.min_confidence > 0:
                recommendations = [
                    rec for rec in recommendations
                    if rec.confidence_score >= request.min_confidence
                ]
                logger.debug(
                    f"[{request_id}] 過濾後剩餘 {len(recommendations)} 個推薦"
                )
            
            # 計算回應時間
            response_time_ms = (time.time() - start_time) * 1000
            
            # 檢查回應時間
            if response_time_ms > settings.MAX_RESPONSE_TIME_SECONDS * 1000:
                logger.warning(
                    f"[{request_id}] 回應時間 {response_time_ms:.2f}ms "
                    f"超過目標 {settings.MAX_RESPONSE_TIME_SECONDS * 1000}ms"
                )
            
            # 建立回應
            response = RecommendationResponse(
                recommendations=recommendations,
                response_time_ms=response_time_ms,
                model_version=settings.MODEL_VERSION,
                request_id=request_id,
                member_code=request.member_code,
                timestamp=datetime.now()
            )
            
            logger.info(
                f"[{request_id}] ✓ 推薦生成完成: {len(recommendations)} 個推薦, "
                f"回應時間: {response_time_ms:.2f}ms"
            )
            
            return response.model_dump()
        
    except HTTPException:
        # 重新拋出 HTTP 異常
        raise
        
    except Exception as e:
        logger.error(f"[{request_id}] 推薦生成失敗: {e}", exc_info=True)
        
        error_response = ErrorResponse(
            error="recommendation_error",
            message="推薦生成失敗",
            detail=str(e),
            timestamp=datetime.now(),
            request_id=request_id
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump()
        )


@router.get(
    "/model/info",
    response_model=ModelInfoResponse,
    summary="獲取模型資訊",
    description="返回當前模型版本、效能指標、訓練時間和資料統計",
    tags=["Model"],
    responses={
        200: {
            "description": "成功返回模型資訊",
            "content": {
                "application/json": {
                    "example": {
                        "model_version": "v1.0.0",
                        "model_type": "lightgbm",
                        "trained_at": "2025-01-15T10:30:00",
                        "metrics": {
                            "accuracy": 0.75,
                            "precision": 0.72,
                            "recall": 0.68,
                            "f1_score": 0.70,
                            "precision_at_5": 0.75,
                            "recall_at_5": 0.68,
                            "ndcg_at_5": 0.82,
                            "map_at_5": 0.78
                        },
                        "total_products": 150,
                        "total_members": 1000,
                        "description": "基於 LightGBM 的產品推薦模型"
                    }
                }
            }
        },
        500: {
            "description": "伺服器內部錯誤",
            "model": ErrorResponse
        },
        503: {
            "description": "服務不可用（模型未載入）",
            "model": ErrorResponse
        }
    }
)
async def get_model_info() -> ModelInfoResponse:
    """
    獲取模型資訊
    
    返回當前模型的版本、類型、訓練時間、效能指標和資料統計。
    
    Returns:
        ModelInfoResponse: 模型資訊
        
    Raises:
        HTTPException: 如果模型未載入或獲取資訊失敗
    """
    try:
        logger.info("獲取模型資訊...")
        
        # 獲取推薦引擎
        engine = get_recommendation_engine()
        
        # 獲取模型資訊
        model_info = engine.get_model_info()
        
        if not model_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "model_info_error",
                    "message": "無法獲取模型資訊",
                    "detail": "模型元資料不存在"
                }
            )
        
        # 建立回應
        response = ModelInfoResponse(
            model_version=model_info.get('model_version', settings.MODEL_VERSION),
            model_type=model_info.get('model_type', settings.MODEL_TYPE),
            trained_at=datetime.fromisoformat(model_info['trained_at']) if 'trained_at' in model_info else datetime.now(),
            metrics=model_info.get('metrics', {}),
            total_products=model_info.get('total_products', 0),
            total_members=model_info.get('total_members', 0),
            description=model_info.get('description')
        )
        
        logger.info(f"✓ 模型資訊獲取完成: {response.model_version}")
        
        return response
        
    except HTTPException:
        # 重新拋出 HTTP 異常
        raise
        
    except Exception as e:
        logger.error(f"獲取模型資訊失敗: {e}", exc_info=True)
        
        error_response = ErrorResponse(
            error="model_info_error",
            message="獲取模型資訊失敗",
            detail=str(e),
            timestamp=datetime.now()
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump()
        )


@router.get(
    "/recommendations/health",
    summary="推薦服務健康檢查",
    description="檢查推薦服務是否正常運行",
    tags=["Health"]
)
async def recommendations_health() -> dict:
    """
    推薦服務健康檢查
    
    Returns:
        健康檢查結果
    """
    try:
        engine = get_recommendation_engine()
        health = engine.health_check()
        
        return {
            "status": "healthy" if health["model_loaded"] else "degraded",
            "service": "recommendations",
            "details": health
        }
    except Exception as e:
        logger.error(f"推薦服務健康檢查失敗: {e}")
        return {
            "status": "unhealthy",
            "service": "recommendations",
            "error": str(e)
        }


@router.get(
    "/monitoring/realtime",
    summary="獲取即時監控數據",
    description="返回最近一段時間的推薦品質和性能監控數據",
    tags=["Monitoring"]
)
async def get_realtime_monitoring(
    time_window_minutes: int = 60,
    member_code: Optional[str] = None
) -> dict:
    """
    獲取即時監控數據
    
    Args:
        time_window_minutes: 時間窗口（分鐘），預設60分鐘
        member_code: 會員編號，None表示所有會員
    
    Returns:
        即時監控數據
    """
    try:
        from datetime import timedelta
        
        quality_monitor = get_quality_monitor()
        time_window = timedelta(minutes=time_window_minutes)
        
        # 獲取監控記錄
        records = quality_monitor.get_records(
            time_window=time_window,
            member_code=member_code
        )
        
        if not records:
            return {
                "time_window_minutes": time_window_minutes,
                "total_records": 0,
                "message": "沒有監控記錄"
            }
        
        # 計算統計數據
        import numpy as np
        
        overall_scores = [r.overall_score for r in records]
        relevance_scores = [r.relevance_score for r in records]
        novelty_scores = [r.novelty_score for r in records]
        explainability_scores = [r.explainability_score for r in records]
        diversity_scores = [r.diversity_score for r in records]
        response_times = [r.total_time_ms for r in records]
        
        return {
            "time_window_minutes": time_window_minutes,
            "total_records": len(records),
            "unique_members": len(set(r.member_code for r in records)),
            "quality_metrics": {
                "overall_score": {
                    "avg": float(np.mean(overall_scores)),
                    "min": float(np.min(overall_scores)),
                    "max": float(np.max(overall_scores)),
                    "p50": float(np.percentile(overall_scores, 50)),
                    "p95": float(np.percentile(overall_scores, 95))
                },
                "relevance_score": {
                    "avg": float(np.mean(relevance_scores)),
                    "min": float(np.min(relevance_scores)),
                    "max": float(np.max(relevance_scores))
                },
                "novelty_score": {
                    "avg": float(np.mean(novelty_scores)),
                    "min": float(np.min(novelty_scores)),
                    "max": float(np.max(novelty_scores))
                },
                "explainability_score": {
                    "avg": float(np.mean(explainability_scores)),
                    "min": float(np.min(explainability_scores)),
                    "max": float(np.max(explainability_scores))
                },
                "diversity_score": {
                    "avg": float(np.mean(diversity_scores)),
                    "min": float(np.min(diversity_scores)),
                    "max": float(np.max(diversity_scores))
                }
            },
            "performance_metrics": {
                "response_time_ms": {
                    "avg": float(np.mean(response_times)),
                    "min": float(np.min(response_times)),
                    "max": float(np.max(response_times)),
                    "p50": float(np.percentile(response_times, 50)),
                    "p95": float(np.percentile(response_times, 95)),
                    "p99": float(np.percentile(response_times, 99))
                }
            },
            "degradation_count": sum(1 for r in records if r.is_degraded),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取即時監控數據失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "monitoring_error",
                "message": "獲取即時監控數據失敗",
                "detail": str(e)
            }
        )


@router.get(
    "/monitoring/statistics",
    summary="獲取歷史統計數據",
    description="返回指定時間範圍的推薦品質和性能統計數據",
    tags=["Monitoring"]
)
async def get_monitoring_statistics(
    report_type: str = "hourly"
) -> dict:
    """
    獲取歷史統計數據
    
    Args:
        report_type: 報告類型（hourly/daily）
    
    Returns:
        歷史統計數據
    """
    try:
        quality_monitor = get_quality_monitor()
        
        # 生成報告
        if report_type == "hourly":
            report = quality_monitor.generate_hourly_report()
        elif report_type == "daily":
            report = quality_monitor.generate_daily_report()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_report_type",
                    "message": f"不支援的報告類型: {report_type}",
                    "detail": "支援的類型: hourly, daily"
                }
            )
        
        # 轉換為字典
        return {
            "report_type": report.report_type,
            "start_time": report.start_time.isoformat(),
            "end_time": report.end_time.isoformat(),
            "recommendation_stats": {
                "total_recommendations": report.total_recommendations,
                "unique_members": report.unique_members,
                "avg_recommendations_per_member": report.avg_recommendations_per_member
            },
            "quality_stats": {
                "avg_overall_score": report.avg_overall_score,
                "avg_relevance_score": report.avg_relevance_score,
                "avg_novelty_score": report.avg_novelty_score,
                "avg_explainability_score": report.avg_explainability_score,
                "avg_diversity_score": report.avg_diversity_score
            },
            "performance_stats": {
                "avg_response_time_ms": report.avg_response_time_ms,
                "p50_response_time_ms": report.p50_response_time_ms,
                "p95_response_time_ms": report.p95_response_time_ms,
                "p99_response_time_ms": report.p99_response_time_ms
            },
            "alert_stats": {
                "total_alerts": report.total_alerts,
                "critical_alerts": report.critical_alerts,
                "warning_alerts": report.warning_alerts,
                "degradation_count": report.degradation_count
            },
            "trends": {
                "score_trend": report.score_trend,
                "performance_trend": report.performance_trend
            },
            "recommendations_for_improvement": report.recommendations_for_improvement,
            "timestamp": report.timestamp.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取歷史統計數據失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "monitoring_error",
                "message": "獲取歷史統計數據失敗",
                "detail": str(e)
            }
        )


@router.get(
    "/monitoring/alerts",
    summary="獲取告警記錄",
    description="返回指定時間範圍和等級的告警記錄",
    tags=["Monitoring"]
)
async def get_alerts(
    time_window_minutes: int = 60,
    level: Optional[str] = None
) -> dict:
    """
    獲取告警記錄
    
    Args:
        time_window_minutes: 時間窗口（分鐘），預設60分鐘
        level: 告警等級（info/warning/critical），None表示所有等級
    
    Returns:
        告警記錄列表
    """
    try:
        from datetime import timedelta
        from src.models.enhanced_data_models import AlertLevel
        
        quality_monitor = get_quality_monitor()
        time_window = timedelta(minutes=time_window_minutes)
        
        # 轉換告警等級
        alert_level = None
        if level:
            try:
                alert_level = AlertLevel(level.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "invalid_alert_level",
                        "message": f"不支援的告警等級: {level}",
                        "detail": "支援的等級: info, warning, critical"
                    }
                )
        
        # 獲取告警記錄
        alerts = quality_monitor.get_alerts(
            time_window=time_window,
            level=alert_level
        )
        
        # 轉換為字典列表
        alert_list = [
            {
                "level": alert.level.value,
                "metric_name": alert.metric_name,
                "current_value": alert.current_value,
                "threshold_value": alert.threshold_value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat()
            }
            for alert in alerts
        ]
        
        # 統計各等級告警數量
        alert_counts = {
            "info": sum(1 for a in alerts if a.level == AlertLevel.INFO),
            "warning": sum(1 for a in alerts if a.level == AlertLevel.WARNING),
            "critical": sum(1 for a in alerts if a.level == AlertLevel.CRITICAL)
        }
        
        return {
            "time_window_minutes": time_window_minutes,
            "filter_level": level,
            "total_alerts": len(alerts),
            "alert_counts": alert_counts,
            "alerts": alert_list,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取告警記錄失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "monitoring_error",
                "message": "獲取告警記錄失敗",
                "detail": str(e)
            }
        )


# 預熱推薦引擎（可選）
def warmup_recommendation_engine():
    """
    預熱推薦引擎
    
    在應用啟動時初始化推薦引擎，避免第一次請求時的延遲
    """
    try:
        logger.info("預熱推薦引擎...")
        get_recommendation_engine()
        logger.info("✓ 推薦引擎預熱完成")
    except Exception as e:
        logger.warning(f"推薦引擎預熱失敗: {e}")
        logger.warning("推薦引擎將在第一次請求時初始化")
