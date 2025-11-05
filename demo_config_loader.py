"""
配置載入器示範程式
展示配置管理功能的使用方式
"""
from pathlib import Path
from src.utils.config_loader import ConfigLoader, get_config_loader


def demo_basic_usage():
    """示範基本使用方式"""
    print("=" * 60)
    print("配置載入器基本使用示範")
    print("=" * 60)
    
    # 載入配置
    config = ConfigLoader(Path("config/recommendation_config.yaml"))
    
    print("\n1. 載入配置成功")
    print(f"   配置路徑: {config.config_path}")
    print(f"   載入時間: {config.get_last_loaded_time()}")
    
    # 獲取策略權重
    print("\n2. 策略權重配置:")
    weights = config.get_strategy_weights()
    for strategy, weight in weights.items():
        print(f"   - {strategy}: {weight * 100:.0f}%")
    
    # 獲取品質閾值
    print("\n3. 品質閾值配置:")
    quality_thresholds = config.get_quality_thresholds()
    for metric, thresholds in quality_thresholds.items():
        print(f"   - {metric}:")
        print(f"     嚴重告警: < {thresholds['critical']}")
        print(f"     警告: < {thresholds['warning']}")
        print(f"     目標: > {thresholds['target']}")
    
    # 獲取性能閾值
    print("\n4. 性能閾值配置:")
    perf_thresholds = config.get_performance_thresholds()
    total_time = perf_thresholds['total_time_ms']
    print(f"   總反應時間:")
    print(f"   - P50: < {total_time['p50']} ms")
    print(f"   - P95: < {total_time['p95']} ms")
    print(f"   - P99: < {total_time['p99']} ms")


def demo_nested_access():
    """示範嵌套鍵訪問"""
    print("\n" + "=" * 60)
    print("嵌套鍵訪問示範")
    print("=" * 60)
    
    config = ConfigLoader(Path("config/recommendation_config.yaml"))
    
    # 使用點號分隔訪問嵌套鍵
    print("\n使用點號分隔訪問嵌套配置:")
    
    cf_weight = config.get('strategy_weights.collaborative_filtering')
    print(f"1. 協同過濾權重: {cf_weight}")
    
    overall_target = config.get('quality_thresholds.overall_score.target')
    print(f"2. 綜合分數目標: {overall_target}")
    
    p95_threshold = config.get('performance_thresholds.total_time_ms.p95')
    print(f"3. P95 反應時間閾值: {p95_threshold} ms")
    
    enable_real_time = config.get('monitoring.enable_real_time')
    print(f"4. 啟用即時監控: {enable_real_time}")
    
    # 使用預設值
    print("\n使用預設值:")
    non_existent = config.get('non.existent.key', 'default_value')
    print(f"不存在的鍵: {non_existent}")


def demo_feature_checks():
    """示範功能啟用檢查"""
    print("\n" + "=" * 60)
    print("功能啟用檢查示範")
    print("=" * 60)
    
    config = ConfigLoader(Path("config/recommendation_config.yaml"))
    
    print("\n檢查各項功能是否啟用:")
    
    features = [
        ('monitoring.enable_real_time', '即時監控'),
        ('monitoring.enable_hourly_report', '小時報告'),
        ('monitoring.enable_daily_report', '日報'),
        ('degradation.enable_auto_degradation', '自動降級'),
        ('cache.enabled', '快取'),
        ('ab_test.enabled', 'A/B 測試')
    ]
    
    for feature_key, feature_name in features:
        enabled = config.is_enabled(feature_key)
        status = "✓ 啟用" if enabled else "✗ 停用"
        print(f"{status} - {feature_name}")


