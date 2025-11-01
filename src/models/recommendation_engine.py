"""
推薦引擎核心
接收會員資訊，返回 Top 5 產品推薦
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging
import json
import time

from src.models.ml_recommender import MLRecommender
from src.models.explanation_generator import ExplanationGenerator
from src.models.data_models import (
    MemberInfo, Recommendation, RecommendationSource
)
from src.config import settings

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """推薦引擎類別"""
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        初始化推薦引擎
        
        Args:
            model_path: 模型目錄路徑，None 表示使用當前版本
        """
        if model_path is None:
            model_path = settings.MODELS_DIR / settings.MODEL_VERSION
        
        self.model_path = Path(model_path)
        
        logger.info("推薦引擎初始化...")
        logger.info(f"  模型路徑: {self.model_path}")
        
        # 載入模型和特徵
        self.model = None
        self.member_features = None
        self.product_features = None
        self.metadata = None
        self.explanation_generator = None
        
        self._load_model()
        self._load_features()
        self._load_metadata()
        self._initialize_explanation_generator()
        
        logger.info("✓ 推薦引擎初始化完成")
    
    def _load_model(self):
        """載入模型"""
        model_file = self.model_path / 'model.pkl'
        
        if not model_file.exists():
            raise FileNotFoundError(f"模型檔案不存在: {model_file}")
        
        logger.info("載入模型...")
        self.model = MLRecommender.load(model_file)
        logger.info("✓ 模型載入完成")
    
    def _load_features(self):
        """載入特徵"""
        member_features_file = self.model_path / 'member_features.parquet'
        product_features_file = self.model_path / 'product_features.parquet'
        
        if member_features_file.exists():
            logger.info("載入會員特徵...")
            self.member_features = pd.read_parquet(member_features_file)
            logger.info(f"✓ 會員特徵載入完成: {len(self.member_features)} 個會員")
        else:
            logger.warning("會員特徵檔案不存在")
        
        if product_features_file.exists():
            logger.info("載入產品特徵...")
            self.product_features = pd.read_parquet(product_features_file)
            logger.info(f"✓ 產品特徵載入完成: {len(self.product_features)} 個產品")
        else:
            logger.warning("產品特徵檔案不存在")
    
    def _load_metadata(self):
        """載入元資料"""
        metadata_file = self.model_path / 'metadata.json'
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            logger.info("✓ 元資料載入完成")
        else:
            logger.warning("元資料檔案不存在")
    
    def _initialize_explanation_generator(self):
        """初始化推薦理由生成器"""
        logger.info("初始化推薦理由生成器...")
        self.explanation_generator = ExplanationGenerator(
            product_features=self.product_features,
            member_features=self.member_features
        )
        logger.info("✓ 推薦理由生成器初始化完成")
    
    def extract_features(self, member_info: MemberInfo) -> Dict[str, Any]:
        """
        從會員資訊提取特徵
        
        Args:
            member_info: 會員資訊
            
        Returns:
            特徵字典
        """
        # 如果會員已存在於特徵庫中，直接使用
        if self.member_features is not None:
            existing = self.member_features[
                self.member_features['member_code'] == member_info.member_code
            ]
            
            if not existing.empty:
                return existing.iloc[0].to_dict()
        
        # 否則，從輸入資訊構建基本特徵
        features = {
            'member_code': member_info.member_code,
            'total_consumption': member_info.total_consumption,
            'accumulated_bonus': member_info.accumulated_bonus,
            # 其他特徵使用預設值
            'recency': 30,  # 預設值
            'frequency': 1,
            'monetary': member_info.total_consumption,
            'product_diversity': len(member_info.recent_purchases),
            'avg_items_per_order': 1.0,
            'days_since_last_purchase': 30,
        }
        
        return features
    
    def get_candidate_products(
        self,
        member_info: MemberInfo,
        exclude_purchased: bool = True,
        max_candidates: int = 100
    ) -> List[str]:
        """
        獲取候選產品列表
        
        Args:
            member_info: 會員資訊
            exclude_purchased: 是否排除已購買產品
            max_candidates: 最大候選數量
            
        Returns:
            產品 ID 列表
        """
        if self.product_features is None:
            logger.warning("產品特徵未載入，無法獲取候選產品")
            return []
        
        # 獲取所有產品
        all_products = self.product_features['stock_id'].tolist()
        
        # 排除已購買產品
        if exclude_purchased and member_info.recent_purchases:
            all_products = [
                p for p in all_products 
                if p not in member_info.recent_purchases
            ]
        
        # 限制候選數量（選擇熱門產品）
        if len(all_products) > max_candidates:
            # 按熱門度排序
            if 'popularity_score' in self.product_features.columns:
                top_products = self.product_features.nlargest(
                    max_candidates, 'popularity_score'
                )
                all_products = top_products['stock_id'].tolist()
            else:
                all_products = all_products[:max_candidates]
        
        return all_products
    
    def recommend(
        self,
        member_info: MemberInfo,
        n: Optional[int] = None
    ) -> List[Recommendation]:
        """
        為會員生成推薦
        
        Args:
            member_info: 會員資訊
            n: 推薦數量
            
        Returns:
            推薦列表
        """
        start_time = time.time()
        
        n = n or settings.TOP_K_RECOMMENDATIONS
        
        logger.info(f"為會員 {member_info.member_code} 生成推薦...")
        
        try:
            # 1. 提取會員特徵
            member_features_dict = self.extract_features(member_info)
            
            # 2. 獲取候選產品
            candidate_products = self.get_candidate_products(member_info)
            
            if not candidate_products:
                logger.warning("沒有候選產品")
                return []
            
            logger.info(f"  候選產品數: {len(candidate_products)}")
            
            # 3. 使用模型預測
            recommendations = self.model.recommend(
                member_id=member_info.member_code,
                product_ids=candidate_products,
                member_features_df=self.member_features,
                product_features_df=self.product_features,
                n=n
            )
            
            # 4. 轉換為 Recommendation 物件
            result = []
            for rank, (product_id, score) in enumerate(recommendations, 1):
                # 獲取產品名稱
                product_name = self._get_product_name(product_id)
                
                # 轉換分數為 0-100
                confidence_score = min(100, max(0, score * 100))
                
                # 使用推薦理由生成器生成理由
                explanation = self.explanation_generator.generate_explanation(
                    member_info=member_info,
                    product_id=product_id,
                    confidence_score=confidence_score,
                    source=RecommendationSource.ML_MODEL
                )
                
                rec = Recommendation(
                    product_id=product_id,
                    product_name=product_name,
                    confidence_score=confidence_score,
                    explanation=explanation,
                    rank=rank,
                    source=RecommendationSource.ML_MODEL,
                    raw_score=score
                )
                
                result.append(rec)
            
            # 計算回應時間
            response_time = (time.time() - start_time) * 1000  # 毫秒
            
            logger.info(f"✓ 推薦生成完成: {len(result)} 個推薦")
            logger.info(f"  回應時間: {response_time:.2f} ms")
            
            # 檢查回應時間
            if response_time > settings.MAX_RESPONSE_TIME_SECONDS * 1000:
                logger.warning(
                    f"回應時間 {response_time:.2f} ms 超過目標 "
                    f"{settings.MAX_RESPONSE_TIME_SECONDS * 1000} ms"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"推薦生成失敗: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_product_name(self, product_id: str) -> str:
        """獲取產品名稱"""
        if self.product_features is None:
            return product_id
        
        product = self.product_features[
            self.product_features['stock_id'] == product_id
        ]
        
        if not product.empty and 'stock_description' in product.columns:
            return product.iloc[0]['stock_description']
        
        return product_id
    
    def _generate_simple_explanation(
        self,
        member_info: MemberInfo,
        product_id: str,
        score: float
    ) -> str:
        """生成簡單的推薦理由"""
        # 這裡使用簡單的規則，實際應該使用更複雜的邏輯
        if score > 0.8:
            return "根據您的消費習慣，強烈推薦此產品"
        elif score > 0.6:
            return "此產品與您的偏好相符"
        elif score > 0.4:
            return "您可能會對此產品感興趣"
        else:
            return "推薦給您參考"
    
    def get_model_info(self) -> Dict[str, Any]:
        """獲取模型資訊"""
        if self.metadata is None:
            return {}
        
        return {
            'model_version': self.metadata.get('version'),
            'model_type': self.metadata.get('model_type'),
            'trained_at': self.metadata.get('trained_at'),
            'metrics': self.metadata.get('metrics', {}),
            'total_products': len(self.product_features) if self.product_features is not None else 0,
            'total_members': len(self.member_features) if self.member_features is not None else 0,
        }
    
    def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        return {
            'status': 'healthy' if self.model is not None else 'unhealthy',
            'model_loaded': self.model is not None,
            'member_features_loaded': self.member_features is not None,
            'product_features_loaded': self.product_features is not None,
            'metadata_loaded': self.metadata is not None,
        }


def main():
    """測試推薦引擎"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("測試推薦引擎")
    print("=" * 60)
    
    try:
        # 建立推薦引擎
        print("\n建立推薦引擎...")
        engine = RecommendationEngine()
        
        # 健康檢查
        print("\n健康檢查...")
        health = engine.health_check()
        for key, value in health.items():
            print(f"  {key}: {value}")
        
        # 獲取模型資訊
        print("\n模型資訊...")
        info = engine.get_model_info()
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        # 測試推薦
        print("\n測試推薦...")
        member_info = MemberInfo(
            member_code="CU000001",
            phone="0937024682",
            total_consumption=17400.0,
            accumulated_bonus=500.0,
            recent_purchases=["30463", "31033"]
        )
        
        recommendations = engine.recommend(member_info, n=5)
        
        print(f"\n為會員 {member_info.member_code} 的推薦:")
        for rec in recommendations:
            print(f"  {rec.rank}. {rec.product_name}")
            print(f"     信心分數: {rec.confidence_score:.2f}")
            print(f"     推薦理由: {rec.explanation}")
        
        print("\n" + "=" * 60)
        print("✓ 推薦引擎測試完成！")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"\n✗ 錯誤: {e}")
        print("請先執行訓練: python src/train.py")
    except Exception as e:
        print(f"\n✗ 錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
