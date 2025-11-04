# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-11-03

### 🚀 Major Release - Enterprise Features

#### Added
- **Async Support**: `AsyncAIMonitor` class for non-blocking monitoring
  - `monitor_async` decorator for async functions
  - Async-compatible metrics collection and export
  - Background task management for high-throughput applications
  
- **Advanced Metrics**: Enhanced analytics capabilities via `AdvancedMetricsCollector`
  - Percentile latencies (P50, P95, P99)
  - Concurrency tracking (active requests, peak concurrency)
  - Resource utilization monitoring (CPU, memory via psutil)
  - Time-windowed metrics (requests per minute, tokens per minute)
  - Rate limiting and throttling event tracking

- **Alerting System**: Threshold-based monitoring and anomaly detection
  - Configurable alert rules with `AlertRule` class
  - Multiple alert channels: `ConsoleAlertChannel`, `LogFileAlertChannel`, `WebhookAlertChannel`
  - Statistical anomaly detection
  - Alert severity levels (critical, warning, info)
  - Duration-based alerting (trigger only after sustained condition)
  
- **Cost Optimization**: Budget management and cost analysis via `CostOptimizer`
  - Real-time cost tracking with per-model pricing
  - Budget alerts (daily and monthly limits)
  - Model cost comparison and recommendations
  - Caching opportunity identification
  - Prompt optimization suggestions
  - Azure OpenAI and OpenAI pricing support

- **Security Metrics**: Compliance and safety features via `SecurityMetrics`
  - PII detection (email, phone, SSN, credit cards, IP addresses, URLs)
  - Content moderation and toxicity detection
  - GDPR compliance tracking
  - Data retention policy enforcement
  - Authentication and authorization monitoring

- **Semantic Analysis**: AI output quality validation via `SemanticAnalyzer`
  - Semantic similarity scoring between prompts and responses
  - Topic coherence checking
  - Context preservation validation
  - Relevance scoring using sentence transformers
  - Embedding-based quality metrics

- **Web Dashboard**: Real-time monitoring UI via Flask
  - Live metrics visualization
  - Historical data display with time-series charts
  - Alert management interface
  - REST API endpoints for programmatic access
  - CORS support for frontend integration
  - Real-time updates via polling

- **Configuration Management**: Centralized config via `MonitorConfig`
  - YAML/JSON configuration file support
  - Environment variable integration
  - Preset configurations (`PresetConfigs.DEVELOPMENT`, `STAGING`, `PRODUCTION`)
  - Dynamic configuration updates
  - Sampling rate control
  - Batch processing configuration

- **Business Metrics Documentation**: `BUSINESS_METRICS_IMPLEMENTATION.md`
  - Comprehensive guide for portfolio tracking
  - User analytics implementation
  - Cost allocation strategies
  - Report generation metrics

#### Changed
- **Minimum Python Version**: Now requires Python 3.8+ (was 3.7+)
- **Enhanced `__init__.py`**: Added 30+ new exports for v2.0 features
- **Updated Dependencies**: Added psutil>=5.9.0 to core dependencies
- **Package Structure**: 8 new modules added to ai_monitor package
- **Development Status**: Changed from Beta to Production/Stable

#### Dependencies
- **Added to Core**: `psutil>=5.9.0` (resource monitoring)
- **New Optional - Dashboard**: `flask>=2.0.0`, `flask-cors>=3.0.0`
- **New Optional - Semantic**: `sentence-transformers>=2.0.0`
- **Updated**: `opentelemetry-api>=1.22.0` (was 1.15.0)
- **Updated**: `opentelemetry-sdk>=1.22.0` (was 1.15.0)
- **Updated**: `opentelemetry-exporter-jaeger>=1.21.0` (was 1.15.0)

#### Migration
- ✅ **All v1.x code remains 100% compatible**
- ✅ **New features are opt-in via optional dependencies**
- ✅ **No breaking changes to existing APIs**
- ✅ **Backward-compatible configuration**
- 📖 **See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for upgrade details**

#### Installation
```bash
# Basic upgrade
pip install --upgrade ai-monitor

# With all v2.0 features
pip install ai-monitor[all]

# Specific features
pip install ai-monitor[dashboard]  # Web dashboard
pip install ai-monitor[semantic]   # Semantic analysis
```

---

## [1.0.11] - 2025-10-26

### Added
- **Request Path Capture**: Enhanced `@monitor_llm_call` decorator to automatically capture request paths from multiple web frameworks (Flask, FastAPI, Django, Bottle, CherryPy) for better API endpoint distinction
- **Prometheus Request Path Labels**: Added `request_path` label to all LLM-related Prometheus metrics to distinguish between different API endpoints calling AI services

### Enhanced
- **Framework Compatibility**: Improved decorator portability across Python web frameworks with graceful fallback handling
- **Metrics Granularity**: Enhanced monitoring granularity by including request context in metrics labels

## [1.0.10] - 2024-10-25log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.9] - 2024-10-24

### Added
- **tiktoken Dependency**: Added `tiktoken>=0.5.0` as core dependency for accurate token counting in HTTP interceptor

### Removed
- **traceloop-sdk**: Removed from optional dependencies to reduce package conflicts and simplify installation

### Fixed
- **Dependency Management**: Ensured all external packages used in ai_monitor are properly declared in requirements

