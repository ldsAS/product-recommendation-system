"""
推薦可參考價值評估器
評估推薦結果的相關性、新穎性、可解釋性和多樣性
"""
from typing import List, Dict, Any, Set
import math
import numpy as np
from datetime import datetime

from src.models.data_models import Recommendation, MemberInfo, Product
from src.models.enhanced_data_models import ReferenceValueScore, MemberHistory


class ReferenceValueEvaluator:
    """推薦可參考價值評估器"""
    
    def __init__(self):
        """初始化評估器"""
        # 權重配置
        self.relevance_weight = 0.40  # 相關性權重 40%
        self.novelty_weight = 0.25    # 新穎性權重 25%
        self.explainability_weight = 0.20  # 可解釋性權重 20%
        self.diversity_weight = 0.15  # 多樣性權重 15%
    
    def evaluate(
        self,
        recommendations: List[Recommendation],
        member_info: MemberInfo,
        member_history: MemberHistory,
        products_info: Dict[str, Product] = None
    ) -> ReferenceValueScore:
        """
        評估推薦的可參考價值
        
        Args:
            recommendations: 推薦列表
            member_info: 會員基本資訊
            member_history: 會員歷史資料
            products_info: 產品資訊字典 (product_id -> Product)
        
        Returns:
            ReferenceValueScore: 可參考價值分數
        """
        if not recommendations:
            return ReferenceValueScore(
                overall_score=0.0,
                relevance_score=0.0,
                novelty_score=0.0,
                explainability_score=0.0,
                diversity_score=0.0,
                score_breakdown={},
                timestamp=datetime.now()
            )
        
        # 計算各維度分數
        relevance_score = self.calculate_relevance(
            recommendations, member_info, member_history, products_info
        )
        novelty_score = self.calculate_novelty(
            recommendations, member_history, products_info
        )
        explainability_score = self.calculate_explainability(recommendations)
        diversity_score = self.calculate_diversity(recommendations, products_info)
        
        # 計算綜合分數
        overall_score = (
            relevance_score * self.relevance_weight +
            novelty_score * self.novelty_weight +
            explainability_score * self.explainability_weight +
            diversity_score * self.diversity_weight
        )
        
        # 生成詳細分數拆解
        score_breakdown = {
            'relevance': {
                'score': relevance_score,
                'weight': self.relevance_weight,
                'contribution': relevance_score * self.relevance_weight
            },
            'novelty': {
                'score': novelty_score,
                'weight': self.novelty_weight,
                'contribution': novelty_score * self.novelty_weight
            },
            'explainability': {
                'score': explainability_score,
                'weight': self.explainability_weight,
                'contribution': explainability_score * self.explainability_weight
            },
            'diversity': {
                'score': diversity_score,
                'weight': self.diversity_weight,
                'contribution': diversity_score * self.diversity_weight
            }
        }
        
        return ReferenceValueScore(
            overall_score=overall_score,
            relevance_score=relevance_score,
            novelty_score=novelty_score,
            explainability_score=explainability_score,
            diversity_score=diversity_score,
            score_breakdown=score_breakdown,
            timestamp=datetime.now()
        )
    
    def calculate_relevance(
        self,
        recommendations: List[Recommendation],
        member_info: MemberInfo,
        member_history: MemberHistory,
        products_info: Dict[str, Product] = None
    ) -> float:
        """
        計算相關性分數 (0-100)
        基於購買歷史匹配度、瀏覽偏好匹配度、消費水平匹配度
        
        Args:
            recommendations: 推薦列表
            member_info: 會員基本資訊
            member_history: 會員歷史資料
            products_info: 產品資訊字典
        
        Returns:
            float: 相關性分數 (0-100)
        """
        if not recommendations:
            return 0.0
        
        # 子維度權重 (各佔 33%)
        purchase_history_weight = 0.33
        browsing_preference_weight = 0.33
        consumption_level_weight = 0.34
        
        # 1. 購買歷史匹配度
        purchase_history_score = self._calculate_purchase_history_match(
            recommendations, member_history, products_info
        )
        
        # 2. 瀏覽偏好匹配度
        browsing_preference_score = self._calculate_browsing_preference_match(
            recommendations, member_history, products_info
        )
        
        # 3. 消費水平匹配度
        consumption_level_score = self._calculate_consumption_level_match(
            recommendations, member_info, member_history, products_info
        )
        
        # 整合三個維度
        relevance_score = (
            purchase_history_score * purchase_history_weight +
            browsing_preference_score * browsing_preference_weight +
            consumption_level_score * consumption_level_weight
        ) * 100
        
        return min(100.0, max(0.0, relevance_score))
    
    def _calculate_purchase_history_match(
        self,
        recommendations: List[Recommendation],
        member_history: MemberHistory,
        products_info: Dict[str, Product] = None
    ) -> float:
        """
        計算購買歷史匹配度
        基於類別和品牌重疊度
        
        Returns:
            float: 匹配度 (0-1)
        """
        if not member_history.purchased_categories and not member_history.purchased_brands:
            return 0.5  # 無歷史資料時返回中性分數
        
        if not products_info:
            # 如果沒有產品資訊，使用簡化計算
            return 0.5
        
        category_matches = 0
        brand_matches = 0
        total_recommendations = len(recommendations)
        
        for rec in recommendations:
            product = products_info.get(rec.product_id)
            if not product:
                continue
            
            # 檢查類別匹配
            if product.category and product.category in member_history.purchased_categories:
                category_matches += 1
            
            # 檢查品牌匹配 (假設品牌資訊在產品描述中)
            # 這裡簡化處理，實際應該有專門的品牌欄位
            for brand in member_history.purchased_brands:
                if brand and brand.lower() in product.stock_description.lower():
                    brand_matches += 1
                    break
        
        # 計算匹配比例
        category_match_ratio = category_matches / total_recommendations if total_recommendations > 0 else 0
        brand_match_ratio = brand_matches / total_recommendations if total_recommendations > 0 else 0
        
        # 類別和品牌各佔 50%
        match_score = (category_match_ratio * 0.5 + brand_match_ratio * 0.5)
        
        return match_score
    
    def _calculate_browsing_preference_match(
        self,
        recommendations: List[Recommendation],
        member_history: MemberHistory,
        products_info: Dict[str, Product] = None
    ) -> float:
        """
        計算瀏覽偏好匹配度
        基於產品相似度
        
        Returns:
            float: 匹配度 (0-1)
        """
        if not member_history.browsed_products:
            # 如果沒有瀏覽歷史，使用購買歷史作為替代
            if not member_history.purchased_products:
                return 0.5
            browsed_set = set(member_history.purchased_products)
        else:
            browsed_set = set(member_history.browsed_products)
        
        if not products_info:
            # 簡化計算：檢查推薦產品是否在瀏覽/購買歷史中
            recommended_ids = {rec.product_id for rec in recommendations}
            overlap = len(recommended_ids & browsed_set)
            return min(1.0, overlap / len(recommendations) * 2)  # 乘以2因為部分重疊是好的
        
        # 計算推薦產品與瀏覽產品的相似度
        similarity_scores = []
        
        for rec in recommendations:
            rec_product = products_info.get(rec.product_id)
            if not rec_product:
                continue
            
            max_similarity = 0.0
            for browsed_id in browsed_set:
                browsed_product = products_info.get(browsed_id)
                if not browsed_product:
                    continue
                
                # 計算產品相似度 (基於類別和價格)
                similarity = self._calculate_product_similarity(rec_product, browsed_product)
                max_similarity = max(max_similarity, similarity)
            
            similarity_scores.append(max_similarity)
        
        # 返回平均相似度
        return sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.5
    
    def _calculate_product_similarity(self, product1: Product, product2: Product) -> float:
        """
        計算兩個產品的相似度
        
        Returns:
            float: 相似度 (0-1)
        """
        similarity = 0.0
        
        # 類別相似度 (權重 60%)
        if product1.category and product2.category:
            if product1.category == product2.category:
                similarity += 0.6
        
        # 價格相似度 (權重 40%)
        if product1.avg_price > 0 and product2.avg_price > 0:
            price_diff_ratio = abs(product1.avg_price - product2.avg_price) / max(product1.avg_price, product2.avg_price)
            price_similarity = max(0, 1 - price_diff_ratio)
            similarity += price_similarity * 0.4
        
        return similarity
    
    def _calculate_consumption_level_match(
        self,
        recommendations: List[Recommendation],
        member_info: MemberInfo,
        member_history: MemberHistory,
        products_info: Dict[str, Product] = None
    ) -> float:
        """
        計算消費水平匹配度
        使用高斯分布計算價格匹配分數
        
        Returns:
            float: 匹配度 (0-1)
        """
        if not products_info or member_history.avg_purchase_price <= 0:
            return 0.5  # 無足夠資訊時返回中性分數
        
        avg_price = member_history.avg_purchase_price
        price_std = member_history.price_std if member_history.price_std > 0 else avg_price * 0.3
        
        match_scores = []
        
        for rec in recommendations:
            product = products_info.get(rec.product_id)
            if not product or product.avg_price <= 0:
                continue
            
            # 使用高斯分布計算匹配分數
            # 價格越接近會員平均消費，分數越高
            price_diff = abs(product.avg_price - avg_price)
            gaussian_score = math.exp(-(price_diff ** 2) / (2 * price_std ** 2))
            match_scores.append(gaussian_score)
        
        return sum(match_scores) / len(match_scores) if match_scores else 0.5

    
    def calculate_novelty(
        self,
        recommendations: List[Recommendation],
        member_history: MemberHistory,
        products_info: Dict[str, Product] = None
    ) -> float:
        """
        計算新穎性分數 (0-100)
        基於新類別比例、新品牌比例、新產品比例
        
        Args:
            recommendations: 推薦列表
            member_history: 會員歷史資料
            products_info: 產品資訊字典
        
        Returns:
            float: 新穎性分數 (0-100)
        """
        if not recommendations:
            return 0.0
        
        # 子維度權重
        new_category_weight = 0.5
        new_brand_weight = 0.3
        new_product_weight = 0.2
        
        # 1. 新類別比例
        new_category_ratio = self._calculate_new_category_ratio(
            recommendations, member_history, products_info
        )
        
        # 2. 新品牌比例
        new_brand_ratio = self._calculate_new_brand_ratio(
            recommendations, member_history, products_info
        )
        
        # 3. 新產品比例
        new_product_ratio = self._calculate_new_product_ratio(
            recommendations, member_history
        )
        
        # 整合三個維度
        novelty_score = (
            new_category_ratio * new_category_weight +
            new_brand_ratio * new_brand_weight +
            new_product_ratio * new_product_weight
        ) * 100
        
        return min(100.0, max(0.0, novelty_score))
    
    def _calculate_new_category_ratio(
        self,
        recommendations: List[Recommendation],
        member_history: MemberHistory,
        products_info: Dict[str, Product] = None
    ) -> float:
        """
        計算新類別比例
        
        Returns:
            float: 新類別比例 (0-1)
        """
        if not products_info:
            return 0.3  # 無產品資訊時返回預設值
        
        purchased_categories = set(member_history.purchased_categories)
        new_category_count = 0
        
        for rec in recommendations:
            product = products_info.get(rec.product_id)
            if product and product.category:
                if product.category not in purchased_categories:
                    new_category_count += 1
        
        return new_category_count / len(recommendations) if recommendations else 0.0
    
    def _calculate_new_brand_ratio(
        self,
        recommendations: List[Recommendation],
        member_history: MemberHistory,
        products_info: Dict[str, Product] = None
    ) -> float:
        """
        計算新品牌比例
        
        Returns:
            float: 新品牌比例 (0-1)
        """
        if not products_info:
            return 0.3  # 無產品資訊時返回預設值
        
        purchased_brands = set(member_history.purchased_brands)
        new_brand_count = 0
        
        for rec in recommendations:
            product = products_info.get(rec.product_id)
            if not product:
                continue
            
            # 從產品描述中提取品牌 (簡化處理)
            is_new_brand = True
            for brand in purchased_brands:
                if brand and brand.lower() in product.stock_description.lower():
                    is_new_brand = False
                    break
            
            if is_new_brand:
                new_brand_count += 1
        
        return new_brand_count / len(recommendations) if recommendations else 0.0
    
    def _calculate_new_product_ratio(
        self,
        recommendations: List[Recommendation],
        member_history: MemberHistory
    ) -> float:
        """
        計算新產品比例 (完全未購買過的產品)
        
        Returns:
            float: 新產品比例 (0-1)
        """
        purchased_products = set(member_history.purchased_products)
        new_product_count = 0
        
        for rec in recommendations:
            if rec.product_id not in purchased_products:
                new_product_count += 1
        
        return new_product_count / len(recommendations) if recommendations else 0.0
    
    def calculate_explainability(
        self,
        recommendations: List[Recommendation]
    ) -> float:
        """
        計算可解釋性分數 (0-100)
        基於理由完整性、理由相關性、理由多樣性
        
        Args:
            recommendations: 推薦列表
        
        Returns:
            float: 可解釋性分數 (0-100)
        """
        if not recommendations:
            return 0.0
        
        # 子維度權重
        completeness_weight = 0.4
        relevance_weight = 0.4
        diversity_weight = 0.2
        
        # 1. 理由完整性
        completeness_score = self._calculate_reason_completeness(recommendations)
        
        # 2. 理由相關性
        relevance_score = self._calculate_reason_relevance(recommendations)
        
        # 3. 理由多樣性
        diversity_score = self._calculate_reason_diversity(recommendations)
        
        # 整合三個維度
        explainability_score = (
            completeness_score * completeness_weight +
            relevance_score * relevance_weight +
            diversity_score * diversity_weight
        ) * 100
        
        return min(100.0, max(0.0, explainability_score))
    
    def _calculate_reason_completeness(
        self,
        recommendations: List[Recommendation]
    ) -> float:
        """
        計算理由完整性
        檢查每個推薦是否都有理由
        
        Returns:
            float: 完整性分數 (0-1)
        """
        if not recommendations:
            return 0.0
        
        has_reason_count = 0
        for rec in recommendations:
            if rec.explanation and len(rec.explanation.strip()) > 0:
                has_reason_count += 1
        
        return has_reason_count / len(recommendations)
    
    def _calculate_reason_relevance(
        self,
        recommendations: List[Recommendation]
    ) -> float:
        """
        計算理由相關性
        評估理由與會員特徵的匹配度
        
        Returns:
            float: 相關性分數 (0-1)
        """
        if not recommendations:
            return 0.0
        
        # 關鍵詞列表 (表示理由與會員特徵相關)
        relevant_keywords = [
            '購買', '偏好', '喜愛', '消費', '品牌', '類別',
            '相似', '適合', '推薦', '選擇', '健康', '美容'
        ]
        
        relevance_scores = []
        for rec in recommendations:
            if not rec.explanation:
                relevance_scores.append(0.0)
                continue
            
            # 檢查理由中是否包含相關關鍵詞
            keyword_count = sum(1 for keyword in relevant_keywords if keyword in rec.explanation)
            # 至少包含1個關鍵詞得分0.5，2個或以上得分1.0
            score = min(1.0, keyword_count * 0.5)
            relevance_scores.append(score)
        
        return sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
    
    def _calculate_reason_diversity(
        self,
        recommendations: List[Recommendation]
    ) -> float:
        """
        計算理由多樣性
        避免所有推薦使用相同理由
        
        Returns:
            float: 多樣性分數 (0-1)
        """
        if not recommendations:
            return 0.0
        
        # 收集所有理由
        reasons = [rec.explanation for rec in recommendations if rec.explanation]
        
        if not reasons:
            return 0.0
        
        # 計算不重複理由的比例
        unique_reasons = len(set(reasons))
        total_reasons = len(reasons)
        
        diversity_ratio = unique_reasons / total_reasons if total_reasons > 0 else 0.0
        
        return diversity_ratio
    
    def calculate_diversity(
        self,
        recommendations: List[Recommendation],
        products_info: Dict[str, Product] = None
    ) -> float:
        """
        計算多樣性分數 (0-100)
        基於類別多樣性、價格多樣性、品牌多樣性
        
        Args:
            recommendations: 推薦列表
            products_info: 產品資訊字典
        
        Returns:
            float: 多樣性分數 (0-100)
        """
        if not recommendations:
            return 0.0
        
        # 子維度權重
        category_weight = 0.4
        price_weight = 0.3
        brand_weight = 0.3
        
        # 1. 類別多樣性
        category_diversity = self._calculate_category_diversity(
            recommendations, products_info
        )
        
        # 2. 價格多樣性
        price_diversity = self._calculate_price_diversity(
            recommendations, products_info
        )
        
        # 3. 品牌多樣性
        brand_diversity = self._calculate_brand_diversity(
            recommendations, products_info
        )
        
        # 整合三個維度
        diversity_score = (
            category_diversity * category_weight +
            price_diversity * price_weight +
            brand_diversity * brand_weight
        ) * 100
        
        return min(100.0, max(0.0, diversity_score))
    
    def _calculate_category_diversity(
        self,
        recommendations: List[Recommendation],
        products_info: Dict[str, Product] = None
    ) -> float:
        """
        計算類別多樣性
        
        Returns:
            float: 類別多樣性分數 (0-1)
        """
        if not products_info:
            return 0.5  # 無產品資訊時返回中性分數
        
        categories = set()
        for rec in recommendations:
            product = products_info.get(rec.product_id)
            if product and product.category:
                categories.add(product.category)
        
        # 不同類別數量佔比
        unique_category_count = len(categories)
        total_recommendations = len(recommendations)
        
        # 理想情況是每個推薦都來自不同類別
        diversity_ratio = unique_category_count / total_recommendations if total_recommendations > 0 else 0.0
        
        return diversity_ratio
    
    def _calculate_price_diversity(
        self,
        recommendations: List[Recommendation],
        products_info: Dict[str, Product] = None
    ) -> float:
        """
        計算價格多樣性
        使用標準差衡量價格分散度
        
        Returns:
            float: 價格多樣性分數 (0-1)
        """
        if not products_info:
            return 0.5  # 無產品資訊時返回中性分數
        
        prices = []
        for rec in recommendations:
            product = products_info.get(rec.product_id)
            if product and product.avg_price > 0:
                prices.append(product.avg_price)
        
        if len(prices) < 2:
            return 0.0
        
        # 計算價格標準差
        mean_price = sum(prices) / len(prices)
        variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
        std_dev = math.sqrt(variance)
        
        # 變異係數 (標準差 / 平均值)
        cv = std_dev / mean_price if mean_price > 0 else 0.0
        
        # 將變異係數映射到 0-1 範圍
        # CV > 0.5 表示高度多樣性，得分 1.0
        diversity_score = min(1.0, cv / 0.5)
        
        return diversity_score
    
    def _calculate_brand_diversity(
        self,
        recommendations: List[Recommendation],
        products_info: Dict[str, Product] = None
    ) -> float:
        """
        計算品牌多樣性
        
        Returns:
            float: 品牌多樣性分數 (0-1)
        """
        if not products_info:
            return 0.5  # 無產品資訊時返回中性分數
        
        # 從產品描述中提取品牌 (簡化處理)
        brands = set()
        for rec in recommendations:
            product = products_info.get(rec.product_id)
            if product:
                # 使用產品描述的第一個詞作為品牌 (簡化)
                brand = product.stock_description.split()[0] if product.stock_description else None
                if brand:
                    brands.add(brand)
        
        # 不同品牌數量佔比
        unique_brand_count = len(brands)
        total_recommendations = len(recommendations)
        
        diversity_ratio = unique_brand_count / total_recommendations if total_recommendations > 0 else 0.0
        
        return diversity_ratio
