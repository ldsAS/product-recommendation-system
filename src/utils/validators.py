"""
輸入驗證器
驗證會員資訊的必填欄位和格式，實作資料範圍檢查，生成明確的驗證錯誤訊息
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from pydantic import ValidationError
from src.models.data_models import (
    MemberInfo, RecommendationRequest, Product
)

logger = logging.getLogger(__name__)


class ValidationResult:
    """驗證結果類別"""
    
    def __init__(self, is_valid: bool = True, errors: Optional[List[Dict[str, str]]] = None):
        """
        初始化驗證結果
        
        Args:
            is_valid: 是否驗證通過
            errors: 錯誤列表
        """
        self.is_valid = is_valid
        self.errors = errors or []
    
    def add_error(self, field: str, message: str, code: str = "validation_error"):
        """
        添加錯誤
        
        Args:
            field: 欄位名稱
            message: 錯誤訊息
            code: 錯誤代碼
        """
        self.is_valid = False
        self.errors.append({
            'field': field,
            'message': message,
            'code': code
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors
        }
    
    def __str__(self) -> str:
        """字串表示"""
        if self.is_valid:
            return "驗證通過"
        
        error_messages = [f"  - {err['field']}: {err['message']}" for err in self.errors]
        return f"驗證失敗:\n" + "\n".join(error_messages)


class MemberInfoValidator:
    """會員資訊驗證器"""
    
    # 驗證規則配置
    MIN_CONSUMPTION = 0.0
    MAX_CONSUMPTION = 10000000.0  # 1000萬
    MIN_BONUS = 0.0
    MAX_BONUS = 1000000.0  # 100萬
    MAX_RECENT_PURCHASES = 100
    
    # 電話號碼格式（台灣）
    PHONE_PATTERN = re.compile(r'^09\d{8}$|^0\d{1,2}-?\d{6,8}$')
    
    # 會員編號格式
    MEMBER_CODE_PATTERN = re.compile(r'^[A-Z]{2}\d{6}$')
    
    @classmethod
    def validate(cls, member_info: MemberInfo) -> ValidationResult:
        """
        驗證會員資訊
        
        Args:
            member_info: 會員資訊
            
        Returns:
            驗證結果
        """
        result = ValidationResult()
        
        # 驗證會員編號
        cls._validate_member_code(member_info.member_code, result)
        
        # 驗證電話號碼
        if member_info.phone:
            cls._validate_phone(member_info.phone, result)
        
        # 驗證消費金額
        cls._validate_consumption(member_info.total_consumption, result)
        
        # 驗證累積紅利
        cls._validate_bonus(member_info.accumulated_bonus, result)
        
        # 驗證最近購買
        cls._validate_recent_purchases(member_info.recent_purchases, result)
        
        # 驗證業務邏輯
        cls._validate_business_logic(member_info, result)
        
        return result
    
    @classmethod
    def _validate_member_code(cls, member_code: str, result: ValidationResult):
        """驗證會員編號"""
        if not member_code:
            result.add_error(
                'member_code',
                '會員編號為必填欄位',
                'required_field'
            )
            return
        
        if not isinstance(member_code, str):
            result.add_error(
                'member_code',
                '會員編號必須是字串',
                'invalid_type'
            )
            return
        
        if len(member_code) < 1:
            result.add_error(
                'member_code',
                '會員編號不能為空',
                'empty_value'
            )
            return
        
        if len(member_code) > 50:
            result.add_error(
                'member_code',
                '會員編號長度不能超過 50 個字元',
                'max_length_exceeded'
            )
            return
        
        # 檢查格式（可選，根據實際需求）
        # if not cls.MEMBER_CODE_PATTERN.match(member_code):
        #     result.add_error(
        #         'member_code',
        #         '會員編號格式不正確（應為 2 個大寫字母 + 6 個數字，例如: CU000001）',
        #         'invalid_format'
        #     )
    
    @classmethod
    def _validate_phone(cls, phone: str, result: ValidationResult):
        """驗證電話號碼"""
        if not phone:
            return  # 電話號碼是可選的
        
        # 移除空格和連字號
        cleaned_phone = phone.replace(' ', '').replace('-', '')
        
        # 檢查是否只包含數字
        if not cleaned_phone.isdigit():
            result.add_error(
                'phone',
                '電話號碼只能包含數字、空格和連字號',
                'invalid_characters'
            )
            return
        
        # 檢查長度
        if len(cleaned_phone) < 8 or len(cleaned_phone) > 12:
            result.add_error(
                'phone',
                '電話號碼長度應在 8-12 位數之間',
                'invalid_length'
            )
            return
        
        # 檢查台灣手機號碼格式（09開頭，共10位）
        if cleaned_phone.startswith('09') and len(cleaned_phone) != 10:
            result.add_error(
                'phone',
                '手機號碼應為 10 位數（09開頭）',
                'invalid_mobile_format'
            )
    
    @classmethod
    def _validate_consumption(cls, consumption: float, result: ValidationResult):
        """驗證消費金額"""
        if not isinstance(consumption, (int, float)):
            result.add_error(
                'total_consumption',
                '總消費金額必須是數字',
                'invalid_type'
            )
            return
        
        if consumption < cls.MIN_CONSUMPTION:
            result.add_error(
                'total_consumption',
                f'總消費金額不能小於 {cls.MIN_CONSUMPTION}',
                'min_value_exceeded'
            )
        
        if consumption > cls.MAX_CONSUMPTION:
            result.add_error(
                'total_consumption',
                f'總消費金額不能超過 {cls.MAX_CONSUMPTION:,.0f}',
                'max_value_exceeded'
            )
    
    @classmethod
    def _validate_bonus(cls, bonus: float, result: ValidationResult):
        """驗證累積紅利"""
        if not isinstance(bonus, (int, float)):
            result.add_error(
                'accumulated_bonus',
                '累積紅利必須是數字',
                'invalid_type'
            )
            return
        
        if bonus < cls.MIN_BONUS:
            result.add_error(
                'accumulated_bonus',
                f'累積紅利不能小於 {cls.MIN_BONUS}',
                'min_value_exceeded'
            )
        
        if bonus > cls.MAX_BONUS:
            result.add_error(
                'accumulated_bonus',
                f'累積紅利不能超過 {cls.MAX_BONUS:,.0f}',
                'max_value_exceeded'
            )
    
    @classmethod
    def _validate_recent_purchases(cls, purchases: List[str], result: ValidationResult):
        """驗證最近購買"""
        if not isinstance(purchases, list):
            result.add_error(
                'recent_purchases',
                '最近購買必須是列表',
                'invalid_type'
            )
            return
        
        if len(purchases) > cls.MAX_RECENT_PURCHASES:
            result.add_error(
                'recent_purchases',
                f'最近購買產品數量不能超過 {cls.MAX_RECENT_PURCHASES}',
                'max_items_exceeded'
            )
        
        # 檢查每個產品 ID
        for i, product_id in enumerate(purchases):
            if not isinstance(product_id, str):
                result.add_error(
                    f'recent_purchases[{i}]',
                    '產品 ID 必須是字串',
                    'invalid_type'
                )
            elif not product_id:
                result.add_error(
                    f'recent_purchases[{i}]',
                    '產品 ID 不能為空',
                    'empty_value'
                )
            elif len(product_id) > 50:
                result.add_error(
                    f'recent_purchases[{i}]',
                    '產品 ID 長度不能超過 50 個字元',
                    'max_length_exceeded'
                )
        
        # 檢查重複
        if len(purchases) != len(set(purchases)):
            result.add_error(
                'recent_purchases',
                '最近購買產品列表包含重複的產品 ID',
                'duplicate_values'
            )
    
    @classmethod
    def _validate_business_logic(cls, member_info: MemberInfo, result: ValidationResult):
        """驗證業務邏輯"""
        # 檢查紅利與消費金額的合理性
        # 假設紅利不應超過消費金額的 20%
        if member_info.total_consumption > 0:
            max_reasonable_bonus = member_info.total_consumption * 0.2
            if member_info.accumulated_bonus > max_reasonable_bonus:
                logger.warning(
                    f"會員 {member_info.member_code} 的累積紅利 "
                    f"({member_info.accumulated_bonus}) 超過消費金額的 20% "
                    f"({max_reasonable_bonus:.2f})，可能存在異常"
                )
                # 這裡只記錄警告，不阻止驗證通過
        
        # 檢查有消費但無購買記錄的情況
        if member_info.total_consumption > 0 and not member_info.recent_purchases:
            logger.info(
                f"會員 {member_info.member_code} 有消費記錄但無最近購買產品，"
                "可能是歷史資料或資料不完整"
            )


class RecommendationRequestValidator:
    """推薦請求驗證器"""
    
    MIN_TOP_K = 1
    MAX_TOP_K = 20
    MIN_CONFIDENCE = 0.0
    MAX_CONFIDENCE = 100.0
    
    @classmethod
    def validate(cls, request: RecommendationRequest) -> ValidationResult:
        """
        驗證推薦請求
        
        Args:
            request: 推薦請求
            
        Returns:
            驗證結果
        """
        result = ValidationResult()
        
        # 先驗證會員資訊
        member_info = MemberInfo(
            member_code=request.member_code,
            phone=request.phone,
            total_consumption=request.total_consumption,
            accumulated_bonus=request.accumulated_bonus,
            recent_purchases=request.recent_purchases
        )
        
        member_result = MemberInfoValidator.validate(member_info)
        if not member_result.is_valid:
            result.errors.extend(member_result.errors)
            result.is_valid = False
        
        # 驗證 top_k
        if request.top_k is not None:
            cls._validate_top_k(request.top_k, result)
        
        # 驗證 min_confidence
        if request.min_confidence is not None:
            cls._validate_min_confidence(request.min_confidence, result)
        
        return result
    
    @classmethod
    def _validate_top_k(cls, top_k: int, result: ValidationResult):
        """驗證推薦數量"""
        if not isinstance(top_k, int):
            result.add_error(
                'top_k',
                '推薦數量必須是整數',
                'invalid_type'
            )
            return
        
        if top_k < cls.MIN_TOP_K:
            result.add_error(
                'top_k',
                f'推薦數量不能小於 {cls.MIN_TOP_K}',
                'min_value_exceeded'
            )
        
        if top_k > cls.MAX_TOP_K:
            result.add_error(
                'top_k',
                f'推薦數量不能超過 {cls.MAX_TOP_K}',
                'max_value_exceeded'
            )
    
    @classmethod
    def _validate_min_confidence(cls, min_confidence: float, result: ValidationResult):
        """驗證最低信心分數"""
        if not isinstance(min_confidence, (int, float)):
            result.add_error(
                'min_confidence',
                '最低信心分數必須是數字',
                'invalid_type'
            )
            return
        
        if min_confidence < cls.MIN_CONFIDENCE:
            result.add_error(
                'min_confidence',
                f'最低信心分數不能小於 {cls.MIN_CONFIDENCE}',
                'min_value_exceeded'
            )
        
        if min_confidence > cls.MAX_CONFIDENCE:
            result.add_error(
                'min_confidence',
                f'最低信心分數不能超過 {cls.MAX_CONFIDENCE}',
                'max_value_exceeded'
            )


class ProductValidator:
    """產品驗證器"""
    
    MIN_PRICE = 0.0
    MAX_PRICE = 1000000.0  # 100萬
    
    @classmethod
    def validate(cls, product: Product) -> ValidationResult:
        """
        驗證產品資訊
        
        Args:
            product: 產品資訊
            
        Returns:
            驗證結果
        """
        result = ValidationResult()
        
        # 驗證產品 ID
        cls._validate_stock_id(product.stock_id, result)
        
        # 驗證產品名稱
        cls._validate_stock_description(product.stock_description, result)
        
        # 驗證價格
        cls._validate_price(product.avg_price, result)
        
        # 驗證熱門度分數
        cls._validate_popularity_score(product.popularity_score, result)
        
        return result
    
    @classmethod
    def _validate_stock_id(cls, stock_id: str, result: ValidationResult):
        """驗證產品 ID"""
        if not stock_id:
            result.add_error(
                'stock_id',
                '產品 ID 為必填欄位',
                'required_field'
            )
            return
        
        if not isinstance(stock_id, str):
            result.add_error(
                'stock_id',
                '產品 ID 必須是字串',
                'invalid_type'
            )
            return
        
        if len(stock_id) > 50:
            result.add_error(
                'stock_id',
                '產品 ID 長度不能超過 50 個字元',
                'max_length_exceeded'
            )
    
    @classmethod
    def _validate_stock_description(cls, description: str, result: ValidationResult):
        """驗證產品名稱"""
        if not description:
            result.add_error(
                'stock_description',
                '產品名稱為必填欄位',
                'required_field'
            )
            return
        
        if not isinstance(description, str):
            result.add_error(
                'stock_description',
                '產品名稱必須是字串',
                'invalid_type'
            )
            return
        
        if len(description) > 200:
            result.add_error(
                'stock_description',
                '產品名稱長度不能超過 200 個字元',
                'max_length_exceeded'
            )
    
    @classmethod
    def _validate_price(cls, price: float, result: ValidationResult):
        """驗證價格"""
        if not isinstance(price, (int, float)):
            result.add_error(
                'avg_price',
                '平均價格必須是數字',
                'invalid_type'
            )
            return
        
        if price < cls.MIN_PRICE:
            result.add_error(
                'avg_price',
                f'平均價格不能小於 {cls.MIN_PRICE}',
                'min_value_exceeded'
            )
        
        if price > cls.MAX_PRICE:
            result.add_error(
                'avg_price',
                f'平均價格不能超過 {cls.MAX_PRICE:,.0f}',
                'max_value_exceeded'
            )
    
    @classmethod
    def _validate_popularity_score(cls, score: float, result: ValidationResult):
        """驗證熱門度分數"""
        if not isinstance(score, (int, float)):
            result.add_error(
                'popularity_score',
                '熱門度分數必須是數字',
                'invalid_type'
            )
            return
        
        if score < 0.0 or score > 1.0:
            result.add_error(
                'popularity_score',
                '熱門度分數必須在 0.0 到 1.0 之間',
                'out_of_range'
            )


def validate_member_info(member_info: MemberInfo) -> ValidationResult:
    """
    驗證會員資訊的便捷函數
    
    Args:
        member_info: 會員資訊
        
    Returns:
        驗證結果
    """
    return MemberInfoValidator.validate(member_info)


def validate_recommendation_request(request: RecommendationRequest) -> ValidationResult:
    """
    驗證推薦請求的便捷函數
    
    Args:
        request: 推薦請求
        
    Returns:
        驗證結果
    """
    return RecommendationRequestValidator.validate(request)


def validate_product(product: Product) -> ValidationResult:
    """
    驗證產品資訊的便捷函數
    
    Args:
        product: 產品資訊
        
    Returns:
        驗證結果
    """
    return ProductValidator.validate(product)


def main():
    """測試驗證器"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 70)
    print("測試輸入驗證器")
    print("=" * 70)
    
    # 測試 1: 有效的會員資訊
    print("\n測試 1: 有效的會員資訊")
    valid_member = MemberInfo(
        member_code="CU000001",
        phone="0937024682",
        total_consumption=17400.0,
        accumulated_bonus=500.0,
        recent_purchases=["30463", "31033"]
    )
    
    result = validate_member_info(valid_member)
    print(f"驗證結果: {result}")
    
    # 測試 2: 無效的會員資訊
    print("\n測試 2: 無效的會員資訊")
    invalid_member = MemberInfo(
        member_code="",  # 空的會員編號
        phone="invalid",  # 無效的電話號碼
        total_consumption=-100.0,  # 負數消費
        accumulated_bonus=20000000.0,  # 超過上限
        recent_purchases=["30463", "30463"]  # 重複的產品
    )
    
    result = validate_member_info(invalid_member)
    print(f"驗證結果: {result}")
    
    # 測試 3: 推薦請求
    print("\n測試 3: 推薦請求")
    request = RecommendationRequest(
        member_code="CU000001",
        phone="0937024682",
        total_consumption=17400.0,
        accumulated_bonus=500.0,
        recent_purchases=["30463", "31033"],
        top_k=5,
        min_confidence=0.0
    )
    
    result = validate_recommendation_request(request)
    print(f"驗證結果: {result}")
    
    print("\n" + "=" * 70)
    print("✓ 驗證器測試完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
