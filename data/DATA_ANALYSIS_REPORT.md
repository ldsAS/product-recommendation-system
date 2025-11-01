# 資料分析報告

## 資料概覽

### 1. 會員資料 (member)
**檔案大小**: > 50MB (大型檔案)
**格式**: JSON Lines (每行一個 JSON 物件)

**主要欄位**:
- `id`: 會員唯一識別碼 (UUID)
- `member_code`: 會員編號 (如 CU000001)
- `member_name`: 會員姓名
- `phone`: 電話號碼
- `total_consumption`: 總消費金額
- `accumulated_bonus`: 累積紅利
- `residence_address_county/city/street`: 居住地址
- `create_time`, `modify_time`: 建立/修改時間
- `customer_type`: 客戶類型 (natural 等)
- `datastream_metadata`: 資料串流元資料

**資料特性**:
- 包含完整的會員個人資訊
- 有消費歷史統計 (total_consumption)
- 有地址資訊 (部分會員)
- 時間範圍: 2023年至今

### 2. 銷售訂單資料 (sales)
**格式**: JSON Lines

**主要欄位**:
- `id`: 訂單唯一識別碼 (UUID)
- `no`: 訂單編號 (如 PShealth000837, PSsaletele007147)
- `date`: 訂單日期時間
- `member`: 會員ID (外鍵，關聯到 member.id)
- `user_id`, `user_name`: 操作人員 (如 蔡亞彤)
- `quantity`: 商品數量
- `total`: 訂單總金額
- `discountTotal`: 折扣金額
- `actualTotal`: 實際金額
- `taxTotal`: 稅額
- `sale_type`: 銷售類型
- `loccode`: 地點代碼 (healthsale, saledepo 等)
- `notes`: 備註 (如 "20220421 中央藥局")

**資料特性**:
- 時間範圍: 2021年至2025年
- 包含多個銷售地點
- 有完整的金額和折扣資訊
- 關聯到會員資料

### 3. 銷售明細資料 (salesdetails)
**格式**: JSON Lines

**主要欄位**:
- `id`: 明細唯一識別碼 (UUID)
- `sales_id`: 訂單ID (外鍵，關聯到 sales.id)
- `stock_id`: 產品ID (如 31033, 30463)
- `stock_description`: 產品名稱/描述
- `quantity`: 購買數量
- `price`: 單價
- `subTotal`: 小計
- `saleCost`: 銷售成本
- `salePrice`: 銷售價格
- `discountRate`: 折扣率
- `balance`: 餘額
- `tax`: 稅額
- `is_free`: 是否免費
- `bonus_type`: 紅利類型

**常見產品** (從樣本中觀察):
- 蓉憶記小瓶 10顆裝 (stock_id: 30463) - 出現頻率最高
- 杏輝新活力錠 (stock_id: 31033)
- 杏輝蓉憶記膠囊 (stock_id: 30469)
- 杏輝南極磷蝦油軟膠囊 (stock_id: 31463)
- 杏輝活芯升級版軟膠囊10粒裝 (stock_id: 39120)

## 資料關聯結構

```
member (會員)
  ├─ id (主鍵)
  └─ member_code, member_name, phone, total_consumption
      │
      └─> sales (銷售訂單)
            ├─ id (主鍵)
            ├─ member (外鍵 → member.id)
            └─ no, date, total, actualTotal
                │
                └─> salesdetails (銷售明細)
                      ├─ id (主鍵)
                      ├─ sales_id (外鍵 → sales.id)
                      └─ stock_id, stock_description, quantity, price
```

## 推薦系統可用特徵

### 會員特徵
1. **人口統計特徵**:
   - 會員編號、姓名
   - 電話號碼
   - 居住地址 (縣市、區域)
   - 客戶類型

2. **消費行為特徵**:
   - 總消費金額 (total_consumption)
   - 累積紅利 (accumulated_bonus)
   - 會員註冊時間 (create_time)
   - 最後消費時間 (可從 sales 計算)

### 訂單特徵
1. **交易特徵**:
   - 訂單頻率
   - 平均訂單金額
   - 折扣使用情況
   - 購買時間模式 (日期、時段)
   - 購買地點 (loccode)

2. **產品特徵**:
   - 購買產品類別
   - 產品購買頻率
   - 產品組合模式
   - 產品價格區間偏好

### 可衍生特徵
1. **RFM 分析**:
   - Recency: 最近一次購買距今天數
   - Frequency: 購買頻率
   - Monetary: 消費金額

2. **產品偏好**:
   - 最常購買的產品類別
   - 產品多樣性 (購買不同產品的數量)
   - 品牌偏好

3. **時間模式**:
   - 購買週期
   - 季節性偏好
   - 購買時段偏好

## 推薦系統建議

### 模型選擇建議
1. **協同過濾 (Collaborative Filtering)**:
   - 基於用戶的協同過濾: 找出相似會員的購買模式
   - 基於物品的協同過濾: 找出相似產品的購買關聯

2. **內容基礎推薦 (Content-Based)**:
   - 基於會員過去購買的產品特徵推薦相似產品

3. **混合模型 (Hybrid)**:
   - 結合協同過濾和內容基礎的優點
   - 使用機器學習模型 (如 XGBoost, LightGBM) 預測購買機率

### 資料處理建議
1. **資料清理**:
   - 處理缺失值 (部分會員地址、電話可能為空)
   - 處理異常值 (如金額為 0 的訂單)
   - 統一編碼格式 (處理中文亂碼問題)

2. **特徵工程**:
   - 計算 RFM 指標
   - 建立產品類別標籤
   - 計算會員生命週期價值 (CLV)
   - 建立購買序列特徵

3. **資料分割**:
   - 訓練集: 2021-2024年資料
   - 驗證集: 2024年後期資料
   - 測試集: 2025年資料

### 評估指標建議
1. **準確性指標**:
   - Precision@5: Top 5 推薦中的準確率
   - Recall@5: Top 5 推薦的召回率
   - NDCG@5: 排序品質

2. **業務指標**:
   - 推薦轉換率
   - 推薦產品的平均訂單價值
   - 推薦接受率

## 需求文件調整建議

基於實際資料分析，建議調整以下需求:

1. **輸入欄位調整**:
   - 會員編號 (member_code)
   - 電話號碼 (phone)
   - 總消費金額 (total_consumption)
   - 累積紅利 (accumulated_bonus)
   - 最近購買時間 (從 sales 計算)
   - 購買頻率 (從 sales 計算)
   - 常購產品類別 (從 salesdetails 計算)

2. **產品資訊顯示**:
   - 產品ID (stock_id)
   - 產品名稱 (stock_description)
   - 推薦信心分數 (0-100%)
   - 推薦理由 (如"基於您購買過的蓉憶記系列產品")

3. **效能要求**:
   - 考慮到資料量較大 (member > 50MB)
   - 建議使用快取機制
   - 模型推論時間 < 3秒 是合理的

## 下一步行動

1. ✅ 資料已放置在 `data/raw/` 資料夾
2. ⏭️ 確認需求文件是否需要根據實際資料調整
3. ⏭️ 進入設計階段，規劃資料處理流程和模型架構
4. ⏭️ 建立實作計畫
