"""
模型訓練主程式
整合資料處理、特徵工程和模型訓練流程
"""
import sys
from pathlib import Path
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_processing.data_loader import DataLoader
from src.data_processing.data_cleaner import DataCleaner
from src.data_processing.feature_engineer import FeatureEngineer
from src.data_processing.data_validator import DataValidator
from src.models.training_data_builder import TrainingDataBuilder
from src.models.ml_recommender import MLRecommender
from src.models.model_evaluator import ModelEvaluator
from src.models.data_models import ModelMetadata, ModelMetrics, ModelType
from src.config import settings

# 設置日誌
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOGS_DIR / 'training.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class TrainingPipeline:
    """訓練管線類別"""
    
    def __init__(
        self,
        model_type: str = 'lightgbm',
        model_version: str = None,
        max_rows: Optional[int] = None
    ):
        """
        初始化訓練管線
        
        Args:
            model_type: 模型類型
            model_version: 模型版本
            max_rows: 最大資料行數（用於測試）
        """
        self.model_type = model_type
        self.model_version = model_version or settings.MODEL_VERSION
        self.max_rows = max_rows
        
        # 建立模型目錄
        self.model_dir = settings.MODELS_DIR / self.model_version
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("=" * 80)
        logger.info("訓練管線初始化")
        logger.info("=" * 80)
        logger.info(f"模型類型: {model_type}")
        logger.info(f"模型版本: {self.model_version}")
        logger.info(f"模型目錄: {self.model_dir}")
        
    def load_data(self) -> Dict[str, Any]:
        """載入資料"""
        logger.info("\n" + "=" * 80)
        logger.info("步驟 1: 載入資料")
        logger.info("=" * 80)
        
        loader = DataLoader()
        
        # 載入並合併資料
        df = loader.merge_data(max_rows=self.max_rows)
        
        if df.empty:
            raise ValueError("資料載入失敗或為空")
        
        logger.info(f"✓ 資料載入完成: {len(df)} 筆記錄")
        
        return {'merged_data': df}
    
    def clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清理資料"""
        logger.info("\n" + "=" * 80)
        logger.info("步驟 2: 清理資料")
        logger.info("=" * 80)
        
        cleaner = DataCleaner()
        
        df = data['merged_data']
        cleaned_df = cleaner.clean_all(df)
        
        logger.info(f"✓ 資料清理完成: {len(cleaned_df)} 筆記錄")
        
        data['cleaned_data'] = cleaned_df
        data['cleaning_report'] = cleaner.get_cleaning_report()
        
        return data
    
    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證資料"""
        logger.info("\n" + "=" * 80)
        logger.info("步驟 3: 驗證資料")
        logger.info("=" * 80)
        
        validator = DataValidator()
        
        df = data['cleaned_data']
        passed, report = validator.validate_all(df)
        
        if not passed:
            logger.warning("資料驗證未完全通過，但繼續訓練")
        else:
            logger.info("✓ 資料驗證通過")
        
        data['validation_report'] = report
        
        return data
    
    def engineer_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """特徵工程"""
        logger.info("\n" + "=" * 80)
        logger.info("步驟 4: 特徵工程")
        logger.info("=" * 80)
        
        engineer = FeatureEngineer()
        
        df = data['cleaned_data']
        
        # 建立會員特徵
        member_features = engineer.create_feature_matrix(df)
        logger.info(f"✓ 會員特徵: {len(member_features)} 個會員, {len(member_features.columns)} 個特徵")
        
        # 建立產品特徵
        product_features = engineer.create_product_features(df)
        logger.info(f"✓ 產品特徵: {len(product_features)} 個產品, {len(product_features.columns)} 個特徵")
        
        data['member_features'] = member_features
        data['product_features'] = product_features
        
        return data
    
    def prepare_training_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """準備訓練資料"""
        logger.info("\n" + "=" * 80)
        logger.info("步驟 5: 準備訓練資料")
        logger.info("=" * 80)
        
        builder = TrainingDataBuilder()
        
        df = data['cleaned_data']
        data_dict = builder.prepare_training_data(df)
        
        # 統計資訊
        stats = builder.get_data_statistics(data_dict)
        logger.info("✓ 訓練資料準備完成")
        for name, stat in stats.items():
            if name != 'all':
                logger.info(f"  {name}: {stat['total_samples']} 樣本")
        
        data['train_data'] = data_dict['train']
        data['val_data'] = data_dict['validation']
        data['test_data'] = data_dict['test']
        data['data_statistics'] = stats
        
        return data
    
    def train_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """訓練模型"""
        logger.info("\n" + "=" * 80)
        logger.info("步驟 6: 訓練模型")
        logger.info("=" * 80)
        
        # 建立模型
        model = MLRecommender(model_type=self.model_type)
        
        # 訓練
        model.train(
            train_df=data['train_data'],
            val_df=data['val_data'],
            member_features_df=data['member_features'],
            product_features_df=data['product_features'],
            num_boost_round=100,
            early_stopping_rounds=10
        )
        
        logger.info("✓ 模型訓練完成")
        
        data['model'] = model
        
        return data
    
    def evaluate_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """評估模型"""
        logger.info("\n" + "=" * 80)
        logger.info("步驟 7: 評估模型")
        logger.info("=" * 80)
        
        evaluator = ModelEvaluator()
        
        # 在測試集上評估
        metrics = evaluator.evaluate_model(
            model=data['model'],
            test_df=data['test_data'],
            member_features_df=data['member_features'],
            product_features_df=data['product_features'],
            k=5
        )
        
        # 檢查是否達到要求
        if 'accuracy' in metrics and metrics['accuracy'] < 0.70:
            logger.warning(f"⚠ 模型準確率 {metrics['accuracy']:.2%} 低於 70%")
        else:
            logger.info("✓ 模型評估完成")
        
        data['metrics'] = metrics
        
        return data
    
    def save_model(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """儲存模型"""
        logger.info("\n" + "=" * 80)
        logger.info("步驟 8: 儲存模型")
        logger.info("=" * 80)
        
        # 儲存模型
        model_path = self.model_dir / 'model.pkl'
        data['model'].save(model_path)
        logger.info(f"✓ 模型已儲存: {model_path}")
        
        # 儲存特徵
        member_features_path = self.model_dir / 'member_features.parquet'
        data['member_features'].to_parquet(member_features_path)
        logger.info(f"✓ 會員特徵已儲存: {member_features_path}")
        
        product_features_path = self.model_dir / 'product_features.parquet'
        data['product_features'].to_parquet(product_features_path)
        logger.info(f"✓ 產品特徵已儲存: {product_features_path}")
        
        # 儲存元資料
        metadata = self.create_metadata(data)
        metadata_path = self.model_dir / 'metadata.json'
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"✓ 元資料已儲存: {metadata_path}")
        
        # 儲存指標
        metrics_path = self.model_dir / 'metrics.json'
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(data['metrics'], f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ 評估指標已儲存: {metrics_path}")
        
        return data
    
    def create_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """建立模型元資料"""
        stats = data['data_statistics']
        
        metadata = {
            'version': self.model_version,
            'model_type': self.model_type,
            'trained_at': datetime.now().isoformat(),
            'training_samples': stats['train']['total_samples'],
            'validation_samples': stats['validation']['total_samples'],
            'test_samples': stats['test']['total_samples'],
            'metrics': data['metrics'],
            'feature_names': data['model'].feature_names,
            'hyperparameters': data['model'].params,
            'config': {
                'random_seed': settings.RANDOM_SEED,
                'negative_sample_ratio': settings.NEGATIVE_SAMPLE_RATIO,
                'train_test_split': settings.TRAIN_TEST_SPLIT,
            }
        }
        
        return metadata
    
    def run(self) -> Dict[str, Any]:
        """執行完整訓練管線"""
        logger.info("\n" + "=" * 80)
        logger.info("開始訓練管線")
        logger.info("=" * 80)
        
        start_time = datetime.now()
        
        try:
            # 執行各步驟
            data = {}
            data = self.load_data()
            data = self.clean_data(data)
            data = self.validate_data(data)
            data = self.engineer_features(data)
            data = self.prepare_training_data(data)
            data = self.train_model(data)
            data = self.evaluate_model(data)
            data = self.save_model(data)
            
            # 計算訓練時間
            end_time = datetime.now()
            training_time = (end_time - start_time).total_seconds()
            
            logger.info("\n" + "=" * 80)
            logger.info("訓練管線完成")
            logger.info("=" * 80)
            logger.info(f"訓練時間: {training_time:.2f} 秒")
            logger.info(f"模型版本: {self.model_version}")
            logger.info(f"模型目錄: {self.model_dir}")
            logger.info("\n評估指標:")
            for metric_name, value in data['metrics'].items():
                logger.info(f"  {metric_name}: {value:.4f}")
            logger.info("=" * 80)
            
            return data
            
        except Exception as e:
            logger.error(f"訓練管線失敗: {e}")
            import traceback
            traceback.print_exc()
            raise


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='訓練推薦模型')
    parser.add_argument(
        '--model-type',
        type=str,
        default='lightgbm',
        choices=['lightgbm', 'xgboost'],
        help='模型類型'
    )
    parser.add_argument(
        '--model-version',
        type=str,
        default=None,
        help='模型版本'
    )
    parser.add_argument(
        '--max-rows',
        type=int,
        default=None,
        help='最大資料行數（用於測試）'
    )
    
    args = parser.parse_args()
    
    # 建立訓練管線
    pipeline = TrainingPipeline(
        model_type=args.model_type,
        model_version=args.model_version,
        max_rows=args.max_rows
    )
    
    # 執行訓練
    try:
        pipeline.run()
        return 0
    except Exception as e:
        logger.error(f"訓練失敗: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
