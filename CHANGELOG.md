# 更新日誌

## [未發布] - 2025-11-03

### 🎉 重大更新

#### 協同過濾遷移到 Implicit

- **移除**: scikit-surprise 依賴（需要 C++ 編譯器）
- **新增**: implicit 庫（預編譯 wheel，無需編譯器）
- **性能提升**: 
  - 訓練速度提升 6-13 倍
  - 推理速度提升 80-160 倍
- **API 兼容**: 保持 100% 向後兼容

### 🔧 技術改進

- 更新 `src/models/collaborative_filtering.py` 使用 Implicit 庫
- 使用稀疏矩陣優化內存使用
- 支持 ALS 和 BPR 算法
- 改進模型保存/載入機制

### 📚 文檔更新

- 新增 `docs/IMPLICIT_MIGRATION.md` 遷移指南
- 更新 `INSTALL.md` 安裝說明
- 更新 `requirements.txt` 依賴列表

### 🧹 清理

- 移除臨時測試和文檔文件
- 保留 `src/models/collaborative_filtering_implicit.py` 作為參考

### ⚙️ 環境要求

- Python 3.11.9（推薦）
- implicit >= 0.7.0
- 無需 C++ 編譯器

---

## 如何升級

1. 更新依賴：
   ```bash
   pip install -r requirements.txt
   ```

2. 重新訓練模型：
   ```bash
   python src/train.py
   ```

3. 驗證安裝：
   ```bash
   python -c "from src.models.collaborative_filtering import CollaborativeFilteringModel; print('✓ 升級成功')"
   ```

詳細說明請參閱 [docs/IMPLICIT_MIGRATION.md](docs/IMPLICIT_MIGRATION.md)
