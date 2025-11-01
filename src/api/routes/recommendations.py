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
    ModelInfoResponse
)
from src.models.recommendation_engine import RecommendationEngine
from src.utils.validators import validate_recommendation_request
from src.config import settings

logger = logging.getLogger(__name__)

# 建立路由器
router = APIRouter(
    prefix="/api/v1",
    tags=["Recommendations"]
)

# 全域推薦引擎實例（延遲初始化）
_recommendation_engine: Optional[RecommendationEngine] = None


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


@router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="獲取產品推薦",
    description="根據會員資訊返回 Top K 產品推薦",
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
                        "response_time_ms": 245.5,
                        "model_version": "v1.0.0",
                        "request_id": "550e8400-e29b-41d4-a716-446655440000",
                        "member_code": "CU000001",
                        "timestamp": "2025-01-15T10:30:00"
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
    http_request: Request
) -> RecommendationResponse:
    """
    獲取產品推薦
    
    根據會員資訊返回 Top K 產品推薦，包含推薦理由和信心分數。
    
    Args:
        request: 推薦請求，包含會員資訊和推薦參數
        http_request: HTTP 請求物件
        
    Returns:
        RecommendationResponse: 推薦回應，包含推薦列表和元資料
        
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
        
        # 2. 獲取推薦引擎
        engine = get_recommendation_engine()
        
        # 3. 轉換為 MemberInfo
        from src.models.data_models import MemberInfo
        member_info = MemberInfo(
            member_code=request.member_code,
            phone=request.phone,
            total_consumption=request.total_consumption,
            accumulated_bonus=request.accumulated_bonus,
            recent_purchases=request.recent_purchases
        )
        
        # 4. 生成推薦
        logger.debug(f"[{request_id}] 生成推薦...")
        recommendations = engine.recommend(
            member_info=member_info,
            n=request.top_k or settings.TOP_K_RECOMMENDATIONS
        )
        
        # 5. 過濾低信心分數的推薦
        if request.min_confidence and request.min_confidence > 0:
            recommendations = [
                rec for rec in recommendations
                if rec.confidence_score >= request.min_confidence
            ]
            logger.debug(
                f"[{request_id}] 過濾後剩餘 {len(recommendations)} 個推薦"
            )
        
        # 6. 計算回應時間
        response_time_ms = (time.time() - start_time) * 1000
        
        # 7. 檢查回應時間
        if response_time_ms > settings.MAX_RESPONSE_TIME_SECONDS * 1000:
            logger.warning(
                f"[{request_id}] 回應時間 {response_time_ms:.2f}ms "
                f"超過目標 {settings.MAX_RESPONSE_TIME_SECONDS * 1000}ms"
            )
        
        # 8. 建立回應
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
        
        return response
        
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
