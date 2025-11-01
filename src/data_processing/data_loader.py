"""
資料載入器
負責讀取原始 JSON Lines 格式的資料檔案並合併
"""
import json
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
from tqdm import tqdm
import logging

from src.config import settings

# 設置日誌
logger = logging.getLogger(__name__)


class DataLoader:
    """資料載入器類別"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        初始化資料載入器
        
        Args:
            data_dir: 資料目錄路徑，預設使用配置中的路徑
        """
        self.data_dir = data_dir or settings.RAW_DATA_DIR
        logger.info(f"資料載入器初始化，資料目錄: {self.data_dir}")
    
    def load_json_lines(
        self, 
        file_path: Path, 
        chunk_size: Optional[int] = None,
        max_rows: Optional[int] = None
    ) -> pd.DataFrame:
        """
        載入 JSON Lines 格式的檔案
        
        Args:
            file_path: 檔案路徑
            chunk_size: 分批讀取的大小，None 表示一次讀取全部
            max_rows: 最大讀取行數，None 表示讀取全部
            
        Returns:
            DataFrame
        """
        logger.info(f"開始載入檔案: {file_path}")
        
        if not file_path.exists():
            raise FileNotFoundError(f"檔案不存在: {file_path}")
        
        records = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(tqdm(f, desc=f"載入 {file_path.name}")):
                    # 檢查是否達到最大行數
                    if max_rows and i >= max_rows:
                        logger.info(f"達到最大行數限制: {max_rows}")
                        break
                    
                    # 跳過空行
                    if not line.strip():
                        continue
                    
                    try:
                        record = json.loads(line.strip())
                        records.append(record)
                        
                        # 分批處理
                        if chunk_size and len(records) >= chunk_size:
                            logger.debug(f"已載入 {len(records)} 筆記錄")
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"第 {i+1} 行 JSON 解析失敗: {e}")
                        continue
            
            if not records:
                logger.warning(f"檔案 {file_path} 沒有有效的記錄")
                return pd.DataFrame()
            
            df = pd.DataFrame(records)
            logger.info(f"成功載入 {len(df)} 筆記錄，{len(df.columns)} 個欄位")
            
            return df
            
        except Exception as e:
            logger.error(f"載入檔案時發生錯誤: {e}")
            raise
    
    def load_members(
        self, 
        file_name: Optional[str] = None,
        max_rows: Optional[int] = None
    ) -> pd.DataFrame:
        """
        載入會員資料
        
        Args:
            file_name: 檔案名稱，預設使用配置中的名稱
            max_rows: 最大讀取行數
            
        Returns:
            會員資料 DataFrame
        """
        file_name = file_name or settings.MEMBER_FILE
        file_path = self.data_dir / file_name
        
        logger.info("載入會員資料...")
        df = self.load_json_lines(file_path, max_rows=max_rows)
        
        # 基本資料清理
        if not df.empty:
            # 確保關鍵欄位存在
            required_columns = ['id', 'member_code']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.warning(f"會員資料缺少欄位: {missing_columns}")
            
            logger.info(f"會員資料載入完成: {len(df)} 筆記錄")
        
        return df
    
    def load_sales(
        self, 
        file_name: Optional[str] = None,
        max_rows: Optional[int] = None
    ) -> pd.DataFrame:
        """
        載入銷售訂單資料
        
        Args:
            file_name: 檔案名稱，預設使用配置中的名稱
            max_rows: 最大讀取行數
            
        Returns:
            銷售訂單資料 DataFrame
        """
        file_name = file_name or settings.SALES_FILE
        file_path = self.data_dir / file_name
        
        logger.info("載入銷售訂單資料...")
        df = self.load_json_lines(file_path, max_rows=max_rows)
        
        # 基本資料清理
        if not df.empty:
            # 確保關鍵欄位存在
            required_columns = ['id', 'member', 'date']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.warning(f"銷售訂單資料缺少欄位: {missing_columns}")
            
            # 轉換日期欄位
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            
            logger.info(f"銷售訂單資料載入完成: {len(df)} 筆記錄")
        
        return df
    
    def load_sales_details(
        self, 
        file_name: Optional[str] = None,
        max_rows: Optional[int] = None
    ) -> pd.DataFrame:
        """
        載入銷售明細資料
        
        Args:
            file_name: 檔案名稱，預設使用配置中的名稱
            max_rows: 最大讀取行數
            
        Returns:
            銷售明細資料 DataFrame
        """
        file_name = file_name or settings.SALES_DETAILS_FILE
        file_path = self.data_dir / file_name
        
        logger.info("載入銷售明細資料...")
        df = self.load_json_lines(file_path, max_rows=max_rows)
        
        # 基本資料清理
        if not df.empty:
            # 確保關鍵欄位存在
            required_columns = ['id', 'sales_id', 'stock_id']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.warning(f"銷售明細資料缺少欄位: {missing_columns}")
            
            logger.info(f"銷售明細資料載入完成: {len(df)} 筆記錄")
        
        return df
    
    def merge_data(
        self,
        members_df: Optional[pd.DataFrame] = None,
        sales_df: Optional[pd.DataFrame] = None,
        sales_details_df: Optional[pd.DataFrame] = None,
        max_rows: Optional[int] = None
    ) -> pd.DataFrame:
        """
        合併會員、銷售訂單和銷售明細資料
        
        合併邏輯:
        member ← sales (on member.id = sales.member)
               ← salesdetails (on sales.id = salesdetails.sales_id)
        
        Args:
            members_df: 會員資料，None 則自動載入
            sales_df: 銷售訂單資料，None 則自動載入
            sales_details_df: 銷售明細資料，None 則自動載入
            max_rows: 最大讀取行數（僅在自動載入時使用）
            
        Returns:
            合併後的 DataFrame
        """
        logger.info("開始合併資料...")
        
        # 載入資料（如果未提供）
        if members_df is None:
            members_df = self.load_members(max_rows=max_rows)
        
        if sales_df is None:
            sales_df = self.load_sales(max_rows=max_rows)
        
        if sales_details_df is None:
            sales_details_df = self.load_sales_details(max_rows=max_rows)
        
        # 檢查資料是否為空
        if members_df.empty or sales_df.empty or sales_details_df.empty:
            logger.warning("部分資料為空，無法合併")
            return pd.DataFrame()
        
        # 第一步：合併 sales 和 salesdetails
        logger.info("合併銷售訂單和銷售明細...")
        sales_with_details = pd.merge(
            sales_df,
            sales_details_df,
            left_on='id',
            right_on='sales_id',
            how='inner',
            suffixes=('_sales', '_details')
        )
        logger.info(f"銷售訂單與明細合併後: {len(sales_with_details)} 筆記錄")
        
        # 第二步：合併 member 和 sales_with_details
        logger.info("合併會員資料...")
        merged_df = pd.merge(
            members_df,
            sales_with_details,
            left_on='id',
            right_on='member',
            how='inner',
            suffixes=('_member', '_sales')
        )
        logger.info(f"最終合併結果: {len(merged_df)} 筆記錄")
        
        # 重新命名關鍵欄位以避免混淆
        if 'id_member' in merged_df.columns:
            merged_df.rename(columns={'id_member': 'member_id'}, inplace=True)
        if 'id_sales' in merged_df.columns:
            merged_df.rename(columns={'id_sales': 'sales_id'}, inplace=True)
        if 'id_details' in merged_df.columns:
            merged_df.rename(columns={'id_details': 'sales_detail_id'}, inplace=True)
        
        logger.info(f"資料合併完成，共 {len(merged_df)} 筆記錄，{len(merged_df.columns)} 個欄位")
        
        return merged_df
    
    def load_all_data(self, max_rows: Optional[int] = None) -> Dict[str, pd.DataFrame]:
        """
        載入所有資料並返回字典
        
        Args:
            max_rows: 最大讀取行數
            
        Returns:
            包含所有資料的字典
        """
        logger.info("載入所有資料...")
        
        data = {
            'members': self.load_members(max_rows=max_rows),
            'sales': self.load_sales(max_rows=max_rows),
            'sales_details': self.load_sales_details(max_rows=max_rows),
        }
        
        # 合併資料
        data['merged'] = self.merge_data(
            members_df=data['members'],
            sales_df=data['sales'],
            sales_details_df=data['sales_details']
        )
        
        logger.info("所有資料載入完成")
        
        return data
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        獲取資料摘要資訊
        
        Args:
            df: DataFrame
            
        Returns:
            摘要資訊字典
        """
        if df.empty:
            return {'empty': True}
        
        summary = {
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': df.columns.tolist(),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024,
            'dtypes': df.dtypes.astype(str).to_dict(),
        }
        
        return summary


def main():
    """測試資料載入器"""
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("測試資料載入器")
    print("=" * 60)
    
    # 建立資料載入器
    loader = DataLoader()
    
    # 測試載入少量資料
    print("\n測試載入會員資料（前 100 筆）...")
    members_df = loader.load_members(max_rows=100)
    print(f"✓ 載入 {len(members_df)} 筆會員資料")
    print(f"  欄位: {list(members_df.columns[:5])}...")
    
    print("\n測試載入銷售訂單資料（前 100 筆）...")
    sales_df = loader.load_sales(max_rows=100)
    print(f"✓ 載入 {len(sales_df)} 筆銷售訂單")
    print(f"  欄位: {list(sales_df.columns[:5])}...")
    
    print("\n測試載入銷售明細資料（前 100 筆）...")
    sales_details_df = loader.load_sales_details(max_rows=100)
    print(f"✓ 載入 {len(sales_details_df)} 筆銷售明細")
    print(f"  欄位: {list(sales_details_df.columns[:5])}...")
    
    print("\n測試資料合併...")
    merged_df = loader.merge_data(
        members_df=members_df,
        sales_df=sales_df,
        sales_details_df=sales_details_df
    )
    print(f"✓ 合併後 {len(merged_df)} 筆記錄")
    
    print("\n資料摘要:")
    summary = loader.get_data_summary(merged_df)
    print(f"  總行數: {summary['rows']}")
    print(f"  總欄位數: {summary['columns']}")
    print(f"  記憶體使用: {summary['memory_usage_mb']:.2f} MB")
    
    print("\n" + "=" * 60)
    print("✓ 資料載入器測試完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
