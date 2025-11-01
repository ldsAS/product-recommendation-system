"""
A/B 測試管理器
支援多版本模型對比測試，追蹤效能指標和轉換率
"""
import random
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import threading

from src.models.data_models import ABTestConfig, ABTestMetrics


@dataclass
class ABTestResult:
    """A/B 測試結果"""
    model_version: str
    total_requests: int = 0
    total_conversions: int = 0
    total_shown: int = 0
    conversion_rate: float = 0.0
    avg_response_time_ms: float = 0.0
    response_times: List[float] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def update_conversion_rate(self):
        """更新轉換率"""
        if self.total_shown > 0:
            self.conversion_rate = self.total_conversions / self.total_shown
    
    def update_avg_response_time(self):
        """更新平均回應時間"""
        if self.response_times:
            self.avg_response_time_ms = sum(self.response_times) / len(self.response_times)
    
    def to_metrics(self) -> ABTestMetrics:
        """轉換為 ABTestMetrics"""
        return ABTestMetrics(
            model_version=self.model_version,
            total_requests=self.total_requests,
            total_conversions=self.total_conversions,
            conversion_rate=self.conversion_rate,
            avg_response_time_ms=self.avg_response_time_ms,
            start_time=self.start_time or datetime.now(),
            end_time=self.end_time or datetime.now()
        )


