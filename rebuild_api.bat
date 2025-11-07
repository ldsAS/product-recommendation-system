@echo off
echo ========================================
echo 重建推薦系統 API 容器
echo ========================================
echo.

echo 正在停止 API 容器...
docker-compose stop recommendation-api

echo.
echo 正在重建 API 容器...
docker-compose build recommendation-api

echo.
echo 正在啟動 API 容器...
docker-compose up -d recommendation-api

echo.
echo 等待容器啟動...
timeout /t 10 /nobreak >nul

echo.
echo 檢查容器狀態...
docker ps --filter "name=recommendation-api"

echo.
echo 查看容器日誌（最後 20 行）...
docker logs --tail 20 recommendation-api

echo.
echo ========================================
echo API 容器已重建完成！
echo ========================================
echo.
echo 請訪問: http://localhost:8000/trends
echo.
pause
