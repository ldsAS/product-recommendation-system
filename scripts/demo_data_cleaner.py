"""
資料清理器示範腳本
"""
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_processing.data_loader import DataLoader
from src.data_processing.data_cleaner import DataCleaner

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_basic_cleaning():
    """示範基本清理功能"""
    print("\n" + "=" * 60)
    print("示範 1: 基本資料清理")
    print("=" * 60)
    
    # 載入資料
    loader = DataLoader()
    print("\n載入會員資料（前 1000 筆）...")
    df = loader.load_members(max_rows=1000)
    print(f"原始資料: {len(df)} 筆記錄")
    
    # 建立清理器
    cleaner = DataCleaner()
    
    # 執行清理
    print("\n執行資料清理...")
    cleaned_df = cleaner.clean_all(df, handle_outliers_flag=False)
    
    print(f"\n清理後資料: {len(cleaned_df)} 筆記錄")
    
    # 顯示清理報告
    report = cleaner.get_cleaning_report()
    print("\n清理報告:")
    print(f"  移除記錄: {report['removed_rows']}")
    print(f"  填補缺失值: {report['filled_values']}")
    print(f"  標準化欄位: {report['standardized_fields']}")
    
    if report['issues']:
        print(f"  發現問題: {len(report['issues'])} 個")


def demo_merged_data_cleaning():
    """示範合併資料清理"""
    print("\n" + "=" * 60)
    print("示範 2: 合併資料清理")
    print("=" * 60)
    
    # 載入並合併資料
    loader = DataLoader()
    print("\n載入並合併資料（各前 500 筆）...")
    merged_df = loader.merge_data(max_rows=500)
    
    if merged_df.empty:
        print("✗ 資料合併失敗或為空")
        return
    
    print(f"合併資料: {len(merged_df)} 筆記錄")
    
    # 建立清理器
    cleaner = DataCleaner()
    
    # 執行清理
    print("\n執行資料清理...")
    cleaned_df = cleaner.clean_all(merged_df)
    
    print(f"\n清理後資料: {len(cleaned_df)} 筆記錄")
    
    # 顯示清理報告
    report = cleaner.get_cleaning_report()
    print("\n清理報告:")
    print(f"  移除記錄: {report['removed_rows']}")
    print(f"  填補缺失值: {report['filled_values']}")
    print(f"  標準化欄位: {report['standardized_fields']}")


def demo_custom_cleaning():
    """示範自訂清理"""
    print("\n" + "=" * 60)
    print("示範 3: 自訂清理策略")
    print("=" * 60)
    
    # 載入資料
    loader = DataLoader()
    print("\n載入銷售資料（前 1000 筆）...")
    df = loader.load_sales(max_rows=1000)
    print(f"原始資料: {len(df)} 筆記錄")
    
    # 建立清理器
    cleaner = DataCleaner()
    
    # 自訂缺失值處理策略
    custom_strategy = {
        'total': 'zero',
        'actualTotal': 'zero',
        'user_name': 'empty_string',
    }
    
    print("\n執行自訂清理...")
    df = cleaner.handle_missing_values(df, strategy=custom_strategy)
    df = cleaner.standardize_dates(df)
    df = cleaner.remove_duplicates(df, subset=['id'])
    
    print(f"\n清理後資料: {len(df)} 筆記錄")
    
    # 顯示清理報告
    report = cleaner.get_cleaning_report()
    print("\n清理報告:")
    print(f"  移除記錄: {report['removed_rows']}")
    print(f"  填補缺失值: {report['filled_values']}")


def main():
    """主函數"""
    print("=" * 60)
    print("資料清理器示範")
    print("=" * 60)
    
    try:
        demo_basic_cleaning()
        demo_merged_data_cleaning()
        demo_custom_cleaning()
        
        print("\n" + "=" * 60)
        print("✓ 所有示範完成！")
        print("=" * 60)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"\n✗ 檔案未找到: {e}")
        return 1
        
    except Exception as e:
        print(f"\n✗ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
