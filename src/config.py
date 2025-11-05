"""
系統配置管理
集中管理所有配置參數
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """系統配置類別"""
    
    # 專案路徑
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    MODELS_DIR: Path = DATA_DIR / "models"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    
    # 資料檔案路徑
    MEMBER_FILE: str = "member"
    SALES_FILE: str = "sales"
    SALES_DETAILS_FILE: str = "salesdetails"
    
    # 模型配置
    MODEL_VERSION: str = "v1.0.0"
    MODEL_TYPE: str = "lightgbm"  # lightgbm, xgboost, collaborative_filtering
    RANDOM_SEED: int = 42
    
    # 訓練配置
    TRAIN_TEST_SPLIT: float = 0.15  # 測試集 15%
    VALIDATION_SPLIT: float = 0.15  # 驗證集 15%（從剩餘 85% 中分出，實際約 12.75%）
    NEGATIVE_SAMPLE_RATIO: float = 3.0  # 負樣本比例 3:1（在 2:1 到 4:1 範圍內）
    
    # 特徵工程配置
    TOP_N_PRODUCTS: int = 3  # 最常購買的前 N 個產品
    RFM_REFERENCE_DATE: Optional[str] = None  # RFM 計算參考日期，None 表示使用當前日期
    
    # 推薦配置
    TOP_K_RECOMMENDATIONS: int = 5
    MIN_CONFIDENCE_SCORE: float = 0.0
    
    # API 配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    APP_NAME: str = "產品推薦系統 API"
    APP_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "基於機器學習的智能產品推薦系統"
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # CORS 配置
    CORS_ORIGINS: list = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]
    
    # 效能配置
    MAX_RESPONSE_TIME_SECONDS: int = 3
    CACHE_TTL_SECONDS: int = 3600  # 快取存活時間 (1小時)
    ENABLE_CACHE: bool = True
    
    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # 日誌配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json 或 text
    LOG_FILE: str = "app.log"
    
    # A/B 測試配置
    AB_TEST_ENABLED: bool = False
    AB_TEST_MODEL_A_RATIO: float = 0.8
    AB_TEST_MODEL_B_VERSION: Optional[str] = None
    
    # 安全配置
    API_KEY_ENABLED: bool = False
    API_KEY: Optional[str] = None
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 全域配置實例
settings = Settings()


def get_settings() -> Settings:
    """獲取配置實例"""
    return settings


def ensure_directories():
    """確保所有必要的目錄存在"""
    directories = [
        settings.DATA_DIR,
        settings.RAW_DATA_DIR,
        settings.PROCESSED_DATA_DIR,
        settings.MODELS_DIR,
        settings.LOGS_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        

if __name__ == "__main__":
    # 測試配置
    ensure_directories()
    print("配置載入成功！")
    print(f"專案根目錄: {settings.PROJECT_ROOT}")
    print(f"資料目錄: {settings.DATA_DIR}")
    print(f"模型目錄: {settings.MODELS_DIR}")