def demo_config_sections():
    """示範獲取各配置區段"""
    print("\n" + "=" * 60)
    print("配置區段訪問示範")
    print("=" * 60)
    
    config = ConfigLoader(Path("config/recommendation_config.yaml"))
    
    # 監控配置
    print("\n1. 監控配置:")
    monitoring = config.get_monitoring_config()
    print(f"   即時監控: {monitoring['enable_real_time']}")
    print(f"   告警通道: {', '.join(monitoring['alert_channels'])}")
    print(f"   記錄保留天數: {monitoring['record_retention_days']}")
    
    # 降級配置
    print("\n2. 降級配置:")
    degradation = config.get_degradation_config()
    print(f"   自動降級: {degradation['enable_auto_degradation']}")
    print(f"   品質閾值: {degradation['degradation_threshold_score']}")
    print(f"   時間閾值: {degradation['degradation_threshold_time_ms']} ms")
    
    # 推薦配置
    print("\n3. 推薦配置:")
    recommendation = config.get_recommendation_config()
    print(f"   預設推薦數量: {recommendation['default_count']}")
    print(f"   最大推薦數量: {recommendation['max_count']}")
    print(f"   每個推薦最大理由數: {recommendation['max_reasons_per_recommendation']}")
    
    # 快取配置
    print("\n4. 快取配置:")
    cache = config.get_cache_config()
    print(f"   啟用快取: {cache['enabled']}")
    print(f"   快取類型: {cache['cache_type']}")
    print(f"   存活時間: {cache['ttl_seconds']} 秒")


def demo_global_singleton():
    """示範全域單例模式"""
    print("\n" + "=" * 60)
    print("全域單例模式示範")
    print("=" * 60)
    
    # 獲取全域配置載入器
    config1 = get_config_loader(Path("config/recommendation_config.yaml"))
    config2 = get_config_loader(Path("config/recommendation_config.yaml"))
    
    print("\n驗證單例模式:")
    print(f"config1 is config2: {config1 is config2}")
    print(f"config1 id: {id(config1)}")
    print(f"config2 id: {id(config2)}")
    
    # 使用全域配置
    print("\n使用全域配置:")
    cf_weight = config1.get('strategy_weights.collaborative_filtering')
    print(f"協同過濾權重: {cf_weight}")


def demo_config_summary():
    """示範配置摘要"""
    print("\n" + "=" * 60)
    print("配置摘要")
    print("=" * 60)
    
    config = ConfigLoader(Path("config/recommendation_config.yaml"))
    
    print("\n推薦系統配置概覽:")
    print(f"  配置文件: {config.config_path}")
    print(f"  載入時間: {config.get_last_loaded_time().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 策略配置
    weights = config.get_strategy_weights()
    print(f"\n  推薦策略:")
    print(f"    協同過濾: {weights['collaborative_filtering'] * 100:.0f}%")
    print(f"    內容推薦: {weights['content_based'] * 100:.0f}%")
    print(f"    熱門推薦: {weights['popularity'] * 100:.0f}%")
    print(f"    多樣性推薦: {weights['diversity'] * 100:.0f}%")
    
    # 品質目標
    quality = config.get_quality_thresholds()
    print(f"\n  品質目標:")
    print(f"    綜合分數: > {quality['overall_score']['target']}")
    print(f"    相關性: > {quality['relevance_score']['target']}")
    print(f"    新穎性: > {quality['novelty_score']['target']}")
    print(f"    可解釋性: > {quality['explainability_score']['target']}")
    print(f"    多樣性: > {quality['diversity_score']['target']}")
    
    # 性能目標
    perf = config.get_performance_thresholds()
    print(f"\n  性能目標:")
    print(f"    P50 反應時間: < {perf['total_time_ms']['p50']} ms")
    print(f"    P95 反應時間: < {perf['total_time_ms']['p95']} ms")
    print(f"    P99 反應時間: < {perf['total_time_ms']['p99']} ms")
    
    # 功能狀態
    print(f"\n  功能狀態:")
    print(f"    即時監控: {'✓' if config.is_enabled('monitoring.enable_real_time') else '✗'}")
    print(f"    自動降級: {'✓' if config.is_enabled('degradation.enable_auto_degradation') else '✗'}")
    print(f"    快取: {'✓' if config.is_enabled('cache.enabled') else '✗'}")
    print(f"    A/B 測試: {'✓' if config.is_enabled('ab_test.enabled') else '✗'}")


def main():
    """主函數"""
    print("\n" + "=" * 60)
    print("配置載入器完整示範")
    print("=" * 60)
    
    try:
        # 1. 基本使用
        demo_basic_usage()
        
        # 2. 嵌套鍵訪問
        demo_nested_access()
        
        # 3. 功能檢查
        demo_feature_checks()
        
        # 4. 配置區段訪問
        demo_config_sections()
        
        # 5. 全域單例
        demo_global_singleton()
        
        # 6. 配置摘要
        demo_config_summary()
        
        print("\n" + "=" * 60)
        print("✓ 所有示範完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
