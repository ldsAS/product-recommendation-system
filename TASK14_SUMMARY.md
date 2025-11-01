# 任務 14 完成總結

## 任務描述
實作輸入驗證 (Input Validation)

## 完成項目

### 1. 核心實作
- ✅ 建立 `src/utils/validators.py`
- ✅ 實作 `ValidationResult` 類別
- ✅ 實作 `MemberInfoValidator` 類別
- ✅ 實作 `RecommendationRequestValidator` 類別
- ✅ 實作 `ProductValidator` 類別

### 2. 驗證功能

#### 2.1 會員資訊驗證
- ✅ 驗證會員編號（必填、格式、長度）
- ✅ 驗證電話號碼（格式、長度、台灣號碼規則）
- ✅ 驗證總消費金額（範圍：0 - 10,000,000）
- ✅ 驗證累積紅利（範圍：0 - 1,000,000）
- ✅ 驗證最近購買（數量限制、重複檢查、空值檢查）
- ✅ 驗證業務邏輯（紅利與消費金額合理性）

#### 2.2 推薦請求驗證
- ✅ 驗證會員資訊（繼承會員資訊驗證）
- ✅ 驗證 top_k 參數（範圍：1 - 20）
- ✅ 驗證 min_confidence 參數（範圍：0.0 - 100.0）

#### 2.3 產品驗證
- ✅ 驗證產品 ID（必填、格式、長度）
- ✅ 驗證產品名稱（必填、長度）
- ✅ 驗證平均價格（範圍：0 - 1,000,000）
- ✅ 驗證熱門度分數（範圍：0.0 - 1.0）

### 3. 錯誤處理
- ✅ 生成明確的錯誤訊息
- ✅ 指出需要修正的欄位
- ✅ 提供錯誤代碼（error code）
- ✅ 支援多個錯誤同時返回

### 4. 測試與示範
- ✅ 建立 `scripts/demo_validators.py` 示範腳本
- ✅ 測試所有驗證規則
- ✅ 測試邊界值
- ✅ 測試錯誤情況

## 需求對應

### 需求 1.2
✅ WHEN 銷售員提交顧客資訊時，推薦系統應驗證所有必填欄位的完整性和格式正確性

**實作**: `MemberInfoValidator` 驗證所有必填欄位和格式

### 需求 1.3
✅ IF 輸入資料格式不正確或缺少必填欄位，THEN 推薦系統應顯示明確的錯誤訊息並指出需要修正的欄位

**實作**: `ValidationResult` 提供明確的錯誤訊息和欄位資訊

### 需求 7.3
✅ IF 輸入的顧客資訊超出模型訓練範圍，THEN 推薦系統應提供基於規則的備用推薦或提示資料異常

**實作**: 驗證器檢查資料範圍，記錄警告但不阻止處理

## 驗證規則

### 會員編號
- 必填欄位
- 長度：1-50 個字元
- 類型：字串

### 電話號碼
- 可選欄位
- 格式：台灣手機號碼（09開頭，10位數）或市話號碼
- 只能包含數字、空格和連字號
- 長度：8-12 位數

### 總消費金額
- 範圍：0 - 10,000,000
- 類型：數字（整數或浮點數）

### 累積紅利
- 範圍：0 - 1,000,000
- 類型：數字（整數或浮點數）
- 業務邏輯：不應超過消費金額的 20%（警告）

### 最近購買
- 類型：字串列表
- 最大數量：100 個產品
- 不允許重複
- 不允許空值

### 推薦數量 (top_k)
- 範圍：1 - 20
- 類型：整數

### 最低信心分數 (min_confidence)
- 範圍：0.0 - 100.0
- 類型：數字（整數或浮點數）

## 程式碼結構

```
src/utils/validators.py
├── ValidationResult 類別
│   ├── __init__() - 初始化驗證結果
│   ├── add_error() - 添加錯誤
│   ├── to_dict() - 轉換為字典
│   └── __str__() - 字串表示
│
├── MemberInfoValidator 類別
│   ├── validate() - 驗證會員資訊
│   ├── _validate_member_code() - 驗證會員編號
│   ├── _validate_phone() - 驗證電話號碼
│   ├── _validate_consumption() - 驗證消費金額
│   ├── _validate_bonus() - 驗證累積紅利
│   ├── _validate_recent_purchases() - 驗證最近購買
│   └── _validate_business_logic() - 驗證業務邏輯
│
├── RecommendationRequestValidator 類別
│   ├── validate() - 驗證推薦請求
│   ├── _validate_top_k() - 驗證推薦數量
│   └── _validate_min_confidence() - 驗證最低信心分數
│
├── ProductValidator 類別
│   ├── validate() - 驗證產品資訊
│   ├── _validate_stock_id() - 驗證產品 ID
│   ├── _validate_stock_description() - 驗證產品名稱
│   ├── _validate_price() - 驗證價格
│   └── _validate_popularity_score() - 驗證熱門度分數
│
└── 便捷函數
    ├── validate_member_info() - 驗證會員資訊
    ├── validate_recommendation_request() - 驗證推薦請求
    └── validate_product() - 驗證產品資訊
```

