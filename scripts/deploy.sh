#!/bin/bash

# 部署腳本
# Deployment Script

set -e  # 遇到錯誤立即退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查環境
check_environment() {
    log_info "檢查部署環境..."
    
    # 檢查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安裝，請先安裝 Docker"
        exit 1
    fi
    
    # 檢查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安裝，請先安裝 Docker Compose"
        exit 1
    fi
    
    # 檢查 .env 文件
    if [ ! -f .env ]; then
        log_error ".env 文件不存在，請從 .env.example 複製並配置"
        exit 1
    fi
    
    log_info "✓ 環境檢查通過"
}

# 備份資料
backup_data() {
    log_info "備份現有資料..."
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 備份資料庫
    if docker ps | grep -q recommendation-postgres; then
        log_info "備份資料庫..."
        docker exec recommendation-postgres pg_dump -U postgres recommendation_db > "$BACKUP_DIR/database.sql"
        log_info "✓ 資料庫備份完成: $BACKUP_DIR/database.sql"
    fi
    
    # 備份模型
    if [ -d "data/models" ]; then
        log_info "備份模型..."
        cp -r data/models "$BACKUP_DIR/"
        log_info "✓ 模型備份完成"
    fi
    
    # 備份配置
    if [ -f "config/recommendation_config.yaml" ]; then
        log_info "備份配置..."
        cp config/recommendation_config.yaml "$BACKUP_DIR/"
        log_info "✓ 配置備份完成"
    fi
    
    log_info "✓ 備份完成: $BACKUP_DIR"
}

# 構建映像
build_images() {
    log_info "構建 Docker 映像..."
    
    docker-compose build --no-cache
    
    log_info "✓ 映像構建完成"
}

# 停止舊服務
stop_old_services() {
    log_info "停止舊服務..."
    
    if docker ps | grep -q recommendation; then
        docker-compose down
        log_info "✓ 舊服務已停止"
    else
        log_info "沒有運行中的服務"
    fi
}

# 啟動新服務
start_new_services() {
    log_info "啟動新服務..."
    
    docker-compose up -d
    
    log_info "✓ 新服務已啟動"
}

# 等待服務就緒
wait_for_services() {
    log_info "等待服務就緒..."
    
    # 等待 API 服務
    MAX_RETRIES=30
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_info "✓ API 服務就緒"
            break
        fi
        
        RETRY_COUNT=$((RETRY_COUNT + 1))
        log_info "等待 API 服務啟動... ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 2
    done
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        log_error "API 服務啟動超時"
        exit 1
    fi
}

# 執行冒煙測試
run_smoke_tests() {
    log_info "執行冒煙測試..."
    
    # 測試健康檢查
    log_info "測試健康檢查端點..."
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_info "✓ 健康檢查通過"
    else
        log_error "健康檢查失敗"
        exit 1
    fi
    
    # 測試推薦 API
    log_info "測試推薦 API..."
    RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/recommendations \
        -H "Content-Type: application/json" \
        -d '{"member_code": "CU000001", "top_k": 5}')
    
    if echo "$RESPONSE" | grep -q "recommendations"; then
        log_info "✓ 推薦 API 測試通過"
    else
        log_error "推薦 API 測試失敗"
        log_error "回應: $RESPONSE"
        exit 1
    fi
    
    # 測試監控 API
    log_info "測試監控 API..."
    if curl -f http://localhost:8000/api/v1/monitoring/realtime &> /dev/null; then
        log_info "✓ 監控 API 測試通過"
    else
        log_warn "監控 API 測試失敗（可能是沒有監控數據）"
    fi
    
    log_info "✓ 冒煙測試完成"
}

# 顯示服務狀態
show_status() {
    log_info "服務狀態:"
    docker-compose ps
    
    log_info ""
    log_info "服務訪問地址:"
    log_info "  - API: http://localhost:8000"
    log_info "  - API 文檔: http://localhost:8000/docs"
    log_info "  - 監控儀表板: http://localhost:8000/dashboard"
    log_info "  - Prometheus: http://localhost:9090"
    log_info "  - Grafana: http://localhost:3000"
}

# 主函數
main() {
    log_info "========================================="
    log_info "推薦系統部署腳本"
    log_info "========================================="
    log_info ""
    
    # 檢查環境
    check_environment
    
    # 詢問是否備份
    read -p "是否備份現有資料? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        backup_data
    fi
    
    # 構建映像
    build_images
    
    # 停止舊服務
    stop_old_services
    
    # 啟動新服務
    start_new_services
    
    # 等待服務就緒
    wait_for_services
    
    # 執行冒煙測試
    run_smoke_tests
    
    # 顯示服務狀態
    show_status
    
    log_info ""
    log_info "========================================="
    log_info "✓ 部署完成！"
    log_info "========================================="
}

# 執行主函數
main
