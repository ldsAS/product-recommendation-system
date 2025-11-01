# 產品推薦系統部署指南

## 目錄

1. [系統需求](#系統需求)
2. [安裝步驟](#安裝步驟)
3. [配置說明](#配置說明)
4. [部署方式](#部署方式)
5. [監控和維護](#監控和維護)
6. [故障排除](#故障排除)

## 系統需求

### 硬體需求

#### 最低配置
- **CPU**: 2 核心
- **記憶體**: 4GB RAM
- **磁碟空間**: 5GB 可用空間
- **網路**: 穩定的網路連接

#### 建議配置
- **CPU**: 4 核心以上
- **記憶體**: 8GB RAM 以上
- **磁碟空間**: 20GB 可用空間（包含日誌和模型）
- **網路**: 100Mbps 以上

### 軟體需求

#### 必要軟體
- **作業系統**: 
  - Linux (Ubuntu 20.04+, CentOS 7+)
  - Windows 10/11
  - macOS 10.15+
- **Python**: 3.9 或更高版本
- **pip**: 最新版本

#### 可選軟體
- **Docker**: 20.10+ (用於容器化部署)
- **Docker Compose**: 1.29+ (用於服務編排)
- **Nginx**: 1.18+ (用於反向代理)
- **Redis**: 6.0+ (用於快取)

## 安裝步驟

### 方式 1: 標準安裝

#### 1. 下載專案

```bash
# 使用 Git 克隆
git clone <repository-url>
cd recommendation-system

# 或下載 ZIP 並解壓
unzip recommendation-system.zip
cd recommendation-system
```

#### 2. 建立虛擬環境

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### 3. 安裝依賴

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. 準備資料

```bash
# 建立必要目錄
mkdir -p data/raw data/processed data/models logs

# 複製資料檔案到 data/raw/
# - member.csv
# - sales.csv
# - salesdetails.csv
```

#### 5. 訓練模型（首次使用）

```bash
python src/train.py
```

#### 6. 啟動服務

```bash
# 開發模式
python src/api/main.py

# 生產模式
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 方式 2: Docker 部署

#### 1. 安裝 Docker

```bash
# Linux (Ubuntu)
sudo apt-get update
sudo apt-get install docker.io docker-compose

# macOS
brew install docker docker-compose

# Windows
# 下載並安裝 Docker Desktop
```

#### 2. 建構映像

```bash
docker-compose build
```

#### 3. 啟動服務

```bash
docker-compose up -d
```

#### 4. 檢查狀態

```bash
docker-compose ps
docker-compose logs -f
```

### 方式 3: 自動化部署

#### Linux/macOS

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh --env production
```

#### Windows

```powershell
.\scripts\deploy.ps1 -Environment production
```

## 配置說明

### 環境變數

建立 `.env` 檔案：

```bash
# 應用配置
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# 資料路徑
DATA_DIR=./data
MODELS_DIR=./data/models
LOGS_DIR=./logs

# 模型配置
MODEL_VERSION=v1.0.0
MODEL_TYPE=lightgbm

# API 配置
API_WORKERS=4
API_TIMEOUT=30
MAX_REQUEST_SIZE=10485760

# 日誌配置
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_ROTATION=daily

# 快取配置（可選）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
CACHE_TTL=3600

# 監控配置
ENABLE_METRICS=true
METRICS_PORT=9090
```

### 配置檔案

#### config.py

```python
import os
from pathlib import Path

# 基礎路徑
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = Path(os.getenv('DATA_DIR', BASE_DIR / 'data'))
MODELS_DIR = Path(os.getenv('MODELS_DIR', DATA_DIR / 'models'))
LOGS_DIR = Path(os.getenv('LOGS_DIR', BASE_DIR / 'logs'))

# API 配置
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 8000))
API_WORKERS = int(os.getenv('API_WORKERS', 4))

# 模型配置
MODEL_VERSION = os.getenv('MODEL_VERSION', 'v1.0.0')
MODEL_TYPE = os.getenv('MODEL_TYPE', 'lightgbm')

# 日誌配置
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')
```

## 部署方式

### 開發環境部署

適用於本地開發和測試。

```bash
# 啟動開發伺服器
python src/api/main.py

# 或使用 uvicorn
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

特點：
- 自動重載
- 詳細的錯誤訊息
- 不適合生產環境

### 測試環境部署

適用於功能測試和整合測試。

```bash
# 使用 Docker Compose
docker-compose -f docker-compose.test.yml up -d
```

特點：
- 獨立的測試資料庫
- 模擬生產環境
- 可重複部署

### 生產環境部署

#### 選項 1: 使用 Uvicorn + Nginx

1. **啟動 Uvicorn**

```bash
# 使用 systemd 管理服務
sudo nano /etc/systemd/system/recommendation-api.service
```

```ini
[Unit]
Description=Recommendation API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/recommendation-system
Environment="PATH=/opt/recommendation-system/venv/bin"
ExecStart=/opt/recommendation-system/venv/bin/uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 啟動服務
sudo systemctl daemon-reload
sudo systemctl start recommendation-api
sudo systemctl enable recommendation-api
```

2. **配置 Nginx**

```bash
sudo nano /etc/nginx/sites-available/recommendation-api
```

```nginx
upstream recommendation_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.example.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://recommendation_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超時設定
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    location /static {
        alias /opt/recommendation-system/static;
    }

    location /health {
        proxy_pass http://recommendation_api/health;
        access_log off;
    }
}
```

```bash
# 啟用站點
sudo ln -s /etc/nginx/sites-available/recommendation-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 選項 2: 使用 Docker Swarm

```bash
# 初始化 Swarm
docker swarm init

# 部署服務
docker stack deploy -c docker-compose.prod.yml recommendation

# 檢查服務
docker service ls
docker service logs recommendation_api
```

#### 選項 3: 使用 Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: recommendation-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: recommendation-api
  template:
    metadata:
      labels:
        app: recommendation-api
    spec:
      containers:
      - name: api
        image: recommendation-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
---
apiVersion: v1
kind: Service
metadata:
  name: recommendation-api
spec:
  selector:
    app: recommendation-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

```bash
kubectl apply -f deployment.yaml
kubectl get pods
kubectl get services
```

## 監控和維護

### 健康檢查

```bash
# 檢查應用健康狀態
curl http://localhost:8000/health

# 檢查推薦服務
curl http://localhost:8000/api/v1/recommendations/health

# 檢查模型資訊
curl http://localhost:8000/api/v1/model/info
```

### 日誌管理

#### 查看日誌

```bash
# 應用日誌
tail -f logs/recommendation_system.log

# 錯誤日誌
tail -f logs/recommendation_system_error.log

# 推薦日誌
tail -f logs/recommendation.log

# Docker 日誌
docker-compose logs -f
```

#### 日誌輪轉

系統自動進行日誌輪轉，配置如下：
- 單個檔案最大 10MB
- 保留最近 5 個備份
- 自動壓縮舊日誌

### 效能監控

#### Prometheus 指標

```bash
# 查看指標
curl http://localhost:8000/metrics

# 常見指標
# - api_requests_total: 總請求數
# - api_response_time_ms: 回應時間
# - recommendations_total: 推薦總數
# - conversions_total: 轉換總數
```

#### 系統資源監控

```bash
# CPU 和記憶體使用
top
htop

# 磁碟使用
df -h
du -sh logs/ data/

# 網路連接
netstat -an | grep 8000
```

### 備份策略

#### 模型備份

```bash
# 備份模型
tar -czf models_backup_$(date +%Y%m%d).tar.gz data/models/

# 恢復模型
tar -xzf models_backup_20250115.tar.gz
```

#### 資料備份

```bash
# 備份資料
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/

# 恢復資料
tar -xzf data_backup_20250115.tar.gz
```

### 更新和升級

#### 更新應用

```bash
# 拉取最新程式碼
git pull origin main

# 安裝新依賴
pip install -r requirements.txt

# 重啟服務
sudo systemctl restart recommendation-api

# 或使用 Docker
docker-compose down
docker-compose build
docker-compose up -d
```

#### 模型更新

```bash
# 訓練新模型
python src/train.py

# 切換模型版本
# 編輯 .env 檔案
MODEL_VERSION=v1.1.0

# 重啟服務
sudo systemctl restart recommendation-api
```

## 故障排除

### 常見問題

#### 1. 服務無法啟動

**症狀**: 執行啟動命令後服務立即退出

**可能原因**:
- 端口被占用
- 模型檔案不存在
- 配置錯誤

**解決方法**:
```bash
# 檢查端口
netstat -an | grep 8000
lsof -i :8000

# 檢查模型
ls -la data/models/

# 檢查日誌
tail -f logs/recommendation_system_error.log
```

#### 2. 推薦回應緩慢

**症狀**: API 回應時間超過 3 秒

**可能原因**:
- 模型載入慢
- 資源不足
- 資料處理瓶頸

**解決方法**:
```bash
# 檢查系統資源
top
free -h

# 優化配置
# 增加 worker 數量
API_WORKERS=8

# 啟用快取
ENABLE_CACHE=true
```

#### 3. 記憶體不足

**症狀**: 系統記憶體使用率持續上升

**可能原因**:
- 記憶體洩漏
- 快取過大
- 模型過大

**解決方法**:
```bash
# 重啟服務
sudo systemctl restart recommendation-api

# 調整配置
# 減少 worker 數量
API_WORKERS=2

# 限制快取大小
CACHE_SIZE=1000
```

### 緊急處理

#### 服務降級

```bash
# 停止推薦服務
sudo systemctl stop recommendation-api

# 啟用備用服務
sudo systemctl start recommendation-api-fallback
```

#### 回滾版本

```bash
# 回滾到上一個版本
git checkout v1.0.0

# 重新部署
./scripts/deploy.sh --env production
```

### 聯繫支援

如果問題無法解決，請聯繫技術支援：

- **Email**: support@company.com
- **電話**: 02-1234-5678
- **工單系統**: https://support.company.com

提供以下資訊：
1. 錯誤訊息和日誌
2. 系統環境資訊
3. 重現步驟
4. 已嘗試的解決方法

## 安全建議

### 1. 網路安全

- 使用 HTTPS (SSL/TLS)
- 配置防火牆規則
- 限制 API 訪問來源
- 啟用 CORS 保護

### 2. 認證和授權

- 實作 API Key 認證
- 使用 JWT Token
- 設置請求頻率限制
- 記錄訪問日誌

### 3. 資料安全

- 加密敏感資料
- 定期備份
- 限制檔案訪問權限
- 清理過期日誌

### 4. 系統加固

- 定期更新依賴
- 掃描安全漏洞
- 最小化權限
- 監控異常活動

## 效能優化

### 1. 應用層優化

- 啟用快取機制
- 使用連接池
- 非同步處理
- 批次請求

### 2. 資料庫優化

- 建立索引
- 查詢優化
- 連接池管理
- 讀寫分離

### 3. 系統層優化

- 調整核心參數
- 優化檔案系統
- 使用 SSD
- 增加記憶體

### 4. 網路優化

- 使用 CDN
- 啟用壓縮
- 減少請求數
- 使用 HTTP/2

---

**文檔版本**: v1.0.0  
**最後更新**: 2025-01-15  
**維護者**: 技術團隊
