"""
Security and compliance metrics for AI/LLM monitoring.

Provides PII detection, content moderation, and compliance tracking
to ensure safe and compliant AI usage.
"""

import re
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
from collections import defaultdict


class SecurityMetrics:
    """
    Tracks security and compliance metrics for AI/LLM usage.
    
    Features:
    - PII detection and classification
    - Content moderation and toxicity detection
    - Compliance tracking (GDPR, data retention)
    - Authentication and authorization monitoring
    """
    
    # Common PII patterns
    PII_PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        "ip_address": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        "url": r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)',
    }
    
    # Toxic keywords (simplified - should use proper model in production)
    TOXIC_KEYWORDS = {
        "hate_speech", "profanity", "violence", "harassment", "discrimination"
    }
    
    def __init__(
        self,
        enable_pii_detection: bool = True,
        enable_content_moderation: bool = True,
        pii_redaction: bool = False
    ):
        """
        Initialize security metrics tracker.
        
        Args:
            enable_pii_detection: Enable PII detection
            enable_content_moderation: Enable content moderation
            pii_redaction: Automatically redact detected PII
        """
        self.enable_pii_detection = enable_pii_detection
        self.enable_content_moderation = enable_content_moderation
        self.pii_redaction = pii_redaction
        
        # Metrics tracking
        self._pii_detections: List[Dict] = []
        self._moderation_flags: List[Dict] = []
        self._auth_events: List[Dict] = []
        self._gdpr_requests: List[Dict] = []
        
        # Counters
        self._pii_counts = defaultdict(int)
        self._toxicity_counts = defaultdict(int)
        self._auth_failures = 0
    
    def analyze_request(
        self,
        prompt: str,
        response: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze request for security and compliance issues.
        
        Args:
            prompt: User prompt
            response: AI response
            user_id: Optional user identifier
            metadata: Optional request metadata
            
        Returns:
            Dictionary with security analysis results
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "has_pii": False,
            "has_toxic_content": False,
            "pii_types": [],
            "moderation_flags": [],
        }
        
        # PII detection
        if self.enable_pii_detection:
            pii_results = self._detect_pii(prompt, response)
            results["has_pii"] = pii_results["detected"]
            results["pii_types"] = pii_results["types"]
            results["pii_details"] = pii_results["details"]
            
            if pii_results["detected"]:
                self._record_pii_detection(pii_results, user_id)
        
        # Content moderation
        if self.enable_content_moderation:
            moderation_results = self._moderate_content(prompt, response)
            results["has_toxic_content"] = moderation_results["flagged"]
            results["moderation_flags"] = moderation_results["flags"]
            results["toxicity_score"] = moderation_results["score"]
            
            if moderation_results["flagged"]:
                self._record_moderation_flag(moderation_results, user_id)
        
        return results
    
    def _detect_pii(self, prompt: str, response: str) -> Dict[str, Any]:
        """
        Detect PII in text.
        
        Args:
            prompt: Prompt text
            response: Response text
            
        Returns:
            Dictionary with PII detection results
        """
        detected_types: Set[str] = set()
        details: List[Dict] = []
        
        combined_text = f"{prompt} {response}"
        
        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = re.finditer(pattern, combined_text)
            
            for match in matches:
                detected_types.add(pii_type)
                details.append({
                    "type": pii_type,
                    "value": match.group() if not self.pii_redaction else "[REDACTED]",
                    "position": match.span()
                })
                
                self._pii_counts[pii_type] += 1
        
        return {
            "detected": len(detected_types) > 0,
            "types": list(detected_types),
            "details": details,
            "count": len(details)
        }
    
    def _moderate_content(self, prompt: str, response: str) -> Dict[str, Any]:
        """
        Moderate content for toxicity.
        
        Note: This is a simplified implementation.
        In production, use proper ML models like Perspective API or similar.
        
        Args:
            prompt: Prompt text
            response: Response text
            
        Returns:
            Dictionary with moderation results
        """
        flags: List[str] = []
        combined_text = f"{prompt} {response}".lower()
        
        # Simple keyword-based detection (should use ML model)
        toxic_keywords = {
            "hate": ["hate", "racist", "sexist"],
            "violence": ["kill", "murder", "attack"],
            "harassment": ["harass", "bully", "threaten"],
        }
        
        for category, keywords in toxic_keywords.items():
            for keyword in keywords:
                if keyword in combined_text:
                    flags.append(category)
                    self._toxicity_counts[category] += 1
                    break
        
        # Calculate simple toxicity score
        score = min(len(flags) * 0.3, 1.0)
        
        return {
            "flagged": len(flags) > 0,
            "flags": list(set(flags)),
            "score": score
        }
    
    def _record_pii_detection(self, pii_results: Dict, user_id: Optional[str]):
        """Record PII detection event."""
        self._pii_detections.append({
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "types": pii_results["types"],
            "count": pii_results["count"]
        })
    
    def _record_moderation_flag(self, moderation_results: Dict, user_id: Optional[str]):
        """Record content moderation flag."""
        self._moderation_flags.append({
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "flags": moderation_results["flags"],
            "score": moderation_results["score"]
        })
    
    def redact_pii(self, text: str) -> str:
        """
        Redact PII from text.
        
        Args:
            text: Text to redact
            
        Returns:
            Text with PII redacted
        """
        redacted = text
        
        for pii_type, pattern in self.PII_PATTERNS.items():
            redacted = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", redacted)
        
        return redacted
    
    def track_auth_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        success: bool = True,
        metadata: Optional[Dict] = None
    ):
        """
        Track authentication/authorization event.
        
        Args:
            event_type: Type of auth event (login, token_refresh, etc.)
            user_id: User identifier
            success: Whether event succeeded
            metadata: Additional metadata
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "success": success,
            "metadata": metadata or {}
        }
        
        self._auth_events.append(event)
        
        if not success:
            self._auth_failures += 1
    
    def track_gdpr_request(
        self,
        request_type: str,
        user_id: str,
        status: str = "pending"
    ):
        """
        Track GDPR data request.
        
        Args:
            request_type: Type of request (access, deletion, portability)
            user_id: User identifier
            status: Request status
        """
        self._gdpr_requests.append({
            "timestamp": datetime.utcnow().isoformat(),
            "request_type": request_type,
            "user_id": user_id,
            "status": status
        })
    
    def get_pii_metrics(self) -> Dict[str, Any]:
        """
        Get PII detection metrics.
        
        Returns:
            Dictionary with PII metrics
        """
        return {
            "total_detections": len(self._pii_detections),
            "detections_by_type": dict(self._pii_counts),
            "recent_detections": self._pii_detections[-10:],
            "unique_users_with_pii": len(set(
                d["user_id"] for d in self._pii_detections if d.get("user_id")
            ))
        }
    
    def get_moderation_metrics(self) -> Dict[str, Any]:
        """
        Get content moderation metrics.
        
        Returns:
            Dictionary with moderation metrics
        """
        total_requests = len(self._moderation_flags)
        
        if total_requests > 0:
            toxicity_rate = len(self._moderation_flags) / total_requests
        else:
            toxicity_rate = 0.0
        
        return {
            "total_flags": len(self._moderation_flags),
            "flags_by_type": dict(self._toxicity_counts),
            "toxicity_rate": toxicity_rate,
            "recent_flags": self._moderation_flags[-10:]
        }
    
    def get_auth_metrics(self) -> Dict[str, Any]:
        """
        Get authentication/authorization metrics.
        
        Returns:
            Dictionary with auth metrics
        """
        total_events = len(self._auth_events)
        success_events = sum(1 for e in self._auth_events if e["success"])
        
        return {
            "total_auth_events": total_events,
            "successful_events": success_events,
            "failed_events": self._auth_failures,
            "success_rate": success_events / total_events if total_events > 0 else 0,
            "recent_events": self._auth_events[-10:]
        }
    
    def get_compliance_metrics(self) -> Dict[str, Any]:
        """
        Get compliance metrics.
        
        Returns:
            Dictionary with compliance metrics
        """
        gdpr_by_type = defaultdict(int)
        for req in self._gdpr_requests:
            gdpr_by_type[req["request_type"]] += 1
        
        return {
            "total_gdpr_requests": len(self._gdpr_requests),
            "requests_by_type": dict(gdpr_by_type),
            "recent_requests": self._gdpr_requests[-10:],
            "pii_detection_enabled": self.enable_pii_detection,
            "content_moderation_enabled": self.enable_content_moderation,
            "pii_redaction_enabled": self.pii_redaction
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all security and compliance metrics.
        
        Returns:
            Dictionary with all metrics
        """
        return {
            "pii": self.get_pii_metrics(),
            "moderation": self.get_moderation_metrics(),
            "authentication": self.get_auth_metrics(),
            "compliance": self.get_compliance_metrics()
        }
    
    def reset_metrics(self):
        """Reset all metrics."""
        self._pii_detections.clear()
        self._moderation_flags.clear()
        self._auth_events.clear()
        self._gdpr_requests.clear()
        self._pii_counts.clear()
        self._toxicity_counts.clear()
        self._auth_failures = 0
