"""
降級策略演示腳本
展示當推薦品質或性能不達標時，系統如何自動執行降級策略
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import logging
from datetime import datetime

from src.models.enhanced_recommendation_engine import EnhancedRecommendationEngine
from src.models.data_models import MemberInfo
from src.utils.quality_monitor import QualityMonitor

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_section(title: str):
    """打印章節標題"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_recommendation_response(response, title: str):
    """打印推薦回應"""
    print(f"\n{title}")
    print("-" * 80)
    print(f"會員編號: {response.member_code}")
    print(f"推薦策略: {response.strategy_used}")
    print(f"品質等級: {response.quality_level.value}")
    print(f"是否降級: {'是' if response.is_degraded else '否'}")
    print(f"總耗時: {response.performance_metrics.total_time_ms:.2f} ms")
    
    print(f"\n可參考價值分數:")
    print(f"  綜合分數: {response.reference_value_score.overall_score:.2f}")
    print(f"  相關性: {response.reference_value_score.relevance_score:.2f}")
    print(f"  新穎性: {response.reference_value_score.novelty_score:.2f}")
    print(f"  可解釋性: {response.reference_value_score.explainability_score:.2f}")
    print(f"  多樣性: {response.reference_value_score.diversity_score:.2f}")
    
    print(f"\n推薦列表 (共 {len(response.recommendations)} 個):")
    for rec in response.recommendations[:5]:  # 只顯示前5個
        print(f"  {rec.rank}. {rec.product_name}")
        print(f"     來源: {rec.source.value}")
        print(f"     信心分數: {rec.confidence_score:.2f}")
        print(f"     推薦理由: {rec.explanation}")


def demo_normal_recommendation():
    """演示正常推薦流程"""
    print_section("場景 1: 正常推薦流程")
    
    # 建立推薦引擎
    engine = EnhancedRecommendationEngine()
    
    # 測試會員
    member_info = MemberInfo(
        member_code="CU000001",
        phone="0937024682",
        total_consumption=17400.0,
        accumulated_bonus=500.0,
        recent_purchases=["30463", "31033"]
    )
    
    print(f"\n為會員 {member_info.member_code} 生成推薦...")
    print(f"  消費金額: {member_info.total_consumption}")
    print(f"  已購買產品: {len(member_info.recent_purchases)} 個")
    
    # 生成推薦
    response = engine.recommend(member_info, n=5, strategy='hybrid')
    
    # 顯示結果
    print_recommendation_response(response, "推薦結果")
    
    # 檢查是否需要降級
    if response.is_degraded:
        print("\n⚠️  系統檢測到品質或性能問題，已自動執行降級策略")
    else:
        print("\n✓ 推薦品質和性能正常，未觸發降級")
    
    return response


def demo_degradation_thresholds():
    """演示降級閾值配置"""
    print_section("場景 2: 降級閾值配置")
    
    # 建立推薦引擎
    engine = EnhancedRecommendationEngine()
    
    # 顯示當前閾值
    thresholds = engine.get_degradation_thresholds()
    print("\n當前降級閾值:")
    print(f"  最低品質分數: {thresholds['min_quality_score']}")
    print(f"  最大反應時間: {thresholds['max_response_time_ms']} ms")
    
    # 更新閾值
    print("\n更新降級閾值...")
    engine.update_degradation_thresholds(
        min_quality_score=50.0,
        max_response_time_ms=1500.0
    )
    
    # 顯示更新後的閾值
    new_thresholds = engine.get_degradation_thresholds()
    print("\n更新後的降級閾值:")
    print(f"  最低品質分數: {new_thresholds['min_quality_score']}")
    print(f"  最大反應時間: {new_thresholds['max_response_time_ms']} ms")
    
    # 恢復原始閾值
    engine.update_degradation_thresholds(
        min_quality_score=40.0,
        max_response_time_ms=2000.0
    )
    print("\n✓ 閾值已恢復為預設值")


