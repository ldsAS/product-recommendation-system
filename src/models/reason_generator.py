"""
推薦理由生成器 (ReasonGenerator)
優化版本 - 擴展理由模板庫並實作智能理由選擇邏輯
"""
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import logging
import random

from src.models.data_models import MemberInfo, RecommendationSource
from src.models.enhanced_data_models import MemberHistory

logger = logging.getLogger(__name__)


class ReasonGenerator:
    """推薦理由生成器類別"""
    
    # 理由模板庫
    REASON_TEMPLATES = {
        # 消費水平相關理由模板 (需求 5.1)
        'consumption_level': {
            'high': [
                "符合您的高端消費偏好",
                "適合您的品質要求",
                "作為高價值會員的專屬推薦",
                "精選高品質產品推薦"
            ],
            'medium': [
                "適合您的消費水平",
                "性價比優秀的選擇",
                "符合您的預算範圍",
                "物超所值的推薦"
            ],
            'low': [
                "經濟實惠的選擇",
                "超值推薦",
                "入門級優質產品",
                "價格親民的好選擇"
            ]
        },
        
        # 產品類別相關理由模板 (需求 5.2)
        'category': {
            '保健': [
                "維護健康的好選擇",
                "關愛健康必備",
                "提升生活品質",
                "守護您的健康"
            ],
            '美妝': [
                "美麗加分的選擇",
                "提升魅力必備",
                "展現自信光彩",
                "煥發迷人風采"
            ],
            '營養': [
                "補充營養所需",
                "均衡營養配方",
                "活力來源",
                "營養補給站"
            ],
            '保養': [
                "呵護肌膚",
                "延緩老化",
                "保持青春活力",
                "肌膚保養首選"
            ]
        },
        
        # 品牌偏好相關理由模板 (需求 5.3)
        'brand_preference': {
            'preferred': [
                "您偏愛的品牌",
                "信賴品牌推薦",
                "您熟悉的品牌",
                "您喜愛的品牌新品"
            ],
            'similar': [
                "與您喜愛品牌相似",
                "同等級品牌",
                "品質相當的品牌",
                "值得信賴的品牌"
            ],
            'popular': [
                "熱門品牌",
                "口碑品牌",
                "暢銷品牌",
                "廣受好評的品牌"
            ]
        },
        
        # 信心分數相關理由模板 (需求 5.4)
        'confidence_level': {
            'very_high': [  # > 85
                "強烈推薦",
                "最適合您",
                "高度符合您的需求",
                "為您精心挑選"
            ],
            'high': [  # 70-85
                "推薦給您",
                "值得考慮",
                "適合您的選擇",
                "符合您的偏好"
            ],
            'medium': [  # 50-70
                "推薦嘗試",
                "可以考慮",
                "不錯的選擇",
                "值得一試"
            ],
            'low': [  # < 50
                "供您參考",
                "備選方案",
                "可供選擇",
                "參考選項"
            ]
        },
        
        # 購買歷史相關理由
        'purchase_history': {
            'similar_product': [
                "與您購買過的產品相似",
                "基於您的購買記錄推薦",
                "您可能也會喜歡",
                "延續您的購買偏好"
            ],
            'same_category': [
                "與您常購買的類別相同",
                "您熟悉的產品類型",
                "符合您的類別偏好",
                "同類型產品推薦"
            ],
            'complementary': [
                "與您購買的產品搭配使用",
                "完美搭配組合",
                "相輔相成的選擇",
                "搭配效果更佳"
            ]
        },
        
        # 新穎性相關理由
        'novelty': {
            'new_category': [
                "探索新類別",
                "拓展您的選擇",
                "嘗試新領域",
                "發現新可能"
            ],
            'new_brand': [
                "發現新品牌",
                "值得嘗試的新品牌",
                "品質保證的新選擇",
                "新品牌體驗"
            ],
            'trending': [
                "當前熱門產品",
                "最新流行趨勢",
                "人氣商品",
                "熱銷新品"
            ]
        },
        
        # 協同過濾相關理由
        'collaborative': [
            "與您相似的會員也購買",
            "相似偏好會員推薦",
            "同類型會員的選擇",
            "相似消費習慣會員喜愛"
        ]
    }
    
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
        
        # 用於追蹤已使用的理由，確保多樣性
        self._used_reasons = set()
        
        logger.info("推薦理由生成器初始化完成")
    
    def reset_used_reasons(self):
        """重置已使用理由追蹤（用於新的推薦批次）"""
        self._used_reasons = set()
    
    def generate_reason(
        self,
        member_info: MemberInfo,
        product_id: str,
        confidence_score: float,
        member_history: Optional[MemberHistory] = None,
        source: RecommendationSource = RecommendationSource.ML_MODEL,
        max_reasons: int = 2
    ) -> str:
        """
        生成推薦理由（需求 5.5 - 最多2個理由）
        
        Args:
            member_info: 會員資訊
            product_id: 產品 ID
            confidence_score: 信心分數 (0-100)
            member_history: 會員歷史資料
            source: 推薦來源
            max_reasons: 最多理由數量（預設2個）
            
        Returns:
            推薦理由文字
        """
        # 選擇理由
        reasons = self._select_reasons(
            member_info=member_info,
            product_id=product_id,
            confidence_score=confidence_score,
            member_history=member_history,
            source=source,
            max_reasons=max_reasons
        )
        
        # 組合理由
        if reasons:
            return "、".join(reasons)
        else:
            return "根據您的消費習慣推薦"
    
    def _select_reasons(
        self,
        member_info: MemberInfo,
        product_id: str,
        confidence_score: float,
        member_history: Optional[MemberHistory],
        source: RecommendationSource,
        max_reasons: int
    ) -> List[str]:
        """
        選擇推薦理由（需求 5.5 - 基於會員特徵選擇並排序）
        
        Returns:
            理由列表
        """
        # 收集候選理由及其優先級
        candidate_reasons: List[Tuple[str, int]] = []
        
        # 1. 基於信心分數的理由（優先級最高）
        confidence_reason = self._get_confidence_reason(confidence_score)
        if confidence_reason:
            candidate_reasons.append((confidence_reason, 100))
        
        # 2. 基於推薦來源的理由
        if source == RecommendationSource.COLLABORATIVE_FILTERING:
            collab_reason = self._get_template('collaborative')
            if collab_reason:
                candidate_reasons.append((collab_reason, 90))
        
        # 3. 基於購買歷史的理由
        if member_info.recent_purchases:
            history_reason = self._get_purchase_history_reason(
                product_id, member_info.recent_purchases
            )
            if history_reason:
                candidate_reasons.append((history_reason, 85))
        
        # 4. 基於消費水平的理由
        consumption_reason = self._get_consumption_level_reason(
            member_info.total_consumption
        )
        if consumption_reason:
            candidate_reasons.append((consumption_reason, 80))
        
        # 5. 基於產品類別的理由
        category_reason = self._get_category_reason(product_id)
        if category_reason:
            candidate_reasons.append((category_reason, 75))
        
        # 6. 基於品牌偏好的理由
        if member_history:
            brand_reason = self._get_brand_preference_reason(
                product_id, member_history
            )
            if brand_reason:
                candidate_reasons.append((brand_reason, 70))
        
        # 7. 基於新穎性的理由
        if member_history:
            novelty_reason = self._get_novelty_reason(
                product_id, member_history
            )
            if novelty_reason:
                candidate_reasons.append((novelty_reason, 65))
        
        # 按優先級排序並確保多樣性
        selected_reasons = self._prioritize_and_diversify(
            candidate_reasons, max_reasons
        )
        
        return selected_reasons
    
    def _prioritize_and_diversify(
        self,
        candidate_reasons: List[Tuple[str, int]],
        max_reasons: int
    ) -> List[str]:
        """
        理由優先級排序並確保多樣性（需求 5.5）
        
        Args:
            candidate_reasons: 候選理由列表 [(理由, 優先級)]
            max_reasons: 最多理由數量
            
        Returns:
            選中的理由列表
        """
        # 按優先級排序
        sorted_reasons = sorted(
            candidate_reasons,
            key=lambda x: x[1],
            reverse=True
        )
        
        # 選擇理由，確保多樣性（避免重複）
        selected = []
        for reason, priority in sorted_reasons:
            if len(selected) >= max_reasons:
                break
            
            # 檢查是否與已選理由過於相似
            if not self._is_too_similar(reason, selected):
                selected.append(reason)
                self._used_reasons.add(reason)
        
        return selected
    
    def _is_too_similar(self, reason: str, selected_reasons: List[str]) -> bool:
        """
        檢查理由是否與已選理由過於相似
        
        Args:
            reason: 待檢查的理由
            selected_reasons: 已選理由列表
            
        Returns:
            是否過於相似
        """
        # 提取關鍵詞
        keywords = set(reason.split())
        
        for selected in selected_reasons:
            selected_keywords = set(selected.split())
            # 如果有超過50%的關鍵詞重疊，視為相似
            overlap = len(keywords & selected_keywords)
            if overlap > len(keywords) * 0.5:
                return True
        
        return False
    
    def _get_confidence_reason(self, confidence_score: float) -> Optional[str]:
        """獲取基於信心分數的理由（需求 5.4）"""
        if confidence_score > 85:
            level = 'very_high'
        elif confidence_score > 70:
            level = 'high'
        elif confidence_score > 50:
            level = 'medium'
        else:
            level = 'low'
        
        return self._get_template('confidence_level', level)
    
    def _get_consumption_level_reason(
        self,
        total_consumption: float
    ) -> Optional[str]:
        """獲取基於消費水平的理由（需求 5.1）"""
        if total_consumption > 20000:
            level = 'high'
        elif total_consumption > 5000:
            level = 'medium'
        else:
            level = 'low'
        
        return self._get_template('consumption_level', level)
    
    def _get_category_reason(self, product_id: str) -> Optional[str]:
        """獲取基於產品類別的理由（需求 5.2）"""
        if self.product_features is None:
            return None
        
        product = self.product_features[
            self.product_features['stock_id'] == product_id
        ]
        
        if product.empty:
            return None
        
        # 從產品描述推斷類別
        description = product.iloc[0].get('stock_description', '')
        
        # 簡單的關鍵詞匹配
        if any(keyword in description for keyword in ['保健', '健康', '維生素', '營養']):
            category = '保健'
        elif any(keyword in description for keyword in ['美妝', '保養', '面膜', '精華']):
            category = '美妝'
        elif any(keyword in description for keyword in ['營養', '補充', '蛋白']):
            category = '營養'
        elif any(keyword in description for keyword in ['保養', '護理', '修護']):
            category = '保養'
        else:
            return None
        
        return self._get_template('category', category)
    
    def _get_brand_preference_reason(
        self,
        product_id: str,
        member_history: MemberHistory
    ) -> Optional[str]:
        """獲取基於品牌偏好的理由（需求 5.3）"""
        if self.product_features is None:
            return None
        
        product = self.product_features[
            self.product_features['stock_id'] == product_id
        ]
        
        if product.empty:
            return None
        
        # 從產品描述提取品牌
        description = product.iloc[0].get('stock_description', '')
        product_brand = self._extract_brand(description)
        
        if not product_brand:
            return None
        
        # 檢查會員是否購買過該品牌
        if product_brand in member_history.purchased_brands:
            preference_type = 'preferred'
        else:
            # 檢查是否為熱門品牌
            preference_type = 'popular'
        
        return self._get_template('brand_preference', preference_type)
    
    def _get_purchase_history_reason(
        self,
        product_id: str,
        recent_purchases: List[str]
    ) -> Optional[str]:
        """獲取基於購買歷史的理由"""
        if self.product_features is None or not recent_purchases:
            return None
        
        # 檢查是否有相似產品
        similar_products = self._find_similar_products(product_id, recent_purchases)
        
        if similar_products:
            return self._get_template('purchase_history', 'similar_product')
        
        # 檢查是否為相同類別
        if self._is_same_category(product_id, recent_purchases):
            return self._get_template('purchase_history', 'same_category')
        
        return None
    
    def _get_novelty_reason(
        self,
        product_id: str,
        member_history: MemberHistory
    ) -> Optional[str]:
        """獲取基於新穎性的理由"""
        if self.product_features is None:
            return None
        
        product = self.product_features[
            self.product_features['stock_id'] == product_id
        ]
        
        if product.empty:
            return None
        
        # 檢查是否為新類別
        description = product.iloc[0].get('stock_description', '')
        product_category = self._extract_category(description)
        
        if product_category and product_category not in member_history.purchased_categories:
            return self._get_template('novelty', 'new_category')
        
        # 檢查是否為新品牌
        product_brand = self._extract_brand(description)
        if product_brand and product_brand not in member_history.purchased_brands:
            return self._get_template('novelty', 'new_brand')
        
        return None
    
    def _get_template(
        self,
        category: str,
        subcategory: Optional[str] = None
    ) -> Optional[str]:
        """
        從模板庫獲取理由
        
        Args:
            category: 理由類別
            subcategory: 理由子類別
            
        Returns:
            理由文字
        """
        templates = self.REASON_TEMPLATES.get(category)
        
        if templates is None:
            return None
        
        if subcategory:
            template_list = templates.get(subcategory, [])
        else:
            template_list = templates if isinstance(templates, list) else []
        
        if not template_list:
            return None
        
        # 隨機選擇一個模板（確保多樣性）
        available_templates = [t for t in template_list if t not in self._used_reasons]
        
        if not available_templates:
            # 如果所有模板都用過了，重置並重新選擇
            available_templates = template_list
        
        return random.choice(available_templates)
    
    def _extract_brand(self, description: str) -> Optional[str]:
        """從產品描述提取品牌"""
        # 常見品牌列表
        brands = ['杏輝', '蓉憶記', '活力', '南極', '磷蝦油']
        
        for brand in brands:
            if brand in description:
                return brand
        
        return None
    
    def _extract_category(self, description: str) -> Optional[str]:
        """從產品描述提取類別"""
        categories = {
            '保健': ['保健', '健康', '維生素', '營養'],
            '美妝': ['美妝', '保養', '面膜', '精華'],
            '營養': ['營養', '補充', '蛋白'],
            '保養': ['保養', '護理', '修護']
        }
        
        for category, keywords in categories.items():
            if any(keyword in description for keyword in keywords):
                return category
        
        return None
    
    def _find_similar_products(
        self,
        product_id: str,
        purchased_products: List[str]
    ) -> List[str]:
        """找出相似產品"""
        if self.product_features is None:
            return []
        
        target_product = self.product_features[
            self.product_features['stock_id'] == product_id
        ]
        
        if target_product.empty or 'stock_description' not in target_product.columns:
            return []
        
        target_name = target_product.iloc[0]['stock_description']
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
                
                if keywords & p_keywords:
                    similar.append(p_id)
        
        return similar
    
    def _is_same_category(
        self,
        product_id: str,
        purchased_products: List[str]
    ) -> bool:
        """檢查是否為相同類別"""
        if self.product_features is None:
            return False
        
        target_category = self._get_product_category(product_id)
        
        if not target_category:
            return False
        
        for p_id in purchased_products:
            p_category = self._get_product_category(p_id)
            if p_category == target_category:
                return True
        
        return False
    
    def _get_product_category(self, product_id: str) -> Optional[str]:
        """獲取產品類別"""
        if self.product_features is None:
            return None
        
        product = self.product_features[
            self.product_features['stock_id'] == product_id
        ]
        
        if product.empty:
            return None
        
        description = product.iloc[0].get('stock_description', '')
        return self._extract_category(description)
    
    def _extract_keywords(self, text: str) -> set:
        """提取關鍵字"""
        keywords = set()
        
        common_terms = [
            '杏輝', '蓉憶記', '活力', '磷蝦油', '膠囊', '錠',
            '維生素', '保健', '營養', '補充', '南極'
        ]
        
        for term in common_terms:
            if term in text:
                keywords.add(term)
        
        return keywords
    
    def _get_product_name(self, product_id: str) -> str:
        """獲取產品名稱"""
        if self.product_features is None:
            return f"產品 {product_id}"
        
        product = self.product_features[
            self.product_features['stock_id'] == product_id
        ]
        
        if not product.empty and 'stock_description' in product.columns:
            name = product.iloc[0]['stock_description']
            if len(name) > 20:
                name = name[:20] + "..."
            return name
        
        return f"產品 {product_id}"
