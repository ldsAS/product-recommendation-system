Write-Host "============================================================"
Write-Host "  Recommendation System Verification Script"
Write-Host "============================================================"
Write-Host ""

# 1. Check Python
Write-Host "[1/4] Checking Python environment..."
try {
    $version = python --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Python check failed" }
    Write-Host "[OK] Python is installed: $version"
}
catch {
    Write-Host "[Error] Python not found. Please install Python and add it to PATH." -ForegroundColor Red
    Read-Host "Press Enter to exit..."
    exit 1
}

# 2. Install Dependencies
Write-Host ""
Write-Host "[2/4] Installing dependencies..."
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Error] Failed to install dependencies." -ForegroundColor Red
    Read-Host "Press Enter to exit..."
    exit 1
}
Write-Host "[OK] Dependencies installed"

# 3. Run Integration Tests
Write-Host ""
Write-Host "[3/4] Running integration tests (Data Processing & Model Training logic)..."
pytest tests/test_integration.py -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Error] Integration tests failed." -ForegroundColor Red
    Read-Host "Press Enter to exit..."
    exit 1
}
Write-Host "[OK] Integration tests passed"

# 4. Run API Tests
Write-Host ""
Write-Host "[4/4] Running API tests (Endpoint logic)..."
pytest tests/test_api_endpoints.py -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Error] API tests failed." -ForegroundColor Red
    Read-Host "Press Enter to exit..."
    exit 1
}
Write-Host "[OK] API tests passed"

# 5. Run Actual Training (Smoke Test)
Write-Host ""
Write-Host "[5/5] Running actual training smoke test..."
python src/train.py --max-rows 1000
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Error] Training script failed." -ForegroundColor Red
    Read-Host "Press Enter to exit..."
    exit 1
}
Write-Host "[OK] Training script executed successfully"

Write-Host ""
Write-Host "============================================================"
Write-Host "  Verification Complete! All tests passed."
Write-Host "============================================================"
Write-Host ""
Read-Host "Press Enter to exit..."
