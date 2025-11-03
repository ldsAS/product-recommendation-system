import sys
import pandas
import numpy
import fastapi
import sklearn
import lightgbm
import xgboost
import implicit

print('✓ 所有核心套件導入成功！')
print(f'Python 版本: {sys.version}')
print(f'Pandas: {pandas.__version__}')
print(f'NumPy: {numpy.__version__}')
print(f'FastAPI: {fastapi.__version__}')
print(f'Scikit-learn: {sklearn.__version__}')
print(f'LightGBM: {lightgbm.__version__}')
print(f'XGBoost: {xgboost.__version__}')
print(f'Implicit (協同過濾): {implicit.__version__}')
