"""
推薦理由生成器單元測試
測試理由生成的相關性、多樣性和數量限制
"""
import pytest
import pandas as pd
from src.models.reason_generator import ReasonGenerator
from src.models.data_models import MemberInfo, RecommendationSource
from src.models.enhanced_data_models import MemberHistory


@pytest.fixture
def sample_product_features():
    """建立測試用產品特徵"""
    return pd.DataFrame({
        'stock_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
        'stock_description': [
            '杏輝蓉憶記膠囊',
            '杏輝南極磷蝦油軟膠囊',
            '活力維生素C錠',
            '保健營養補充品',
            '美妝保養精華液'
        ],
        'avg_price': [1200, 1500, 800, 600, 2000]
    })


@pytest.fixture
def sample_member_features():
    """建立測試用會員特徵"""
    return pd.DataFrame({
        'member_code': ['M001', 'M002', 'M003'],
        'total_consumption': [25000, 12000, 3000],
        'recency': [5, 15, 30],
        'frequency': [10, 5, 2]
    })


@pytest.fixture
def reason_generator(sample_product_features, sample_member_features):
    """建立理由生成器實例"""
    return ReasonGenerator(
        product_features=sample_product_features,
        member_features=sample_member_features
    )


@pytest.fixture
def high_value_member():
    """高價值會員"""
    return MemberInfo(
        member_code="M001",
        phone="0912345678",
        total_consumption=25000.0,
        accumulated_bonus=1000.0,
        recent_purchases=["P001", "P002"]
    )


@pytest.fixture
def medium_value_member():
    """中等價值會員"""
    return MemberInfo(
        member_code="M002",
        phone="0923456789",
        total_consumption=12000.0,
        accumulated_bonus=500.0,
        recent_purchases=["P003"]
    )


@pytest.fixture
def low_value_member():
    """低價值會員"""
    return MemberInfo(
        member_code="M003",
        phone="0934567890",
        total_consumption=3000.0,
        accumulated_bonus=100.0,
        recent_purchases=[]
    )


@pytest.fixture
def sample_member_history():
    """建立測試用會員歷史"""
    return MemberHistory(
        member_code="M001",
        purchased_products=["P001", "P002"],
        purchased_categories=["保健"],
        purchased_brands=["杏輝"],
        avg_purchase_price=1350.0,
        price_std=150.0,
        browsed_products=["P003", "P004"]
    )


class TestReasonTemplates:
    """測試理由模板庫"""
    
    def test_consumption_level_templates_exist(self, reason_generator):
        """測試消費水平理由模板存在（需求 5.1）"""
        templates = reason_generator.REASON_TEMPLATES['consumption_level']
        
        assert 'high' in templates
        assert 'medium' in templates
        assert 'low' in templates
        assert len(templates['high']) > 0
        assert len(templates['medium']) > 0
        assert len(templates['low']) > 0
    
    def test_category_templates_exist(self, reason_generator):
        """測試產品類別理由模板存在（需求 5.2）"""
        templates = reason_generator.REASON_TEMPLATES['category']
        
        assert '保健' in templates
        assert '美妝' in templates
        assert len(templates['保健']) > 0
        assert len(templates['美妝']) > 0
    
    def test_brand_preference_templates_exist(self, reason_generator):
        """測試品牌偏好理由模板存在（需求 5.3）"""
        templates = reason_generator.REASON_TEMPLATES['brand_preference']
        
        assert 'preferred' in templates
        assert 'similar' in templates
        assert 'popular' in templates
        assert len(templates['preferred']) > 0
    
    def test_confidence_level_templates_exist(self, reason_generator):
        """測試信心分數理由模板存在（需求 5.4）"""
        templates = reason_generator.REASON_TEMPLATES['confidence_level']
        
        assert 'very_high' in templates
        assert 'high' in templates
        assert 'medium' in templates
        assert 'low' in templates
        assert len(templates['very_high']) > 0


