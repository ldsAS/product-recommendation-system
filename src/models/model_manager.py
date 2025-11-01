"""
模型版本管理
實作模型儲存和載入功能、版本命名和目錄結構管理、符號連結指向當前版本
"""
import os
import json
import pickle
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.config import settings

logger = logging.getLogger(__name__)


class ModelManager:
    """模型版本管理器"""
    
    def __init__(self, models_dir: Optional[Path] = None):
        """
        初始化模型管理器
        
        Args:
            models_dir: 模型目錄路徑，None 表示使用配置中的路徑
        """
        self.models_dir = Path(models_dir) if models_dir else settings.MODELS_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"模型管理器初始化: {self.models_dir}")
    
    def save_model(
        self,
        model: Any,
        version: str,
        metadata: Dict[str, Any],
        set_as_current: bool = True
    ) -> Path:
        """
        儲存模型
        
        Args:
            model: 模型物件
            version: 版本號（如 v1.0.0）
            metadata: 模型元資料
            set_as_current: 是否設置為當前版本
            
        Returns:
            模型目錄路徑
        """
        logger.info(f"儲存模型版本: {version}")
        
        # 驗證版本格式
        if not self._validate_version(version):
            raise ValueError(f"無效的版本格式: {version}，應為 vX.Y.Z 格式")
        
        # 建立版本目錄
        version_dir = self.models_dir / version
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # 儲存模型
        model_file = version_dir / "model.pkl"
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"✓ 模型已儲存: {model_file}")
        
        # 儲存元資料
        metadata_file = version_dir / "metadata.json"
        metadata['version'] = version
        metadata['saved_at'] = datetime.now().isoformat()
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ 元資料已儲存: {metadata_file}")
        
        # 設置為當前版本
        if set_as_current:
            self.set_current_version(version)
        
        return version_dir
    
    def load_model(self, version: str = "current") -> Any:
        """
        載入模型
        
        Args:
            version: 版本號或 "current"
            
        Returns:
            模型物件
        """
        logger.info(f"載入模型版本: {version}")
        
        # 解析版本
        if version == "current":
            version = self.get_current_version()
            if not version:
                raise FileNotFoundError("當前版本未設置")
        
        # 載入模型
        model_file = self.models_dir / version / "model.pkl"
        
        if not model_file.exists():
            raise FileNotFoundError(f"模型檔案不存在: {model_file}")
        
        with open(model_file, 'rb') as f:
            model = pickle.load(f)
        
        logger.info(f"✓ 模型已載入: {version}")
        
        return model
    
    def load_metadata(self, version: str = "current") -> Dict[str, Any]:
        """
        載入模型元資料
        
        Args:
            version: 版本號或 "current"
            
        Returns:
            元資料字典
        """
        # 解析版本
        if version == "current":
            version = self.get_current_version()
            if not version:
                raise FileNotFoundError("當前版本未設置")
        
        # 載入元資料
        metadata_file = self.models_dir / version / "metadata.json"
        
        if not metadata_file.exists():
            raise FileNotFoundError(f"元資料檔案不存在: {metadata_file}")
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        return metadata
    
    def set_current_version(self, version: str):
        """
        設置當前版本
        
        Args:
            version: 版本號
        """
        logger.info(f"設置當前版本: {version}")
        
        # 檢查版本是否存在
        version_dir = self.models_dir / version
        if not version_dir.exists():
            raise FileNotFoundError(f"版本目錄不存在: {version_dir}")
        
        # 建立或更新符號連結（Windows 使用文件記錄）
        current_file = self.models_dir / "current.txt"
        
        with open(current_file, 'w') as f:
            f.write(version)
        
        logger.info(f"✓ 當前版本已設置: {version}")
    
    def get_current_version(self) -> Optional[str]:
        """
        獲取當前版本
        
        Returns:
            當前版本號，如果未設置則返回 None
        """
        current_file = self.models_dir / "current.txt"
        
        if not current_file.exists():
            return None
        
        with open(current_file, 'r') as f:
            version = f.read().strip()
        
        return version if version else None
    
    def list_versions(self) -> List[str]:
        """
        列出所有版本
        
        Returns:
            版本號列表，按時間排序
        """
        versions = []
        
        for item in self.models_dir.iterdir():
            if item.is_dir() and self._validate_version(item.name):
                versions.append(item.name)
        
        # 按版本號排序
        versions.sort(key=self._parse_version, reverse=True)
        
        return versions
    
    def delete_version(self, version: str, force: bool = False):
        """
        刪除版本
        
        Args:
            version: 版本號
            force: 是否強制刪除（即使是當前版本）
        """
        logger.info(f"刪除模型版本: {version}")
        
        # 檢查是否是當前版本
        current_version = self.get_current_version()
        if version == current_version and not force:
            raise ValueError(f"無法刪除當前版本 {version}，請先切換到其他版本或使用 force=True")
        
        # 刪除版本目錄
        version_dir = self.models_dir / version
        
        if not version_dir.exists():
            raise FileNotFoundError(f"版本目錄不存在: {version_dir}")
        
        shutil.rmtree(version_dir)
        
        logger.info(f"✓ 版本已刪除: {version}")
        
        # 如果刪除的是當前版本，清除當前版本設置
        if version == current_version:
            current_file = self.models_dir / "current.txt"
            if current_file.exists():
                current_file.unlink()
            logger.warning("當前版本已被刪除，請設置新的當前版本")
    
    def compare_versions(self, version1: str, version2: str) -> Dict[str, Any]:
        """
        比較兩個版本
        
        Args:
            version1: 版本號 1
            version2: 版本號 2
            
        Returns:
            比較結果字典
        """
        logger.info(f"比較版本: {version1} vs {version2}")
        
        # 載入元資料
        metadata1 = self.load_metadata(version1)
        metadata2 = self.load_metadata(version2)
        
        # 比較指標
        comparison = {
            'version1': version1,
            'version2': version2,
            'metadata1': metadata1,
            'metadata2': metadata2,
            'metrics_comparison': {}
        }
        
        # 比較效能指標
        if 'metrics' in metadata1 and 'metrics' in metadata2:
            metrics1 = metadata1['metrics']
            metrics2 = metadata2['metrics']
            
            for metric_name in set(metrics1.keys()) | set(metrics2.keys()):
                value1 = metrics1.get(metric_name)
                value2 = metrics2.get(metric_name)
                
                if value1 is not None and value2 is not None:
                    diff = value2 - value1
                    comparison['metrics_comparison'][metric_name] = {
                        'version1': value1,
                        'version2': value2,
                        'difference': diff,
                        'improvement': diff > 0
                    }
        
        return comparison
    
    def get_version_info(self, version: str = "current") -> Dict[str, Any]:
        """
        獲取版本資訊
        
        Args:
            version: 版本號或 "current"
            
        Returns:
            版本資訊字典
        """
        # 解析版本
        if version == "current":
            version = self.get_current_version()
            if not version:
                raise FileNotFoundError("當前版本未設置")
        
        # 載入元資料
        metadata = self.load_metadata(version)
        
        # 獲取版本目錄資訊
        version_dir = self.models_dir / version
        
        # 計算目錄大小
        total_size = sum(
            f.stat().st_size for f in version_dir.rglob('*') if f.is_file()
        )
        
        info = {
            'version': version,
            'is_current': version == self.get_current_version(),
            'directory': str(version_dir),
            'size_bytes': total_size,
            'size_mb': round(total_size / (1024 * 1024), 2),
            'metadata': metadata
        }
        
        return info
    
    def _validate_version(self, version: str) -> bool:
        """
        驗證版本格式
        
        Args:
            version: 版本號
            
        Returns:
            是否有效
        """
        import re
        pattern = r'^v\d+\.\d+\.\d+$'
        return bool(re.match(pattern, version))
    
    def _parse_version(self, version: str) -> tuple:
        """
        解析版本號
        
        Args:
            version: 版本號（如 v1.2.3）
            
        Returns:
            版本元組（如 (1, 2, 3)）
        """
        parts = version[1:].split('.')  # 移除 'v' 前綴
        return tuple(int(p) for p in parts)


def main():
    """測試模型管理器"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 70)
    print("測試模型管理器")
    print("=" * 70)
    
    # 建立模型管理器
    manager = ModelManager()
    
    # 測試 1: 列出版本
    print("\n測試 1: 列出所有版本")
    versions = manager.list_versions()
    print(f"找到 {len(versions)} 個版本:")
    for v in versions:
        print(f"  - {v}")
    
    # 測試 2: 獲取當前版本
    print("\n測試 2: 獲取當前版本")
    current = manager.get_current_version()
    print(f"當前版本: {current if current else '未設置'}")
    
    # 測試 3: 獲取版本資訊
    if current:
        print("\n測試 3: 獲取版本資訊")
        try:
            info = manager.get_version_info(current)
            print(f"版本: {info['version']}")
            print(f"是否為當前版本: {info['is_current']}")
            print(f"大小: {info['size_mb']} MB")
        except Exception as e:
            print(f"獲取版本資訊失敗: {e}")
    
    print("\n" + "=" * 70)
    print("✓ 模型管理器測試完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
