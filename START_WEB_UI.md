# 🎨 啟動 Web UI 指南

## 快速啟動

### 方式 1: 直接啟動（推薦）

```bash
python src/api/main.py
```

然後在瀏覽器中打開：
**http://localhost:8000**

### 方式 2: 使用 uvicorn

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

然後在瀏覽器中打開：
**http://localhost:8000**

---

## 📱 Web UI 功能

### 介面特色

- 🎯 **簡潔美觀**: 現代化的漸層設計
- 📝 **表單輸入**: 輸入會員資訊
- ⚡ **即時推薦**: 快速獲取推薦結果
- 📊 **結果展示**: 清晰的推薦列表和理由

### 使用步驟

1. **輸入會員資訊**
   - 會員編號（必填）
   - 電話號碼（選填）
   - 總消費金額（必填）
   - 累積紅利（必填）
   - 最近購買的產品 ID（選填，用逗號分隔）

2. **點擊「獲取推薦」按鈕**

3. **查看推薦結果**
   - Top 5 推薦產品
   - 信心分數
   - 推薦理由
   - 產品詳情

---

## 🔧 測試範例

### 範例 1: 基本測試

```
會員編號: CU000001
電話號碼: 0937024682
總消費金額: 17400
累積紅利: 500
最近購買: 30463, 31033
```

### 範例 2: 新會員

```
會員編號: CU000999
電話號碼: 0912345678
總消費金額: 5000
累積紅利: 100
最近購買: （留空）
```

---

## 📊 其他可用端點

### API 文檔（Swagger UI）
**http://localhost:8000/docs**

互動式 API 文檔，可以直接測試 API

### API 文檔（ReDoc）
**http://localhost:8000/redoc**

更適合閱讀的 API 文檔

### 健康檢查
**http://localhost:8000/health**

檢查服務狀態

### 應用資訊
**http://localhost:8000/info**

查看應用程式資訊

---

## 🎯 完整啟動流程

### 步驟 1: 確認模型已訓練

```bash
# 檢查模型文件是否存在
dir data\models\v1.0.0
```

應該看到：
- model.pkl
- member_features.parquet
- product_features.parquet
- metadata.json

### 步驟 2: 啟動服務

```bash
python src/api/main.py
```

你會看到類似的輸出：
```
============================================================
FastAPI 應用啟動中...
應用名稱: 產品推薦系統 API
版本: 1.0.0
環境: development
============================================================
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 步驟 3: 打開瀏覽器

訪問：**http://localhost:8000**

你會看到一個漂亮的紫色漸層介面！

---

## 🎨 Web UI 預覽

### 介面元素

1. **標題區域**
   - 🎯 產品推薦系統
   - 輸入會員資訊，獲取個性化產品推薦

2. **輸入表單**
   - 會員編號輸入框
   - 電話號碼輸入框
   - 總消費金額輸入框
   - 累積紅利輸入框
   - 最近購買產品輸入框
   - 「獲取推薦」按鈕

3. **載入動畫**
   - 旋轉的載入圖示
   - "正在生成推薦..." 文字

4. **推薦結果**
   - 推薦排名標籤
   - 產品名稱
   - 信心分數（綠色標籤）
   - 推薦理由
   - 產品 ID 和來源

---

## 🔍 故障排查

### 問題 1: 無法訪問 http://localhost:8000

**檢查**:
```bash
# 確認服務是否啟動
netstat -an | findstr 8000
```

**解決**:
- 確認沒有其他程式占用 8000 端口
- 嘗試使用其他端口：`uvicorn src.api.main:app --port 8001`

### 問題 2: 推薦失敗

**可能原因**:
- 模型未訓練
- 會員編號不存在於訓練資料中

**解決**:
- 檢查 `data/models/v1.0.0/` 是否有模型文件
- 使用訓練資料中存在的會員編號

### 問題 3: 頁面顯示不正常

**解決**:
- 清除瀏覽器快取
- 使用無痕模式
- 檢查瀏覽器控制台是否有錯誤

---

## 💡 進階使用

### 開發模式（自動重載）

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

修改代碼後會自動重啟服務

### 生產模式（多 worker）

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

使用 4 個 worker 處理請求

### 自定義端口

```bash
python src/api/main.py
# 或
uvicorn src.api.main:app --port 8080
```

---

## 📸 截圖說明

### 主介面
- 紫色漸層背景
- 白色卡片式表單
- 現代化的輸入框設計

### 推薦結果
- 卡片式結果展示
- 每個推薦有獨立的區塊
- 清晰的排名和分數顯示
- 詳細的推薦理由

---

## 🎉 開始使用

現在就執行以下命令啟動 Web UI：

```bash
python src/api/main.py
```

然後在瀏覽器中打開 **http://localhost:8000** 開始體驗！
