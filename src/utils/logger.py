"""
日誌系統
提供結構化日誌記錄功能，支援 JSON 格式和日誌輪轉
"""
import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler


class JSONFormatter(logging.Formatter):
    """JSON 格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日誌記錄為 JSON"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # 添加額外欄位
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'member_code'):
            log_data['member_code'] = record.member_code
        if hasattr(record, 'response_time_ms'):
            log_data['response_time_ms'] = record.response_time_ms
        if hasattr(record, 'model_version'):
            log_data['model_version'] = record.model_version
        
        # 添加異常資訊
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # 添加額外的自定義欄位
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data, ensure_ascii=False)


class LoggerManager:
    """日誌管理器"""
    
    def __init__(
        self,
        log_dir: str = "logs",
        app_name: str = "recommendation_system",
        log_level: str = "INFO",
        enable_console: bool = True,
        enable_file: bool = True,
        enable_json: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        """
        初始化日誌管理器
        
        Args:
            log_dir: 日誌目錄
            app_name: 應用名稱
            log_level: 日誌級別
            enable_console: 是否啟用控制台輸出
            enable_file: 是否啟用檔案輸出
            enable_json: 是否使用 JSON 格式
            max_bytes: 單個日誌檔案最大大小
            backup_count: 保留的備份檔案數量
        """
        self.log_dir = Path(log_dir)
        self.app_name = app_name
        self.log_level = getattr(logging, log_level.upper())
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_json = enable_json
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        # 建立日誌目錄
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化日誌器
        self._loggers: Dict[str, logging.Logger] = {}
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        獲取日誌器
        
        Args:
            name: 日誌器名稱
            
        Returns:
            logging.Logger: 日誌器實例
        """
        if name in self._loggers:
            return self._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        logger.propagate = False
        
        # 清除現有的處理器
        logger.handlers.clear()
        
        # 添加控制台處理器
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            
            if self.enable_json:
                console_handler.setFormatter(JSONFormatter())
            else:
                console_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                console_handler.setFormatter(console_formatter)
            
            logger.addHandler(console_handler)
        
        # 添加檔案處理器
        if self.enable_file:
            # 應用日誌
            app_log_file = self.log_dir / f"{self.app_name}.log"
            app_handler = RotatingFileHandler(
                app_log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            app_handler.setLevel(self.log_level)
            
            if self.enable_json:
                app_handler.setFormatter(JSONFormatter())
            else:
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                app_handler.setFormatter(file_formatter)
            
            logger.addHandler(app_handler)
            
            # 錯誤日誌（單獨檔案）
            error_log_file = self.log_dir / f"{self.app_name}_error.log"
            error_handler = RotatingFileHandler(
                error_log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            
            if self.enable_json:
                error_handler.setFormatter(JSONFormatter())
            else:
                error_handler.setFormatter(file_formatter)
            
            logger.addHandler(error_handler)
        
        self._loggers[name] = logger
        return logger
    
    def log_recommendation(
        self,
        request_id: str,
        member_code: str,
        recommendations: list,
        response_time_ms: float,
        model_version: str,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """
        記錄推薦日誌
        
        Args:
            request_id: 請求ID
            member_code: 會員編號
            recommendations: 推薦列表
            response_time_ms: 回應時間（毫秒）
            model_version: 模型版本
            extra_data: 額外資料
        """
        logger = self.get_logger('recommendation')
        
        log_data = {
            'request_id': request_id,
            'member_code': member_code,
            'num_recommendations': len(recommendations),
            'response_time_ms': response_time_ms,
            'model_version': model_version,
        }
        
        if extra_data:
            log_data.update(extra_data)
        
        # 建立日誌記錄
        record = logger.makeRecord(
            logger.name,
            logging.INFO,
            __file__,
            0,
            f"推薦請求完成: {member_code}",
            (),
            None
        )
        record.request_id = request_id
        record.member_code = member_code
        record.response_time_ms = response_time_ms
        record.model_version = model_version
        record.extra_data = log_data
        
        logger.handle(record)
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        request_id: Optional[str] = None,
        member_code: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """
        記錄錯誤日誌
        
        Args:
            error_type: 錯誤類型
            error_message: 錯誤訊息
            request_id: 請求ID
            member_code: 會員編號
            extra_data: 額外資料
        """
        logger = self.get_logger('error')
        
        log_data = {
            'error_type': error_type,
            'error_message': error_message,
        }
        
        if request_id:
            log_data['request_id'] = request_id
        if member_code:
            log_data['member_code'] = member_code
        if extra_data:
            log_data.update(extra_data)
        
        # 建立日誌記錄
        record = logger.makeRecord(
            logger.name,
            logging.ERROR,
            __file__,
            0,
            f"錯誤: {error_type} - {error_message}",
            (),
            None
        )
        if request_id:
            record.request_id = request_id
        if member_code:
            record.member_code = member_code
        record.extra_data = log_data
        
        logger.handle(record)
    
    def log_model_training(
        self,
        model_version: str,
        model_type: str,
        training_samples: int,
        metrics: Dict[str, float],
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """
        記錄模型訓練日誌
        
        Args:
            model_version: 模型版本
            model_type: 模型類型
            training_samples: 訓練樣本數
            metrics: 評估指標
            extra_data: 額外資料
        """
        logger = self.get_logger('training')
        
        log_data = {
            'model_version': model_version,
            'model_type': model_type,
            'training_samples': training_samples,
            'metrics': metrics,
        }
        
        if extra_data:
            log_data.update(extra_data)
        
        logger.info(
            f"模型訓練完成: {model_version}",
            extra={'extra_data': log_data}
        )
    
    def log_api_request(
        self,
        request_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """
        記錄 API 請求日誌
        
        Args:
            request_id: 請求ID
            endpoint: 端點
            method: HTTP 方法
            status_code: 狀態碼
            response_time_ms: 回應時間（毫秒）
            user_agent: User Agent
            ip_address: IP 地址
            extra_data: 額外資料
        """
        logger = self.get_logger('api')
        
        log_data = {
            'request_id': request_id,
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'response_time_ms': response_time_ms,
        }
        
        if user_agent:
            log_data['user_agent'] = user_agent
        if ip_address:
            log_data['ip_address'] = ip_address
        if extra_data:
            log_data.update(extra_data)
        
        # 建立日誌記錄
        record = logger.makeRecord(
            logger.name,
            logging.INFO,
            __file__,
            0,
            f"API 請求: {method} {endpoint} - {status_code}",
            (),
            None
        )
        record.request_id = request_id
        record.response_time_ms = response_time_ms
        record.extra_data = log_data
        
        logger.handle(record)


# 全域日誌管理器實例
_logger_manager: Optional[LoggerManager] = None


def get_logger_manager() -> LoggerManager:
    """獲取全域日誌管理器"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    return _logger_manager


def setup_logger(
    log_dir: str = "logs",
    app_name: str = "recommendation_system",
    log_level: str = "INFO",
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json: bool = True
) -> LoggerManager:
    """
    設置全域日誌管理器
    
    Args:
        log_dir: 日誌目錄
        app_name: 應用名稱
        log_level: 日誌級別
        enable_console: 是否啟用控制台輸出
        enable_file: 是否啟用檔案輸出
        enable_json: 是否使用 JSON 格式
        
    Returns:
        LoggerManager: 日誌管理器實例
    """
    global _logger_manager
    _logger_manager = LoggerManager(
        log_dir=log_dir,
        app_name=app_name,
        log_level=log_level,
        enable_console=enable_console,
        enable_file=enable_file,
        enable_json=enable_json
    )
    return _logger_manager


def get_logger(name: str) -> logging.Logger:
    """
    獲取日誌器（便捷函數）
    
    Args:
        name: 日誌器名稱
        
    Returns:
        logging.Logger: 日誌器實例
    """
    return get_logger_manager().get_logger(name)


if __name__ == "__main__":
    # 測試日誌系統
    print("測試日誌系統...")
    
    # 設置日誌管理器
    logger_manager = setup_logger(
        log_dir="logs",
        app_name="test_app",
        log_level="INFO",
        enable_console=True,
        enable_file=True,
        enable_json=False  # 測試時使用可讀格式
    )
    
    # 測試基本日誌
    logger = logger_manager.get_logger('test')
    logger.info("這是一條測試訊息")
    logger.warning("這是一條警告訊息")
    logger.error("這是一條錯誤訊息")
    
    # 測試推薦日誌
    logger_manager.log_recommendation(
        request_id="test-123",
        member_code="CU000001",
        recommendations=[
            {'product_id': '30469', 'confidence_score': 85.5},
            {'product_id': '31463', 'confidence_score': 78.2}
        ],
        response_time_ms=245.5,
        model_version="v1.0.0"
    )
    
    # 測試錯誤日誌
    logger_manager.log_error(
        error_type="ValidationError",
        error_message="會員編號不能為空",
        request_id="test-456",
        member_code="CU000002"
    )
    
    # 測試 API 請求日誌
    logger_manager.log_api_request(
        request_id="test-789",
        endpoint="/api/v1/recommendations",
        method="POST",
        status_code=200,
        response_time_ms=245.5,
        user_agent="Mozilla/5.0",
        ip_address="127.0.0.1"
    )
    
    print("✓ 日誌系統測試完成")
    print(f"✓ 日誌檔案位於: logs/")
