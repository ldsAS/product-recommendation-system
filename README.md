# 🛍️ 顧客產品推薦系統

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

基於機器學習的智能產品推薦系統，為銷售團隊提供精準的個人化產品推薦，提升銷售轉換率。

## 📋 專案概述

本系統整合會員資料、歷史銷售訂單和產品資訊，運用機器學習演算法訓練推薦模型，透過 RESTful API 提供即時的個人化產品推薦服務。銷售人員只需輸入顧客基本資訊，即可在 3 秒內獲得 Top 5 推薦產品及推薦理由。

### ✨ 核心特色

- 🎯 **智能推薦引擎**: 結合協同過濾與機器學習模型，精準預測顧客購買偏好
- ⚡ **高效能回應**: 保證 3 秒內返回推薦結果，支援高併發請求
- 📊 **可解釋性**: 每個推薦都附帶清晰的理由說明，增強銷售說服力
- 🔄 **模型管理**: 支援多版本模型管理、A/B 測試和自動化評估
- 📈 **效能監控**: 即時追蹤推薦準確率、點擊率和轉換率等關鍵指標
- 🔒 **資料驗證**: 完整的輸入驗證和錯誤處理機制

## 🚀 快速開始

### 🐳 方式 1: Docker 一鍵部署（推薦）

最簡單的部署方式！只需 3 個步驟：

```bash
# 1. 複製環境變數文件
cp .env.example .env

# 2. 編輯 .env 設置密碼（至少設置 DB_PASSWORD 和 REDIS_PASSWORD）
# Windows: notepad .env
# Linux/Mac: nano .env

# 3. 一鍵啟動
# Windows:
quick-start.bat

# Linux/Mac:
chmod +x quick-start.sh
./quick-start.sh
```

**啟動後訪問**:
- 主頁面: http://localhost:8000
- API 文檔: http://localhost:8000/docs
- 監控儀表板: http://localhost:8000/dashboard

📖 **詳細說明**: 查看 [Docker 快速開始指南](README_DOCKER.md)

---

### 💻 方式 2: 本地安裝

#### 系統需求

- Python 3.9 或更高版本
- 4GB+ RAM（建議 8GB）
- pip 或 conda 套件管理器

#### 安裝步驟

#### 1. 克隆專案

```bash
git clone https://github.com/ldsAS/product-recommendation-system.git
cd product-recommendation-system
```

#### 2. 建立虛擬環境（強烈建議）

```bash
# 使用 venv
python -m venv venv

# 啟動虛擬環境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

#### 3. 安裝依賴套件

```bash
pip install -r requirements.txt
```

#### 4. 配置環境變數

```bash
# 複製環境變數範本
cp .env.example .env

# 編輯 .env 檔案，根據需求調整配置
# 主要配置項：
# - MODEL_VERSION: 模型版本
# - LOG_LEVEL: 日誌級別
# - ENABLE_CACHE: 是否啟用快取
```

#### 5. 準備訓練資料

將以下資料檔案放入 `data/raw/` 目錄：
- `member` - 會員資料
- `sales` - 銷售訂單
- `salesdetails` - 訂單明細

> **注意**: 資料檔案不包含在 Git 倉庫中，請確保您有權限存取這些資料。

### 使用指南

#### 訓練推薦模型

```bash
# 執行完整訓練流程（資料處理 + 模型訓練 + 評估）
python src/train.py

# 訓練完成後，模型會儲存在 data/models/ 目錄
```

#### 啟動 API 服務

```bash
# 方式 1: 直接執行
python src/api/main.py

# 方式 2: 使用 uvicorn（推薦用於生產環境）
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# 開發模式（自動重載）
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

服務啟動後，訪問 http://localhost:8000/docs 查看 API 文件。

#### 測試推薦功能

**方式 1: 使用 curl**

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

**方式 2: 使用命令列工具（互動式）**

```bash
python src/cli/recommend_cli.py
```

**方式 3: 使用測試腳本**

