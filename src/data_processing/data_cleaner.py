"""
資料清理器
負責處理缺失值、異常值和資料品質問題
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DataCleaner:
    """資料清理器類別"""
    
    def __init__(self):
        """初始化資料清理器"""
        logger.info("資料清理器初始化")
        self.cleaning_report = {
            'removed_rows': 0,
            'filled_values': 0,
            'standardized_fields': 0,
            'issues': []
        }
    
    def remove_invalid_orders(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        移除無效的訂單記錄
        
        規則:
        - 移除金額為 0 且無產品的訂單
        - 移除缺少關鍵欄位的記錄
        
        Args:
            df: 輸入 DataFrame
            
        Returns:
            清理後的 DataFrame
        """
        logger.info("移除無效訂單...")
        initial_count = len(df)
        
        # 檢查是否有必要的欄位
        if 'actualTotal' in df.columns and 'stock_id' in df.columns:
            # 移除金額為 0 且無產品的訂單
            invalid_mask = (
                (df['actualTotal'].fillna(0) == 0) & 
                (df['stock_id'].isna())
            )
            df = df[~invalid_mask].copy()
            
            removed = initial_count - len(df)
            if removed > 0:
                logger.info(f"移除 {removed} 筆無效訂單（金額為0且無產品）")
                self.cleaning_report['removed_rows'] += removed
        
        # 移除關鍵欄位全為空的記錄
        key_columns = ['id', 'member_id', 'member_code']
        available_key_columns = [col for col in key_columns if col in df.columns]
        
        if available_key_columns:
            before = len(df)
            df = df.dropna(subset=available_key_columns, how='all').copy()
            removed = before - len(df)
            if removed > 0:
                logger.info(f"移除 {removed} 筆關鍵欄位全為空的記錄")
                self.cleaning_report['removed_rows'] += removed
        
        logger.info(f"無效訂單移除完成，剩餘 {len(df)} 筆記錄")
        return df
    
    def handle_missing_values(
        self, 
        df: pd.DataFrame,
        strategy: Dict[str, str] = None
    ) -> pd.DataFrame:
        """
        處理缺失值
        
        Args:
            df: 輸入 DataFrame
            strategy: 處理策略字典 {欄位名: 策略}
                     策略可以是: 'drop', 'mean', 'median', 'mode', 'zero', 'empty_string'
            
        Returns:
            處理後的 DataFrame
        """
        logger.info("處理缺失值...")
        
        if strategy is None:
            # 預設策略
            strategy = {
                'total_consumption': 'zero',
                'accumulated_bonus': 'zero',
                'actualTotal': 'zero',
                'quantity': 'zero',
                'price': 'zero',
                'member_name': 'empty_string',
                'phone': 'empty_string',
            }
        
        filled_count = 0
        
        for column, method in strategy.items():
            if column not in df.columns:
                continue
            
            missing_count = df[column].isna().sum()
            if missing_count == 0:
                continue
            
            if method == 'drop':
                df = df.dropna(subset=[column]).copy()
                logger.info(f"移除 {column} 欄位有缺失值的 {missing_count} 筆記錄")
                self.cleaning_report['removed_rows'] += missing_count
                
            elif method == 'mean':
                if pd.api.types.is_numeric_dtype(df[column]):
                    fill_value = df[column].mean()
                    df[column].fillna(fill_value, inplace=True)
                    filled_count += missing_count
                    logger.info(f"使用平均值 {fill_value:.2f} 填補 {column} 的 {missing_count} 個缺失值")
                    
            elif method == 'median':
                if pd.api.types.is_numeric_dtype(df[column]):
                    fill_value = df[column].median()
                    df[column].fillna(fill_value, inplace=True)
                    filled_count += missing_count
                    logger.info(f"使用中位數 {fill_value:.2f} 填補 {column} 的 {missing_count} 個缺失值")
                    
            elif method == 'mode':
                mode_value = df[column].mode()
                if len(mode_value) > 0:
                    df[column].fillna(mode_value[0], inplace=True)
                    filled_count += missing_count
                    logger.info(f"使用眾數填補 {column} 的 {missing_count} 個缺失值")
                    
            elif method == 'zero':
                df[column].fillna(0, inplace=True)
                filled_count += missing_count
                logger.info(f"使用 0 填補 {column} 的 {missing_count} 個缺失值")
                
            elif method == 'empty_string':
                df[column].fillna('', inplace=True)
                filled_count += missing_count
                logger.info(f"使用空字串填補 {column} 的 {missing_count} 個缺失值")
        
        self.cleaning_report['filled_values'] += filled_count
        logger.info(f"缺失值處理完成，共填補 {filled_count} 個值")
        
        return df
    
    def remove_duplicates(
        self, 
        df: pd.DataFrame,
        subset: Optional[List[str]] = None,
        keep: str = 'first'
    ) -> pd.DataFrame:
        """
        移除重複記錄
        
        Args:
            df: 輸入 DataFrame
            subset: 用於判斷重複的欄位列表，None 表示使用所有欄位
            keep: 保留策略 ('first', 'last', False)
            
        Returns:
            去重後的 DataFrame
        """
        logger.info("移除重複記錄...")
        initial_count = len(df)
        
        # 如果指定了 subset，確保這些欄位存在
        if subset:
            subset = [col for col in subset if col in df.columns]
            if not subset:
                logger.warning("指定的去重欄位都不存在，跳過去重")
                return df
        
        df = df.drop_duplicates(subset=subset, keep=keep).copy()
        
        removed = initial_count - len(df)
        if removed > 0:
            logger.info(f"移除 {removed} 筆重複記錄")
            self.cleaning_report['removed_rows'] += removed
        else:
            logger.info("沒有發現重複記錄")
        
        return df
    
    def standardize_dates(
        self, 
        df: pd.DataFrame,
        date_columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        統一日期時間格式
        
        Args:
            df: 輸入 DataFrame
            date_columns: 日期欄位列表，None 表示自動偵測
            
        Returns:
            標準化後的 DataFrame
        """
        logger.info("統一日期時間格式...")
        
        if date_columns is None:
            # 自動偵測可能的日期欄位
            date_columns = [
                'date', 'create_time', 'modify_time', 
                'created_at', 'updated_at', 'select_time'
            ]
        
        standardized_count = 0
        
        for column in date_columns:
            if column not in df.columns:
                continue
            
            try:
                # 如果已經是 datetime 類型，跳過
                if pd.api.types.is_datetime64_any_dtype(df[column]):
                    logger.debug(f"{column} 已經是 datetime 類型")
                    continue
                
                # 轉換為 datetime
                df[column] = pd.to_datetime(df[column], errors='coerce')
                standardized_count += 1
                
                # 檢查轉換失敗的數量
                null_count = df[column].isna().sum()
                if null_count > 0:
                    logger.warning(f"{column} 有 {null_count} 個值無法轉換為日期")
                    self.cleaning_report['issues'].append(
                        f"{column}: {null_count} 個值無法轉換為日期"
                    )
                else:
                    logger.info(f"成功標準化 {column} 欄位")
                    
            except Exception as e:
                logger.error(f"標準化 {column} 時發生錯誤: {e}")
                self.cleaning_report['issues'].append(f"{column}: 標準化失敗 - {e}")
        
        self.cleaning_report['standardized_fields'] += standardized_count
        logger.info(f"日期標準化完成，共處理 {standardized_count} 個欄位")
        
        return df
    
    def handle_outliers(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: str = 'iqr',
        threshold: float = 1.5
    ) -> pd.DataFrame:
        """
        處理異常值
        
        Args:
            df: 輸入 DataFrame
            columns: 要處理的數值欄位列表，None 表示所有數值欄位
            method: 處理方法 ('iqr', 'zscore', 'clip')
            threshold: 閾值（IQR 倍數或 Z-score 標準差倍數）
            
        Returns:
            處理後的 DataFrame
        """
        logger.info(f"處理異常值（方法: {method}）...")
        
        if columns is None:
            # 自動選擇數值欄位
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
            # 排除 ID 類欄位
            columns = [col for col in columns if 'id' not in col.lower()]
        
        outlier_count = 0
        
        for column in columns:
            if column not in df.columns:
                continue
            
            if not pd.api.types.is_numeric_dtype(df[column]):
                continue
            
            try:
                if method == 'iqr':
                    # 使用 IQR 方法
                    Q1 = df[column].quantile(0.25)
                    Q3 = df[column].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - threshold * IQR
                    upper_bound = Q3 + threshold * IQR
                    
                    outliers = ((df[column] < lower_bound) | (df[column] > upper_bound))
                    outlier_count_col = outliers.sum()
                    
                    if outlier_count_col > 0:
                        # 將異常值裁剪到邊界
                        df[column] = df[column].clip(lower=lower_bound, upper=upper_bound)
                        outlier_count += outlier_count_col
                        logger.info(f"{column}: 處理 {outlier_count_col} 個異常值")
                        
                elif method == 'zscore':
                    # 使用 Z-score 方法
                    mean = df[column].mean()
                    std = df[column].std()
                    z_scores = np.abs((df[column] - mean) / std)
                    
                    outliers = z_scores > threshold
                    outlier_count_col = outliers.sum()
                    
                    if outlier_count_col > 0:
                        # 將異常值替換為平均值
                        df.loc[outliers, column] = mean
                        outlier_count += outlier_count_col
                        logger.info(f"{column}: 處理 {outlier_count_col} 個異常值")
                        
            except Exception as e:
                logger.error(f"處理 {column} 異常值時發生錯誤: {e}")
        
        logger.info(f"異常值處理完成，共處理 {outlier_count} 個異常值")
        return df
    
    def clean_text_fields(
        self,
        df: pd.DataFrame,
        text_columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        清理文字欄位
        
        Args:
            df: 輸入 DataFrame
            text_columns: 文字欄位列表，None 表示自動偵測
            
        Returns:
            清理後的 DataFrame
        """
        logger.info("清理文字欄位...")
        
        if text_columns is None:
            # 自動選擇文字欄位
            text_columns = df.select_dtypes(include=['object']).columns.tolist()
        
        cleaned_count = 0
        
        for column in text_columns:
            if column not in df.columns:
                continue
            
            try:
                # 移除前後空白
                df[column] = df[column].astype(str).str.strip()
                
                # 將 'nan', 'None', 'null' 等字串轉為空字串
                df[column] = df[column].replace(['nan', 'None', 'null', 'NaN'], '')
                
                cleaned_count += 1
                logger.debug(f"清理文字欄位: {column}")
                
            except Exception as e:
                logger.error(f"清理 {column} 時發生錯誤: {e}")
        
        logger.info(f"文字欄位清理完成，共處理 {cleaned_count} 個欄位")
        return df
    
    def clean_all(
        self,
        df: pd.DataFrame,
        remove_invalid: bool = True,
        handle_missing: bool = True,
        remove_dups: bool = True,
        standardize_dates_flag: bool = True,
        handle_outliers_flag: bool = False,
        clean_text: bool = True
    ) -> pd.DataFrame:
        """
        執行所有清理步驟
        
        Args:
            df: 輸入 DataFrame
            remove_invalid: 是否移除無效訂單
            handle_missing: 是否處理缺失值
            remove_dups: 是否移除重複記錄
            standardize_dates_flag: 是否標準化日期
            handle_outliers_flag: 是否處理異常值
            clean_text: 是否清理文字欄位
            
        Returns:
            清理後的 DataFrame
        """
        logger.info("=" * 60)
        logger.info("開始完整資料清理流程")
        logger.info("=" * 60)
        
        initial_count = len(df)
        initial_columns = len(df.columns)
        
        # 重置清理報告
        self.cleaning_report = {
            'removed_rows': 0,
            'filled_values': 0,
            'standardized_fields': 0,
            'issues': []
        }
        
        # 執行清理步驟
        if remove_invalid:
            df = self.remove_invalid_orders(df)
        
        if handle_missing:
            df = self.handle_missing_values(df)
        
        if remove_dups:
            df = self.remove_duplicates(df, subset=['id'] if 'id' in df.columns else None)
        
        if standardize_dates_flag:
            df = self.standardize_dates(df)
        
        if handle_outliers_flag:
            df = self.handle_outliers(df)
        
        if clean_text:
            df = self.clean_text_fields(df)
        
        # 生成清理報告
        final_count = len(df)
        final_columns = len(df.columns)
        
        logger.info("=" * 60)
        logger.info("資料清理完成")
        logger.info(f"初始記錄數: {initial_count:,}")
        logger.info(f"最終記錄數: {final_count:,}")
        logger.info(f"移除記錄數: {self.cleaning_report['removed_rows']:,}")
        logger.info(f"填補缺失值: {self.cleaning_report['filled_values']:,}")
        logger.info(f"標準化欄位: {self.cleaning_report['standardized_fields']}")
        
        if self.cleaning_report['issues']:
            logger.warning(f"發現 {len(self.cleaning_report['issues'])} 個問題:")
            for issue in self.cleaning_report['issues'][:5]:  # 只顯示前 5 個
                logger.warning(f"  - {issue}")
        
        logger.info("=" * 60)
        
        return df
    
    def get_cleaning_report(self) -> Dict[str, Any]:
        """
        獲取清理報告
        
        Returns:
            清理報告字典
        """
        return self.cleaning_report.copy()


def main():
    """測試資料清理器"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from src.data_processing.data_loader import DataLoader
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("測試資料清理器")
    print("=" * 60)
    
    # 載入測試資料
    print("\n載入測試資料...")
    loader = DataLoader()
    df = loader.load_members(max_rows=1000)
    
    print(f"原始資料: {len(df)} 筆記錄")
    
    # 建立清理器
    cleaner = DataCleaner()
    
    # 執行清理
    print("\n執行資料清理...")
    cleaned_df = cleaner.clean_all(df)
    
    print(f"\n清理後資料: {len(cleaned_df)} 筆記錄")
    
    # 顯示清理報告
    report = cleaner.get_cleaning_report()
    print("\n清理報告:")
    print(f"  移除記錄: {report['removed_rows']}")
    print(f"  填補缺失值: {report['filled_values']}")
    print(f"  標準化欄位: {report['standardized_fields']}")
    
    print("\n" + "=" * 60)
    print("✓ 資料清理器測試完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
