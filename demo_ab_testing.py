"""
A/B 測試框架示範
展示如何使用 A/B 測試框架進行推薦策略對比
"""
import sys
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.ab_testing_framework import (
    ABTestingFramework,
    TestGroupConfig,
    get_ab_testing_framework
)
from src.models.enhanced_recommendation_engine import EnhancedRecommendationEngine
from src.models.data_models import MemberInfo
from src.config import settings
import random


def demo_ab_testing():
    """示範 A/B 測試框架"""
    
    print("=" * 60)
    print("A/B 測試框架示範")
    print("=" * 60)
    
    # 1. 創建 A/B 測試框架
    print("\n1. 初始化 A/B 測試框架...")
    ab_framework = ABTestingFramework(
        config_path="config/ab_test_config.json",
        data_path="data/ab_test_data.json"
    )
    print("✓ A/B 測試框架初始化完成")
    
    # 2. 配置測試組
    print("\n2. 配置測試組...")
    test_groups = [
        TestGroupConfig(
            group_id="control",
            group_name="對照組（原策略）",
            strategy_config={
                'collaborative_filtering': 0.40,
                'content_based': 0.30,
                'popularity': 0.20,
                'diversity': 0.10
            },
            traffic_ratio=0.5,
            description="使用原有的混合推薦策略"
        ),
        TestGroupConfig(
            group_id="test_a",
            group_name="測試組 A（強化協同過濾）",
            strategy_config={
                'collaborative_filtering': 0.60,  # 提高協同過濾權重
                'content_based': 0.20,
                'popularity': 0.10,
                'diversity': 0.10
            },
            traffic_ratio=0.5,
            description="提高協同過濾權重至 60%"
        )
    ]
    
    success = ab_framework.create_test(
        test_name="推薦策略權重優化測試",
        test_groups=test_groups
    )
    
    if success:
        print("✓ 測試配置成功")
        print(f"  測試名稱: 推薦策略權重優化測試")
        print(f"  測試組數: {len(test_groups)}")
    else:
        print("✗ 測試配置失敗")
        return
    
    # 3. 模擬推薦請求
    print("\n3. 模擬推薦請求...")
    
    # 初始化推薦引擎
    try:
        engine = EnhancedRecommendationEngine()
        print("✓ 推薦引擎初始化完成")
    except Exception as e:
        print(f"✗ 推薦引擎初始化失敗: {e}")
        print("  將使用模擬數據繼續示範...")
        engine = None
    
    # 模擬 100 個會員的推薦請求
    num_requests = 100
    print(f"\n模擬 {num_requests} 個推薦請求...")
    
    for i in range(num_requests):
        member_code = f"M{i+1:04d}"
        
        # 分配測試組
        group_id = ab_framework.assign_group(member_code)
        
        if not group_id:
            continue
        
        # 獲取測試組配置
        group_config = ab_framework.get_group_config(group_id)
        
        # 模擬推薦結果（如果沒有真實引擎）
        if engine is None:
            # 模擬不同策略的效果
            if group_id == "test_a":
                # 測試組 A 有稍好的分數
                overall_score = random.uniform(62, 75)
                relevance_score = random.uniform(70, 85)
                novelty_score = random.uniform(28, 38)
                explainability_score = random.uniform(78, 88)
                diversity_score = random.uniform(55, 68)
                response_time_ms = random.uniform(180, 250)
            else:
                # 對照組
                overall_score = random.uniform(58, 70)
                relevance_score = random.uniform(65, 80)
                novelty_score = random.uniform(25, 35)
                explainability_score = random.uniform(75, 85)
                diversity_score = random.uniform(52, 65)
                response_time_ms = random.uniform(190, 260)
            
            recommendation_count = 5
            strategy_used = "hybrid"
        else:
            # 使用真實推薦引擎
            # 這裡需要根據 group_config 調整策略權重
            # 實際實現時需要修改 EnhancedRecommendationEngine 支援動態權重
            # 暫時使用模擬數據
            if group_id == "test_a":
                overall_score = random.uniform(62, 75)
                relevance_score = random.uniform(70, 85)
                novelty_score = random.uniform(28, 38)
                explainability_score = random.uniform(78, 88)
                diversity_score = random.uniform(55, 68)
                response_time_ms = random.uniform(180, 250)
            else:
                overall_score = random.uniform(58, 70)
                relevance_score = random.uniform(65, 80)
                novelty_score = random.uniform(25, 35)
                explainability_score = random.uniform(75, 85)
                diversity_score = random.uniform(52, 65)
                response_time_ms = random.uniform(190, 260)
            
            recommendation_count = 5
            strategy_used = "hybrid"
        
        # 記錄測試結果
        ab_framework.record_test_result(
            member_code=member_code,
            group_id=group_id,
            overall_score=overall_score,
            relevance_score=relevance_score,
            novelty_score=novelty_score,
            explainability_score=explainability_score,
            diversity_score=diversity_score,
            response_time_ms=response_time_ms,
            recommendation_count=recommendation_count,
            strategy_used=strategy_used
        )
        
        if (i + 1) % 20 == 0:
            print(f"  已完成 {i + 1}/{num_requests} 個請求")
    
    print(f"✓ 完成 {num_requests} 個推薦請求")
    
    # 4. 計算統計數據
    print("\n4. 計算統計數據...")
    all_stats = ab_framework.calculate_all_statistics()
    
    print("\n各組統計結果:")
    print("-" * 60)
    for group_id, stats in all_stats.items():
        if stats:
            print(f"\n{stats.group_name} ({group_id}):")
            print(f"  樣本數: {stats.total_records}")
            print(f"  綜合可參考價值分數: {stats.avg_overall_score:.2f} ± {stats.std_overall_score:.2f}")
            print(f"  相關性分數: {stats.avg_relevance_score:.2f}")
            print(f"  新穎性分數: {stats.avg_novelty_score:.2f}")
            print(f"  可解釋性分數: {stats.avg_explainability_score:.2f}")
            print(f"  多樣性分數: {stats.avg_diversity_score:.2f}")
            print(f"  平均反應時間: {stats.avg_response_time_ms:.2f} ms")
            print(f"  P95 反應時間: {stats.p95_response_time_ms:.2f} ms")
    
    # 5. 執行統計顯著性檢驗
    print("\n5. 執行統計顯著性檢驗...")
    print("-" * 60)
    
    test_result = ab_framework.perform_statistical_test("control", "test_a")
    
    if 'error' in test_result:
        print(f"✗ 統計檢驗失敗: {test_result['error']}")
    else:
        print("\n統計檢驗結果:")
        print(f"  對照組平均分數: {test_result['group_a']['mean']:.2f}")
        print(f"  測試組平均分數: {test_result['group_b']['mean']:.2f}")
        print(f"  平均差異: {test_result['test_results']['mean_difference']:.2f}")
        print(f"  改進百分比: {test_result['test_results']['improvement_pct']:.2f}%")
        print(f"  t 統計量: {test_result['test_results']['t_statistic']:.3f}")
        print(f"  p 值: {test_result['test_results']['p_value']:.3f}")
        print(f"  顯著性: {test_result['test_results']['significance']}")
        print(f"  效應大小: {test_result['test_results']['effect_size']}")
        print(f"\n結果解釋:")
        print(f"  {test_result['interpretation']}")
    
    # 6. 生成對比報告
    print("\n6. 生成對比報告...")
    report = ab_framework.generate_comparison_report()
    
    if 'error' in report:
        print(f"✗ 報告生成失敗: {report['error']}")
    else:
        print("\n測試報告:")
        print(f"  測試名稱: {report['test_info']['test_name']}")
        print(f"  開始時間: {report['test_info']['start_time']}")
        print(f"  總記錄數: {report['test_info']['total_records']}")
        
        if 'recommendation' in report:
            print(f"\n推薦結果:")
            print(f"  最佳組別: {report['recommendation']['best_group_name']}")
            print(f"  最佳分數: {report['recommendation']['best_score']:.2f}")
    
    # 7. 停止測試
    print("\n7. 停止測試...")
    ab_framework.stop_test()
    print("✓ 測試已停止")
    
    print("\n" + "=" * 60)
    print("A/B 測試框架示範完成")
    print("=" * 60)


if __name__ == "__main__":
    demo_ab_testing()
