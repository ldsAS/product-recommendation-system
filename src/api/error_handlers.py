"""
全域異常處理器
處理驗證錯誤、模型錯誤和資料錯誤，返回友善的錯誤訊息
"""
import logging
from datetime import datetime
from typing import Union

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from src.models.data_models import ErrorResponse

logger = logging.getLogger(__name__)


# ============================================================================
# 自定義異常類別
# ============================================================================

class RecommendationSystemError(Exception):
    """推薦系統基礎異常"""
    def __init__(self, message: str, detail: str = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class ModelNotFoundError(RecommendationSystemError):
    """模型未找到異常"""
    pass


class ModelLoadError(RecommendationSystemError):
    """模型載入異常"""
    pass


class FeatureExtractionError(RecommendationSystemError):
    """特徵提取異常"""
    pass


class PredictionError(RecommendationSystemError):
    """預測異常"""
    pass


class DataValidationError(RecommendationSystemError):
    """資料驗證異常"""
    pass


class DataProcessingError(RecommendationSystemError):
    """資料處理異常"""
    pass


# ============================================================================
# 錯誤處理函數
# ============================================================================

async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    處理請求驗證錯誤
    
    Args:
        request: HTTP 請求
        exc: 驗證異常
        
    Returns:
        JSON 錯誤回應
    """
    logger.error(f"請求驗證錯誤: {exc}")
    
    # 提取錯誤詳情
    errors = []
    if isinstance(exc, RequestValidationError):
        for error in exc.errors():
            errors.append({
                'field': '.'.join(str(loc) for loc in error['loc']),
                'message': error['msg'],
                'type': error['type']
            })
    else:
        errors.append({
            'field': 'unknown',
            'message': str(exc),
            'type': 'validation_error'
        })
    
    error_response = ErrorResponse(
        error="validation_error",
        message="請求資料驗證失敗，請檢查輸入欄位",
        detail=errors,
        timestamp=datetime.now()
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(mode='json')
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """
    處理值錯誤
    
    Args:
        request: HTTP 請求
        exc: 值錯誤異常
        
    Returns:
        JSON 錯誤回應
    """
    logger.error(f"值錯誤: {exc}")
    
    error_response = ErrorResponse(
        error="value_error",
        message="輸入值錯誤",
        detail=str(exc),
        timestamp=datetime.now()
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response.model_dump(mode='json')
    )


async def model_not_found_handler(
    request: Request,
    exc: ModelNotFoundError
) -> JSONResponse:
    """
    處理模型未找到錯誤
    
    Args:
        request: HTTP 請求
        exc: 模型未找到異常
        
    Returns:
        JSON 錯誤回應
    """
    logger.error(f"模型未找到: {exc.message}")
    
    error_response = ErrorResponse(
        error="model_not_found",
        message=exc.message or "推薦模型未找到",
        detail=exc.detail or "請先訓練模型或檢查模型路徑",
        timestamp=datetime.now()
    )
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_response.model_dump(mode='json')
    )


async def model_load_error_handler(
    request: Request,
    exc: ModelLoadError
) -> JSONResponse:
    """
    處理模型載入錯誤
    
    Args:
        request: HTTP 請求
        exc: 模型載入異常
        
    Returns:
        JSON 錯誤回應
    """
    logger.error(f"模型載入錯誤: {exc.message}")
    
    error_response = ErrorResponse(
        error="model_load_error",
        message=exc.message or "模型載入失敗",
        detail=exc.detail or "模型檔案可能損壞或格式不正確",
        timestamp=datetime.now()
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json')
    )


async def feature_extraction_error_handler(
    request: Request,
    exc: FeatureExtractionError
) -> JSONResponse:
    """
    處理特徵提取錯誤
    
    Args:
        request: HTTP 請求
        exc: 特徵提取異常
        
    Returns:
        JSON 錯誤回應
    """
    logger.error(f"特徵提取錯誤: {exc.message}")
    
    error_response = ErrorResponse(
        error="feature_extraction_error",
        message=exc.message or "特徵提取失敗",
        detail=exc.detail or "無法從輸入資料提取特徵",
        timestamp=datetime.now()
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json')
    )


async def prediction_error_handler(
    request: Request,
    exc: PredictionError
) -> JSONResponse:
    """
    處理預測錯誤
    
    Args:
        request: HTTP 請求
        exc: 預測異常
        
    Returns:
        JSON 錯誤回應
    """
    logger.error(f"預測錯誤: {exc.message}")
    
    error_response = ErrorResponse(
        error="prediction_error",
        message=exc.message or "推薦生成失敗",
        detail=exc.detail or "模型預測過程中發生錯誤",
        timestamp=datetime.now()
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json')
    )


async def data_validation_error_handler(
    request: Request,
    exc: DataValidationError
) -> JSONResponse:
    """
    處理資料驗證錯誤
    
    Args:
        request: HTTP 請求
        exc: 資料驗證異常
        
    Returns:
        JSON 錯誤回應
    """
    logger.error(f"資料驗證錯誤: {exc.message}")
    
    error_response = ErrorResponse(
        error="data_validation_error",
        message=exc.message or "資料驗證失敗",
        detail=exc.detail or "輸入資料不符合要求",
        timestamp=datetime.now()
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response.model_dump(mode='json')
    )


async def data_processing_error_handler(
    request: Request,
    exc: DataProcessingError
) -> JSONResponse:
    """
    處理資料處理錯誤
    
    Args:
        request: HTTP 請求
        exc: 資料處理異常
        
    Returns:
        JSON 錯誤回應
    """
    logger.error(f"資料處理錯誤: {exc.message}")
    
    error_response = ErrorResponse(
        error="data_processing_error",
        message=exc.message or "資料處理失敗",
        detail=exc.detail or "處理輸入資料時發生錯誤",
        timestamp=datetime.now()
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json')
    )


async def file_not_found_handler(
    request: Request,
    exc: FileNotFoundError
) -> JSONResponse:
    """
    處理檔案不存在錯誤
    
    Args:
        request: HTTP 請求
        exc: 檔案不存在異常
        
    Returns:
        JSON 錯誤回應
    """
    logger.error(f"檔案不存在: {exc}")
    
    error_response = ErrorResponse(
        error="file_not_found",
        message="所需檔案不存在",
        detail=str(exc),
        timestamp=datetime.now()
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json')
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    處理一般異常
    
    Args:
        request: HTTP 請求
        exc: 異常
        
    Returns:
        JSON 錯誤回應
    """
    logger.error(f"未預期的錯誤: {exc}", exc_info=True)
    
    # 在開發環境顯示詳細錯誤，生產環境隱藏
    from src.config import settings
    detail = str(exc) if settings.ENVIRONMENT == "development" else "請聯繫系統管理員"
    
    error_response = ErrorResponse(
        error="internal_server_error",
        message="伺服器內部錯誤",
        detail=detail,
        timestamp=datetime.now()
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json')
    )


# ============================================================================
# 錯誤處理器註冊函數
# ============================================================================

def register_error_handlers(app):
    """
    註冊所有錯誤處理器到 FastAPI 應用
    
    Args:
        app: FastAPI 應用實例
    """
    # 驗證錯誤
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    
    # 值錯誤
    app.add_exception_handler(ValueError, value_error_handler)
    
    # 模型相關錯誤
    app.add_exception_handler(ModelNotFoundError, model_not_found_handler)
    app.add_exception_handler(ModelLoadError, model_load_error_handler)
    
    # 特徵和預測錯誤
    app.add_exception_handler(FeatureExtractionError, feature_extraction_error_handler)
    app.add_exception_handler(PredictionError, prediction_error_handler)
    
    # 資料相關錯誤
    app.add_exception_handler(DataValidationError, data_validation_error_handler)
    app.add_exception_handler(DataProcessingError, data_processing_error_handler)
    
    # 檔案錯誤
    app.add_exception_handler(FileNotFoundError, file_not_found_handler)
    
    # 一般異常（最後註冊，作為兜底）
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("✓ 錯誤處理器註冊完成")


# ============================================================================
# 輔助函數
# ============================================================================

def create_error_response(
    error_code: str,
    message: str,
    detail: str = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
) -> JSONResponse:
    """
    建立標準化的錯誤回應
    
    Args:
        error_code: 錯誤代碼
        message: 錯誤訊息
        detail: 詳細資訊
        status_code: HTTP 狀態碼
        
    Returns:
        JSON 錯誤回應
    """
    error_response = ErrorResponse(
        error=error_code,
        message=message,
        detail=detail,
        timestamp=datetime.now()
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(mode='json')
    )


def log_error(error_type: str, message: str, exc: Exception = None):
    """
    記錄錯誤日誌
    
    Args:
        error_type: 錯誤類型
        message: 錯誤訊息
        exc: 異常物件
    """
    if exc:
        logger.error(f"[{error_type}] {message}: {exc}", exc_info=True)
    else:
        logger.error(f"[{error_type}] {message}")
