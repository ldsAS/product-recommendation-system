"""
特徵工程器示範腳本
"""
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_processing.data_loader import DataLoader
from src.data_processing.data_cleaner import DataCleaner
from src.data_processing.feature_engineer import FeatureEngineer

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_complete_pipeline():
    """示範完整的資料處理管線"""
    print("\n" + "=" * 60)
    print("示範: 完整資料處理管線")
    print("=" * 60)
    
    # 步驟 1: 載入資料
    print("\n步驟 1: 載入資料...")
    loader = DataLoader()
    df = loader.merge_data(max_rows=1000)
    
    if df.empty:
        print("✗ 資料載入失敗")
        return
    
    print(f"✓ 載入 {len(df)} 筆記錄")
    
    # 步驟 2: 清理資料
    print("\n步驟 2: 清理資料...")
    cleaner = DataCleaner()
    df = cleaner.clean_all(df)
    print(f"✓ 清理後 {len(df)} 筆記錄")
    
    # 步驟 3: 特徵工程
    print("\n步驟 3: 特徵工程...")
    engineer = FeatureEngineer()
    
    # 建立會員特徵矩陣
    feature_matrix = engineer.create_feature_matrix(df)
    print(f"✓ 會員特徵矩陣: {len(feature_matrix)} 個會員, {len(feature_matrix.columns)} 個特徵")
    
    # 建立產品特徵
    product_features = engineer.create_product_features(df)
    print(f"✓ 產品特徵: {len(product_features)} 個產品")
    
    # 顯示特徵摘要
    print("\n特徵摘要:")
    summary = engineer.get_feature_summary(feature_matrix)
    print(f"  數值特徵: {len(summary['numeric_features'])} 個")
    print(f"  類別特徵: {len(summary['categorical_features'])} 個")
    
    # 顯示範例
    print("\n會員特徵範例（前 3 個）:")
    display_cols = ['member_code', 'recency', 'frequency', 'monetary', 'product_diversity']
    available_cols = [col for col in display_cols if col in feature_matrix.columns]
    if available_cols:
        print(feature_matrix[available_cols].head(3))
    
    print("\n產品特徵範例（前 5 個）:")
    display_cols = ['stock_id', 'stock_description', 'avg_price', 'total_sales', 'popularity_score']
    available_cols = [col for col in display_cols if col in product_features.columns]
    if available_cols:
        print(product_features[available_cols].head(5))
    
    return feature_matrix, product_features


def demo_rfm_analysis():
    """示範 RFM 分析"""
    print("\n" + "=" * 60)
    print("示範: RFM 分析")
    print("=" * 60)
    
    loader = DataLoader()
    df = loader.merge_data(max_rows=500)
    
    if df.empty:
        return
    
    cleaner = DataCleaner()
    df = cleaner.clean_all(df)
    
    engineer = FeatureEngineer()
    rfm_df = engineer.calculate_rfm(df)
    
    print(f"\nRFM 統計:")
    print(f"  Recency (最近購買):")
    print(f"    平均: {rfm_df['recency'].mean():.1f} 天")
    print(f"    中位數: {rfm_df['recency'].median():.1f} 天")
    
    print(f"  Frequency (購買頻率):")
    print(f"    平均: {rfm_df['frequency'].mean():.1f} 次")
    print(f"    中位數: {rfm_df['frequency'].median():.1f} 次")
    
    print(f"  Monetary (平均金額):")
    print(f"    平均: ${rfm_df['monetary'].mean():.2f}")
    print(f"    中位數: ${rfm_df['monetary'].median():.2f}")


def main():
    """主函數"""
    print("=" * 60)
    print("特徵工程器示範")
    print("=" * 60)
    
    try:
        demo_complete_pipeline()
        demo_rfm_analysis()
        
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
