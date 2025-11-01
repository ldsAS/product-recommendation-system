# GitHub 倉庫設定指南

本文件說明如何設定 GitHub 倉庫的各項功能。

## 啟用 GitHub Discussions

GitHub Discussions 是一個社群討論功能，適合用於：
- 一般問答
- 功能討論
- 想法分享
- 社群交流

### 啟用步驟

1. **前往倉庫設定**
   - 開啟您的 GitHub 倉庫頁面
   - 點擊右上角的 "Settings" 按鈕

2. **啟用 Discussions 功能**
   - 在左側選單中，找到 "General" 分類
   - 向下捲動到 "Features" 區塊
   - 勾選 "Discussions" 選項
   - 點擊 "Set up discussions" 按鈕

3. **初始化 Discussions**
   - GitHub 會自動創建一個歡迎貼文
   - 您可以編輯或刪除這個預設貼文
   - 可以自訂討論分類（Categories）

4. **自訂討論分類（可選）**
   
   建議的分類設定：
   - **💡 Ideas** - 新功能想法和建議
   - **❓ Q&A** - 問題與解答
   - **🙏 Show and tell** - 分享使用經驗
   - **📣 Announcements** - 重要公告
   - **🐛 General** - 一般討論

### 驗證設定

啟用後，您可以透過以下 URL 訪問 Discussions：
```
https://github.com/ldsAS/product-recommendation-system/discussions
```

倉庫頂部也會出現 "Discussions" 標籤頁。

## 其他建議設定

### 1. 設定 Issue 模板

創建 `.github/ISSUE_TEMPLATE/` 目錄，添加以下模板：

**bug_report.md** - Bug 回報模板
**feature_request.md** - 功能需求模板

### 2. 設定 Pull Request 模板

創建 `.github/pull_request_template.md` 檔案。

### 3. 啟用 GitHub Actions

在 Settings → Actions → General 中：
- 允許所有 actions 和可重用的工作流程
- 設定工作流程權限

### 4. 設定分支保護規則

在 Settings → Branches 中：
- 保護 `main` 分支
- 要求 PR 審查
- 要求狀態檢查通過

### 5. 設定 GitHub Pages（可選）

如果要部署文檔網站：
- Settings → Pages
- 選擇來源分支（通常是 `main` 或 `gh-pages`）
- 選擇目錄（`/docs` 或 `/`）

## 社群健康檔案

建議在 `.github/` 目錄中添加：

- `CODE_OF_CONDUCT.md` - 行為準則
- `CONTRIBUTING.md` - 貢獻指南
- `SECURITY.md` - 安全政策
- `SUPPORT.md` - 支援資訊

這些檔案會自動顯示在倉庫的社群標準頁面。

## 參考資源

- [GitHub Discussions 文檔](https://docs.github.com/en/discussions)
- [設定 Issue 模板](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests)
- [關於社群健康檔案](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions)

---

**最後更新**: 2025-11-01
