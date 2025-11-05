#!/usr/bin/env python3
"""
Enhanced AI Quality Monitoring - Tracks hallucination, drift, and response quality
Implements AWS best practices for RAG hallucination detection
"""

import re
import json
import numpy as np
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import hashlib
import logging

logger = logging.getLogger(__name__)

class AIQualityAnalyzer:
    """Analyzes AI responses for quality, hallucination, and drift indicators"""
    
    def __init__(self):
        self.baseline_responses = {}  # Store baseline responses for drift detection
        self.quality_thresholds = {
            'min_response_length': 10,
            'max_response_length': 5000,
            'max_latency': 30.0,
            'confidence_threshold': 0.8
        }
        
        # AWS-recommended hallucination detection settings
        self.hallucination_config = {
            'token_similarity_threshold': 0.8,  # High score = likely hallucination
            'semantic_similarity_threshold': 0.6,  # High score = low similarity to context
            'enable_token_detector': True,  # Fast, free, 96% precision
            'enable_semantic_detector': True,  # For RAG with context
        }
        
        # Cache for embeddings client (lazy initialization)
        self._embeddings_client = None
    
    def analyze_response_quality(self, prompt: str, response: str, metadata: dict) -> Dict[str, Any]:
        """
        Comprehensive analysis of AI response quality
        Returns quality metrics including hallucination and drift indicators
        """
        analysis = {
            'quality_score': 0.0,
            'hallucination_risk': 'low',
            'drift_detected': False,
            'quality_issues': [],
            'metrics': {},
            'detection_method': 'pattern_based'  # Default
        }
        
        # 1. Basic Response Quality Checks
        basic_quality = self._analyze_basic_quality(prompt, response)
        analysis['metrics']['basic_quality'] = basic_quality
        
        # 2. Multi-Layer Hallucination Detection (AWS best practices)
        # Extract context from metadata if available (for RAG)
        context = None
        if metadata:
            context = metadata.get('context') or metadata.get('rag_context') or metadata.get('retrieval_context')
        
        # Use comprehensive detection if available, fallback to pattern-based
        try:
            hallucination_result = self.detect_hallucinations_comprehensive(
                prompt=prompt,
                response=response,
                context=context,
                metadata=metadata
            )
            analysis['hallucination_risk'] = hallucination_result['overall_risk_level']
            analysis['metrics']['hallucination'] = hallucination_result
            analysis['detection_method'] = hallucination_result.get('primary_method', 'multi_layer')
            analysis['hallucination_score'] = hallucination_result['overall_score']
        except Exception as e:
            # Fallback to simple pattern-based detection
            logger.debug(f"Comprehensive hallucination detection failed, using pattern-based: {e}")
            hallucination_risk = self._detect_hallucination_patterns(prompt, response)
            analysis['hallucination_risk'] = hallucination_risk['risk_level']
            analysis['metrics']['hallucination'] = hallucination_risk
            analysis['detection_method'] = 'pattern_based'
        
        # 3. Response Consistency & Drift Detection
        drift_analysis = self._analyze_response_drift(prompt, response)
        analysis['drift_detected'] = drift_analysis['drift_detected']
        analysis['metrics']['drift'] = drift_analysis
        
        # 4. Content Safety & Appropriateness
        safety_analysis = self._analyze_content_safety(response)
        analysis['metrics']['safety'] = safety_analysis
        
        # 5. Calculate Overall Quality Score
        analysis['quality_score'] = self._calculate_quality_score(analysis['metrics'])
        
        # 6. Identify Quality Issues
        analysis['quality_issues'] = self._identify_quality_issues(analysis['metrics'])
        
        return analysis
    
    def _analyze_basic_quality(self, prompt: str, response: str) -> Dict[str, Any]:
        """Basic quality metrics for AI responses"""
        return {
            'response_length': len(response),
            'prompt_length': len(prompt),
            'response_to_prompt_ratio': len(response) / max(len(prompt), 1),
            'has_structured_response': self._has_structured_content(response),
            'completeness': self._assess_completeness(prompt, response),
            'relevance_score': self._assess_relevance(prompt, response)
        }
    
    def _detect_hallucination_patterns(self, prompt: str, response: str) -> Dict[str, Any]:
        """Detect patterns that might indicate hallucination"""
        
        # Common hallucination indicators
        indicators = {
            'false_certainty': 0,  # "I'm 100% sure", "definitely", "always"
            'unsupported_facts': 0,  # Specific dates, numbers, names without context
            'contradictions': 0,    # Internal contradictions in response
            'off_topic': 0,        # Response doesn't address the prompt
            'fabricated_sources': 0 # Made-up citations, URLs, references
        }
        
        response_lower = response.lower()
        
        # 1. False Certainty Patterns
        certainty_patterns = [
            r'\b(100% (?:sure|certain|confident))\b',
            r'\b(definitely (?:always|never))\b',
            r'\b(impossible|guaranteed|absolutely certain)\b',
            r'\b(no doubt|without question|unquestionably)\b'
        ]
        for pattern in certainty_patterns:
            indicators['false_certainty'] += len(re.findall(pattern, response_lower))
        
        # 2. Unsupported Specific Claims
        specific_patterns = [
            r'\b(in \d{4})\b',  # Specific years
            r'\b(\d{1,3}%)\b',  # Specific percentages
            r'\b(exactly \d+)\b' # Exact numbers without context
        ]
        for pattern in specific_patterns:
            indicators['unsupported_facts'] += len(re.findall(pattern, response_lower))
        
        # 3. Fabricated Sources
        source_patterns = [
            r'https?://[^\s]+',  # URLs (could be made up)
            r'\(.*?\d{4}.*?\)',  # Citation format (Author, Year)
            r'according to [A-Z][a-z]+ [A-Z][a-z]+',  # "According to John Smith"
        ]
        for pattern in source_patterns:
            indicators['fabricated_sources'] += len(re.findall(pattern, response))
        
        # 4. Calculate Risk Level
        total_indicators = sum(indicators.values())
        if total_indicators >= 5:
            risk_level = 'high'
        elif total_indicators >= 2:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'risk_level': risk_level,
            'indicators': indicators,
            'total_risk_signals': total_indicators
        }
    
    def _detect_hallucination_token_similarity(
        self, 
        prompt: str, 
        response: str, 
        context: Optional[str] = None
    ) -> Dict[str, Union[float, str]]:
        """
        AWS Method 4: Token Similarity Detection
        
        Fast, free, high precision (96%) hallucination detector.
        Calculates token intersection and BLEU-like n-gram overlap.
        
        Returns:
            dict with 'intersection_score' and 'ngram_score' (0=factual, 1=hallucinated)
        """
        
        # Use context if available (RAG), otherwise use prompt
        reference_text = context if context else prompt
        
        if not reference_text or not response:
            return {'intersection_score': 0.0, 'ngram_score': 0.0, 'combined_score': 0.0}
        
        # Remove punctuation and lowercase
        ref_clean = re.sub(r'[^\w\s]', '', reference_text).lower()
        resp_clean = re.sub(r'[^\w\s]', '', response).lower()
        
        # Common stopwords to ignore
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        # Calculate token intersection (precision)
        ref_tokens = {word for word in ref_clean.split() if word not in stopwords and len(word) > 2}
        resp_tokens = {word for word in resp_clean.split() if word not in stopwords and len(word) > 2}
        
        if len(resp_tokens) == 0:
            return {'intersection_score': 0.0, 'ngram_score': 0.0, 'combined_score': 0.0}
        
        # Intersection score: how many response tokens appear in reference
        intersection = len(ref_tokens & resp_tokens) / len(resp_tokens)
        
        # Calculate n-gram overlap (similar to BLEU)
        ngram_scores = []
        for n in range(1, 4):  # Unigrams, bigrams, trigrams
            ref_ngrams = self._extract_ngrams(ref_clean.split(), n)
            resp_ngrams = self._extract_ngrams(resp_clean.split(), n)
            
            if len(resp_ngrams) > 0:
                ngram_overlap = len(ref_ngrams & resp_ngrams) / len(resp_ngrams)
                ngram_scores.append(ngram_overlap)
        
        avg_ngram_score = sum(ngram_scores) / len(ngram_scores) if ngram_scores else 0.0
        
        # Combined score (average)
        combined_score = (intersection + avg_ngram_score) / 2
        
        # Return hallucination scores (1 - similarity)
        return {
            'intersection_score': 1 - intersection,
            'ngram_score': 1 - avg_ngram_score,
            'combined_score': 1 - combined_score,
            'detection_method': 'token_similarity'
        }
    
    def _extract_ngrams(self, tokens: List[str], n: int) -> set:
        """Extract n-grams from token list"""
        ngrams = set()
        for i in range(len(tokens) - n + 1):
            ngram = ' '.join(tokens[i:i+n])
            ngrams.add(ngram)
        return ngrams
    
    def _detect_hallucination_semantic_similarity(
        self,
        context: str,
        response: str
    ) -> Dict[str, Union[float, str]]:
        """
        AWS Method 2: Semantic Similarity Detection
        
        Uses embeddings to calculate cosine similarity between context and response.
        High similarity = factual, low similarity = potential hallucination.
        
        Requires: Azure OpenAI embeddings API
        
        Returns:
            dict with 'similarity_score' (0=factual, 1=hallucinated)
        """
        
        if not context or not response:
            return {
                'similarity_score': 0.0, 
                'detection_method': 'semantic_similarity',
                'error': 'missing_context_or_response'
            }
        
        try:
            # Lazy initialization of embeddings client
            if self._embeddings_client is None:
                self._embeddings_client = self._initialize_embeddings_client()
            
            if self._embeddings_client is None:
                # Embeddings not available, return neutral score
                return {
                    'similarity_score': 0.5,
                    'detection_method': 'semantic_similarity',
                    'error': 'embeddings_unavailable'
                }
            
            # Get embeddings for context and response
            context_embedding = self._get_embedding(context)
            response_embedding = self._get_embedding(response)
            
            if context_embedding is None or response_embedding is None:
                return {
                    'similarity_score': 0.5,
                    'detection_method': 'semantic_similarity',
                    'error': 'embedding_failed'
                }
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(context_embedding, response_embedding)
            
            # Return hallucination score (1 - similarity)
            return {
                'similarity_score': 1 - similarity,
                'raw_similarity': similarity,
                'detection_method': 'semantic_similarity'
            }
            
        except Exception as e:
            logger.debug(f"Semantic similarity detection failed: {e}")
            return {
                'similarity_score': 0.5,
                'detection_method': 'semantic_similarity',
                'error': str(e)
            }
    
    def _initialize_embeddings_client(self):
        """Initialize Azure OpenAI embeddings client"""
        try:
            import os
            from openai import AzureOpenAI
            
            # Try to get Azure OpenAI credentials from environment
            api_key = os.getenv('AZURE_OPENAI_API_KEY')
            endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            
            if not api_key or not endpoint:
                logger.debug("Azure OpenAI credentials not found, semantic similarity disabled")
                return None
            
            client = AzureOpenAI(
                api_key=api_key,
                api_version="2024-02-15-preview",
                azure_endpoint=endpoint
            )
            
            return client
            
        except ImportError:
            logger.debug("OpenAI library not available, semantic similarity disabled")
            return None
        except Exception as e:
            logger.debug(f"Failed to initialize embeddings client: {e}")
            return None
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding vector for text"""
        try:
            if self._embeddings_client is None:
                return None
            
            # Truncate text if too long (max 8191 tokens for text-embedding-ada-002)
            if len(text) > 30000:  # Rough estimate: 4 chars per token
                text = text[:30000]
            
            response = self._embeddings_client.embeddings.create(
                input=text,
                model="text-embedding-ada-002"  # Or your deployed embedding model name
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.debug(f"Failed to get embedding: {e}")
            return None
    
    def _cosine_similarity(
        self, 
        vec1: List[float], 
        vec2: List[float]
    ) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            # Convert to numpy arrays
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            
            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0
            
            similarity = dot_product / (norm_v1 * norm_v2)
            
            # Ensure result is between 0 and 1
            return max(0.0, min(1.0, float(similarity)))
            
        except Exception as e:
            logger.debug(f"Cosine similarity calculation failed: {e}")
            return 0.0
    
    def detect_hallucinations_comprehensive(
        self,
        prompt: str,
        response: str,
        context: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Dict[str, Any]:
        """
        Multi-layer hallucination detection following AWS best practices.
        
        Implements cascading detection:
        1. Token Similarity (fast, free, 96% precision)
        2. Pattern-Based (our existing method)
        3. Semantic Similarity (if context available)
        
        Args:
            prompt: User's original question
            response: LLM's response
            context: RAG context (optional, improves accuracy)
            metadata: Additional metadata
            
        Returns:
            Comprehensive hallucination analysis with scores and risk level
        """
        
        results = {
            'overall_risk_level': 'low',
            'overall_score': 0.0,
            'detection_methods_used': [],
            'method_scores': {},
            'cost': 0  # Number of API calls
        }
        
        # Layer 1: Token Similarity (AWS recommended, free, fast)
        if self.hallucination_config.get('enable_token_detector', True):
            token_result = self._detect_hallucination_token_similarity(prompt, response, context)
            results['method_scores']['token_similarity'] = token_result
            results['detection_methods_used'].append('token_similarity')
            
            # If high hallucination score, can return early
            if token_result['combined_score'] > self.hallucination_config['token_similarity_threshold']:
                results['overall_risk_level'] = 'high'
                results['overall_score'] = token_result['combined_score']
                results['primary_method'] = 'token_similarity'
                return results
        
        # Layer 2: Pattern-Based Detection (existing method)
        pattern_result = self._detect_hallucination_patterns(prompt, response)
        results['method_scores']['pattern_based'] = pattern_result
        results['detection_methods_used'].append('pattern_based')
        
        # Layer 3: Semantic Similarity (if context available and enabled)
        if context and self.hallucination_config.get('enable_semantic_detector', True):
            semantic_result = self._detect_hallucination_semantic_similarity(context, response)
            results['method_scores']['semantic_similarity'] = semantic_result
            results['detection_methods_used'].append('semantic_similarity')
            
            # Count API cost (2 embedding calls)
            if 'error' not in semantic_result:
                results['cost'] = 2
        
        # Calculate overall score (weighted average)
        scores = []
        weights = []
        
        # Token similarity (weight: 0.4)
        if 'token_similarity' in results['method_scores']:
            scores.append(results['method_scores']['token_similarity']['combined_score'])
            weights.append(0.4)
        
        # Pattern-based (weight: 0.3)
        pattern_score = 0.0
        if pattern_result['risk_level'] == 'high':
            pattern_score = 0.8
        elif pattern_result['risk_level'] == 'medium':
            pattern_score = 0.5
        else:
            pattern_score = 0.2
        scores.append(pattern_score)
        weights.append(0.3)
        
        # Semantic similarity (weight: 0.3)
        if 'semantic_similarity' in results['method_scores']:
            sem_score = results['method_scores']['semantic_similarity'].get('similarity_score', 0.5)
            scores.append(sem_score)
            weights.append(0.3)
        
        # Calculate weighted average
        if scores and weights:
            results['overall_score'] = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        
        # Determine overall risk level
        if results['overall_score'] >= 0.7:
            results['overall_risk_level'] = 'high'
        elif results['overall_score'] >= 0.4:
            results['overall_risk_level'] = 'medium'
        else:
            results['overall_risk_level'] = 'low'
        
        results['primary_method'] = 'multi_layer'
        
        return results
    
    def _analyze_response_drift(self, prompt: str, response: str) -> Dict[str, Any]:
        """Detect if responses are drifting from expected patterns"""
        
        # Create a hash of the prompt to identify similar queries
        prompt_hash = hashlib.md5(prompt.lower().strip().encode()).hexdigest()[:8]
        
        # Get response characteristics
        current_characteristics = {
            'length': len(response),
            'structure_type': self._get_response_structure(response),
            'tone': self._analyze_tone(response),
            'complexity': self._assess_complexity(response)
        }
        
        drift_detected = False
        drift_magnitude = 0.0
        
        # Compare with baseline if we have previous responses for similar prompts
        if prompt_hash in self.baseline_responses:
            baseline = self.baseline_responses[prompt_hash]
            drift_magnitude = self._calculate_drift_magnitude(current_characteristics, baseline)
            drift_detected = drift_magnitude > 0.3  # 30% change threshold
        else:
            # Store as baseline for future comparisons
            self.baseline_responses[prompt_hash] = current_characteristics
        
        return {
            'drift_detected': drift_detected,
            'drift_magnitude': drift_magnitude,
            'current_characteristics': current_characteristics,
            'prompt_signature': prompt_hash
        }
    
    def _analyze_content_safety(self, response: str) -> Dict[str, Any]:
        """Analyze content for safety and appropriateness"""
        
        safety_flags = {
            'inappropriate_content': False,
            'potential_harm': False,
            'incomplete_response': False,
            'error_messages': False
        }
        
        response_lower = response.lower()
        
        # Check for incomplete responses
        incomplete_patterns = [
            r'i (?:cannot|can\'t|am unable)',
            r'(?:sorry|apologize).{0,20}(?:cannot|can\'t)',
            r'as an ai',
            r'i (?:don\'t|do not) have access'
        ]
        
        for pattern in incomplete_patterns:
            if re.search(pattern, response_lower):
                safety_flags['incomplete_response'] = True
                break
        
        # Check for error patterns
        error_patterns = [
            r'error|exception|failed',
            r'something went wrong',
            r'try again later'
        ]
        
        for pattern in error_patterns:
            if re.search(pattern, response_lower):
                safety_flags['error_messages'] = True
                break
        
        return safety_flags
    
    def _calculate_quality_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall quality score (0.0 to 1.0)"""
        
        score = 1.0
        
        # Deduct for quality issues
        basic = metrics.get('basic_quality', {})
        hallucination = metrics.get('hallucination', {})
        drift = metrics.get('drift', {})
        safety = metrics.get('safety', {})
        
        # Response length penalties
        length = basic.get('response_length', 0)
        if length < 10:
            score -= 0.3
        elif length > 5000:
            score -= 0.2
        
        # Hallucination penalties
        if hallucination.get('risk_level') == 'high':
            score -= 0.4
        elif hallucination.get('risk_level') == 'medium':
            score -= 0.2
        
        # Drift penalties
        if drift.get('drift_detected'):
            score -= min(0.3, drift.get('drift_magnitude', 0))
        
        # Safety penalties
        safety_issues = sum(1 for flag in safety.values() if flag)
        score -= safety_issues * 0.1
        
        return max(0.0, score)
    
    def _identify_quality_issues(self, metrics: Dict[str, Any]) -> List[str]:
        """Identify specific quality issues"""
        issues = []
        
        basic = metrics.get('basic_quality', {})
        hallucination = metrics.get('hallucination', {})
        drift = metrics.get('drift', {})
        safety = metrics.get('safety', {})
        
        # Check various issues
        if basic.get('response_length', 0) < 10:
            issues.append("Response too short")
        
        if basic.get('response_length', 0) > 5000:
            issues.append("Response too long")
        
        if hallucination.get('risk_level') in ['medium', 'high']:
            issues.append(f"Hallucination risk: {hallucination.get('risk_level')}")
        
        if drift.get('drift_detected'):
            issues.append("Response drift detected")
        
        if safety.get('incomplete_response'):
            issues.append("Incomplete or refusal response")
        
        if safety.get('error_messages'):
            issues.append("Contains error messages")
        
        return issues
    
    # Helper methods
    def _has_structured_content(self, text: str) -> bool:
        """Check if response has structured content (lists, headers, etc.)"""
        return bool(re.search(r'(\n-|\n\d+\.|\n#+|\n\*)', text))
    
    def _assess_completeness(self, prompt: str, response: str) -> float:
        """Assess if response completely addresses the prompt"""
        # Simple heuristic: response should be proportional to prompt complexity
        prompt_questions = len(re.findall(r'\?', prompt))
        response_sentences = len(re.findall(r'[.!?]', response))
        
        if prompt_questions == 0:
            return 0.8  # Default for statements
        
        return min(1.0, response_sentences / (prompt_questions * 2))
    
    def _assess_relevance(self, prompt: str, response: str) -> float:
        """Simple relevance assessment"""
        prompt_words = set(re.findall(r'\b\w+\b', prompt.lower()))
        response_words = set(re.findall(r'\b\w+\b', response.lower()))
        
        if not prompt_words:
            return 1.0
        
        overlap = len(prompt_words.intersection(response_words))
        return overlap / len(prompt_words)
    
    def _get_response_structure(self, response: str) -> str:
        """Categorize response structure type"""
        if re.search(r'\n#+', response):
            return 'formatted_with_headers'
        elif re.search(r'\n-|\n\*', response):
            return 'bulleted_list'
        elif re.search(r'\n\d+\.', response):
            return 'numbered_list'
        elif len(response.split('\n')) > 3:
            return 'multi_paragraph'
        else:
            return 'single_paragraph'
    
    def _analyze_tone(self, response: str) -> str:
        """Analyze response tone"""
        response_lower = response.lower()
        
        if any(word in response_lower for word in ['sorry', 'apologize', 'unfortunately']):
            return 'apologetic'
        elif any(word in response_lower for word in ['excellent', 'great', 'wonderful']):
            return 'positive'
        elif any(word in response_lower for word in ['however', 'but', 'although']):
            return 'balanced'
        else:
            return 'neutral'
    
    def _assess_complexity(self, response: str) -> float:
        """Assess response complexity"""
        sentences = re.findall(r'[.!?]', response)
        words = re.findall(r'\b\w+\b', response)
        
        if not sentences:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        return min(1.0, avg_sentence_length / 20)  # Normalize to 0-1
    
    def _calculate_drift_magnitude(self, current: dict, baseline: dict) -> float:
        """Calculate drift magnitude between current and baseline characteristics"""
        differences = []
        
        for key in ['length', 'complexity']:
            if key in current and key in baseline:
                curr_val = current[key]
                base_val = baseline[key]
                if base_val > 0:
                    diff = abs(curr_val - base_val) / base_val
                    differences.append(diff)
        
        return sum(differences) / len(differences) if differences else 0.0


# Integration with existing monitoring system
def enhance_llm_call_with_quality_analysis(llm_call_data: dict) -> dict:
    """Enhance LLM call data with quality analysis"""
    
    analyzer = AIQualityAnalyzer()
    
    # Extract data
    prompt = llm_call_data.get('prompt', '')
    response = llm_call_data.get('response', '')
    metadata = llm_call_data.get('metadata', {})
    
    # Perform quality analysis
    quality_analysis = analyzer.analyze_response_quality(prompt, response, metadata)
    
    # Add quality metrics to the LLM call data
    llm_call_data['quality_analysis'] = quality_analysis
    
    # Add quality flags for easy filtering
    llm_call_data['quality_score'] = quality_analysis['quality_score']
    llm_call_data['hallucination_risk'] = quality_analysis['hallucination_risk']
    llm_call_data['drift_detected'] = quality_analysis['drift_detected']
    llm_call_data['quality_issues'] = quality_analysis['quality_issues']
    
    return llm_call_data
