"""
配置載入器 (ConfigLoader)
載入和管理推薦系統配置
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    配置載入器
    
    負責載入 YAML 配置文件，提供配置訪問介面，支援配置熱更新
    """
    
    # 預設配置文件路徑
    DEFAULT_CONFIG_PATH = Path("config/recommendation_config.yaml")
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化配置載入器
        
        Args:
            config_path: 配置文件路徑，None 表示使用預設路徑
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._config: Dict[str, Any] = {}
        self._last_loaded: Optional[datetime] = None
        self._file_mtime: Optional[float] = None
        
        # 載入配置
        self.load_config()
    
    def load_config(self) -> None:
        """
        載入配置文件
        
        Raises:
            FileNotFoundError: 配置文件不存在
            yaml.YAMLError: YAML 格式錯誤
        """
        if not self.config_path.exists():
            logger.error(f"配置文件不存在: {self.config_path}")
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            
            # 記錄載入時間和文件修改時間
            self._last_loaded = datetime.now()
            self._file_mtime = self.config_path.stat().st_mtime
            
            logger.info(f"✓ 配置載入成功: {self.config_path}")
            
            # 驗證配置
            self._validate_config()
            
        except yaml.YAMLError as e:
            logger.error(f"配置文件格式錯誤: {e}")
            raise
        except Exception as e:
            logger.error(f"配置載入失敗: {e}")
            raise
    
    def reload_if_changed(self) -> bool:
        """
        如果配置文件已修改，則重新載入
        
        Returns:
            bool: 是否重新載入了配置
        """
        if not self.config_path.exists():
            return False
        
        current_mtime = self.config_path.stat().st_mtime
        
        if self._file_mtime is None or current_mtime > self._file_mtime:
            logger.info("檢測到配置文件變更，重新載入...")
            self.load_config()
            return True
        
        return False
    
    def _validate_config(self) -> None:
        """
        驗證配置的完整性和正確性
        
        Raises:
            ValueError: 配置驗證失敗
        """
        # 檢查配置是否為空
        if self._config is None or not isinstance(self._config, dict):
            raise ValueError("配置為空或格式不正確")
        
        required_sections = [
            'strategy_weights',
            'quality_thresholds',
            'performance_thresholds',
            'monitoring',
            'degradation',
            'recommendation'
        ]
        
        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"配置缺少必要部分: {section}")
        
        # 驗證策略權重總和為 1.0
        weights = self._config['strategy_weights']
        total_weight = sum(weights.values())
        if not (0.99 <= total_weight <= 1.01):  # 允許浮點誤差
            logger.warning(
                f"策略權重總和不為 1.0: {total_weight:.2f}，"
                "將自動標準化"
            )
        
        logger.info("✓ 配置驗證通過")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        獲取配置值（支援點號分隔的嵌套鍵）
        
        Args:
            key: 配置鍵，支援 'section.subsection.key' 格式
            default: 預設值
        
        Returns:
            Any: 配置值
        
        Examples:
            >>> config.get('strategy_weights.collaborative_filtering')
            0.40
            >>> config.get('quality_thresholds.overall_score.target')
            60
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_strategy_weights(self) -> Dict[str, float]:
        """
        獲取策略權重配置
        
        Returns:
            Dict[str, float]: 策略權重字典
        """
        return self._config.get('strategy_weights', {})
    
    def get_quality_thresholds(self) -> Dict[str, Dict[str, float]]:
        """
        獲取品質閾值配置
        
        Returns:
            Dict[str, Dict[str, float]]: 品質閾值字典
        """
        return self._config.get('quality_thresholds', {})
    
    def get_performance_thresholds(self) -> Dict[str, Dict[str, float]]:
        """
        獲取性能閾值配置
        
        Returns:
            Dict[str, Dict[str, float]]: 性能閾值字典
        """
        return self._config.get('performance_thresholds', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """
        獲取監控配置
        
        Returns:
            Dict[str, Any]: 監控配置字典
        """
        return self._config.get('monitoring', {})
    
    def get_degradation_config(self) -> Dict[str, Any]:
        """
        獲取降級配置
        
        Returns:
            Dict[str, Any]: 降級配置字典
        """
        return self._config.get('degradation', {})
    
    def get_recommendation_config(self) -> Dict[str, Any]:
        """
        獲取推薦配置
        
        Returns:
            Dict[str, Any]: 推薦配置字典
        """
        return self._config.get('recommendation', {})
    
    def get_cache_config(self) -> Dict[str, Any]:
        """
        獲取快取配置
        
        Returns:
            Dict[str, Any]: 快取配置字典
        """
        return self._config.get('cache', {})
    
    def get_model_config(self) -> Dict[str, Any]:
        """
        獲取模型配置
        
        Returns:
            Dict[str, Any]: 模型配置字典
        """
        return self._config.get('model', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        獲取日誌配置
        
        Returns:
            Dict[str, Any]: 日誌配置字典
        """
        return self._config.get('logging', {})
    
    def get_ab_test_config(self) -> Dict[str, Any]:
        """
        獲取 A/B 測試配置
        
        Returns:
            Dict[str, Any]: A/B 測試配置字典
        """
        return self._config.get('ab_test', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """
        獲取安全配置
        
        Returns:
            Dict[str, Any]: 安全配置字典
        """
        return self._config.get('security', {})
    
    def get_all_config(self) -> Dict[str, Any]:
        """
        獲取完整配置
        
        Returns:
            Dict[str, Any]: 完整配置字典
        """
        return self._config.copy()
    
    def is_enabled(self, feature: str) -> bool:
        """
        檢查功能是否啟用
        
        Args:
            feature: 功能鍵，支援點號分隔
        
        Returns:
            bool: 是否啟用
        
        Examples:
            >>> config.is_enabled('monitoring.enable_real_time')
            True
            >>> config.is_enabled('degradation.enable_auto_degradation')
            True
        """
        value = self.get(feature, False)
        return bool(value)
    
    def get_last_loaded_time(self) -> Optional[datetime]:
        """
        獲取最後載入時間
        
        Returns:
            Optional[datetime]: 最後載入時間
        """
        return self._last_loaded
    
    def __repr__(self) -> str:
        """字串表示"""
        return (
            f"ConfigLoader(config_path={self.config_path}, "
            f"last_loaded={self._last_loaded})"
        )


# 全域配置載入器實例
_global_config_loader: Optional[ConfigLoader] = None


def get_config_loader(config_path: Optional[Path] = None) -> ConfigLoader:
    """
    獲取全域配置載入器實例（單例模式）
    
    Args:
        config_path: 配置文件路徑，None 表示使用預設路徑
    
    Returns:
        ConfigLoader: 配置載入器實例
    """
    global _global_config_loader
    
    if _global_config_loader is None:
        _global_config_loader = ConfigLoader(config_path)
    
    return _global_config_loader


def reload_config() -> bool:
    """
    重新載入全域配置
    
    Returns:
        bool: 是否重新載入了配置
    """
    global _global_config_loader
    
    if _global_config_loader is None:
        return False
    
    return _global_config_loader.reload_if_changed()
