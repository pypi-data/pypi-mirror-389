"""
AI Agent Monitor - Plug & Play Monitoring Solution
=================================================

A comprehensive monitoring library for AI agents that requires no source code changes.
Simply import and use decorators or context managers.

Usage:
    from ai_monitor import AIMonitor, monitor_llm_call, monitor_agent
    
    # Decorator usage
    @monitor_llm_call()
    def my_llm_function():
        pass
    
    # Context manager usage
    with AIMonitor() as monitor:
        # Your AI agent code here
        pass
"""

from .core import AIMonitor, MonitoringConfig
from .decorators import monitor_llm_call, monitor_agent, monitor_tool_use
from .context_managers import LLMCallMonitor, AgentSessionMonitor, monitor_agent_session
from .collectors import MetricsCollector, TraceCollector
from .exporters import PrometheusExporter, JaegerExporter, LogExporter
from .detectors import HallucinationDetector, DriftDetector
from .utils import setup_monitoring, configure_exporters
from .auto_integrate import enable_auto_monitoring, one_line_setup, quick_monitor
from .http_interceptor import enable_http_monitoring, disable_http_monitoring
from .version import __version__, __version_info__

# Enhanced features - all now required
from .config import MonitorConfig, get_config, set_config, reset_config, PresetConfigs
from .async_core import AsyncAIMonitor, monitor_async
from .advanced_metrics import AdvancedMetricsCollector
from .alerting import AlertingSystem, AlertRule, Alert, ConsoleAlertChannel, LogFileAlertChannel, WebhookAlertChannel
from .cost_optimizer import CostOptimizer
from .semantic_analyzer import SemanticAnalyzer
from .quality_analyzer import AIQualityAnalyzer
from .security_metrics import SecurityMetrics
from .dashboard import MonitoringDashboard, create_dashboard

# Ensure HTTP monitoring is enabled on import for better cross-machine compatibility
try:
    from .http_interceptor import enable_http_monitoring
    import sys
    
    # Enable HTTP monitoring immediately if not already done
    if not hasattr(sys.modules.get('requests', {}), '_ai_monitor_patched'):
        enable_http_monitoring()
        # Mark as patched to avoid double-patching
        if 'requests' in sys.modules:
            sys.modules['requests']._ai_monitor_patched = True
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Could not auto-enable HTTP monitoring: {e}")

# Import plug & play functions
try:
    from .plug_and_play import (
        ultra_simple_setup, 
        setup_with_traceloop,
        flask_plug_and_play,
        agent_plug_and_play,
        langchain_plug_and_play,
        multi_agent_setup,
        setup,
        quick_setup,
        plug_and_play
    )
except ImportError:
    # Fallback if plug_and_play module has issues
    def ultra_simple_setup():
        return one_line_setup()
    
    setup = ultra_simple_setup
    quick_setup = ultra_simple_setup

__author__ = "AI Monitor Team"

# Default monitoring instance for quick setup
default_monitor = None

def init_monitoring(config=None):
    """Initialize default monitoring with optional configuration."""
    global default_monitor
    if config is None:
        config = MonitoringConfig()
    default_monitor = AIMonitor(config)
    return default_monitor

def get_monitor():
    """Get the default monitoring instance."""
    global default_monitor
    if default_monitor is None:
        default_monitor = init_monitoring()
    return default_monitor

# Auto-setup for immediate use
init_monitoring()

def debug_setup():
    """Debug function to check ai-monitor setup status"""
    import logging
    import sys
    
    logger = logging.getLogger(__name__)
    logger.info("🔍 [DEBUG] AI-Monitor Setup Status:")
    logger.info(f"   Version: {__version__}")
    logger.info(f"   Default monitor active: {default_monitor is not None}")
    
    # Check if HTTP interception is working
    try:
        import requests
        is_patched = hasattr(requests.post, '__name__') and 'monitored' in requests.post.__name__
        logger.info(f"   requests.post patched: {is_patched}")
        
        try:
            import httpx
            is_httpx_patched = hasattr(httpx.post, '__name__') and 'monitored' in httpx.post.__name__
            logger.info(f"   httpx.post patched: {is_httpx_patched}")
        except ImportError:
            logger.info(f"   httpx not available")
            
    except Exception as e:
        logger.info(f"   HTTP patching check failed: {e}")
    
    # Check available modules
    logger.info(f"   Available modules: {list(sys.modules.keys())[:10]}...")
    
    return {
        'version': __version__,
        'monitor_active': default_monitor is not None,
        'http_patched': hasattr(sys.modules.get('requests', {}), '_ai_monitor_patched')
    }