## [1.0.8] - 2024-10-24

### Added
- **Cross-Machine Compatibility**: Enhanced decorator system with force HTTP monitoring setup to ensure consistent behavior across different servers
- **Debug Tools**: Added comprehensive debug utilities including `debug_setup()` function and test scripts
- **Enhanced Logging**: Improved decorator initialization logging with "🔧 [DECORATOR INIT]" messages for better troubleshooting
- **Debug Scripts**: Created `simple_debug.py` and `test_decorator_debug.py` for cross-machine testing
- **One-Liner Tests**: Added quick copy-paste debug commands for rapid server testing
- **Cross-Machine Debug Guide**: Comprehensive troubleshooting documentation in `CROSS_MACHINE_DEBUG.md`

### Fixed
- **Decorator Reliability**: Fixed issues where `@monitor_llm_call()` decorator would work locally but fail on other machines
- **HTTP Monitoring**: Ensured HTTP request patching is properly initialized within decorators
- **Import Order Issues**: Enhanced package initialization to handle various import sequences
- **Silent Failures**: Added extensive debug logging to identify why decorators fail to apply

### Enhanced
- **Decorator System**: Force-enables HTTP monitoring setup on every decorator call for maximum compatibility
- **Error Tracking**: Comprehensive logging throughout the monitoring chain for easier debugging
- **Package Exports**: Added debug utilities to main package exports for easier access

## [1.0.7] - 2024-10-24

### Added
- **Core Dependencies**: Added `httpx>=0.24.0` and `requests>=2.25.0` as required dependencies
- **Enhanced HTTP Monitoring**: Improved HTTPX client monitoring with better error handling

### Fixed
- **Dependency Issues**: Resolved missing httpx dependency causing import errors on clean installations
- **Token Calculation**: Fixed Azure OpenAI token calculation discrepancies

## [1.0.5] - 2024-10-23

### Fixed
- **Version Requirements**: Added + Corrected
Support for other open ai calls 
Calculation/Extraction of tokens

## [1.0.4] - 2024-10-15

### Fixed
- **Version Requirements**: Corrected opentelemetry-exporter-jaeger version requirement to >=1.21.0 (latest available)
- **Installation**: Fixed ai-monitor[all] installation by using correct dependency versions

## [1.0.3] - 2024-10-15

### Fixed
- **Dependency Conflicts**: Removed traceloop-sdk from `ai-monitor[all]` to resolve googleapis-common-protos conflicts
- **Installation Options**: `ai-monitor[all]` now includes tracing, prometheus, and system monitoring without conflicts

### Changed
- Separated traceloop from the all-in-one installation option

## [1.0.2] - 2024-10-15

### Fixed
- **Dependency Conflicts**: Updated OpenTelemetry to v1.22+ for full compatibility with Traceloop SDK
- **googleapis-common-protos**: Resolved protobuf version conflicts in ai-monitor[all] installation

### Changed
- Updated tracing dependencies to OpenTelemetry v1.22.0+ for better compatibility

## [1.0.1] - 2024-10-15

### Fixed
- **Dependency Conflicts**: Resolved OpenTelemetry version conflicts between Jaeger and Traceloop
- **Installation Options**: Separated `tracing` (v1.20+) and `jaeger` (v1.15) optional dependencies
- **Compatibility**: Fixed `ai-monitor[all]` installation issues

### Changed
- Updated OpenTelemetry dependencies to compatible versions
- Added separate `jaeger` optional dependency for legacy Jaeger support

### Installation
```bash
# All features (now works without conflicts)
pip install ai-monitor[all]

# Specific tracing options
pip install ai-monitor[tracing]        # Modern Jaeger (v1.20+)
pip install ai-monitor[jaeger]         # Legacy Jaeger (v1.15)
```
- **Plug & Play Monitoring**: Zero-configuration monitoring for AI agents
- **HTTP Interception**: Automatic monitoring of OpenAI API calls
- **Quality Analysis**: Hallucination detection and drift analysis
- **Prometheus Metrics**: Comprehensive metrics export
- **OpenTelemetry Tracing**: Distributed tracing support
- **Traceloop Integration**: Enterprise-grade observability
- **Decorator API**: Easy-to-use decorators for monitoring
- **Context Managers**: Flexible monitoring contexts
- **Flask Integration**: One-line Flask app monitoring
- **Multi-Agent Support**: Monitor complex agent systems
- **LangChain Integration**: Seamless LangChain monitoring

### Features
- **Zero Source Code Changes**: Drop-in monitoring solution
- **Automatic LLM Detection**: Recognizes OpenAI, Anthropic, and custom APIs
- **Real-time Metrics**: Latency, tokens, costs, and quality scores
- **Comprehensive Tracing**: Request/response tracing with metadata
- **Quality Assurance**: Automated hallucination and drift detection
- **Multiple Export Options**: Prometheus, Jaeger, and Traceloop
- **System Metrics**: CPU, memory, and disk monitoring
- **Alert Integration**: Configurable thresholds and alerts

### Dependencies
- Core: `numpy>=1.20.0`
- Optional: Prometheus, OpenTelemetry, Traceloop SDK, psutil

### Installation
```bash
pip install ai-monitor
# For full features:
pip install ai-monitor[all]
```
