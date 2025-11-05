# 🎨 Web UI 使用指南

## 🚀 快速啟動

### 方法 1: 使用啟動腳本（最簡單）

雙擊執行：
```
start_web_ui.bat
```

### 方法 2: 使用命令列

打開命令提示字元（cmd）或 PowerShell，執行：

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### 方法 3: 使用 Python

```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

---

## 📱 訪問 Web UI

啟動成功後，你會看到類似的輸出：

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

然後在瀏覽器中打開以下任一網址：

- **http://localhost:8000** （推薦）
- **http://127.0.0.1:8000**
- **http://0.0.0.0:8000**

---

## 🎯 使用 Web UI

### 介面說明

你會看到一個漂亮的紫色漸層介面，包含：

1. **標題區域**
   - 🎯 產品推薦系統
   - 副標題：輸入會員資訊，獲取個性化產品推薦

2. **輸入表單**（白色卡片）
   - 會員編號 * （必填）
   - 電話號碼（選填）
   - 總消費金額 * （必填）
   - 累積紅利 * （必填）
   - 最近購買的產品 ID（選填）
   - 「獲取推薦」按鈕

3. **推薦結果區域**
   - 顯示 Top 5 推薦產品
   - 每個推薦包含：
     - 推薦排名
     - 產品名稱
     - 信心分數
     - 推薦理由
     - 產品 ID

### 測試範例

#### 範例 1: 使用訓練資料中的會員

```
會員編號: CU000001
電話號碼: 0937024682
總消費金額: 17400
累積紅利: 500
最近購買: 30463, 31033
```

#### 範例 2: 新會員（可能沒有推薦）

```
會員編號: CU999999
電話號碼: 0912345678
總消費金額: 5000
累積紅利: 100
最近購買: （留空）
```

### 操作步驟

1. **填寫表單**
   - 在各個輸入框中填入會員資訊
   - 必填欄位標有 * 號

2. **提交請求**
   - 點擊「獲取推薦」按鈕
   - 會顯示載入動畫

3. **查看結果**
   - 推薦結果會顯示在下方
   - 包含詳細的推薦理由和分數

---

## 🔗 其他可用頁面

### 1. API 文檔（Swagger UI）

**網址**: http://localhost:8000/docs

**功能**:
- 互動式 API 文檔
- 可以直接測試 API
- 查看所有端點和參數

### 2. API 文檔（ReDoc）

**網址**: http://localhost:8000/redoc

**功能**:
- 更適合閱讀的 API 文檔
- 清晰的結構展示

### 3. 健康檢查

**網址**: http://localhost:8000/health

**返回**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "uptime_seconds": 123.45,
  "timestamp": "2025-11-03T15:30:00"
}
```

### 4. 應用資訊

**網址**: http://localhost:8000/info

**返回**:
```json
{
  "app_name": "產品推薦系統 API",
  "version": "1.0.0",
  "environment": "development",
  "uptime_seconds": 123.45,
  "model_version": "v1.0.0"
}
```

---

## 🛠️ 進階選項

### 開發模式（自動重載）

當你修改代碼時自動重啟服務：

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 使用不同端口

如果 8000 端口被占用：

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8080
```

然後訪問 http://localhost:8080

### 只允許本地訪問

```bash
uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

---

## 🐛 故障排查

### 問題 1: 無法啟動服務

**錯誤**: `ModuleNotFoundError: No module named 'fastapi'`

**解決**:
```bash
pip install fastapi uvicorn jinja2
```

### 問題 2: 端口被占用

**錯誤**: `[Errno 10048] error while attempting to bind on address`

**解決**:
```bash
# 使用其他端口
uvicorn src.api.main:app --port 8001

# 或找出占用端口的程式
netstat -ano | findstr :8000
```

### 問題 3: 無法訪問頁面

**檢查**:
1. 確認服務已啟動
2. 檢查防火牆設置
3. 嘗試使用 127.0.0.1 而不是 localhost

### 問題 4: 推薦失敗

**可能原因**:
- 模型未訓練
- 會員編號不存在

**解決**:
1. 檢查模型文件：
   ```bash
   dir data\models\v1.0.0
   ```

2. 使用訓練資料中存在的會員編號

3. 查看服務日誌中的錯誤訊息

---

## 📸 介面預覽

### 主介面特色

- **背景**: 紫色漸層（#667eea → #764ba2）
- **卡片**: 白色圓角卡片，陰影效果
- **按鈕**: 漸層紫色，懸停時有動畫
- **輸入框**: 聚焦時藍色邊框
- **結果**: 卡片式展示，左側藍色邊框

### 響應式設計

- 自動適應不同螢幕尺寸
- 手機、平板、電腦都能正常使用

---

## 💡 使用技巧

### 1. 快速測試

使用瀏覽器的「記住表單」功能，避免重複輸入

### 2. 批量測試

打開多個瀏覽器分頁，測試不同會員

### 3. 查看網路請求

按 F12 打開開發者工具，查看 Network 標籤，可以看到：
- 請求內容
- 回應時間
- 返回的 JSON 資料

### 4. 複製推薦結果

推薦結果可以直接選取複製，方便分享

---

## 🔒 安全提示

### 開發環境

當前配置適合開發和測試，不建議直接用於生產環境。

### 生產環境

如需部署到生產環境，請：

1. 修改 `.env` 文件：
   ```
   ENVIRONMENT=production
   DEBUG=false
   ```

2. 使用 HTTPS
3. 配置防火牆
4. 設置 API 認證
5. 限制 CORS 來源

---

## 📞 需要協助？

如果遇到問題：

1. 查看服務日誌中的錯誤訊息
2. 檢查 `logs/` 目錄中的日誌文件
3. 參考 README.md 中的疑難排解章節
4. 提交 GitHub Issue

---

## 🎉 開始使用

現在就執行以下命令啟動 Web UI：

```bash
# 方式 1: 雙擊
start_web_ui.bat

# 方式 2: 命令列
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

然後在瀏覽器中打開：
**http://localhost:8000**

享受使用！🚀
