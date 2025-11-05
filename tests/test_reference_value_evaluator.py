"""
測試推薦可參考價值評估器
"""
import pytest
from datetime import datetime

from src.models.data_models import Recommendation, MemberInfo, Product, RecommendationSource
from src.models.enhanced_data_models import MemberHistory
from src.models.reference_value_evaluator import ReferenceValueEvaluator


@pytest.fixture
def evaluator():
    """創建評估器實例"""
    return ReferenceValueEvaluator()


@pytest.fixture
def sample_recommendations():
    """創建範例推薦列表"""
    return [
        Recommendation(
            product_id="P001",
            product_name="產品A",
            confidence_score=85.0,
            explanation="基於您的購買歷史推薦",
            rank=1,
            source=RecommendationSource.ML_MODEL
        ),
        Recommendation(
            product_id="P002",
            product_name="產品B",
            confidence_score=78.0,
            explanation="與您相似的會員也購買了此產品",
            rank=2,
            source=RecommendationSource.COLLABORATIVE_FILTERING
        ),
        Recommendation(
            product_id="P003",
            product_name="產品C",
            confidence_score=72.0,
            explanation="適合您的消費水平",
            rank=3,
            source=RecommendationSource.CONTENT_BASED
        ),
        Recommendation(
            product_id="P004",
            product_name="產品D",
            confidence_score=68.0,
            explanation="熱門產品推薦",
            rank=4,
            source=RecommendationSource.ML_MODEL
        ),
        Recommendation(
            product_id="P005",
            product_name="產品E",
            confidence_score=65.0,
            explanation="新品類推薦",
            rank=5,
            source=RecommendationSource.CONTENT_BASED
        )
    ]


@pytest.fixture
def sample_member_info():
    """創建範例會員資訊"""
    return MemberInfo(
        member_code="CU000001",
        phone="0912345678",
        total_consumption=50000.0,
        accumulated_bonus=1000.0,
        recent_purchases=["P001", "P006", "P007"]
    )


@pytest.fixture
def sample_member_history():
    """創建範例會員歷史"""
    return MemberHistory(
        member_code="CU000001",
        purchased_products=["P001", "P006", "P007", "P008"],
        purchased_categories=["保健", "美妝"],
        purchased_brands=["品牌A", "品牌B"],
        avg_purchase_price=500.0,
        price_std=150.0,
        browsed_products=["P001", "P002", "P009", "P010"]
    )


@pytest.fixture
def sample_products_info():
    """創建範例產品資訊字典"""
    return {
        "P001": Product(
            stock_id="P001",
            stock_description="品牌A 保健產品",
            category="保健",
            avg_price=480.0,
            popularity_score=0.8,
            total_sales=100,
            unique_buyers=50
        ),
        "P002": Product(
            stock_id="P002",
            stock_description="品牌A 美妝產品",
            category="美妝",
            avg_price=520.0,
            popularity_score=0.7,
            total_sales=80,
            unique_buyers=40
        ),
        "P003": Product(
            stock_id="P003",
            stock_description="品牌B 保健產品",
            category="保健",
            avg_price=450.0,
            popularity_score=0.6,
            total_sales=60,
            unique_buyers=30
        ),
        "P004": Product(
            stock_id="P004",
            stock_description="品牌C 日用品",
            category="日用品",
            avg_price=300.0,
            popularity_score=0.9,
            total_sales=150,
            unique_buyers=80
        ),
        "P005": Product(
            stock_id="P005",
            stock_description="品牌D 食品",
            category="食品",
            avg_price=200.0,
            popularity_score=0.5,
            total_sales=40,
            unique_buyers=20
        )
    }


