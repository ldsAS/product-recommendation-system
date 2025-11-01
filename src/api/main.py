"""
FastAPI 應用主程式
初始化 FastAPI 應用，配置 CORS 和中介軟體，實作健康檢查端點
"""
import time
import logging
from datetime import datetime
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from pathlib import Path

from src.config import settings
from src.models.data_models import HealthCheckResponse, ErrorResponse
from src.api.routes import recommendations
from src.api.error_handlers import register_error_handlers

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 應用啟動時間
app_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用生命週期管理
    """
    # 啟動時執行
    logger.info("=" * 60)
    logger.info("FastAPI 應用啟動中...")
    logger.info(f"應用名稱: {settings.APP_NAME}")
    logger.info(f"版本: {settings.APP_VERSION}")
    logger.info(f"環境: {settings.ENVIRONMENT}")
    logger.info("=" * 60)
    
    # 預熱推薦引擎（可選）
    # recommendations.warmup_recommendation_engine()
    
    yield
    
    # 關閉時執行
    logger.info("FastAPI 應用關閉中...")
    # 清理資源
    logger.info("資源清理完成")


# 建立 FastAPI 應用
app = FastAPI(
    title=settings.APP_NAME,
    description="基於機器學習的產品推薦系統 API",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# 註冊路由
app.include_router(recommendations.router)

# 註冊錯誤處理器
register_error_handlers(app)

# 設置模板
templates_dir = Path(__file__).parent.parent / "web" / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


# ============================================================================
# 中介軟體配置
# ============================================================================

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 請求日誌中介軟體
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    記錄所有 HTTP 請求
    """
    start_time = time.time()
    
    # 記錄請求資訊
    logger.info(f"請求開始: {request.method} {request.url.path}")
    
    # 處理請求
    response = await call_next(request)
    
    # 計算處理時間
    process_time = (time.time() - start_time) * 1000  # 毫秒
    
    # 記錄回應資訊
    logger.info(
        f"請求完成: {request.method} {request.url.path} "
        f"- 狀態碼: {response.status_code} "
        f"- 處理時間: {process_time:.2f}ms"
    )
    
    # 添加處理時間到回應標頭
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    
    return response


# ============================================================================
# 基礎端點
# ============================================================================

@app.get("/", response_class=HTMLResponse, tags=["Root"])
async def root(request: Request):
    """
    根端點 - Web UI
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api", tags=["Root"])
async def api_root() -> Dict[str, Any]:
    """
    API 根端點
    """
    return {
        "message": "歡迎使用產品推薦系統 API",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_check_url": "/health"
    }


@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check() -> HealthCheckResponse:
    """
    健康檢查端點
    
    檢查應用程式是否正常運行
    
    Returns:
        HealthCheckResponse: 健康檢查結果
    """
    uptime_seconds = time.time() - app_start_time
    
    # 檢查模型是否已載入（如果有的話）
    model_loaded = False
    try:
        if hasattr(app.state, 'recommendation_engine'):
            model_loaded = app.state.recommendation_engine is not None
    except Exception as e:
        logger.warning(f"檢查模型狀態時發生錯誤: {e}")
    
    return HealthCheckResponse(
        status="healthy",
        model_loaded=model_loaded,
        uptime_seconds=uptime_seconds,
        timestamp=datetime.now()
    )


@app.get("/info", tags=["Info"])
async def app_info() -> Dict[str, Any]:
    """
    應用程式資訊端點
    
    Returns:
        應用程式資訊
    """
    uptime_seconds = time.time() - app_start_time
    
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": uptime_seconds,
        "uptime_formatted": format_uptime(uptime_seconds),
        "model_version": settings.MODEL_VERSION,
        "max_response_time_seconds": settings.MAX_RESPONSE_TIME_SECONDS,
        "top_k_recommendations": settings.TOP_K_RECOMMENDATIONS
    }


def format_uptime(seconds: float) -> str:
    """
    格式化運行時間
    
    Args:
        seconds: 秒數
        
    Returns:
        格式化的時間字串
    """
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days} 天")
    if hours > 0:
        parts.append(f"{hours} 小時")
    if minutes > 0:
        parts.append(f"{minutes} 分鐘")
    if secs > 0 or not parts:
        parts.append(f"{secs} 秒")
    
    return " ".join(parts)


# ============================================================================
# 主程式
# ============================================================================

def main():
    """
    主程式：啟動 FastAPI 應用
    """
    import uvicorn
    
    logger.info("啟動 FastAPI 應用...")
    logger.info(f"主機: {settings.API_HOST}")
    logger.info(f"端口: {settings.API_PORT}")
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )


if __name__ == "__main__":
    main()
