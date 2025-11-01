"""
推薦系統命令列工具
實作互動式命令列介面，允許輸入會員資訊並顯示推薦結果
"""
import sys
from pathlib import Path
import logging

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.recommendation_engine import RecommendationEngine
from src.models.data_models import MemberInfo
from src.config import settings

# 設置日誌
logging.basicConfig(
    level=logging.WARNING,  # CLI 只顯示警告和錯誤
    format='%(levelname)s: %(message)s'
)


class RecommendCLI:
    """推薦系統命令列介面"""
    
    def __init__(self):
        """初始化 CLI"""
        self.engine = None
        print("=" * 70)
        print(" " * 20 + "產品推薦系統 CLI")
        print("=" * 70)
    
    def initialize_engine(self):
        """初始化推薦引擎"""
        print("\n正在載入推薦引擎...")
        try:
            self.engine = RecommendationEngine()
            print("✓ 推薦引擎載入成功")
            return True
        except FileNotFoundError as e:
            print(f"✗ 錯誤: 模型未找到")
            print(f"  {e}")
            print("\n請先訓練模型: python src/train.py")
            return False
        except Exception as e:
            print(f"✗ 錯誤: 推薦引擎初始化失敗")
            print(f"  {e}")
            return False
    
    def get_member_info(self) -> MemberInfo:
        """
        互動式獲取會員資訊
        
        Returns:
            MemberInfo: 會員資訊物件
        """
        print("\n" + "=" * 70)
        print("請輸入會員資訊")
        print("=" * 70)
        
        # 會員編號
        while True:
            member_code = input("\n會員編號 (必填): ").strip()
            if member_code:
                break
            print("  ✗ 會員編號不能為空")
        
        # 電話號碼
        phone = input("電話號碼 (選填，按 Enter 跳過): ").strip() or None
        
        # 總消費金額
        while True:
            try:
                consumption_input = input("總消費金額 (必填): ").strip()
                total_consumption = float(consumption_input)
                if total_consumption >= 0:
                    break
                print("  ✗ 消費金額不能為負數")
            except ValueError:
                print("  ✗ 請輸入有效的數字")
        
        # 累積紅利
        while True:
            try:
                bonus_input = input("累積紅利 (必填): ").strip()
                accumulated_bonus = float(bonus_input)
                if accumulated_bonus >= 0:
                    break
                print("  ✗ 累積紅利不能為負數")
            except ValueError:
                print("  ✗ 請輸入有效的數字")
        
        # 最近購買
        print("\n最近購買的產品 ID (選填，多個用逗號分隔，按 Enter 跳過):")
        recent_input = input("產品 ID: ").strip()
        recent_purchases = []
        if recent_input:
            recent_purchases = [p.strip() for p in recent_input.split(',') if p.strip()]
        
        # 建立會員資訊
        member_info = MemberInfo(
            member_code=member_code,
            phone=phone,
            total_consumption=total_consumption,
            accumulated_bonus=accumulated_bonus,
            recent_purchases=recent_purchases
        )
        
        return member_info
    
    def display_recommendations(self, recommendations, member_code: str):
        """
        顯示推薦結果
        
        Args:
            recommendations: 推薦列表
            member_code: 會員編號
        """
        print("\n" + "=" * 70)
        print(f"為會員 {member_code} 的推薦結果")
        print("=" * 70)
        
        if not recommendations:
            print("\n✗ 沒有找到推薦產品")
            return
        
        print(f"\n找到 {len(recommendations)} 個推薦產品:\n")
        
        for rec in recommendations:
            print(f"【推薦 {rec.rank}】")
            print(f"  產品 ID: {rec.product_id}")
            print(f"  產品名稱: {rec.product_name}")
            print(f"  信心分數: {rec.confidence_score:.1f}%")
            print(f"  推薦理由: {rec.explanation}")
            print(f"  推薦來源: {rec.source.value}")
            print()
    
    def run(self):
        """執行 CLI 主程式"""
        # 初始化推薦引擎
        if not self.initialize_engine():
            return 1
        
        while True:
            try:
                # 獲取會員資訊
                member_info = self.get_member_info()
                
                # 生成推薦
                print("\n正在生成推薦...")
                recommendations = self.engine.recommend(member_info, n=5)
                
                # 顯示推薦結果
                self.display_recommendations(recommendations, member_info.member_code)
                
                # 詢問是否繼續
                print("=" * 70)
                continue_input = input("\n是否繼續推薦？(y/n): ").strip().lower()
                if continue_input not in ['y', 'yes', '是']:
                    break
                
            except KeyboardInterrupt:
                print("\n\n操作已取消")
                break
            except Exception as e:
                print(f"\n✗ 錯誤: {e}")
                continue_input = input("\n是否繼續？(y/n): ").strip().lower()
                if continue_input not in ['y', 'yes', '是']:
                    break
        
        print("\n" + "=" * 70)
        print("感謝使用產品推薦系統！")
        print("=" * 70)
        return 0


def main():
    """主函數"""
    cli = RecommendCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