__all__ = [
    # Core
    'AIMonitor',
    'MonitoringConfig',
    'MonitorConfig',
    'PresetConfigs',
    # Decorators & Context Managers
    'monitor_llm_call',
    'monitor_agent', 
    'monitor_tool_use',
    'monitor_async',
    'LLMCallMonitor',
    'AgentSessionMonitor',
    'monitor_agent_session',
    # Collectors & Exporters
    'MetricsCollector',
    'TraceCollector',
    'PrometheusExporter',
    'JaegerExporter',
    'LogExporter',
    # Detectors
    'HallucinationDetector',
    'DriftDetector',
    # Setup Functions
    'setup_monitoring',
    'configure_exporters',
    'init_monitoring',
    'get_monitor',
    'enable_auto_monitoring',
    'one_line_setup',
    'quick_monitor',
    'debug_setup',
    # Enhanced Features
    'AsyncAIMonitor',
    'AdvancedMetricsCollector',
    'AlertingSystem',
    'AlertRule',
    'Alert',
    'ConsoleAlertChannel',
    'LogFileAlertChannel',
    'WebhookAlertChannel',
    'CostOptimizer',
    'SemanticAnalyzer',
    'SecurityMetrics',
    'MonitoringDashboard',
    'create_dashboard',
    # Configuration
    'get_config',
    'set_config',
    'reset_config',
    # ONE-LINE SETUP - The main feature!
    'enable_monitoring',
    'get_monitoring',
    'get_monitoring_stats',
]


# ============================================================================
# ONE-LINE AUTO-INTEGRATION - The Magic Happens Here!
# ============================================================================

_global_monitoring = None


