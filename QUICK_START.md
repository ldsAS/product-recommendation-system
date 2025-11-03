# 🚀 快速啟動指南

本指南適用於從 GitHub clone 後的快速設置。

---

## ✅ 環境檢查 (已完成)

你的環境已通過完整檢查：
- ✓ Python 3.11.9
- ✓ 所有依賴已安裝
- ✓ 資料檔案已就緒
- ✓ 所有模組正常運作

詳細報告請查看: [SYSTEM_CHECK_REPORT.md](SYSTEM_CHECK_REPORT.md)

---

## 🎯 立即開始 (3 步驟)

### 步驟 1: 訓練模型

```bash
# 完整訓練 (推薦)
python src/train.py

# 或快速測試 (使用部分資料)
python src/train.py --max-rows 1000
```

**預期時間**: 5-15 分鐘 (取決於資料量)

**輸出檔案**:
- `data/models/v1.0.0/model.pkl` - 訓練好的模型
- `data/models/v1.0.0/member_features.parquet` - 會員特徵
- `data/models/v1.0.0/product_features.parquet` - 產品特徵
- `data/models/v1.0.0/metadata.json` - 模型元資料

### 步驟 2: 啟動 API 服務

```bash
python src/api/main.py
```

服務將在 http://localhost:8000 啟動

### 步驟 3: 測試推薦功能

**方式 1: 使用 Swagger UI**
- 訪問: http://localhost:8000/docs
- 找到 `/api/v1/recommendations` 端點
- 點擊 "Try it out"
- 輸入測試資料並執行

**方式 2: 使用測試腳本**
```bash
python scripts/test_api.py
```

**方式 3: 使用 curl**
```bash
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "member_code": "CU000001",
    "phone": "0937024682",
    "total_consumption": 17400,
    "accumulated_bonus": 500,
    "recent_purchases": ["30463", "31033"]
  }'
```

---

## 📊 驗證系統

### 檢查模型資訊

```bash
# 訪問模型資訊 API
curl http://localhost:8000/api/v1/model/info
```

### 健康檢查

```bash
# 檢查服務健康狀態
curl http://localhost:8000/api/v1/health
```

### 執行測試

```bash
# 執行所有測試
pytest tests/ -v

# 執行特定測試
pytest tests/test_recommendation_engine.py -v
```

---

## 🔧 常用命令

### 開發模式

```bash
# 啟動開發服務器 (自動重載)
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 查看日誌

```bash
# Windows
type logs\app.log

# Linux/Mac
tail -f logs/app.log
```

### 重新訓練模型

```bash
# 使用不同模型類型
python src/train.py --model-type xgboost

# 指定版本
python src/train.py --model-version v1.1.0
```

---

## 📚 相關文檔

- [README.md](README.md) - 完整專案說明
- [INSTALL.md](INSTALL.md) - 詳細安裝指南
- [SYSTEM_CHECK_REPORT.md](SYSTEM_CHECK_REPORT.md) - 系統檢查報告
- [docs/IMPLICIT_MIGRATION.md](docs/IMPLICIT_MIGRATION.md) - 協同過濾遷移說明
- [CHANGELOG.md](CHANGELOG.md) - 更新日誌

---

## ⚡ 效能優化建議

### 1. 設置環境變數

在 `.env` 文件中添加：

```env
# 優化 OpenBLAS 性能
OPENBLAS_NUM_THREADS=1

# 啟用快取
ENABLE_CACHE=true
```

### 2. 使用生產模式

```bash
# 使用 gunicorn (需要安裝)
pip install gunicorn
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## 🐛 問題排查

### 問題 1: 訓練失敗

**檢查**:
- 資料檔案是否存在於 `data/raw/`
- 查看 `logs/training.log` 錯誤訊息

### 問題 2: API 無法啟動

**檢查**:
- 模型是否已訓練
- 端口 8000 是否被占用
- 查看終端錯誤訊息

### 問題 3: 推薦結果為空

**檢查**:
- 會員 ID 是否存在於訓練資料中
- 產品特徵是否正確載入
- 查看 API 日誌

---

## 💡 提示

1. **首次使用**: 建議先用 `--max-rows 1000` 快速測試
2. **開發階段**: 使用 `--reload` 模式啟動 API
3. **生產環境**: 使用 gunicorn 或 uvicorn workers
4. **監控**: 定期查看 `logs/` 目錄中的日誌

---

**準備好了嗎？開始第一步吧！** 🎉

```bash
python src/train.py
```