def demo_quality_monitoring_with_degradation():
    """演示品質監控與降級策略的整合"""
    print_section("場景 3: 品質監控與降級策略整合")
    
    # 建立推薦引擎和品質監控器
    engine = EnhancedRecommendationEngine()
    monitor = QualityMonitor()
    
    # 測試多個會員
    test_members = [
        MemberInfo(
            member_code="CU000001",
            phone="0937024682",
            total_consumption=17400.0,
            accumulated_bonus=500.0,
            recent_purchases=["30463", "31033"]
        ),
        MemberInfo(
            member_code="CU000002",
            phone="0912345678",
            total_consumption=5000.0,
            accumulated_bonus=100.0,
            recent_purchases=["30463"]
        ),
        MemberInfo(
            member_code="CU000003",
            phone="0923456789",
            total_consumption=25000.0,
            accumulated_bonus=800.0,
            recent_purchases=["30463", "31033", "30464"]
        )
    ]
    
    print(f"\n為 {len(test_members)} 個會員生成推薦並監控品質...")
    
    degradation_count = 0
    
    for i, member in enumerate(test_members, 1):
        print(f"\n處理會員 {i}/{len(test_members)}: {member.member_code}")
        
        # 生成推薦
        response = engine.recommend(member, n=5, strategy='hybrid')
        
        # 記錄到監控系統
        monitor.record_recommendation(
            request_id=response.performance_metrics.request_id,
            member_code=response.member_code,
            value_score=response.reference_value_score,
            performance_metrics=response.performance_metrics,
            recommendation_count=len(response.recommendations),
            strategy_used=response.strategy_used,
            is_degraded=response.is_degraded
        )
        
        # 檢查告警
        alerts = monitor.trigger_alerts(
            value_score=response.reference_value_score,
            performance_metrics=response.performance_metrics
        )
        
        # 統計降級次數
        if response.is_degraded:
            degradation_count += 1
        
        # 顯示簡要結果
        print(f"  品質分數: {response.reference_value_score.overall_score:.2f}")
        print(f"  反應時間: {response.performance_metrics.total_time_ms:.2f} ms")
        print(f"  是否降級: {'是' if response.is_degraded else '否'}")
        print(f"  告警數量: {len(alerts)}")
    
    # 生成監控報告
    print("\n生成監控報告...")
    report = monitor.generate_hourly_report()
    
    print(f"\n監控報告摘要:")
    print(f"  總推薦次數: {report.total_recommendations}")
    print(f"  唯一會員數: {report.unique_members}")
    print(f"  平均品質分數: {report.avg_overall_score:.2f}")
    print(f"  平均反應時間: {report.avg_response_time_ms:.2f} ms")
    print(f"  降級次數: {report.degradation_count}")
    print(f"  告警總數: {report.total_alerts}")
    print(f"    - 嚴重告警: {report.critical_alerts}")
    print(f"    - 警告: {report.warning_alerts}")
    
    if report.recommendations_for_improvement:
        print(f"\n改進建議:")
        for i, recommendation in enumerate(report.recommendations_for_improvement, 1):
            print(f"  {i}. {recommendation}")
    
    print(f"\n✓ 品質監控完成，降級率: {degradation_count}/{len(test_members)} = {degradation_count/len(test_members)*100:.1f}%")


def demo_health_check():
    """演示系統健康檢查"""
    print_section("場景 4: 系統健康檢查")
    
    # 建立推薦引擎
    engine = EnhancedRecommendationEngine()
    
    # 執行健康檢查
    health = engine.health_check()
    
    print("\n系統健康狀態:")
    for key, value in health.items():
        status = "✓" if value else "✗"
        print(f"  {status} {key}: {value}")
    
    # 檢查降級策略是否啟用
    if health.get('degradation_strategy_active'):
        print("\n✓ 降級策略已啟用並正常運行")
    else:
        print("\n✗ 降級策略未啟用")


def main():
    """主函數"""
    print("=" * 80)
    print(" 降級策略演示")
    print("=" * 80)
    print("\n本演示展示推薦系統的降級策略功能:")
    print("  1. 正常推薦流程")
    print("  2. 降級閾值配置")
    print("  3. 品質監控與降級策略整合")
    print("  4. 系統健康檢查")
    
    try:
        # 場景 1: 正常推薦
        demo_normal_recommendation()
        
        # 場景 2: 降級閾值配置
        demo_degradation_thresholds()
        
        # 場景 3: 品質監控與降級策略整合
        demo_quality_monitoring_with_degradation()
        
        # 場景 4: 系統健康檢查
        demo_health_check()
        
        print_section("演示完成")
        print("\n✓ 所有場景演示完成！")
        print("\n降級策略功能總結:")
        print("  • 自動檢測品質分數低於閾值（< 40分）")
        print("  • 自動檢測反應時間超過閾值（> 2000ms）")
        print("  • 自動切換到簡單的熱門產品推薦")
        print("  • 記錄降級事件到監控系統")
        print("  • 支援動態調整降級閾值")
        print("  • 與品質監控系統無縫整合")
        
    except FileNotFoundError as e:
        print(f"\n✗ 錯誤: {e}")
        print("請先執行訓練: python src/train.py")
    except Exception as e:
        print(f"\n✗ 錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
