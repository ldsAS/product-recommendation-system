@echo off
echo ========================================
echo 重啟推薦系統 API 容器
echo ========================================
echo.

echo 正在重啟 recommendation-api 容器...
docker restart recommendation-api

echo.
echo 等待容器啟動...
timeout /t 5 /nobreak >nul

echo.
echo 檢查容器狀態...
docker ps --filter "name=recommendation-api"

echo.
echo ========================================
echo API 容器已重啟完成！
echo ========================================
echo.
echo 請訪問: http://localhost:8000/trends
echo.
pause