```bash
python scripts/test_api.py
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
├── config/                        # 配置文件
│   ├── recommendation_config.yaml # 推薦系統配置
│   └── production.yaml            # 生產環境配置
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
│   ├── deploy.sh                  # 部署腳本
│   └── init_db.sql                # 資料庫初始化
├── docker-compose.yml             # Docker Compose 配置
├── Dockerfile                     # Docker 映像配置
├── quick-start.bat                # Windows 一鍵啟動
├── quick-start.sh                 # Linux/Mac 一鍵啟動
├── README_DOCKER.md               # Docker 快速指南
├── DOCKER_QUICK_START.md          # Docker 詳細指南
├── requirements.txt               # Python 依賴
├── .env.example                   # 環境變數範本
└── README.md                      # 本檔案
```

## 📚 API 文件

啟動服務後，可透過以下 URL 查看完整的互動式 API 文件：

- **Swagger UI**: http://localhost:8000/docs （推薦，可直接測試）
- **ReDoc**: http://localhost:8000/redoc （更適合閱讀）

### 主要 API 端點

| 方法 | 端點 | 說明 | 回應時間 |
|------|------|------|----------|
| `POST` | `/api/v1/recommendations` | 獲取個人化產品推薦 | < 3s |
| `GET` | `/api/v1/model/info` | 查看當前模型資訊和版本 | < 100ms |
| `GET` | `/api/v1/health` | 健康檢查端點 | < 50ms |

### 請求範例

```json
{
  "member_code": "CU000001",
  "phone": "0937024682",
  "total_consumption": 17400,
  "accumulated_bonus": 500,
  "recent_purchases": ["30463", "31033"]
}
```

### 回應範例

```json
{
  "recommendations": [
    {
      "product_id": "30463",
      "product_name": "產品名稱",
      "score": 0.85,
      "reason": "基於您的購買歷史和偏好"
    }
  ],
  "model_version": "v1.0.0",
  "response_time_ms": 1250
}
```

## 🔧 開發指南

### 執行測試

```bash
# 執行所有測試
pytest

# 執行特定測試檔案
pytest tests/test_data_loader.py -v

# 查看測試覆蓋率
pytest --cov=src --cov-report=html tests/

# 執行整合測試
pytest tests/test_integration.py

# 執行效能測試
pytest tests/test_performance.py
```

### 程式碼品質

```bash
# 格式化程式碼（使用 black）
black src/ tests/

# 檢查程式碼風格（使用 flake8）
flake8 src/ tests/ --max-line-length=100

# 類型檢查（使用 mypy）
mypy src/ --ignore-missing-imports

# 排序 import（使用 isort）
isort src/ tests/
```

### 資料探索與分析

```bash
# 啟動 Jupyter Notebook
jupyter notebook

# 執行資料分析腳本
python scripts/analyze_data.py

# 驗證資料品質
python scripts/verify_models.py
```

### 除錯與日誌

日誌檔案位於 `logs/` 目錄，可透過環境變數 `LOG_LEVEL` 調整日誌級別：

