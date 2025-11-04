"""
Advanced Streaming Analytics for Real-time LLM Monitoring

This module provides:
1. Real-time trend detection
2. Anomaly detection
3. Advanced alerting
4. Performance analytics
5. Quality metrics aggregation
"""

import time
import asyncio
from typing import List, Dict, Any, Optional, Callable, Deque, Tuple
from collections import deque, defaultdict
from dataclasses import dataclass, field
import statistics
import numpy as np
from datetime import datetime, timedelta

@dataclass
class MetricWindow:
    """Sliding window for metric tracking"""
    window_size: int
    metrics: Deque[Dict[str, float]] = field(default_factory=lambda: deque())
    timestamps: Deque[datetime] = field(default_factory=lambda: deque())
    
    def add_metric(self, metric: Dict[str, float], timestamp: Optional[datetime] = None):
        """Add a new metric to the window"""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.metrics.append(metric)
        self.timestamps.append(timestamp)
        
        # Maintain window size
        while len(self.metrics) > self.window_size:
            self.metrics.popleft()
            self.timestamps.popleft()
    
    def get_latest_metrics(self) -> Optional[Dict[str, float]]:
        """Get the most recent metrics"""
        if self.metrics:
            return self.metrics[-1]
        return None
    
    def get_aggregated_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get aggregated statistics for all metrics in window"""
        if not self.metrics:
            return {}
        
        result = {}
        metric_names = self.metrics[0].keys()
        
        for metric_name in metric_names:
            values = [m[metric_name] for m in self.metrics if metric_name in m]
            if values:
                result[metric_name] = {
                    "mean": float(statistics.mean(values)),
                    "median": float(statistics.median(values)),
                    "min": float(min(values)),
                    "max": float(max(values)),
                    "std": float(statistics.stdev(values)) if len(values) > 1 else 0.0,
                    "count": len(values)
                }
        
        return result
    
    def get_trend(self, metric_name: str, window: int = 10) -> Optional[float]:
        """Calculate trend for a specific metric (slope of linear regression)"""
        if len(self.metrics) < window:
            return None
        
        recent_metrics = list(self.metrics)[-window:]
        recent_timestamps = list(self.timestamps)[-window:]
        
        if len(recent_metrics) < 2:
            return None
        
        # Convert timestamps to seconds for numerical analysis
        time_diffs = [(ts - recent_timestamps[0]).total_seconds() for ts in recent_timestamps]
        values = [m.get(metric_name, 0.0) for m in recent_metrics]
        
        # Simple linear regression slope
        if len(time_diffs) > 1:
            x_mean = statistics.mean(time_diffs)
            y_mean = statistics.mean(values)
            
            numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(time_diffs, values))
            denominator = sum((x - x_mean) ** 2 for x in time_diffs)
            
            if denominator != 0:
                return float(numerator / denominator)
        
        return None

@dataclass
class AlertRule:
    """Configuration for alerting rules"""
    metric_name: str
    threshold: float
    comparison: str  # "gt", "lt", "gte", "lte", "eq", "ne"
    severity: str = "warning"  # "info", "warning", "error", "critical"
    duration: int = 1  # Number of consecutive violations before alerting
    message_template: str = "{metric_name} {comparison} {threshold} (current: {current_value})"
    
    def evaluate(self, current_value: float) -> bool:
        """Evaluate if the rule is triggered"""
        if self.comparison == "gt":
            return current_value > self.threshold
        elif self.comparison == "lt":
            return current_value < self.threshold
        elif self.comparison == "gte":
            return current_value >= self.threshold
        elif self.comparison == "lte":
            return current_value <= self.threshold
        elif self.comparison == "eq":
            return abs(current_value - self.threshold) < 1e-6
        elif self.comparison == "ne":
            return abs(current_value - self.threshold) >= 1e-6
        return False

@dataclass
class Alert:
    """Alert instance"""
    rule: AlertRule
    current_value: float
    timestamp: datetime
    message: str
    severity: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class AnomalyDetector:
    """Statistical anomaly detection for metrics"""
    
    def __init__(self, window_size: int = 100, threshold: float = 2.0):
        self.window_size = window_size
        self.threshold = threshold  # Standard deviations for anomaly detection
        self.metric_history = defaultdict(lambda: deque(maxlen=window_size))
    
    def add_metric(self, metric_name: str, value: float):
        """Add a metric value to the history"""
        self.metric_history[metric_name].append(value)
    
    def detect_anomalies(self, current_metrics: Dict[str, float]) -> Dict[str, bool]:
        """Detect anomalies in current metrics"""
        anomalies = {}
        
        for metric_name, current_value in current_metrics.items():
            history = self.metric_history[metric_name]
            
            if len(history) < 10:  # Need minimum data for detection
                anomalies[metric_name] = False
                continue
            
            # Calculate z-score
            mean_val = statistics.mean(history)
            std_val = statistics.stdev(history) if len(history) > 1 else 0.0
            
            if std_val > 0:
                z_score = abs((current_value - mean_val) / std_val)
                anomalies[metric_name] = z_score > self.threshold
            else:
                anomalies[metric_name] = False
        
        return anomalies

class StreamingAnalytics:
    """Advanced streaming analytics engine"""
    
    def __init__(
        self,
        window_size: int = 100,
        alert_rules: Optional[List[AlertRule]] = None,
        anomaly_detection: bool = True,
        trend_analysis: bool = True
    ):
        self.window_size = window_size
        self.metric_window = MetricWindow(window_size)
        self.alert_rules = alert_rules or []
        self.anomaly_detector = AnomalyDetector(window_size) if anomaly_detection else None
        self.trend_analysis = trend_analysis
        
        # Performance tracking
        self.processing_times = deque(maxlen=100)
        self.alert_history = deque(maxlen=1000)
        
        # Callbacks
        self.on_alert: Optional[Callable[[Alert], None]] = None
        self.on_anomaly: Optional[Callable[[str, float, Dict[str, bool]], None]] = None
        self.on_trend: Optional[Callable[[str, float], None]] = None
    
    def add_metrics(self, metrics: Dict[str, float], timestamp: Optional[datetime] = None):
        """Add new metrics to the analytics engine"""
        start_time = time.perf_counter()
        
        # Add to metric window
        self.metric_window.add_metric(metrics, timestamp)
        
        # Add to anomaly detector
        if self.anomaly_detector:
            for metric_name, value in metrics.items():
                self.anomaly_detector.add_metric(metric_name, value)
        
        # Process analytics
        self._process_analytics(metrics)
        
        # Track processing time
        processing_time = time.perf_counter() - start_time
        self.processing_times.append(processing_time)
    
    def _process_analytics(self, current_metrics: Dict[str, float]):
        """Process all analytics for current metrics"""
        # Check alert rules
        self._check_alerts(current_metrics)
        
        # Detect anomalies
        if self.anomaly_detector:
            anomalies = self.anomaly_detector.detect_anomalies(current_metrics)
            self._handle_anomalies(current_metrics, anomalies)
        
        # Analyze trends
        if self.trend_analysis:
            self._analyze_trends(current_metrics)
    
    def _check_alerts(self, current_metrics: Dict[str, float]):
        """Check all alert rules against current metrics"""
        for rule in self.alert_rules:
            if rule.metric_name in current_metrics:
                current_value = current_metrics[rule.metric_name]
                
                if rule.evaluate(current_value):
                    # Create alert
                    message = rule.message_template.format(
                        metric_name=rule.metric_name,
                        comparison=rule.comparison,
                        threshold=rule.threshold,
                        current_value=current_value
                    )
                    
                    alert = Alert(
                        rule=rule,
                        current_value=current_value,
                        timestamp=datetime.now(),
                        message=message,
                        severity=rule.severity
                    )
                    
                    self.alert_history.append(alert)
                    
                    # Trigger callback
                    if self.on_alert:
                        self.on_alert(alert)
    
    def _handle_anomalies(self, current_metrics: Dict[str, float], anomalies: Dict[str, bool]):
        """Handle detected anomalies"""
        for metric_name, is_anomaly in anomalies.items():
            if is_anomaly and self.on_anomaly:
                self.on_anomaly(metric_name, current_metrics[metric_name], anomalies)
    
    def _analyze_trends(self, current_metrics: Dict[str, float]):
        """Analyze trends for current metrics"""
        for metric_name in current_metrics.keys():
            trend = self.metric_window.get_trend(metric_name)
            if trend is not None and self.on_trend:
                self.on_trend(metric_name, trend)
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        if not self.processing_times:
            return {}
        
        times = list(self.processing_times)
        return {
            "avg_processing_time_ms": float(statistics.mean(times) * 1000),
            "max_processing_time_ms": float(max(times) * 1000),
            "min_processing_time_ms": float(min(times) * 1000),
            "total_metrics_processed": len(self.metric_window.metrics),
            "total_alerts_generated": len(self.alert_history)
        }
    
    def get_metric_summary(self) -> Dict[str, Any]:
        """Get comprehensive metric summary"""
        return {
            "window_size": self.window_size,
            "current_metrics": self.metric_window.get_latest_metrics(),
            "aggregated_metrics": self.metric_window.get_aggregated_metrics(),
            "performance_stats": self.get_performance_stats(),
            "alert_count": len(self.alert_history),
            "anomaly_detection_enabled": self.anomaly_detector is not None,
            "trend_analysis_enabled": self.trend_analysis
        }

class AsyncStreamingAnalytics(StreamingAnalytics):
    """Asynchronous version of streaming analytics"""
    
    async def add_metrics_async(self, metrics: Dict[str, float], timestamp: Optional[datetime] = None):
        """Add metrics asynchronously"""
        # Run the synchronous version in a thread pool
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.add_metrics, metrics, timestamp)
    
    async def get_metric_summary_async(self) -> Dict[str, Any]:
        """Get metric summary asynchronously"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.get_metric_summary)

# The following function is now deprecated for provider-neutrality:
# Users should instantiate StreamingAnalytics and supply their own alert rules; no defaults or provider-coupling remain in core code.