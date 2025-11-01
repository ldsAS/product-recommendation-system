"""
推薦理由生成器示範腳本
展示如何使用 ExplanationGenerator 生成推薦理由
"""
import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.explanation_generator import ExplanationGenerator
from src.models.data_models import MemberInfo, RecommendationSource


def demo_basic_explanation():
    """示範基本推薦理由生成"""
    print("=" * 70)
    print("示範 1: 基本推薦理由生成")
    print("=" * 70)
    
    # 建立生成器
    generator = ExplanationGenerator()
    
    # 測試會員資訊
    member_info = MemberInfo(
        member_code="CU000001",
        phone="0937024682",
        total_consumption=17400.0,
        accumulated_bonus=500.0,
        recent_purchases=["30463", "31033"]
    )
    
    print(f"\n會員資訊:")
    print(f"  會員編號: {member_info.member_code}")
    print(f"  總消費金額: ${member_info.total_consumption:,.0f}")
    print(f"  累積紅利: {member_info.accumulated_bonus:,.0f} 點")
    print(f"  最近購買: {', '.join(member_info.recent_purchases)}")
    
    # 生成推薦理由
    product_id = "30469"
    confidence_score = 85.5
    
    explanation = generator.generate_explanation(
        member_info=member_info,
        product_id=product_id,
        confidence_score=confidence_score,
        source=RecommendationSource.ML_MODEL
    )
    
    print(f"\n推薦產品: {product_id}")
    print(f"信心分數: {confidence_score}")
    print(f"推薦理由: {explanation}")


def demo_different_sources():
    """示範不同推薦來源的理由"""
    print("\n" + "=" * 70)
    print("示範 2: 不同推薦來源的理由")
    print("=" * 70)
    
    generator = ExplanationGenerator()
    
    member_info = MemberInfo(
        member_code="CU000002",
        total_consumption=25000.0,
        accumulated_bonus=800.0,
        recent_purchases=["30463", "31033", "30469"]
    )
    
    product_id = "31463"
    confidence_score = 78.2
    
    sources = [
        (RecommendationSource.ML_MODEL, "機器學習模型"),
        (RecommendationSource.COLLABORATIVE_FILTERING, "協同過濾"),
        (RecommendationSource.CONTENT_BASED, "內容基礎"),
        (RecommendationSource.RULE_BASED, "規則基礎"),
        (RecommendationSource.FALLBACK, "備用推薦"),
    ]
    
    print(f"\n推薦產品: {product_id}")
    print(f"信心分數: {confidence_score}")
    print(f"\n不同來源的推薦理由:")
    
    for source, source_name in sources:
        explanation = generator.generate_explanation(
            member_info=member_info,
            product_id=product_id,
            confidence_score=confidence_score,
            source=source
        )
        print(f"\n  [{source_name}]")
        print(f"  {explanation}")


def demo_detailed_explanation():
    """示範詳細推薦理由"""
    print("\n" + "=" * 70)
    print("示範 3: 詳細推薦理由")
    print("=" * 70)
    
    generator = ExplanationGenerator()
    
    member_info = MemberInfo(
        member_code="CU000003",
        phone="0912345678",
        total_consumption=35000.0,
        accumulated_bonus=1200.0,
        recent_purchases=["30463", "31033", "30469", "31463"]
    )
    
    product_id = "30470"
    confidence_score = 92.3
    
    detailed = generator.generate_detailed_explanation(
        member_info=member_info,
        product_id=product_id,
        confidence_score=confidence_score
    )
    
    print(f"\n推薦產品: {product_id}")
    print(f"\n摘要: {detailed['summary']}")
    print(f"信心分數: {detailed['confidence_score']}")
    
    print(f"\n關鍵因素:")
    for factor in detailed['key_factors']:
        print(f"  • {factor['factor']}: {factor['description']}")


def demo_confidence_levels():
    """示範不同信心分數的理由"""
    print("\n" + "=" * 70)
    print("示範 4: 不同信心分數的推薦理由")
    print("=" * 70)
    
    generator = ExplanationGenerator()
    
    member_info = MemberInfo(
        member_code="CU000004",
        total_consumption=15000.0,
        accumulated_bonus=400.0,
        recent_purchases=["30463"]
    )
    
    product_id = "31033"
    
    confidence_levels = [95.0, 75.0, 55.0, 35.0]
    
    print(f"\n推薦產品: {product_id}")
    print(f"\n不同信心分數的推薦理由:")
    
    for confidence in confidence_levels:
        explanation = generator.generate_explanation(
            member_info=member_info,
            product_id=product_id,
            confidence_score=confidence,
            source=RecommendationSource.ML_MODEL
        )
        print(f"\n  信心分數 {confidence}%:")
        print(f"  {explanation}")


def main():
    """主函數"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "推薦理由生成器示範" + " " * 20 + "║")
    print("╚" + "═" * 68 + "╝")
    
    try:
        # 執行各個示範
        demo_basic_explanation()
        demo_different_sources()
        demo_detailed_explanation()
        demo_confidence_levels()
        
        # 總結
        print("\n" + "=" * 70)
        print("✓ 所有示範完成！")
        print("=" * 70)
        print("\n推薦理由生成器功能:")
        print("  • 支援多種推薦來源（ML模型、協同過濾、內容基礎等）")
        print("  • 根據會員資訊生成個性化理由")
        print("  • 根據信心分數調整推薦語氣")
        print("  • 提供詳細推薦理由和關鍵因素")
        print("\n")
        
    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
