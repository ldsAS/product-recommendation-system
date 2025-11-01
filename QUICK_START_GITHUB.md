# 🚀 快速上傳到 GitHub

## 最簡單的方式（3 步驟）

### 步驟 1: 在 GitHub 建立新倉庫

1. 前往 https://github.com/new
2. 填寫資訊：
   - Repository name: `product-recommendation-system`
   - Description: `基於機器學習的產品推薦系統`
   - 選擇 Public 或 Private
   - **不要**勾選任何初始化選項
3. 點擊 `Create repository`
4. **複製**倉庫 URL（例如：`https://github.com/你的使用者名稱/product-recommendation-system.git`）

### 步驟 2: 執行上傳腳本

#### Windows 使用者：
```powershell
.\scripts\upload_to_github.ps1
```

#### Linux/macOS 使用者：
```bash
chmod +x scripts/upload_to_github.sh
./scripts/upload_to_github.sh
```

### 步驟 3: 按照提示操作

腳本會引導您：
1. 配置 Git 使用者資訊（如果需要）
2. 輸入提交訊息
3. 輸入 GitHub 倉庫 URL
4. 自動推送到 GitHub

---

## 手動上傳（如果腳本無法使用）

### 1. 配置 Git（首次使用）
```bash
git config --global user.name "您的名字"
git config --global user.email "您的郵箱"
```

### 2. 檢查 Git 狀態
```bash
git status
```

### 3. 添加所有檔案
```bash
git add .
```

### 4. 提交變更
```bash
git commit -m "Initial commit: 產品推薦系統完整實作"
```

### 5. 連接 GitHub 倉庫
```bash
# 替換成您的倉庫 URL
git remote add origin https://github.com/您的使用者名稱/product-recommendation-system.git
```

### 6. 推送到 GitHub
```bash
git branch -M main
git push -u origin main
```

---

## 常見問題

### ❓ 推送時要求輸入密碼

GitHub 不再支援密碼驗證，請使用以下方式之一：

**方式 1: Personal Access Token**
1. 前往 GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 點擊 `Generate new token (classic)`
3. 勾選 `repo` 權限
4. 生成並複製 token
5. 推送時使用 token 作為密碼

**方式 2: GitHub Desktop**
- 下載 [GitHub Desktop](https://desktop.github.com/)
- 使用圖形介面操作

### ❓ 檔案太大無法推送

檢查 `.gitignore` 是否正確配置：
- 資料檔案（`data/raw/*.csv`）
- 模型檔案（`data/models/*.pkl`）
- 日誌檔案（`logs/*.log`）

這些大檔案應該被排除。

### ❓ 推送被拒絕

```bash
# 先拉取遠端變更
git pull origin main --rebase

# 再推送
git push origin main
```

---

## 📚 詳細說明

完整的上傳指南請參考：[GITHUB_UPLOAD_GUIDE.md](GITHUB_UPLOAD_GUIDE.md)

---

## ✅ 上傳後檢查

上傳成功後，您應該能在 GitHub 上看到：

- ✅ 所有原始碼檔案
- ✅ 文檔檔案（README.md, docs/）
- ✅ 測試檔案（tests/）
- ✅ 配置檔案（requirements.txt, Dockerfile 等）
- ❌ 資料檔案（已被 .gitignore 排除）
- ❌ 模型檔案（已被 .gitignore 排除）
- ❌ 日誌檔案（已被 .gitignore 排除）

---

**祝您上傳順利！** 🎉

如有問題，請參考 [GITHUB_UPLOAD_GUIDE.md](GITHUB_UPLOAD_GUIDE.md) 獲取更多幫助。