## 使用範例

### 基本使用
```python
from src.utils.validators import validate_member_info
from src.models.data_models import MemberInfo

# 建立會員資訊
member = MemberInfo(
    member_code="CU000001",
    phone="0937024682",
    total_consumption=17400.0,
    accumulated_bonus=500.0,
    recent_purchases=["30463", "31033"]
)

# 驗證
result = validate_member_info(member)

if result.is_valid:
    print("驗證通過")
else:
    print("驗證失敗:")
    for error in result.errors:
        print(f"  - {error['field']}: {error['message']}")
```

### 推薦請求驗證
```python
from src.utils.validators import validate_recommendation_request
from src.models.data_models import RecommendationRequest

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
```

## 錯誤訊息範例

### 會員編號錯誤
```json
{
  "field": "member_code",
  "message": "會員編號為必填欄位",
  "code": "required_field"
}
```

### 電話號碼錯誤
```json
{
  "field": "phone",
  "message": "電話號碼長度應在 8-12 位數之間",
  "code": "invalid_length"
}
```

### 消費金額錯誤
```json
{
  "field": "total_consumption",
  "message": "總消費金額不能超過 10,000,000",
  "code": "max_value_exceeded"
}
```

### 最近購買錯誤
```json
{
  "field": "recent_purchases",
  "message": "最近購買產品列表包含重複的產品 ID",
  "code": "duplicate_values"
}
```

## 驗證層級

### 第一層：Pydantic 驗證
- 類型檢查
- 基本格式驗證
- 必填欄位檢查

### 第二層：自定義驗證器
- 業務規則驗證
- 範圍檢查
- 複雜格式驗證
- 業務邏輯驗證

## 技術特點

1. **分層驗證**: Pydantic + 自定義驗證器
2. **明確錯誤**: 每個錯誤都有欄位、訊息和代碼
3. **可擴展**: 易於添加新的驗證規則
4. **業務邏輯**: 支援複雜的業務邏輯驗證
5. **友善訊息**: 錯誤訊息清晰易懂

## 測試結果

所有驗證規則測試通過：
- ✅ 會員編號驗證
- ✅ 電話號碼驗證
- ✅ 消費金額驗證
- ✅ 累積紅利驗證
- ✅ 最近購買驗證
- ✅ 推薦請求驗證
- ✅ 產品驗證
- ✅ 業務邏輯驗證

## 後續改進建議

1. **國際化**: 支援多語言錯誤訊息
2. **自定義規則**: 允許動態配置驗證規則
3. **批次驗證**: 支援批次驗證多個物件
4. **驗證快取**: 快取驗證結果以提升效能
5. **更多格式**: 支援更多電話號碼格式（國際號碼）

## 整合建議

### API 層整合
```python
from fastapi import HTTPException
from src.utils.validators import validate_recommendation_request

@app.post("/api/v1/recommendations")
async def get_recommendations(request: RecommendationRequest):
    # 驗證請求
    result = validate_recommendation_request(request)
    
    if not result.is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "validation_error",
                "message": "輸入資料驗證失敗",
                "errors": result.errors
            }
        )
    
    # 處理推薦請求
    ...
```

### 推薦引擎整合
```python
from src.utils.validators import validate_member_info

def recommend(self, member_info: MemberInfo):
    # 驗證會員資訊
    result = validate_member_info(member_info)
    
    if not result.is_valid:
        logger.error(f"會員資訊驗證失敗: {result}")
        raise ValueError(f"會員資訊驗證失敗: {result}")
    
    # 生成推薦
    ...
```

## 檔案清單

- `src/utils/__init__.py` - 工具模組初始化
- `src/utils/validators.py` - 驗證器實作
- `scripts/demo_validators.py` - 示範腳本
- `TASK14_SUMMARY.md` - 本總結文件

## 結論

任務 14 已成功完成。輸入驗證器已實作，能夠驗證會員資訊的必填欄位和格式，實作資料範圍檢查，並生成明確的驗證錯誤訊息，滿足需求 1.2、1.3 和 7.3 的所有要求。驗證器採用分層設計，結合 Pydantic 的類型驗證和自定義的業務邏輯驗證，提供全面的輸入驗證功能。
