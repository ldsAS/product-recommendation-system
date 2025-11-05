"""
增強推薦引擎演示腳本
展示性能追蹤、可參考價值評估、混合推薦策略的完整功能
"""
import sys
from pathlib import Path
import logging

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent))

from src.models.enhanced_recommendation_engine import EnhancedRecommendationEngine
from src.models.data_models import MemberInfo

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_separator(title: str = ""):
    """打印分隔線"""
    if title:
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}\n")
    else:
        print(f"{'=' * 60}\n")


def demo_enhanced_recommendation():
    """演示增強推薦引擎"""
    print_separator("增強推薦引擎演示")
    
    try:
        # 1. 初始化引擎
        print("步驟 1: 初始化增強推薦引擎")
        engine = EnhancedRecommendationEngine()
        print("✓ 引擎初始化完成\n")
        
        # 2. 健康檢查
        print("步驟 2: 執行健康檢查")
        health = engine.health_check()
        for key, value in health.items():
            status = "✓" if value else "✗"
            print(f"  {status} {key}: {value}")
        print()
        
        # 3. 獲取模型資訊
        print("步驟 3: 獲取模型資訊")
        info = engine.get_model_info()
        print(f"  模型版本: {info['model_version']}")
        print(f"  產品數量: {info['total_products']}")
        print(f"  會員數量: {info['total_members']}")
        print(f"  協同過濾可用: {info['cf_model_available']}")
        print(f"  策略權重:")
        for strategy, weight in info['strategy_weights'].items():
            print(f"    - {strategy}: {weight * 100:.0f}%")
        print()
        
        # 4. 測試會員資訊
        print("步驟 4: 準備測試會員")
        test_members = [
            MemberInfo(
                member_code="CU000001",
                phone="0937024682",
                total_consumption=17400.0,
                accumulated_bonus=500.0,
                recent_purchases=["30463", "31033"]
            ),
            MemberInfo(
                member_code="CU000010",
                phone="0900000000",
                total_consumption=5000.0,
                accumulated_bonus=100.0,
                recent_purchases=[]
            )
        ]
        print(f"✓ 準備了 {len(test_members)} 個測試會員\n")
        
        # 5. 測試不同策略
        strategies = ['hybrid', 'ml_only']
        
        for member in test_members:
            print_separator(f"會員 {member.member_code} 的推薦")
            
            for strategy in strategies:
                print(f"\n策略: {strategy.upper()}")
                print("-" * 60)
                
                # 生成推薦
                response = engine.recommend(
                    member_info=member,
                    n=5,
                    strategy=strategy
                )
                
                # 顯示推薦結果
                print(f"\n推薦數量: {len(response.recommendations)}")
                print(f"品質等級: {response.quality_level.value}")
                print(f"是否降級: {'是' if response.is_degraded else '否'}")
                
                # 顯示性能指標
                print(f"\n性能指標:")
                print(f"  總耗時: {response.performance_metrics.total_time_ms:.2f} ms")
                print(f"  慢查詢: {'是' if response.performance_metrics.is_slow_query else '否'}")
                print(f"  階段耗時:")
                for stage, time_ms in response.performance_metrics.stage_times.items():
                    print(f"    - {stage}: {time_ms:.2f} ms")
                
                # 顯示可參考價值分數
                print(f"\n可參考價值分數:")
                score = response.reference_value_score
                print(f"  綜合分數: {score.overall_score:.2f}")
                print(f"  相關性: {score.relevance_score:.2f}")
                print(f"  新穎性: {score.novelty_score:.2f}")
                print(f"  可解釋性: {score.explainability_score:.2f}")
                print(f"  多樣性: {score.diversity_score:.2f}")
                
                # 顯示推薦列表
                print(f"\n推薦列表:")
                for rec in response.recommendations:
                    print(f"  {rec.rank}. {rec.product_name}")
                    print(f"     來源: {rec.source.value}")
                    print(f"     信心分數: {rec.confidence_score:.2f}")
                    print(f"     推薦理由: {rec.explanation}")
                
                print()
        
        # 6. 性能統計
        print_separator("性能統計")
        from datetime import timedelta
        stats = engine.performance_tracker.get_statistics(
            time_window=timedelta(minutes=5)
        )
        
        print(f"統計時間窗口: {stats.time_window}")
        print(f"總請求數: {stats.total_requests}")
        print(f"平均耗時: {stats.avg_time_ms:.2f} ms")
        print(f"P50 耗時: {stats.p50_time_ms:.2f} ms")
        print(f"P95 耗時: {stats.p95_time_ms:.2f} ms")
        print(f"P99 耗時: {stats.p99_time_ms:.2f} ms")
        print(f"慢查詢數: {stats.slow_query_count}")
        print(f"慢查詢率: {stats.slow_query_rate * 100:.2f}%")
        
        if stats.stage_avg_times:
            print(f"\n各階段平均耗時:")
            for stage, avg_time in stats.stage_avg_times.items():
                print(f"  {stage}: {avg_time:.2f} ms")
        
        print_separator("演示完成")
        print("✓ 增強推薦引擎演示成功完成！")
        
    except FileNotFoundError as e:
        print(f"\n✗ 錯誤: {e}")
        print("請先執行訓練: python src/train.py")
    except Exception as e:
        print(f"\n✗ 錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_enhanced_recommendation()