```bash
# 設定為 DEBUG 模式以獲得詳細日誌
export LOG_LEVEL=DEBUG
python src/api/main.py
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

## 📊 效能指標

系統設計目標與實際表現：

| 指標 | 目標值 | 說明 |
|------|--------|------|
| API 回應時間 | < 3 秒 | 從請求到返回推薦結果的時間 |
| 模型準確率 | ≥ 70% | 推薦產品的整體準確率 |
| Precision@5 | ≥ 0.70 | Top 5 推薦的精確度 |
| 系統可用性 | ≥ 99% | 服務正常運行時間比例 |
| 併發處理 | 100+ req/s | 支援的同時請求數量 |

## 🛠️ 技術架構

### 核心技術棧

| 類別 | 技術 | 用途 |
|------|------|------|
| **程式語言** | Python 3.9+ | 主要開發語言 |
| **Web 框架** | FastAPI | RESTful API 服務 |
| **機器學習** | LightGBM, XGBoost | 推薦模型訓練 |
| **協同過濾** | scikit-learn | 基於相似度的推薦 |
| **資料處理** | pandas, numpy | 資料清洗與特徵工程 |
| **API 文件** | Swagger/OpenAPI | 自動生成 API 文件 |
| **測試框架** | pytest | 單元測試與整合測試 |
| **日誌管理** | Python logging | 結構化日誌記錄 |
| **快取** | Redis (可選) | 提升回應速度 |
| **容器化** | Docker (可選) | 簡化部署流程 |

### 系統架構

#### 本地部署架構
```
┌─────────────┐
│   銷售員    │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────────────────────┐
│      FastAPI Server         │
│  ┌─────────────────────┐   │
│  │  Recommendation API │   │
│  └──────────┬──────────┘   │
│             │               │
│  ┌──────────▼──────────┐   │
│  │ Recommendation      │   │
│  │ Engine              │   │
│  │ ┌─────────────────┐ │   │
│  │ │ ML Model        │ │   │
│  │ │ (LightGBM/XGB)  │ │   │
│  │ └─────────────────┘ │   │
│  │ ┌─────────────────┐ │   │
│  │ │ Collaborative   │ │   │
│  │ │ Filtering       │ │   │
│  │ └─────────────────┘ │   │
│  └─────────────────────┘   │
└─────────────────────────────┘
       │
       ▼
┌─────────────────┐
│  Model Files    │
│  (data/models/) │
└─────────────────┘
```

#### Docker 部署架構
```
┌─────────────────────────────────────────────────────────────┐
│                         Nginx (反向代理)                      │
│                      Port 80/443 (HTTPS)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                  推薦系統 API (FastAPI)                       │
│                      Port 8000                               │
│  - Web UI                                                    │
│  - REST API                                                  │
│  - 監控儀表板                                                 │
└─────────┬────────────────────────────────┬──────────────────┘
          │                                │
┌─────────┴─────────┐          ┌──────────┴──────────┐
│   PostgreSQL      │          │      Redis          │
│   Port 5432       │          │    Port 6379        │
│  - 監控記錄        │          │   - 快取            │
│  - 告警記錄        │          │   - 會話            │
└───────────────────┘          └─────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      監控系統                                 │
│  - Prometheus (Port 9090)                                   │
│  - Grafana (Port 3000)                                      │
└─────────────────────────────────────────────────────────────┘
```

## ❓ 疑難排解

### 常見問題與解決方案

#### 1. 模型檔案找不到

**錯誤訊息**: `FileNotFoundError: Model file not found`

**解決方法**:
```bash
# 確認是否已訓練模型
python src/train.py

# 檢查模型檔案是否存在
ls -la data/models/

# 驗證模型完整性
python scripts/verify_models.py
```

#### 2. API 回應時間過長

**症狀**: 推薦請求超過 3 秒

**解決方法**:
- 啟用快取: 在 `.env` 中設定 `ENABLE_CACHE=true`
- 檢查模型大小: 考慮使用更輕量的模型
- 特徵預計算: 將常用特徵預先計算並快取
- 增加硬體資源: 升級 CPU 或增加記憶體

#### 3. 記憶體不足

**錯誤訊息**: `MemoryError` 或系統變慢

**解決方法**:
```python
# 在 src/config.py 中調整批次大小
BATCH_SIZE = 1000  # 減少批次大小

# 使用資料分塊載入
# 在 data_loader.py 中使用 chunksize 參數
df = pd.read_csv('data.csv', chunksize=10000)
```

#### 4. 資料格式錯誤

**錯誤訊息**: `ValidationError` 或資料驗證失敗

**解決方法**:
```bash
# 檢查資料格式
python scripts/demo_validators.py

# 查看資料分析報告
cat data/DATA_ANALYSIS_REPORT.md
```

#### 5. 模型準確率低

**症狀**: Precision@5 < 0.70

**解決方法**:
- 檢查訓練資料品質和數量
- 調整模型超參數
- 增加特徵工程
- 使用 A/B 測試比較不同模型

### 取得協助

如果問題仍未解決，請：
1. 查看 `logs/` 目錄中的詳細日誌
2. 檢查 [Issues](https://github.com/ldsAS/product-recommendation-system/issues) 是否有類似問題
3. 提交新的 Issue 並附上錯誤訊息和日誌

## 🤝 貢獻指南

我們歡迎各種形式的貢獻！無論是回報 bug、提出新功能建議，或是提交程式碼改進。

### 貢獻流程

1. **Fork 專案**
   ```bash
   # 點擊 GitHub 頁面右上角的 Fork 按鈕
   ```

2. **克隆您的 Fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/product-recommendation-system.git
   cd product-recommendation-system
   ```

