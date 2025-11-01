"""
專案健康檢查腳本
檢查系統依賴、配置、資料和模型狀態
"""
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_dependencies():
    """檢查必要的依賴套件"""
    print("=" * 60)
    print("1. 檢查依賴套件")
    print("=" * 60)
    
    required_packages = [
        ("pandas", "資料處理"),
        ("numpy", "數值計算"),
        ("pydantic", "資料驗證"),
        ("fastapi", "Web 框架"),
        ("lightgbm", "機器學習"),
        ("sklearn", "機器學習基礎"),
    ]
    
    success = 0
    failed = []
    
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"✓ {package:20s} - {description}")
            success += 1
        except ImportError:
            print(f"✗ {package:20s} - 未安裝")
            failed.append(package)
    
    print(f"\n結果: {success}/{len(required_packages)} 套件已安裝")
    
    if failed:
        print(f"\n⚠️  缺少套件: {', '.join(failed)}")
        print("請執行: pip install -r requirements.txt")
        return False
    
    return True


def check_config():
    """檢查配置檔案"""
    print("\n" + "=" * 60)
    print("2. 檢查配置檔案")
    print("=" * 60)
    
    env_example = project_root / ".env.example"
    env_file = project_root / ".env"
    
    if not env_example.exists():
        print("✗ .env.example 不存在")
        return False
    
    print("✓ .env.example 存在")
    
    if not env_file.exists():
        print("⚠️  .env 不存在（使用預設配置）")
        print("建議執行: cp .env.example .env")
        config_ok = True  # 不是致命錯誤
    else:
        print("✓ .env 存在")
        config_ok = True
    
    # 嘗試載入配置
    try:
        from src.config import settings
        print(f"✓ 配置載入成功")
        print(f"  - 模型版本: {settings.MODEL_VERSION}")
        print(f"  - 模型類型: {settings.MODEL_TYPE}")
        print(f"  - 日誌級別: {settings.LOG_LEVEL}")
        return True
    except Exception as e:
        print(f"✗ 配置載入失敗: {e}")
        return False


def check_data():
    """檢查資料檔案"""
    print("\n" + "=" * 60)
    print("3. 檢查資料檔案")
    print("=" * 60)
    
    data_dir = project_root / "data" / "raw"
    required_files = ["member", "sales", "salesdetails"]
    
    all_exist = True
    for filename in required_files:
        filepath = data_dir / filename
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"✓ {filename:15s} - {size_mb:.1f} MB")
        else:
            print(f"✗ {filename:15s} - 不存在")
            all_exist = False
    
    if not all_exist:
        print("\n⚠️  缺少訓練資料檔案")
        print("請將資料檔案放入 data/raw/ 目錄")
        return False
    
    return True


def check_models():
    """檢查模型檔案"""
    print("\n" + "=" * 60)
    print("4. 檢查模型檔案")
    print("=" * 60)
    
    models_dir = project_root / "data" / "models"
    model_files = list(models_dir.glob("*.pkl")) + list(models_dir.glob("*.joblib"))
    
    if not model_files:
        print("⚠️  未找到訓練好的模型")
        print("請執行: python src/train.py")
        return False
    
    print(f"✓ 找到 {len(model_files)} 個模型檔案:")
    for model_file in model_files:
        size_mb = model_file.stat().st_size / (1024 * 1024)
        print(f"  - {model_file.name} ({size_mb:.1f} MB)")
    
    return True


def check_directories():
    """檢查必要的目錄結構"""
    print("\n" + "=" * 60)
    print("5. 檢查目錄結構")
    print("=" * 60)
    
    required_dirs = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/models",
        "logs",
        "scripts",
        "docs",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"✓ {dir_path}")
        else:
            print(f"✗ {dir_path} - 不存在")
            all_exist = False
    
    return all_exist


def main():
    """執行完整的健康檢查"""
    print("\n" + "🔍 專案健康檢查".center(60, "="))
    print()
    
    results = {
        "依賴套件": check_dependencies(),
        "配置檔案": check_config(),
        "資料檔案": check_data(),
        "模型檔案": check_models(),
        "目錄結構": check_directories(),
    }
    
    # 總結
    print("\n" + "=" * 60)
    print("📊 檢查總結")
    print("=" * 60)
    
    for check_name, result in results.items():
        status = "✓ 通過" if result else "✗ 失敗"
        print(f"{check_name:12s}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\n總計: {passed}/{total} 項檢查通過")
    
    # 建議
    print("\n" + "=" * 60)
    print("💡 建議")
    print("=" * 60)
    
    if not results["依賴套件"]:
        print("1. 安裝依賴: pip install -r requirements.txt")
    
    if not results["配置檔案"]:
        print("2. 配置環境: cp .env.example .env")
    
    if not results["資料檔案"]:
        print("3. 準備資料: 將資料檔案放入 data/raw/")
    
    if not results["模型檔案"]:
        print("4. 訓練模型: python src/train.py")
    
    if all(results.values()):
        print("✅ 系統狀態良好，可以開始使用！")
        print("\n啟動 API 服務:")
        print("  python src/api/main.py")
        print("  或")
        print("  uvicorn src.api.main:app --reload")
        return 0
    else:
        print("\n⚠️  請先解決上述問題")
        return 1


if __name__ == "__main__":
    sys.exit(main())
