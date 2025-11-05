# 部署指南

## 概述

本文檔提供推薦系統的完整部署指南，包括測試環境和生產環境的部署步驟。

## 部署架構

```
┌─────────────────────────────────────────────────────────────┐
│                         Nginx (反向代理)                      │
│                      Port 80/443 (HTTPS)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                  推薦系統 API (FastAPI)                       │
│                      Port 8000                               │
│  - 推薦引擎                                                   │
│  - 品質監控                                                   │
│  - 性能追蹤                                                   │
└─────────┬────────────────────────────────┬──────────────────┘
          │                                │
┌─────────┴─────────┐          ┌──────────┴──────────┐
│   PostgreSQL      │          │      Redis          │
│   Port 5432       │          │    Port 6379        │
│  - 監控記錄        │          │   - 快取            │
│  - 告警記錄        │          │   - 會話            │
│  - A/B 測試       │          │                     │
└───────────────────┘          └─────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      監控系統                                 │
│  - Prometheus (Port 9090)                                   │
│  - Grafana (Port 3000)                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 前置需求

### 系統需求

- **作業系統**: Linux (Ubuntu 20.04+ 推薦) / Windows Server 2019+
- **CPU**: 4 核心以上
- **記憶體**: 8GB 以上（推薦 16GB）
- **硬碟**: 50GB 以上可用空間
- **網路**: 穩定的網路連接

### 軟體需求

- **Docker**: 20.10+
- **Docker Compose**: 1.29+
- **Python**: 3.10+ (如果不使用 Docker)
- **PostgreSQL**: 15+ (如果不使用 Docker)
- **Redis**: 7+ (如果不使用 Docker)

---

## 部署步驟

### 1. 準備環境

#### 1.1 安裝 Docker 和 Docker Compose

**Ubuntu/Debian**:
```bash
# 安裝 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安裝 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 驗證安裝
docker --version
docker-compose --version
```

**Windows**:
- 下載並安裝 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)

#### 1.2 克隆代碼庫

```bash
git clone https://github.com/your-org/recommendation-system.git
cd recommendation-system
```

#### 1.3 配置環境變數

```bash
# 複製環境變數範例文件
cp .env.example .env

# 編輯 .env 文件，填入實際配置
nano .env
```

**必須配置的環境變數**:
```bash
# 資料庫
DB_HOST=postgres
DB_NAME=recommendation_db
DB_USER=postgres
DB_PASSWORD=your-secure-password

# Redis
REDIS_HOST=redis
REDIS_PASSWORD=your-redis-password

# 告警
ALERT_FROM_EMAIL=alerts@your-domain.com
ALERT_TO_EMAIL_1=team@your-domain.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# API Keys
API_KEY_1=your-api-key-1-min-32-characters-long
API_KEY_2=your-api-key-2-min-32-characters-long
```

---

### 2. 測試環境部署

#### 2.1 啟動服務

```bash
# 使用 Docker Compose 啟動所有服務
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f recommendation-api
```

#### 2.2 初始化資料庫

```bash
# 資料庫會自動初始化，檢查初始化狀態
docker-compose logs postgres | grep "initialization"
```

#### 2.3 驗證服務

```bash
# 健康檢查
curl http://localhost:8000/health

# 測試推薦 API
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "member_code": "CU000001",
    "top_k": 5
  }'

# 訪問 API 文檔
# 瀏覽器打開: http://localhost:8000/docs

# 訪問監控儀表板
# 瀏覽器打開: http://localhost:8000/dashboard
```

#### 2.4 執行冒煙測試

```bash
# 運行測試腳本
python scripts/test_system.py

# 或使用 pytest
pytest tests/test_e2e_integration.py -v
```

---

### 3. 生產環境部署

#### 3.1 準備生產配置

```bash
# 使用生產環境配置
cp config/production.yaml config/recommendation_config.yaml

