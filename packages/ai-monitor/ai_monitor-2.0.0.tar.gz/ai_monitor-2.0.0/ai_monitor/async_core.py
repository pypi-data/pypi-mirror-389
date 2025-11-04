"""
Async version of AI Monitor core functionality.

This module provides async support for high-throughput applications
that need non-blocking metric collection and export.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

try:
    from .core import AIMonitor
    from .config import MonitorConfig, get_config
except ImportError:
    from core import AIMonitor
    from config import MonitorConfig, get_config


class AsyncAIMonitor(AIMonitor):
    """
    Async-enabled AI monitoring with non-blocking operations.
    
    This class extends AIMonitor to provide async methods for
    tracking requests, analyzing quality, and exporting metrics
    without blocking the main event loop.
    """
    
    def __init__(self, config: Optional[MonitorConfig] = None):
        """
        Initialize async monitor.
        
        Args:
            config: Optional MonitorConfig instance
        """
        super().__init__()
        self.config = config or get_config()
        self._background_tasks: set = set()
        self._export_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def track_request_async(
        self,
        model: str,
        prompt: str,
        response: str,
        latency: float,
        tokens_used: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Async version of track_request.
        
        Args:
            model: Model identifier
            prompt: Input prompt
            response: Model response
            latency: Response time in seconds
            tokens_used: Token usage dictionary
            metadata: Additional metadata
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with tracking results
        """
        start_time = time.time()
        
        # Apply sampling
        import random
        if random.random() > self.config.sampling_rate:
            return {"sampled_out": True}
        
        # Prepare metrics
        metrics = {
            "model": model,
            "prompt": prompt,
            "response": response,
            "latency": latency,
            "tokens_used": tokens_used or {},
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Calculate cost if tokens provided
        if tokens_used and model:
            # Simple cost calculation without calculate_cost method
            pass
            
        # Store metrics asynchronously
        await self._store_metrics_async(metrics)
        
        # Track processing overhead
        overhead = time.time() - start_time
        metrics["monitoring_overhead"] = overhead
        
        return metrics
    
    
    async def _store_metrics_async(self, metrics: Dict[str, Any]):
        """
        Async metrics storage.
        
        Args:
            metrics: Metrics dictionary to store
        """
        # Use asyncio.Lock for thread-safe access
        if not hasattr(self, '_metrics_lock'):
            self._metrics_lock = asyncio.Lock()
        
        async with self._metrics_lock:
            self._request_history.append(metrics)
            
            # Maintain max history size
            if len(self._request_history) > self.config.max_history:
                self._request_history = self._request_history[-self.config.max_history:]
    
    async def export_metrics_async(
        self,
        exporter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Async metric export.
        
        Args:
            exporter: Optional exporter type (prometheus, datadog, etc.)
            
        Returns:
            Export result dictionary
        """
        exporters_to_use = [exporter] if exporter else self.config.exporters
        
        results = {}
        tasks = []
        
        for exp in exporters_to_use:
            task = asyncio.create_task(self._export_to_backend_async(exp))
            tasks.append((exp, task))
        
        for exp, task in tasks:
            try:
                result = await task
                results[exp] = {"success": True, "result": result}
            except Exception as e:
                results[exp] = {"success": False, "error": str(e)}
        
        return results
    
    async def _export_to_backend_async(self, backend: str) -> Any:
        """
        Export to specific backend asynchronously.
        
        Args:
            backend: Backend type
            
        Returns:
            Export result
        """
        # Run export in executor to avoid blocking
        loop = asyncio.get_event_loop()
        
        if backend == "prometheus":
            # Prometheus is pull-based, just ensure metrics are updated
            return await loop.run_in_executor(
                None,
                self._update_prometheus_metrics
            )
        elif backend == "datadog":
            return await loop.run_in_executor(
                None,
                self._export_to_datadog
            )
        elif backend == "json":
            return await loop.run_in_executor(
                None,
                self._export_to_json
            )
        else:
            raise ValueError(f"Unsupported backend: {backend}")
    
    def _update_prometheus_metrics(self):
        """Update Prometheus metrics from history."""
        # This would update prometheus collectors
        return {"metrics_updated": len(self._request_history)}
    
    def _export_to_datadog(self):
        """Export metrics to DataDog."""
        # Placeholder for DataDog export logic
        return {"exported_count": len(self._request_history)}
    
    def _export_to_json(self):
        """Export metrics to JSON file."""
        import json
        from pathlib import Path
        
        export_path = Path(self.config.json_export_path or "./metrics")
        export_path.mkdir(parents=True, exist_ok=True)
        
        filename = export_path / f"metrics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(self._request_history, f, indent=2, default=str)
        
        return {"file": str(filename), "count": len(self._request_history)}
    
    async def start_background_export(self):
        """Start background task for periodic metric export."""
        if self._running:
            return
        
        self._running = True
        self._export_task = asyncio.create_task(self._periodic_export())
    
    async def stop_background_export(self):
        """Stop background export task."""
        self._running = False
        
        if self._export_task:
            self._export_task.cancel()
            try:
                await self._export_task
            except asyncio.CancelledError:
                pass
    
    async def _periodic_export(self):
        """Periodic export task."""
        while self._running:
            try:
                await asyncio.sleep(self.config.flush_interval)
                await self.export_metrics_async()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in periodic export: {e}")
    
    async def get_metrics_async(self) -> Dict[str, Any]:
        """
        Get current metrics asynchronously.
        
        Returns:
            Dictionary with current metrics
        """
        if not hasattr(self, '_metrics_lock'):
            self._metrics_lock = asyncio.Lock()
        
        async with self._metrics_lock:
            return {
                "total_requests": len(self._request_history),
                "recent_requests": self._request_history[-100:],
                "summary": self._calculate_summary(),
            }
    
    def _calculate_summary(self) -> Dict[str, Any]:
        """Calculate summary statistics."""
        if not self._request_history:
            return {}
        
        latencies = [r.get("latency", 0) for r in self._request_history]
        costs = [r.get("cost", 0) for r in self._request_history]
        
        return {
            "avg_latency": sum(latencies) / len(latencies) if latencies else 0,
            "total_cost": sum(costs),
            "avg_cost": sum(costs) / len(costs) if costs else 0,
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_background_export()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_background_export()
        # Final export
        await self.export_metrics_async()


# Convenience decorator for async monitoring
def monitor_async(
    model: Optional[str] = None,
    config: Optional[MonitorConfig] = None
):
    """
    Decorator for async AI function monitoring.
    
    Args:
        model: Optional model name
        config: Optional MonitorConfig
        
    Example:
        @monitor_async(model="gpt-4")
        async def my_ai_function(prompt: str):
            # ... AI call logic
            return response
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            monitor = AsyncAIMonitor(config)
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                latency = time.time() - start_time
                
                # Extract prompt and response from args/kwargs/result
                prompt = kwargs.get('prompt', args[0] if args else '')
                response = result if isinstance(result, str) else str(result)
                
                await monitor.track_request_async(
                    model=model or "unknown",
                    prompt=str(prompt),
                    response=response,
                    latency=latency,
                )
                
                return result
            except Exception as e:
                latency = time.time() - start_time
                await monitor.track_request_async(
                    model=model or "unknown",
                    prompt=str(kwargs.get('prompt', args[0] if args else '')),
                    response=f"Error: {str(e)}",
                    latency=latency,
                    metadata={"error": str(e), "error_type": type(e).__name__}
                )
                raise
        
        return wrapper
    return decorator