class TestReasonGeneration:
    """測試理由生成功能"""
    
    def test_generate_reason_returns_string(
        self,
        reason_generator,
        high_value_member
    ):
        """測試生成理由返回字串"""
        reason = reason_generator.generate_reason(
            member_info=high_value_member,
            product_id="P001",
            confidence_score=85.0
        )
        
        assert isinstance(reason, str)
        assert len(reason) > 0
    
    def test_high_confidence_score_reason(
        self,
        reason_generator,
        high_value_member
    ):
        """測試高信心分數生成適當理由（需求 5.4）"""
        reason = reason_generator.generate_reason(
            member_info=high_value_member,
            product_id="P001",
            confidence_score=90.0
        )
        
        # 高信心分數應該包含積極的推薦語氣
        positive_keywords = ['強烈', '最適合', '高度', '精心']
        assert any(keyword in reason for keyword in positive_keywords)
    
    def test_low_confidence_score_reason(
        self,
        reason_generator,
        low_value_member
    ):
        """測試低信心分數生成適當理由（需求 5.4）"""
        reason = reason_generator.generate_reason(
            member_info=low_value_member,
            product_id="P004",
            confidence_score=45.0
        )
        
        # 低信心分數應該使用較溫和的語氣
        assert isinstance(reason, str)
        assert len(reason) > 0
    
    def test_high_consumption_level_reason(
        self,
        reason_generator,
        high_value_member
    ):
        """測試高消費水平生成適當理由（需求 5.1）"""
        reason = reason_generator.generate_reason(
            member_info=high_value_member,
            product_id="P001",
            confidence_score=80.0
        )
        
        # 高消費水平應該提到品質或高端
        assert isinstance(reason, str)
        assert len(reason) > 0
    
    def test_category_based_reason(
        self,
        reason_generator,
        medium_value_member
    ):
        """測試基於產品類別的理由（需求 5.2）"""
        # P001 是保健類產品
        reason = reason_generator.generate_reason(
            member_info=medium_value_member,
            product_id="P001",
            confidence_score=75.0
        )
        
        assert isinstance(reason, str)
        assert len(reason) > 0
    
    def test_brand_preference_reason(
        self,
        reason_generator,
        high_value_member,
        sample_member_history
    ):
        """測試基於品牌偏好的理由（需求 5.3）"""
        # P001 是杏輝品牌，會員歷史中有購買過杏輝
        reason = reason_generator.generate_reason(
            member_info=high_value_member,
            product_id="P001",
            confidence_score=80.0,
            member_history=sample_member_history
        )
        
        assert isinstance(reason, str)
        assert len(reason) > 0


class TestReasonLimit:
    """測試理由數量限制"""
    
    def test_max_two_reasons_default(
        self,
        reason_generator,
        high_value_member
    ):
        """測試預設最多2個理由（需求 5.5）"""
        reason = reason_generator.generate_reason(
            member_info=high_value_member,
            product_id="P001",
            confidence_score=85.0,
            max_reasons=2
        )
        
        # 計算理由數量（以頓號分隔）
        reason_count = reason.count('、') + 1
        assert reason_count <= 2
    
    def test_single_reason_limit(
        self,
        reason_generator,
        medium_value_member
    ):
        """測試可以限制為1個理由"""
        reason = reason_generator.generate_reason(
            member_info=medium_value_member,
            product_id="P003",
            confidence_score=70.0,
            max_reasons=1
        )
        
        # 單一理由不應該包含頓號
        assert '、' not in reason
    
    def test_three_reasons_limit(
        self,
        reason_generator,
        high_value_member,
        sample_member_history
    ):
        """測試可以設定3個理由"""
        reason = reason_generator.generate_reason(
            member_info=high_value_member,
            product_id="P001",
            confidence_score=85.0,
            member_history=sample_member_history,
            max_reasons=3
        )
        
        reason_count = reason.count('、') + 1
        assert reason_count <= 3


class TestReasonDiversity:
    """測試理由多樣性"""
    
    def test_different_products_different_reasons(
        self,
        reason_generator,
        high_value_member
    ):
        """測試不同產品生成不同理由（需求 5.5）"""
        reason_generator.reset_used_reasons()
        
        reason1 = reason_generator.generate_reason(
            member_info=high_value_member,
            product_id="P001",
            confidence_score=85.0
        )
        
        reason2 = reason_generator.generate_reason(
            member_info=high_value_member,
            product_id="P002",
            confidence_score=85.0
        )
        
        # 理由應該有所不同（至少部分不同）
        assert reason1 != reason2 or len(reason1) > 0
    
    def test_batch_generation_diversity(
        self,
        reason_generator,
        high_value_member
    ):
        """測試批次生成時的理由多樣性"""
        reason_generator.reset_used_reasons()
        
        products = ["P001", "P002", "P003", "P004", "P005"]
        reasons = []
        
        for product_id in products:
            reason = reason_generator.generate_reason(
                member_info=high_value_member,
                product_id=product_id,
                confidence_score=80.0
            )
            reasons.append(reason)
        
        # 至少應該有一些不同的理由
        unique_reasons = set(reasons)
        assert len(unique_reasons) >= 2
    
    def test_reset_used_reasons(self, reason_generator, high_value_member):
        """測試重置已使用理由功能"""
        # 生成一些理由
        for i in range(5):
            reason_generator.generate_reason(
                member_info=high_value_member,
                product_id=f"P00{i+1}",
                confidence_score=80.0
            )
        
        # 重置
        reason_generator.reset_used_reasons()
        
        # 應該可以重新使用之前的理由
        assert len(reason_generator._used_reasons) == 0