# 編輯配置文件
nano config/recommendation_config.yaml
```

**重要配置項**:
- 關閉 debug 模式
- 設置正確的資料庫連接
- 配置告警通道
- 設置 API 認證
- 配置 CORS 白名單

#### 3.2 使用部署腳本

```bash
# 賦予執行權限
chmod +x scripts/deploy.sh

# 執行部署
./scripts/deploy.sh
```

部署腳本會自動執行以下步驟：
1. 檢查環境
2. 備份現有資料
3. 構建 Docker 映像
4. 停止舊服務
5. 啟動新服務
6. 等待服務就緒
7. 執行冒煙測試
8. 顯示服務狀態

#### 3.3 配置 Nginx 反向代理（可選）

```nginx
# /etc/nginx/sites-available/recommendation-api

upstream recommendation_api {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.your-domain.com;
    
    # SSL 證書
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # 日誌
    access_log /var/log/nginx/recommendation-api-access.log;
    error_log /var/log/nginx/recommendation-api-error.log;
    
    # 代理配置
    location / {
        proxy_pass http://recommendation_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超時設置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 健康檢查
    location /health {
        proxy_pass http://recommendation_api/health;
        access_log off;
    }
}
```

啟用配置：
```bash
sudo ln -s /etc/nginx/sites-available/recommendation-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 3.4 配置 SSL 證書

使用 Let's Encrypt 免費證書：
```bash
# 安裝 Certbot
sudo apt-get install certbot python3-certbot-nginx

# 獲取證書
sudo certbot --nginx -d api.your-domain.com

# 自動續期
sudo certbot renew --dry-run
```

---

### 4. 監控系統運行狀態

#### 4.1 查看服務狀態

```bash
# Docker 容器狀態
docker-compose ps

# 查看資源使用
docker stats

# 查看日誌
docker-compose logs -f --tail=100 recommendation-api
```

#### 4.2 訪問監控儀表板

- **應用儀表板**: http://localhost:8000/dashboard
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (預設帳號: admin/admin)

#### 4.3 設置告警

告警會自動發送到配置的通道（Email、Slack）。

檢查告警配置：
```bash
# 查看告警記錄
curl http://localhost:8000/api/v1/monitoring/alerts?time_window_minutes=60

# 測試告警通道
python scripts/test_alerts.py
```

---

### 5. 備份和恢復

#### 5.1 自動備份

系統會自動執行以下備份：
- **資料庫**: 每天凌晨 2 點
- **模型**: 每週日凌晨 3 點
- **日誌**: 每天凌晨 4 點

備份文件位置：`/backups/`

#### 5.2 手動備份

```bash
# 備份資料庫
docker exec recommendation-postgres pg_dump -U postgres recommendation_db > backup_$(date +%Y%m%d).sql

# 備份模型
tar -czf models_backup_$(date +%Y%m%d).tar.gz data/models/

# 備份配置
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/
```

#### 5.3 恢復資料

```bash
# 恢復資料庫
docker exec -i recommendation-postgres psql -U postgres recommendation_db < backup_20250115.sql

# 恢復模型
tar -xzf models_backup_20250115.tar.gz

# 恢復配置
tar -xzf config_backup_20250115.tar.gz
```

---

### 6. 擴展和優化

#### 6.1 水平擴展

增加 API 服務實例：
```yaml
# docker-compose.yml
services:
  recommendation-api:
    # ...
    deploy:
      replicas: 4  # 增加到 4 個實例
```

#### 6.2 垂直擴展

增加資源限制：
```yaml
services:
  recommendation-api:
    # ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

#### 6.3 資料庫優化

```sql
-- 創建額外索引
CREATE INDEX idx_monitoring_records_composite 
ON monitoring_records(timestamp, member_code, overall_score);

-- 分區表（大量數據時）
CREATE TABLE monitoring_records_2025_01 PARTITION OF monitoring_records
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- 定期清理
SELECT cleanup_expired_records();
```

---

### 7. 故障排除

#### 7.1 服務無法啟動

**檢查日誌**:
```bash
docker-compose logs recommendation-api
```

**常見問題**:
1. 端口被佔用
   ```bash
   # 檢查端口
   netstat -tulpn | grep 8000
   # 修改 docker-compose.yml 中的端口映射
   ```

2. 資料庫連接失敗
   ```bash
   # 檢查資料庫狀態
   docker-compose logs postgres
   # 檢查 .env 中的資料庫配置
   ```

3. 模型文件缺失
   ```bash
   # 檢查模型文件
   ls -la data/models/
   # 重新訓練模型
   python src/train.py
   ```

#### 7.2 性能問題

**檢查資源使用**:
```bash
# CPU 和記憶體使用
docker stats

# 資料庫連接數
docker exec recommendation-postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
```

**優化建議**:
1. 增加 Redis 快取
2. 優化資料庫查詢
3. 增加 API 服務實例
4. 使用 CDN 加速靜態資源

#### 7.3 資料不一致

**檢查監控記錄**:
```bash
# 查看最近的監控記錄
docker exec recommendation-postgres psql -U postgres recommendation_db -c "SELECT * FROM monitoring_records ORDER BY timestamp DESC LIMIT 10;"
```

**重建索引**:
```bash
docker exec recommendation-postgres psql -U postgres recommendation_db -c "REINDEX DATABASE recommendation_db;"
```

---

### 8. 安全最佳實踐

#### 8.1 網路安全

- 使用防火牆限制訪問
- 僅開放必要的端口
- 使用 VPN 訪問管理介面

```bash
# UFW 防火牆配置
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # 僅允許內部訪問
sudo ufw enable
```

#### 8.2 資料安全

- 定期備份資料
- 加密敏感資訊
- 使用強密碼
- 定期更換密鑰

#### 8.3 應用安全

- 啟用 API 認證
- 配置速率限制
- 定期更新依賴
- 監控異常訪問

```bash
# 檢查安全漏洞
pip install safety
safety check

# 更新依賴
pip install --upgrade -r requirements.txt
```

---

### 9. 維護計劃

#### 9.1 日常維護

- 查看監控儀表板
- 檢查告警記錄
- 查看系統日誌
- 驗證備份完整性

#### 9.2 週期性維護

**每週**:
- 查看性能趨勢
- 分析慢查詢
- 清理過期資料
- 更新文檔

**每月**:
- 生成月度報告
- 評估系統改進
- 更新依賴套件
- 執行安全審計

**每季度**:
- 容量規劃
- 災難恢復演練
- 性能基準測試
- 架構評估

---

### 10. 回滾計劃

如果部署出現問題，可以快速回滾：

```bash
# 停止新服務
docker-compose down

# 恢復備份
./scripts/restore_backup.sh /backups/20250115_100000

# 啟動舊版本
git checkout v1.0.0
docker-compose up -d

# 驗證服務
curl http://localhost:8000/health
```

---

## 檢查清單

### 部署前檢查

- [ ] 環境變數已配置
- [ ] 資料庫連接已測試
- [ ] Redis 連接已測試
- [ ] 模型文件已準備
- [ ] 告警通道已配置
- [ ] SSL 證書已安裝
- [ ] 備份策略已設置
- [ ] 監控系統已配置

### 部署後檢查

- [ ] 所有服務正常運行
- [ ] 健康檢查通過
- [ ] API 測試通過
- [ ] 監控數據正常
- [ ] 告警功能正常
- [ ] 日誌記錄正常
- [ ] 備份任務正常
- [ ] 性能指標達標

---

## 支援

如有問題，請聯繫：
- **技術支援**: support@your-domain.com
- **緊急聯繫**: +886-xxx-xxx-xxx
- **文檔**: https://docs.your-domain.com

---

## 參考資料

- [API 文檔](API_DOCUMENTATION.md)
- [監控儀表板使用指南](MONITORING_DASHBOARD_GUIDE.md)
- [性能追蹤使用指南](PERFORMANCE_TRACKING_GUIDE.md)
- [Docker 官方文檔](https://docs.docker.com/)
- [FastAPI 官方文檔](https://fastapi.tiangolo.com/)
