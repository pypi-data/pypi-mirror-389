"""
Exporters for sending monitoring data to various backends.
"""
import json
import time
import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseExporter(ABC):
    """Base class for all exporters."""
    
    def __init__(self, config):
        self.config = config
        
    @abstractmethod
    def export_llm_call(self, llm_call):
        """Export an LLM call."""
        pass
        
    @abstractmethod
    def export_metrics(self, metrics: Dict[str, List[tuple]]):
        """Export metrics."""
        pass

class LogExporter(BaseExporter):
    """Export monitoring data to logs."""
    
    def __init__(self, config):
        super().__init__(config)
        self.logger = logging.getLogger("ai_monitor.export")
        
        # Configure logger
        if config.log_file:
            handler = logging.FileHandler(config.log_file)
        else:
            handler = logging.StreamHandler()
            
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(getattr(logging, config.log_level.upper()))
    
    def export_llm_call(self, llm_call):
        """Export LLM call to logs."""
        log_data = {
            'type': 'llm_call',
            'id': llm_call.id,
            'timestamp': llm_call.timestamp.isoformat(),
            'model': llm_call.model,
            'input_tokens': llm_call.input_tokens,
            'output_tokens': llm_call.output_tokens,
            'total_tokens': llm_call.total_tokens,
            'latency': llm_call.latency,
            'cost': llm_call.cost,
            'prompt_length': len(llm_call.prompt),
            'response_length': len(llm_call.response),
            'metadata': llm_call.metadata
        }
        
        self.logger.info(f"LLM_CALL: {json.dumps(log_data)}")
    
    def export_metrics(self, metrics: Dict[str, List[tuple]]):
        """Export metrics to logs."""
        for metric_name, values in metrics.items():
            if values:  # Only export if we have data
                latest_value = values[-1]  # Get most recent value
                log_data = {
                    'type': 'metric',
                    'name': metric_name,
                    'value': latest_value[1],
                    'timestamp': latest_value[0]
                }
                self.logger.debug(f"METRIC: {json.dumps(log_data)}")

