# 🔧 Web UI 故障排查指南

## 問題：推薦生成失敗

### 原因分析

推薦生成失敗通常有以下原因：

1. **虛擬環境未啟動** ⭐ 最常見
2. 模型未訓練
3. 會員編號不存在
4. 依賴套件未安裝

---

## ✅ 解決方案

### 方案 1: 使用正確的啟動方式（推薦）

**使用更新後的啟動腳本**:

雙擊執行：
```
start_web_ui.bat
```

這個腳本會自動使用虛擬環境啟動服務。

### 方案 2: 手動啟動（確保使用虛擬環境）

#### Windows PowerShell:

```powershell
# 1. 啟動虛擬環境
.\venv\Scripts\Activate.ps1

# 2. 啟動服務
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

#### Windows CMD:

```cmd
# 1. 啟動虛擬環境
.\venv\Scripts\activate.bat

# 2. 啟動服務
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

#### 或直接使用虛擬環境的 uvicorn:

```cmd
.\venv\Scripts\uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

---

## 🔍 診斷步驟

### 步驟 1: 檢查系統狀態

運行診斷腳本：

```cmd
.\venv\Scripts\python diagnose_recommendation_error.py
```

**預期輸出**:
```
✓ 訓練好的模型: model.pkl
✓ 會員特徵: member_features.parquet
✓ 產品特徵: product_features.parquet
✓ 模型元資料: metadata.json
✓ 推薦引擎初始化成功
✓ 推薦生成成功: 5 個推薦
```

### 步驟 2: 確認虛擬環境

檢查是否在虛擬環境中：

```powershell
# PowerShell
Get-Command python | Select-Object Source

# 應該顯示類似:
# ...\venv\Scripts\python.exe
```

### 步驟 3: 測試 API 端點

服務啟動後，測試健康檢查：

```powershell
# 使用 curl (PowerShell)
Invoke-WebRequest http://localhost:8000/health

# 或使用瀏覽器訪問
# http://localhost:8000/health
```

**預期回應**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "uptime_seconds": 123.45
}
```

---

## 🐛 常見錯誤及解決方案

### 錯誤 1: ModuleNotFoundError: No module named 'pandas'

**原因**: 未使用虛擬環境或虛擬環境中缺少依賴

**解決**:
```cmd
# 確保在虛擬環境中安裝依賴
.\venv\Scripts\pip install -r requirements.txt

# 使用虛擬環境啟動
.\venv\Scripts\uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### 錯誤 2: FileNotFoundError: Model file not found

**原因**: 模型未訓練

**解決**:
```cmd
# 訓練模型
.\venv\Scripts\python src/train.py
```

### 錯誤 3: 推薦結果為空

**原因**: 會員編號不在訓練資料中

**解決**: 使用訓練資料中存在的會員編號

**測試會員編號**:
- CU000001
- CU000002
- CU000003

### 錯誤 4: 端口被占用

**錯誤訊息**: `[Errno 10048] error while attempting to bind on address`

**解決**:
```cmd
# 使用其他端口
.\venv\Scripts\uvicorn src.api.main:app --port 8001

# 或找出占用端口的程式
netstat -ano | findstr :8000
```

---

## 📋 完整啟動檢查清單

在啟動 Web UI 前，確認以下項目：

- [ ] 虛擬環境已創建 (`venv` 目錄存在)
- [ ] 依賴已安裝 (`.\venv\Scripts\pip list` 顯示所有套件)
- [ ] 模型已訓練 (`data/models/v1.0.0/model.pkl` 存在)
- [ ] 使用虛擬環境啟動服務
- [ ] 端口 8000 未被占用

---

## 🎯 快速修復命令

如果遇到問題，依序執行以下命令：

```cmd
# 1. 重新安裝依賴
.\venv\Scripts\pip install -r requirements.txt

# 2. 檢查模型
dir data\models\v1.0.0

# 3. 如果模型不存在，訓練模型
.\venv\Scripts\python src/train.py --max-rows 5000

# 4. 運行診斷
.\venv\Scripts\python diagnose_recommendation_error.py

# 5. 啟動服務
.\venv\Scripts\uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

---

## 💡 測試推薦

服務啟動後，使用以下測試資料：

### 測試資料 1（推薦）:

```json
{
  "member_code": "CU000001",
  "phone": "0937024682",
  "total_consumption": 17400,
  "accumulated_bonus": 500,
  "recent_purchases": []
}
```

### 測試資料 2:

```json
{
  "member_code": "CU000002",
  "phone": "0912345678",
  "total_consumption": 25000,
  "accumulated_bonus": 800,
  "recent_purchases": []
}
```

---

## 🔗 相關資源

- **診斷腳本**: `diagnose_recommendation_error.py`
- **啟動腳本**: `start_web_ui.bat`
- **完整指南**: `WEB_UI_GUIDE.md`
- **快速啟動**: `QUICK_START.md`

---

## 📞 仍然有問題？

如果以上方法都無法解決問題：

1. 查看服務日誌中的錯誤訊息
2. 檢查 `logs/` 目錄中的日誌文件
3. 在瀏覽器中按 F12 查看控制台錯誤
4. 提供錯誤訊息以獲得更多幫助

---

**記住**: 始終使用虛擬環境啟動服務！✨
