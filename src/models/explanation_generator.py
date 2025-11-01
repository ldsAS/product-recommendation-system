"""
推薦理由生成器
根據不同推薦來源生成清晰易懂的推薦理由
"""
import pandas as pd
from typing import Dict, List, Optional, Any
import logging

from src.models.data_models import MemberInfo, Product, RecommendationSource

logger = logging.getLogger(__name__)


class ExplanationGenerator:
    """推薦理由生成器類別"""
    
    def __init__(
        self,
        product_features: Optional[pd.DataFrame] = None,
        member_features: Optional[pd.DataFrame] = None
    ):
        """
        初始化推薦理由生成器
        
        Args:
            product_features: 產品特徵 DataFrame
            member_features: 會員特徵 DataFrame
        """
        self.product_features = product_features
        self.member_features = member_features
        
        logger.info("推薦理由生成器初始化")
    
    def generate_explanation(
        self,
        member_info: MemberInfo,
        product_id: str,
        confidence_score: float,
        source: RecommendationSource = RecommendationSource.ML_MODEL,
        feature_importance: Optional[Dict[str, float]] = None
    ) -> str:
        """
        生成推薦理由
        
        Args:
            member_info: 會員資訊
            product_id: 產品 ID
            confidence_score: 信心分數
            source: 推薦來源
            feature_importance: 特徵重要性
            
        Returns:
            推薦理由文字
        """
        # 根據推薦來源選擇生成策略
        if source == RecommendationSource.COLLABORATIVE_FILTERING:
            return self._generate_cf_explanation(member_info, product_id, confidence_score)
        elif source == RecommendationSource.CONTENT_BASED:
            return self._generate_content_explanation(member_info, product_id, confidence_score)
        elif source == RecommendationSource.RULE_BASED:
            return self._generate_rule_explanation(member_info, product_id, confidence_score)
        elif source == RecommendationSource.FALLBACK:
            return self._generate_fallback_explanation(product_id)
        else:  # ML_MODEL
            return self._generate_ml_explanation(
                member_info, product_id, confidence_score, feature_importance
            )
    
    def _generate_ml_explanation(
        self,
        member_info: MemberInfo,
        product_id: str,
        confidence_score: float,
        feature_importance: Optional[Dict[str, float]] = None
    ) -> str:
        """生成機器學習模型的推薦理由"""
        reasons = []
        
        # 基於購買歷史
        if member_info.recent_purchases:
            # 檢查是否有相似產品
            similar_products = self._find_similar_products(
                product_id, member_info.recent_purchases
            )
            
            if similar_products:
                product_names = [self._get_product_name(p) for p in similar_products[:2]]
                reasons.append(f"與您購買過的{', '.join(product_names)}相似")
        
        # 基於消費金額
        if member_info.total_consumption > 10000:
            reasons.append("符合您的消費水平")
        
        # 基於信心分數
        if confidence_score > 80:
            reasons.append("高度推薦")
        elif confidence_score > 60:
            reasons.append("推薦給您")
        
        # 組合理由
        if reasons:
            return "、".join(reasons)
        else:
            return "根據您的消費習慣推薦"
    
    def _generate_cf_explanation(
        self,
        member_info: MemberInfo,
        product_id: str,
        confidence_score: float
    ) -> str:
        """生成協同過濾的推薦理由"""
        product_name = self._get_product_name(product_id)
        
        explanations = [
            f"與您相似的會員也購買了{product_name}",
            f"購買過類似產品的會員推薦{product_name}",
            f"根據相似會員的購買模式推薦",
        ]
        
        # 根據信心分數選擇
        if confidence_score > 70:
            return explanations[0]
        elif confidence_score > 50:
            return explanations[1]
        else:
            return explanations[2]
    
    def _generate_content_explanation(
        self,
        member_info: MemberInfo,
        product_id: str,
        confidence_score: float
    ) -> str:
        """生成內容基礎的推薦理由"""
        product_name = self._get_product_name(product_id)
        
        if member_info.recent_purchases:
            recent_names = [
                self._get_product_name(p) 
                for p in member_info.recent_purchases[:2]
            ]
            return f"基於您購買過的{', '.join(recent_names)}等產品推薦"
        else:
            return f"根據產品特性推薦{product_name}"
    
    def _generate_rule_explanation(
        self,
        member_info: MemberInfo,
        product_id: str,
        confidence_score: float
    ) -> str:
        """生成規則基礎的推薦理由"""
        product_name = self._get_product_name(product_id)
        
        # 基於消費金額
        if member_info.total_consumption > 20000:
            return f"作為高價值會員，特別推薦{product_name}"
        elif member_info.total_consumption > 10000:
            return f"根據您的消費記錄推薦{product_name}"
        else:
            return f"推薦您嘗試{product_name}"
    
    def _generate_fallback_explanation(self, product_id: str) -> str:
        """生成備用推薦理由"""
        product_name = self._get_product_name(product_id)
        return f"{product_name}是熱門產品，推薦給您參考"
    
    def _get_product_name(self, product_id: str) -> str:
        """獲取產品名稱"""
        if self.product_features is None:
            return f"產品 {product_id}"
        
        product = self.product_features[
            self.product_features['stock_id'] == product_id
        ]
        
        if not product.empty and 'stock_description' in product.columns:
            name = product.iloc[0]['stock_description']
            # 簡化產品名稱（移除過長的描述）
            if len(name) > 20:
                name = name[:20] + "..."
            return name
        
        return f"產品 {product_id}"
    
    def _find_similar_products(
        self,
        product_id: str,
        purchased_products: List[str]
    ) -> List[str]:
        """找出相似產品"""
        if self.product_features is None:
            return []
        
        # 簡單的相似度：檢查產品名稱是否包含相同關鍵字
        target_product = self.product_features[
            self.product_features['stock_id'] == product_id
        ]
        
        if target_product.empty or 'stock_description' not in target_product.columns:
            return []
        
        target_name = target_product.iloc[0]['stock_description']
        
        # 提取關鍵字（簡化版）
        keywords = self._extract_keywords(target_name)
        
        similar = []
        for p_id in purchased_products:
            if p_id == product_id:
                continue
            
            p_product = self.product_features[
                self.product_features['stock_id'] == p_id
            ]
            
            if not p_product.empty and 'stock_description' in p_product.columns:
                p_name = p_product.iloc[0]['stock_description']
                p_keywords = self._extract_keywords(p_name)
                
                # 檢查是否有共同關鍵字
                if keywords & p_keywords:
                    similar.append(p_id)
        
        return similar
    
    def _extract_keywords(self, text: str) -> set:
        """提取關鍵字"""
        # 簡化版：分割文字並提取常見品牌/類別詞
        keywords = set()
        
        # 常見品牌和類別詞
        common_terms = [
            '杏輝', '蓉憶記', '活力', '磷蝦油', '膠囊', '錠',
            '維生素', '保健', '營養', '補充'
        ]
        
        for term in common_terms:
            if term in text:
                keywords.add(term)
        
        return keywords
    
    def generate_detailed_explanation(
        self,
        member_info: MemberInfo,
        product_id: str,
        confidence_score: float,
        feature_importance: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        生成詳細的推薦理由（包含關鍵因素）
        
        Args:
            member_info: 會員資訊
            product_id: 產品 ID
            confidence_score: 信心分數
            feature_importance: 特徵重要性
            
        Returns:
            詳細推薦理由字典
        """
        explanation = {
            'summary': self.generate_explanation(
                member_info, product_id, confidence_score
            ),
            'confidence_score': confidence_score,
            'key_factors': []
        }
        
        # 添加關鍵因素
        if member_info.recent_purchases:
            explanation['key_factors'].append({
                'factor': '購買歷史',
                'description': f"您購買過 {len(member_info.recent_purchases)} 個相關產品"
            })
        
        if member_info.total_consumption > 10000:
            explanation['key_factors'].append({
                'factor': '消費水平',
                'description': f"總消費金額 ${member_info.total_consumption:,.0f}"
            })
        
        if member_info.accumulated_bonus > 0:
            explanation['key_factors'].append({
                'factor': '會員紅利',
                'description': f"累積紅利 {member_info.accumulated_bonus:,.0f} 點"
            })
        
        # 添加產品資訊
        product_info = self._get_product_info(product_id)
        if product_info:
            explanation['product_info'] = product_info
        
        return explanation
    
    def _get_product_info(self, product_id: str) -> Optional[Dict[str, Any]]:
        """獲取產品資訊"""
        if self.product_features is None:
            return None
        
        product = self.product_features[
            self.product_features['stock_id'] == product_id
        ]
        
        if product.empty:
            return None
        
        product_row = product.iloc[0]
        
        info = {
            'name': product_row.get('stock_description', product_id),
            'avg_price': float(product_row.get('avg_price', 0)),
            'popularity_score': float(product_row.get('popularity_score', 0)),
        }
        
        return info


def main():
    """測試推薦理由生成器"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from src.models.data_models import MemberInfo
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("測試推薦理由生成器")
    print("=" * 60)
    
    # 建立生成器
    generator = ExplanationGenerator()
    
    # 測試會員資訊
    member_info = MemberInfo(
        member_code="CU000001",
        phone="0937024682",
        total_consumption=17400.0,
        accumulated_bonus=500.0,
        recent_purchases=["30463", "31033"]
    )
    
    # 測試不同來源的推薦理由
    print("\n測試不同推薦來源的理由:")
    
    sources = [
        RecommendationSource.ML_MODEL,
        RecommendationSource.COLLABORATIVE_FILTERING,
        RecommendationSource.CONTENT_BASED,
        RecommendationSource.RULE_BASED,
        RecommendationSource.FALLBACK,
    ]
    
    for source in sources:
        explanation = generator.generate_explanation(
            member_info=member_info,
            product_id="30469",
            confidence_score=85.5,
            source=source
        )
        print(f"\n{source.value}:")
        print(f"  {explanation}")
    
    # 測試詳細推薦理由
    print("\n測試詳細推薦理由:")
    detailed = generator.generate_detailed_explanation(
        member_info=member_info,
        product_id="30469",
        confidence_score=85.5
    )
    
    print(f"\n摘要: {detailed['summary']}")
    print(f"信心分數: {detailed['confidence_score']}")
    print("關鍵因素:")
    for factor in detailed['key_factors']:
        print(f"  - {factor['factor']}: {factor['description']}")
    
    print("\n" + "=" * 60)
    print("✓ 推薦理由生成器測試完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
