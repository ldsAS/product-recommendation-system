"""
效能追蹤系統
追蹤 API 回應時間、推薦轉換率和其他效能指標
支援 Prometheus 格式匯出
"""
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from dataclasses import dataclass, field
import threading
import json


@dataclass
class MetricPoint:
    """指標資料點"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSummary:
    """指標摘要"""
    count: int = 0
    sum: float = 0.0
    min: float = float('inf')
    max: float = float('-inf')
    avg: float = 0.0
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0


class MetricsCollector:
    """指標收集器"""
    
    def __init__(self, max_history: int = 10000):
        """
        初始化指標收集器
        
        Args:
            max_history: 保留的歷史資料點數量
        """
        self.max_history = max_history
        self._lock = threading.Lock()
        
        # 計數器
        self._counters: Dict[str, int] = defaultdict(int)
        
        # 計量器
        self._gauges: Dict[str, float] = {}
        
        # 直方圖（用於追蹤分布）
        self._histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        
        # 時間序列資料
        self._timeseries: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        
        # 啟動時間
        self._start_time = time.time()
    
    def increment_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """
        增加計數器
        
        Args:
            name: 計數器名稱
            value: 增加的值
            labels: 標籤
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += value
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        設置計量器
        
        Args:
            name: 計量器名稱
            value: 值
            labels: 標籤
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        觀察直方圖值
        
        Args:
            name: 直方圖名稱
            value: 觀察值
            labels: 標籤
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._histograms[key].append(value)
            
            # 同時記錄時間序列
            self._timeseries[key].append(MetricPoint(
                timestamp=datetime.now(),
                value=value,
                labels=labels or {}
            ))
    
    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> int:
        """獲取計數器值"""
        with self._lock:
            key = self._make_key(name, labels)
            return self._counters.get(key, 0)
    
    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """獲取計量器值"""
        with self._lock:
            key = self._make_key(name, labels)
            return self._gauges.get(key, 0.0)
    
    def get_histogram_summary(self, name: str, labels: Optional[Dict[str, str]] = None) -> MetricSummary:
        """
        獲取直方圖摘要
        
        Args:
            name: 直方圖名稱
            labels: 標籤
            
        Returns:
            MetricSummary: 指標摘要
        """
        with self._lock:
            key = self._make_key(name, labels)
            values = list(self._histograms.get(key, []))
            
            if not values:
                return MetricSummary()
            
            sorted_values = sorted(values)
            count = len(sorted_values)
            
            return MetricSummary(
                count=count,
                sum=sum(sorted_values),
                min=sorted_values[0],
                max=sorted_values[-1],
                avg=sum(sorted_values) / count,
                p50=self._percentile(sorted_values, 50),
                p95=self._percentile(sorted_values, 95),
                p99=self._percentile(sorted_values, 99)
            )
    
    def get_timeseries(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[MetricPoint]:
        """
        獲取時間序列資料
        
        Args:
            name: 指標名稱
            labels: 標籤
            start_time: 開始時間
            end_time: 結束時間
            
        Returns:
            List[MetricPoint]: 時間序列資料點列表
        """
        with self._lock:
            key = self._make_key(name, labels)
            points = list(self._timeseries.get(key, []))
            
            # 過濾時間範圍
            if start_time:
                points = [p for p in points if p.timestamp >= start_time]
            if end_time:
                points = [p for p in points if p.timestamp <= end_time]
            
            return points
    
    def get_uptime_seconds(self) -> float:
        """獲取運行時間（秒）"""
        return time.time() - self._start_time
    
    def reset(self):
        """重置所有指標"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timeseries.clear()
    
    def export_prometheus(self) -> str:
        """
        匯出 Prometheus 格式的指標
        
        Returns:
            str: Prometheus 格式的指標文字
        """
        lines = []
        
        with self._lock:
            # 匯出計數器
            for key, value in self._counters.items():
                name, labels = self._parse_key(key)
                labels_str = self._format_labels(labels)
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name}{labels_str} {value}")
            
            # 匯出計量器
            for key, value in self._gauges.items():
                name, labels = self._parse_key(key)
                labels_str = self._format_labels(labels)
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name}{labels_str} {value}")
            
            # 匯出直方圖摘要
            for key, values in self._histograms.items():
                if not values:
                    continue
                
                name, labels = self._parse_key(key)
                summary = self.get_histogram_summary(name, labels)
                labels_str = self._format_labels(labels)
                
                lines.append(f"# TYPE {name} summary")
                lines.append(f"{name}_count{labels_str} {summary.count}")
                lines.append(f"{name}_sum{labels_str} {summary.sum}")
                lines.append(f"{name}{{quantile=\"0.5\"{self._format_labels(labels, prefix=',')}}} {summary.p50}")
                lines.append(f"{name}{{quantile=\"0.95\"{self._format_labels(labels, prefix=',')}}} {summary.p95}")
                lines.append(f"{name}{{quantile=\"0.99\"{self._format_labels(labels, prefix=',')}}} {summary.p99}")
        
        return '\n'.join(lines)
    
    def export_json(self) -> Dict[str, Any]:
        """
        匯出 JSON 格式的指標
        
        Returns:
            Dict: JSON 格式的指標
        """
        with self._lock:
            return {
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'histograms': {
                    key: {
                        'summary': self.get_histogram_summary(*self._parse_key(key)).__dict__,
                        'values': list(values)
                    }
                    for key, values in self._histograms.items()
                },
                'uptime_seconds': self.get_uptime_seconds(),
                'timestamp': datetime.now().isoformat()
            }
    
    @staticmethod
    def _make_key(name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """建立指標鍵"""
        if not labels:
            return name
        labels_str = ','.join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{labels_str}}}"
    
    @staticmethod
    def _parse_key(key: str) -> tuple:
        """解析指標鍵"""
        if '{' not in key:
            return key, {}
        
        name, labels_str = key.split('{', 1)
        labels_str = labels_str.rstrip('}')
        
        labels = {}
        if labels_str:
            for pair in labels_str.split(','):
                k, v = pair.split('=', 1)
                labels[k] = v
        
        return name, labels
    
    @staticmethod
    def _format_labels(labels: Dict[str, str], prefix: str = '') -> str:
        """格式化標籤為 Prometheus 格式"""
        if not labels:
            return ''
        labels_str = ','.join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{prefix}{{{labels_str}}}"
    
    @staticmethod
    def _percentile(sorted_values: List[float], percentile: float) -> float:
        """計算百分位數"""
        if not sorted_values:
            return 0.0
        
        index = int(len(sorted_values) * percentile / 100)
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]


class PerformanceTracker:
    """效能追蹤器"""
    
    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        """
        初始化效能追蹤器
        
        Args:
            metrics_collector: 指標收集器
        """
        self.metrics = metrics_collector or MetricsCollector()
    
    def track_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float
    ):
        """
        追蹤 API 請求
        
        Args:
            endpoint: 端點
            method: HTTP 方法
            status_code: 狀態碼
            response_time_ms: 回應時間（毫秒）
        """
        labels = {
            'endpoint': endpoint,
            'method': method,
            'status': str(status_code)
        }
        
        # 增加請求計數
        self.metrics.increment_counter('api_requests_total', labels=labels)
        
        # 記錄回應時間
        self.metrics.observe_histogram('api_response_time_ms', response_time_ms, labels=labels)
        
        # 如果是錯誤，增加錯誤計數
        if status_code >= 400:
            self.metrics.increment_counter('api_errors_total', labels=labels)
    
    def track_recommendation(
        self,
        member_code: str,
        num_recommendations: int,
        response_time_ms: float,
        model_version: str
    ):
        """
        追蹤推薦請求
        
        Args:
            member_code: 會員編號
            num_recommendations: 推薦數量
            response_time_ms: 回應時間（毫秒）
            model_version: 模型版本
        """
        labels = {'model_version': model_version}
        
        # 增加推薦請求計數
        self.metrics.increment_counter('recommendations_total', labels=labels)
        
        # 記錄推薦數量
        self.metrics.observe_histogram('recommendations_count', num_recommendations, labels=labels)
        
        # 記錄回應時間
        self.metrics.observe_histogram('recommendation_response_time_ms', response_time_ms, labels=labels)
    
    def track_conversion(
        self,
        member_code: str,
        product_id: str,
        converted: bool,
        model_version: str
    ):
        """
        追蹤轉換
        
        Args:
            member_code: 會員編號
            product_id: 產品ID
            converted: 是否轉換
            model_version: 模型版本
        """
        labels = {'model_version': model_version}
        
        # 增加轉換計數
        if converted:
            self.metrics.increment_counter('conversions_total', labels=labels)
        
        # 增加總推薦計數（用於計算轉換率）
        self.metrics.increment_counter('recommendations_shown_total', labels=labels)
    
    def track_model_load(self, model_version: str, load_time_ms: float):
        """
        追蹤模型載入
        
        Args:
            model_version: 模型版本
            load_time_ms: 載入時間（毫秒）
        """
        labels = {'model_version': model_version}
        
        # 記錄載入時間
        self.metrics.observe_histogram('model_load_time_ms', load_time_ms, labels=labels)
        
        # 增加載入計數
        self.metrics.increment_counter('model_loads_total', labels=labels)
    
    def get_api_metrics(self) -> Dict[str, Any]:
        """
        獲取 API 指標
        
        Returns:
            Dict: API 指標
        """
        total_requests = self.metrics.get_counter('api_requests_total')
        total_errors = self.metrics.get_counter('api_errors_total')
        response_time_summary = self.metrics.get_histogram_summary('api_response_time_ms')
        
        return {
            'total_requests': total_requests,
            'total_errors': total_errors,
            'error_rate': total_errors / total_requests if total_requests > 0 else 0.0,
            'response_time': {
                'avg_ms': response_time_summary.avg,
                'p50_ms': response_time_summary.p50,
                'p95_ms': response_time_summary.p95,
                'p99_ms': response_time_summary.p99,
                'min_ms': response_time_summary.min,
                'max_ms': response_time_summary.max
            }
        }
    
    def get_recommendation_metrics(self, model_version: Optional[str] = None) -> Dict[str, Any]:
        """
        獲取推薦指標
        
        Args:
            model_version: 模型版本（可選）
            
        Returns:
            Dict: 推薦指標
        """
        labels = {'model_version': model_version} if model_version else None
        
        total_recommendations = self.metrics.get_counter('recommendations_total', labels=labels)
        total_conversions = self.metrics.get_counter('conversions_total', labels=labels)
        total_shown = self.metrics.get_counter('recommendations_shown_total', labels=labels)
        
        response_time_summary = self.metrics.get_histogram_summary(
            'recommendation_response_time_ms',
            labels=labels
        )
        
        return {
            'total_recommendations': total_recommendations,
            'total_conversions': total_conversions,
            'total_shown': total_shown,
            'conversion_rate': total_conversions / total_shown if total_shown > 0 else 0.0,
            'response_time': {
                'avg_ms': response_time_summary.avg,
                'p50_ms': response_time_summary.p50,
                'p95_ms': response_time_summary.p95,
                'p99_ms': response_time_summary.p99
            }
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        獲取所有指標
        
        Returns:
            Dict: 所有指標
        """
        return {
            'api': self.get_api_metrics(),
            'recommendations': self.get_recommendation_metrics(),
            'uptime_seconds': self.metrics.get_uptime_seconds(),
            'timestamp': datetime.now().isoformat()
        }


# 全域效能追蹤器實例
_performance_tracker: Optional[PerformanceTracker] = None


def get_performance_tracker() -> PerformanceTracker:
    """獲取全域效能追蹤器"""
    global _performance_tracker
    if _performance_tracker is None:
        _performance_tracker = PerformanceTracker()
    return _performance_tracker


def setup_performance_tracker(metrics_collector: Optional[MetricsCollector] = None) -> PerformanceTracker:
    """
    設置全域效能追蹤器
    
    Args:
        metrics_collector: 指標收集器
        
    Returns:
        PerformanceTracker: 效能追蹤器實例
    """
    global _performance_tracker
    _performance_tracker = PerformanceTracker(metrics_collector)
    return _performance_tracker


if __name__ == "__main__":
    # 測試效能追蹤系統
    print("測試效能追蹤系統...")
    
    # 建立效能追蹤器
    tracker = PerformanceTracker()
    
    # 模擬 API 請求
    print("\n模擬 API 請求...")
    for i in range(10):
        tracker.track_api_request(
            endpoint="/api/v1/recommendations",
            method="POST",
            status_code=200,
            response_time_ms=100 + i * 10
        )
    
    # 模擬一些錯誤
    tracker.track_api_request(
        endpoint="/api/v1/recommendations",
        method="POST",
        status_code=400,
        response_time_ms=50
    )
    
    # 模擬推薦請求
    print("模擬推薦請求...")
    for i in range(5):
        tracker.track_recommendation(
            member_code=f"CU{i:06d}",
            num_recommendations=5,
            response_time_ms=200 + i * 20,
            model_version="v1.0.0"
        )
    
    # 模擬轉換
    print("模擬轉換...")
    for i in range(3):
        tracker.track_conversion(
            member_code=f"CU{i:06d}",
            product_id=f"P{i:05d}",
            converted=True,
            model_version="v1.0.0"
        )
    
    # 獲取指標
    print("\n=== API 指標 ===")
    api_metrics = tracker.get_api_metrics()
    print(json.dumps(api_metrics, indent=2, ensure_ascii=False))
    
    print("\n=== 推薦指標 ===")
    rec_metrics = tracker.get_recommendation_metrics()
    print(json.dumps(rec_metrics, indent=2, ensure_ascii=False))
    
    print("\n=== 所有指標 ===")
    all_metrics = tracker.get_all_metrics()
    print(json.dumps(all_metrics, indent=2, ensure_ascii=False))
    
    print("\n=== Prometheus 格式 ===")
    prometheus_output = tracker.metrics.export_prometheus()
    print(prometheus_output[:500] + "...")
    
    print("\n✓ 效能追蹤系統測試完成")
