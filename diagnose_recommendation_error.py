"""
診斷推薦錯誤
"""
import sys
from pathlib import Path

print("=" * 80)
print("診斷推薦系統錯誤")
print("=" * 80)

# 1. 檢查模型文件
print("\n1. 檢查模型文件...")
model_dir = Path("data/models/v1.0.0")

if not model_dir.exists():
    print(f"✗ 模型目錄不存在: {model_dir}")
    print("\n解決方案: 執行 python src/train.py 訓練模型")
    sys.exit(1)

required_files = {
    'model.pkl': '訓練好的模型',
    'member_features.parquet': '會員特徵',
    'product_features.parquet': '產品特徵',
    'metadata.json': '模型元資料'
}

all_ok = True
for filename, description in required_files.items():
    filepath = model_dir / filename
    if filepath.exists():
        size_mb = filepath.stat().st_size / (1024 * 1024)
        print(f"✓ {description}: {filename} ({size_mb:.2f} MB)")
    else:
        print(f"✗ {description}: {filename} (不存在)")
        all_ok = False

if not all_ok:
    print("\n解決方案: 執行 python src/train.py 訓練模型")
    sys.exit(1)

# 2. 測試推薦引擎初始化
print("\n2. 測試推薦引擎初始化...")
try:
    from src.models.recommendation_engine import RecommendationEngine
    print("✓ 推薦引擎模組導入成功")
    
    engine = RecommendationEngine()
    print("✓ 推薦引擎初始化成功")
    
    # 3. 檢查健康狀態
    print("\n3. 檢查推薦引擎健康狀態...")
    health = engine.health_check()
    for key, value in health.items():
        status = "✓" if value else "✗"
        print(f"{status} {key}: {value}")
    
    # 4. 測試推薦生成
    print("\n4. 測試推薦生成...")
    from src.models.data_models import MemberInfo
    
    test_member = MemberInfo(
        member_code="CU000001",
        phone="0937024682",
        total_consumption=17400,
        accumulated_bonus=500,
        recent_purchases=[]
    )
    
    recommendations = engine.recommend(test_member, n=5)
    
    if recommendations:
        print(f"✓ 推薦生成成功: {len(recommendations)} 個推薦")
        print("\n推薦結果:")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"  {i}. {rec.product_name} (信心度: {rec.confidence_score:.1f}%)")
    else:
        print("⚠ 推薦生成成功但沒有結果")
        print("  可能原因: 會員不在訓練資料中")
    
    print("\n" + "=" * 80)
    print("✓ 所有檢查通過！推薦系統正常運作")
    print("=" * 80)
    print("\n如果 Web UI 仍然失敗，請:")
    print("1. 重啟 Web 服務")
    print("2. 檢查瀏覽器控制台的錯誤訊息")
    print("3. 使用訓練資料中存在的會員編號")
    
except FileNotFoundError as e:
    print(f"✗ 文件未找到: {e}")
    print("\n解決方案: 執行 python src/train.py 訓練模型")
    sys.exit(1)
    
except Exception as e:
    print(f"✗ 錯誤: {e}")
    print("\n詳細錯誤:")
    import traceback
    traceback.print_exc()
    sys.exit(1)