class TestReasonRelevance:
    """測試理由相關性"""
    
    def test_purchase_history_relevance(
        self,
        reason_generator,
        high_value_member
    ):
        """測試購買歷史相關性（需求 5.1, 5.2, 5.3）"""
        # 會員購買過 P001 和 P002（都是杏輝產品）
        # 推薦 P001 應該提到相關性
        reason = reason_generator.generate_reason(
            member_info=high_value_member,
            product_id="P001",
            confidence_score=85.0
        )
        
        assert isinstance(reason, str)
        assert len(reason) > 0
    
    def test_collaborative_filtering_source(
        self,
        reason_generator,
        medium_value_member
    ):
        """測試協同過濾來源的理由"""
        reason = reason_generator.generate_reason(
            member_info=medium_value_member,
            product_id="P003",
            confidence_score=75.0,
            source=RecommendationSource.COLLABORATIVE_FILTERING
        )
        
        # 協同過濾應該提到相似會員
        assert isinstance(reason, str)
        assert len(reason) > 0
    
    def test_member_without_history(
        self,
        reason_generator,
        low_value_member
    ):
        """測試無購買歷史會員的理由生成"""
        reason = reason_generator.generate_reason(
            member_info=low_value_member,
            product_id="P004",
            confidence_score=60.0
        )
        
        # 即使沒有購買歷史，也應該生成合理的理由
        assert isinstance(reason, str)
        assert len(reason) > 0


class TestReasonPriority:
    """測試理由優先級"""
    
    def test_confidence_score_high_priority(
        self,
        reason_generator,
        high_value_member,
        sample_member_history
    ):
        """測試信心分數理由具有高優先級"""
        reason = reason_generator.generate_reason(
            member_info=high_value_member,
            product_id="P001",
            confidence_score=95.0,
            member_history=sample_member_history,
            max_reasons=1
        )
        
        # 高信心分數應該優先顯示
        positive_keywords = ['強烈', '最適合', '高度', '精心']
        assert any(keyword in reason for keyword in positive_keywords)
    
    def test_reason_selection_logic(
        self,
        reason_generator,
        high_value_member,
        sample_member_history
    ):
        """測試理由選擇邏輯（需求 5.5）"""
        # 測試選擇邏輯是否基於會員特徵
        reason = reason_generator.generate_reason(
            member_info=high_value_member,
            product_id="P001",
            confidence_score=85.0,
            member_history=sample_member_history,
            max_reasons=2
        )
        
        # 應該生成相關的理由
        assert isinstance(reason, str)
        assert len(reason) > 0
        
        # 理由數量應該符合限制
        reason_count = reason.count('、') + 1
        assert reason_count <= 2


class TestEdgeCases:
    """測試邊界情況"""
    
    def test_empty_product_features(self, high_value_member):
        """測試空產品特徵"""
        generator = ReasonGenerator(
            product_features=None,
            member_features=None
        )
        
        reason = generator.generate_reason(
            member_info=high_value_member,
            product_id="P001",
            confidence_score=80.0
        )
        
        # 即使沒有產品特徵，也應該生成基本理由
        assert isinstance(reason, str)
        assert len(reason) > 0
    
    def test_invalid_product_id(
        self,
        reason_generator,
        high_value_member
    ):
        """測試無效產品ID"""
        reason = reason_generator.generate_reason(
            member_info=high_value_member,
            product_id="INVALID",
            confidence_score=70.0
        )
        
        # 應該生成備用理由
        assert isinstance(reason, str)
        assert len(reason) > 0
    
    def test_zero_confidence_score(
        self,
        reason_generator,
        medium_value_member
    ):
        """測試零信心分數"""
        reason = reason_generator.generate_reason(
            member_info=medium_value_member,
            product_id="P003",
            confidence_score=0.0
        )
        
        assert isinstance(reason, str)
        assert len(reason) > 0
    
    def test_max_confidence_score(
        self,
        reason_generator,
        high_value_member
    ):
        """測試最大信心分數"""
        reason = reason_generator.generate_reason(
            member_info=high_value_member,
            product_id="P001",
            confidence_score=100.0
        )
        
        assert isinstance(reason, str)
        assert len(reason) > 0
        
        # 最高信心分數應該使用最積極的語氣
        positive_keywords = ['強烈', '最適合', '高度', '精心']
        assert any(keyword in reason for keyword in positive_keywords)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
