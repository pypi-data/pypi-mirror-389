"""
Core AI Monitoring Classes
"""
import time
import threading
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class MonitoringConfig:
    """Configuration for AI monitoring."""
    # Exporters
    enable_prometheus: bool = True
    enable_jaeger: bool = True
    enable_logging: bool = True
    
    # Prometheus config
    prometheus_port: int = 8000
    prometheus_host: str = "localhost"
    
    # Jaeger config
    jaeger_endpoint: str = "http://localhost:14268/api/traces"
    
    # Logging config
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Monitoring features
    track_tokens: bool = True
    track_latency: bool = True
    detect_hallucination: bool = True
    detect_drift: bool = True
    track_costs: bool = True
    
    # Sampling
    trace_sampling_rate: float = 1.0
    metrics_collection_interval: float = 1.0
    
    # Storage
    max_trace_history: int = 10000
    max_metrics_history: int = 100000

@dataclass
class LLMCall:
    """Represents an LLM call for monitoring."""
    id: str
    timestamp: datetime
    model: str
    prompt: str
    response: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency: float
    cost: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
class AIMonitor:
    """Main AI monitoring class that can be used as context manager or singleton."""
    
    def __init__(self, config: Optional[MonitoringConfig] = None):
        self.config = config or MonitoringConfig()
        self.session_id = str(uuid.uuid4())
        self.start_time = time.time()
        
        # Storage
        self.llm_calls: deque = deque(maxlen=self.config.max_trace_history)
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.config.max_metrics_history))
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Exporters
        self._exporters = []
        self._setup_exporters()
        
        # Background monitoring
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()
        
    def _setup_exporters(self):
        """Setup configured exporters."""
        if self.config.enable_prometheus:
            try:
                from .exporters import PrometheusExporter
                self._exporters.append(PrometheusExporter(self.config))
            except ImportError:
                logger.warning("Prometheus exporter not available")
                
        if self.config.enable_jaeger:
            try:
                from .exporters import JaegerExporter
                self._exporters.append(JaegerExporter(self.config))
            except ImportError:
                logger.warning("Jaeger exporter not available")
                
        if self.config.enable_logging:
            try:
                from .exporters import LogExporter
                self._exporters.append(LogExporter(self.config))
            except ImportError:
                logger.warning("Log exporter not available")
    
    def __enter__(self):
        """Context manager entry."""
        self.start_monitoring()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_monitoring()
        
    def start_monitoring(self):
        """Start background monitoring."""
        if self._monitoring_thread is None or not self._monitoring_thread.is_alive():
            self._stop_monitoring.clear()
            self._monitoring_thread = threading.Thread(target=self._monitoring_loop)
            self._monitoring_thread.daemon = True
            self._monitoring_thread.start()
            
    def stop_monitoring(self):
        """Stop background monitoring."""
        self._stop_monitoring.set()
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5.0)
    
    def _monitoring_loop(self):
        """Background monitoring loop."""
        while not self._stop_monitoring.is_set():
            try:
                self._collect_system_metrics()
                self._export_metrics()
                time.sleep(self.config.metrics_collection_interval)
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
    
    def _collect_system_metrics(self):
        """Collect system-level metrics."""
        timestamp = time.time()
        
        # Memory usage
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent()
            
            self.record_metric("system.memory_mb", memory_mb, timestamp)
            self.record_metric("system.cpu_percent", cpu_percent, timestamp)
        except ImportError:
            pass
    
    def record_llm_call(self, 
                       model: str,
                       prompt: str, 
                       response: str,
                       input_tokens: int,
                       output_tokens: int,
                       latency: float,
                       cost: float = 0.0,
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """Record an LLM call for monitoring."""
        
        # CRITICAL DEBUG: Show what tokens were passed in
        logger.info(f"🚨 [CRITICAL] record_llm_call called with:")
        logger.info(f"   Model: {model}")
        logger.info(f"   Input tokens: {input_tokens} (type: {type(input_tokens)})")
        logger.info(f"   Output tokens: {output_tokens} (type: {type(output_tokens)})")
        logger.info(f"   Metadata: {metadata}")
        
        # FIXED: Always prioritize Azure/OpenAI provided tokens
        if input_tokens > 0:
            logger.info(f"✅ [FIXED] Using Azure/OpenAI provided tokens: {input_tokens}")
            # Use the exact tokens provided by Azure - no corrections needed
        else:
            logger.info(f"⚠️ [FIXED] No tokens provided, will calculate from prompt...")
            
        # FIXED: Only calculate tokens if Azure/OpenAI didn't provide them
        if input_tokens == 0 and prompt and len(prompt) > 0:
            # More accurate estimation methods that better match Azure OpenAI
            
            # Method 1: Character-based (conservative baseline)
            char_estimate = len(prompt) // 4  # ~4 chars per token
            
            # Method 2: Word + punctuation based (more accurate for English)
            import re
            # Count words, punctuation, and special characters separately
            words = len(re.findall(r'\b\w+\b', prompt))
            punctuation = len(re.findall(r'[^\w\s]', prompt))
            spaces = prompt.count(' ')
            word_estimate = int(words * 1.2 + punctuation * 0.5 + spaces * 0.3)
            
            # Method 3: tiktoken approximation (most accurate for GPT models)
            # Based on actual tiktoken analysis: GPT-4 averages ~6.4 chars per token
            # This is more accurate than the traditional ~4 chars per token
            subword_estimate = len(prompt) // 6.2  # More accurate based on tiktoken analysis
            
            # Method 4: Try actual tiktoken if available (most accurate)
            tiktoken_exact = None
            try:
                import tiktoken
                # Map Azure OpenAI model names to tiktoken encodings
                model_encodings = {
                    'gpt-4': 'cl100k_base',
                    'gpt-4.1': 'cl100k_base',
                    'gpt-4-turbo': 'cl100k_base',
                    'gpt-4o': 'o200k_base',
                    'gpt-4o-mini': 'o200k_base',
                    'gpt-35-turbo': 'cl100k_base',
                    'gpt-3.5-turbo': 'cl100k_base'
                }
                
                # Extract base model name for encoding lookup (handle Azure deployment names)
                base_model = model.lower().replace('_', '-').split(':')[0].split('/')[0]  # Handle deployment names and URLs
                encoding_name = model_encodings.get(base_model, 'cl100k_base')  # Default to GPT-4 encoding
                
                encoding = tiktoken.get_encoding(encoding_name)
                tiktoken_exact = len(encoding.encode(prompt))
                
                # FIXED: Don't apply Azure correction factor - Azure gives exact tokens
                # The original correction was incorrect and causing mismatches
                logger.info(f"🎯 [FIXED] Exact tiktoken count: {tiktoken_exact} (using {encoding_name})")
                
            except ImportError:
                logger.info("ℹ️ [FIXED] tiktoken not available, using approximation")
            except Exception as e:
                logger.info(f"⚠️ [FIXED] tiktoken error: {e}")
            
            # Method 5: Hybrid approach (weighted average, updated with better ratios)
            hybrid_estimate = int(
                char_estimate * 0.1 +      # 10% weight - too conservative
                word_estimate * 0.2 +      # 20% weight - linguistic structure  
                subword_estimate * 0.7     # 70% weight - most accurate approximation
            )
            
            # Use tiktoken if available, otherwise use hybrid estimate
            if tiktoken_exact is not None:
                input_tokens = tiktoken_exact
                logger.info(f"✅ [FIXED] Using exact tiktoken count: {input_tokens}")
            else:
                input_tokens = max(hybrid_estimate, char_estimate, 1)
                logger.info(f"📊 [FIXED] Using hybrid estimate: {input_tokens}")
            
            logger.info(f"🔧 [FIXED] Calculated input tokens: {input_tokens} (from {len(prompt)} chars, ratio: {len(prompt)/input_tokens:.1f})")
            if tiktoken_exact is None:
                logger.info(f"📊 [FIXED] Estimation methods - char: {char_estimate}, word: {word_estimate}, subword: {int(subword_estimate)}, final: {input_tokens}")
        
        call_id = str(uuid.uuid4())
        llm_call = LLMCall(
            id=call_id,
            timestamp=datetime.now(),
            model=model,
            prompt=prompt,
            response=response,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency=latency,
            cost=cost,
            metadata=metadata or {}
        )
        
        with self._lock:
            self.llm_calls.append(llm_call)
            
        # Record metrics
        timestamp = time.time()
        self.record_metric(f"llm.{model}.latency", latency, timestamp)
        self.record_metric(f"llm.{model}.input_tokens", input_tokens, timestamp)
        self.record_metric(f"llm.{model}.output_tokens", output_tokens, timestamp)
        self.record_metric(f"llm.{model}.total_tokens", input_tokens + output_tokens, timestamp)
        self.record_metric(f"llm.{model}.cost", cost, timestamp)
        
        # CRITICAL: Record advanced metrics if available
        try:
            from . import get_monitoring
            global_monitoring = get_monitoring()
            if global_monitoring and 'components' in global_monitoring:
                advanced_metrics = global_monitoring['components'].get('advanced_metrics')
                if advanced_metrics:
                    # Track the completed request with advanced metrics
                    # Note: Since record_llm_call is called after the request completes,
                    # we add the latency directly without needing start/end tracking
                    current_time = time.time()
                    advanced_metrics._latencies.append(latency)
                    advanced_metrics._latency_timestamps.append(current_time)
                    
                    # Model-specific tracking
                    advanced_metrics._model_latencies[model].append(latency)
                    advanced_metrics._model_request_counts[model] = advanced_metrics._model_request_counts.get(model, 0) + 1
                    
                    # Track tokens
                    total_tokens = input_tokens + output_tokens
                    advanced_metrics.track_tokens(total_tokens)
                    
                    # Update RPM counter
                    advanced_metrics._update_rpm_counter()
                    
                    logger.info(f"✅ [Advanced Metrics] Recorded: latency={latency:.3f}s, tokens={total_tokens}, model={model}")
                
                # CRITICAL: Run quality analysis if semantic analyzer available
                semantic_analyzer = global_monitoring['components'].get('semantic_analyzer')
                if semantic_analyzer and prompt and response:
                    try:
                        quality_analysis = semantic_analyzer.analyze_response_quality(
                            prompt=prompt,
                            response=response,
                            metadata=metadata
                        )
                        # Add quality analysis to metadata for export
                        llm_call.metadata['quality_analysis'] = quality_analysis
                        logger.info(f"✅ [Quality Analysis] score={quality_analysis.get('quality_score', 0):.2f}, "
                                  f"hallucination={quality_analysis.get('hallucination_risk', 'unknown')}, "
                                  f"drift={quality_analysis.get('drift_detected', False)}")
                    except Exception as qe:
                        logger.debug(f"Quality analysis failed: {qe}")
        except Exception as e:
            logger.debug(f"Could not record advanced metrics: {e}")
        
        # Export to configured exporters
        self._export_llm_call(llm_call)
        
        return call_id
    
    def record_metric(self, name: str, value: float, timestamp: Optional[float] = None):
        """Record a metric value."""
        if timestamp is None:
            timestamp = time.time()
            
        with self._lock:
            self.metrics[name].append((timestamp, value))
    
    def _export_llm_call(self, llm_call: LLMCall):
        """Export LLM call to all configured exporters."""
        for exporter in self._exporters:
            try:
                exporter.export_llm_call(llm_call)
            except Exception as e:
                logger.error(f"Exporter {type(exporter).__name__} error: {e}")
    
    def _export_metrics(self):
        """Export metrics to all configured exporters."""
        for exporter in self._exporters:
            try:
                exporter.export_metrics(dict(self.metrics))
                
                # Export advanced metrics if exporter supports it and we have the global monitoring
                if hasattr(exporter, 'export_advanced_metrics'):
                    try:
                        from . import get_monitoring
                        global_monitoring = get_monitoring()
                        if global_monitoring and 'components' in global_monitoring:
                            advanced_metrics = global_monitoring['components'].get('advanced_metrics')
                            if advanced_metrics:
                                exporter.export_advanced_metrics(advanced_metrics)
                    except Exception as e:
                        logger.debug(f"Could not export advanced metrics: {e}")
                        
            except Exception as e:
                logger.error(f"Exporter {type(exporter).__name__} error: {e}")
    
    def get_metrics(self, name: Optional[str] = None) -> Dict[str, List[tuple]]:
        """Get collected metrics."""
        with self._lock:
            if name:
                return {name: list(self.metrics.get(name, []))}
            return {k: list(v) for k, v in self.metrics.items()}
    
    def get_llm_calls(self, limit: Optional[int] = None) -> List[LLMCall]:
        """Get recorded LLM calls."""
        with self._lock:
            calls = list(self.llm_calls)
            if limit:
                calls = calls[-limit:]
            return calls
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        with self._lock:
            total_calls = len(self.llm_calls)
            if total_calls == 0:
                return {"total_calls": 0}
            
            total_tokens = sum(call.total_tokens for call in self.llm_calls)
            total_cost = sum(call.cost for call in self.llm_calls)
            avg_latency = sum(call.latency for call in self.llm_calls) / total_calls
            
            return {
                "session_id": self.session_id,
                "uptime_seconds": time.time() - self.start_time,
                "total_calls": total_calls,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "average_latency": avg_latency,
                "tokens_per_second": total_tokens / (time.time() - self.start_time)
            }

# Global monitor instance for HTTP interception
_default_monitor = None

def get_default_monitor():
    """Get the default monitor instance."""
    return _default_monitor

def set_default_monitor(monitor):
    """Set the default monitor instance."""
    global _default_monitor
    _default_monitor = monitor

