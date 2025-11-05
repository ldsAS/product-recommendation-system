"""
推薦理由生成器演示
展示 ReasonGenerator 的功能
"""
import pandas as pd
from src.models.reason_generator import ReasonGenerator
from src.models.data_models import MemberInfo, RecommendationSource
from src.models.enhanced_data_models import MemberHistory


def main():
    print("=" * 80)
    print("推薦理由生成器演示")
    print("=" * 80)
    
    # 建立測試用產品特徵
    product_features = pd.DataFrame({
        'stock_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
        'stock_description': [
            '杏輝蓉憶記膠囊',
            '杏輝南極磷蝦油軟膠囊',
            '活力維生素C錠',
            '保健營養補充品',
            '美妝保養精華液'
        ],
        'avg_price': [1200, 1500, 800, 600, 2000]
    })
    
    # 初始化生成器
    generator = ReasonGenerator(
        product_features=product_features,
        member_features=None
    )
    
    print("\n1. 高價值會員 - 高信心分數推薦")
    print("-" * 80)
    
    high_value_member = MemberInfo(
        member_code="M001",
        phone="0912345678",
        total_consumption=25000.0,
        accumulated_bonus=1000.0,
        recent_purchases=["P001", "P002"]
    )
    
    member_history = MemberHistory(
        member_code="M001",
        purchased_products=["P001", "P002"],
        purchased_categories=["保健"],
        purchased_brands=["杏輝"],
        avg_purchase_price=1350.0,
        price_std=150.0
    )
    
    reason = generator.generate_reason(
        member_info=high_value_member,
        product_id="P003",
        confidence_score=90.0,
        member_history=member_history,
        max_reasons=2
    )
    
    print(f"會員: {high_value_member.member_code}")
    print(f"消費金額: ${high_value_member.total_consumption:,.0f}")
    print(f"推薦產品: {product_features[product_features['stock_id']=='P003'].iloc[0]['stock_description']}")
    print(f"信心分數: 90.0")
    print(f"推薦理由: {reason}")
    
    print("\n2. 中等價值會員 - 中等信心分數推薦")
    print("-" * 80)
    
    generator.reset_used_reasons()
    
    medium_value_member = MemberInfo(
        member_code="M002",
        phone="0923456789",
        total_consumption=12000.0,
        accumulated_bonus=500.0,
        recent_purchases=["P003"]
    )
    
    reason = generator.generate_reason(
        member_info=medium_value_member,
        product_id="P004",
        confidence_score=70.0,
        max_reasons=2
    )
    
    print(f"會員: {medium_value_member.member_code}")
    print(f"消費金額: ${medium_value_member.total_consumption:,.0f}")
    print(f"推薦產品: {product_features[product_features['stock_id']=='P004'].iloc[0]['stock_description']}")
    print(f"信心分數: 70.0")
    print(f"推薦理由: {reason}")
    
    print("\n3. 新會員 - 低信心分數推薦")
    print("-" * 80)
    
    generator.reset_used_reasons()
    
    new_member = MemberInfo(
        member_code="M003",
        phone="0934567890",
        total_consumption=3000.0,
        accumulated_bonus=100.0,
        recent_purchases=[]
    )
    
    reason = generator.generate_reason(
        member_info=new_member,
        product_id="P005",
        confidence_score=45.0,
        max_reasons=2
    )
    
    print(f"會員: {new_member.member_code}")
    print(f"消費金額: ${new_member.total_consumption:,.0f}")
    print(f"推薦產品: {product_features[product_features['stock_id']=='P005'].iloc[0]['stock_description']}")
    print(f"信心分數: 45.0")
    print(f"推薦理由: {reason}")
    
    print("\n4. 協同過濾推薦")
    print("-" * 80)
    
    generator.reset_used_reasons()
    
    reason = generator.generate_reason(
        member_info=high_value_member,
        product_id="P004",
        confidence_score=75.0,
        source=RecommendationSource.COLLABORATIVE_FILTERING,
        max_reasons=2
    )
    
    print(f"會員: {high_value_member.member_code}")
    print(f"推薦產品: {product_features[product_features['stock_id']=='P004'].iloc[0]['stock_description']}")
    print(f"推薦來源: 協同過濾")
    print(f"信心分數: 75.0")
    print(f"推薦理由: {reason}")
    
    print("\n5. 批次推薦 - 測試多樣性")
    print("-" * 80)
    
    generator.reset_used_reasons()
    
    products = ["P001", "P002", "P003", "P004", "P005"]
    
    print(f"會員: {high_value_member.member_code}")
    print(f"生成 {len(products)} 個推薦理由:\n")
    
    for i, product_id in enumerate(products, 1):
        reason = generator.generate_reason(
            member_info=high_value_member,
            product_id=product_id,
            confidence_score=80.0 - i * 5,
            member_history=member_history,
            max_reasons=2
        )
        
        product_name = product_features[product_features['stock_id']==product_id].iloc[0]['stock_description']
        print(f"{i}. {product_name}")
        print(f"   理由: {reason}\n")
    
    print("\n6. 理由數量限制測試")
    print("-" * 80)
    
    generator.reset_used_reasons()
    
    print("測試不同的理由數量限制:\n")
    
    for max_reasons in [1, 2, 3]:
        reason = generator.generate_reason(
            member_info=high_value_member,
            product_id="P001",
            confidence_score=85.0,
            member_history=member_history,
            max_reasons=max_reasons
        )
        
        reason_count = reason.count('、') + 1
        print(f"最多 {max_reasons} 個理由: {reason}")
        print(f"實際理由數: {reason_count}\n")
    
    print("=" * 80)
    print("演示完成！")
    print("=" * 80)
    
    print("\n功能特點:")
    print("✓ 基於消費水平選擇理由")
    print("✓ 基於信心分數調整語氣")
    print("✓ 基於產品類別提供建議")
    print("✓ 基於品牌偏好推薦")
    print("✓ 確保理由多樣性")
    print("✓ 限制理由數量（預設2個）")
    print("✓ 支援多種推薦來源")


if __name__ == "__main__":
    main()
