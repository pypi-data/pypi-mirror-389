# Migration Guide: v1.x to v2.0

This guide helps you migrate from ai-monitor v1.x to v2.0.

## Breaking Changes

### 1. Minimum Python Version
- **v1.x**: Python 3.7+
- **v2.0**: Python 3.8+

### 2. New Dependencies

v2.0 introduces optional dependencies for new features:

```bash
# Dashboard
pip install ai-monitor[dashboard]

# Semantic analysis
pip install ai-monitor[semantic]

# All features
pip install ai-monitor[all]
```

### 3. Configuration Changes

**Old (v1.x):**
```python
from ai_monitor import AIMonitor

monitor = AIMonitor(
    service_name="my-app",
    enable_prometheus=True,
    enable_jaeger=True
)
```

**New (v2.0) - Backward Compatible:**
```python
from ai_monitor import AIMonitor, MonitorConfig

# Option 1: Use new config system
config = MonitorConfig(
    enable_metrics=True,
    enable_tracing=True,
    sampling_rate=1.0
)

monitor = AIMonitor(config=config)

# Option 2: Old way still works
monitor = AIMonitor()  # Uses defaults
```

## New Features in v2.0

### 1. Async Support

```python
from ai_monitor import AsyncAIMonitor

monitor = AsyncAIMonitor()

@monitor.monitor_async
async def my_async_function():
    # Your async code
    pass
```

### 2. Alerting System

```python
from ai_monitor import AlertingSystem, AlertRule, ConsoleAlertChannel

alerting = AlertingSystem()
alerting.add_rule(AlertRule(
    name="High Latency",
    metric_name="latency",
    threshold=1000,  # ms
    severity="warning"
))

# Add alert channel
alerting.add_channel(ConsoleAlertChannel())
alerting.start()
```

### 3. Web Dashboard

```python
from ai_monitor import create_dashboard

# Create and run dashboard
dashboard = create_dashboard(port=8080)
dashboard.run()

# Visit http://localhost:8080 to see real-time metrics
```

### 4. Cost Optimization

```python
from ai_monitor import CostOptimizer

optimizer = CostOptimizer(
    daily_budget=100.0,
    monthly_budget=1000.0
)

# Track costs automatically
optimizer.track_request(
    model="gpt-4",
    prompt_tokens=100,
    completion_tokens=200
)

# Get optimization recommendations
recommendations = optimizer.get_recommendations()
for rec in recommendations:
    print(f"{rec['type']}: {rec['description']}")
```

### 5. Security Metrics

```python
from ai_monitor import SecurityMetrics

security = SecurityMetrics()

# Check for PII in user input
user_input = "My email is john@example.com"
has_pii, pii_types = security.detect_pii(user_input)

if has_pii:
    print(f"PII detected: {pii_types}")

# Content moderation
is_toxic, score = security.check_toxicity(text)
```

### 6. Semantic Analysis

```python
from ai_monitor import SemanticAnalyzer

analyzer = SemanticAnalyzer()

# Check semantic similarity between prompt and response
similarity = analyzer.calculate_similarity(
    prompt="What is AI?",
    response="Artificial Intelligence is..."
)

print(f"Relevance score: {similarity}")
```

### 7. Advanced Metrics

```python
from ai_monitor import AdvancedMetricsCollector

metrics = AdvancedMetricsCollector()

# Get percentile latencies
latencies = metrics.get_latency_percentiles()
print(f"P95 latency: {latencies['p95']}ms")
print(f"P99 latency: {latencies['p99']}ms")

# Get concurrency stats
concurrency = metrics.get_concurrency_stats()
print(f"Current concurrent requests: {concurrency['current']}")
print(f"Max concurrent: {concurrency['max']}")
```

### 8. Centralized Configuration

```python
from ai_monitor import MonitorConfig, PresetConfigs

# Use preset configurations
config = PresetConfigs.PRODUCTION

# Or load from YAML file
config = MonitorConfig.from_file("config.yaml")

# Or customize
config = MonitorConfig(
    enable_metrics=True,
    enable_quality_analysis=True,
    sampling_rate=0.1,  # Sample 10% of requests
    batch_size=100,
    async_mode=True
)

monitor = AIMonitor(config=config)
```

## Compatibility

✅ **All v1.x code will continue to work in v2.0**

New features are additive and optional. Your existing monitoring code requires no changes.

## Upgrade Steps

### 1. Update Package

```bash
pip install --upgrade ai-monitor
```

