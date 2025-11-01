# 📦 安裝指南

本文件提供詳細的安裝步驟和疑難排解方案。

## ⚡ 快速安裝（推薦）

適合大多數使用者的快速安裝流程。

### 前置需求檢查

```bash
# 檢查 Python 版本（需要 3.9+）
python --version

# 檢查 pip 版本
pip --version

# 如果 pip 版本過舊，請升級
python -m pip install --upgrade pip
```

### 步驟 1: 建立虛擬環境

**強烈建議使用虛擬環境**，避免套件衝突。

```bash
# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 確認虛擬環境已啟動（命令提示字元前會顯示 (venv)）
```

### 步驟 2: 安裝依賴套件

```bash
# 一鍵安裝所有依賴
pip install -r requirements.txt
```

這將安裝以下核心套件：
- **資料處理**: pandas, numpy, pyarrow
- **資料驗證**: pydantic, pydantic-settings
- **Web 框架**: FastAPI, uvicorn
- **機器學習**: LightGBM, XGBoost, scikit-learn
- **測試工具**: pytest, pytest-asyncio
- **其他工具**: python-dotenv, python-multipart

### 步驟 3: 驗證安裝

```bash
# 驗證核心套件
python -c "import pandas, fastapi, lightgbm; print('✅ 安裝成功！')"

# 執行完整驗證腳本
python scripts/verify_models.py

# 驗證配置載入
python -c "from src.config import settings; print(f'✅ 配置載入成功！版本: {settings.MODEL_VERSION}')"
```

### 步驟 4: 配置環境變數

```bash
# 複製環境變數範本
cp .env.example .env

# 使用文字編輯器編輯 .env 檔案
# Windows: notepad .env
# Linux/Mac: nano .env 或 vim .env
```

主要配置項：
```env
MODEL_VERSION=v1.0.0
MODEL_TYPE=lightgbm
LOG_LEVEL=INFO
ENABLE_CACHE=false
TOP_K_RECOMMENDATIONS=5
```

## 分步安裝（如果遇到問題）

### 核心套件

```bash
# 資料處理
pip install pandas>=2.0.0 numpy>=1.24.0 pyarrow>=12.0.0

# 資料驗證
pip install pydantic>=2.0.0 pydantic-settings>=2.0.0

# Web 框架
pip install fastapi>=0.104.0 uvicorn[standard]>=0.24.0

# 機器學習
pip install scikit-learn>=1.3.0 lightgbm>=4.0.0
```

### 可選套件

```bash
# XGBoost (可選，如果 LightGBM 不夠用)
pip install xgboost>=2.0.0

# 協同過濾 (可選)
pip install scikit-surprise>=1.1.3

# Redis (可選，用於快取)
pip install redis>=5.0.0

# 測試工具
pip install pytest>=7.4.0 pytest-asyncio>=0.21.0
```

## 驗證安裝

### 檢查 Python 版本

```bash
python --version
```

應該顯示 Python 3.9 或更高版本。

### 檢查套件安裝

```bash
python -c "import pandas; print('pandas:', pandas.__version__)"
python -c "import pydantic; print('pydantic:', pydantic.__version__)"
python -c "import fastapi; print('fastapi:', fastapi.__version__)"
python -c "import lightgbm; print('lightgbm:', lightgbm.__version__)"
```

### 執行驗證腳本

```bash
# 驗證資料模型
python scripts/verify_models.py

# 驗證配置
python src/config.py
```

## ❓ 常見問題與解決方案

### 問題 1: pip 安裝失敗或速度很慢

**症狀**: `pip install` 失敗或下載速度極慢

**解決方案**:

```bash
# 方案 1: 升級 pip
python -m pip install --upgrade pip

# 方案 2: 使用國內鏡像源（中國地區）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 方案 3: 使用代理
pip install -r requirements.txt --proxy http://your-proxy:port
```

### 問題 2: 某些套件安裝失敗

**症狀**: 部分套件安裝時出現錯誤

**解決方案**:

```bash
# 方案 1: 分別安裝核心套件
pip install pandas numpy
pip install pydantic pydantic-settings
pip install fastapi uvicorn
pip install scikit-learn lightgbm

# 方案 2: 跳過有問題的套件，稍後手動安裝
pip install -r requirements.txt --no-deps
pip install <problem-package> --no-cache-dir

# 方案 3: 使用預編譯的二進位檔案
pip install <package-name> --prefer-binary
```

### 問題 3: Windows 上 LightGBM 安裝失敗

**症狀**: `error: Microsoft Visual C++ 14.0 is required`

**解決方案**:

```bash
# 方案 1: 使用預編譯的 wheel（推薦）
pip install lightgbm --prefer-binary

# 方案 2: 從 conda 安裝
conda install -c conda-forge lightgbm

# 方案 3: 安裝 Visual C++ Build Tools
# 下載並安裝: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

### 問題 4: macOS 上編譯錯誤

**症狀**: `clang: error` 或 `fatal error: 'Python.h' file not found`

**解決方案**:

```bash
# 安裝 Xcode Command Line Tools
xcode-select --install

