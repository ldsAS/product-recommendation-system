"""
配置載入器測試
測試配置載入、訪問和驗證功能
"""
import pytest
import yaml
import time
from pathlib import Path
from datetime import datetime
from src.utils.config_loader import ConfigLoader, get_config_loader, reload_config


@pytest.fixture
def temp_config_file(tmp_path):
    """創建臨時配置文件"""
    config_data = {
        'strategy_weights': {
            'collaborative_filtering': 0.40,
            'content_based': 0.30,
            'popularity': 0.20,
            'diversity': 0.10
        },
        'quality_thresholds': {
            'overall_score': {
                'critical': 40,
                'warning': 50,
                'target': 60
            },
            'relevance_score': {
                'critical': 50,
                'warning': 60,
                'target': 70
            }
        },
        'performance_thresholds': {
            'total_time_ms': {
                'p50': 200,
                'p95': 500,
                'p99': 1000
            }
        },
        'monitoring': {
            'enable_real_time': True,
            'enable_hourly_report': True,
            'alert_channels': ['console', 'log']
        },
        'degradation': {
            'enable_auto_degradation': True,
            'degradation_threshold_score': 40,
            'degradation_threshold_time_ms': 2000
        },
        'recommendation': {
            'default_count': 5,
            'min_confidence_score': 0.0,
            'max_reasons_per_recommendation': 2
        }
    }
    
    config_file = tmp_path / "test_config.yaml"
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f)
    
    return config_file


@pytest.fixture
def config_loader(temp_config_file):
    """創建配置載入器實例"""
    return ConfigLoader(temp_config_file)


