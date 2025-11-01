"""
資料載入器示範腳本
展示如何使用 DataLoader 載入和合併資料
"""
import sys
from pathlib import Path
import logging

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_processing.data_loader import DataLoader
from src.config import settings

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_basic_loading():
    """示範基本載入功能"""
    print("\n" + "=" * 60)
    print("示範 1: 基本資料載入")
    print("=" * 60)
    
    loader = DataLoader()
    
    # 載入少量資料進行測試
    print("\n載入會員資料（前 1000 筆）...")
    members_df = loader.load_members(max_rows=1000)
    print(f"✓ 載入 {len(members_df)} 筆會員資料")
    print(f"  欄位數: {len(members_df.columns)}")
    print(f"  前 5 個欄位: {list(members_df.columns[:5])}")
    
    if not members_df.empty:
        print(f"\n範例資料（前 3 筆）:")
        print(members_df[['id', 'member_code', 'member_name', 'total_consumption']].head(3))


def demo_sales_loading():
    """示範銷售資料載入"""
    print("\n" + "=" * 60)
    print("示範 2: 銷售資料載入")
    print("=" * 60)
    
    loader = DataLoader()
    
    print("\n載入銷售訂單資料（前 1000 筆）...")
    sales_df = loader.load_sales(max_rows=1000)
    print(f"✓ 載入 {len(sales_df)} 筆銷售訂單")
    
    if not sales_df.empty:
        print(f"\n範例資料（前 3 筆）:")
        print(sales_df[['id', 'no', 'date', 'member', 'total']].head(3))
        
        # 檢查日期轉換
        print(f"\n日期欄位類型: {sales_df['date'].dtype}")


def demo_merge():
    """示範資料合併"""
    print("\n" + "=" * 60)
    print("示範 3: 資料合併")
    print("=" * 60)
    
    loader = DataLoader()
    
    print("\n載入並合併資料（各前 500 筆）...")
    merged_df = loader.merge_data(max_rows=500)
    
    if not merged_df.empty:
        print(f"✓ 合併完成")
        print(f"  總記錄數: {len(merged_df)}")
        print(f"  總欄位數: {len(merged_df.columns)}")
        
        # 顯示關鍵欄位
        key_columns = [
            'member_code', 'member_name', 'total_consumption',
            'date', 'stock_id', 'stock_description', 'quantity'
        ]
        available_columns = [col for col in key_columns if col in merged_df.columns]
        
        if available_columns:
            print(f"\n範例合併資料（前 3 筆）:")
            print(merged_df[available_columns].head(3))


def demo_data_summary():
    """示範資料摘要"""
    print("\n" + "=" * 60)
    print("示範 4: 資料摘要")
    print("=" * 60)
    
    loader = DataLoader()
    
    print("\n載入會員資料...")
    members_df = loader.load_members(max_rows=1000)
    
    print("\n獲取資料摘要...")
    summary = loader.get_data_summary(members_df)
    
    print(f"✓ 資料摘要:")
    print(f"  總行數: {summary.get('rows', 0):,}")
    print(f"  總欄位數: {summary.get('columns', 0)}")
    print(f"  記憶體使用: {summary.get('memory_usage_mb', 0):.2f} MB")
    
    if 'column_names' in summary:
        print(f"  欄位名稱（前 10 個）: {summary['column_names'][:10]}")


def main():
    """主函數"""
    print("=" * 60)
    print("資料載入器示範")
    print("=" * 60)
    print(f"資料目錄: {settings.RAW_DATA_DIR}")
    
    try:
        # 檢查資料目錄是否存在
        if not settings.RAW_DATA_DIR.exists():
            print(f"\n✗ 資料目錄不存在: {settings.RAW_DATA_DIR}")
            print("請確保資料檔案已放置在 data/raw/ 目錄中")
            return 1
        
        # 執行示範
        demo_basic_loading()
        demo_sales_loading()
        demo_merge()
        demo_data_summary()
        
        print("\n" + "=" * 60)
        print("✓ 所有示範完成！")
        print("=" * 60)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"\n✗ 檔案未找到: {e}")
        print("請確保以下檔案存在於 data/raw/ 目錄:")
        print("  - member")
        print("  - sales")
        print("  - salesdetails")
        return 1
        
    except Exception as e:
        print(f"\n✗ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
