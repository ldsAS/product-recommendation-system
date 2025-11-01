# 顧客產品推薦系統

基於機器學習的智能產品推薦系統，為銷售員提供 Top 5 產品推薦。

## 專案概述

本系統分析會員資料、銷售訂單和產品明細，訓練推薦模型，並提供 API 介面讓銷售員輸入顧客資訊後快速獲得個人化的產品推薦。

### 主要功能

- 🎯 **智能推薦**: 基於機器學習模型預測顧客購買偏好
- ⚡ **快速回應**: 3 秒內返回 Top 5 推薦結果
- 📊 **可解釋性**: 為每個推薦提供清晰的理由說明
- 🔄 **持續優化**: 支援模型版本管理和 A/B 測試
- 📈 **效能監控**: 追蹤推薦準確率和轉換率

## 快速開始

### 前置需求

- Python 3.9 或更高版本
- pip 套件管理器

### 安裝步驟

1. **克隆專案** (如果使用 Git):
```bash
git clone <repository-url>
cd customer-product-recommendation
```

2. **建立虛擬環境** (建議):
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安裝依賴套件**:
```bash
pip install -r requirements.txt
```

4. **配置環境變數**:
```bash
cp .env.example .env
# 編輯 .env 檔案，填入實際配置
```

5. **準備資料**:
將資料檔案放在 `data/raw/` 目錄：
- member
- sales
- salesdetails

### 訓練模型

```bash
python src/train.py
```

### 啟動 API 服務

```bash
python src/api/main.py
```

或使用 uvicorn：
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 測試推薦

使用 curl 測試 API：
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

或使用命令列工具：
```bash
python src/cli/recommend_cli.py
```

## 專案結構

```
.
├── .kiro/
│   └── specs/                     # 專案規格文件
│       └── customer-product-recommendation/
│           ├── requirements.md    # 需求文件
│           ├── design.md          # 設計文件
│           └── tasks.md           # 任務清單
├── data/
│   ├── raw/                       # 原始資料
│   ├── processed/                 # 處理後資料
│   └── models/                    # 訓練好的模型
├── src/
│   ├── data_processing/           # 資料處理模組
│   │   ├── data_loader.py
│   │   ├── data_cleaner.py
│   │   ├── feature_engineer.py
│   │   └── data_validator.py
│   ├── models/                    # 模型相關
│   │   ├── data_models.py
│   │   ├── collaborative_filtering.py
│   │   ├── ml_recommender.py
│   │   ├── recommendation_engine.py
│   │   ├── model_evaluator.py
│   │   ├── model_manager.py
│   │   └── ab_test_manager.py
│   ├── api/                       # API 服務
│   │   ├── main.py
│   │   ├── routes/
│   │   └── error_handlers.py
│   ├── utils/                     # 工具函數
│   │   ├── logger.py
│   │   ├── validators.py
│   │   └── metrics.py
│   ├── cli/                       # 命令列工具
│   │   └── recommend_cli.py
│   ├── web/                       # Web UI
│   ├── config.py                  # 配置管理
│   └── train.py                   # 訓練入口
├── tests/                         # 測試檔案
├── docs/                          # 文件
├── logs/                          # 日誌
├── scripts/                       # 腳本工具
├── requirements.txt               # Python 依賴
├── .env.example                   # 環境變數範本
└── README.md                      # 本檔案
```

## API 文件

啟動服務後，訪問以下 URL 查看自動生成的 API 文件：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要端點

- `POST /api/v1/recommendations` - 獲取產品推薦
- `GET /api/v1/model/info` - 查看模型資訊
- `GET /api/v1/health` - 健康檢查

## 開發指南

### 執行測試

```bash
# 執行所有測試
pytest

# 執行特定測試檔案
pytest tests/test_data_loader.py

# 查看測試覆蓋率
pytest --cov=src tests/
```

### 程式碼格式化

```bash
# 格式化程式碼
black src/ tests/

# 檢查程式碼風格
flake8 src/ tests/

# 類型檢查
mypy src/
```

### 資料探索

使用 Jupyter Notebook 進行資料探索：
```bash
jupyter notebook
```

## 配置說明

主要配置參數在 `src/config.py` 中定義，可透過環境變數覆蓋。

### 重要配置

- `MODEL_VERSION`: 模型版本
- `MODEL_TYPE`: 模型類型 (lightgbm, xgboost, collaborative_filtering)
- `TOP_K_RECOMMENDATIONS`: 推薦產品數量 (預設 5)
- `MAX_RESPONSE_TIME_SECONDS`: 最大回應時間 (預設 3 秒)
- `ENABLE_CACHE`: 是否啟用快取
- `LOG_LEVEL`: 日誌級別 (DEBUG, INFO, WARNING, ERROR)

## 效能指標

- ✅ API 回應時間: < 3 秒
- ✅ 模型準確率: ≥ 70%
- ✅ Precision@5: ≥ 0.70
- ✅ 推薦品質: 可解釋且相關

## 技術棧

- **程式語言**: Python 3.9+
- **Web 框架**: FastAPI
- **機器學習**: LightGBM, XGBoost, scikit-learn
- **資料處理**: pandas, numpy
- **快取**: Redis (可選)
- **測試**: pytest
- **部署**: Docker (可選)

## 疑難排解

### 常見問題

1. **模型檔案找不到**
   - 確保已執行 `python src/train.py` 訓練模型
   - 檢查 `data/models/` 目錄是否存在模型檔案

2. **API 回應時間過長**
   - 啟用快取: 設定 `ENABLE_CACHE=true`
   - 檢查模型大小和複雜度
   - 考慮使用更快的模型或特徵預計算

3. **記憶體不足**
   - 使用分批處理載入大型資料檔案
   - 減少特徵數量或使用特徵選擇
   - 增加系統記憶體

## 貢獻指南

歡迎貢獻！請遵循以下步驟：

1. Fork 專案
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 授權

[請在此處添加授權資訊]

## 聯絡資訊

如有問題或建議，請聯絡：
- 專案負責人: [姓名]
- Email: [email]

## 致謝

感謝所有貢獻者和支持者！

---

**祝使用愉快！** 🚀