def enable_monitoring(
    preset="full_featured",
    daily_budget=None,
    enable_dashboard=True,
    dashboard_port=5000,
    **kwargs
):
    """
    🚀 ONE-LINE SETUP - Enable complete AI monitoring with all features!
    
    This single function call enables:
    - Core monitoring with metrics collection
    - HTTP request interception (automatic AI call detection)
    - Advanced metrics (p50/p95/p99 latencies, concurrency, RPM/TPM)
    - Cost tracking and optimization
    - Semantic quality analysis
    - Security & PII detection
    - Anomaly detection & alerting
    - Real-time web dashboard
    - Prometheus metrics export
    
    Args:
        preset: Configuration preset ("full_featured", "production", "development")
        daily_budget: Daily cost budget limit in USD
        enable_dashboard: Start web dashboard (default: True)
        dashboard_port: Dashboard port (default: 5000)
        **kwargs: Additional configuration overrides
    
    Returns:
        Global monitoring instance
    
    Example:
        >>> from ai_monitor import enable_monitoring
        >>> enable_monitoring()  # That's it! Everything is now monitored!
        
        >>> # Or with custom settings:
        >>> enable_monitoring(
        ...     preset="production",
        ...     daily_budget=100.0,
        ...     dashboard_port=8080
        ... )
    
    After calling this, all your AI/LLM calls are automatically monitored!
    View metrics at: http://localhost:5000
    """
    global _global_monitoring
    
    import atexit
    import signal
    import sys
    from pathlib import Path
    
    if _global_monitoring is not None:
        print("⚠️  Monitoring already enabled")
        return _global_monitoring
    
    print("\n" + "="*70)
    print("🚀 AI MONITOR - ONE-LINE SETUP")
    print("="*70)
    
    # Load configuration
    config_overrides = kwargs.copy()
    if daily_budget:
        config_overrides['daily_budget_limit'] = daily_budget
    config_overrides['enable_dashboard'] = enable_dashboard
    config_overrides['dashboard_port'] = dashboard_port
    
    # Load preset configuration
    if preset == "production":
        from .config import PresetConfigs
        config = PresetConfigs.production()
    elif preset == "development":
        from .config import PresetConfigs
        config = PresetConfigs.development()
    elif preset == "cost_optimized":
        from .config import PresetConfigs
        config = PresetConfigs.cost_optimized()
    elif preset == "security_focused":
        from .config import PresetConfigs
        config = PresetConfigs.security_focused()
    else:  # full_featured
        from .config import PresetConfigs
        config = PresetConfigs.full_featured()
    
    # Apply overrides
    config.update(**config_overrides)
    
    # Initialize components
    components = {}
    
    print("\n📦 Initializing components...")
    
    # 1. Core Monitor
    print("  ✓ Core monitoring")
    monitor = AIMonitor()
    components['monitor'] = monitor
    
    # 2. HTTP Interceptor
    print("  ✓ HTTP interceptor (auto-detect AI calls)")
    enable_http_monitoring()
    components['http_interceptor'] = True
    
    # 2.5. Patch OpenAI/Azure OpenAI SDK
    print("  ✓ OpenAI SDK patching (Azure OpenAI support)")
    try:
        enable_auto_monitoring(
            monitor_openai=True,
            monitor_anthropic=False,
            monitor_langchain=False,
            agent_name="flask_app"
        )
        components['sdk_patching'] = True
    except Exception as e:
        print(f"    ⚠️  SDK patching failed: {e}")
        components['sdk_patching'] = False
    
    # 3. Advanced Metrics (with resource tracking enabled)
    print("  ✓ Advanced metrics (percentiles, concurrency, RPM/TPM, CPU/memory)")
    advanced_metrics = AdvancedMetricsCollector(
        window_size=3600,
        enable_resource_tracking=True  # Always enable resource tracking
    )
    components['advanced_metrics'] = advanced_metrics
    
    # 4. Cost Optimizer (always enabled with default pricing)
    print("  ✓ Cost optimizer & budget tracking")
    cost_optimizer = CostOptimizer(
        daily_budget=config.daily_budget_limit,
        monthly_budget=config.monthly_budget_limit
    )
    components['cost_optimizer'] = cost_optimizer
    
    # 5. Quality Analyzer (always attempt to enable for quality metrics)
    print("  ✓ Quality analysis (hallucination, drift, scores)")
    try:
        quality_analyzer = AIQualityAnalyzer()
        components['semantic_analyzer'] = quality_analyzer  # Keep same key for compatibility
        print("    ✅ Quality metrics enabled")
    except Exception as e:
        print(f"    ⚠️  Quality metrics disabled: {e}")
    
    # 6. Security Metrics (always attempt to enable)
    print("  ✓ Security & PII detection")
    try:
        security_metrics = SecurityMetrics(
            enable_pii_detection=config.enable_pii_detection,
            enable_content_moderation=config.enable_content_moderation,
            pii_redaction=config.pii_redaction
        )
        components['security_metrics'] = security_metrics
        print("    ✅ Security metrics enabled")
    except Exception as e:
        print(f"    ⚠️  Security metrics disabled: {e}")
    
    
    # 7. Alerting System - DISABLED (Prometheus only)
    # if config.enable_alerting:
    #     print("  ✓ Alerting & anomaly detection")
    #     alerting = AlertingSystem(
    #         anomaly_sensitivity=config.anomaly_sensitivity
    #     )
    #     components['alerting'] = alerting
    
    # 8. Dashboard - DISABLED (Prometheus only)
    # if enable_dashboard:
    #     print(f"  ✓ Web dashboard on port {dashboard_port}")
    #     dashboard = MonitoringDashboard(monitor=monitor, port=dashboard_port)
    #     components['dashboard'] = dashboard
    
    # Store global state
    _global_monitoring = {
        'config': config,
        'components': components,
        'monitor': monitor
    }
    
    # Start the monitoring loop for periodic metric exports
    print("  ✓ Starting monitoring loop (exports every 1s)")
    monitor.start_monitoring()
    
    # Register cleanup
    def cleanup():
        print("\n🛑 Shutting down AI Monitor...")
        # Stop monitoring thread
        if monitor and hasattr(monitor, 'stop_monitoring'):
            try:
                monitor.stop_monitoring()
                print("  ✓ Monitoring thread stopped")
            except:
                pass
        # Export final metrics
        if monitor and hasattr(monitor, '_export_metrics'):
            try:
                monitor._export_metrics()
                print("  ✓ Final metrics exported")
            except:
                pass
    
    atexit.register(cleanup)
    
    # Success message
    print("\n" + "="*70)
    print("✅ AI MONITOR READY!")
    print("="*70)
    print(f"\n Prometheus:  http://{config.prometheus_host}:{config.prometheus_port}/metrics")
    if config.daily_budget_limit:
        print(f"💰 Daily Budget: ${config.daily_budget_limit}")
    print(f"\n🔍 Active Components: {len(components)}")
    for name in components.keys():
        print(f"   • {name}")
    print("\n🎯 All AI/LLM calls are now being monitored automatically!")
    print("📊 View Prometheus metrics at the URL above")
    print("="*70 + "\n")
    
    return _global_monitoring


def get_monitoring():
    """Get the global monitoring instance"""
    return _global_monitoring


def get_monitoring_stats():
    """Get current monitoring statistics"""
    if _global_monitoring is None:
        return {"status": "not_enabled"}
    
    monitor = _global_monitoring['monitor']
    components = _global_monitoring['components']
    
    stats = {
        "status": "active",
        "components_count": len(components),
        "components": list(components.keys()),
    }
    
    # Get metrics from advanced_metrics if available
    if 'advanced_metrics' in components:
        adv = components['advanced_metrics']
        stats['advanced_metrics'] = adv.get_all_metrics()
    
    # Get cost info if available
    if 'cost_optimizer' in components:
        cost = components['cost_optimizer']
        stats['cost'] = {
            'daily': cost.get_daily_cost(),
            'monthly': cost.get_monthly_cost(),
        }
    
    return stats