### 2. Install Optional Dependencies (if needed)

```bash
# For all features
pip install ai-monitor[all]

# Or specific features
pip install ai-monitor[dashboard]
pip install ai-monitor[semantic]
```

### 3. Test Your Application

```python
import ai_monitor
print(f"Version: {ai_monitor.__version__}")  # Should show 2.0.0

# Test existing code works
from ai_monitor import AIMonitor
monitor = AIMonitor()
print("✓ Basic monitoring works")

# Test new features (optional)
from ai_monitor import AsyncAIMonitor, create_dashboard
print("✓ New features available")
```

### 4. Gradually Adopt New Features

Start using new features in non-critical paths first:
- Add alerting for specific metrics
- Enable dashboard for development/staging
- Use cost optimizer to track spending
- Add security checks for user inputs

## Example: Full Migration

**Before (v1.x):**
```python
import ai_monitor

# Simple setup
ai_monitor.ultra_simple_setup()

# Your AI code
import openai
response = openai.ChatCompletion.create(...)
```

**After (v2.0) - Enhanced:**
```python
import ai_monitor
from ai_monitor import AlertingSystem, AlertRule, CostOptimizer

# Simple setup still works
ai_monitor.ultra_simple_setup()

# Add new features
alerting = AlertingSystem()
alerting.add_rule(AlertRule(
    name="High Cost",
    metric_name="cost",
    threshold=10.0,
    severity="critical"
))
alerting.start()

# Add cost tracking
optimizer = CostOptimizer(daily_budget=100.0)

# Your AI code (unchanged)
import openai
response = openai.ChatCompletion.create(...)

# Get insights
recommendations = optimizer.get_recommendations()
```

## Common Migration Scenarios

### Scenario 1: Basic Monitoring
**No changes needed** - v1.x code works as-is

### Scenario 2: Adding Dashboard
```python
# Add this to your existing code
from ai_monitor import create_dashboard

dashboard = create_dashboard(port=8080)
dashboard.run(debug=False)
```

### Scenario 3: Adding Alerts
```python
from ai_monitor import get_monitor, AlertingSystem, AlertRule

monitor = get_monitor()

# Add alerting to existing monitor
alerting = AlertingSystem()
alerting.add_rule(AlertRule(
    name="Slow Response",
    metric_name="latency",
    threshold=2000,
    duration=60  # Alert if true for 60s
))
alerting.start()
```

### Scenario 4: Async Applications
```python
# Replace AIMonitor with AsyncAIMonitor
from ai_monitor import AsyncAIMonitor

monitor = AsyncAIMonitor()

@monitor.track_operation("chat")
async def chat_with_ai(prompt):
    # Your async code
    response = await async_openai_call(prompt)
    return response
```

## Troubleshooting

### Import Errors
If you get import errors for new features:
```bash
# Install missing dependencies
pip install ai-monitor[all]
```

### Version Check
```python
import ai_monitor
print(ai_monitor.__version__)  # Should be 2.0.0
```

### Feature Availability
```python
# Check if new features are available
try:
    from ai_monitor import AsyncAIMonitor, create_dashboard
    print("✓ All v2.0 features available")
except ImportError as e:
    print(f"Missing: {e}")
    print("Install with: pip install ai-monitor[all]")
```

## Performance Considerations

### v2.0 Performance Improvements
- Async support reduces blocking overhead
- Better batching for metrics export
- Configurable sampling rates
- Resource-aware monitoring

### Recommended Settings for Production
```python
from ai_monitor import MonitorConfig, PresetConfigs

# Use production preset
config = PresetConfigs.PRODUCTION

# Or customize
config = MonitorConfig(
    sampling_rate=0.1,  # Sample 10% for high-volume
    batch_size=1000,    # Larger batches
    async_mode=True,    # Non-blocking
    enable_semantic_analysis=False  # Disable if not needed
)
```

## Getting Help

### Documentation
- [README.md](README.md) - Quick start guide
- [CHANGELOG.md](CHANGELOG.md) - What's new in v2.0
- [METRICS_DOCUMENTATION.md](METRICS_DOCUMENTATION.md) - Available metrics

### Support
- GitHub Issues: [Report bugs](https://github.com/Maersk-Global/ai-llm/issues)
- GitHub Discussions: [Ask questions](https://github.com/Maersk-Global/ai-llm/discussions)

## Questions?

Open an issue on GitHub if you have migration questions or encounter problems.
