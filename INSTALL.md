# 安裝指南

## 快速安裝

### 1. 安裝 Python 依賴套件

```bash
pip install -r requirements.txt
```

這將安裝所有必要的套件，包括：
- pandas, numpy (資料處理)
- pydantic (資料驗證)
- fastapi, uvicorn (Web 框架)
- lightgbm, xgboost (機器學習)
- scikit-learn (機器學習基礎)
- 以及其他依賴

### 2. 驗證安裝

驗證資料模型是否正常：
```bash
python scripts/verify_models.py
```

驗證配置是否正常：
```bash
python src/config.py
```

### 3. 配置環境變數

```bash
cp .env.example .env
```

編輯 `.env` 檔案，根據需要調整配置。

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

## 常見問題

### 問題 1: pip 安裝失敗

**解決方案**: 升級 pip
```bash
python -m pip install --upgrade pip
```

### 問題 2: 某些套件安裝失敗

**解決方案**: 分別安裝
```bash
pip install pandas
pip install pydantic
pip install fastapi
```

### 問題 3: Windows 上 LightGBM 安裝失敗

**解決方案**: 使用預編譯的 wheel
```bash
pip install lightgbm --prefer-binary
```

或從 conda 安裝：
```bash
conda install -c conda-forge lightgbm
```

### 問題 4: 記憶體不足

**解決方案**: 
- 使用虛擬環境
- 分批安裝套件
- 增加系統記憶體

## 開發環境設置

### 使用虛擬環境（強烈建議）

```bash
# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

### 使用 conda（替代方案）

```bash
# 建立 conda 環境
conda create -n recommendation python=3.9

# 啟動環境
conda activate recommendation

# 安裝依賴
pip install -r requirements.txt
```

## 下一步

安裝完成後，請參考 [README.md](README.md) 開始使用系統。
