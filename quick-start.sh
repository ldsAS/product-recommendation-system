#!/bin/bash

# ============================================================================
# 推薦系統 Docker 一鍵部署腳本 (Linux/Mac)
# Recommendation System Docker Quick Start Script
# ============================================================================

set -e  # 遇到錯誤立即退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[$1]${NC} $2"
}

# 顯示標題
echo ""
echo "============================================================"
echo "  推薦系統 Docker 一鍵部署"
echo "  Recommendation System Docker Quick Start"
echo "============================================================"
echo ""

# 檢查 Docker
log_step "1/6" "檢查 Docker 環境..."
if ! command -v docker &> /dev/null; then
    log_error "Docker 未安裝"
    echo "請先安裝 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
log_info "Docker 已安裝: $(docker --version)"

# 檢查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose 未安裝"
    echo "請先安裝 Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
log_info "Docker Compose 已安裝: $(docker-compose --version)"

# 檢查 Docker 是否運行
if ! docker info &> /dev/null; then
    log_error "Docker 未運行"
    echo "請啟動 Docker 服務"
    exit 1
fi
log_info "Docker 服務正在運行"

# 檢查 .env 文件
echo ""
log_step "2/6" "檢查環境變數配置..."
if [ ! -f .env ]; then
    log_warn ".env 文件不存在"
    echo "正在從 .env.example 複製..."
    cp .env.example .env
    echo ""
    log_warn "請編輯 .env 文件並設置以下變數:"
    echo "  - DB_PASSWORD: 資料庫密碼"
    echo "  - REDIS_PASSWORD: Redis 密碼"
    echo "  - GRAFANA_PASSWORD: Grafana 密碼"
    echo ""
    read -p "是否已完成配置? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "請先配置 .env 文件後再執行此腳本"
        ${EDITOR:-nano} .env
        exit 1
    fi
else
    log_info ".env 文件已存在"
fi

# 檢查模型文件
echo ""
log_step "3/6" "檢查模型文件..."
if [ -f "data/models/v1.0.0/model.pkl" ]; then
    log_info "模型文件已存在"
else
    log_warn "模型文件不存在"
    echo "首次啟動後需要訓練模型"
    echo "訓練命令: docker-compose exec recommendation-api python src/train.py"
fi

# 停止舊服務
echo ""
log_step "4/6" "停止舊服務..."
docker-compose down &> /dev/null || true
log_info "舊服務已停止"

# 啟動服務
echo ""
log_step "5/6" "啟動 Docker 服務..."
echo "這可能需要幾分鐘時間（首次啟動需要下載映像）..."
docker-compose up -d

if [ $? -ne 0 ]; then
    log_error "服務啟動失敗"
    echo "請查看錯誤訊息並檢查配置"
    exit 1
fi

log_info "服務已啟動"

# 等待服務就緒
echo ""
log_step "6/6" "等待服務就緒..."
sleep 10

MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_info "API 服務就緒"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "等待 API 服務啟動... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "API 服務啟動超時"
    echo "請查看日誌: docker-compose logs recommendation-api"
    exit 1
fi

# 顯示服務狀態
echo ""
echo "============================================================"
echo "  部署完成！"
echo "============================================================"
echo ""
echo "服務狀態:"
docker-compose ps
echo ""
echo "============================================================"
echo "  訪問地址"
echo "============================================================"
echo ""
echo "  主頁面:          http://localhost:8000"
echo "  API 文檔:        http://localhost:8000/docs"
echo "  監控儀表板:      http://localhost:8000/dashboard"
echo "  趨勢分析:        http://localhost:8000/trends"
echo "  Prometheus:      http://localhost:9090"
echo "  Grafana:         http://localhost:3000"
echo ""
echo "============================================================"
echo "  常用命令"
echo "============================================================"
echo ""
echo "  查看日誌:        docker-compose logs -f"
echo "  停止服務:        docker-compose down"
echo "  重啟服務:        docker-compose restart"
echo "  查看狀態:        docker-compose ps"
echo ""
echo "============================================================"
echo "  下一步"
echo "============================================================"
echo ""
echo "  1. 在瀏覽器中打開: http://localhost:8000"
echo "  2. 輸入測試資料獲取推薦"
echo "  3. 查看監控儀表板: http://localhost:8000/dashboard"
echo ""
echo "  如果模型文件不存在，請執行:"
echo "  docker-compose exec recommendation-api python src/train.py"
echo ""
echo "============================================================"
echo ""

# 詢問是否打開瀏覽器
read -p "是否在瀏覽器中打開主頁面? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 根據作業系統選擇打開命令
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open http://localhost:8000
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        xdg-open http://localhost:8000 &> /dev/null || true
    fi
fi

echo ""
echo "感謝使用推薦系統！"
