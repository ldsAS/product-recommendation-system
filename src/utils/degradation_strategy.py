"""
降級策略 (DegradationStrategy)
當推薦品質或性能不達標時，自動執行降級策略
"""
from typing import List, Optional
import logging

from src.models.enhanced_data_models import (
    ReferenceValueScore,
    PerformanceMetrics
)
from src.models.data_models import (
    MemberInfo,
    Recommendation,
    RecommendationSource
)

logger = logging.getLogger(__name__)


class DegradationStrategy:
    """
    降級策略
    
    當推薦品質或性能不達標時，自動切換到簡單的降級推薦策略
    """
    
    # 降級閾值配置
    DEGRADATION_THRESHOLDS = {
        'min_quality_score': 40,  # 可參考價值分數低於40分時降級
        'max_response_time_ms': 2000  # 反應時間超過2000ms時降級
    }
    
    def __init__(self, product_features=None):
        """
        初始化降級策略
        
        Args:
            product_features: 產品特徵資料（用於生成熱門推薦）
        """
        self.product_features = product_features
        logger.info("降級策略初始化完成")
    
    def should_degrade(
        self,
        value_score: Optional[ReferenceValueScore] = None,
        performance_metrics: Optional[PerformanceMetrics] = None
    ) -> bool:
        """
        判斷是否需要降級
        
        Args:
            value_score: 可參考價值分數
            performance_metrics: 性能指標
        
        Returns:
            bool: 是否需要降級
        """
        # 檢查品質分數
        if value_score is not None:
            if value_score.overall_score < self.DEGRADATION_THRESHOLDS['min_quality_score']:
                logger.warning(
                    f"品質分數過低 ({value_score.overall_score:.1f} < "
                    f"{self.DEGRADATION_THRESHOLDS['min_quality_score']})，需要降級"
                )
                return True
        
        # 檢查反應時間
        if performance_metrics is not None:
            if performance_metrics.total_time_ms > self.DEGRADATION_THRESHOLDS['max_response_time_ms']:
                logger.warning(
                    f"反應時間過長 ({performance_metrics.total_time_ms:.1f}ms > "
                    f"{self.DEGRADATION_THRESHOLDS['max_response_time_ms']}ms)，需要降級"
                )
                return True
        
        return False
    
    def execute_degradation(
        self,
        member_info: MemberInfo,
        n: int = 5
    ) -> List[Recommendation]:
        """
        執行降級推薦
        
        使用簡單的熱門產品推薦作為降級方案
        
        Args:
            member_info: 會員資訊
            n: 推薦數量
        
        Returns:
            List[Recommendation]: 降級推薦列表
        """
        logger.info(f"執行降級推薦策略，為會員 {member_info.member_code} 生成 {n} 個推薦")
        
        try:
            # 使用熱門產品推薦作為降級方案
            recommendations = self._get_popular_recommendations(member_info, n)
            
            logger.info(f"✓ 降級推薦生成完成，共 {len(recommendations)} 個推薦")
            return recommendations
            
        except Exception as e:
            logger.error(f"降級推薦生成失敗: {e}")
            # 返回空列表作為最後的降級方案
            return []
    
    def _get_popular_recommendations(
        self,
        member_info: MemberInfo,
        n: int
    ) -> List[Recommendation]:
        """
        獲取熱門產品推薦
        
        Args:
            member_info: 會員資訊
            n: 推薦數量
        
        Returns:
            List[Recommendation]: 推薦列表
        """
        import pandas as pd
        
        if self.product_features is None or self.product_features.empty:
            logger.warning("產品特徵資料不可用，無法生成降級推薦")
            return []
        
        # 排除已購買產品
        available_products = self.product_features.copy()
        if member_info.recent_purchases:
            available_products = available_products[
                ~available_products['stock_id'].isin(member_info.recent_purchases)
            ]
        
        if available_products.empty:
            logger.warning("沒有可推薦的產品")
            return []
        
        # 按熱門度排序（如果有熱門度分數）
        if 'popularity_score' in available_products.columns:
            top_products = available_products.nlargest(
                min(n, len(available_products)), 
                'popularity_score'
            )
        else:
            # 如果沒有熱門度分數，隨機選擇
            top_products = available_products.sample(
                min(n, len(available_products))
            )
        
        # 轉換為 Recommendation 物件
        recommendations = []
        for rank, (_, row) in enumerate(top_products.iterrows(), 1):
            product_id = row['stock_id']
            product_name = row.get('stock_description', product_id)
            popularity_score = row.get('popularity_score', 50.0)
            
            rec = Recommendation(
                product_id=product_id,
                product_name=product_name,
                confidence_score=min(100, max(0, popularity_score)),
                explanation="熱門產品推薦",  # 簡單的降級理由
                rank=rank,
                source=RecommendationSource.POPULARITY,
                raw_score=popularity_score
            )
            recommendations.append(rec)
        
        return recommendations
    
    def get_degradation_thresholds(self) -> dict:
        """
        獲取降級閾值配置
        
        Returns:
            dict: 降級閾值配置
        """
        return self.DEGRADATION_THRESHOLDS.copy()
    
    def update_degradation_thresholds(
        self,
        min_quality_score: Optional[float] = None,
        max_response_time_ms: Optional[float] = None
    ) -> None:
        """
        更新降級閾值配置
        
        Args:
            min_quality_score: 最低品質分數閾值
            max_response_time_ms: 最大反應時間閾值
        """
        if min_quality_score is not None:
            self.DEGRADATION_THRESHOLDS['min_quality_score'] = min_quality_score
            logger.info(f"更新最低品質分數閾值: {min_quality_score}")
        
        if max_response_time_ms is not None:
            self.DEGRADATION_THRESHOLDS['max_response_time_ms'] = max_response_time_ms
            logger.info(f"更新最大反應時間閾值: {max_response_time_ms}ms")
