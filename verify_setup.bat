@echo off
chcp 65001
echo ============================================================
echo   推薦系統驗證腳本
echo   Recommendation System Verification Script
echo ============================================================
echo.

REM 1. 檢查 Python
echo [1/4] 檢查 Python 環境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 找不到 Python。請確保已安裝 Python 並加入 PATH 環境變數。
    echo [Error] Python not found. Please install Python and add it to PATH.
    pause
    exit /b 1
)
echo [✓] Python 已安裝
python --version

REM 2. 安裝依賴
echo.
echo [2/4] 安裝依賴套件...
pip install -r requirements.txt
if errorlevel 1 (
    echo [錯誤] 安裝依賴失敗。
    echo [Error] Failed to install dependencies.
    pause
    exit /b 1
)
echo [✓] 依賴套件已安裝

REM 3. 執行整合測試
echo.
echo [3/4] 執行整合測試 (資料處理與模型訓練邏輯)...
pytest tests/test_integration.py -v
if errorlevel 1 (
    echo [錯誤] 整合測試失敗。
    echo [Error] Integration tests failed.
    pause
    exit /b 1
)
echo [✓] 整合測試通過

REM 4. 執行 API 測試
echo.
echo [4/4] 執行 API 測試 (端點邏輯)...
pytest tests/test_api_endpoints.py -v
if errorlevel 1 (
    echo [錯誤] API 測試失敗。
    echo [Error] API tests failed.
    pause
    exit /b 1
)
echo [✓] API 測試通過

REM 5. 執行實際訓練測試 (Smoke Test)
echo.
echo [5/5] 執行實際訓練測試 (Smoke Test)...
python src/train.py --max-rows 1000
if errorlevel 1 (
    echo [錯誤] 訓練腳本執行失敗。
    echo [Error] Training script failed.
    pause
    exit /b 1
)
echo [✓] 訓練腳本執行成功

echo.
echo ============================================================
echo   驗證完成！所有測試均通過。
echo   Verification Complete! All tests passed.
echo ============================================================
echo.
pause
