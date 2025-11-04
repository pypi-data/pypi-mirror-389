"""
Alerting and anomaly detection system.

Provides threshold-based alerting and statistical anomaly detection
for AI monitoring metrics.
"""

import time
import threading
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from collections import deque, defaultdict
import statistics


@dataclass
class AlertRule:
    """
    Definition of an alert rule.
    
    Attributes:
        name: Rule name/identifier
        metric_name: Name of metric to monitor
        threshold: Threshold value
        condition: Comparison operator (>, <, >=, <=, ==, !=)
        duration: Number of seconds condition must be true
        severity: Alert severity (critical, warning, info)
        enabled: Whether rule is active
    """
    name: str
    metric_name: str
    threshold: float
    condition: str = ">"
    duration: int = 0
    severity: str = "warning"
    enabled: bool = True
    
    def evaluate(self, value: float) -> bool:
        """
        Evaluate if value triggers alert.
        
        Args:
            value: Metric value to check
            
        Returns:
            True if alert should trigger
        """
        if not self.enabled:
            return False
        
        if self.condition == ">":
            return value > self.threshold
        elif self.condition == ">=":
            return value >= self.threshold
        elif self.condition == "<":
            return value < self.threshold
        elif self.condition == "<=":
            return value <= self.threshold
        elif self.condition == "==":
            return value == self.threshold
        elif self.condition == "!=":
            return value != self.threshold
        else:
            raise ValueError(f"Unknown condition: {self.condition}")


@dataclass
class Alert:
    """
    Represents a triggered alert.
    
    Attributes:
        rule_name: Name of triggered rule
        metric_name: Metric that triggered alert
        value: Current metric value
        threshold: Configured threshold
        severity: Alert severity
        timestamp: When alert was triggered
        message: Alert message
    """
    rule_name: str
    metric_name: str
    value: float
    threshold: float
    severity: str
    timestamp: str
    message: str


class AlertChannel:
    """Base class for alert notification channels."""
    
    def send(self, alert: Alert):
        """
        Send alert notification.
        
        Args:
            alert: Alert to send
        """
        raise NotImplementedError


class ConsoleAlertChannel(AlertChannel):
    """Sends alerts to console/stdout."""
    
    def send(self, alert: Alert):
        """Print alert to console."""
        print(f"[{alert.severity.upper()}] {alert.timestamp}")
        print(f"  Rule: {alert.rule_name}")
        print(f"  Metric: {alert.metric_name} = {alert.value} (threshold: {alert.threshold})")
        print(f"  Message: {alert.message}")
        print()


class LogFileAlertChannel(AlertChannel):
    """Sends alerts to log file."""
    
    def __init__(self, log_file: str = "alerts.log"):
        """
        Initialize log file channel.
        
        Args:
            log_file: Path to log file
        """
        self.log_file = log_file
    
    def send(self, alert: Alert):
        """Write alert to log file."""
        import json
        
        with open(self.log_file, 'a') as f:
            alert_dict = {
                "rule_name": alert.rule_name,
                "metric_name": alert.metric_name,
                "value": alert.value,
                "threshold": alert.threshold,
                "severity": alert.severity,
                "timestamp": alert.timestamp,
                "message": alert.message,
            }
            f.write(json.dumps(alert_dict) + "\n")


class WebhookAlertChannel(AlertChannel):
    """Sends alerts via HTTP webhook."""
    
    def __init__(self, webhook_url: str):
        """
        Initialize webhook channel.
        
        Args:
            webhook_url: Webhook URL to POST alerts to
        """
        self.webhook_url = webhook_url
    
    def send(self, alert: Alert):
        """Send alert via webhook."""
        import requests
        import json
        
        payload = {
            "rule_name": alert.rule_name,
            "metric_name": alert.metric_name,
            "value": alert.value,
            "threshold": alert.threshold,
            "severity": alert.severity,
            "timestamp": alert.timestamp,
            "message": alert.message,
        }
        
        try:
            requests.post(
                self.webhook_url,
                json=payload,
                timeout=5
            )
        except Exception as e:
            print(f"Failed to send webhook alert: {e}")


