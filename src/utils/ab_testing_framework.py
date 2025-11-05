"""
A/B 測試框架
支援多組測試、推薦策略對比、統計顯著性檢驗
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import threading


@dataclass
class TestGroupConfig:
    """測試組配置"""
    group_id: str
    group_name: str
    strategy_config: Dict[str, Any]  # 推薦策略配置
    traffic_ratio: float  # 流量比例 (0-1)
    description: str = ""


@dataclass
class TestRecord:
    """測試記錄"""
    member_code: str
    group_id: str
    timestamp: datetime
    
    # 可參考價值分數
    overall_score: float
    relevance_score: float
    novelty_score: float
    explainability_score: float
    diversity_score: float
    
    # 性能指標
    response_time_ms: float
    
    # 推薦元資料
    recommendation_count: int
    strategy_used: str


@dataclass
class GroupStatistics:
    """組別統計數據"""
    group_id: str
    group_name: str
    
    # 樣本數
    total_records: int = 0
    
    # 可參考價值分數統計
    avg_overall_score: float = 0.0
    avg_relevance_score: float = 0.0
    avg_novelty_score: float = 0.0
    avg_explainability_score: float = 0.0
    avg_diversity_score: float = 0.0
    
    std_overall_score: float = 0.0
    
    # 性能統計
    avg_response_time_ms: float = 0.0
    p50_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    
    # 原始數據（用於統計檢驗）
    overall_scores: List[float] = field(default_factory=list)
    response_times: List[float] = field(default_factory=list)


class ABTestingFramework:
    """A/B 測試框架"""
    
    def __init__(
        self,
        config_path: str = "config/ab_test_config.json",
        data_path: str = "data/ab_test_data.json"
    ):
        """
        初始化 A/B 測試框架
        
        Args:
            config_path: 配置檔案路徑
            data_path: 測試數據路徑
        """
        self.config_path = Path(config_path)
        self.data_path = Path(data_path)
        self._lock = threading.Lock()
        
        # 測試配置
        self.test_enabled: bool = False
        self.test_name: str = ""
        self.test_groups: Dict[str, TestGroupConfig] = {}
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # 測試數據
        self.test_records: List[TestRecord] = []
        
        # 載入配置和數據
        self._load_config()
        self._load_data()
    
    def _load_config(self):
        """載入測試配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.test_enabled = data.get('test_enabled', False)
                self.test_name = data.get('test_name', '')
                
                if data.get('start_time'):
                    self.start_time = datetime.fromisoformat(data['start_time'])
                if data.get('end_time'):
                    self.end_time = datetime.fromisoformat(data['end_time'])
                
                # 載入測試組配置
                for group_data in data.get('test_groups', []):
                    group = TestGroupConfig(**group_data)
                    self.test_groups[group.group_id] = group
                    
            except Exception as e:
                print(f"載入 A/B 測試配置失敗: {e}")
    
    def _save_config(self):
        """儲存測試配置"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'test_enabled': self.test_enabled,
                'test_name': self.test_name,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None,
                'test_groups': [asdict(group) for group in self.test_groups.values()]
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"儲存 A/B 測試配置失敗: {e}")
    
    def _load_data(self):
        """載入測試數據"""
        if self.data_path.exists():
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for record_data in data:
                    record_data['timestamp'] = datetime.fromisoformat(record_data['timestamp'])
                    self.test_records.append(TestRecord(**record_data))
                    
            except Exception as e:
                print(f"載入 A/B 測試數據失敗: {e}")
    
    def _save_data(self):
        """儲存測試數據"""
        try:
            self.data_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = []
            for record in self.test_records:
                record_dict = asdict(record)
                record_dict['timestamp'] = record_dict['timestamp'].isoformat()
                data.append(record_dict)
            
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"儲存 A/B 測試數據失敗: {e}")
    
    def create_test(
        self,
        test_name: str,
        test_groups: List[TestGroupConfig]
    ) -> bool:
        """
        創建新的 A/B 測試
        
        Args:
            test_name: 測試名稱
            test_groups: 測試組配置列表
            
        Returns:
            bool: 是否創建成功
        """
        with self._lock:
            # 驗證流量比例總和為 1
            total_ratio = sum(group.traffic_ratio for group in test_groups)
            if abs(total_ratio - 1.0) > 0.01:
                print(f"錯誤: 流量比例總和必須為 1.0，當前為 {total_ratio}")
                return False
            
            # 重置測試
            self.test_enabled = True
            self.test_name = test_name
            self.test_groups = {group.group_id: group for group in test_groups}
            self.start_time = datetime.now()
            self.end_time = None
            self.test_records = []
            
            self._save_config()
            self._save_data()
            
            return True
    
    def assign_group(self, member_code: str) -> Optional[str]:
        """
        為會員分配測試組（基於一致性雜湊）
        
        Args:
            member_code: 會員代碼
            
        Returns:
            Optional[str]: 測試組 ID，如果測試未啟用則返回 None
        """
        if not self.test_enabled or not self.test_groups:
            return None
        
        # 使用 MD5 雜湊確保一致性分組
        hash_value = hashlib.md5(member_code.encode()).hexdigest()
        hash_int = int(hash_value[:8], 16)
        ratio = (hash_int % 10000) / 10000.0
        
        # 根據流量比例分配組別
        cumulative_ratio = 0.0
        for group_id, group in self.test_groups.items():
            cumulative_ratio += group.traffic_ratio
            if ratio < cumulative_ratio:
                return group_id
        
        # 容錯：返回最後一個組
        return list(self.test_groups.keys())[-1]
    
    def get_group_config(self, group_id: str) -> Optional[TestGroupConfig]:
        """
        獲取測試組配置
        
        Args:
            group_id: 測試組 ID
            
        Returns:
            Optional[TestGroupConfig]: 測試組配置
        """
        return self.test_groups.get(group_id)
    
    def is_enabled(self) -> bool:
        """檢查測試是否啟用"""
        return self.test_enabled
    
    def stop_test(self):
        """停止測試"""
        with self._lock:
            self.test_enabled = False
            self.end_time = datetime.now()
            self._save_config()

    
    def record_test_result(
        self,
        member_code: str,
        group_id: str,
        overall_score: float,
        relevance_score: float,
        novelty_score: float,
        explainability_score: float,
        diversity_score: float,
        response_time_ms: float,
        recommendation_count: int,
        strategy_used: str
    ):
        """
        記錄測試結果
        
        Args:
            member_code: 會員代碼
            group_id: 測試組 ID
            overall_score: 綜合可參考價值分數
            relevance_score: 相關性分數
            novelty_score: 新穎性分數
            explainability_score: 可解釋性分數
            diversity_score: 多樣性分數
            response_time_ms: 反應時間（毫秒）
            recommendation_count: 推薦數量
            strategy_used: 使用的策略
        """
        with self._lock:
            record = TestRecord(
                member_code=member_code,
                group_id=group_id,
                timestamp=datetime.now(),
                overall_score=overall_score,
                relevance_score=relevance_score,
                novelty_score=novelty_score,
                explainability_score=explainability_score,
                diversity_score=diversity_score,
                response_time_ms=response_time_ms,
                recommendation_count=recommendation_count,
                strategy_used=strategy_used
            )
            
            self.test_records.append(record)
            
            # 每次都儲存數據以確保持久化
            self._save_data()
    
    def calculate_group_statistics(self, group_id: str) -> Optional[GroupStatistics]:
        """
        計算測試組統計數據
        
        Args:
            group_id: 測試組 ID
            
        Returns:
            Optional[GroupStatistics]: 統計數據
        """
        group = self.test_groups.get(group_id)
        if not group:
            return None
        
        # 過濾該組的記錄
        group_records = [r for r in self.test_records if r.group_id == group_id]
        
        if not group_records:
            return GroupStatistics(
                group_id=group_id,
                group_name=group.group_name
            )
        
        # 計算統計數據
        stats = GroupStatistics(
            group_id=group_id,
            group_name=group.group_name,
            total_records=len(group_records)
        )
        
        # 可參考價值分數統計
        stats.overall_scores = [r.overall_score for r in group_records]
        stats.avg_overall_score = sum(stats.overall_scores) / len(stats.overall_scores)
        
        stats.avg_relevance_score = sum(r.relevance_score for r in group_records) / len(group_records)
        stats.avg_novelty_score = sum(r.novelty_score for r in group_records) / len(group_records)
        stats.avg_explainability_score = sum(r.explainability_score for r in group_records) / len(group_records)
        stats.avg_diversity_score = sum(r.diversity_score for r in group_records) / len(group_records)
        
        # 計算標準差
        if len(stats.overall_scores) > 1:
            mean = stats.avg_overall_score
            variance = sum((x - mean) ** 2 for x in stats.overall_scores) / len(stats.overall_scores)
            stats.std_overall_score = variance ** 0.5
        
        # 性能統計
        stats.response_times = [r.response_time_ms for r in group_records]
        stats.avg_response_time_ms = sum(stats.response_times) / len(stats.response_times)
        
        # 計算百分位數
        sorted_times = sorted(stats.response_times)
        n = len(sorted_times)
        stats.p50_response_time_ms = sorted_times[int(n * 0.50)]
        stats.p95_response_time_ms = sorted_times[int(n * 0.95)]
        stats.p99_response_time_ms = sorted_times[int(n * 0.99)] if n > 100 else sorted_times[-1]
        
        return stats
    
    def calculate_all_statistics(self) -> Dict[str, GroupStatistics]:
        """
        計算所有測試組的統計數據
        
        Returns:
            Dict[str, GroupStatistics]: 各組統計數據
        """
        return {
            group_id: self.calculate_group_statistics(group_id)
            for group_id in self.test_groups.keys()
        }
    
    def perform_statistical_test(
        self,
        group_a_id: str,
        group_b_id: str
    ) -> Dict[str, Any]:
        """
        執行統計顯著性檢驗（雙樣本 t 檢驗）
        
        Args:
            group_a_id: 測試組 A ID
            group_b_id: 測試組 B ID
            
        Returns:
            Dict: 檢驗結果
        """
        stats_a = self.calculate_group_statistics(group_a_id)
        stats_b = self.calculate_group_statistics(group_b_id)
        
        if not stats_a or not stats_b:
            return {
                'error': '無法獲取統計數據'
            }
        
        if stats_a.total_records < 30 or stats_b.total_records < 30:
            return {
                'error': '樣本數不足（每組至少需要 30 個樣本）',
                'group_a_samples': stats_a.total_records,
                'group_b_samples': stats_b.total_records
            }
        
        # 計算 t 統計量（簡化版本）
        mean_diff = stats_b.avg_overall_score - stats_a.avg_overall_score
        
        # 合併標準誤差
        n_a = stats_a.total_records
        n_b = stats_b.total_records
        
        if stats_a.std_overall_score == 0 and stats_b.std_overall_score == 0:
            # 如果兩組標準差都為 0，無法進行檢驗
            return {
                'error': '標準差為 0，無法進行統計檢驗'
            }
        
        pooled_std = ((stats_a.std_overall_score ** 2 / n_a) + 
                      (stats_b.std_overall_score ** 2 / n_b)) ** 0.5
        
        if pooled_std == 0:
            t_statistic = 0
        else:
            t_statistic = mean_diff / pooled_std
        
        # 簡化的 p 值估計（基於 t 統計量的絕對值）
        abs_t = abs(t_statistic)
        if abs_t > 2.576:  # 99% 信心水準
            p_value = 0.01
            significance = '***'
            is_significant = True
        elif abs_t > 1.96:  # 95% 信心水準
            p_value = 0.05
            significance = '**'
            is_significant = True
        elif abs_t > 1.645:  # 90% 信心水準
            p_value = 0.10
            significance = '*'
            is_significant = True
        else:
            p_value = 0.20
            significance = 'ns'
            is_significant = False
        
        # 計算效應大小（Cohen's d）
        pooled_std_effect = ((stats_a.std_overall_score ** 2 + stats_b.std_overall_score ** 2) / 2) ** 0.5
        if pooled_std_effect == 0:
            cohens_d = 0
        else:
            cohens_d = mean_diff / pooled_std_effect
        
        # 判斷效應大小
        if abs(cohens_d) < 0.2:
            effect_size = 'small'
        elif abs(cohens_d) < 0.5:
            effect_size = 'medium'
        else:
            effect_size = 'large'
        
        return {
            'group_a': {
                'id': group_a_id,
                'name': stats_a.group_name,
                'mean': stats_a.avg_overall_score,
                'std': stats_a.std_overall_score,
                'n': stats_a.total_records
            },
            'group_b': {
                'id': group_b_id,
                'name': stats_b.group_name,
                'mean': stats_b.avg_overall_score,
                'std': stats_b.std_overall_score,
                'n': stats_b.total_records
            },
            'test_results': {
                'mean_difference': mean_diff,
                'improvement_pct': (mean_diff / stats_a.avg_overall_score * 100) if stats_a.avg_overall_score > 0 else 0,
                't_statistic': t_statistic,
                'p_value': p_value,
                'significance': significance,
                'is_significant': is_significant,
                'cohens_d': cohens_d,
                'effect_size': effect_size
            },
            'interpretation': self._interpret_results(mean_diff, is_significant, effect_size)
        }
    
    def _interpret_results(
        self,
        mean_diff: float,
        is_significant: bool,
        effect_size: str
    ) -> str:
        """
        解釋統計檢驗結果
        
        Args:
            mean_diff: 平均差異
            is_significant: 是否顯著
            effect_size: 效應大小
            
        Returns:
            str: 結果解釋
        """
        if not is_significant:
            return "兩組之間沒有統計顯著差異，建議繼續收集數據或選擇原有策略。"
        
        direction = "更好" if mean_diff > 0 else "更差"
        
        if effect_size == 'large':
            return f"測試組 B 的表現顯著{direction}（大效應），建議採用測試組 B 的策略。"
        elif effect_size == 'medium':
            return f"測試組 B 的表現顯著{direction}（中等效應），建議考慮採用測試組 B 的策略。"
        else:
            return f"測試組 B 的表現顯著{direction}（小效應），差異較小，可根據其他因素決策。"
    
    def generate_comparison_report(self) -> Dict[str, Any]:
        """
        生成 A/B 測試對比報告
        
        Returns:
            Dict: 對比報告
        """
        # 允許在測試進行中或已完成時生成報告
        if not self.test_enabled and not self.end_time and len(self.test_records) == 0:
            return {
                'error': '測試未啟用或無數據'
            }
        
        # 計算所有組的統計數據
        all_stats = self.calculate_all_statistics()
        
        # 準備報告
        report = {
            'test_info': {
                'test_name': self.test_name,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None,
                'duration_hours': (
                    (self.end_time - self.start_time).total_seconds() / 3600
                    if self.start_time and self.end_time else None
                ),
                'total_records': len(self.test_records)
            },
            'groups': {},
            'comparisons': []
        }
        
        # 添加各組統計
        for group_id, stats in all_stats.items():
            if stats:
                report['groups'][group_id] = {
                    'group_name': stats.group_name,
                    'total_records': stats.total_records,
                    'quality_scores': {
                        'overall': stats.avg_overall_score,
                        'relevance': stats.avg_relevance_score,
                        'novelty': stats.avg_novelty_score,
                        'explainability': stats.avg_explainability_score,
                        'diversity': stats.avg_diversity_score,
                        'std': stats.std_overall_score
                    },
                    'performance': {
                        'avg_response_time_ms': stats.avg_response_time_ms,
                        'p50_response_time_ms': stats.p50_response_time_ms,
                        'p95_response_time_ms': stats.p95_response_time_ms,
                        'p99_response_time_ms': stats.p99_response_time_ms
                    }
                }
        
        # 執行兩兩比較（如果有多個組）
        group_ids = list(self.test_groups.keys())
        if len(group_ids) >= 2:
            # 以第一組為對照組，與其他組比較
            control_group = group_ids[0]
            for test_group in group_ids[1:]:
                comparison = self.perform_statistical_test(control_group, test_group)
                if 'error' not in comparison:
                    report['comparisons'].append(comparison)
        
        # 找出最佳組
        if all_stats:
            best_group_id = max(
                all_stats.keys(),
                key=lambda gid: all_stats[gid].avg_overall_score if all_stats[gid] else 0
            )
            best_stats = all_stats[best_group_id]
            report['recommendation'] = {
                'best_group_id': best_group_id,
                'best_group_name': best_stats.group_name if best_stats else '',
                'best_score': best_stats.avg_overall_score if best_stats else 0
            }
        
        return report
    
    def export_raw_data(self) -> List[Dict[str, Any]]:
        """
        匯出原始測試數據
        
        Returns:
            List[Dict]: 原始數據列表
        """
        return [
            {
                'member_code': record.member_code,
                'group_id': record.group_id,
                'timestamp': record.timestamp.isoformat(),
                'overall_score': record.overall_score,
                'relevance_score': record.relevance_score,
                'novelty_score': record.novelty_score,
                'explainability_score': record.explainability_score,
                'diversity_score': record.diversity_score,
                'response_time_ms': record.response_time_ms,
                'recommendation_count': record.recommendation_count,
                'strategy_used': record.strategy_used
            }
            for record in self.test_records
        ]


# 全域實例
_ab_testing_framework: Optional[ABTestingFramework] = None


def get_ab_testing_framework() -> ABTestingFramework:
    """獲取全域 A/B 測試框架實例"""
    global _ab_testing_framework
    if _ab_testing_framework is None:
        _ab_testing_framework = ABTestingFramework()
    return _ab_testing_framework
