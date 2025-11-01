"""
輸入驗證器示範腳本
展示如何使用驗證器驗證會員資訊和推薦請求
"""
import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.validators import (
    validate_member_info,
    validate_recommendation_request,
    validate_product,
    MemberInfoValidator,
    ValidationResult
)
from src.models.data_models import (
    MemberInfo, RecommendationRequest, Product
)


def demo_valid_member():
    """示範有效的會員資訊驗證"""
    print("=" * 70)
    print("示範 1: 有效的會員資訊")
    print("=" * 70)
    
    member = MemberInfo(
        member_code="CU000001",
        phone="0937024682",
        total_consumption=17400.0,
        accumulated_bonus=500.0,
        recent_purchases=["30463", "31033", "30469"]
    )
    
    print(f"\n會員資訊:")
    print(f"  會員編號: {member.member_code}")
    print(f"  電話: {member.phone}")
    print(f"  總消費: ${member.total_consumption:,.0f}")
    print(f"  累積紅利: {member.accumulated_bonus:,.0f} 點")
    print(f"  最近購買: {len(member.recent_purchases)} 個產品")
    
    result = validate_member_info(member)
    
    print(f"\n驗證結果:")
    print(f"  是否通過: {'✓ 是' if result.is_valid else '✗ 否'}")
    if not result.is_valid:
        print(f"  錯誤數量: {len(result.errors)}")
        for error in result.errors:
            print(f"    - {error['field']}: {error['message']}")


def demo_invalid_member():
    """示範無效的會員資訊驗證"""
    print("\n" + "=" * 70)
    print("示範 2: 無效的會員資訊")
    print("=" * 70)
    
    # 建立一個有多個錯誤的會員資訊
    try:
        member = MemberInfo(
            member_code="",  # 空的會員編號
            phone="12345",  # 無效的電話號碼
            total_consumption=-100.0,  # 負數消費
            accumulated_bonus=2000000.0,  # 超過上限
            recent_purchases=["30463", "30463", ""]  # 重複和空值
        )
    except Exception as e:
        print(f"\nPydantic 驗證錯誤: {e}")
        print("（某些錯誤在 Pydantic 層級就被攔截了）")
        return
    
    result = validate_member_info(member)
    
    print(f"\n驗證結果:")
    print(f"  是否通過: {'✓ 是' if result.is_valid else '✗ 否'}")
    if not result.is_valid:
        print(f"  錯誤數量: {len(result.errors)}")
        for error in result.errors:
            print(f"    - {error['field']}: {error['message']}")


def demo_phone_validation():
    """示範電話號碼驗證"""
    print("\n" + "=" * 70)
    print("示範 3: 電話號碼驗證")
    print("=" * 70)
    
    test_phones = [
        ("0937024682", "有效的手機號碼"),
        ("09-3702-4682", "有效的手機號碼（含連字號）"),
        ("02-12345678", "有效的市話號碼"),
        ("12345", "無效：太短"),
        ("09370246821234", "無效：太長"),
        ("0937abc682", "無效：包含字母"),
    ]
    
    print("\n測試不同的電話號碼格式:")
    for phone, description in test_phones:
        member = MemberInfo(
            member_code="CU000001",
            phone=phone,
            total_consumption=10000.0,
            accumulated_bonus=100.0
        )
        
        result = validate_member_info(member)
        status = "✓" if result.is_valid else "✗"
        print(f"  {status} {phone:20s} - {description}")
        
        if not result.is_valid:
            for error in result.errors:
                if error['field'] == 'phone':
                    print(f"      錯誤: {error['message']}")


def demo_consumption_validation():
    """示範消費金額驗證"""
    print("\n" + "=" * 70)
    print("示範 4: 消費金額驗證")
    print("=" * 70)
    
    test_consumptions = [
        (0.0, "最小值"),
        (10000.0, "正常值"),
        (1000000.0, "高消費"),
        (10000000.0, "最大值"),
        (10000001.0, "超過上限"),
    ]
    
    print("\n測試不同的消費金額:")
    for consumption, description in test_consumptions:
        member = MemberInfo(
            member_code="CU000001",
            total_consumption=consumption,
            accumulated_bonus=0.0
        )
        
        result = validate_member_info(member)
        status = "✓" if result.is_valid else "✗"
        print(f"  {status} ${consumption:15,.0f} - {description}")
        
        if not result.is_valid:
            for error in result.errors:
                if error['field'] == 'total_consumption':
                    print(f"      錯誤: {error['message']}")


def demo_recent_purchases_validation():
    """示範最近購買驗證"""
    print("\n" + "=" * 70)
    print("示範 5: 最近購買驗證")
    print("=" * 70)
    
    test_cases = [
        ([], "空列表"),
        (["30463"], "單一產品"),
        (["30463", "31033", "30469"], "多個產品"),
        (["30463", "30463"], "重複產品"),
        (["30463"] * 101, "超過上限（101個）"),
    ]
    
    print("\n測試不同的最近購買情況:")
    for purchases, description in test_cases:
        member = MemberInfo(
            member_code="CU000001",
            total_consumption=10000.0,
            accumulated_bonus=100.0,
            recent_purchases=purchases
        )
        
        result = validate_member_info(member)
        status = "✓" if result.is_valid else "✗"
        print(f"  {status} {len(purchases):3d} 個產品 - {description}")
        
        if not result.is_valid:
            for error in result.errors:
                if 'recent_purchases' in error['field']:
                    print(f"      錯誤: {error['message']}")


