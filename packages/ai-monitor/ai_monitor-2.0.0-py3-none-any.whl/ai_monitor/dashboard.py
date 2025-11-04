"""
Web dashboard for AI/LLM monitoring.

Provides real-time visualization and REST API for monitoring metrics.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

try:
    from flask import Flask, render_template, jsonify, request
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


class MonitoringDashboard:
    """
    Web dashboard for monitoring AI/LLM metrics.
    
    Features:
    - Real-time metrics display
    - REST API endpoints
    - Historical data visualization
    - Alert management
    
    Note: Requires Flask. Install with: pip install flask flask-cors
    """
    
    def __init__(
        self,
        monitor=None,
        host: str = "localhost",
        port: int = 5000,
        debug: bool = False
    ):
        """
        Initialize dashboard.
        
        Args:
            monitor: AIMonitor instance
            host: Host to bind to
            port: Port to listen on
            debug: Enable debug mode
        """
        if not FLASK_AVAILABLE:
            raise ImportError(
                "Flask is required for dashboard. "
                "Install with: pip install flask flask-cors"
            )
        
        self.monitor = monitor
        self.host = host
        self.port = port
        self.debug = debug
        
        self.app = Flask(__name__)
        CORS(self.app)
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Dashboard home page."""
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>AI Monitor Dashboard</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .metric-card { 
                        border: 1px solid #ddd; 
                        padding: 15px; 
                        margin: 10px 0;
                        border-radius: 5px;
                    }
                    .metric-value { font-size: 24px; font-weight: bold; color: #007bff; }
                    .metric-label { color: #666; }
                    h1 { color: #333; }
                    .refresh-btn {
                        background: #007bff;
                        color: white;
                        padding: 10px 20px;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                    }
                </style>
            </head>
            <body>
                <h1>🤖 AI Monitor Dashboard</h1>
                <button class="refresh-btn" onclick="loadMetrics()">Refresh</button>
                <div id="metrics"></div>
                
                <script>
                    async function loadMetrics() {
                        const response = await fetch('/api/metrics');
                        const data = await response.json();
                        
                        const metricsHtml = `
                            <div class="metric-card">
                                <div class="metric-label">Total Requests</div>
                                <div class="metric-value">${data.summary.total_requests || 0}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">Average Latency</div>
                                <div class="metric-value">${(data.summary.avg_latency || 0).toFixed(3)}s</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">Total Cost</div>
                                <div class="metric-value">$${(data.summary.total_cost || 0).toFixed(4)}</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">Average Quality Score</div>
                                <div class="metric-value">${(data.summary.avg_quality || 0).toFixed(1)}</div>
                            </div>
                        `;
                        
                        document.getElementById('metrics').innerHTML = metricsHtml;
                    }
                    
                    // Load metrics on page load
                    loadMetrics();
                    
                    // Auto-refresh every 10 seconds
                    setInterval(loadMetrics, 10000);
                </script>
            </body>
            </html>
            """
        
        @self.app.route('/api/metrics')
        def api_metrics():
            """Get current metrics summary."""
            if not self.monitor:
                return jsonify({"error": "No monitor configured"}), 500
            
            try:
                summary = self._get_metrics_summary()
                return jsonify(summary)
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/metrics/detailed')
        def api_metrics_detailed():
            """Get detailed metrics."""
            if not self.monitor:
                return jsonify({"error": "No monitor configured"}), 500
            
            try:
                metrics = {
                    "summary": self._get_metrics_summary(),
                    "recent_requests": self._get_recent_requests(),
                    "model_breakdown": self._get_model_breakdown(),
                }
                return jsonify(metrics)
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/metrics/history')
        def api_metrics_history():
            """Get metrics history."""
            hours = request.args.get('hours', default=24, type=int)
            
            if not self.monitor:
                return jsonify({"error": "No monitor configured"}), 500
            
            try:
                history = self._get_metrics_history(hours)
                return jsonify(history)
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/alerts')
        def api_alerts():
            """Get current alerts."""
            # Placeholder - would integrate with AlertingSystem
            return jsonify({
                "active_alerts": [],
                "alert_history": []
            })
        
        @self.app.route('/api/health')
        def api_health():
            """Health check endpoint."""
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "monitor_active": self.monitor is not None
            })
    
    def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        if not hasattr(self.monitor, '_request_history'):
            return {
                "total_requests": 0,
                "avg_latency": 0,
                "total_cost": 0,
                "avg_quality": 0
            }
        
        history = self.monitor._request_history
        
        if not history:
            return {
                "total_requests": 0,
                "avg_latency": 0,
                "total_cost": 0,
                "avg_quality": 0
            }
        
        total_requests = len(history)
        
        latencies = [r.get("latency", 0) for r in history]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        costs = [r.get("cost", 0) for r in history]
        total_cost = sum(costs)
        
        qualities = [r.get("quality", {}).get("overall_score", 0) for r in history]
        avg_quality = sum(qualities) / len(qualities) if qualities else 0
        
        return {
            "total_requests": total_requests,
            "avg_latency": avg_latency,
            "total_cost": total_cost,
            "avg_quality": avg_quality,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _get_recent_requests(self, limit: int = 10) -> list:
        """Get recent requests."""
        if not hasattr(self.monitor, '_request_history'):
            return []
        
        history = self.monitor._request_history
        
        recent = history[-limit:] if len(history) > limit else history
        
        # Sanitize for JSON
        sanitized = []
        for req in recent:
            sanitized.append({
                "model": req.get("model", "unknown"),
                "latency": req.get("latency", 0),
                "cost": req.get("cost", 0),
                "tokens": req.get("tokens_used", {}),
                "timestamp": req.get("timestamp", "")
            })
        
        return sanitized
    
    def _get_model_breakdown(self) -> Dict[str, Any]:
        """Get metrics broken down by model."""
        if not hasattr(self.monitor, '_request_history'):
            return {}
        
        history = self.monitor._request_history
        
        model_stats = {}
        
        for req in history:
            model = req.get("model", "unknown")
            
            if model not in model_stats:
                model_stats[model] = {
                    "count": 0,
                    "total_cost": 0,
                    "total_latency": 0,
                    "total_tokens": 0
                }
            
            model_stats[model]["count"] += 1
            model_stats[model]["total_cost"] += req.get("cost", 0)
            model_stats[model]["total_latency"] += req.get("latency", 0)
            
            tokens = req.get("tokens_used", {})
            model_stats[model]["total_tokens"] += tokens.get("total_tokens", 0)
        
        # Calculate averages
        for model, stats in model_stats.items():
            count = stats["count"]
            stats["avg_cost"] = stats["total_cost"] / count
            stats["avg_latency"] = stats["total_latency"] / count
            stats["avg_tokens"] = stats["total_tokens"] / count
        
        return model_stats
    
    def _get_metrics_history(self, hours: int) -> Dict[str, Any]:
        """Get metrics for specified time period."""
        if not hasattr(self.monitor, '_request_history'):
            return {"data": []}
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        history = self.monitor._request_history
        
        # Filter by time
        filtered = [
            r for r in history
            if "timestamp" in r and 
            datetime.fromisoformat(r["timestamp"]) >= cutoff
        ]
        
        return {
            "period_hours": hours,
            "data_points": len(filtered),
            "data": filtered
        }
    
    def run(self):
        """Start the dashboard server."""
        print(f"🚀 Starting AI Monitor Dashboard at http://{self.host}:{self.port}")
        print(f"📊 API endpoints available at /api/*")
        
        self.app.run(
            host=self.host,
            port=self.port,
            debug=self.debug
        )


def create_dashboard(
    monitor=None,
    host: str = "localhost",
    port: int = 5000
) -> MonitoringDashboard:
    """
    Create and return a dashboard instance.
    
    Args:
        monitor: AIMonitor instance
        host: Host to bind to
        port: Port to listen on
        
    Returns:
        MonitoringDashboard instance
    """
    return MonitoringDashboard(monitor, host, port)