class PrometheusExporter(BaseExporter):
    """Export monitoring data to Prometheus."""
    
    _instance = None
    _metrics_initialized = False
    
    def __new__(cls, config):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config):
        if hasattr(self, '_initialized'):
            return
        super().__init__(config)
        self._setup_prometheus()
        
        # Track unique users and success rate
        self._unique_users = set()
        self._total_requests = 0
        self._successful_requests = 0
        
        self._initialized = True
        
    def _setup_prometheus(self):
        """Setup Prometheus metrics."""
        if self._metrics_initialized:
            return
            
        try:
            from prometheus_client import Counter, Histogram, Gauge, start_http_server, CollectorRegistry, REGISTRY
            
            # Check if metrics already exist
            existing_names = {collector._name for collector in REGISTRY._collector_to_names.keys() 
                            if hasattr(collector, '_name')}
            
            if 'ai_monitor_llm_calls_total' in existing_names:
                logger.info("Prometheus metrics already initialized, reusing existing metrics")
                self._metrics_initialized = True
                return
            
            # Define metrics
            self.llm_calls_total = Counter(
                'ai_monitor_llm_calls_total',
                'Total number of LLM calls',
                ['model', 'request_path']
            )
            
            self.llm_latency = Histogram(
                'ai_monitor_llm_latency_seconds',
                'LLM call latency',
                ['model', 'request_path'],
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
            )
            
            self.llm_tokens = Counter(
                'ai_monitor_tokens_total',
                'Total tokens processed',
                ['model', 'type', 'request_path']  # type: input/output
            )
            
            self.llm_cost = Counter(
                'ai_monitor_cost_total',
                'Total cost',
                ['model', 'request_path']
            )
            
            self.agent_sessions = Counter(
                'ai_monitor_agent_sessions_total',
                'Total agent sessions',
                ['agent', 'status']  # status: started/completed/failed
            )
            
            self.tool_calls = Counter(
                'ai_monitor_tool_calls_total', 
                'Total tool calls',
                ['tool', 'status']  # status: success/error
            )
            
            # AI Quality Metrics
            self.quality_scores = Histogram(
                'ai_monitor_quality_score',
                'AI response quality scores',
                ['model', 'request_path'],
                buckets=[0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 1.0]
            )
            
            self.hallucination_risk = Counter(
                'ai_monitor_hallucination_risk_total',
                'Hallucination risk detections',
                ['model', 'risk_level', 'request_path']  # risk_level: low/medium/high
            )
            
            # AWS-Enhanced Hallucination Detection Metrics
            self.hallucination_detection_method = Counter(
                'ai_monitor_hallucination_detection_method_total',
                'Hallucination detection methods used',
                ['model', 'method', 'request_path']  # method: token_similarity/pattern_based/semantic_similarity/multi_layer
            )
            
            self.hallucination_score = Histogram(
                'ai_monitor_hallucination_score',
                'Hallucination scores from detection methods',
                ['model', 'method', 'request_path'],
                buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            )
            
            self.token_similarity_score = Histogram(
                'ai_monitor_token_similarity_score',
                'Token similarity scores (AWS method)',
                ['model', 'request_path'],
                buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            )
            
            self.semantic_similarity_score = Histogram(
                'ai_monitor_semantic_similarity_score',
                'Semantic similarity scores (AWS method)',
                ['model', 'request_path'],
                buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            )
            
            self.hallucination_detection_cost = Counter(
                'ai_monitor_hallucination_detection_cost_total',
                'API calls used for hallucination detection',
                ['model', 'method', 'request_path']  # Tracks embeddings API usage
            )
            
            self.drift_detections = Counter(
                'ai_monitor_drift_detections_total',
                'Response drift detections',
                ['model', 'drift_type', 'request_path']  # drift_type: detected/not_detected
            )
            
            self.quality_issues = Counter(
                'ai_monitor_quality_issues_total',
                'Quality issues detected',
                ['model', 'issue_type', 'request_path']
            )
            
            # Advanced Metrics - Percentile Latencies
            self.latency_p50 = Gauge(
                'ai_monitor_latency_p50_seconds',
                'P50 (median) latency in seconds',
                []
            )
            
            self.latency_p95 = Gauge(
                'ai_monitor_latency_p95_seconds',
                'P95 latency in seconds',
                []
            )
            
            self.latency_p99 = Gauge(
                'ai_monitor_latency_p99_seconds',
                'P99 latency in seconds',
                []
            )
            
            # Advanced Metrics - Concurrency
            self.active_requests = Gauge(
                'ai_monitor_active_requests',
                'Currently active requests',
                []
            )
            
            self.max_concurrent_requests = Gauge(
                'ai_monitor_max_concurrent_requests',
                'Maximum concurrent requests observed',
                []
            )
            
            # Advanced Metrics - Rate Metrics
            self.requests_per_minute = Gauge(
                'ai_monitor_requests_per_minute',
                'Current requests per minute',
                []
            )
            
            self.tokens_per_minute = Gauge(
                'ai_monitor_tokens_per_minute',
                'Current tokens per minute',
                []
            )
            
            # ============================================
            # NEW METRICS - Token Efficiency
            # ============================================
            self.tokens_per_second = Gauge(
                'ai_monitor_tokens_per_second',
                'Token throughput (tokens/latency)',
                ['model', 'request_path']
            )
            
            self.prompt_to_response_ratio = Gauge(
                'ai_monitor_prompt_to_response_ratio',
                'Output/input token ratio',
                ['model', 'request_path']
            )
            
            self.cached_tokens = Counter(
                'ai_monitor_cached_tokens_total',
                'Azure cache hits (cached prompt tokens)',
                ['model', 'request_path']
            )
            
            self.token_waste = Counter(
                'ai_monitor_token_waste_total',
                'Tokens in failed/retried requests',
                ['model', 'error_type', 'request_path']
            )
            
            # ============================================
            # NEW METRICS - Error & Reliability
            # ============================================
            self.errors_total = Counter(
                'ai_monitor_errors_total',
                'Failed LLM calls',
                ['model', 'error_type', 'request_path']  # error_type: timeout, rate_limit, auth, server_error, unknown
            )
            
            self.retries_total = Counter(
                'ai_monitor_retries_total',
                'Retry attempts',
                ['model', 'request_path']
            )
            
            self.timeouts_total = Counter(
                'ai_monitor_timeouts_total',
                'Requests exceeding latency threshold',
                ['model', 'threshold', 'request_path']
            )
            
            self.rate_limit_hits = Counter(
                'ai_monitor_rate_limit_hits_total',
                'Rate limiting events',
                ['model', 'request_path']
            )
            
            self.success_rate = Gauge(
                'ai_monitor_success_rate',
                'Success percentage (0-1)',
                ['model', 'request_path']
            )
            
            # ============================================
            # NEW METRICS - Business/User
            # ============================================
            self.unique_users = Gauge(
                'ai_monitor_unique_users_total',
                'Distinct users making requests',
                ['time_window']  # time_window: hourly, daily
            )
            
            self.requests_by_portfolio = Counter(
                'ai_monitor_requests_by_portfolio_total',
                'Requests breakdown by portfolio',
                ['portfolio', 'model']
            )
            
            self.report_generation_time = Histogram(
                'ai_monitor_report_generation_seconds',
                'End-to-end report generation time (DB + AI + formatting)',
                ['report_type', 'portfolio'],
                buckets=[1.0, 5.0, 10.0, 15.0, 30.0, 60.0]
            )
            
            # ============================================
            # NEW METRICS - Cost Optimization
            # ============================================
            self.daily_cost = Gauge(
                'ai_monitor_daily_cost',
                'Cost per day (resets daily)',
                ['model']
            )
            
            self.hourly_cost = Gauge(
                'ai_monitor_hourly_cost',
                'Cost per hour',
                ['model']
            )
            
            self.budget_remaining = Gauge(
                'ai_monitor_budget_remaining',
                'Budget remaining',
                ['budget_type']  # budget_type: daily, monthly
            )
            
            self.cost_per_request = Gauge(
                'ai_monitor_cost_per_request',
                'Average cost per request',
                ['model', 'request_path']
            )
            
            self.expensive_requests = Counter(
                'ai_monitor_expensive_requests_total',
                'Requests exceeding cost threshold',
                ['model', 'threshold', 'request_path']
            )
            
            # ============================================
            # NEW METRICS - Response Quality (Extended)
            # ============================================
            self.response_completeness = Histogram(
                'ai_monitor_response_completeness',
                'Response completeness score (0-1)',
                ['model', 'request_path'],
                buckets=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
            )
            
            self.response_relevance = Histogram(
                'ai_monitor_response_relevance',
                'Semantic relevance to prompt (0-1)',
                ['model', 'request_path'],
                buckets=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
            )
            
            self.response_length_chars = Histogram(
                'ai_monitor_response_length_chars',
                'Response length in characters',
                ['model', 'request_path'],
                buckets=[100, 500, 1000, 2000, 5000, 10000]
            )
            
            self.formatting_quality = Counter(
                'ai_monitor_formatting_quality_total',
                'Structured vs unstructured responses',
                ['model', 'format_type', 'request_path']  # format_type: structured, unstructured
            )
            
            # ============================================
            # NEW METRICS - Performance Percentiles (Extended)
            # ============================================
            self.latency_p90 = Gauge(
                'ai_monitor_latency_p90_seconds',
                'P90 latency in seconds',
                []
            )
            
            self.latency_p99_9 = Gauge(
                'ai_monitor_latency_p99_9_seconds',
                'P99.9 latency in seconds',
                []
            )
            
            self.tokens_per_second_p95 = Gauge(
                'ai_monitor_tokens_per_second_p95',
                'P95 token throughput',
                []
            )
            
            # ============================================
            # NEW METRICS - Model-Specific
            # ============================================
            self.model_temperature = Histogram(
                'ai_monitor_temperature',
                'Temperature setting distribution',
                ['model'],
                buckets=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.5, 2.0]
            )
            
            self.max_tokens_requested = Histogram(
                'ai_monitor_max_tokens_requested',
                'Max tokens parameter in requests',
                ['model'],
                buckets=[100, 500, 1000, 2000, 4000, 8000, 16000]
            )
            
            self.reasoning_tokens = Counter(
                'ai_monitor_reasoning_tokens_total',
                'Reasoning tokens (for o1 models)',
                ['model', 'request_path']
            )
            
            self.audio_tokens = Counter(
                'ai_monitor_audio_tokens_total',
                'Audio tokens (for multimodal models)',
                ['model', 'request_path']
            )
            
            # ============================================
            # NEW METRICS - Semantic/Content
            # ============================================
            self.pii_detections = Counter(
                'ai_monitor_pii_detections_total',
                'PII detected in prompts/responses',
                ['model', 'pii_type', 'location', 'request_path']  # location: prompt, response
            )
            
            self.toxic_content = Counter(
                'ai_monitor_toxic_content_total',
                'Toxic/harmful content flags',
                ['model', 'severity', 'request_path']
            )
            
            self.code_snippets = Counter(
                'ai_monitor_code_snippets_total',
                'Responses containing code',
                ['model', 'language', 'request_path']
            )
            
            # ============================================
            # NEW METRICS - Caching
            # ============================================
            self.cache_hit_rate = Gauge(
                'ai_monitor_cache_hit_rate',
                'Cache hit rate percentage (0-1)',
                ['model']
            )
            
            self.cache_savings_cost = Counter(
                'ai_monitor_cache_savings_cost_total',
                'Money saved via caching',
                ['model']
            )
            
            self.cache_savings_latency = Counter(
                'ai_monitor_cache_savings_latency_seconds_total',
                'Time saved via caching (estimated)',
                ['model']
            )
            
            # ============================================
            # NEW METRICS - SLO/SLA
            # ============================================
            self.slo_violations = Counter(
                'ai_monitor_slo_violations_total',
                'SLO breaches',
                ['violation_type', 'model', 'request_path']  # violation_type: latency, cost, quality
            )
            
            self.availability_percent = Gauge(
                'ai_monitor_availability_percent',
                'Service availability percentage',
                ['time_window']  # time_window: hourly, daily, monthly
            )
            
            self.error_budget_remaining = Gauge(
                'ai_monitor_error_budget_remaining',
                'SLO error budget remaining (0-1)',
                ['time_window']
            )
            
            self.reliability_score = Gauge(
                'ai_monitor_monthly_reliability_score',
                'Combined reliability metric (0-100)',
                []
            )
            
            # Start HTTP server (only if not already started)
            if not hasattr(self, '_server_started') or not self._server_started:
                start_http_server(self.config.prometheus_port)
                self._server_started = True
                logger.info(f"Prometheus metrics server started on port {self.config.prometheus_port}")
            
            self._metrics_initialized = True
            
        except ImportError:
            logger.warning("prometheus_client not installed, Prometheus export disabled")
            self.llm_calls_total = None
        except Exception as e:
            logger.error(f"Error setting up Prometheus metrics: {e}")
            # Don't mark as initialized if there was an error
            return
    
    def export_llm_call(self, llm_call):
        """Export LLM call to Prometheus with all enhanced metrics."""
        if not self.llm_calls_total:
            logger.warning("Prometheus metrics not initialized, skipping export")
            return
            
        model = llm_call.model
        request_path = llm_call.metadata.get('request_path', 'unknown')
        
        # ============================================
        # Core Metrics (Original)
        # ============================================
        self.llm_calls_total.labels(model=model, request_path=request_path).inc()
        self.llm_latency.labels(model=model, request_path=request_path).observe(llm_call.latency)
        self.llm_tokens.labels(model=model, type='input', request_path=request_path).inc(llm_call.input_tokens)
        self.llm_tokens.labels(model=model, type='output', request_path=request_path).inc(llm_call.output_tokens)
        self.llm_cost.labels(model=model, request_path=request_path).inc(llm_call.cost)
        
        # ============================================
        # Token Efficiency Metrics
        # ============================================
        try:
            # Tokens per second (throughput)
            if llm_call.latency > 0:
                tps = llm_call.total_tokens / llm_call.latency
                self.tokens_per_second.labels(model=model, request_path=request_path).set(tps)
            
            # Prompt to response ratio
            if llm_call.input_tokens > 0:
                ratio = llm_call.output_tokens / llm_call.input_tokens
                self.prompt_to_response_ratio.labels(model=model, request_path=request_path).set(ratio)
            
            # Cached tokens (from Azure OpenAI)
            cached_tokens = llm_call.metadata.get('cached_tokens', 0)
            if cached_tokens > 0:
                self.cached_tokens.labels(model=model, request_path=request_path).inc(cached_tokens)
                
                # Calculate cache savings
                from .cost_optimizer import CostOptimizer
                cache_savings = (cached_tokens / 1000) * CostOptimizer.MODEL_PRICING.get(model, {}).get('prompt', 0.002) * 0.5  # 50% discount
                self.cache_savings_cost.labels(model=model).inc(cache_savings)
                
                # Cache hit rate
                if llm_call.input_tokens > 0:
                    hit_rate = cached_tokens / llm_call.input_tokens
                    self.cache_hit_rate.labels(model=model).set(hit_rate)
        except Exception as e:
            logger.debug(f"Token efficiency metrics failed: {e}")
        
        # ============================================
        # Response Quality Metrics (Extended)
        # ============================================
        try:
            quality_analysis = llm_call.metadata.get('quality_analysis', {})
            if quality_analysis:
                # Quality score (existing)
                quality_score = quality_analysis.get('quality_score', 0.0)
                self.quality_scores.labels(model=model, request_path=request_path).observe(quality_score)
                
                # Hallucination risk (existing)
                hallucination_risk = quality_analysis.get('hallucination_risk', 'unknown')
                self.hallucination_risk.labels(model=model, risk_level=hallucination_risk, request_path=request_path).inc()
                
                # NEW: Hallucination detection method tracking (AWS best practices)
                detection_method = quality_analysis.get('detection_method', 'unknown')
                self.hallucination_detection_method.labels(
                    model=model, 
                    method=detection_method, 
                    request_path=request_path
                ).inc()
                
                # NEW: Overall hallucination score
                hallucination_score = quality_analysis.get('hallucination_score', 0.0)
                if hallucination_score > 0:
                    self.hallucination_score.labels(
                        model=model, 
                        method=detection_method, 
                        request_path=request_path
                    ).observe(hallucination_score)
                
                # NEW: Token similarity scores (if available)
                hallucination_metrics = quality_analysis.get('metrics', {}).get('hallucination', {})
                if isinstance(hallucination_metrics, dict):
                    method_scores = hallucination_metrics.get('method_scores', {})
                    
                    # Token similarity
                    if 'token_similarity' in method_scores:
                        token_score = method_scores['token_similarity'].get('combined_score', 0.0)
                        self.token_similarity_score.labels(
                            model=model, 
                            request_path=request_path
                        ).observe(token_score)
                    
                    # Semantic similarity
                    if 'semantic_similarity' in method_scores:
                        semantic_score = method_scores['semantic_similarity'].get('similarity_score', 0.0)
                        self.semantic_similarity_score.labels(
                            model=model, 
                            request_path=request_path
                        ).observe(semantic_score)
                    
                    # Detection cost (embedding API calls)
                    detection_cost = hallucination_metrics.get('cost', 0)
                    if detection_cost > 0:
                        self.hallucination_detection_cost.labels(
                            model=model,
                            method='semantic_similarity',
                            request_path=request_path
                        ).inc(detection_cost)
                
                # Drift detection (existing)
                drift_detected = quality_analysis.get('drift_detected', False)
                drift_type = 'detected' if drift_detected else 'not_detected'
                self.drift_detections.labels(model=model, drift_type=drift_type, request_path=request_path).inc()
                
                # Quality issues (existing)
                quality_issues = quality_analysis.get('quality_issues', [])
                for issue in quality_issues:
                    issue_type = issue.lower().replace(' ', '_')
                    self.quality_issues.labels(model=model, issue_type=issue_type, request_path=request_path).inc()
                
                # NEW: Response completeness
                metrics = quality_analysis.get('metrics', {})
                basic_quality = metrics.get('basic_quality', {})
                completeness = basic_quality.get('completeness', 0.0)
                if completeness > 0:
                    self.response_completeness.labels(model=model, request_path=request_path).observe(completeness)
                
                # NEW: Response relevance
                relevance = basic_quality.get('relevance_score', 0.0)
                if relevance > 0:
                    self.response_relevance.labels(model=model, request_path=request_path).observe(relevance)
                
                # NEW: Formatting quality
                has_structured = basic_quality.get('has_structured_response', False)
                format_type = 'structured' if has_structured else 'unstructured'
                self.formatting_quality.labels(model=model, format_type=format_type, request_path=request_path).inc()
                
        except Exception as quality_error:
            logger.debug(f"Quality metrics export failed: {quality_error}")
        
        # ============================================
        # Response Length
        # ============================================
        try:
            response_len = len(llm_call.response)
            self.response_length_chars.labels(model=model, request_path=request_path).observe(response_len)
        except Exception as e:
            logger.debug(f"Response length metric failed: {e}")
        
        # ============================================
        # Model-Specific Metrics
        # ============================================
        try:
            # Temperature
            temperature = llm_call.metadata.get('temperature', 0.7)
            if temperature is not None:
                self.model_temperature.labels(model=model).observe(float(temperature))
            
            # Max tokens
            max_tokens = llm_call.metadata.get('max_tokens', 0)
            if max_tokens > 0:
                self.max_tokens_requested.labels(model=model).observe(max_tokens)
            
            # Reasoning tokens (o1 models)
            reasoning_tokens = llm_call.metadata.get('reasoning_tokens', 0)
            if reasoning_tokens > 0:
                self.reasoning_tokens.labels(model=model, request_path=request_path).inc(reasoning_tokens)
            
            # Audio tokens (multimodal)
            audio_tokens = llm_call.metadata.get('audio_tokens', 0)
            if audio_tokens > 0:
                self.audio_tokens.labels(model=model, request_path=request_path).inc(audio_tokens)
        except Exception as e:
            logger.debug(f"Model-specific metrics failed: {e}")
        
        # ============================================
        # Cost Optimization Metrics
        # ============================================
        try:
            # Cost per request (moving average)
            self.cost_per_request.labels(model=model, request_path=request_path).set(llm_call.cost)
            
            # Expensive requests (threshold: $0.50)
            if llm_call.cost > 0.50:
                self.expensive_requests.labels(model=model, threshold='0.50', request_path=request_path).inc()
            if llm_call.cost > 1.00:
                self.expensive_requests.labels(model=model, threshold='1.00', request_path=request_path).inc()
        except Exception as e:
            logger.debug(f"Cost metrics failed: {e}")
        
        # ============================================
        # SLO Violations
        # ============================================
        try:
            # Latency SLO (>15s)
            if llm_call.latency > 15.0:
                self.slo_violations.labels(violation_type='latency', model=model, request_path=request_path).inc()
                self.timeouts_total.labels(model=model, threshold='15s', request_path=request_path).inc()
            
            # Cost SLO (>$1)
            if llm_call.cost > 1.00:
                self.slo_violations.labels(violation_type='cost', model=model, request_path=request_path).inc()
            
            # Quality SLO (<0.5)
            quality_analysis = llm_call.metadata.get('quality_analysis', {})
            if quality_analysis:
                quality_score = quality_analysis.get('quality_score', 1.0)
                if quality_score < 0.5:
                    self.slo_violations.labels(violation_type='quality', model=model, request_path=request_path).inc()
        except Exception as e:
            logger.debug(f"SLO metrics failed: {e}")
        
        # ============================================
        # Business Metrics
        # ============================================
        try:
            # Portfolio tracking
            portfolio = llm_call.metadata.get('portfolio', 'unknown')
            if portfolio != 'unknown':
                self.requests_by_portfolio.labels(portfolio=portfolio, model=model).inc()
            
            # User tracking
            user = llm_call.metadata.get('user') or llm_call.metadata.get('user_id') or llm_call.metadata.get('username')
            if user:
                self._unique_users.add(user)
                self.unique_users.set(len(self._unique_users))
            
            # Report generation time (if available)
            report_gen_time = llm_call.metadata.get('report_generation_time', 0)
            if report_gen_time > 0:
                report_type = llm_call.metadata.get('report_type', 'ops_insights')
                self.report_generation_time.labels(report_type=report_type, portfolio=portfolio).observe(report_gen_time)
            
            # Success rate calculation
            self._total_requests += 1
            error_occurred = llm_call.metadata.get('error') or llm_call.metadata.get('exception')
            if not error_occurred:
                self._successful_requests += 1
            
            if self._total_requests > 0:
                success_rate = self._successful_requests / self._total_requests
                self.success_rate.set(success_rate)
                
        except Exception as e:
            logger.debug(f"Business metrics failed: {e}")
        
        # ============================================
        # Content Safety (if security metrics available)
        # ============================================
        try:
            # Code detection
            if '```' in llm_call.response or 'def ' in llm_call.response or 'function ' in llm_call.response:
                # Simple heuristic for code detection
                language = 'python' if 'def ' in llm_call.response else 'unknown'
                self.code_snippets.labels(model=model, language=language, request_path=request_path).inc()
        except Exception as e:
            logger.debug(f"Content metrics failed: {e}")
    
    def export_metrics(self, metrics: Dict[str, List[tuple]]):
        """Export custom metrics to Prometheus."""
        if not self.llm_calls_total:
            return
            
        # Handle agent and tool metrics
        for metric_name, values in metrics.items():
            if not values:
                continue
                
            latest_value = values[-1][1]
            
            if metric_name.startswith('agent.') and 'sessions_started' in metric_name:
                agent_name = metric_name.split('.')[1]
                self.agent_sessions.labels(agent=agent_name, status='started').inc(latest_value)
            elif metric_name.startswith('agent.') and 'sessions_completed' in metric_name:
                agent_name = metric_name.split('.')[1] 
                self.agent_sessions.labels(agent=agent_name, status='completed').inc(latest_value)
            elif metric_name.startswith('agent.') and 'sessions_failed' in metric_name:
                agent_name = metric_name.split('.')[1]
                self.agent_sessions.labels(agent=agent_name, status='failed').inc(latest_value)
            elif metric_name.startswith('tool.') and 'success_calls' in metric_name:
                tool_name = metric_name.split('.')[1]
                self.tool_calls.labels(tool=tool_name, status='success').inc(latest_value)
            elif metric_name.startswith('tool.') and 'error_calls' in metric_name:
                tool_name = metric_name.split('.')[1]
                self.tool_calls.labels(tool=tool_name, status='error').inc(latest_value)
    
    def export_advanced_metrics(self, advanced_metrics):
        """Export advanced metrics to Prometheus gauges."""
        if not self.llm_calls_total:
            return
        
        try:
            all_metrics = advanced_metrics.get_all_metrics()
            
            # Export percentile latencies (existing + new p90, p99.9)
            latency_percentiles = all_metrics.get('latency_percentiles', {})
            if latency_percentiles:
                p50 = latency_percentiles.get('p50', 0.0)
                p90 = latency_percentiles.get('p90', 0.0)
                p95 = latency_percentiles.get('p95', 0.0)
                p99 = latency_percentiles.get('p99', 0.0)
                p99_9 = latency_percentiles.get('p99.9', 0.0)
                
                self.latency_p50.set(p50)
                self.latency_p90.set(p90)  # NEW
                self.latency_p95.set(p95)
                self.latency_p99.set(p99)
                self.latency_p99_9.set(p99_9)  # NEW
            
            # Export concurrency metrics
            concurrency = all_metrics.get('concurrency', {})
            if concurrency:
                active = concurrency.get('active_requests', 0)
                max_concurrent = concurrency.get('max_concurrent', 0)
                
                self.active_requests.set(active)
                self.max_concurrent_requests.set(max_concurrent)
            
            # Export rate metrics
            rate_metrics = all_metrics.get('rate_metrics', {})
            if rate_metrics:
                rpm = rate_metrics.get('current_rpm', 0)
                tpm = rate_metrics.get('current_tpm', 0)
                
                self.requests_per_minute.set(rpm)
                self.tokens_per_minute.set(tpm)
            
            # NEW: Export token throughput percentiles
            token_throughput = all_metrics.get('token_throughput', {})
            if token_throughput:
                tps_p95 = token_throughput.get('p95', 0.0)
                self.tokens_per_second_p95.set(tps_p95)
            
            # NEW: Export success rate
            reliability = all_metrics.get('reliability', {})
            if reliability:
                success_rate = reliability.get('success_rate', 1.0)
                # Update per model if available
                # For now, set global success rate
                # self.success_rate will be set per model in export_llm_call
            
            # NEW: Export SLO metrics
            slo_metrics = all_metrics.get('slo_metrics', {})
            if slo_metrics:
                availability = slo_metrics.get('availability_percent', 100.0)
                self.availability_percent.labels(time_window='hourly').set(availability)
                
                error_budget = slo_metrics.get('error_budget_remaining', 1.0)
                self.error_budget_remaining.labels(time_window='hourly').set(error_budget)
                
                reliability_score = slo_metrics.get('reliability_score', 100.0)
                self.reliability_score.set(reliability_score)
                
        except Exception as e:
            logger.error(f"Error exporting advanced metrics: {e}")
            import traceback
            logger.error(traceback.format_exc())


