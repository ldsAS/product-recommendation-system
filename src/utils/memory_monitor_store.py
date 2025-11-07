"""
內存監控數據存儲
用於在沒有資料庫的情況下臨時存儲監控數據
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from collections import deque
import threading

# 台灣時區 (UTC+8)
TW_TIMEZONE = timezone(timedelta(hours=8))


class MemoryMonitorStore:
    """內存監控數據存儲"""
    
    def __init__(self, max_records: int = 1000):
        """
        初始化內存存儲
        
        Args:
            max_records: 最大記錄數量
        """
        self.max_records = max_records
        self.records = deque(maxlen=max_records)
        self.lock = threading.Lock()
    
    def add_record(self, record: Dict[str, Any]):
        """
        添加監控記錄
        
        Args:
            record: 監控記錄
        """
        with self.lock:
            # 添加時間戳（使用台灣時區）
            if 'timestamp' not in record:
                record['timestamp'] = datetime.now(TW_TIMEZONE).isoformat()
            
            self.records.append(record)
    
    def get_records(
        self,
        time_window_minutes: int = 60,
        member_code: str = None
    ) -> List[Dict[str, Any]]:
        """
        獲取監控記錄
        
        Args:
            time_window_minutes: 時間窗口（分鐘）
            member_code: 會員編號（可選）
            
        Returns:
            List[Dict[str, Any]]: 監控記錄列表
        """
        with self.lock:
            cutoff_time = datetime.now(TW_TIMEZONE) - timedelta(minutes=time_window_minutes)
            
            filtered_records = []
            for record in self.records:
                # 解析時間戳
                try:
                    record_time = datetime.fromisoformat(record['timestamp'])
                    # 確保時間戳有時區信息
                    if record_time.tzinfo is None:
                        record_time = record_time.replace(tzinfo=TW_TIMEZONE)
                    if record_time < cutoff_time:
                        continue
                except:
                    continue
                
                # 過濾會員編號
                if member_code and record.get('member_code') != member_code:
                    continue
                
                filtered_records.append(record)
            
            return filtered_records
    
    def get_stats(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """
        獲取統計數據
        
        Args:
            time_window_minutes: 時間窗口（分鐘）
            
        Returns:
            Dict[str, Any]: 統計數據
        """
        records = self.get_records(time_window_minutes)
        
        if not records:
            return {
                'total_records': 0,
                'unique_members': 0,
                'quality_metrics': {},
                'performance_metrics': {}
            }
        
        # 計算統計
        total_records = len(records)
        unique_members = len(set(r.get('member_code') for r in records if r.get('member_code')))
        
        # 品質指標
        quality_scores = {
            'overall_score': [],
            'relevance_score': [],
            'novelty_score': [],
            'explainability_score': [],
            'diversity_score': []
        }
        
        # 性能指標
        response_times = []
        
        for record in records:
            # 品質分數
            if 'reference_value_score' in record:
                rvs = record['reference_value_score']
                quality_scores['overall_score'].append(rvs.get('overall_score', 0))
                quality_scores['relevance_score'].append(rvs.get('relevance_score', 0))
                quality_scores['novelty_score'].append(rvs.get('novelty_score', 0))
                quality_scores['explainability_score'].append(rvs.get('explainability_score', 0))
                quality_scores['diversity_score'].append(rvs.get('diversity_score', 0))
            
            # 性能指標
            if 'response_time_ms' in record:
                response_times.append(record['response_time_ms'])
        
        # 計算平均值和百分位數
        def calc_stats(values):
            if not values:
                return {'avg': 0, 'min': 0, 'max': 0, 'p50': 0, 'p95': 0, 'p99': 0}
            
            sorted_values = sorted(values)
            n = len(sorted_values)
            
            return {
                'avg': sum(values) / n,
                'min': sorted_values[0],
                'max': sorted_values[-1],
                'p50': sorted_values[int(n * 0.5)],
                'p95': sorted_values[int(n * 0.95)] if n > 1 else sorted_values[0],
                'p99': sorted_values[int(n * 0.99)] if n > 1 else sorted_values[0]
            }
        
        quality_metrics = {
            key: calc_stats(values)
            for key, values in quality_scores.items()
        }
        
        performance_metrics = {
            'response_time_ms': calc_stats(response_times)
        }
        
        return {
            'total_records': total_records,
            'unique_members': unique_members,
            'quality_metrics': quality_metrics,
            'performance_metrics': performance_metrics,
            'degradation_count': sum(1 for r in records if r.get('is_degraded', False))
        }


# 全局實例
_monitor_store = None


def get_monitor_store() -> MemoryMonitorStore:
    """獲取全局監控存儲實例"""
    global _monitor_store
    if _monitor_store is None:
        _monitor_store = MemoryMonitorStore()
    return _monitor_store
