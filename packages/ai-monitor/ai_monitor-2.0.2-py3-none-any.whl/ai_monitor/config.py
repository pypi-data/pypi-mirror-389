"""
Centralized configuration management for AI Monitor.

This module provides a flexible configuration system with support for
file-based configuration (YAML/JSON) and environment variables.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import os
import json
from pathlib import Path


@dataclass
class MonitorConfig:
    """Centralized configuration for AI monitoring."""
    
    # Collection settings
    enable_metrics: bool = True
    enable_quality_analysis: bool = True
    sampling_rate: float = 1.0  # 0.0 to 1.0 - percentage of requests to monitor
    
    # Performance settings
    batch_size: int = 100
    flush_interval: int = 10  # seconds
    max_history: int = 10000  # maximum number of requests to keep in memory
    async_mode: bool = False
    
    # Export settings
    exporters: List[str] = field(default_factory=lambda: ["prometheus"])
    prometheus_port: int = 8000
    prometheus_host: str = "0.0.0.0"
    datadog_api_key: Optional[str] = None
    datadog_app_key: Optional[str] = None
    azure_monitor_connection_string: Optional[str] = None
    json_export_path: Optional[str] = "./metrics"
    
    # Quality settings
    quality_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "min_quality_score": 60.0,
        "max_response_time": 30.0,
        "min_response_length": 10,
        "max_error_rate": 0.05
    })
    enable_semantic_analysis: bool = False
    enable_sentiment_analysis: bool = False
    
    # Cost settings
    cost_tracking: bool = True
    budget_alerts: bool = False
    daily_budget_limit: Optional[float] = None
    monthly_budget_limit: Optional[float] = None
    cost_alert_threshold: float = 0.8  # Alert at 80% of budget
    
    # Security settings
    enable_pii_detection: bool = False
    enable_content_moderation: bool = False
    pii_redaction: bool = False
    
    # Alerting settings
    enable_alerting: bool = False
    alert_channels: List[str] = field(default_factory=list)
    anomaly_detection: bool = False
    anomaly_sensitivity: float = 3.0  # z-score threshold
    
    # Dashboard settings
    enable_dashboard: bool = False
    dashboard_port: int = 5000
    dashboard_host: str = "localhost"
    
    # Advanced metrics
    enable_advanced_metrics: bool = True
    track_percentiles: bool = True
    track_concurrency: bool = True
    track_resource_usage: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not 0.0 <= self.sampling_rate <= 1.0:
            raise ValueError("sampling_rate must be between 0.0 and 1.0")
        
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        
        if self.flush_interval <= 0:
            raise ValueError("flush_interval must be positive")
        
        if self.max_history <= 0:
            raise ValueError("max_history must be positive")
        
        # Load from environment variables if not set
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        if not self.datadog_api_key:
            self.datadog_api_key = os.getenv("DATADOG_API_KEY")
        
        if not self.datadog_app_key:
            self.datadog_app_key = os.getenv("DATADOG_APP_KEY")
        
        if not self.azure_monitor_connection_string:
            self.azure_monitor_connection_string = os.getenv(
                "AZURE_MONITOR_CONNECTION_STRING"
            )
        
        # Override with environment variables if present
        sampling_rate_env = os.getenv("AI_MONITOR_SAMPLING_RATE")
        if sampling_rate_env:
            self.sampling_rate = float(sampling_rate_env)
        
        batch_size_env = os.getenv("AI_MONITOR_BATCH_SIZE")
        if batch_size_env:
            self.batch_size = int(batch_size_env)
        
        dashboard_env = os.getenv("AI_MONITOR_ENABLE_DASHBOARD")
        if dashboard_env:
            self.enable_dashboard = dashboard_env.lower() == "true"
    
    @classmethod
    def from_file(cls, filepath: str) -> 'MonitorConfig':
        """
        Load configuration from a YAML or JSON file.
        
        Args:
            filepath: Path to configuration file (.yaml, .yml, or .json)
            
        Returns:
            MonitorConfig instance
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is unsupported
        """
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        
        suffix = path.suffix.lower()
        
        if suffix == '.json':
            with open(filepath, 'r') as f:
                config_dict = json.load(f)
        elif suffix in ['.yaml', '.yml']:
            try:
                import yaml
                with open(filepath, 'r') as f:
                    config_dict = yaml.safe_load(f)
            except ImportError:
                raise ImportError(
                    "PyYAML is required to load YAML configuration files. "
                    "Install it with: pip install pyyaml"
                )
        else:
            raise ValueError(f"Unsupported configuration file format: {suffix}")
        
        return cls(**config_dict)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'MonitorConfig':
        """
        Create configuration from dictionary.
        
        Args:
            config_dict: Dictionary with configuration values
            
        Returns:
            MonitorConfig instance
        """
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of configuration
        """
        from dataclasses import asdict
        return asdict(self)
    
    def to_file(self, filepath: str):
        """
        Save configuration to a JSON file.
        
        Args:
            filepath: Path to save configuration
        """
        path = Path(filepath)
        
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def update(self, **kwargs):
        """
        Update configuration values.
        
        Args:
            **kwargs: Configuration key-value pairs to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown configuration key: {key}")
        
        # Re-validate
        self.__post_init__()


# Default global configuration
_default_config = MonitorConfig()


def get_config() -> MonitorConfig:
    """Get the current global configuration."""
    return _default_config


def set_config(config: MonitorConfig):
    """Set the global configuration."""
    global _default_config
    _default_config = config


def reset_config():
    """Reset to default configuration."""
    global _default_config
    _default_config = MonitorConfig()


# Preset configurations for common use cases
class PresetConfigs:
    """Predefined configurations for common scenarios"""
    
    @staticmethod
    def development() -> MonitorConfig:
        """Development configuration with verbose logging and metrics only"""
        return MonitorConfig(
            enable_metrics=True,
            enable_quality_analysis=True,
            enable_semantic_analysis=True,
            sampling_rate=1.0,
            exporters=["prometheus", "json"],
            enable_dashboard=False,  # Disabled - only Prometheus
            enable_pii_detection=True,
            enable_content_moderation=True,
            enable_alerting=False,  # Disabled - only Prometheus
            cost_tracking=True,
            anomaly_detection=False  # Disabled - only Prometheus
        )
    
    @staticmethod
    def production() -> MonitorConfig:
        """Production configuration optimized for performance - Prometheus only"""
        return MonitorConfig(
            enable_metrics=True,
            enable_quality_analysis=False,  # Disabled for performance
            enable_semantic_analysis=False,  # Disabled for performance
            sampling_rate=0.1,  # Sample 10% of requests
            batch_size=500,
            flush_interval=30,
            async_mode=True,
            exporters=["prometheus"],
            enable_dashboard=False,  # Disabled - only Prometheus
            enable_pii_detection=False,
            enable_content_moderation=False,
            cost_tracking=True,
            enable_alerting=False  # Disabled - only Prometheus
        )
    
    @staticmethod
    def cost_optimized() -> MonitorConfig:
        """Configuration focused on cost tracking - Prometheus metrics only"""
        return MonitorConfig(
            enable_metrics=True,
            enable_quality_analysis=False,
            enable_semantic_analysis=False,
            cost_tracking=True,
            budget_alerts=False,  # Disabled - only Prometheus
            enable_alerting=False,  # Disabled - only Prometheus
            alert_channels=["console"],
            enable_dashboard=False  # Disabled - only Prometheus
        )
    
    @staticmethod
    def security_focused() -> MonitorConfig:
        """Configuration with security features - Prometheus metrics only"""
        return MonitorConfig(
            enable_metrics=True,
            enable_quality_analysis=True,
            enable_pii_detection=True,
            enable_content_moderation=True,
            pii_redaction=True,
            enable_alerting=False,  # Disabled - only Prometheus
            alert_channels=["console"],
            enable_dashboard=False  # Disabled - only Prometheus
        )
    
    @staticmethod
    def full_featured() -> MonitorConfig:
        """All monitoring features enabled - Complete metrics suite"""
        return MonitorConfig(
            enable_metrics=True,
            enable_quality_analysis=True,
            enable_semantic_analysis=True,  # Enable quality metrics
            cost_tracking=True,
            budget_alerts=False,  # Disabled - only Prometheus
            enable_pii_detection=True,
            enable_content_moderation=True,
            pii_redaction=False,  # Don't redact, just detect
            enable_alerting=False,  # Disabled - only Prometheus
            enable_dashboard=False,  # Disabled - only Prometheus
            anomaly_detection=False,  # Disabled - only Prometheus
            alert_channels=["console"],
            exporters=["prometheus", "json"],
            sampling_rate=1.0,
            enable_advanced_metrics=True,
            track_percentiles=True,
            track_concurrency=True,
            track_resource_usage=True  # Enable CPU/memory tracking
        )
