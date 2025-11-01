#!/bin/bash
# GitHub 上傳腳本（Linux/macOS）

echo "========================================"
echo "GitHub 上傳腳本"
echo "========================================"

# 檢查 Git 是否安裝
if ! command -v git &> /dev/null; then
    echo "錯誤: Git 未安裝"
    echo "請從 https://git-scm.com/ 下載安裝"
    exit 1
fi

echo "✓ Git 已安裝"

# 檢查是否已初始化 Git
if [ ! -d ".git" ]; then
    echo "初始化 Git 倉庫..."
    git init
    echo "✓ Git 倉庫初始化完成"
fi

# 檢查 Git 配置
if [ -z "$(git config user.name)" ]; then
    echo ""
    read -p "請輸入您的 Git 使用者名稱: " username
    git config user.name "$username"
fi

if [ -z "$(git config user.email)" ]; then
    echo ""
    read -p "請輸入您的 Git 郵箱: " email
    git config user.email "$email"
fi

echo "✓ Git 配置完成"
echo "  使用者: $(git config user.name)"
echo "  郵箱: $(git config user.email)"

# 添加所有檔案
echo ""
echo "添加檔案到 Git..."
git add .
echo "✓ 檔案添加完成"

# 顯示狀態
echo ""
echo "Git 狀態:"
git status --short

# 提交
echo ""
read -p "請輸入提交訊息 (預設: 'Initial commit: 產品推薦系統完整實作'): " commit_msg
commit_msg=${commit_msg:-"Initial commit: 產品推薦系統完整實作"}

git commit -m "$commit_msg"
echo "✓ 提交完成"

# 詢問 GitHub 倉庫 URL
echo ""
echo "========================================"
echo "請在 GitHub 上建立新倉庫"
echo "========================================"
echo "1. 前往 https://github.com/new"
echo "2. 建立名為 'product-recommendation-system' 的倉庫"
echo "3. 不要勾選 'Initialize this repository with a README'"
echo "4. 複製倉庫 URL"
echo ""
read -p "請輸入 GitHub 倉庫 URL (例如: https://github.com/username/repo.git): " repo_url

if [ -z "$repo_url" ]; then
    echo "錯誤: 未提供倉庫 URL"
    exit 1
fi

# 添加遠端倉庫
echo ""
echo "連接遠端倉庫..."
git remote add origin "$repo_url" 2>/dev/null || git remote set-url origin "$repo_url"
echo "✓ 遠端倉庫連接完成"

# 確認分支名稱
current_branch=$(git branch --show-current)
if [ "$current_branch" != "main" ]; then
    echo "重命名分支為 main..."
    git branch -M main
fi

# 推送到 GitHub
echo ""
echo "推送到 GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "✓ 上傳成功！"
    echo "========================================"
    echo "您的專案已上傳到: $repo_url"
    echo ""
else
    echo ""
    echo "========================================"
    echo "✗ 上傳失敗"
    echo "========================================"
    echo "請檢查:"
    echo "1. GitHub 倉庫 URL 是否正確"
    echo "2. 是否有權限推送到該倉庫"
    echo "3. 網路連接是否正常"
    echo ""
    echo "詳細說明請參考 GITHUB_UPLOAD_GUIDE.md"
fi
