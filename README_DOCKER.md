# 🐳 Docker 一鍵部署

最簡單的部署方式！只需 3 個步驟即可啟動完整的推薦系統。

## 🚀 快速開始

### Windows 用戶

```cmd
# 1. 複製環境變數文件
copy .env.example .env

# 2. 編輯 .env 設置密碼（至少設置 DB_PASSWORD 和 REDIS_PASSWORD）
notepad .env

# 3. 執行一鍵啟動腳本
quick-start.bat
```

### Linux/Mac 用戶

```bash
# 1. 複製環境變數文件
cp .env.example .env

# 2. 編輯 .env 設置密碼
nano .env

# 3. 執行一鍵啟動腳本
chmod +x quick-start.sh
./quick-start.sh
```

## 📋 前置需求

- **Docker**: 20.10+ ([安裝指南](https://docs.docker.com/get-docker/))
- **Docker Compose**: 1.29+ (通常隨 Docker Desktop 一起安裝)
- **可用端口**: 8000, 5432, 6379, 9090, 3000

## 🎯 啟動後訪問

服務啟動後（約 30 秒），訪問以下網址：

| 服務 | 網址 | 說明 |
|------|------|------|
| 🏠 主頁面 | http://localhost:8000 | 推薦系統 Web UI |
| 📚 API 文檔 | http://localhost:8000/docs | Swagger 互動式文檔 |
| 📊 監控儀表板 | http://localhost:8000/dashboard | 即時監控 |
| 📈 趨勢分析 | http://localhost:8000/trends | 歷史趨勢 |
| 🔍 Prometheus | http://localhost:9090 | 指標監控 |
| 📉 Grafana | http://localhost:3000 | 視覺化儀表板 |

## 🧪 測試推薦功能

### 方式 1: Web UI（推薦）

1. 訪問 http://localhost:8000
2. 輸入測試資料：
   ```
   會員編號: CU000001
   總消費金額: 10000
   累積紅利: 500
   ```
3. 點擊「獲取推薦」

### 方式 2: API 測試

```bash
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "member_code": "CU000001",
    "total_consumption": 10000,
    "accumulated_bonus": 500,
    "top_k": 5
  }'
```

## 📦 包含的服務

Docker Compose 會自動啟動以下服務：

```
┌─────────────────────────────────────────┐
│     推薦系統 API (Port 8000)             │
│  - Web UI                               │
│  - REST API                             │
│  - 監控儀表板                            │
└──────────┬──────────────────────────────┘
           │
    ┌──────┴──────┐
    │             │
┌───▼────┐   ┌───▼────┐
│Postgres│   │ Redis  │
│ 5432   │   │ 6379   │
└────────┘   └────────┘

┌─────────────────────────────────────────┐
│         監控系統                         │
│  - Prometheus (9090)                    │
│  - Grafana (3000)                       │
└─────────────────────────────────────────┘
```

## 🛠️ 常用命令

```bash
# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f recommendation-api

# 停止所有服務
docker-compose down

# 重啟服務
docker-compose restart

# 進入容器
docker-compose exec recommendation-api bash

# 訓練模型（如果模型文件不存在）
docker-compose exec recommendation-api python src/train.py
```

## ⚙️ 環境變數配置

最少需要配置的變數（在 `.env` 文件中）：

```bash
# 必須配置
DB_PASSWORD=your-secure-password-here
REDIS_PASSWORD=your-redis-password-here

# 可選配置
GRAFANA_PASSWORD=admin123
APP_ENV=production
```

完整配置說明請參考 [.env.example](.env.example)

## 🔧 故障排除

### 問題 1: 端口被佔用

```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000

# 解決方法：修改 docker-compose.yml 中的端口映射
# 將 "8000:8000" 改為 "8001:8000"
```

### 問題 2: 服務啟動失敗

```bash
# 查看詳細日誌
docker-compose logs

# 檢查 Docker 狀態
docker info

# 重新構建並啟動
docker-compose down
docker-compose up -d --build
```

### 問題 3: 模型文件缺失

```bash
# 進入容器訓練模型
docker-compose exec recommendation-api python src/train.py

# 或從主機複製模型文件
# 將模型文件放到 data/models/v1.0.0/ 目錄
```

## 📖 詳細文檔

- [Docker 快速開始指南](DOCKER_QUICK_START.md) - 詳細的部署說明
- [完整部署指南](docs/DEPLOYMENT_GUIDE.md) - 生產環境部署
- [監控儀表板使用指南](docs/MONITORING_DASHBOARD_GUIDE.md)
- [API 文檔](http://localhost:8000/docs) - 啟動後訪問

## 🔒 安全建議

1. **修改預設密碼**: 在 `.env` 中設置強密碼
2. **限制網路訪問**: 生產環境中限制端口訪問
3. **啟用 HTTPS**: 配置 SSL 證書
4. **定期更新**: 定期更新 Docker 映像

## 🎓 下一步

部署成功後，你可以：

1. ✅ 測試推薦功能
2. 📊 查看監控儀表板
3. 🧪 設置 A/B 測試
4. 🔧 調整推薦策略
5. 📈 分析性能趨勢

## 💡 提示

- 首次啟動需要下載映像，可能需要幾分鐘
- 確保 Docker Desktop 正在運行
- 如果遇到問題，查看日誌: `docker-compose logs -f`
- 生產環境建議使用 `scripts/deploy.sh` 腳本

## 📞 獲取幫助

- 查看 [故障排除指南](DOCKER_QUICK_START.md#故障排除)
- 查看 [完整文檔](docs/DEPLOYMENT_GUIDE.md)
- 提交 Issue: [GitHub Issues](https://github.com/your-org/recommendation-system/issues)

---

**祝你使用愉快！** 🎉

如果這個項目對你有幫助，請給我們一個 ⭐ Star！