def demo_recommendation_request():
    """示範推薦請求驗證"""
    print("\n" + "=" * 70)
    print("示範 6: 推薦請求驗證")
    print("=" * 70)
    
    # 有效的請求
    print("\n有效的推薦請求:")
    valid_request = RecommendationRequest(
        member_code="CU000001",
        phone="0937024682",
        total_consumption=17400.0,
        accumulated_bonus=500.0,
        recent_purchases=["30463", "31033"],
        top_k=5,
        min_confidence=0.0
    )
    
    result = validate_recommendation_request(valid_request)
    print(f"  驗證結果: {'✓ 通過' if result.is_valid else '✗ 失敗'}")
    
    # 無效的請求
    print("\n無效的推薦請求（top_k 超過上限）:")
    invalid_request = RecommendationRequest(
        member_code="CU000001",
        total_consumption=10000.0,
        accumulated_bonus=100.0,
        top_k=25,  # 超過上限
        min_confidence=0.0
    )
    
    result = validate_recommendation_request(invalid_request)
    print(f"  驗證結果: {'✓ 通過' if result.is_valid else '✗ 失敗'}")
    if not result.is_valid:
        for error in result.errors:
            print(f"    - {error['field']}: {error['message']}")


def demo_product_validation():
    """示範產品驗證"""
    print("\n" + "=" * 70)
    print("示範 7: 產品驗證")
    print("=" * 70)
    
    # 有效的產品
    print("\n有效的產品:")
    valid_product = Product(
        stock_id="30469",
        stock_description="杏輝蓉憶記膠囊",
        avg_price=1200.0,
        popularity_score=0.85
    )
    
    result = validate_product(valid_product)
    print(f"  產品: {valid_product.stock_description}")
    print(f"  驗證結果: {'✓ 通過' if result.is_valid else '✗ 失敗'}")
    
    # 無效的產品
    print("\n無效的產品（價格超過上限）:")
    invalid_product = Product(
        stock_id="99999",
        stock_description="超貴產品",
        avg_price=2000000.0,  # 超過上限
        popularity_score=1.5  # 超過範圍
    )
    
    result = validate_product(invalid_product)
    print(f"  產品: {invalid_product.stock_description}")
    print(f"  驗證結果: {'✓ 通過' if result.is_valid else '✗ 失敗'}")
    if not result.is_valid:
        for error in result.errors:
            print(f"    - {error['field']}: {error['message']}")


def demo_business_logic():
    """示範業務邏輯驗證"""
    print("\n" + "=" * 70)
    print("示範 8: 業務邏輯驗證")
    print("=" * 70)
    
    print("\n測試紅利與消費金額的合理性:")
    
    # 合理的紅利
    print("\n1. 合理的紅利（10%）:")
    member1 = MemberInfo(
        member_code="CU000001",
        total_consumption=10000.0,
        accumulated_bonus=1000.0  # 10%
    )
    result = validate_member_info(member1)
    print(f"   消費: ${member1.total_consumption:,.0f}")
    print(f"   紅利: {member1.accumulated_bonus:,.0f} 點")
    print(f"   驗證: {'✓ 通過' if result.is_valid else '✗ 失敗'}")
    
    # 偏高的紅利（會有警告但不會失敗）
    print("\n2. 偏高的紅利（30%，會記錄警告）:")
    member2 = MemberInfo(
        member_code="CU000002",
        total_consumption=10000.0,
        accumulated_bonus=3000.0  # 30%
    )
    result = validate_member_info(member2)
    print(f"   消費: ${member2.total_consumption:,.0f}")
    print(f"   紅利: {member2.accumulated_bonus:,.0f} 點")
    print(f"   驗證: {'✓ 通過' if result.is_valid else '✗ 失敗'}")
    print(f"   註: 系統會記錄警告但不阻止驗證通過")


def main():
    """主函數"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 22 + "輸入驗證器示範" + " " * 22 + "║")
    print("╚" + "═" * 68 + "╝")
    
    try:
        # 執行各個示範
        demo_valid_member()
        demo_invalid_member()
        demo_phone_validation()
        demo_consumption_validation()
        demo_recent_purchases_validation()
        demo_recommendation_request()
        demo_product_validation()
        demo_business_logic()
        
        # 總結
        print("\n" + "=" * 70)
        print("✓ 所有示範完成！")
        print("=" * 70)
        print("\n驗證器功能:")
        print("  • 驗證會員資訊的必填欄位和格式")
        print("  • 驗證資料範圍（消費金額、紅利、產品數量等）")
        print("  • 驗證電話號碼格式")
        print("  • 驗證推薦請求參數")
        print("  • 驗證產品資訊")
        print("  • 檢查業務邏輯合理性")
        print("  • 生成明確的驗證錯誤訊息")
        print("\n")
        
        return 0
        
    except Exception as e:
        print(f"\n錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