class JaegerExporter(BaseExporter):
    """Export monitoring data to Jaeger for distributed tracing."""
    
    def __init__(self, config):
        super().__init__(config)
        self._setup_jaeger()
        
    def _setup_jaeger(self):
        """Setup Jaeger tracing."""
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.jaeger.thrift import JaegerExporter as JaegerThriftExporter
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.sdk.resources import Resource
            
            # Configure resource
            resource = Resource.create({"service.name": "ai-monitor"})
            
            # Setup tracer
            trace.set_tracer_provider(TracerProvider(resource=resource))
            tracer_provider = trace.get_tracer_provider()
            
            # Setup Jaeger exporter
            jaeger_exporter = JaegerThriftExporter(
                agent_host_name="localhost",
                agent_port=6831,
            )
            
            # Add span processor
            span_processor = BatchSpanProcessor(jaeger_exporter)
            tracer_provider.add_span_processor(span_processor)
            
            self.tracer = trace.get_tracer(__name__)
            logger.info("Jaeger exporter configured successfully")
            
        except Exception as e:
            logger.warning(f"OpenTelemetry setup failed ({type(e).__name__}: {e}), Jaeger export disabled")
            self.tracer = None
    
    def export_llm_call(self, llm_call):
        """Export LLM call as Jaeger trace."""
        if not self.tracer:
            return
            
        with self.tracer.start_as_current_span(f"llm_call_{llm_call.model}") as span:
            span.set_attributes({
                "llm.call_id": llm_call.id,
                "llm.model": llm_call.model,
                "llm.input_tokens": llm_call.input_tokens,
                "llm.output_tokens": llm_call.output_tokens,
                "llm.total_tokens": llm_call.total_tokens,
                "llm.latency": llm_call.latency,
                "llm.cost": llm_call.cost,
                "llm.prompt_length": len(llm_call.prompt),
                "llm.response_length": len(llm_call.response)
            })
            
            # Add metadata as attributes
            for key, value in llm_call.metadata.items():
                span.set_attribute(f"llm.metadata.{key}", str(value))
    
    def export_metrics(self, metrics: Dict[str, List[tuple]]):
        """Export metrics as Jaeger spans."""
        if not self.tracer:
            return
            
        # Create spans for significant metrics
        with self.tracer.start_as_current_span("metrics_batch") as span:
            for metric_name, values in metrics.items():
                if values:
                    latest_value = values[-1][1]
                    span.set_attribute(f"metric.{metric_name}", latest_value)

