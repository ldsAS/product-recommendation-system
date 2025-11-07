# 🚀 Docker 一鍵部署指南

## 快速開始（3 步驟）

### 步驟 1: 準備環境變數

```bash
# 複製環境變數範例文件
cp .env.example .env

# 編輯 .env 文件（使用你喜歡的編輯器）
notepad .env  # Windows
# 或
nano .env     # Linux/Mac
```

**最少需要配置的變數**：
```bash
# 資料庫密碼
DB_PASSWORD=your-secure-password-here

# Redis 密碼
REDIS_PASSWORD=your-redis-password-here

# Grafana 密碼（可選）
GRAFANA_PASSWORD=admin123
```

### 步驟 2: 一鍵啟動

```bash
# Windows
docker-compose up -d

# Linux/Mac（使用部署腳本）
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### 步驟 3: 驗證服務

等待約 30 秒後，訪問以下網址：

- **主頁面**: http://localhost:8000
- **API 文檔**: http://localhost:8000/docs
- **監控儀表板**: http://localhost:8000/dashboard
- **趨勢分析**: http://localhost:8000/trends

---

## 詳細說明

### 服務架構

啟動後會運行以下服務：

| 服務 | 端口 | 說明 |
|------|------|------|
| recommendation-api | 8000 | 推薦系統 API |
| postgres | 5432 | PostgreSQL 資料庫 |
| redis | 6379 | Redis 快取 |
| prometheus | 9090 | Prometheus 監控 |
| grafana | 3000 | Grafana 儀表板 |
| nginx | 80/443 | Nginx 反向代理 |

### 常用命令

```bash
# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f recommendation-api

# 停止所有服務
docker-compose down

# 停止並刪除所有資料（包括資料庫）
docker-compose down -v

# 重啟特定服務
docker-compose restart recommendation-api

# 查看資源使用
docker stats
```

### 測試推薦功能

**方式 1: 使用 Web UI**
1. 訪問 http://localhost:8000
2. 輸入測試資料：
   - 會員編號: CU000001
   - 總消費金額: 10000
   - 累積紅利: 500
3. 點擊「獲取推薦」

**方式 2: 使用 curl**
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

**方式 3: 使用 Swagger UI**
1. 訪問 http://localhost:8000/docs
2. 找到 `/api/v1/recommendations` 端點
3. 點擊 "Try it out"
4. 輸入測試資料並執行

---

## 故障排除

### 問題 1: 端口被佔用

**錯誤訊息**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**解決方法**:
```bash
# Windows - 查看佔用端口的程序
netstat -ano | findstr :8000

# 修改 docker-compose.yml 中的端口映射
# 將 "8000:8000" 改為 "8001:8000"
```

### 問題 2: 資料庫連接失敗

**檢查步驟**:
```bash
# 1. 檢查 postgres 容器狀態
docker-compose ps postgres

# 2. 查看 postgres 日誌
docker-compose logs postgres

# 3. 檢查 .env 中的資料庫配置
cat .env | grep DB_
```

### 問題 3: 服務啟動慢

**原因**: 首次啟動需要下載映像和初始化資料庫

**解決方法**: 耐心等待 1-2 分鐘，可以查看日誌：
```bash
docker-compose logs -f
```

### 問題 4: 模型文件缺失

**錯誤訊息**: `Model file not found`

**解決方法**:
```bash
# 1. 確保模型文件存在
ls -la data/models/v1.0.0/

# 2. 如果沒有，需要先訓練模型
# 進入容器
docker-compose exec recommendation-api bash

# 訓練模型
python src/train.py

# 退出容器
exit
```

---

## 進階配置

### 使用生產環境配置

```bash
# 1. 編輯 .env
APP_ENV=production
APP_DEBUG=false

# 2. 使用生產配置文件
cp config/production.yaml config/recommendation_config.yaml

# 3. 重啟服務
docker-compose restart recommendation-api
```

### 增加 API 服務實例

編輯 `docker-compose.yml`:
```yaml
services:
  recommendation-api:
    # ...
    deploy:
      replicas: 4  # 增加到 4 個實例
