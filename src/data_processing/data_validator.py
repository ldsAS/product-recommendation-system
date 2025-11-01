"""
資料驗證器
驗證資料完整性、一致性和品質
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DataValidator:
    """資料驗證器類別"""
    
    def __init__(self):
        """初始化資料驗證器"""
        logger.info("資料驗證器初始化")
        self.validation_report = {
            'passed': [],
            'warnings': [],
            'errors': [],
            'statistics': {}
        }
    
    def validate_completeness(
        self,
        df: pd.DataFrame,
        required_columns: Optional[List[str]] = None
    ) -> bool:
        """
        驗證資料完整性
        
        Args:
            df: 輸入 DataFrame
            required_columns: 必要欄位列表
            
        Returns:
            是否通過驗證
        """
        logger.info("驗證資料完整性...")
        passed = True
        
        # 檢查 DataFrame 是否為空
        if df.empty:
            self.validation_report['errors'].append("DataFrame 為空")
            logger.error("DataFrame 為空")
            return False
        
        self.validation_report['passed'].append(f"DataFrame 包含 {len(df)} 筆記錄")
        
        # 檢查必要欄位
        if required_columns:
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.validation_report['errors'].append(
                    f"缺少必要欄位: {missing_columns}"
                )
                logger.error(f"缺少必要欄位: {missing_columns}")
                passed = False
            else:
                self.validation_report['passed'].append("所有必要欄位都存在")
        
        # 檢查缺失值比例
        missing_stats = {}
        for column in df.columns:
            missing_count = df[column].isna().sum()
            missing_pct = (missing_count / len(df)) * 100
            
            if missing_pct > 0:
                missing_stats[column] = {
                    'count': int(missing_count),
                    'percentage': float(missing_pct)
                }
                
                if missing_pct > 50:
                    self.validation_report['warnings'].append(
                        f"{column} 有 {missing_pct:.1f}% 的缺失值"
                    )
                    logger.warning(f"{column} 有 {missing_pct:.1f}% 的缺失值")
        
        self.validation_report['statistics']['missing_values'] = missing_stats
        
        logger.info(f"完整性驗證{'通過' if passed else '失敗'}")
        return passed
    
    def validate_consistency(self, df: pd.DataFrame) -> bool:
        """
        驗證資料一致性
        
        Args:
            df: 輸入 DataFrame
            
        Returns:
            是否通過驗證
        """
        logger.info("驗證資料一致性...")
        passed = True
        
        # 檢查重複的 ID
        if 'id' in df.columns:
            duplicate_ids = df['id'].duplicated().sum()
            if duplicate_ids > 0:
                self.validation_report['warnings'].append(
                    f"發現 {duplicate_ids} 個重複的 ID"
                )
                logger.warning(f"發現 {duplicate_ids} 個重複的 ID")
            else:
                self.validation_report['passed'].append("沒有重複的 ID")
        
        # 檢查日期一致性
        date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        for col in date_columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                # 檢查未來日期
                future_dates = df[col] > datetime.now()
                if future_dates.any():
                    future_count = future_dates.sum()
                    self.validation_report['warnings'].append(
                        f"{col} 有 {future_count} 個未來日期"
                    )
                    logger.warning(f"{col} 有 {future_count} 個未來日期")
        
        # 檢查數值範圍
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if col in ['total', 'actualTotal', 'price', 'quantity', 'total_consumption']:
                # 檢查負值
                negative_count = (df[col] < 0).sum()
                if negative_count > 0:
                    self.validation_report['warnings'].append(
                        f"{col} 有 {negative_count} 個負值"
                    )
                    logger.warning(f"{col} 有 {negative_count} 個負值")
        
        logger.info(f"一致性驗證{'通過' if passed else '失敗'}")
        return passed
    
    def validate_data_quality(self, df: pd.DataFrame) -> bool:
        """
        驗證資料品質
        
        Args:
            df: 輸入 DataFrame
            
        Returns:
            是否通過驗證
        """
        logger.info("驗證資料品質...")
        passed = True
        
        # 計算資料品質指標
        quality_metrics = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'duplicate_rows': df.duplicated().sum(),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
        }
        
        # 檢查重複行
        if quality_metrics['duplicate_rows'] > 0:
            dup_pct = (quality_metrics['duplicate_rows'] / len(df)) * 100
            self.validation_report['warnings'].append(
                f"發現 {quality_metrics['duplicate_rows']} 筆重複記錄 ({dup_pct:.1f}%)"
            )
            logger.warning(f"發現 {quality_metrics['duplicate_rows']} 筆重複記錄")
        else:
            self.validation_report['passed'].append("沒有重複記錄")
        
        # 檢查資料型態
        dtype_issues = []
        for col in df.columns:
            if df[col].dtype == 'object':
                # 檢查是否應該是數值型態
                if col in ['total', 'price', 'quantity', 'actualTotal']:
                    try:
                        pd.to_numeric(df[col], errors='raise')
                    except:
                        dtype_issues.append(col)
        
        if dtype_issues:
            self.validation_report['warnings'].append(
                f"以下欄位可能有型態問題: {dtype_issues}"
            )
            logger.warning(f"欄位型態問題: {dtype_issues}")
        
        self.validation_report['statistics']['quality_metrics'] = quality_metrics
        
        logger.info(f"品質驗證{'通過' if passed else '失敗'}")
        return passed
    
    def validate_feature_distribution(
        self,
        df: pd.DataFrame,
        numeric_columns: Optional[List[str]] = None
    ) -> bool:
        """
        驗證特徵分布
        
        Args:
            df: 輸入 DataFrame
            numeric_columns: 要檢查的數值欄位
            
        Returns:
            是否通過驗證
        """
        logger.info("驗證特徵分布...")
        passed = True
        
        if numeric_columns is None:
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        distribution_stats = {}
        
        for col in numeric_columns:
            if col not in df.columns:
                continue
            
            stats = {
                'mean': float(df[col].mean()),
                'std': float(df[col].std()),
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'median': float(df[col].median()),
                'q25': float(df[col].quantile(0.25)),
                'q75': float(df[col].quantile(0.75)),
            }
            
            # 檢查是否有異常分布
            if stats['std'] == 0:
                self.validation_report['warnings'].append(
                    f"{col} 的標準差為 0（所有值相同）"
                )
                logger.warning(f"{col} 的標準差為 0")
            
            # 檢查極端值
            iqr = stats['q75'] - stats['q25']
            if iqr > 0:
                lower_bound = stats['q25'] - 3 * iqr
                upper_bound = stats['q75'] + 3 * iqr
                outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
                
                if outliers > 0:
                    outlier_pct = (outliers / len(df)) * 100
                    if outlier_pct > 5:
                        self.validation_report['warnings'].append(
                            f"{col} 有 {outliers} 個極端值 ({outlier_pct:.1f}%)"
                        )
                        logger.warning(f"{col} 有 {outliers} 個極端值")
            
            distribution_stats[col] = stats
        
        self.validation_report['statistics']['distribution'] = distribution_stats
        
        logger.info(f"分布驗證{'通過' if passed else '失敗'}")
        return passed
    
    def validate_relationships(self, df: pd.DataFrame) -> bool:
        """
        驗證資料關聯性
        
        Args:
            df: 輸入 DataFrame
            
        Returns:
            是否通過驗證
        """
        logger.info("驗證資料關聯性...")
        passed = True
        
        # 檢查會員-訂單關聯
        if 'member_id' in df.columns and 'sales_id' in df.columns:
            # 檢查孤立的訂單（沒有對應會員）
            orphan_orders = df['member_id'].isna().sum()
            if orphan_orders > 0:
                self.validation_report['warnings'].append(
                    f"發現 {orphan_orders} 筆沒有對應會員的訂單"
                )
                logger.warning(f"發現 {orphan_orders} 筆孤立訂單")
        
        # 檢查訂單-產品關聯
        if 'sales_id' in df.columns and 'stock_id' in df.columns:
            # 檢查沒有產品的訂單
            no_product_orders = df['stock_id'].isna().sum()
            if no_product_orders > 0:
                self.validation_report['warnings'].append(
                    f"發現 {no_product_orders} 筆沒有產品的訂單"
                )
                logger.warning(f"發現 {no_product_orders} 筆沒有產品的訂單")
        
        logger.info(f"關聯性驗證{'通過' if passed else '失敗'}")
        return passed
    
    def validate_all(
        self,
        df: pd.DataFrame,
        required_columns: Optional[List[str]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        執行所有驗證
        
        Args:
            df: 輸入 DataFrame
            required_columns: 必要欄位列表
            
        Returns:
            (是否通過, 驗證報告)
        """
        logger.info("=" * 60)
        logger.info("開始完整資料驗證")
        logger.info("=" * 60)
        
        # 重置驗證報告
        self.validation_report = {
            'passed': [],
            'warnings': [],
            'errors': [],
            'statistics': {}
        }
        
        # 執行各項驗證
        completeness_passed = self.validate_completeness(df, required_columns)
        consistency_passed = self.validate_consistency(df)
        quality_passed = self.validate_data_quality(df)
        distribution_passed = self.validate_feature_distribution(df)
        relationship_passed = self.validate_relationships(df)
        
        # 判斷整體是否通過
        all_passed = (
            completeness_passed and
            consistency_passed and
            quality_passed and
            distribution_passed and
            relationship_passed
        )
        
        # 生成報告摘要
        self.validation_report['summary'] = {
            'total_checks': 5,
            'passed_checks': sum([
                completeness_passed,
                consistency_passed,
                quality_passed,
                distribution_passed,
                relationship_passed
            ]),
            'total_passed': len(self.validation_report['passed']),
            'total_warnings': len(self.validation_report['warnings']),
            'total_errors': len(self.validation_report['errors']),
            'overall_status': 'PASSED' if all_passed else 'FAILED'
        }
        
        # 輸出報告
        logger.info("=" * 60)
        logger.info("驗證報告")
        logger.info("=" * 60)
        logger.info(f"通過項目: {self.validation_report['summary']['total_passed']}")
        logger.info(f"警告: {self.validation_report['summary']['total_warnings']}")
        logger.info(f"錯誤: {self.validation_report['summary']['total_errors']}")
        logger.info(f"整體狀態: {self.validation_report['summary']['overall_status']}")
        
        if self.validation_report['errors']:
            logger.error("錯誤列表:")
            for error in self.validation_report['errors']:
                logger.error(f"  - {error}")
        
        if self.validation_report['warnings']:
            logger.warning("警告列表:")
            for warning in self.validation_report['warnings'][:5]:  # 只顯示前 5 個
                logger.warning(f"  - {warning}")
        
        logger.info("=" * 60)
        
        return all_passed, self.validation_report
    
    def generate_quality_report(self, df: pd.DataFrame) -> str:
        """
        生成資料品質報告
        
        Args:
            df: 輸入 DataFrame
            
        Returns:
            報告文字
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("資料品質報告")
        report_lines.append("=" * 60)
        
        # 基本統計
        report_lines.append(f"\n基本統計:")
        report_lines.append(f"  總記錄數: {len(df):,}")
        report_lines.append(f"  總欄位數: {len(df.columns)}")
        report_lines.append(f"  記憶體使用: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        
        # 缺失值統計
        missing_counts = df.isnull().sum()
        if missing_counts.sum() > 0:
            report_lines.append(f"\n缺失值統計:")
            for col, count in missing_counts[missing_counts > 0].items():
                pct = (count / len(df)) * 100
                report_lines.append(f"  {col}: {count} ({pct:.1f}%)")
        
        # 重複記錄
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            report_lines.append(f"\n重複記錄: {dup_count}")
        
        # 數值欄位統計
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            report_lines.append(f"\n數值欄位統計:")
            for col in numeric_cols[:5]:  # 只顯示前 5 個
                report_lines.append(f"  {col}:")
                report_lines.append(f"    平均: {df[col].mean():.2f}")
                report_lines.append(f"    標準差: {df[col].std():.2f}")
                report_lines.append(f"    範圍: [{df[col].min():.2f}, {df[col].max():.2f}]")
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def get_validation_report(self) -> Dict[str, Any]:
        """
        獲取驗證報告
        
        Returns:
            驗證報告字典
        """
        return self.validation_report.copy()


def main():
    """測試資料驗證器"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from src.data_processing.data_loader import DataLoader
    from src.data_processing.data_cleaner import DataCleaner
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("測試資料驗證器")
    print("=" * 60)
    
    # 載入資料
    print("\n載入資料...")
    loader = DataLoader()
    df = loader.merge_data(max_rows=500)
    
    if df.empty:
        print("✗ 資料載入失敗")
        return
    
    # 清理資料
    print("\n清理資料...")
    cleaner = DataCleaner()
    df = cleaner.clean_all(df)
    
    # 建立驗證器
    print("\n執行資料驗證...")
    validator = DataValidator()
    
    # 執行驗證
    passed, report = validator.validate_all(df)
    
    # 顯示結果
    print(f"\n驗證結果: {'✓ 通過' if passed else '✗ 失敗'}")
    print(f"通過項目: {report['summary']['total_passed']}")
    print(f"警告: {report['summary']['total_warnings']}")
    print(f"錯誤: {report['summary']['total_errors']}")
    
    # 生成品質報告
    print("\n" + validator.generate_quality_report(df))
    
    print("\n" + "=" * 60)
    print("✓ 資料驗證器測試完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