class ConsoleExporter(BaseExporter):
    """Export monitoring data to console for debugging."""
    
    def export_llm_call(self, llm_call):
        """Export LLM call to console."""
        logger.info(f"[LLM CALL] {llm_call.model} | "
              f"Tokens: {llm_call.input_tokens}→{llm_call.output_tokens} | "
              f"Latency: {llm_call.latency:.2f}s | "
              f"Cost: ${llm_call.cost:.4f}")
    
    def export_metrics(self, metrics: Dict[str, List[tuple]]):
        """Export metrics to console."""
        for metric_name, values in metrics.items():
            if values and len(values) > 0:
                latest = values[-1]
                logger.info(f"[METRIC] {metric_name}: {latest[1]}")

class JSONFileExporter(BaseExporter):
    """Export monitoring data to JSON files."""
    
    def __init__(self, config, file_prefix="ai_monitor"):
        super().__init__(config)
        self.file_prefix = file_prefix
        
    def export_llm_call(self, llm_call):
        """Export LLM call to JSON file."""
        filename = f"{self.file_prefix}_llm_calls.jsonl"
        
        data = {
            'id': llm_call.id,
            'timestamp': llm_call.timestamp.isoformat(),
            'model': llm_call.model,
            'input_tokens': llm_call.input_tokens,
            'output_tokens': llm_call.output_tokens,
            'total_tokens': llm_call.total_tokens,
            'latency': llm_call.latency,
            'cost': llm_call.cost,
            'prompt': llm_call.prompt[:500],  # Truncate for file size
            'response': llm_call.response[:500],
            'metadata': llm_call.metadata
        }
        
        try:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data) + '\n')
        except Exception as e:
            logger.error(f"Failed to write LLM call to file: {e}")
    
    def export_metrics(self, metrics: Dict[str, List[tuple]]):
        """Export metrics to JSON file."""
        filename = f"{self.file_prefix}_metrics.jsonl"
        
        timestamp = time.time()
        data = {
            'timestamp': timestamp,
            'metrics': {name: values[-1] if values else None for name, values in metrics.items()}
        }
        
        try:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data) + '\n')
        except Exception as e:
            logger.error(f"Failed to write metrics to file: {e}")