```

### 配置 SSL 證書

```bash
# 1. 將證書文件放到 config/nginx/ssl/
cp your-cert.pem config/nginx/ssl/cert.pem
cp your-key.pem config/nginx/ssl/key.pem

# 2. 重啟 nginx
docker-compose restart nginx

# 3. 訪問 https://localhost
```

---

## 監控和維護

### 查看監控數據

1. **應用監控**: http://localhost:8000/dashboard
   - 品質指標
   - 性能指標
   - 告警記錄

2. **Prometheus**: http://localhost:9090
   - 原始指標數據
   - 查詢和圖表

3. **Grafana**: http://localhost:3000
   - 預設帳號: admin
   - 預設密碼: 在 .env 中設置的 GRAFANA_PASSWORD

### 備份資料

```bash
# 備份資料庫
docker exec recommendation-postgres pg_dump -U postgres recommendation_db > backup_$(date +%Y%m%d).sql

# 備份模型
tar -czf models_backup_$(date +%Y%m%d).tar.gz data/models/

# 備份配置
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/
```

### 恢復資料

```bash
# 恢復資料庫
docker exec -i recommendation-postgres psql -U postgres recommendation_db < backup_20250115.sql

# 恢復模型
tar -xzf models_backup_20250115.tar.gz

# 恢復配置
tar -xzf config_backup_20250115.tar.gz
```

### 清理資源

```bash
# 清理未使用的映像
docker image prune -a

# 清理未使用的容器
docker container prune

# 清理未使用的卷
docker volume prune

# 清理所有未使用的資源
docker system prune -a --volumes
```

---

## 效能優化

### 1. 調整 Worker 數量

編輯 `Dockerfile`:
```dockerfile
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "8"]
```

### 2. 增加資料庫連接池

編輯 `.env`:
```bash
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=20
```

### 3. 增加 Redis 記憶體

編輯 `docker-compose.yml`:
```yaml
redis:
  command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 2gb --maxmemory-policy allkeys-lru
```

---

## 安全建議

1. **使用強密碼**
   - 資料庫密碼至少 16 字元
   - Redis 密碼至少 32 字元
   - 定期更換密碼

2. **限制網路訪問**
   ```bash
   # 僅允許本地訪問資料庫
   # 修改 docker-compose.yml
   postgres:
     ports:
       - "127.0.0.1:5432:5432"  # 僅本地訪問
   ```

3. **啟用 HTTPS**
   - 使用 Let's Encrypt 免費證書
   - 配置 Nginx SSL

4. **定期更新**
   ```bash
   # 更新映像
   docker-compose pull
   docker-compose up -d
   ```

---

## 完整部署檢查清單

- [ ] 已安裝 Docker 和 Docker Compose
- [ ] 已複製並配置 .env 文件
- [ ] 已設置強密碼
- [ ] 已準備模型文件（或計劃訓練）
- [ ] 已執行 `docker-compose up -d`
- [ ] 所有服務狀態為 "Up"
- [ ] 可以訪問 http://localhost:8000
- [ ] 健康檢查通過
- [ ] 推薦功能正常
- [ ] 監控儀表板可訪問
- [ ] 已設置備份計劃

---

## 獲取幫助

如果遇到問題：

1. 查看日誌: `docker-compose logs -f`
2. 檢查服務狀態: `docker-compose ps`
3. 查看詳細部署指南: [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)
4. 提交 Issue: https://github.com/your-org/recommendation-system/issues

---

## 下一步

部署成功後，你可以：

1. 📊 查看[監控儀表板使用指南](docs/MONITORING_DASHBOARD_GUIDE.md)
2. 📈 了解[性能追蹤功能](docs/PERFORMANCE_TRACKING_GUIDE.md)
3. 🧪 設置 [A/B 測試](AB_TESTING_FRAMEWORK_IMPLEMENTATION.md)
4. 🔧 調整[推薦策略配置](config/recommendation_config.yaml)

祝你使用愉快！🎉