class AlertingSystem:
    """
    Main alerting system coordinating rules, evaluation, and notifications.
    
    Features:
    - Threshold-based alerts
    - Statistical anomaly detection
    - Multiple notification channels
    - Alert deduplication
    - Alert history
    """
    
    def __init__(self, anomaly_sensitivity: float = 3.0):
        """
        Initialize alerting system.
        
        Args:
            anomaly_sensitivity: Z-score threshold for anomaly detection
        """
        self.anomaly_sensitivity = anomaly_sensitivity
        
        # Alert rules
        self._rules: Dict[str, AlertRule] = {}
        
        # Notification channels
        self._channels: List[AlertChannel] = []
        
        # Alert history
        self._alert_history: deque = deque(maxlen=1000)
        
        # Active alerts (for deduplication)
        self._active_alerts: Dict[str, Alert] = {}
        
        # Metric history for anomaly detection
        self._metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Rule evaluation state
        self._rule_state: Dict[str, Dict] = defaultdict(dict)
        
        # Thread safety
        self._lock = threading.Lock()
    
    def add_rule(self, rule: AlertRule):
        """
        Add alert rule.
        
        Args:
            rule: AlertRule to add
        """
        with self._lock:
            self._rules[rule.name] = rule
    
    def remove_rule(self, rule_name: str):
        """
        Remove alert rule.
        
        Args:
            rule_name: Name of rule to remove
        """
        with self._lock:
            if rule_name in self._rules:
                del self._rules[rule_name]
    
    def add_channel(self, channel: AlertChannel):
        """
        Add notification channel.
        
        Args:
            channel: AlertChannel to add
        """
        self._channels.append(channel)
    
    def check_metrics(self, metrics: Dict[str, float]):
        """
        Check metrics against alert rules.
        
        Args:
            metrics: Dictionary of metric name -> value
        """
        with self._lock:
            for metric_name, value in metrics.items():
                # Store for anomaly detection
                self._metric_history[metric_name].append(value)
                
                # Check threshold-based rules
                self._check_threshold_rules(metric_name, value)
                
                # Check for anomalies
                if self._is_anomaly(metric_name, value):
                    self._trigger_anomaly_alert(metric_name, value)
    
    def _check_threshold_rules(self, metric_name: str, value: float):
        """
        Check threshold-based rules for a metric.
        
        Args:
            metric_name: Name of metric
            value: Current value
        """
        for rule in self._rules.values():
            if rule.metric_name != metric_name:
                continue
            
            if not rule.enabled:
                continue
            
            # Evaluate rule
            triggered = rule.evaluate(value)
            
            # Handle duration requirements
            if rule.duration > 0:
                triggered = self._check_duration(rule, triggered)
            
            # Trigger alert if needed
            if triggered:
                self._trigger_alert(rule, metric_name, value)
    
    def _check_duration(self, rule: AlertRule, current_result: bool) -> bool:
        """
        Check if condition has been true for required duration.
        
        Args:
            rule: Alert rule
            current_result: Current evaluation result
            
        Returns:
            True if duration requirement is met
        """
        state_key = f"{rule.name}_duration"
        
        if current_result:
            # Start or continue timer
            if state_key not in self._rule_state:
                self._rule_state[state_key] = {
                    'start_time': time.time(),
                    'triggered': False
                }
            
            elapsed = time.time() - self._rule_state[state_key]['start_time']
            
            if elapsed >= rule.duration and not self._rule_state[state_key]['triggered']:
                self._rule_state[state_key]['triggered'] = True
                return True
        else:
            # Reset timer
            if state_key in self._rule_state:
                del self._rule_state[state_key]
        
        return False
    
    def _trigger_alert(self, rule: AlertRule, metric_name: str, value: float):
        """
        Trigger an alert.
        
        Args:
            rule: Alert rule that triggered
            metric_name: Metric name
            value: Current value
        """
        alert_key = f"{rule.name}_{metric_name}"
        
        # Deduplicate (don't re-send same alert within 5 minutes)
        if alert_key in self._active_alerts:
            last_alert = self._active_alerts[alert_key]
            last_time = datetime.fromisoformat(last_alert.timestamp)
            if (datetime.utcnow() - last_time).total_seconds() < 300:
                return
        
        # Create alert
        alert = Alert(
            rule_name=rule.name,
            metric_name=metric_name,
            value=value,
            threshold=rule.threshold,
            severity=rule.severity,
            timestamp=datetime.utcnow().isoformat(),
            message=f"{metric_name} {rule.condition} {rule.threshold} (current: {value})"
        )
        
        # Store alert
        self._active_alerts[alert_key] = alert
        self._alert_history.append(alert)
        
        # Send notifications
        self._send_alert(alert)
    
    def _is_anomaly(self, metric_name: str, value: float) -> bool:
        """
        Detect if value is a statistical anomaly.
        
        Uses z-score method: |z| > threshold indicates anomaly
        
        Args:
            metric_name: Metric name
            value: Current value
            
        Returns:
            True if value is anomalous
        """
        history = list(self._metric_history[metric_name])
        
        # Need at least 10 samples
        if len(history) < 10:
            return False
        
        try:
            mean = statistics.mean(history)
            stdev = statistics.stdev(history)
            
            if stdev == 0:
                return False
            
            z_score = abs((value - mean) / stdev)
            
            return z_score > self.anomaly_sensitivity
        except Exception:
            return False
    
    def _trigger_anomaly_alert(self, metric_name: str, value: float):
        """
        Trigger anomaly alert.
        
        Args:
            metric_name: Metric name
            value: Anomalous value
        """
        history = list(self._metric_history[metric_name])
        mean = statistics.mean(history) if history else 0
        stdev = statistics.stdev(history) if len(history) > 1 else 0
        
        alert = Alert(
            rule_name="anomaly_detection",
            metric_name=metric_name,
            value=value,
            threshold=mean,
            severity="warning",
            timestamp=datetime.utcnow().isoformat(),
            message=f"Anomaly detected: {metric_name}={value} (mean={mean:.2f}, stdev={stdev:.2f})"
        )
        
        alert_key = f"anomaly_{metric_name}"
        
        # Deduplicate anomaly alerts
        if alert_key in self._active_alerts:
            last_alert = self._active_alerts[alert_key]
            last_time = datetime.fromisoformat(last_alert.timestamp)
            if (datetime.utcnow() - last_time).total_seconds() < 300:
                return
        
        self._active_alerts[alert_key] = alert
        self._alert_history.append(alert)
        self._send_alert(alert)
    
    def _send_alert(self, alert: Alert):
        """
        Send alert through all configured channels.
        
        Args:
            alert: Alert to send
        """
        for channel in self._channels:
            try:
                channel.send(alert)
            except Exception as e:
                print(f"Failed to send alert via {channel.__class__.__name__}: {e}")
    
    def get_alert_history(self, limit: Optional[int] = None) -> List[Alert]:
        """
        Get alert history.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of alerts
        """
        with self._lock:
            history = list(self._alert_history)
            if limit:
                return history[-limit:]
            return history
    
    def get_active_alerts(self) -> List[Alert]:
        """
        Get currently active alerts.
        
        Returns:
            List of active alerts
        """
        with self._lock:
            return list(self._active_alerts.values())
    
    def clear_alert(self, alert_key: str):
        """
        Clear/acknowledge an alert.
        
        Args:
            alert_key: Alert key to clear
        """
        with self._lock:
            if alert_key in self._active_alerts:
                del self._active_alerts[alert_key]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """
        Get alert summary statistics.
        
        Returns:
            Dictionary with alert statistics
        """
        with self._lock:
            history = list(self._alert_history)
            
            severity_counts = defaultdict(int)
            for alert in history:
                severity_counts[alert.severity] += 1
            
            return {
                "total_alerts": len(history),
                "active_alerts": len(self._active_alerts),
                "by_severity": dict(severity_counts),
                "rules_count": len(self._rules),
                "enabled_rules": sum(1 for r in self._rules.values() if r.enabled),
            }