class TestReferenceValueEvaluator:
    """測試推薦可參考價值評估器"""
    
    def test_evaluator_initialization(self, evaluator):
        """測試評估器初始化"""
        assert evaluator.relevance_weight == 0.40
        assert evaluator.novelty_weight == 0.25
        assert evaluator.explainability_weight == 0.20
        assert evaluator.diversity_weight == 0.15
        assert evaluator.relevance_weight + evaluator.novelty_weight + \
               evaluator.explainability_weight + evaluator.diversity_weight == 1.0
    
    def test_evaluate_empty_recommendations(self, evaluator, sample_member_info, sample_member_history):
        """測試空推薦列表"""
        result = evaluator.evaluate([], sample_member_info, sample_member_history)
        
        assert result.overall_score == 0.0
        assert result.relevance_score == 0.0
        assert result.novelty_score == 0.0
        assert result.explainability_score == 0.0
        assert result.diversity_score == 0.0
    
    def test_evaluate_with_recommendations(
        self, evaluator, sample_recommendations, sample_member_info, 
        sample_member_history, sample_products_info
    ):
        """測試完整評估流程"""
        result = evaluator.evaluate(
            sample_recommendations,
            sample_member_info,
            sample_member_history,
            sample_products_info
        )
        
        # 驗證分數範圍
        assert 0 <= result.overall_score <= 100
        assert 0 <= result.relevance_score <= 100
        assert 0 <= result.novelty_score <= 100
        assert 0 <= result.explainability_score <= 100
        assert 0 <= result.diversity_score <= 100
        
        # 驗證綜合分數計算
        expected_overall = (
            result.relevance_score * 0.40 +
            result.novelty_score * 0.25 +
            result.explainability_score * 0.20 +
            result.diversity_score * 0.15
        )
        assert abs(result.overall_score - expected_overall) < 0.01
        
        # 驗證分數拆解
        assert 'relevance' in result.score_breakdown
        assert 'novelty' in result.score_breakdown
        assert 'explainability' in result.score_breakdown
        assert 'diversity' in result.score_breakdown
    
    def test_calculate_relevance(
        self, evaluator, sample_recommendations, sample_member_info,
        sample_member_history, sample_products_info
    ):
        """測試相關性分數計算"""
        score = evaluator.calculate_relevance(
            sample_recommendations,
            sample_member_info,
            sample_member_history,
            sample_products_info
        )
        
        assert 0 <= score <= 100
        # 由於推薦中有會員購買過的類別和品牌，相關性應該 > 0
        assert score > 0
    
    def test_calculate_relevance_without_products_info(
        self, evaluator, sample_recommendations, sample_member_info, sample_member_history
    ):
        """測試無產品資訊時的相關性計算"""
        score = evaluator.calculate_relevance(
            sample_recommendations,
            sample_member_info,
            sample_member_history,
            None
        )
        
        assert 0 <= score <= 100
    
    def test_calculate_novelty(
        self, evaluator, sample_recommendations, sample_member_history, sample_products_info
    ):
        """測試新穎性分數計算"""
        score = evaluator.calculate_novelty(
            sample_recommendations,
            sample_member_history,
            sample_products_info
        )
        
        assert 0 <= score <= 100
        # 推薦中包含新類別和新產品，新穎性應該 > 0
        assert score > 0
    
    def test_calculate_novelty_all_new_products(self, evaluator, sample_products_info):
        """測試全新產品的新穎性"""
        new_recommendations = [
            Recommendation(
                product_id="P004",
                product_name="新產品D",
                confidence_score=70.0,
                explanation="新品推薦",
                rank=1,
                source=RecommendationSource.ML_MODEL
            ),
            Recommendation(
                product_id="P005",
                product_name="新產品E",
                confidence_score=65.0,
                explanation="新品推薦",
                rank=2,
                source=RecommendationSource.ML_MODEL
            )
        ]
        
        member_history = MemberHistory(
            member_code="CU000001",
            purchased_products=["P001"],
            purchased_categories=["保健"],
            purchased_brands=["品牌A"],
            avg_purchase_price=500.0,
            price_std=150.0
        )
        
        score = evaluator.calculate_novelty(
            new_recommendations,
            member_history,
            sample_products_info
        )
        
        # 全新產品的新穎性應該很高
        assert score > 50
    
    def test_calculate_explainability(self, evaluator, sample_recommendations):
        """測試可解釋性分數計算"""
        score = evaluator.calculate_explainability(sample_recommendations)
        
        assert 0 <= score <= 100
        # 所有推薦都有理由，可解釋性應該很高
        assert score > 50
    
    def test_calculate_explainability_no_reasons(self, evaluator):
        """測試無理由的可解釋性"""
        recommendations_no_reason = [
            Recommendation(
                product_id="P001",
                product_name="產品A",
                confidence_score=85.0,
                explanation="",
                rank=1,
                source=RecommendationSource.ML_MODEL
            ),
            Recommendation(
                product_id="P002",
                product_name="產品B",
                confidence_score=78.0,
                explanation="",
                rank=2,
                source=RecommendationSource.ML_MODEL
            )
        ]
        
        score = evaluator.calculate_explainability(recommendations_no_reason)
        
        # 無理由的可解釋性應該很低
        assert score < 50
    
    def test_calculate_diversity(
        self, evaluator, sample_recommendations, sample_products_info
    ):
        """測試多樣性分數計算"""
        score = evaluator.calculate_diversity(
            sample_recommendations,
            sample_products_info
        )
        
        assert 0 <= score <= 100
        # 推薦包含多個類別和不同價格，多樣性應該 > 0
        assert score > 0
    
    def test_calculate_diversity_same_category(self, evaluator):
        """測試相同類別的多樣性"""
        same_category_recommendations = [
            Recommendation(
                product_id="P001",
                product_name="產品A",
                confidence_score=85.0,
                explanation="推薦",
                rank=1,
                source=RecommendationSource.ML_MODEL
            ),
            Recommendation(
                product_id="P003",
                product_name="產品C",
                confidence_score=72.0,
                explanation="推薦",
                rank=2,
                source=RecommendationSource.ML_MODEL
            )
        ]
        
        products_info = {
            "P001": Product(
                stock_id="P001",
                stock_description="品牌A 保健產品",
                category="保健",
                avg_price=480.0,
                popularity_score=0.8
            ),
            "P003": Product(
                stock_id="P003",
                stock_description="品牌B 保健產品",
                category="保健",
                avg_price=450.0,
                popularity_score=0.6
            )
        }
        
        score = evaluator.calculate_diversity(
            same_category_recommendations,
            products_info
        )
        
        # 相同類別的多樣性應該較低
        assert score < 70
    
    def test_score_breakdown_structure(
        self, evaluator, sample_recommendations, sample_member_info,
        sample_member_history, sample_products_info
    ):
        """測試分數拆解結構"""
        result = evaluator.evaluate(
            sample_recommendations,
            sample_member_info,
            sample_member_history,
            sample_products_info
        )
        
        # 驗證每個維度的拆解結構
        for dimension in ['relevance', 'novelty', 'explainability', 'diversity']:
            assert dimension in result.score_breakdown
            assert 'score' in result.score_breakdown[dimension]
            assert 'weight' in result.score_breakdown[dimension]
            assert 'contribution' in result.score_breakdown[dimension]
            
            # 驗證貢獻值計算
            expected_contribution = (
                result.score_breakdown[dimension]['score'] *
                result.score_breakdown[dimension]['weight']
            )
            actual_contribution = result.score_breakdown[dimension]['contribution']
            assert abs(expected_contribution - actual_contribution) < 0.01
    
    def test_weighted_score_calculation(
        self, evaluator, sample_recommendations, sample_member_info,
        sample_member_history, sample_products_info
    ):
        """測試加權分數計算"""
        result = evaluator.evaluate(
            sample_recommendations,
            sample_member_info,
            sample_member_history,
            sample_products_info
        )
        
        # 手動計算綜合分數
        manual_overall = (
            result.relevance_score * evaluator.relevance_weight +
            result.novelty_score * evaluator.novelty_weight +
            result.explainability_score * evaluator.explainability_weight +
            result.diversity_score * evaluator.diversity_weight
        )
        
        # 驗證計算結果
        assert abs(result.overall_score - manual_overall) < 0.01
    
    def test_boundary_cases(self, evaluator):
        """測試邊界情況"""
        # 測試單個推薦
        single_rec = [
            Recommendation(
                product_id="P001",
                product_name="產品A",
                confidence_score=85.0,
                explanation="推薦理由",
                rank=1,
                source=RecommendationSource.ML_MODEL
            )
        ]
        
        member_info = MemberInfo(
            member_code="CU000001",
            total_consumption=1000.0,
            accumulated_bonus=100.0
        )
        
        member_history = MemberHistory(
            member_code="CU000001",
            purchased_products=[],
            purchased_categories=[],
            purchased_brands=[]
        )
        
        result = evaluator.evaluate(single_rec, member_info, member_history)
        
        # 即使是單個推薦，也應該有有效的分數
        assert 0 <= result.overall_score <= 100
        assert result.explainability_score > 0  # 有理由，可解釋性應該 > 0
    
    def test_reason_completeness(self, evaluator):
        """測試理由完整性計算"""
        # 部分推薦有理由
        partial_reasons = [
            Recommendation(
                product_id="P001",
                product_name="產品A",
                confidence_score=85.0,
                explanation="有理由",
                rank=1,
                source=RecommendationSource.ML_MODEL
            ),
            Recommendation(
                product_id="P002",
                product_name="產品B",
                confidence_score=78.0,
                explanation="",
                rank=2,
                source=RecommendationSource.ML_MODEL
            )
        ]
        
        completeness = evaluator._calculate_reason_completeness(partial_reasons)
        assert completeness == 0.5  # 50% 有理由
    
    def test_reason_diversity(self, evaluator):
        """測試理由多樣性計算"""
        # 相同理由
        same_reasons = [
            Recommendation(
                product_id="P001",
                product_name="產品A",
                confidence_score=85.0,
                explanation="相同理由",
                rank=1,
                source=RecommendationSource.ML_MODEL
            ),
            Recommendation(
                product_id="P002",
                product_name="產品B",
                confidence_score=78.0,
                explanation="相同理由",
                rank=2,
                source=RecommendationSource.ML_MODEL
            )
        ]
        
        diversity = evaluator._calculate_reason_diversity(same_reasons)
        assert diversity == 0.5  # 只有1個不重複理由 / 2個總理由
        
        # 不同理由
        different_reasons = [
            Recommendation(
                product_id="P001",
                product_name="產品A",
                confidence_score=85.0,
                explanation="理由A",
                rank=1,
                source=RecommendationSource.ML_MODEL
            ),
            Recommendation(
                product_id="P002",
                product_name="產品B",
                confidence_score=78.0,
                explanation="理由B",
                rank=2,
                source=RecommendationSource.ML_MODEL
            )
        ]
        
        diversity = evaluator._calculate_reason_diversity(different_reasons)
        assert diversity == 1.0  # 2個不重複理由 / 2個總理由


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
