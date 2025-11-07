@echo off
REM ============================================================================
REM 推薦系統 Docker 一鍵部署腳本 (Windows)
REM Recommendation System Docker Quick Start Script
REM ============================================================================

echo.
echo ============================================================
echo   推薦系統 Docker 一鍵部署
echo   Recommendation System Docker Quick Start
echo ============================================================
echo.

REM 檢查 Docker 是否安裝
echo [1/6] 檢查 Docker 環境...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] Docker 未安裝或未啟動
    echo 請先安裝 Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo [✓] Docker 已安裝

REM 檢查 Docker Compose 是否可用
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] Docker Compose 不可用
    pause
    exit /b 1
)
echo [✓] Docker Compose 可用

REM 檢查 .env 文件
echo.
echo [2/6] 檢查環境變數配置...
if not exist .env (
    echo [警告] .env 文件不存在
    echo 正在從 .env.example 複製...
    copy .env.example .env
    echo.
    echo [重要] 請編輯 .env 文件並設置以下變數:
    echo   - DB_PASSWORD: 資料庫密碼
    echo   - REDIS_PASSWORD: Redis 密碼
    echo   - GRAFANA_PASSWORD: Grafana 密碼
    echo.
    set /p continue="是否已完成配置? (y/n): "
    if /i not "%continue%"=="y" (
        echo 請先配置 .env 文件後再執行此腳本
        notepad .env
        pause
        exit /b 1
    )
) else (
    echo [✓] .env 文件已存在
)

REM 檢查模型文件
echo.
echo [3/6] 檢查模型文件...
if exist data\models\v1.0.0\model.pkl (
    echo [✓] 模型文件已存在
) else (
    echo [警告] 模型文件不存在
    echo 首次啟動後需要訓練模型
    echo 訓練命令: docker-compose exec recommendation-api python src/train.py
)

REM 停止舊服務（如果存在）
echo.
echo [4/6] 停止舊服務...
docker-compose down >nul 2>&1
echo [✓] 舊服務已停止

REM 啟動服務
echo.
echo [5/6] 啟動 Docker 服務...
echo 這可能需要幾分鐘時間（首次啟動需要下載映像）...
docker-compose up -d

if errorlevel 1 (
    echo [錯誤] 服務啟動失敗
    echo 請查看錯誤訊息並檢查配置
    pause
    exit /b 1
)

echo [✓] 服務已啟動

REM 等待服務就緒
echo.
echo [6/6] 等待服務就緒...
timeout /t 10 /nobreak >nul

set MAX_RETRIES=30
set RETRY_COUNT=0

:wait_loop
curl -f http://localhost:8000/health >nul 2>&1
if not errorlevel 1 (
    echo [✓] API 服務就緒
    goto services_ready
)

set /a RETRY_COUNT+=1
if %RETRY_COUNT% geq %MAX_RETRIES% (
    echo [錯誤] API 服務啟動超時
    echo 請查看日誌: docker-compose logs recommendation-api
    pause
    exit /b 1
)

echo 等待 API 服務啟動... (%RETRY_COUNT%/%MAX_RETRIES%)
timeout /t 2 /nobreak >nul
goto wait_loop

:services_ready

REM 顯示服務狀態
echo.
echo ============================================================
echo   部署完成！
echo ============================================================
echo.
echo 服務狀態:
docker-compose ps
echo.
echo ============================================================
echo   訪問地址
echo ============================================================
echo.
echo   主頁面:          http://localhost:8000
echo   API 文檔:        http://localhost:8000/docs
echo   監控儀表板:      http://localhost:8000/dashboard
echo   趨勢分析:        http://localhost:8000/trends
echo   Prometheus:      http://localhost:9090
echo   Grafana:         http://localhost:3000
echo.
echo ============================================================
echo   常用命令
echo ============================================================
echo.
echo   查看日誌:        docker-compose logs -f
echo   停止服務:        docker-compose down
echo   重啟服務:        docker-compose restart
echo   查看狀態:        docker-compose ps
echo.
echo ============================================================
echo   下一步
echo ============================================================
echo.
echo   1. 在瀏覽器中打開: http://localhost:8000
echo   2. 輸入測試資料獲取推薦
echo   3. 查看監控儀表板: http://localhost:8000/dashboard
echo.
echo   如果模型文件不存在，請執行:
echo   docker-compose exec recommendation-api python src/train.py
echo.
echo ============================================================

REM 詢問是否打開瀏覽器
set /p open_browser="是否在瀏覽器中打開主頁面? (y/n): "
if /i "%open_browser%"=="y" (
    start http://localhost:8000
)

echo.
pause
