"""
性能追蹤器
追蹤推薦系統各階段的反應時間，提供性能統計和慢查詢檢測
"""
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import numpy as np
from src.models.enhanced_data_models import PerformanceMetrics, PerformanceStats


class PerformanceTracker:
    """
    性能追蹤器
    
    追蹤推薦流程中每個環節的耗時，計算百分位數統計，識別慢查詢
    """
    
    # 慢查詢閾值（毫秒）
    SLOW_QUERY_THRESHOLD_MS = 1000
    
    def __init__(self, slow_query_threshold_ms: float = SLOW_QUERY_THRESHOLD_MS):
        """
        初始化性能追蹤器
        
        Args:
            slow_query_threshold_ms: 慢查詢閾值（毫秒），預設1000ms
        """
        self.slow_query_threshold_ms = slow_query_threshold_ms
        
        # 追蹤中的請求：{request_id: {stage: timestamp}}
        self._tracking_requests: Dict[str, Dict[str, float]] = {}
        
        # 歷史記錄：存儲已完成的性能指標
        self._history: List[PerformanceMetrics] = []
        
    def start_tracking(self, request_id: str) -> None:
        """
        開始追蹤一個推薦請求
        
        Args:
            request_id: 請求ID
        """
        if request_id in self._tracking_requests:
            raise ValueError(f"請求 {request_id} 已經在追蹤中")
        
        # 記錄開始時間
        self._tracking_requests[request_id] = {
            'start': time.time()
        }
    
    def track_stage(self, request_id: str, stage: str) -> None:
        """
        記錄一個階段的完成時間
        
        Args:
            request_id: 請求ID
            stage: 階段名稱
        """
        if request_id not in self._tracking_requests:
            raise ValueError(f"請求 {request_id} 未開始追蹤")
        
        # 記錄階段完成時間
        self._tracking_requests[request_id][stage] = time.time()
    
    def end_tracking(self, request_id: str) -> PerformanceMetrics:
        """
        結束追蹤並返回性能指標
        
        Args:
            request_id: 請求ID
            
        Returns:
            PerformanceMetrics: 性能指標
        """
        if request_id not in self._tracking_requests:
            raise ValueError(f"請求 {request_id} 未開始追蹤")
        
        tracking_data = self._tracking_requests[request_id]
        start_time = tracking_data['start']
        end_time = time.time()
        
        # 計算總耗時
        total_time_ms = (end_time - start_time) * 1000
        
        # 計算各階段耗時
        stage_times = {}
        previous_time = start_time
        
        for stage, stage_end_time in tracking_data.items():
            if stage == 'start':
                continue
            
            stage_duration_ms = (stage_end_time - previous_time) * 1000
            stage_times[stage] = stage_duration_ms
            previous_time = stage_end_time
        
        # 判斷是否為慢查詢
        is_slow_query = total_time_ms > self.slow_query_threshold_ms
        
        # 創建性能指標
        metrics = PerformanceMetrics(
            request_id=request_id,
            total_time_ms=total_time_ms,
            stage_times=stage_times,
            is_slow_query=is_slow_query,
            timestamp=datetime.now()
        )
        
        # 保存到歷史記錄
        self._history.append(metrics)
        
        # 清理追蹤數據
        del self._tracking_requests[request_id]
        
        return metrics
    
    def get_statistics(self, time_window: Optional[timedelta] = None) -> PerformanceStats:
        """
        獲取指定時間窗口的統計數據
        
        Args:
            time_window: 時間窗口，None表示所有歷史數據
            
        Returns:
            PerformanceStats: 性能統計
        """
        if not self._history:
            # 沒有歷史數據，返回空統計
            return PerformanceStats(
                time_window=time_window or timedelta(hours=1),
                total_requests=0,
                p50_time_ms=0.0,
                p95_time_ms=0.0,
                p99_time_ms=0.0,
                avg_time_ms=0.0,
                slow_query_count=0,
                slow_query_rate=0.0,
                stage_avg_times={},
                timestamp=datetime.now()
            )
        
        # 過濾時間窗口內的數據
        now = datetime.now()
        if time_window:
            cutoff_time = now - time_window
            filtered_metrics = [
                m for m in self._history 
                if m.timestamp >= cutoff_time
            ]
        else:
            filtered_metrics = self._history
            time_window = timedelta(hours=1)  # 預設時間窗口
        
        if not filtered_metrics:
            return PerformanceStats(
                time_window=time_window,
                total_requests=0,
                p50_time_ms=0.0,
                p95_time_ms=0.0,
                p99_time_ms=0.0,
                avg_time_ms=0.0,
                slow_query_count=0,
                slow_query_rate=0.0,
                stage_avg_times={},
                timestamp=now
            )
        
        # 提取總耗時列表
        total_times = [m.total_time_ms for m in filtered_metrics]
        
        # 計算百分位數
        p50_time_ms = float(np.percentile(total_times, 50))
        p95_time_ms = float(np.percentile(total_times, 95))
        p99_time_ms = float(np.percentile(total_times, 99))
        avg_time_ms = float(np.mean(total_times))
        
        # 計算慢查詢統計
        slow_query_count = sum(1 for m in filtered_metrics if m.is_slow_query)
        slow_query_rate = slow_query_count / len(filtered_metrics) if filtered_metrics else 0.0
        
        # 計算各階段平均耗時
        stage_times_sum = defaultdict(float)
        stage_counts = defaultdict(int)
        
        for metrics in filtered_metrics:
            for stage, duration in metrics.stage_times.items():
                stage_times_sum[stage] += duration
                stage_counts[stage] += 1
        
        stage_avg_times = {
            stage: stage_times_sum[stage] / stage_counts[stage]
            for stage in stage_times_sum
        }
        
        return PerformanceStats(
            time_window=time_window,
            total_requests=len(filtered_metrics),
            p50_time_ms=p50_time_ms,
            p95_time_ms=p95_time_ms,
            p99_time_ms=p99_time_ms,
            avg_time_ms=avg_time_ms,
            slow_query_count=slow_query_count,
            slow_query_rate=slow_query_rate,
            stage_avg_times=stage_avg_times,
            timestamp=now
        )
    
    def clear_history(self) -> None:
        """清空歷史記錄"""
        self._history.clear()
    
    def get_history_count(self) -> int:
        """獲取歷史記錄數量"""
        return len(self._history)