3. **建立功能分支**
   ```bash
   git checkout -b feature/amazing-feature
   # 或
   git checkout -b fix/bug-description
   ```

4. **進行開發**
   - 撰寫程式碼
   - 新增測試
   - 更新文件

5. **執行測試**
   ```bash
   pytest
   black src/ tests/
   flake8 src/ tests/
   ```

6. **提交變更**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   # 使用語義化提交訊息：feat, fix, docs, style, refactor, test, chore
   ```

7. **推送到您的 Fork**
   ```bash
   git push origin feature/amazing-feature
   ```

8. **開啟 Pull Request**
   - 前往原始專案頁面
   - 點擊 "New Pull Request"
   - 填寫 PR 描述，說明變更內容

### 程式碼規範

- 遵循 PEP 8 風格指南
- 使用 Black 格式化程式碼
- 為新功能撰寫測試
- 更新相關文件
- 提交訊息使用語義化格式

## 📄 授權

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 📞 聯絡資訊

如有任何問題、建議或合作機會，歡迎聯絡：

- **回報問題**: [GitHub Issues](https://github.com/ldsAS/product-recommendation-system/issues) - 回報 bug 或提出功能需求
- **討論交流**: [GitHub Discussions](https://github.com/ldsAS/product-recommendation-system/discussions) - 一般討論、問答和想法分享

> **注意**: 如果 Discussions 連結無法開啟，請前往倉庫的 Settings → General → Features，勾選 "Discussions" 以啟用此功能。

## 🙏 致謝

感謝所有為本專案做出貢獻的開發者和使用者！

特別感謝：
- FastAPI 團隊提供優秀的 Web 框架
- scikit-learn 和 LightGBM 社群
- 所有開源貢獻者

## 📚 相關文件

### 部署相關
- [🐳 Docker 快速開始](README_DOCKER.md) - Docker 一鍵部署指南
- [📦 Docker 詳細指南](DOCKER_QUICK_START.md) - 完整的 Docker 部署說明
- [🚀 部署指南](docs/DEPLOYMENT_GUIDE.md) - 生產環境部署

### 開發相關
- [📖 安裝指南](INSTALL.md) - 詳細的本地安裝說明
- [🤖 模型訓練文件](docs/MODEL_TRAINING.md) - 模型訓練與調優
- [📊 專案總結](docs/PROJECT_SUMMARY.md) - 專案架構與設計決策

### 功能相關
- [📈 監控儀表板使用指南](docs/MONITORING_DASHBOARD_GUIDE.md) - 監控系統使用說明
- [⚡ 性能追蹤指南](docs/PERFORMANCE_TRACKING_GUIDE.md) - 性能監控與優化
- [🧪 Colab 快速體驗](docs/COLAB_GUIDE.md) - 在 Google Colab 上試用（實驗性功能）

## 🗺️ 開發路線圖

### 已完成 ✅
- [x] 提供 Docker Compose 一鍵部署
- [x] 建立效能監控儀表板
- [x] 增加 Web UI 介面
- [x] 實作品質監控系統
- [x] 實作性能追蹤功能
- [x] 支援 A/B 測試框架

### 進行中 🚧
- [ ] 支援更多推薦演算法（深度學習模型）
- [ ] 實作即時模型更新機制

### 計劃中 📋
- [ ] 支援多語言推薦理由
- [ ] 整合更多資料來源
- [ ] 實作自動化模型訓練流程
- [ ] 增加推薦解釋性視覺化
- [ ] 支援多租戶架構

---

**⭐ 如果這個專案對您有幫助，請給我們一個 Star！**

**祝使用愉快！** 🚀
