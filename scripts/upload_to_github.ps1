# GitHub 上傳腳本（Windows PowerShell）

Write-Host "========================================"
Write-Host "GitHub 上傳腳本"
Write-Host "========================================"

# 檢查 Git 是否安裝
try {
    git --version | Out-Null
    Write-Host "✓ Git 已安裝" -ForegroundColor Green
} catch {
    Write-Host "錯誤: Git 未安裝" -ForegroundColor Red
    Write-Host "請從 https://git-scm.com/ 下載安裝"
    exit 1
}

# 檢查是否已初始化 Git
if (-not (Test-Path ".git")) {
    Write-Host "初始化 Git 倉庫..."
    git init
    Write-Host "✓ Git 倉庫初始化完成" -ForegroundColor Green
}

# 檢查 Git 配置
$username = git config user.name
if ([string]::IsNullOrEmpty($username)) {
    $username = Read-Host "請輸入您的 Git 使用者名稱"
    git config user.name $username
}

$email = git config user.email
if ([string]::IsNullOrEmpty($email)) {
    $email = Read-Host "請輸入您的 Git 郵箱"
    git config user.email $email
}

Write-Host "✓ Git 配置完成" -ForegroundColor Green
Write-Host "  使用者: $username"
Write-Host "  郵箱: $email"

# 添加所有檔案
Write-Host ""
Write-Host "添加檔案到 Git..."
git add .
Write-Host "✓ 檔案添加完成" -ForegroundColor Green

# 顯示狀態
Write-Host ""
Write-Host "Git 狀態:"
git status --short

# 提交
Write-Host ""
$commitMsg = Read-Host "請輸入提交訊息 (按 Enter 使用預設訊息)"
if ([string]::IsNullOrEmpty($commitMsg)) {
    $commitMsg = "Initial commit: 產品推薦系統完整實作"
}

git commit -m $commitMsg
Write-Host "✓ 提交完成" -ForegroundColor Green

# 詢問 GitHub 倉庫 URL
Write-Host ""
Write-Host "========================================"
Write-Host "請在 GitHub 上建立新倉庫"
Write-Host "========================================"
Write-Host "1. 前往 https://github.com/new"
Write-Host "2. 建立名為 'product-recommendation-system' 的倉庫"
Write-Host "3. 不要勾選 'Initialize this repository with a README'"
Write-Host "4. 複製倉庫 URL"
Write-Host ""
$repoUrl = Read-Host "請輸入 GitHub 倉庫 URL (例如: https://github.com/username/repo.git)"

if ([string]::IsNullOrEmpty($repoUrl)) {
    Write-Host "錯誤: 未提供倉庫 URL" -ForegroundColor Red
    exit 1
}

# 添加遠端倉庫
Write-Host ""
Write-Host "連接遠端倉庫..."
git remote add origin $repoUrl 2>$null
if ($LASTEXITCODE -ne 0) {
    git remote set-url origin $repoUrl
}
Write-Host "✓ 遠端倉庫連接完成" -ForegroundColor Green

# 確認分支名稱
$currentBranch = git branch --show-current
if ($currentBranch -ne "main") {
    Write-Host "重命名分支為 main..."
    git branch -M main
}

# 推送到 GitHub
Write-Host ""
Write-Host "推送到 GitHub..."
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================"
    Write-Host "✓ 上傳成功！" -ForegroundColor Green
    Write-Host "========================================"
    Write-Host "您的專案已上傳到: $repoUrl"
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================"
    Write-Host "✗ 上傳失敗" -ForegroundColor Red
    Write-Host "========================================"
    Write-Host "請檢查:"
    Write-Host "1. GitHub 倉庫 URL 是否正確"
    Write-Host "2. 是否有權限推送到該倉庫"
    Write-Host "3. 網路連接是否正常"
    Write-Host ""
    Write-Host "詳細說明請參考 GITHUB_UPLOAD_GUIDE.md"
}

Write-Host ""
Write-Host "按任意鍵退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
