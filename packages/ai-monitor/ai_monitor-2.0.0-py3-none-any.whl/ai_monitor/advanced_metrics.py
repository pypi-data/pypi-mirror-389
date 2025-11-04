"""
Advanced metrics collection and analysis.

This module provides advanced performance metrics including percentile
latencies, concurrency tracking, rate limiting metrics, and resource usage.
"""

import time
import psutil
import threading
from collections import deque, defaultdict
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import statistics


class AdvancedMetricsCollector:
    """
    Collects advanced performance and operational metrics.
    
    Tracks:
    - Percentile latencies (p50, p95, p99)
    - Rate limiting and throttling events
    - Concurrent request tracking
    - Resource utilization (CPU, memory)
    - Time-windowed metrics (RPM, TPM)
    """
    
    def __init__(
        self,
        window_size: int = 3600,  # 1 hour window
        enable_resource_tracking: bool = False
    ):
        """
        Initialize advanced metrics collector.
        
        Args:
            window_size: Time window in seconds for rolling metrics
            enable_resource_tracking: Enable CPU/memory tracking
        """
        self.window_size = window_size
        self.enable_resource_tracking = enable_resource_tracking
        
        # Latency tracking with sliding window
        self._latencies = deque(maxlen=10000)
        self._latency_timestamps = deque(maxlen=10000)
        
        # Concurrency tracking
        self._active_requests = 0
        self._max_concurrent = 0
        self._concurrency_lock = threading.Lock()
        
        # Rate limiting metrics
        self._rate_limit_hits = 0
        self._throttle_events = 0
        
        # Time-based counters
        self._requests_per_minute = deque(maxlen=60)
        self._tokens_per_minute = deque(maxlen=60)
        self._minute_tracker = defaultdict(int)
        self._last_minute_reset = time.time()
        
        # Resource tracking
        if self.enable_resource_tracking:
            self._process = psutil.Process()
        
        # Error tracking by type
        self._error_counts = defaultdict(int)
        self._error_types = defaultdict(list)
        
        # Model-specific metrics
        self._model_latencies = defaultdict(list)
        self._model_request_counts = defaultdict(int)
        
    def track_request_start(self) -> str:
        """
        Track request start for concurrency monitoring.
        
        Returns:
            Request ID
        """
        request_id = f"req_{time.time()}_{threading.get_ident()}"
        
        with self._concurrency_lock:
            self._active_requests += 1
            if self._active_requests > self._max_concurrent:
                self._max_concurrent = self._active_requests
        
        return request_id
    
    def track_request_end(self, request_id: str, latency: float, model: str = "unknown"):
        """
        Track request completion.
        
        Args:
            request_id: Request identifier
            latency: Request latency in seconds
            model: Model name
        """
        with self._concurrency_lock:
            self._active_requests = max(0, self._active_requests - 1)
        
        # Store latency with timestamp
        current_time = time.time()
        self._latencies.append(latency)
        self._latency_timestamps.append(current_time)
        
        # Model-specific tracking
        self._model_latencies[model].append(latency)
        self._model_request_counts[model] += 1
        
        # Update RPM
        self._update_rpm_counter()
    
    def track_tokens(self, token_count: int):
        """
        Track token usage for TPM calculations.
        
        Args:
            token_count: Number of tokens used
        """
        self._update_tpm_counter(token_count)
    
    def track_rate_limit_hit(self):
        """Record a rate limit event."""
        self._rate_limit_hits += 1
    
    def track_throttle_event(self):
        """Record a throttling event."""
        self._throttle_events += 1
    
    def track_error(self, error_type: str, error_message: str):
        """
        Track error occurrence.
        
        Args:
            error_type: Type/category of error
            error_message: Error message
        """
        self._error_counts[error_type] += 1
        self._error_types[error_type].append({
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def _update_rpm_counter(self):
        """Update requests per minute counter."""
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self._last_minute_reset >= 60:
            self._requests_per_minute.append(self._minute_tracker['requests'])
            self._minute_tracker['requests'] = 0
            self._last_minute_reset = current_time
        
        self._minute_tracker['requests'] += 1
    
    def _update_tpm_counter(self, tokens: int):
        """Update tokens per minute counter."""
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self._last_minute_reset >= 60:
            self._tokens_per_minute.append(self._minute_tracker['tokens'])
            self._minute_tracker['tokens'] = 0
        
        self._minute_tracker['tokens'] += tokens
    
    def calculate_percentile(self, percentile: float) -> float:
        """
        Calculate percentile latency.
        
        Args:
            percentile: Percentile to calculate (0-100)
            
        Returns:
            Percentile latency in seconds
        """
        if not self._latencies:
            return 0.0
        
        # Filter to window
        latencies = self._get_windowed_latencies()
        
        if not latencies:
            return 0.0
        
        # Handle small sample sizes
        if len(latencies) == 1:
            return latencies[0]
        
        # Use sorted list and calculate percentile index
        sorted_latencies = sorted(latencies)
        
        # Calculate the index for the percentile
        # For p50 (median), we want the middle value
        # For p95, we want the value at 95% position
        index = (percentile / 100.0) * (len(sorted_latencies) - 1)
        
        # Linear interpolation between two closest values
        lower_index = int(index)
        upper_index = min(lower_index + 1, len(sorted_latencies) - 1)
        
        if lower_index == upper_index:
            return sorted_latencies[lower_index]
        
        # Interpolate
        weight = index - lower_index
        return sorted_latencies[lower_index] * (1 - weight) + sorted_latencies[upper_index] * weight
    
    def _get_windowed_latencies(self) -> List[float]:
        """Get latencies within the time window."""
        current_time = time.time()
        cutoff_time = current_time - self.window_size
        
        windowed_latencies = []
        for latency, timestamp in zip(self._latencies, self._latency_timestamps):
            if timestamp >= cutoff_time:
                windowed_latencies.append(latency)
        
        return windowed_latencies
    
    def get_resource_usage(self) -> Dict[str, float]:
        """
        Get current resource usage.
        
        Returns:
            Dictionary with CPU and memory metrics
        """
        if not self.enable_resource_tracking:
            return {"cpu_percent": 0.0, "memory_mb": 0.0}
        
        try:
            cpu_percent = self._process.cpu_percent(interval=0.1)
            memory_info = self._process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            return {
                "cpu_percent": cpu_percent,
                "memory_mb": memory_mb,
                "memory_percent": self._process.memory_percent(),
            }
        except Exception:
            return {"cpu_percent": 0.0, "memory_mb": 0.0}
    
    def get_concurrency_metrics(self) -> Dict[str, int]:
        """
        Get concurrency metrics.
        
        Returns:
            Dictionary with concurrency information
        """
        with self._concurrency_lock:
            return {
                "active_requests": self._active_requests,
                "max_concurrent": self._max_concurrent,
            }
    
    def get_rate_metrics(self) -> Dict[str, Any]:
        """
        Get rate-based metrics.
        
        Returns:
            Dictionary with RPM, TPM, and rate limiting metrics
        """
        return {
            "current_rpm": self._minute_tracker['requests'],
            "avg_rpm": statistics.mean(self._requests_per_minute) if self._requests_per_minute else 0,
            "current_tpm": self._minute_tracker['tokens'],
            "avg_tpm": statistics.mean(self._tokens_per_minute) if self._tokens_per_minute else 0,
            "rate_limit_hits": self._rate_limit_hits,
            "throttle_events": self._throttle_events,
        }
    
    def get_error_metrics(self) -> Dict[str, Any]:
        """
        Get error metrics.
        
        Returns:
            Dictionary with error counts and details
        """
        total_errors = sum(self._error_counts.values())
        
        return {
            "total_errors": total_errors,
            "error_counts": dict(self._error_counts),
            "error_types": dict(self._error_types),
        }
    
    def get_model_metrics(self) -> Dict[str, Any]:
        """
        Get model-specific metrics.
        
        Returns:
            Dictionary with per-model statistics
        """
        model_stats = {}
        
        for model, latencies in self._model_latencies.items():
            if latencies:
                model_stats[model] = {
                    "request_count": self._model_request_counts[model],
                    "avg_latency": statistics.mean(latencies),
                    "min_latency": min(latencies),
                    "max_latency": max(latencies),
                    "p50_latency": statistics.median(latencies),
                    "p95_latency": statistics.quantiles(latencies, n=20)[18] if len(latencies) > 1 else latencies[0],
                }
        
        return model_stats
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all advanced metrics.
        
        Returns:
            Dictionary with all collected metrics
        """
        latencies = self._get_windowed_latencies()
        
        metrics = {
            "latency_percentiles": {
                "p50": self.calculate_percentile(50),
                "p90": self.calculate_percentile(90),
                "p95": self.calculate_percentile(95),
                "p99": self.calculate_percentile(99),
                "p99.9": self.calculate_percentile(99.9),  # NEW
            },
            "latency_stats": {
                "avg": statistics.mean(latencies) if latencies else 0,
                "min": min(latencies) if latencies else 0,
                "max": max(latencies) if latencies else 0,
                "stddev": statistics.stdev(latencies) if len(latencies) > 1 else 0,
            },
            "concurrency": self.get_concurrency_metrics(),
            "rate_metrics": self.get_rate_metrics(),
            "error_metrics": self.get_error_metrics(),
            "model_metrics": self.get_model_metrics(),
            "token_throughput": self._calculate_token_throughput(),  # NEW
            "reliability": self._calculate_reliability(),  # NEW
            "slo_metrics": self._calculate_slo_metrics(),  # NEW
        }
        
        if self.enable_resource_tracking:
            metrics["resource_usage"] = self.get_resource_usage()
        
        return metrics
    
    def _calculate_token_throughput(self) -> Dict[str, float]:
        """Calculate token throughput percentiles."""
        throughputs = []
        for latency in self._get_windowed_latencies():
            if latency > 0:
                # Estimate tokens (rough average)
                tokens = 1000  # Placeholder, would need actual token counts
                tps = tokens / latency
                throughputs.append(tps)
        
        if not throughputs:
            return {"p95": 0.0, "avg": 0.0}
        
        sorted_throughputs = sorted(throughputs)
        p95_index = int(0.95 * (len(sorted_throughputs) - 1))
        
        return {
            "p95": sorted_throughputs[p95_index] if sorted_throughputs else 0.0,
            "avg": statistics.mean(throughputs),
        }
    
    def _calculate_reliability(self) -> Dict[str, float]:
        """Calculate reliability metrics."""
        total_requests = sum(self._model_request_counts.values())
        total_errors = sum(self._error_counts.values())
        
        success_rate = 1.0
        if total_requests > 0:
            success_rate = (total_requests - total_errors) / total_requests
        
        return {
            "success_rate": success_rate,
            "total_requests": total_requests,
            "total_errors": total_errors,
        }
    
    def _calculate_slo_metrics(self) -> Dict[str, float]:
        """Calculate SLO/SLA metrics."""
        latencies = self._get_windowed_latencies()
        
        # Calculate availability (uptime percentage)
        total_requests = sum(self._model_request_counts.values())
        total_errors = sum(self._error_counts.values())
        availability = 100.0
        if total_requests > 0:
            availability = ((total_requests - total_errors) / total_requests) * 100
        
        # Calculate error budget (SLO target: 99.9% = 0.1% error budget)
        slo_target = 0.999
        error_budget_remaining = 1.0
        if total_requests > 0:
            current_availability = (total_requests - total_errors) / total_requests
            if current_availability < slo_target:
                error_budget_consumed = (slo_target - current_availability) / (1 - slo_target)
                error_budget_remaining = max(0, 1 - error_budget_consumed)
        
        # Calculate reliability score (0-100)
        reliability_score = 100.0
        if latencies:
            p99_latency = self.calculate_percentile(99)
            # Penalty for high latency (>15s)
            if p99_latency > 15:
                reliability_score -= min(30, (p99_latency - 15) * 2)
            # Penalty for errors
            if total_requests > 0:
                error_rate = total_errors / total_requests
                reliability_score -= min(40, error_rate * 400)
        
        return {
            "availability_percent": availability,
            "error_budget_remaining": error_budget_remaining,
            "reliability_score": max(0, reliability_score),
        }
    
    def reset_metrics(self):
        """Reset all metrics."""
        self._latencies.clear()
        self._latency_timestamps.clear()
        self._max_concurrent = 0
        self._rate_limit_hits = 0
        self._throttle_events = 0
        self._error_counts.clear()
        self._error_types.clear()
        self._model_latencies.clear()
        self._model_request_counts.clear()


class SlidingWindowMetrics:
    """
    Time-based sliding window for metrics.
    
    Useful for calculating metrics over specific time periods
    (e.g., last 5 minutes, last hour).
    """
    
    def __init__(self, window_seconds: int = 300):
        """
        Initialize sliding window.
        
        Args:
            window_seconds: Window size in seconds
        """
        self.window_seconds = window_seconds
        self._data = deque()
    
    def add(self, value: Any, timestamp: Optional[float] = None):
        """
        Add value to window.
        
        Args:
            value: Value to add
            timestamp: Optional timestamp (defaults to current time)
        """
        if timestamp is None:
            timestamp = time.time()
        
        self._data.append((timestamp, value))
        self._cleanup()
    
    def _cleanup(self):
        """Remove expired entries."""
        cutoff = time.time() - self.window_seconds
        
        while self._data and self._data[0][0] < cutoff:
            self._data.popleft()
    
    def get_values(self) -> List[Any]:
        """Get all values in current window."""
        self._cleanup()
        return [value for _, value in self._data]
    
    def count(self) -> int:
        """Get count of items in window."""
        self._cleanup()
        return len(self._data)
    
    def sum(self) -> float:
        """Get sum of numeric values in window."""
        values = self.get_values()
        return sum(v for v in values if isinstance(v, (int, float)))
    
    def average(self) -> float:
        """Get average of numeric values in window."""
        values = [v for v in self.get_values() if isinstance(v, (int, float))]
        return statistics.mean(values) if values else 0.0
