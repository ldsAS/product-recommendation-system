# GitHub 上傳指南

## 📋 前置準備

### 1. 確認 Git 已安裝
```bash
git --version
```

如果未安裝，請從 [git-scm.com](https://git-scm.com/) 下載安裝。

### 2. 配置 Git（首次使用）
```bash
git config --global user.name "您的名字"
git config --global user.email "您的郵箱"
```

---

## 🚀 上傳步驟

### 方式 1: 使用現有的 Git 倉庫（推薦）

#### 步驟 1: 檢查 Git 狀態
```bash
git status
```

#### 步驟 2: 添加所有檔案
```bash
git add .
```

#### 步驟 3: 提交變更
```bash
git commit -m "完成產品推薦系統 - 所有功能實作完成"
```

#### 步驟 4: 在 GitHub 上建立新倉庫

1. 登入 [GitHub](https://github.com)
2. 點擊右上角的 `+` → `New repository`
3. 填寫倉庫資訊：
   - **Repository name**: `product-recommendation-system`
   - **Description**: `基於機器學習的產品推薦系統`
   - **Public** 或 **Private**: 根據需求選擇
   - **不要**勾選 "Initialize this repository with a README"
4. 點擊 `Create repository`

#### 步驟 5: 連接遠端倉庫
```bash
# 替換 YOUR_USERNAME 為您的 GitHub 使用者名稱
git remote add origin https://github.com/YOUR_USERNAME/product-recommendation-system.git
```

#### 步驟 6: 推送到 GitHub
```bash
# 首次推送
git push -u origin main

# 如果分支名稱是 master
git push -u origin master
```

如果遇到分支名稱問題，可以重命名分支：
```bash
git branch -M main
git push -u origin main
```

---

### 方式 2: 重新初始化 Git 倉庫

如果需要重新開始：

#### 步驟 1: 刪除現有 Git 倉庫（謹慎操作）
```bash
# Windows PowerShell
Remove-Item -Recurse -Force .git

# Linux/macOS
rm -rf .git
```

#### 步驟 2: 初始化新倉庫
```bash
git init
```

#### 步驟 3: 添加檔案
```bash
git add .
```

#### 步驟 4: 首次提交
```bash
git commit -m "Initial commit: 產品推薦系統完整實作"
```

#### 步驟 5: 連接 GitHub（同方式 1 的步驟 4-6）

---

## 📝 建議的提交訊息

### 首次提交
```bash
git commit -m "Initial commit: 產品推薦系統完整實作

- 完成所有 30 個任務
- 實作資料處理管線
- 實作模型訓練系統
- 實作推薦引擎
- 實作 API 服務
- 實作監控和日誌系統
- 實作測試套件
- 完成 400+ 頁文檔"
```

### 後續提交範例
```bash
# 修復 bug
git commit -m "fix: 修正推薦引擎的特徵提取問題"

# 新增功能
git commit -m "feat: 新增深度學習推薦模型"

# 更新文檔
git commit -m "docs: 更新 API 使用指南"

# 效能優化
git commit -m "perf: 優化推薦回應時間"
```

---

## 🔐 使用 SSH（推薦）

### 1. 生成 SSH 金鑰
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

### 2. 複製公鑰
```bash
# Windows
type ~/.ssh/id_ed25519.pub

# Linux/macOS
cat ~/.ssh/id_ed25519.pub
```

### 3. 添加到 GitHub
1. 登入 GitHub
2. 點擊右上角頭像 → `Settings`
3. 左側選單選擇 `SSH and GPG keys`
4. 點擊 `New SSH key`
5. 貼上公鑰，點擊 `Add SSH key`

### 4. 使用 SSH URL
```bash
git remote set-url origin git@github.com:YOUR_USERNAME/product-recommendation-system.git
```

---

## 📦 上傳前檢查清單

### ✅ 必須檢查的項目

- [ ] `.gitignore` 已建立（避免上傳敏感資料）
- [ ] 移除或加密敏感資訊（API keys, 密碼等）
- [ ] 確認 `.env` 檔案不會被上傳
- [ ] 確認大型資料檔案不會被上傳
- [ ] 確認模型檔案不會被上傳（太大）
- [ ] README.md 已更新
- [ ] 文檔已完成

### ✅ 建議檢查的項目

- [ ] 程式碼已格式化
- [ ] 測試已通過
- [ ] 文檔已更新
- [ ] CHANGELOG 已更新（如果有）

---

## 🔍 常見問題

### Q1: 推送時要求輸入使用者名稱和密碼

**A**: GitHub 已不再支援密碼驗證，請使用以下方式之一：

1. **使用 Personal Access Token (PAT)**
   - 前往 GitHub Settings → Developer settings → Personal access tokens
   - 生成新 token
   - 使用 token 作為密碼

2. **使用 SSH**（推薦）
   - 參考上面的 SSH 設定步驟

### Q2: 檔案太大無法推送

**A**: 
```bash
# 檢查大檔案
git ls-files -z | xargs -0 du -h | sort -h | tail -20

# 移除大檔案
git rm --cached path/to/large/file

# 更新 .gitignore
echo "path/to/large/file" >> .gitignore

# 重新提交
git commit --amend
```

### Q3: 推送被拒絕（rejected）

**A**:
```bash
# 先拉取遠端變更
git pull origin main --rebase

# 再推送
git push origin main
```

### Q4: 想要排除某些檔案

**A**: 編輯 `.gitignore` 檔案，添加要排除的檔案或目錄。

---

## 📚 後續維護

### 日常工作流程

```bash
# 1. 拉取最新變更
git pull

# 2. 建立新分支（開發新功能）
git checkout -b feature/new-feature

# 3. 進行開發...

# 4. 提交變更
git add .
git commit -m "feat: 新功能描述"

# 5. 推送分支
git push origin feature/new-feature

# 6. 在 GitHub 上建立 Pull Request

# 7. 合併後切回主分支
git checkout main
git pull
```

### 查看歷史記錄

```bash
# 查看提交歷史
git log --oneline --graph --all

# 查看特定檔案的歷史
git log --follow path/to/file
```

### 撤銷變更

```bash
# 撤銷未提交的變更
git checkout -- file.py

# 撤銷最後一次提交（保留變更）
git reset --soft HEAD~1

# 撤銷最後一次提交（丟棄變更）
git reset --hard HEAD~1
```

---

## 🎯 建議的倉庫設定

### README.md 徽章

在 README.md 頂部添加徽章：

```markdown
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-production-success.svg)
```

### GitHub Topics

在倉庫設定中添加 topics：
- `machine-learning`
- `recommendation-system`
- `python`
- `fastapi`
- `lightgbm`
- `collaborative-filtering`
- `product-recommendation`

### 啟用 GitHub Pages（可選）

如果想要展示文檔：
1. 前往倉庫 Settings → Pages
2. Source 選擇 `main` 分支的 `/docs` 目錄
3. 點擊 Save

---

## 📞 需要幫助？

如果遇到問題：

1. 查看 [GitHub 官方文檔](https://docs.github.com/)
2. 查看 [Git 官方文檔](https://git-scm.com/doc)
3. 搜尋 [Stack Overflow](https://stackoverflow.com/)

---

**祝您上傳順利！** 🚀
