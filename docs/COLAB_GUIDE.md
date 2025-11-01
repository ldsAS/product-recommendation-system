# 🚀 Google Colab 快速開始指南

本指南說明如何在 Google Colab 上運行產品推薦系統。

## 📋 為什麼使用 Colab？

- ✅ **免費 GPU/TPU**: 加速模型訓練
- ✅ **無需安裝**: 瀏覽器即可運行
- ✅ **易於分享**: 一鍵分享給團隊
- ✅ **快速測試**: 立即驗證系統功能

## 🎯 快速開始

### 方式 1: 使用預製 Notebook（推薦）

1. **開啟 Colab Notebook**
   
   點擊下方按鈕直接開啟：
   
   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ldsAS/product-recommendation-system/blob/main/notebooks/colab_demo.ipynb)

2. **執行所有儲存格**
   
   點擊選單：`Runtime` → `Run all`

3. **查看結果**
   
   Notebook 會自動：
   - 安裝依賴套件
   - 克隆專案
   - 創建示範資料
   - 訓練模型
   - 生成推薦結果

### 方式 2: 手動設置

如果您想要更多控制，可以手動執行以下步驟：

#### 步驟 1: 創建新的 Colab Notebook

前往 [Google Colab](https://colab.research.google.com/) 並創建新的 Notebook。

#### 步驟 2: 安裝依賴

```python
!pip install pandas numpy scikit-learn lightgbm pydantic pydantic-settings python-dotenv
```

#### 步驟 3: 克隆專案

```python
!git clone https://github.com/ldsAS/product-recommendation-system.git
%cd product-recommendation-system
```

#### 步驟 4: 準備資料

**選項 A: 使用示範資料**

```python
# 執行示範資料生成腳本
!python scripts/generate_demo_data.py
```

**選項 B: 上傳您的資料**

```python
from google.colab import files
import shutil

# 上傳資料檔案
uploaded = files.upload()

# 移動到正確位置
for filename in uploaded.keys():
    shutil.move(filename, f'data/raw/{filename}')
```

#### 步驟 5: 訓練模型

```python
!python src/train.py
```

#### 步驟 6: 測試推薦

```python
import sys
sys.path.insert(0, '/content/product-recommendation-system')

from src.models.recommendation_engine import RecommendationEngine
from src.models.data_models import RecommendationRequest

# 初始化引擎
engine = RecommendationEngine()

# 創建測試請求
request = RecommendationRequest(
    member_code="CU000001",
    phone="0937024682",
    total_consumption=17400,
    accumulated_bonus=500,
    recent_purchases=["30463", "31033"]
)

# 獲取推薦
recommendations = engine.get_recommendations(request)

# 顯示結果
for i, rec in enumerate(recommendations.recommendations, 1):
    print(f"{i}. 產品 {rec.product_id} (信心度: {rec.score:.2%})")
    print(f"   理由: {rec.reason}\n")
```

## 📊 資料格式

### 上傳資料檔案

如果您要使用自己的資料，請確保格式正確：

#### member（會員資料）
```csv
會員編號,電話,總消費金額,累積紅利,註冊日期
CU000001,0937024682,17400,500,2023-01-15
```

#### sales（銷售訂單）
```csv
訂單編號,會員編號,訂單日期,訂單金額,門市代碼
S000001,CU000001,2024-01-10,1200,STORE01
```

#### salesdetails（訂單明細）
```csv
訂單編號,產品編號,數量,單價,小計
S000001,30463,2,500,1000
```

## 🎨 視覺化結果

在 Colab 中可以輕鬆視覺化推薦結果：

```python
import matplotlib.pyplot as plt
import seaborn as sns

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']

# 視覺化推薦分數
scores = [rec.score for rec in recommendations.recommendations]
products = [rec.product_id for rec in recommendations.recommendations]

plt.figure(figsize=(10, 6))
plt.barh(products, scores)
plt.xlabel('Confidence Score')
plt.ylabel('Product ID')
plt.title('Top 5 Product Recommendations')
plt.xlim([0, 1])
plt.show()
```

## ⚡ 效能優化

### 使用 GPU 加速

1. 點擊選單：`Runtime` → `Change runtime type`
2. 選擇 `Hardware accelerator` → `GPU`
3. 點擊 `Save`

### 增加 RAM

如果遇到記憶體不足：

1. 點擊選單：`Runtime` → `Change runtime type`
2. 選擇 `Runtime shape` → `High-RAM`

## 🔧 常見問題

### Q1: 安裝套件時出錯

**解決方案**: 重新啟動 Runtime

```python
# 在新的儲存格中執行
!pip install --upgrade pip
!pip install -r requirements.txt
```

### Q2: 找不到模組

**解決方案**: 確保專案路徑已添加

```python
import sys
sys.path.insert(0, '/content/product-recommendation-system')
```

### Q3: 資料檔案太大

**解決方案**: 使用 Google Drive

```python
from google.colab import drive
drive.mount('/content/drive')

# 從 Drive 讀取資料
import shutil
shutil.copy('/content/drive/MyDrive/data/member', 'data/raw/member')
```

### Q4: Session 逾時

Colab 免費版有使用時間限制。建議：

- 定期儲存模型到 Drive
- 使用 Colab Pro 獲得更長時間
- 分段執行訓練

## 💾 儲存結果

### 儲存訓練好的模型

```python
from google.colab import files

# 下載模型
files.download('data/models/recommender_v1.0.0.pkl')
```

### 儲存到 Google Drive

```python
from google.colab import drive
drive.mount('/content/drive')

# 複製模型到 Drive
!cp -r data/models /content/drive/MyDrive/recommendation_models
```

## 📱 分享您的 Notebook

1. 點擊右上角的 `Share` 按鈕
2. 設定權限（任何人可查看/編輯）
3. 複製連結分享給團隊

## 🚀 進階使用

### 自動化訓練

設定定期訓練：

```python
# 每週自動訓練
from datetime import datetime

def auto_train():
    print(f"開始訓練: {datetime.now()}")
    !python src/train.py
    print("訓練完成！")

# 執行訓練
auto_train()
```

### 整合 Weights & Biases

追蹤實驗：

```python
!pip install wandb

import wandb
wandb.login()

# 在訓練腳本中添加 wandb 追蹤
```

### 部署為 API

使用 ngrok 暫時公開 API：

```python
!pip install pyngrok

from pyngrok import ngrok

# 啟動 API
!python src/api/main.py &

# 創建公開 URL
public_url = ngrok.connect(8000)
print(f"API URL: {public_url}")
```

## 📚 相關資源

- [Colab 官方文檔](https://colab.research.google.com/notebooks/intro.ipynb)
- [專案 README](../README.md)
- [模型訓練指南](MODEL_TRAINING.md)
- [API 文檔](API_GUIDE.md)

## 🆘 需要協助？

如果遇到問題：

1. 查看 [GitHub Issues](https://github.com/ldsAS/product-recommendation-system/issues)
2. 參考 [疑難排解](../README.md#疑難排解)
3. 提交新的 Issue

---

**最後更新**: 2025-11-01  
**維護者**: 開發團隊
