"""
品質監控器
監控推薦系統的品質和性能，提供告警和報告功能
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from collections import defaultdict
import numpy as np

from src.models.enhanced_data_models import (
    MonitoringRecord,
    ReferenceValueScore,
    PerformanceMetrics,
    QualityCheckResult,
    PerformanceCheckResult,
    Alert,
    AlertLevel,
    MonitoringReport
)


class QualityMonitor:
    """
    品質監控器
    
    監控推薦結果的可參考價值和性能指標，提供告警和報告功能
    """
    
    # 品質閾值配置
    QUALITY_THRESHOLDS = {
        'overall_score': {
            'critical': 40,  # 低於40分觸發嚴重告警
            'warning': 50,   # 低於50分觸發警告
            'target': 60     # 目標值
        },
        'relevance_score': {
            'critical': 50,
            'warning': 60,
            'target': 70
        },
        'novelty_score': {
            'critical': 15,
            'warning': 20,
            'target': 30
        },
        'explainability_score': {
            'critical': 60,
            'warning': 70,
            'target': 80
        },
        'diversity_score': {
            'critical': 40,
            'warning': 50,
            'target': 60
        }
    }
    
    # 性能閾值配置
    PERFORMANCE_THRESHOLDS = {
        'total_time_ms': {
            'p50': 200,
            'p95': 500,
            'p99': 1000
        },
        'feature_loading_ms': {
            'max': 100
        },
        'model_inference_ms': {
            'max': 200
        }
    }
    
    def __init__(self):
        """初始化品質監控器"""
        # 監控記錄存儲（記憶體）
        self._records: List[MonitoringRecord] = []
        
        # 告警記錄
        self._alerts: List[Alert] = []
    
    def record_recommendation(
        self,
        request_id: str,
        member_code: str,
        value_score: ReferenceValueScore,
        performance_metrics: PerformanceMetrics,
        recommendation_count: int = 0,
        strategy_used: str = "hybrid",
        is_degraded: bool = False
    ) -> None:
        """
        記錄一次推薦的品質和性能數據
        
        Args:
            request_id: 請求ID
            member_code: 會員編號
            value_score: 可參考價值分數
            performance_metrics: 性能指標
            recommendation_count: 推薦數量
            strategy_used: 使用的推薦策略
            is_degraded: 是否使用降級策略
        """
        # 提取各階段耗時
        stage_times = performance_metrics.stage_times
        
        # 創建監控記錄
        record = MonitoringRecord(
            request_id=request_id,
            member_code=member_code,
            timestamp=datetime.now(),
            # 品質指標
            overall_score=value_score.overall_score,
            relevance_score=value_score.relevance_score,
            novelty_score=value_score.novelty_score,
            explainability_score=value_score.explainability_score,
            diversity_score=value_score.diversity_score,
            # 性能指標
            total_time_ms=performance_metrics.total_time_ms,
            feature_loading_ms=stage_times.get('feature_loading', 0.0),
            model_inference_ms=stage_times.get('model_inference', 0.0),
            reason_generation_ms=stage_times.get('reason_generation', 0.0),
            quality_evaluation_ms=stage_times.get('quality_evaluation', 0.0),
            # 元資料
            recommendation_count=recommendation_count,
            strategy_used=strategy_used,
            is_degraded=is_degraded
        )
        
        # 存儲到記憶體
        self._records.append(record)
    
    def get_records(
        self,
        time_window: Optional[timedelta] = None,
        member_code: Optional[str] = None
    ) -> List[MonitoringRecord]:
        """
        查詢監控記錄
        
        Args:
            time_window: 時間窗口，None表示所有記錄
            member_code: 會員編號，None表示所有會員
        
        Returns:
            List[MonitoringRecord]: 監控記錄列表
        """
        records = self._records
        
        # 過濾時間窗口
        if time_window:
            cutoff_time = datetime.now() - time_window
            records = [r for r in records if r.timestamp >= cutoff_time]
        
        # 過濾會員
        if member_code:
            records = [r for r in records if r.member_code == member_code]
        
        return records

    
    def check_quality_threshold(
        self,
        value_score: ReferenceValueScore
    ) -> QualityCheckResult:
        """
        檢查品質是否達標
        
        Args:
            value_score: 可參考價值分數
        
        Returns:
            QualityCheckResult: 品質檢查結果
        """
        failed_metrics = []
        warnings = []
        
        # 檢查綜合可參考價值分數
        if value_score.overall_score < self.QUALITY_THRESHOLDS['overall_score']['critical']:
            failed_metrics.append(f"綜合分數過低: {value_score.overall_score:.1f} < {self.QUALITY_THRESHOLDS['overall_score']['critical']}")
        elif value_score.overall_score < self.QUALITY_THRESHOLDS['overall_score']['warning']:
            warnings.append(f"綜合分數低於警告線: {value_score.overall_score:.1f} < {self.QUALITY_THRESHOLDS['overall_score']['warning']}")
        
        # 檢查相關性分數
        if value_score.relevance_score < self.QUALITY_THRESHOLDS['relevance_score']['critical']:
            failed_metrics.append(f"相關性分數過低: {value_score.relevance_score:.1f} < {self.QUALITY_THRESHOLDS['relevance_score']['critical']}")
        elif value_score.relevance_score < self.QUALITY_THRESHOLDS['relevance_score']['warning']:
            warnings.append(f"相關性分數低於警告線: {value_score.relevance_score:.1f} < {self.QUALITY_THRESHOLDS['relevance_score']['warning']}")
        
        # 檢查新穎性分數
        if value_score.novelty_score < self.QUALITY_THRESHOLDS['novelty_score']['critical']:
            failed_metrics.append(f"新穎性分數過低: {value_score.novelty_score:.1f} < {self.QUALITY_THRESHOLDS['novelty_score']['critical']}")
        elif value_score.novelty_score < self.QUALITY_THRESHOLDS['novelty_score']['warning']:
            warnings.append(f"新穎性分數低於警告線: {value_score.novelty_score:.1f} < {self.QUALITY_THRESHOLDS['novelty_score']['warning']}")
        
        # 檢查可解釋性分數
        if value_score.explainability_score < self.QUALITY_THRESHOLDS['explainability_score']['critical']:
            failed_metrics.append(f"可解釋性分數過低: {value_score.explainability_score:.1f} < {self.QUALITY_THRESHOLDS['explainability_score']['critical']}")
        elif value_score.explainability_score < self.QUALITY_THRESHOLDS['explainability_score']['warning']:
            warnings.append(f"可解釋性分數低於警告線: {value_score.explainability_score:.1f} < {self.QUALITY_THRESHOLDS['explainability_score']['warning']}")
        
        # 檢查多樣性分數
        if value_score.diversity_score < self.QUALITY_THRESHOLDS['diversity_score']['critical']:
            failed_metrics.append(f"多樣性分數過低: {value_score.diversity_score:.1f} < {self.QUALITY_THRESHOLDS['diversity_score']['critical']}")
        elif value_score.diversity_score < self.QUALITY_THRESHOLDS['diversity_score']['warning']:
            warnings.append(f"多樣性分數低於警告線: {value_score.diversity_score:.1f} < {self.QUALITY_THRESHOLDS['diversity_score']['warning']}")
        
        # 判斷是否通過檢查
        passed = len(failed_metrics) == 0
        
        return QualityCheckResult(
            passed=passed,
            overall_score=value_score.overall_score,
            failed_metrics=failed_metrics,
            warnings=warnings,
            timestamp=datetime.now()
        )

    
    def check_performance_threshold(
        self,
        performance_metrics: PerformanceMetrics
    ) -> PerformanceCheckResult:
        """
        檢查性能是否達標
        
        Args:
            performance_metrics: 性能指標
        
        Returns:
            PerformanceCheckResult: 性能檢查結果
        """
        failed_metrics = []
        warnings = []
        
        # 檢查總反應時間（使用P99閾值作為嚴重告警線）
        if performance_metrics.total_time_ms > self.PERFORMANCE_THRESHOLDS['total_time_ms']['p99']:
            failed_metrics.append(
                f"總反應時間過長: {performance_metrics.total_time_ms:.1f}ms > "
                f"{self.PERFORMANCE_THRESHOLDS['total_time_ms']['p99']}ms"
            )
        elif performance_metrics.total_time_ms > self.PERFORMANCE_THRESHOLDS['total_time_ms']['p95']:
            warnings.append(
                f"總反應時間接近閾值: {performance_metrics.total_time_ms:.1f}ms > "
                f"{self.PERFORMANCE_THRESHOLDS['total_time_ms']['p95']}ms"
            )
        
        # 檢查特徵載入時間
        feature_loading_ms = performance_metrics.stage_times.get('feature_loading', 0.0)
        if feature_loading_ms > self.PERFORMANCE_THRESHOLDS['feature_loading_ms']['max']:
            warnings.append(
                f"特徵載入時間過長: {feature_loading_ms:.1f}ms > "
                f"{self.PERFORMANCE_THRESHOLDS['feature_loading_ms']['max']}ms"
            )
        
        # 檢查模型推理時間
        model_inference_ms = performance_metrics.stage_times.get('model_inference', 0.0)
        if model_inference_ms > self.PERFORMANCE_THRESHOLDS['model_inference_ms']['max']:
            warnings.append(
                f"模型推理時間過長: {model_inference_ms:.1f}ms > "
                f"{self.PERFORMANCE_THRESHOLDS['model_inference_ms']['max']}ms"
            )
        
        # 判斷是否通過檢查
        passed = len(failed_metrics) == 0
        
        return PerformanceCheckResult(
            passed=passed,
            total_time_ms=performance_metrics.total_time_ms,
            failed_metrics=failed_metrics,
            warnings=warnings,
            timestamp=datetime.now()
        )

    
    def trigger_alerts(
        self,
        value_score: ReferenceValueScore,
        performance_metrics: PerformanceMetrics
    ) -> List[Alert]:
        """
        觸發告警
        
        根據品質和性能檢查結果觸發相應等級的告警
        
        Args:
            value_score: 可參考價值分數
            performance_metrics: 性能指標
        
        Returns:
            List[Alert]: 觸發的告警列表
        """
        alerts = []
        
        # 檢查品質指標
        quality_result = self.check_quality_threshold(value_score)
        
        # 處理品質相關的嚴重告警
        for failed_metric in quality_result.failed_metrics:
            alert = self._create_quality_alert(
                AlertLevel.CRITICAL,
                failed_metric,
                value_score
            )
            alerts.append(alert)
            self._alerts.append(alert)
        
        # 處理品質相關的警告
        for warning in quality_result.warnings:
            alert = self._create_quality_alert(
                AlertLevel.WARNING,
                warning,
                value_score
            )
            alerts.append(alert)
            self._alerts.append(alert)
        
        # 檢查性能指標
        performance_result = self.check_performance_threshold(performance_metrics)
        
        # 處理性能相關的嚴重告警
        for failed_metric in performance_result.failed_metrics:
            alert = self._create_performance_alert(
                AlertLevel.CRITICAL,
                failed_metric,
                performance_metrics
            )
            alerts.append(alert)
            self._alerts.append(alert)
        
        # 處理性能相關的警告
        for warning in performance_result.warnings:
            alert = self._create_performance_alert(
                AlertLevel.WARNING,
                warning,
                performance_metrics
            )
            alerts.append(alert)
            self._alerts.append(alert)
        
        return alerts
    
    def _create_quality_alert(
        self,
        level: AlertLevel,
        message: str,
        value_score: ReferenceValueScore
    ) -> Alert:
        """
        創建品質相關告警
        
        Args:
            level: 告警等級
            message: 告警訊息
            value_score: 可參考價值分數
        
        Returns:
            Alert: 告警物件
        """
        # 從訊息中提取指標名稱和值
        metric_name = "overall_score"
        current_value = value_score.overall_score
        threshold_value = self.QUALITY_THRESHOLDS['overall_score']['critical']
        
        if "相關性" in message:
            metric_name = "relevance_score"
            current_value = value_score.relevance_score
            threshold_value = self.QUALITY_THRESHOLDS['relevance_score']['critical']
        elif "新穎性" in message:
            metric_name = "novelty_score"
            current_value = value_score.novelty_score
            threshold_value = self.QUALITY_THRESHOLDS['novelty_score']['critical']
        elif "可解釋性" in message:
            metric_name = "explainability_score"
            current_value = value_score.explainability_score
            threshold_value = self.QUALITY_THRESHOLDS['explainability_score']['critical']
        elif "多樣性" in message:
            metric_name = "diversity_score"
            current_value = value_score.diversity_score
            threshold_value = self.QUALITY_THRESHOLDS['diversity_score']['critical']
        
        return Alert(
            level=level,
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            message=message,
            timestamp=datetime.now()
        )
    
    def _create_performance_alert(
        self,
        level: AlertLevel,
        message: str,
        performance_metrics: PerformanceMetrics
    ) -> Alert:
        """
        創建性能相關告警
        
        Args:
            level: 告警等級
            message: 告警訊息
            performance_metrics: 性能指標
        
        Returns:
            Alert: 告警物件
        """
        # 從訊息中提取指標名稱和值
        metric_name = "total_time_ms"
        current_value = performance_metrics.total_time_ms
        threshold_value = self.PERFORMANCE_THRESHOLDS['total_time_ms']['p99']
        
        if "特徵載入" in message:
            metric_name = "feature_loading_ms"
            current_value = performance_metrics.stage_times.get('feature_loading', 0.0)
            threshold_value = self.PERFORMANCE_THRESHOLDS['feature_loading_ms']['max']
        elif "模型推理" in message:
            metric_name = "model_inference_ms"
            current_value = performance_metrics.stage_times.get('model_inference', 0.0)
            threshold_value = self.PERFORMANCE_THRESHOLDS['model_inference_ms']['max']
        
        return Alert(
            level=level,
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            message=message,
            timestamp=datetime.now()
        )
    
    def get_alerts(
        self,
        time_window: Optional[timedelta] = None,
        level: Optional[AlertLevel] = None
    ) -> List[Alert]:
        """
        獲取告警記錄
        
        Args:
            time_window: 時間窗口，None表示所有告警
            level: 告警等級，None表示所有等級
        
        Returns:
            List[Alert]: 告警列表
        """
        alerts = self._alerts
        
        # 過濾時間窗口
        if time_window:
            cutoff_time = datetime.now() - time_window
            alerts = [a for a in alerts if a.timestamp >= cutoff_time]
        
        # 過濾告警等級
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return alerts

    
    def generate_hourly_report(self) -> MonitoringReport:
        """
        生成小時報告
        
        Returns:
            MonitoringReport: 監控報告
        """
        time_window = timedelta(hours=1)
        return self._generate_report("hourly", time_window)
    
    def generate_daily_report(self) -> MonitoringReport:
        """
        生成日報
        
        Returns:
            MonitoringReport: 監控報告
        """
        time_window = timedelta(days=1)
        return self._generate_report("daily", time_window)
    
    def _generate_report(
        self,
        report_type: str,
        time_window: timedelta
    ) -> MonitoringReport:
        """
        生成監控報告
        
        Args:
            report_type: 報告類型（hourly/daily）
            time_window: 時間窗口
        
        Returns:
            MonitoringReport: 監控報告
        """
        now = datetime.now()
        start_time = now - time_window
        
        # 獲取時間窗口內的記錄
        records = self.get_records(time_window=time_window)
        
        if not records:
            # 沒有記錄時返回空報告
            return MonitoringReport(
                report_type=report_type,
                start_time=start_time,
                end_time=now,
                total_recommendations=0,
                unique_members=0,
                avg_recommendations_per_member=0.0,
                avg_overall_score=0.0,
                avg_relevance_score=0.0,
                avg_novelty_score=0.0,
                avg_explainability_score=0.0,
                avg_diversity_score=0.0,
                avg_response_time_ms=0.0,
                p50_response_time_ms=0.0,
                p95_response_time_ms=0.0,
                p99_response_time_ms=0.0,
                total_alerts=0,
                critical_alerts=0,
                warning_alerts=0,
                degradation_count=0,
                score_trend="stable",
                performance_trend="stable",
                recommendations_for_improvement=[],
                timestamp=now
            )
        
        # 推薦量統計
        total_recommendations = len(records)
        unique_members = len(set(r.member_code for r in records))
        avg_recommendations_per_member = total_recommendations / unique_members if unique_members > 0 else 0.0
        
        # 品質統計
        avg_overall_score = np.mean([r.overall_score for r in records])
        avg_relevance_score = np.mean([r.relevance_score for r in records])
        avg_novelty_score = np.mean([r.novelty_score for r in records])
        avg_explainability_score = np.mean([r.explainability_score for r in records])
        avg_diversity_score = np.mean([r.diversity_score for r in records])
        
        # 性能統計
        response_times = [r.total_time_ms for r in records]
        avg_response_time_ms = float(np.mean(response_times))
        p50_response_time_ms = float(np.percentile(response_times, 50))
        p95_response_time_ms = float(np.percentile(response_times, 95))
        p99_response_time_ms = float(np.percentile(response_times, 99))
        
        # 異常統計
        alerts = self.get_alerts(time_window=time_window)
        total_alerts = len(alerts)
        critical_alerts = len([a for a in alerts if a.level == AlertLevel.CRITICAL])
        warning_alerts = len([a for a in alerts if a.level == AlertLevel.WARNING])
        degradation_count = sum(1 for r in records if r.is_degraded)
        
        # 趨勢分析
        score_trend = self._analyze_score_trend(records)
        performance_trend = self._analyze_performance_trend(records)
        
        # 生成改進建議
        recommendations_for_improvement = self._generate_improvement_recommendations(
            avg_overall_score,
            avg_relevance_score,
            avg_novelty_score,
            avg_explainability_score,
            avg_diversity_score,
            p95_response_time_ms,
            critical_alerts,
            degradation_count
        )
        
        return MonitoringReport(
            report_type=report_type,
            start_time=start_time,
            end_time=now,
            total_recommendations=total_recommendations,
            unique_members=unique_members,
            avg_recommendations_per_member=avg_recommendations_per_member,
            avg_overall_score=float(avg_overall_score),
            avg_relevance_score=float(avg_relevance_score),
            avg_novelty_score=float(avg_novelty_score),
            avg_explainability_score=float(avg_explainability_score),
            avg_diversity_score=float(avg_diversity_score),
            avg_response_time_ms=avg_response_time_ms,
            p50_response_time_ms=p50_response_time_ms,
            p95_response_time_ms=p95_response_time_ms,
            p99_response_time_ms=p99_response_time_ms,
            total_alerts=total_alerts,
            critical_alerts=critical_alerts,
            warning_alerts=warning_alerts,
            degradation_count=degradation_count,
            score_trend=score_trend,
            performance_trend=performance_trend,
            recommendations_for_improvement=recommendations_for_improvement,
            timestamp=now
        )
    
    def _analyze_score_trend(self, records: List[MonitoringRecord]) -> str:
        """
        分析分數趨勢
        
        Args:
            records: 監控記錄列表
        
        Returns:
            str: 趨勢（improving/stable/declining）
        """
        if len(records) < 10:
            return "stable"
        
        # 將記錄按時間排序
        sorted_records = sorted(records, key=lambda r: r.timestamp)
        
        # 計算前半段和後半段的平均分數
        mid_point = len(sorted_records) // 2
        first_half_avg = np.mean([r.overall_score for r in sorted_records[:mid_point]])
        second_half_avg = np.mean([r.overall_score for r in sorted_records[mid_point:]])
        
        # 判斷趨勢
        diff = second_half_avg - first_half_avg
        
        if diff > 5:
            return "improving"
        elif diff < -5:
            return "declining"
        else:
            return "stable"
    
    def _analyze_performance_trend(self, records: List[MonitoringRecord]) -> str:
        """
        分析性能趨勢
        
        Args:
            records: 監控記錄列表
        
        Returns:
            str: 趨勢（improving/stable/declining）
        """
        if len(records) < 10:
            return "stable"
        
        # 將記錄按時間排序
        sorted_records = sorted(records, key=lambda r: r.timestamp)
        
        # 計算前半段和後半段的平均反應時間
        mid_point = len(sorted_records) // 2
        first_half_avg = np.mean([r.total_time_ms for r in sorted_records[:mid_point]])
        second_half_avg = np.mean([r.total_time_ms for r in sorted_records[mid_point:]])
        
        # 判斷趨勢（反應時間越低越好）
        diff = second_half_avg - first_half_avg
        
        if diff < -50:  # 反應時間減少超過50ms
            return "improving"
        elif diff > 50:  # 反應時間增加超過50ms
            return "declining"
        else:
            return "stable"
    
    def _generate_improvement_recommendations(
        self,
        avg_overall_score: float,
        avg_relevance_score: float,
        avg_novelty_score: float,
        avg_explainability_score: float,
        avg_diversity_score: float,
        p95_response_time_ms: float,
        critical_alerts: int,
        degradation_count: int
    ) -> List[str]:
        """
        生成改進建議
        
        Args:
            avg_overall_score: 平均綜合分數
            avg_relevance_score: 平均相關性分數
            avg_novelty_score: 平均新穎性分數
            avg_explainability_score: 平均可解釋性分數
            avg_diversity_score: 平均多樣性分數
            p95_response_time_ms: P95反應時間
            critical_alerts: 嚴重告警數
            degradation_count: 降級次數
        
        Returns:
            List[str]: 改進建議列表
        """
        recommendations = []
        
        # 檢查綜合分數
        if avg_overall_score < self.QUALITY_THRESHOLDS['overall_score']['target']:
            recommendations.append(
                f"綜合可參考價值分數({avg_overall_score:.1f})低於目標值"
                f"({self.QUALITY_THRESHOLDS['overall_score']['target']})，"
                "建議優化推薦策略"
            )
        
        # 檢查相關性分數
        if avg_relevance_score < self.QUALITY_THRESHOLDS['relevance_score']['target']:
            recommendations.append(
                f"相關性分數({avg_relevance_score:.1f})偏低，"
                "建議加強會員特徵分析和產品匹配度"
            )
        
        # 檢查新穎性分數
        if avg_novelty_score < self.QUALITY_THRESHOLDS['novelty_score']['target']:
            recommendations.append(
                f"新穎性分數({avg_novelty_score:.1f})偏低，"
                "建議增加新產品和新類別的推薦比例"
            )
        
        # 檢查可解釋性分數
        if avg_explainability_score < self.QUALITY_THRESHOLDS['explainability_score']['target']:
            recommendations.append(
                f"可解釋性分數({avg_explainability_score:.1f})偏低，"
                "建議優化推薦理由生成邏輯"
            )
        
        # 檢查多樣性分數
        if avg_diversity_score < self.QUALITY_THRESHOLDS['diversity_score']['target']:
            recommendations.append(
                f"多樣性分數({avg_diversity_score:.1f})偏低，"
                "建議增加推薦產品的類別和價格多樣性"
            )
        
        # 檢查性能
        if p95_response_time_ms > self.PERFORMANCE_THRESHOLDS['total_time_ms']['p95']:
            recommendations.append(
                f"P95反應時間({p95_response_time_ms:.1f}ms)超過閾值，"
                "建議優化特徵載入和模型推理速度"
            )
        
        # 檢查告警
        if critical_alerts > 0:
            recommendations.append(
                f"發現{critical_alerts}個嚴重告警，"
                "建議立即檢查系統狀態並採取修復措施"
            )
        
        # 檢查降級
        if degradation_count > 0:
            recommendations.append(
                f"發生{degradation_count}次降級，"
                "建議檢查推薦品質和性能瓶頸"
            )
        
        return recommendations
    
    def clear_history(self) -> None:
        """清空歷史記錄"""
        self._records.clear()
        self._alerts.clear()
    
    def get_record_count(self) -> int:
        """獲取記錄數量"""
        return len(self._records)
    
    def get_alert_count(self) -> int:
        """獲取告警數量"""
        return len(self._alerts)