class ABTestManager:
    """A/B 測試管理器"""
    
    def __init__(
        self,
        config_path: str = "data/ab_test_config.json",
        results_path: str = "data/ab_test_results.json"
    ):
        """
        初始化 A/B 測試管理器
        
        Args:
            config_path: 配置檔案路徑
            results_path: 結果檔案路徑
        """
        self.config_path = Path(config_path)
        self.results_path = Path(results_path)
        self._lock = threading.Lock()
        
        # 載入配置
        self.config = self._load_config()
        
        # 測試結果
        self.results: Dict[str, ABTestResult] = {}
        self._load_results()
        
        # 初始化結果
        if self.config.enabled:
            if self.config.model_a_version not in self.results:
                self.results[self.config.model_a_version] = ABTestResult(
                    model_version=self.config.model_a_version,
                    start_time=datetime.now()
                )
            if self.config.model_b_version not in self.results:
                self.results[self.config.model_b_version] = ABTestResult(
                    model_version=self.config.model_b_version,
                    start_time=datetime.now()
                )
    
    def _load_config(self) -> ABTestConfig:
        """載入配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return ABTestConfig(**data)
            except Exception as e:
                print(f"載入 A/B 測試配置失敗: {e}")
        
        # 返回預設配置
        return ABTestConfig(
            enabled=False,
            model_a_version="v1.0.0",
            model_b_version="v1.1.0",
            model_a_ratio=0.5
        )
    
    def _save_config(self):
        """儲存配置"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"儲存 A/B 測試配置失敗: {e}")
    
    def _load_results(self):
        """載入結果"""
        if self.results_path.exists():
            try:
                with open(self.results_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for version, result_data in data.items():
                    # 轉換日期時間
                    if result_data.get('start_time'):
                        result_data['start_time'] = datetime.fromisoformat(result_data['start_time'])
                    if result_data.get('end_time'):
                        result_data['end_time'] = datetime.fromisoformat(result_data['end_time'])
                    
                    self.results[version] = ABTestResult(**result_data)
            except Exception as e:
                print(f"載入 A/B 測試結果失敗: {e}")
    
    def _save_results(self):
        """儲存結果"""
        try:
            self.results_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 轉換為可序列化的格式
            data = {}
            for version, result in self.results.items():
                result_dict = asdict(result)
                # 轉換日期時間為字串
                if result_dict.get('start_time'):
                    result_dict['start_time'] = result_dict['start_time'].isoformat()
                if result_dict.get('end_time'):
                    result_dict['end_time'] = result_dict['end_time'].isoformat()
                data[version] = result_dict
            
            with open(self.results_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"儲存 A/B 測試結果失敗: {e}")
    
    def is_enabled(self) -> bool:
        """檢查 A/B 測試是否啟用"""
        return self.config.enabled
    
    def select_model(self, user_id: Optional[str] = None) -> str:
        """
        選擇模型版本
        
        Args:
            user_id: 使用者ID（用於一致性雜湊）
            
        Returns:
            str: 模型版本
        """
        if not self.config.enabled:
            return self.config.model_a_version
        
        # 使用一致性雜湊確保同一使用者總是分配到同一模型
        if user_id:
            hash_value = hash(user_id)
            ratio = (hash_value % 100) / 100.0
        else:
            ratio = random.random()
        
        if ratio < self.config.model_a_ratio:
            return self.config.model_a_version
        else:
            return self.config.model_b_version
    
    def record_request(
        self,
        model_version: str,
        response_time_ms: float,
        num_recommendations: int = 0
    ):
        """
        記錄請求
        
        Args:
            model_version: 模型版本
            response_time_ms: 回應時間（毫秒）
            num_recommendations: 推薦數量
        """
        with self._lock:
            if model_version not in self.results:
                self.results[model_version] = ABTestResult(
                    model_version=model_version,
                    start_time=datetime.now()
                )
            
            result = self.results[model_version]
            result.total_requests += 1
            result.total_shown += num_recommendations
            result.response_times.append(response_time_ms)
            result.update_avg_response_time()
            
            # 定期儲存結果
            if result.total_requests % 10 == 0:
                self._save_results()
    
    def record_conversion(
        self,
        model_version: str,
        converted: bool = True
    ):
        """
        記錄轉換
        
        Args:
            model_version: 模型版本
            converted: 是否轉換
        """
        with self._lock:
            if model_version not in self.results:
                self.results[model_version] = ABTestResult(
                    model_version=model_version,
                    start_time=datetime.now()
                )
            
            result = self.results[model_version]
            if converted:
                result.total_conversions += 1
            result.update_conversion_rate()
            
            # 定期儲存結果
            if result.total_conversions % 5 == 0:
                self._save_results()
    
    def get_results(self, model_version: Optional[str] = None) -> Dict[str, ABTestResult]:
        """
        獲取測試結果
        
        Args:
            model_version: 模型版本（可選）
            
        Returns:
            Dict[str, ABTestResult]: 測試結果
        """
        with self._lock:
            if model_version:
                return {model_version: self.results.get(model_version)}
            return dict(self.results)
    
    def get_metrics(self, model_version: Optional[str] = None) -> List[ABTestMetrics]:
        """
        獲取測試指標
        
        Args:
            model_version: 模型版本（可選）
            
        Returns:
            List[ABTestMetrics]: 測試指標列表
        """
        results = self.get_results(model_version)
        return [result.to_metrics() for result in results.values() if result]
    
    def compare_models(self) -> Dict[str, Any]:
        """
        比較模型效能
        
        Returns:
            Dict: 比較結果
        """
        if not self.config.enabled:
            return {
                'enabled': False,
                'message': 'A/B 測試未啟用'
            }
        
        model_a = self.results.get(self.config.model_a_version)
        model_b = self.results.get(self.config.model_b_version)
        
        if not model_a or not model_b:
            return {
                'enabled': True,
                'message': '資料不足，無法比較'
            }
        
        # 計算差異
        conversion_rate_diff = model_b.conversion_rate - model_a.conversion_rate
        conversion_rate_improvement = (
            (conversion_rate_diff / model_a.conversion_rate * 100)
            if model_a.conversion_rate > 0 else 0
        )
        
        response_time_diff = model_b.avg_response_time_ms - model_a.avg_response_time_ms
        response_time_improvement = (
            (response_time_diff / model_a.avg_response_time_ms * 100)
            if model_a.avg_response_time_ms > 0 else 0
        )
        
        # 判斷勝者
        winner = None
        if abs(conversion_rate_improvement) > 5:  # 至少 5% 的改進
            winner = (
                self.config.model_b_version
                if conversion_rate_improvement > 0
                else self.config.model_a_version
            )
        
        return {
            'enabled': True,
            'model_a': {
                'version': self.config.model_a_version,
                'total_requests': model_a.total_requests,
                'conversion_rate': model_a.conversion_rate,
                'avg_response_time_ms': model_a.avg_response_time_ms
            },
            'model_b': {
                'version': self.config.model_b_version,
                'total_requests': model_b.total_requests,
                'conversion_rate': model_b.conversion_rate,
                'avg_response_time_ms': model_b.avg_response_time_ms
            },
            'comparison': {
                'conversion_rate_diff': conversion_rate_diff,
                'conversion_rate_improvement_pct': conversion_rate_improvement,
                'response_time_diff_ms': response_time_diff,
                'response_time_improvement_pct': response_time_improvement,
                'winner': winner,
                'confidence': self._calculate_confidence(model_a, model_b)
            }
        }
    
    def _calculate_confidence(
        self,
        model_a: ABTestResult,
        model_b: ABTestResult
    ) -> str:
        """
        計算統計信心水準
        
        Args:
            model_a: 模型 A 結果
            model_b: 模型 B 結果
            
        Returns:
            str: 信心水準（low/medium/high）
        """
        # 簡單的樣本數檢查
        min_samples = min(model_a.total_requests, model_b.total_requests)
        
        if min_samples < 100:
            return 'low'
        elif min_samples < 500:
            return 'medium'
        else:
            return 'high'
    
    def enable_test(
        self,
        model_a_version: str,
        model_b_version: str,
        model_a_ratio: float = 0.5
    ):
        """
        啟用 A/B 測試
        
        Args:
            model_a_version: 模型 A 版本
            model_b_version: 模型 B 版本
            model_a_ratio: 模型 A 流量比例
        """
        with self._lock:
            self.config = ABTestConfig(
                enabled=True,
                model_a_version=model_a_version,
                model_b_version=model_b_version,
                model_a_ratio=model_a_ratio
            )
            
            # 初始化結果
            if model_a_version not in self.results:
                self.results[model_a_version] = ABTestResult(
                    model_version=model_a_version,
                    start_time=datetime.now()
                )
            if model_b_version not in self.results:
                self.results[model_b_version] = ABTestResult(
                    model_version=model_b_version,
                    start_time=datetime.now()
                )
            
            self._save_config()
            self._save_results()
    
    def disable_test(self):
        """停用 A/B 測試"""
        with self._lock:
            # 標記結束時間
            for result in self.results.values():
                if not result.end_time:
                    result.end_time = datetime.now()
            
            self.config.enabled = False
            self._save_config()
            self._save_results()
    
    def reset_results(self):
        """重置測試結果"""
        with self._lock:
            self.results.clear()
            self._save_results()
    
    def export_report(self) -> Dict[str, Any]:
        """
        匯出測試報告
        
        Returns:
            Dict: 測試報告
        """
        comparison = self.compare_models()
        
        return {
            'config': asdict(self.config),
            'results': {
                version: asdict(result)
                for version, result in self.results.items()
            },
            'comparison': comparison,
            'generated_at': datetime.now().isoformat()
        }


# 全域 A/B 測試管理器實例
_ab_test_manager: Optional[ABTestManager] = None


def get_ab_test_manager() -> ABTestManager:
    """獲取全域 A/B 測試管理器"""
    global _ab_test_manager
    if _ab_test_manager is None:
        _ab_test_manager = ABTestManager()
    return _ab_test_manager


def setup_ab_test_manager(
    config_path: str = "data/ab_test_config.json",
    results_path: str = "data/ab_test_results.json"
) -> ABTestManager:
    """
    設置全域 A/B 測試管理器
    
    Args:
        config_path: 配置檔案路徑
        results_path: 結果檔案路徑
        
    Returns:
        ABTestManager: A/B 測試管理器實例
    """
    global _ab_test_manager
    _ab_test_manager = ABTestManager(config_path, results_path)
    return _ab_test_manager


if __name__ == "__main__":
    # 測試 A/B 測試管理器
    print("測試 A/B 測試管理器...")
    
    # 建立管理器
    manager = ABTestManager(
        config_path="data/test_ab_config.json",
        results_path="data/test_ab_results.json"
    )
    
    # 啟用測試
    print("\n啟用 A/B 測試...")
    manager.enable_test(
        model_a_version="v1.0.0",
        model_b_version="v1.1.0",
        model_a_ratio=0.5
    )
    print(f"✓ A/B 測試已啟用")
    
    # 模擬請求
    print("\n模擬請求...")
    for i in range(100):
        user_id = f"user_{i}"
        model_version = manager.select_model(user_id)
        
        # 記錄請求
        response_time = 200 + random.randint(-50, 50)
        manager.record_request(model_version, response_time, num_recommendations=5)
        
        # 模擬轉換（v1.1.0 有更高的轉換率）
        if model_version == "v1.1.0":
            converted = random.random() < 0.15  # 15% 轉換率
        else:
            converted = random.random() < 0.10  # 10% 轉換率
        
        if converted:
            manager.record_conversion(model_version, converted=True)
    
    print(f"✓ 已模擬 100 個請求")
    
    # 獲取結果
    print("\n=== 測試結果 ===")
    results = manager.get_results()
    for version, result in results.items():
        print(f"\n{version}:")
        print(f"  總請求數: {result.total_requests}")
        print(f"  總轉換數: {result.total_conversions}")
        print(f"  轉換率: {result.conversion_rate:.2%}")
        print(f"  平均回應時間: {result.avg_response_time_ms:.2f} ms")
    
    # 比較模型
    print("\n=== 模型比較 ===")
    comparison = manager.compare_models()
    print(json.dumps(comparison, indent=2, ensure_ascii=False))
    
    # 匯出報告
    print("\n=== 測試報告 ===")
    report = manager.export_report()
    print(f"報告已生成，包含 {len(report['results'])} 個模型的結果")
    
    # 停用測試
    print("\n停用 A/B 測試...")
    manager.disable_test()
    print("✓ A/B 測試已停用")
    
    print("\n✓ A/B 測試管理器測試完成")
