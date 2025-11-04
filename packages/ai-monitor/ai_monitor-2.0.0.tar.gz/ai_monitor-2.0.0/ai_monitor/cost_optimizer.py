"""
Cost optimization and budget management for AI/LLM monitoring.

Provides budget tracking, cost analysis, and optimization recommendations
to help manage AI/LLM API costs effectively.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics


class CostOptimizer:
    """
    Analyzes AI/LLM usage patterns and provides cost optimization recommendations.
    
    Features:
    - Budget tracking and alerts
    - Cost trend analysis
    - Model recommendation based on cost/performance
    - Caching opportunity identification
    - Prompt optimization suggestions
    """
    
    # Model pricing (per 1K tokens) - Updated with Azure OpenAI pricing
    MODEL_PRICING = {
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-4.1": {"prompt": 0.03, "completion": 0.06},  # Azure OpenAI GPT-4.1
        "gpt-4-32k": {"prompt": 0.06, "completion": 0.12},
        "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
        "gpt-4o": {"prompt": 0.005, "completion": 0.015},
        "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
        "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
        "gpt-3.5-turbo-16k": {"prompt": 0.003, "completion": 0.004},
        "text-embedding-ada-002": {"prompt": 0.0001, "completion": 0.0001},
    }
    
    def __init__(
        self,
        daily_budget: Optional[float] = None,
        monthly_budget: Optional[float] = None,
        alert_threshold: float = 0.8
    ):
        """
        Initialize cost optimizer.
        
        Args:
            daily_budget: Daily spending limit in USD
            monthly_budget: Monthly spending limit in USD
            alert_threshold: Alert when spending reaches this fraction of budget
        """
        self.daily_budget = daily_budget
        self.monthly_budget = monthly_budget
        self.alert_threshold = alert_threshold
        
        # Cost tracking
        self._request_costs: deque = deque(maxlen=10000)
        self._daily_costs: Dict[str, float] = {}
        self._monthly_costs: Dict[str, float] = {}
        
        # Usage patterns
        self._model_usage: Dict[str, List[Dict]] = defaultdict(list)
        self._prompt_patterns: Dict[int, int] = defaultdict(int)
        
        # Caching analysis
        self._similar_prompts: Dict[int, List[Tuple[str, str]]] = defaultdict(list)
        
        # Alerts
        self._budget_alerts: List[Dict] = []
    
    def track_request_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency: float,
        response_quality: Optional[float] = None,
        prompt: Optional[str] = None,
        response: Optional[str] = None
    ) -> float:
        """
        Track cost of a single request.
        
        Args:
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            latency: Response latency in seconds
            response_quality: Quality score (0-100)
            prompt: Prompt text (for caching analysis)
            response: Response text
            
        Returns:
            Cost in USD
        """
        cost = self.calculate_cost(model, prompt_tokens, completion_tokens)
        
        request_data = {
            "model": model,
            "cost": cost,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "latency": latency,
            "quality": response_quality,
            "timestamp": datetime.utcnow(),
            "date": datetime.utcnow().date().isoformat(),
            "month": datetime.utcnow().strftime("%Y-%m"),
        }
        
        if prompt:
            request_data["prompt"] = prompt
            request_data["prompt_hash"] = hash(prompt)
        
        if response:
            request_data["response"] = response
        
        # Store request
        self._request_costs.append(request_data)
        
        # Update daily/monthly totals
        date_key = request_data["date"]
        month_key = request_data["month"]
        
        self._daily_costs[date_key] = self._daily_costs.get(date_key, 0) + cost
        self._monthly_costs[month_key] = self._monthly_costs.get(month_key, 0) + cost
        
        # Track model usage
        self._model_usage[model].append(request_data)
        
        # Analyze for caching opportunities
        if prompt:
            self._analyze_prompt_similarity(prompt, response or "")
        
        # Check budget alerts
        self._check_budget_alerts()
        
        return cost
    
    @staticmethod
    def calculate_cost(
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Calculate cost for a request.
        
        Args:
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Cost in USD
        """
        pricing = CostOptimizer.MODEL_PRICING.get(
            model,
            {"prompt": 0.002, "completion": 0.002}  # default
        )
        
        prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing["completion"]
        
        return prompt_cost + completion_cost
    
    def get_daily_cost(self, date: Optional[str] = None) -> float:
        """
        Get cost for a specific day.
        
        Args:
            date: Date string (YYYY-MM-DD), defaults to today
            
        Returns:
            Total cost for the day
        """
        if date is None:
            date = datetime.utcnow().date().isoformat()
        
        return self._daily_costs.get(date, 0.0)
    
    def get_monthly_cost(self, month: Optional[str] = None) -> float:
        """
        Get cost for a specific month.
        
        Args:
            month: Month string (YYYY-MM), defaults to current month
            
        Returns:
            Total cost for the month
        """
        if month is None:
            month = datetime.utcnow().strftime("%Y-%m")
        
        return self._monthly_costs.get(month, 0.0)
    
    def _check_budget_alerts(self):
        """Check if spending is approaching budget limits."""
        alerts = []
        
        # Check daily budget
        if self.daily_budget:
            daily_cost = self.get_daily_cost()
            daily_pct = daily_cost / self.daily_budget
            
            if daily_pct >= self.alert_threshold:
                alerts.append({
                    "type": "daily_budget",
                    "current": daily_cost,
                    "budget": self.daily_budget,
                    "percentage": daily_pct * 100,
                    "message": f"Daily spending at {daily_pct*100:.1f}% of budget"
                })
        
        # Check monthly budget
        if self.monthly_budget:
            monthly_cost = self.get_monthly_cost()
            monthly_pct = monthly_cost / self.monthly_budget
            
            if monthly_pct >= self.alert_threshold:
                alerts.append({
                    "type": "monthly_budget",
                    "current": monthly_cost,
                    "budget": self.monthly_budget,
                    "percentage": monthly_pct * 100,
                    "message": f"Monthly spending at {monthly_pct*100:.1f}% of budget"
                })
        
        if alerts:
            self._budget_alerts.extend(alerts)
    
    def get_budget_status(self) -> Dict[str, Any]:
        """
        Get current budget status.
        
        Returns:
            Dictionary with budget information
        """
        status = {}
        
        if self.daily_budget:
            daily_cost = self.get_daily_cost()
            status["daily"] = {
                "budget": self.daily_budget,
                "spent": daily_cost,
                "remaining": self.daily_budget - daily_cost,
                "percentage": (daily_cost / self.daily_budget) * 100,
                "over_budget": daily_cost > self.daily_budget
            }
        
        if self.monthly_budget:
            monthly_cost = self.get_monthly_cost()
            status["monthly"] = {
                "budget": self.monthly_budget,
                "spent": monthly_cost,
                "remaining": self.monthly_budget - monthly_cost,
                "percentage": (monthly_cost / self.monthly_budget) * 100,
                "over_budget": monthly_cost > self.monthly_budget
            }
        
        status["recent_alerts"] = self._budget_alerts[-10:]
        
        return status
    
    def suggest_optimizations(self) -> Dict[str, Any]:
        """
        Analyze usage and suggest cost optimizations.
        
        Returns:
            Dictionary with optimization recommendations
        """
        suggestions = {
            "model_alternatives": self._suggest_cheaper_models(),
            "caching_opportunities": self._identify_caching_opportunities(),
            "prompt_optimizations": self._suggest_prompt_optimizations(),
            "usage_patterns": self._analyze_usage_patterns(),
            "estimated_savings": 0.0
        }
        
        # Calculate total potential savings
        total_savings = 0.0
        
        for alt in suggestions["model_alternatives"]:
            total_savings += alt.get("potential_savings", 0)
        
        for cache in suggestions["caching_opportunities"]:
            total_savings += cache.get("potential_savings", 0)
        
        suggestions["estimated_savings"] = total_savings
        
        return suggestions
    
    def _suggest_cheaper_models(self) -> List[Dict[str, Any]]:
        """Suggest cheaper model alternatives based on usage patterns."""
        suggestions = []
        
        for model, requests in self._model_usage.items():
            if not requests:
                continue
            
            # Calculate average quality and cost
            avg_quality = statistics.mean([
                r.get("quality", 0) for r in requests if r.get("quality")
            ]) if any(r.get("quality") for r in requests) else None
            
            total_cost = sum(r["cost"] for r in requests)
            
            # Find cheaper alternatives
            current_pricing = self.MODEL_PRICING.get(model, {})
            
            for alt_model, alt_pricing in self.MODEL_PRICING.items():
                if alt_model == model:
                    continue
                
                # Only suggest if significantly cheaper
                if alt_pricing["completion"] < current_pricing.get("completion", 999) * 0.7:
                    # Estimate savings
                    avg_completion_tokens = statistics.mean([
                        r["completion_tokens"] for r in requests
                    ])
                    
                    cost_diff_per_1k = (
                        current_pricing.get("completion", 0) - alt_pricing["completion"]
                    )
                    
                    potential_savings = (
                        cost_diff_per_1k * avg_completion_tokens / 1000 * len(requests)
                    )
                    
                    suggestions.append({
                        "current_model": model,
                        "suggested_model": alt_model,
                        "current_cost": total_cost,
                        "potential_savings": potential_savings,
                        "requests_analyzed": len(requests),
                        "note": "Consider testing if cheaper model maintains quality"
                    })
        
        return suggestions
    
    def _identify_caching_opportunities(self) -> List[Dict[str, Any]]:
        """Identify requests that could benefit from caching."""
        opportunities = []
        
        # Find similar/duplicate prompts
        prompt_counts = defaultdict(int)
        
        for request in self._request_costs:
            if "prompt_hash" in request:
                prompt_counts[request["prompt_hash"]] += 1
        
        # Find prompts that appear multiple times
        for prompt_hash, count in prompt_counts.items():
            if count > 1:
                # Find requests with this prompt
                matching_requests = [
                    r for r in self._request_costs
                    if r.get("prompt_hash") == prompt_hash
                ]
                
                if matching_requests:
                    total_cost = sum(r["cost"] for r in matching_requests)
                    # Savings = all but first request
                    potential_savings = sum(r["cost"] for r in matching_requests[1:])
                    
                    opportunities.append({
                        "duplicate_count": count,
                        "total_cost": total_cost,
                        "potential_savings": potential_savings,
                        "sample_prompt": matching_requests[0].get("prompt", "")[:100] + "...",
                        "recommendation": "Implement response caching for this prompt pattern"
                    })
        
        return sorted(opportunities, key=lambda x: x["potential_savings"], reverse=True)[:10]
    
    def _suggest_prompt_optimizations(self) -> List[Dict[str, Any]]:
        """Suggest ways to optimize prompts to reduce token usage."""
        suggestions = []
        
        for request in self._request_costs:
            if "prompt" not in request:
                continue
            
            prompt = request["prompt"]
            prompt_tokens = request["prompt_tokens"]
            
            # Check for very long prompts
            if prompt_tokens > 1000:
                suggestions.append({
                    "issue": "long_prompt",
                    "prompt_tokens": prompt_tokens,
                    "cost_per_request": request["cost"],
                    "recommendation": "Consider condensing prompt or using smaller context window",
                    "potential_savings_per_request": request["cost"] * 0.3  # Estimate 30% reduction
                })
        
        return suggestions[:10]
    
    def _analyze_usage_patterns(self) -> Dict[str, Any]:
        """Analyze usage patterns for insights."""
        if not self._request_costs:
            return {}
        
        # Time-based analysis
        hourly_usage = defaultdict(float)
        for request in self._request_costs:
            hour = request["timestamp"].hour
            hourly_usage[hour] += request["cost"]
        
        # Model distribution
        model_costs = defaultdict(float)
        for request in self._request_costs:
            model_costs[request["model"]] += request["cost"]
        
        total_cost = sum(self._daily_costs.values())
        
        return {
            "total_requests": len(self._request_costs),
            "total_cost": total_cost,
            "avg_cost_per_request": total_cost / len(self._request_costs) if self._request_costs else 0,
            "model_distribution": dict(model_costs),
            "peak_hour": max(hourly_usage.items(), key=lambda x: x[1])[0] if hourly_usage else None,
            "hourly_costs": dict(hourly_usage)
        }
    
    def _analyze_prompt_similarity(self, prompt: str, response: str):
        """Analyze prompt for similarity with previous prompts."""
        # Simple hash-based similarity
        prompt_hash = hash(prompt)
        self._prompt_patterns[prompt_hash] += 1
        
        # Store for caching analysis
        if self._prompt_patterns[prompt_hash] > 1:
            self._similar_prompts[prompt_hash].append((prompt, response))
    
    def get_cost_report(self, days: int = 7) -> Dict[str, Any]:
        """
        Generate cost report for specified period.
        
        Args:
            days: Number of days to include in report
            
        Returns:
            Dictionary with cost report data
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        recent_requests = [
            r for r in self._request_costs
            if r["timestamp"] >= cutoff_date
        ]
        
        if not recent_requests:
            return {"error": "No data for specified period"}
        
        total_cost = sum(r["cost"] for r in recent_requests)
        total_tokens = sum(r["total_tokens"] for r in recent_requests)
        
        # Daily breakdown
        daily_breakdown = defaultdict(lambda: {"cost": 0.0, "requests": 0, "tokens": 0})
        
        for r in recent_requests:
            date = r["date"]
            daily_breakdown[date]["cost"] += r["cost"]
            daily_breakdown[date]["requests"] += 1
            daily_breakdown[date]["tokens"] += r["total_tokens"]
        
        return {
            "period_days": days,
            "total_cost": total_cost,
            "total_requests": len(recent_requests),
            "total_tokens": total_tokens,
            "avg_cost_per_request": total_cost / len(recent_requests),
            "avg_cost_per_day": total_cost / days,
            "daily_breakdown": dict(daily_breakdown),
            "projection_monthly": (total_cost / days) * 30,
        }
