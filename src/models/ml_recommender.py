"""
機器學習推薦模型
使用 LightGBM 或 XGBoost 預測會員對產品的購買機率
"""
import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Optional, Any
import logging
import pickle
from pathlib import Path

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logging.warning("LightGBM 未安裝")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logging.warning("XGBoost 未安裝")

from sklearn.preprocessing import LabelEncoder
from src.config import settings

logger = logging.getLogger(__name__)


class MLRecommender:
    """機器學習推薦模型類別"""
    
    def __init__(
        self,
        model_type: str = 'lightgbm',
        params: Optional[Dict[str, Any]] = None,
        random_state: Optional[int] = None
    ):
        """
        初始化機器學習推薦模型
        
        Args:
            model_type: 模型類型 ('lightgbm' 或 'xgboost')
            params: 模型參數
            random_state: 隨機種子
        """
        self.model_type = model_type.lower()
        self.random_state = random_state or settings.RANDOM_SEED
        
        # 檢查庫是否可用
        if self.model_type == 'lightgbm' and not LIGHTGBM_AVAILABLE:
            raise ImportError("請安裝 LightGBM: pip install lightgbm")
        elif self.model_type == 'xgboost' and not XGBOOST_AVAILABLE:
            raise ImportError("請安裝 XGBoost: pip install xgboost")
        
        # 設置預設參數（優化後的超參數，需求 2.1-2.4）
        if params is None:
            if self.model_type == 'lightgbm':
                params = {
                    'objective': 'binary',
                    'metric': 'auc',
                    'boosting_type': 'gbdt',
                    'num_leaves': 75,  # 需求 2.1: 調整為 50-100 範圍內
                    'learning_rate': 0.03,  # 需求 2.2: 調整為 0.01-0.05 範圍內
                    'max_depth': 8,  # 需求 2.3: 調整為 6-10 範圍內
                    'feature_fraction': 0.9,
                    'bagging_fraction': 0.8,
                    'bagging_freq': 5,
                    'min_child_samples': 20,
                    'reg_alpha': 0.1,
                    'reg_lambda': 0.1,
                    'verbose': -1,
                    'random_state': self.random_state
                }
            else:  # xgboost
                params = {
                    'objective': 'binary:logistic',
                    'eval_metric': 'auc',
                    'max_depth': 8,  # 需求 2.3: 調整為 6-10 範圍內
                    'learning_rate': 0.03,  # 需求 2.2: 調整為 0.01-0.05 範圍內
                    'subsample': 0.8,
                    'colsample_bytree': 0.9,
                    'min_child_weight': 3,
                    'reg_alpha': 0.1,
                    'reg_lambda': 0.1,
                    'random_state': self.random_state
                }
        
        self.params = params
        self.model = None
        self.is_trained = False
        self.feature_names = []
        self.feature_importance = {}
        self.label_encoders = {}
        
        logger.info(f"機器學習推薦模型初始化 ({self.model_type.upper()})")
        logger.info(f"  參數: {params}")
    
    def prepare_features(
        self,
        df: pd.DataFrame,
        member_features_df: Optional[pd.DataFrame] = None,
        product_features_df: Optional[pd.DataFrame] = None,
        member_col: str = 'member_id',
        product_col: str = 'stock_id'
    ) -> pd.DataFrame:
        """
        準備特徵
        
        Args:
            df: 基礎 DataFrame（包含 member_id, product_id, label）
            member_features_df: 會員特徵 DataFrame
            product_features_df: 產品特徵 DataFrame
            member_col: 會員 ID 欄位
            product_col: 產品 ID 欄位
            
        Returns:
            包含所有特徵的 DataFrame
        """
        logger.info("準備特徵...")
        
        result_df = df.copy()
        
        # 合併會員特徵
        if member_features_df is not None:
            logger.info(f"  合併會員特徵: {len(member_features_df.columns)} 個欄位")
            result_df = pd.merge(
                result_df,
                member_features_df,
                on=member_col,
                how='left'
            )
        
        # 合併產品特徵
        if product_features_df is not None:
            logger.info(f"  合併產品特徵: {len(product_features_df.columns)} 個欄位")
            result_df = pd.merge(
                result_df,
                product_features_df,
                on=product_col,
                how='left'
            )
        
        logger.info(f"特徵準備完成: {len(result_df.columns)} 個欄位")
        
        return result_df
    
    def encode_categorical_features(
        self,
        df: pd.DataFrame,
        categorical_columns: Optional[List[str]] = None,
        fit: bool = True
    ) -> pd.DataFrame:
        """
        編碼類別特徵
        
        Args:
            df: 輸入 DataFrame
            categorical_columns: 類別欄位列表
            fit: 是否擬合編碼器（訓練時為 True，預測時為 False）
            
        Returns:
            編碼後的 DataFrame
        """
        df = df.copy()
        
        if categorical_columns is None:
            # 自動偵測類別欄位
            categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
            # 排除 ID 欄位
            categorical_columns = [col for col in categorical_columns 
                                  if col not in ['member_id', 'stock_id', 'label']]
        
        if not categorical_columns:
            return df
        
        logger.info(f"編碼類別特徵: {categorical_columns}")
        
        for col in categorical_columns:
            if col not in df.columns:
                continue
            
            if fit:
                # 訓練時：建立並擬合編碼器
                le = LabelEncoder()
                df[col] = df[col].fillna('missing')
                df[col] = le.fit_transform(df[col].astype(str))
                self.label_encoders[col] = le
            else:
                # 預測時：使用已有的編碼器
                if col in self.label_encoders:
                    le = self.label_encoders[col]
                    df[col] = df[col].fillna('missing')
                    # 處理未見過的類別
                    df[col] = df[col].apply(
                        lambda x: le.transform([str(x)])[0] 
                        if str(x) in le.classes_ else -1
                    )
        
        return df
    
    def select_features(
        self,
        df: pd.DataFrame,
        exclude_columns: Optional[List[str]] = None
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        選擇特徵
        
        Args:
            df: 輸入 DataFrame
            exclude_columns: 要排除的欄位
            
        Returns:
            (特徵 DataFrame, 特徵名稱列表)
        """
        if exclude_columns is None:
            exclude_columns = ['member_id', 'stock_id', 'label', 'member_code', 
                             'stock_description', 'member_name', 'phone']
        
        # 選擇數值特徵
        feature_columns = [col for col in df.columns 
                          if col not in exclude_columns]
        
        # 只保留數值欄位
        numeric_columns = df[feature_columns].select_dtypes(
            include=[np.number]
        ).columns.tolist()
        
        X = df[numeric_columns].copy()
        
        # 填補缺失值
        X = X.fillna(0)
        
        logger.info(f"選擇特徵: {len(numeric_columns)} 個")
        
        return X, numeric_columns
    
    def train(
        self,
        train_df: pd.DataFrame,
        val_df: Optional[pd.DataFrame] = None,
        member_features_df: Optional[pd.DataFrame] = None,
        product_features_df: Optional[pd.DataFrame] = None,
        num_boost_round: int = 100,
        early_stopping_rounds: int = 20  # 需求 2.4: 設置 patience 為 20 輪
    ):
        """
        訓練模型（使用優化後的超參數）
        
        Args:
            train_df: 訓練資料
            val_df: 驗證資料
            member_features_df: 會員特徵
            product_features_df: 產品特徵
            num_boost_round: 訓練輪數
            early_stopping_rounds: 早停輪數（需求 2.4: patience=20）
        """
        logger.info("=" * 60)
        logger.info("開始訓練機器學習推薦模型")
        logger.info("=" * 60)
        logger.info(f"超參數配置:")
        for key, value in self.params.items():
            logger.info(f"  {key}: {value}")
        
        # 準備特徵
        train_full = self.prepare_features(
            train_df, member_features_df, product_features_df
        )
        
        # 編碼類別特徵
        train_full = self.encode_categorical_features(train_full, fit=True)
        
        # 選擇特徵
        X_train, self.feature_names = self.select_features(train_full)
        y_train = train_full['label']
        
        logger.info(f"訓練集: {len(X_train)} 樣本, {len(self.feature_names)} 特徵")
        
        # 準備驗證集
        eval_set = None
        if val_df is not None:
            val_full = self.prepare_features(
                val_df, member_features_df, product_features_df
            )
            val_full = self.encode_categorical_features(val_full, fit=False)
            X_val, _ = self.select_features(val_full)
            y_val = val_full['label']
            eval_set = [(X_val, y_val)]
            logger.info(f"驗證集: {len(X_val)} 樣本")
            logger.info(f"早停機制: 啟用 (patience={early_stopping_rounds})")  # 需求 2.4
        
        # 訓練模型
        logger.info("訓練中...")
        
        if self.model_type == 'lightgbm':
            train_data = lgb.Dataset(X_train, label=y_train)
            valid_data = lgb.Dataset(X_val, label=y_val) if eval_set else None
            
            # 需求 2.4: 添加 early_stopping 機制
            callbacks = [lgb.log_evaluation(10)]
            if valid_data:
                callbacks.append(lgb.early_stopping(early_stopping_rounds))
            
            self.model = lgb.train(
                self.params,
                train_data,
                num_boost_round=num_boost_round,
                valid_sets=[valid_data] if valid_data else None,
                callbacks=callbacks
            )
            
            # 獲取特徵重要性
            importance = self.model.feature_importance(importance_type='gain')
            self.feature_importance = dict(zip(self.feature_names, importance))
            
        else:  # xgboost
            dtrain = xgb.DMatrix(X_train, label=y_train)
            dval = xgb.DMatrix(X_val, label=y_val) if eval_set else None
            
            evals = [(dval, 'validation')] if dval else []
            
            # 需求 2.4: 添加 early_stopping 機制
            self.model = xgb.train(
                self.params,
                dtrain,
                num_boost_round=num_boost_round,
                evals=evals,
                early_stopping_rounds=early_stopping_rounds if dval else None,
                verbose_eval=10
            )
            
            # 獲取特徵重要性
            importance = self.model.get_score(importance_type='gain')
            self.feature_importance = importance
        
        self.is_trained = True
        
        # 顯示 Top 10 重要特徵
        logger.info("\nTop 10 重要特徵:")
        sorted_features = sorted(
            self.feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        for feat, imp in sorted_features:
            logger.info(f"  {feat}: {imp:.2f}")
        
        logger.info("=" * 60)
        logger.info("模型訓練完成")
        logger.info(f"✓ 超參數已優化:")
        logger.info(f"  - num_leaves: {self.params.get('num_leaves', 'N/A')} (需求 2.1: 50-100)")
        logger.info(f"  - learning_rate: {self.params.get('learning_rate', 'N/A')} (需求 2.2: 0.01-0.05)")
        logger.info(f"  - max_depth: {self.params.get('max_depth', 'N/A')} (需求 2.3: 6-10)")
        logger.info(f"  - early_stopping: {early_stopping_rounds} rounds (需求 2.4)")
        logger.info("=" * 60)
    
    def predict_proba(
        self,
        df: pd.DataFrame,
        member_features_df: Optional[pd.DataFrame] = None,
        product_features_df: Optional[pd.DataFrame] = None
    ) -> np.ndarray:
        """
        預測購買機率
        
        Args:
            df: 輸入 DataFrame
            member_features_df: 會員特徵
            product_features_df: 產品特徵
            
        Returns:
            預測機率陣列
        """
        if not self.is_trained:
            raise ValueError("模型尚未訓練")
        
        # 準備特徵
        test_full = self.prepare_features(
            df, member_features_df, product_features_df
        )
        
        # 編碼類別特徵
        test_full = self.encode_categorical_features(test_full, fit=False)
        
        # 選擇特徵
        X_test, _ = self.select_features(test_full)
        
        # 預測
        if self.model_type == 'lightgbm':
            predictions = self.model.predict(X_test)
        else:  # xgboost
            dtest = xgb.DMatrix(X_test)
            predictions = self.model.predict(dtest)
        
        return predictions
    
    def recommend(
        self,
        member_id: str,
        product_ids: List[str],
        member_features_df: Optional[pd.DataFrame] = None,
        product_features_df: Optional[pd.DataFrame] = None,
        n: int = 5
    ) -> List[Tuple[str, float]]:
        """
        為會員推薦產品
        
        Args:
            member_id: 會員 ID
            product_ids: 候選產品 ID 列表
            member_features_df: 會員特徵
            product_features_df: 產品特徵
            n: 推薦數量
            
        Returns:
            [(產品ID, 預測分數), ...]
        """
        # 建立候選 DataFrame
        candidates_df = pd.DataFrame({
            'member_id': [member_id] * len(product_ids),
            'stock_id': product_ids,
            'label': [0] * len(product_ids)  # 佔位符
        })
        
        # 預測
        predictions = self.predict_proba(
            candidates_df,
            member_features_df,
            product_features_df
        )
        
        # 組合結果
        results = list(zip(product_ids, predictions))
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:n]
    
    def save(self, file_path: Path):
        """儲存模型"""
        logger.info(f"儲存模型到 {file_path}")
        
        model_data = {
            'model': self.model,
            'model_type': self.model_type,
            'params': self.params,
            'is_trained': self.is_trained,
            'feature_names': self.feature_names,
            'feature_importance': self.feature_importance,
            'label_encoders': self.label_encoders,
        }
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info("模型儲存完成")
    
    @classmethod
    def load(cls, file_path: Path) -> 'MLRecommender':
        """載入模型"""
        logger.info(f"載入模型從 {file_path}")
        
        with open(file_path, 'rb') as f:
            model_data = pickle.load(f)
        
        instance = cls(
            model_type=model_data['model_type'],
            params=model_data['params']
        )
        
        instance.model = model_data['model']
        instance.is_trained = model_data['is_trained']
        instance.feature_names = model_data['feature_names']
        instance.feature_importance = model_data['feature_importance']
        instance.label_encoders = model_data['label_encoders']
        
        logger.info("模型載入完成")
        
        return instance


def main():
    """測試機器學習推薦模型"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from src.data_processing.data_loader import DataLoader
    from src.data_processing.data_cleaner import DataCleaner
    from src.data_processing.feature_engineer import FeatureEngineer
    from src.models.training_data_builder import TrainingDataBuilder
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("測試機器學習推薦模型")
    print("=" * 60)
    
    if not LIGHTGBM_AVAILABLE and not XGBOOST_AVAILABLE:
        print("\n✗ LightGBM 和 XGBoost 都未安裝")
        print("請執行: pip install lightgbm 或 pip install xgboost")
        return
    
    # 載入資料
    print("\n載入資料...")
    loader = DataLoader()
    df = loader.merge_data(max_rows=1000)
    
    if df.empty:
        print("✗ 資料載入失敗")
        return
    
    # 清理資料
    print("\n清理資料...")
    cleaner = DataCleaner()
    df = cleaner.clean_all(df)
    
    # 特徵工程
    print("\n特徵工程...")
    engineer = FeatureEngineer()
    member_features = engineer.create_feature_matrix(df)
    product_features = engineer.create_product_features(df)
    
    # 準備訓練資料
    print("\n準備訓練資料...")
    builder = TrainingDataBuilder()
    data_dict = builder.prepare_training_data(df)
    
    # 建立模型
    print("\n建立模型...")
    model_type = 'lightgbm' if LIGHTGBM_AVAILABLE else 'xgboost'
    ml_model = MLRecommender(model_type=model_type)
    
    # 訓練模型
    print("\n訓練模型...")
    ml_model.train(
        train_df=data_dict['train'],
        val_df=data_dict['validation'],
        member_features_df=member_features,
        product_features_df=product_features,
        num_boost_round=50
    )
    
    print("\n" + "=" * 60)
    print("✓ 機器學習推薦模型測試完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