class TestConfigLoader:
    """配置載入器測試類"""
    
    def test_load_config_success(self, config_loader):
        """測試配置載入成功"""
        assert config_loader._config is not None
        assert len(config_loader._config) > 0
        assert config_loader._last_loaded is not None
        assert config_loader._file_mtime is not None
    
    def test_load_config_file_not_found(self, tmp_path):
        """測試配置文件不存在"""
        non_existent_file = tmp_path / "non_existent.yaml"
        
        with pytest.raises(FileNotFoundError):
            ConfigLoader(non_existent_file)
    
    def test_load_config_invalid_yaml(self, tmp_path):
        """測試無效的 YAML 格式"""
        invalid_file = tmp_path / "invalid.yaml"
        with open(invalid_file, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        with pytest.raises(yaml.YAMLError):
            ConfigLoader(invalid_file)
    
    def test_validate_config_missing_section(self, tmp_path):
        """測試配置缺少必要部分"""
        incomplete_config = {
            'strategy_weights': {
                'collaborative_filtering': 0.40
            }
            # 缺少其他必要部分
        }
        
        config_file = tmp_path / "incomplete.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(incomplete_config, f)
        
        with pytest.raises(ValueError, match="配置缺少必要部分"):
            ConfigLoader(config_file)
    
    def test_get_simple_key(self, config_loader):
        """測試獲取簡單鍵值"""
        strategy_weights = config_loader.get('strategy_weights')
        assert strategy_weights is not None
        assert isinstance(strategy_weights, dict)
        assert 'collaborative_filtering' in strategy_weights
    
    def test_get_nested_key(self, config_loader):
        """測試獲取嵌套鍵值"""
        cf_weight = config_loader.get('strategy_weights.collaborative_filtering')
        assert cf_weight == 0.40
        
        target_score = config_loader.get('quality_thresholds.overall_score.target')
        assert target_score == 60
    
    def test_get_with_default(self, config_loader):
        """測試獲取不存在的鍵返回預設值"""
        value = config_loader.get('non_existent_key', 'default_value')
        assert value == 'default_value'
        
        nested_value = config_loader.get('non.existent.nested.key', 42)
        assert nested_value == 42
    
    def test_get_strategy_weights(self, config_loader):
        """測試獲取策略權重"""
        weights = config_loader.get_strategy_weights()
        assert isinstance(weights, dict)
        assert weights['collaborative_filtering'] == 0.40
        assert weights['content_based'] == 0.30
        assert weights['popularity'] == 0.20
        assert weights['diversity'] == 0.10
        
        # 驗證權重總和
        total = sum(weights.values())
        assert 0.99 <= total <= 1.01
    
    def test_get_quality_thresholds(self, config_loader):
        """測試獲取品質閾值"""
        thresholds = config_loader.get_quality_thresholds()
        assert isinstance(thresholds, dict)
        assert 'overall_score' in thresholds
        assert 'relevance_score' in thresholds
        
        overall = thresholds['overall_score']
        assert overall['critical'] == 40
        assert overall['warning'] == 50
        assert overall['target'] == 60
    
    def test_get_performance_thresholds(self, config_loader):
        """測試獲取性能閾值"""
        thresholds = config_loader.get_performance_thresholds()
        assert isinstance(thresholds, dict)
        assert 'total_time_ms' in thresholds
        
        total_time = thresholds['total_time_ms']
        assert total_time['p50'] == 200
        assert total_time['p95'] == 500
        assert total_time['p99'] == 1000
    
    def test_get_monitoring_config(self, config_loader):
        """測試獲取監控配置"""
        monitoring = config_loader.get_monitoring_config()
        assert isinstance(monitoring, dict)
        assert monitoring['enable_real_time'] is True
        assert monitoring['enable_hourly_report'] is True
        assert 'console' in monitoring['alert_channels']
    
    def test_get_degradation_config(self, config_loader):
        """測試獲取降級配置"""
        degradation = config_loader.get_degradation_config()
        assert isinstance(degradation, dict)
        assert degradation['enable_auto_degradation'] is True
        assert degradation['degradation_threshold_score'] == 40
        assert degradation['degradation_threshold_time_ms'] == 2000
    
    def test_get_recommendation_config(self, config_loader):
        """測試獲取推薦配置"""
        recommendation = config_loader.get_recommendation_config()
        assert isinstance(recommendation, dict)
        assert recommendation['default_count'] == 5
        assert recommendation['min_confidence_score'] == 0.0
        assert recommendation['max_reasons_per_recommendation'] == 2
    
    def test_get_all_config(self, config_loader):
        """測試獲取完整配置"""
        all_config = config_loader.get_all_config()
        assert isinstance(all_config, dict)
        assert 'strategy_weights' in all_config
        assert 'quality_thresholds' in all_config
        assert 'performance_thresholds' in all_config
        
        # 驗證返回的是副本
        all_config['new_key'] = 'new_value'
        assert 'new_key' not in config_loader._config
    
    def test_is_enabled(self, config_loader):
        """測試功能啟用檢查"""
        assert config_loader.is_enabled('monitoring.enable_real_time') is True
        assert config_loader.is_enabled('monitoring.enable_hourly_report') is True
        assert config_loader.is_enabled('degradation.enable_auto_degradation') is True
        
        # 測試不存在的鍵
        assert config_loader.is_enabled('non_existent.feature') is False
    
    def test_get_last_loaded_time(self, config_loader):
        """測試獲取最後載入時間"""
        last_loaded = config_loader.get_last_loaded_time()
        assert last_loaded is not None
        assert isinstance(last_loaded, datetime)
        assert last_loaded <= datetime.now()
    
    def test_reload_if_changed_no_change(self, config_loader):
        """測試配置未變更時不重新載入"""
        original_time = config_loader._last_loaded
        time.sleep(0.1)
        
        reloaded = config_loader.reload_if_changed()
        assert reloaded is False
        assert config_loader._last_loaded == original_time
    
    def test_reload_if_changed_with_change(self, config_loader, temp_config_file):
        """測試配置變更時重新載入"""
        original_time = config_loader._last_loaded
        time.sleep(0.1)
        
        # 修改配置文件
        with open(temp_config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        config_data['strategy_weights']['collaborative_filtering'] = 0.50
        
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        # 重新載入
        reloaded = config_loader.reload_if_changed()
        assert reloaded is True
        assert config_loader._last_loaded > original_time
        
        # 驗證配置已更新
        cf_weight = config_loader.get('strategy_weights.collaborative_filtering')
        assert cf_weight == 0.50
    
    def test_config_loader_repr(self, config_loader):
        """測試字串表示"""
        repr_str = repr(config_loader)
        assert 'ConfigLoader' in repr_str
        assert 'config_path' in repr_str
        assert 'last_loaded' in repr_str


class TestGlobalConfigLoader:
    """全域配置載入器測試類"""
    
    def test_get_config_loader_singleton(self, temp_config_file):
        """測試全域配置載入器單例模式"""
        # 重置全域實例
        import src.utils.config_loader as config_module
        config_module._global_config_loader = None
        
        loader1 = get_config_loader(temp_config_file)
        loader2 = get_config_loader(temp_config_file)
        
        assert loader1 is loader2
    
    def test_reload_config(self, temp_config_file):
        """測試重新載入全域配置"""
        # 重置全域實例
        import src.utils.config_loader as config_module
        config_module._global_config_loader = None
        
        loader = get_config_loader(temp_config_file)
        original_time = loader._last_loaded
        
        time.sleep(0.1)
        
        # 修改配置文件
        with open(temp_config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        config_data['recommendation']['default_count'] = 10
        
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        # 重新載入
        reloaded = reload_config()
        assert reloaded is True
        assert loader._last_loaded > original_time
        
        # 驗證配置已更新
        default_count = loader.get('recommendation.default_count')
        assert default_count == 10


class TestConfigValidation:
    """配置驗證測試類"""
    
    def test_strategy_weights_sum_validation(self, tmp_path):
        """測試策略權重總和驗證"""
        # 權重總和不為 1.0 的配置（應該發出警告但不報錯）
        config_data = {
            'strategy_weights': {
                'collaborative_filtering': 0.50,
                'content_based': 0.30,
                'popularity': 0.10,
                'diversity': 0.05  # 總和 = 0.95
            },
            'quality_thresholds': {
                'overall_score': {'critical': 40, 'warning': 50, 'target': 60}
            },
            'performance_thresholds': {
                'total_time_ms': {'p50': 200, 'p95': 500, 'p99': 1000}
            },
            'monitoring': {'enable_real_time': True},
            'degradation': {'enable_auto_degradation': True},
            'recommendation': {'default_count': 5}
        }
        
        config_file = tmp_path / "test_weights.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        # 應該能成功載入（只是警告）
        loader = ConfigLoader(config_file)
        weights = loader.get_strategy_weights()
        # 使用 pytest.approx 處理浮點數精度問題
        assert sum(weights.values()) == pytest.approx(0.95, rel=1e-9)
    
    def test_empty_config(self, tmp_path):
        """測試空配置文件"""
        config_file = tmp_path / "empty.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write("")
        
        with pytest.raises(ValueError):
            ConfigLoader(config_file)
    
    def test_config_with_extra_fields(self, temp_config_file):
        """測試包含額外欄位的配置"""
        # 添加額外欄位
        with open(temp_config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        config_data['extra_field'] = 'extra_value'
        config_data['custom_section'] = {'key': 'value'}
        
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
        
        # 應該能成功載入
        loader = ConfigLoader(temp_config_file)
        assert loader.get('extra_field') == 'extra_value'
        assert loader.get('custom_section.key') == 'value'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
