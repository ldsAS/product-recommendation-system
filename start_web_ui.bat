@echo off
echo ============================================================
echo 啟動產品推薦系統 Web UI
echo ============================================================
echo.
echo 正在啟動服務...
echo.
echo 使用虛擬環境啟動...
echo.
.\venv\Scripts\uvicorn src.api.main:app --host 0.0.0.0 --port 8000