# 使用 Homebrew 安裝 Python（如果尚未安裝）
brew install python@3.9

# 重新安裝套件
pip install -r requirements.txt
```

### 問題 5: Linux 上缺少系統依賴

**症狀**: 安裝時提示缺少系統庫

**解決方案**:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-dev build-essential

# CentOS/RHEL
sudo yum install python3-devel gcc gcc-c++

# 重新安裝
pip install -r requirements.txt
```

### 問題 6: 記憶體不足

**症狀**: 安裝過程中系統變慢或崩潰

**解決方案**:

```bash
# 方案 1: 分批安裝，避免同時編譯多個套件
pip install pandas numpy
pip install scikit-learn
pip install lightgbm

# 方案 2: 限制 pip 使用的記憶體
pip install -r requirements.txt --no-cache-dir

# 方案 3: 增加系統交換空間（Linux）
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 問題 7: 虛擬環境無法啟動

**症狀**: `activate` 命令無效或報錯

**解決方案**:

```bash
# Windows PowerShell 執行策略問題
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 或使用 cmd 而非 PowerShell
venv\Scripts\activate.bat

# Linux/Mac 權限問題
chmod +x venv/bin/activate
source venv/bin/activate
```

### 問題 8: 套件版本衝突

**症狀**: `ERROR: pip's dependency resolver does not currently take into account...`

**解決方案**:

```bash
# 方案 1: 使用 --use-deprecated=legacy-resolver
pip install -r requirements.txt --use-deprecated=legacy-resolver

# 方案 2: 建立全新的虛擬環境
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate  # 或 venv\Scripts\activate
pip install -r requirements.txt

# 方案 3: 手動解決衝突
pip install <package>==<specific-version>
```

## 🔧 進階安裝選項

### 使用 Conda（替代方案）

如果您偏好使用 Conda 管理環境：

```bash
# 建立 conda 環境
conda create -n recommendation python=3.9 -y

# 啟動環境
conda activate recommendation

# 安裝部分套件（從 conda-forge）
conda install -c conda-forge pandas numpy scikit-learn lightgbm -y

# 安裝其餘套件（從 pip）
pip install fastapi uvicorn pydantic pydantic-settings

# 或直接使用 pip 安裝所有套件
pip install -r requirements.txt
```

### Docker 安裝（未來支援）

Docker 容器化部署正在開發中，敬請期待。

### 開發環境額外套件

如果您要參與開發，建議安裝以下額外工具：

```bash
# 程式碼格式化與檢查
pip install black flake8 isort mypy

# Jupyter Notebook（用於資料探索）
pip install jupyter notebook ipykernel

# 測試覆蓋率報告
pip install pytest-cov

# 效能分析工具
pip install memory-profiler line-profiler
```

## ✅ 安裝驗證清單

完成安裝後，請執行以下檢查：

- [ ] Python 版本 ≥ 3.9
- [ ] 虛擬環境已啟動
- [ ] 所有依賴套件已安裝
- [ ] 核心套件可正常導入（pandas, fastapi, lightgbm）
- [ ] 環境變數檔案已配置（.env）
- [ ] 驗證腳本執行成功

### 完整驗證命令

```bash
# 1. 檢查 Python 版本
python --version

# 2. 檢查虛擬環境
which python  # Linux/Mac
where python  # Windows

# 3. 測試核心套件導入
python -c "import pandas, numpy, fastapi, lightgbm, pydantic; print('✅ 所有核心套件正常')"

# 4. 執行驗證腳本
python scripts/verify_models.py

# 5. 測試配置載入
python -c "from src.config import settings; print(f'✅ 配置正常，模型版本: {settings.MODEL_VERSION}')"

# 6. 執行簡單測試
pytest tests/test_data_models.py -v
```

如果所有檢查都通過，恭喜您已成功完成安裝！

## 📚 下一步

安裝完成後，您可以：

1. **準備資料**: 將訓練資料放入 `data/raw/` 目錄
2. **訓練模型**: 執行 `python src/train.py`
3. **啟動服務**: 執行 `python src/api/main.py`
4. **查看文件**: 閱讀 [README.md](README.md) 了解詳細使用方法

## 🆘 需要協助？

如果遇到本文件未涵蓋的問題：

1. 查看 [README.md](README.md) 的疑難排解章節
2. 搜尋 [GitHub Issues](https://github.com/ldsAS/product-recommendation-system/issues)
3. 提交新的 Issue 並附上：
   - 作業系統和版本
   - Python 版本
   - 完整的錯誤訊息
   - 已嘗試的解決方案

---

**祝安裝順利！** 🎉
