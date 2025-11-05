"""
品質監控器演示腳本
展示 QualityMonitor 的監控記錄、閾值檢查、告警觸發和報告生成功能
"""
from datetime import datetime, timedelta
from src.utils.quality_monitor import QualityMonitor
from src.models.enhanced_data_models import (
    ReferenceValueScore,
    PerformanceMetrics,
    AlertLevel
)


def print_section(title: str):
    """打印章節標題"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")


def demo_basic_monitoring():
    """演示基本監控功能"""
    print_section("1. 基本監控記錄功能")
    
    monitor = QualityMonitor()
    
    # 創建高品質推薦數據
    value_score = ReferenceValueScore(
        overall_score=75.0,
        relevance_score=80.0,
        novelty_score=40.0,
        explainability_score=90.0,
        diversity_score=70.0,
        score_breakdown={}
    )
    
    performance_metrics = PerformanceMetrics(
        request_id="demo_001",
        total_time_ms=180.0,
        stage_times={
            "feature_loading": 40.0,
            "model_inference": 80.0,
            "reason_generation": 30.0,
            "quality_evaluation": 30.0
        },
        is_slow_query=False
    )
    
    # 記錄推薦
    monitor.record_recommendation(
        request_id="demo_001",
        member_code="M001",
        value_score=value_score,
        performance_metrics=performance_metrics,
        recommendation_count=5,
        strategy_used="hybrid",
        is_degraded=False
    )
    
    print(f"✓ 已記錄推薦數據")
    print(f"  - 請求ID: demo_001")
    print(f"  - 會員編號: M001")
    print(f"  - 綜合分數: {value_score.overall_score:.1f}")
    print(f"  - 總反應時間: {performance_metrics.total_time_ms:.1f}ms")
    print(f"  - 記錄總數: {monitor.get_record_count()}")


def demo_quality_check():
    """演示品質閾值檢查"""
    print_section("2. 品質閾值檢查")
    
    monitor = QualityMonitor()
    
    # 測試高品質分數
    print("【測試案例 1: 高品質推薦】")
    high_quality_score = ReferenceValueScore(
        overall_score=75.0,
        relevance_score=80.0,
        novelty_score=40.0,
        explainability_score=90.0,
        diversity_score=70.0,
        score_breakdown={}
    )
    
    result = monitor.check_quality_threshold(high_quality_score)
    print(f"  檢查結果: {'✓ 通過' if result.passed else '✗ 未通過'}")
    print(f"  綜合分數: {result.overall_score:.1f}")
    print(f"  失敗指標: {len(result.failed_metrics)}")
    print(f"  警告數量: {len(result.warnings)}")
    
    # 測試低品質分數
    print("\n【測試案例 2: 低品質推薦】")
    low_quality_score = ReferenceValueScore(
        overall_score=35.0,
        relevance_score=45.0,
        novelty_score=10.0,
        explainability_score=55.0,
        diversity_score=35.0,
        score_breakdown={}
    )
    
    result = monitor.check_quality_threshold(low_quality_score)
    print(f"  檢查結果: {'✓ 通過' if result.passed else '✗ 未通過'}")
    print(f"  綜合分數: {result.overall_score:.1f}")
    print(f"  失敗指標數量: {len(result.failed_metrics)}")
    if result.failed_metrics:
        print("  失敗指標:")
        for metric in result.failed_metrics[:3]:  # 只顯示前3個
            print(f"    - {metric}")


def demo_performance_check():
    """演示性能閾值檢查"""
    print_section("3. 性能閾值檢查")
    
    monitor = QualityMonitor()
    
    # 測試良好性能
    print("【測試案例 1: 良好性能】")
    good_performance = PerformanceMetrics(
        request_id="demo_001",
        total_time_ms=180.0,
        stage_times={
            "feature_loading": 40.0,
            "model_inference": 80.0,
        },
        is_slow_query=False
    )
    
    result = monitor.check_performance_threshold(good_performance)
    print(f"  檢查結果: {'✓ 通過' if result.passed else '✗ 未通過'}")
    print(f"  總反應時間: {result.total_time_ms:.1f}ms")
    print(f"  失敗指標: {len(result.failed_metrics)}")
    print(f"  警告數量: {len(result.warnings)}")
    
    # 測試慢查詢
    print("\n【測試案例 2: 慢查詢】")
    slow_performance = PerformanceMetrics(
        request_id="demo_002",
        total_time_ms=1200.0,
        stage_times={
            "feature_loading": 150.0,
            "model_inference": 800.0,
        },
        is_slow_query=True
    )
    
    result = monitor.check_performance_threshold(slow_performance)
    print(f"  檢查結果: {'✓ 通過' if result.passed else '✗ 未通過'}")
    print(f"  總反應時間: {result.total_time_ms:.1f}ms")
    print(f"  失敗指標數量: {len(result.failed_metrics)}")
    if result.failed_metrics:
        print("  失敗指標:")
        for metric in result.failed_metrics:
            print(f"    - {metric}")


def demo_alert_system():
    """演示告警機制"""
    print_section("4. 告警機制")
    
    monitor = QualityMonitor()
    
    # 創建會觸發告警的數據
    low_quality_score = ReferenceValueScore(
        overall_score=35.0,
        relevance_score=45.0,
        novelty_score=10.0,
        explainability_score=55.0,
        diversity_score=35.0,
        score_breakdown={}
    )
    
    slow_performance = PerformanceMetrics(
        request_id="demo_001",
        total_time_ms=1200.0,
        stage_times={
            "feature_loading": 150.0,
            "model_inference": 800.0,
        },
        is_slow_query=True
    )
    
    # 觸發告警
    alerts = monitor.trigger_alerts(low_quality_score, slow_performance)
    
    print(f"✓ 觸發告警數量: {len(alerts)}")
    print(f"  - 嚴重告警: {len([a for a in alerts if a.level == AlertLevel.CRITICAL])}")
    print(f"  - 警告: {len([a for a in alerts if a.level == AlertLevel.WARNING])}")
    
    print("\n告警詳情:")
    for i, alert in enumerate(alerts[:5], 1):  # 只顯示前5個
        print(f"\n  [{i}] {alert.level.value.upper()}")
        print(f"      指標: {alert.metric_name}")
        print(f"      當前值: {alert.current_value:.1f}")
        print(f"      閾值: {alert.threshold_value:.1f}")
        print(f"      訊息: {alert.message}")


def demo_report_generation():
    """演示報告生成功能"""
    print_section("5. 報告生成功能")
    
    monitor = QualityMonitor()
    
    # 生成多個推薦記錄
    print("正在生成測試數據...")
    for i in range(20):
        value_score = ReferenceValueScore(
            overall_score=60.0 + i * 1.5,
            relevance_score=65.0 + i,
            novelty_score=30.0 + i * 0.5,
            explainability_score=80.0 + i * 0.3,
            diversity_score=55.0 + i * 0.8,
            score_breakdown={}
        )
        
        performance_metrics = PerformanceMetrics(
            request_id=f"demo_{i:03d}",
            total_time_ms=200.0 + i * 10,
            stage_times={
                "feature_loading": 50.0 + i * 2,
                "model_inference": 100.0 + i * 5,
            },
            is_slow_query=False
        )
        
        monitor.record_recommendation(
            request_id=f"demo_{i:03d}",
            member_code=f"M{i % 5:03d}",  # 5個不同會員
            value_score=value_score,
            performance_metrics=performance_metrics,
            recommendation_count=5,
            strategy_used="hybrid",
            is_degraded=False
        )
    
    # 生成小時報告
    report = monitor.generate_hourly_report()
    
    print(f"\n✓ 已生成小時報告")
    print(f"\n【推薦量統計】")
    print(f"  - 總推薦次數: {report.total_recommendations}")
    print(f"  - 唯一會員數: {report.unique_members}")
    print(f"  - 每會員平均推薦: {report.avg_recommendations_per_member:.1f}")
    
    print(f"\n【品質統計】")
    print(f"  - 平均綜合分數: {report.avg_overall_score:.1f}")
    print(f"  - 平均相關性分數: {report.avg_relevance_score:.1f}")
    print(f"  - 平均新穎性分數: {report.avg_novelty_score:.1f}")
    print(f"  - 平均可解釋性分數: {report.avg_explainability_score:.1f}")
    print(f"  - 平均多樣性分數: {report.avg_diversity_score:.1f}")
    
    print(f"\n【性能統計】")
    print(f"  - 平均反應時間: {report.avg_response_time_ms:.1f}ms")
    print(f"  - P50反應時間: {report.p50_response_time_ms:.1f}ms")
    print(f"  - P95反應時間: {report.p95_response_time_ms:.1f}ms")
    print(f"  - P99反應時間: {report.p99_response_time_ms:.1f}ms")
    
    print(f"\n【異常統計】")
    print(f"  - 總告警數: {report.total_alerts}")
    print(f"  - 嚴重告警數: {report.critical_alerts}")
    print(f"  - 警告數: {report.warning_alerts}")
    print(f"  - 降級次數: {report.degradation_count}")
    
    print(f"\n【趨勢分析】")
    print(f"  - 分數趨勢: {report.score_trend}")
    print(f"  - 性能趨勢: {report.performance_trend}")
    
    if report.recommendations_for_improvement:
        print(f"\n【改進建議】")
        for i, recommendation in enumerate(report.recommendations_for_improvement[:3], 1):
            print(f"  {i}. {recommendation}")


def demo_complete_workflow():
    """演示完整工作流程"""
    print_section("6. 完整工作流程演示")
    
    monitor = QualityMonitor()
    
    print("【場景: 推薦系統運行中】\n")
    
    # 模擬3個推薦請求
    scenarios = [
        {
            "name": "高品質推薦",
            "value_score": ReferenceValueScore(
                overall_score=75.0,
                relevance_score=80.0,
                novelty_score=40.0,
                explainability_score=90.0,
                diversity_score=70.0,
                score_breakdown={}
            ),
            "performance": PerformanceMetrics(
                request_id="req_001",
                total_time_ms=180.0,
                stage_times={"feature_loading": 40.0, "model_inference": 80.0},
                is_slow_query=False
            )
        },
        {
            "name": "中等品質推薦",
            "value_score": ReferenceValueScore(
                overall_score=55.0,
                relevance_score=60.0,
                novelty_score=25.0,
                explainability_score=75.0,
                diversity_score=50.0,
                score_breakdown={}
            ),
            "performance": PerformanceMetrics(
                request_id="req_002",
                total_time_ms=450.0,
                stage_times={"feature_loading": 80.0, "model_inference": 250.0},
                is_slow_query=False
            )
        },
        {
            "name": "低品質推薦（觸發告警）",
            "value_score": ReferenceValueScore(
                overall_score=35.0,
                relevance_score=45.0,
                novelty_score=10.0,
                explainability_score=55.0,
                diversity_score=35.0,
                score_breakdown={}
            ),
            "performance": PerformanceMetrics(
                request_id="req_003",
                total_time_ms=1200.0,
                stage_times={"feature_loading": 150.0, "model_inference": 800.0},
                is_slow_query=True
            )
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"推薦請求 #{i}: {scenario['name']}")
        
        # 記錄推薦
        monitor.record_recommendation(
            request_id=scenario['performance'].request_id,
            member_code=f"M{i:03d}",
            value_score=scenario['value_score'],
            performance_metrics=scenario['performance'],
            recommendation_count=5,
            strategy_used="hybrid",
            is_degraded=False
        )
        
        # 檢查品質
        quality_result = monitor.check_quality_threshold(scenario['value_score'])
        print(f"  品質檢查: {'✓ 通過' if quality_result.passed else '✗ 未通過'} "
              f"(分數: {scenario['value_score'].overall_score:.1f})")
        
        # 檢查性能
        perf_result = monitor.check_performance_threshold(scenario['performance'])
        print(f"  性能檢查: {'✓ 通過' if perf_result.passed else '✗ 未通過'} "
              f"(時間: {scenario['performance'].total_time_ms:.1f}ms)")
        
        # 觸發告警
        alerts = monitor.trigger_alerts(scenario['value_score'], scenario['performance'])
        if alerts:
            print(f"  ⚠ 觸發 {len(alerts)} 個告警")
        
        print()
    
    # 生成報告
    print("\n【生成監控報告】")
    report = monitor.generate_hourly_report()
    print(f"  總推薦次數: {report.total_recommendations}")
    print(f"  平均品質分數: {report.avg_overall_score:.1f}")
    print(f"  平均反應時間: {report.avg_response_time_ms:.1f}ms")
    print(f"  總告警數: {report.total_alerts}")


def main():
    """主函數"""
    print("\n" + "=" * 80)
    print(" 品質監控器 (QualityMonitor) 功能演示")
    print("=" * 80)
    
    try:
        demo_basic_monitoring()
        demo_quality_check()
        demo_performance_check()
        demo_alert_system()
        demo_report_generation()
        demo_complete_workflow()
        
        print("\n" + "=" * 80)
        print(" 演示完成！")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
