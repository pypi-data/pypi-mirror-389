"""
Semantic analysis for AI/LLM responses.

Provides semantic similarity, relevance scoring, and topic analysis
using lightweight TF-IDF vectorization (NO TORCH DEPENDENCY!).

This implementation uses scikit-learn's TF-IDF for fast, memory-efficient
semantic analysis without requiring 500MB+ transformer models.
"""

from typing import Dict, List, Optional, Any, Tuple
import re
import numpy as np


class SemanticAnalyzer:
    """
    Analyzes semantic quality of AI/LLM responses using lightweight TF-IDF.
    
    Features:
    - Semantic similarity between prompt and response (TF-IDF + cosine)
    - Topic coherence analysis
    - Context preservation checking
    - Lightweight embeddings (~30MB vs 500MB+ for transformers)
    - Fast initialization (<1 second vs 10+ seconds for transformers)
    
    Note: Uses scikit-learn for TF-IDF vectorization.
    For advanced transformer-based analysis, install sentence-transformers separately.
    """
    
    def __init__(
        self,
        max_features: int = 5000,
        enable_caching: bool = True,
        use_transformers: bool = False
    ):
        """
        Initialize semantic analyzer.
        
        Args:
            max_features: Maximum vocabulary size for TF-IDF (default: 5000)
            enable_caching: Cache vectors for repeated texts
            use_transformers: Use sentence-transformers if available (default: False)
        """
        self.max_features = max_features
        self.enable_caching = enable_caching
        self.use_transformers = use_transformers
        
        self._vectorizer = None
        self._transformer_model = None
        self._vector_cache: Dict[str, np.ndarray] = {}
        self._corpus: List[str] = []  # For fitting vectorizer
        
    def _get_vectorizer(self):
        """Lazy load and fit the TF-IDF vectorizer."""
        if self._vectorizer is None:
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                self._vectorizer = TfidfVectorizer(
                    max_features=self.max_features,
                    stop_words='english',
                    ngram_range=(1, 2),  # Unigrams and bigrams
                    min_df=1,
                    lowercase=True
                )
            except ImportError:
                raise ImportError(
                    "scikit-learn is required for semantic analysis. "
                    "Install with: pip install scikit-learn scipy"
                )
        return self._vectorizer
    
    def _get_transformer_model(self):
        """Lazy load transformer model if requested and available."""
        if self._transformer_model is None and self.use_transformers:
            try:
                from sentence_transformers import SentenceTransformer
                self._transformer_model = SentenceTransformer("all-MiniLM-L6-v2")
            except ImportError:
                # Fallback to TF-IDF silently
                self.use_transformers = False
        return self._transformer_model
    
    def _get_vector(self, text: str) -> np.ndarray:
        """
        Get vector representation for text with caching.
        
        Args:
            text: Text to vectorize
            
        Returns:
            Vector representation
        """
        # Check cache
        if self.enable_caching and text in self._vector_cache:
            return self._vector_cache[text]
        
        # Use transformers if available
        if self.use_transformers:
            model = self._get_transformer_model()
            if model is not None:
                vector = model.encode(text, convert_to_numpy=True)
                if self.enable_caching:
                    self._vector_cache[text] = vector
                return vector
        
        # Use TF-IDF (lightweight)
        vectorizer = self._get_vectorizer()
        
        # Add to corpus if not already fitted
        if text not in self._corpus:
            self._corpus.append(text)
            # Refit vectorizer with updated corpus
            try:
                vectorizer.fit(self._corpus)
            except Exception:
                # If fitting fails, use simple word overlap
                return self._simple_vector(text)
        
        # Transform text
        try:
            vector = vectorizer.transform([text]).toarray()[0]
        except Exception:
            # Fallback to simple vector
            vector = self._simple_vector(text)
        
        # Cache if enabled
        if self.enable_caching:
            self._vector_cache[text] = vector
        
        return vector
    
    def _simple_vector(self, text: str) -> np.ndarray:
        """
        Fallback to simple word-based vector if TF-IDF fails.
        
        Args:
            text: Text to vectorize
            
        Returns:
            Simple word frequency vector
        """
        words = text.lower().split()
        # Create a simple binary vector
        return np.array([1.0] * min(len(words), 100) + [0.0] * max(0, 100 - len(words)))
    
    def analyze_semantic_quality(
        self,
        prompt: str,
        response: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive semantic quality analysis.
        
        Args:
            prompt: Input prompt
            response: Model response
            context: Optional additional context
            
        Returns:
            Dictionary with semantic quality metrics
        """
        metrics = {}
        
        # Semantic similarity
        metrics["semantic_similarity"] = self.calculate_similarity(prompt, response)
        
        # Topic coherence
        metrics["topic_coherence"] = self.measure_coherence(response)
        
        # Context preservation
        if context:
            metrics["context_preservation"] = self.check_context_preservation(
                context, prompt, response
            )
        
        # Relevance score (0-100)
        metrics["relevance_score"] = self._calculate_relevance_score(metrics)
        
        return metrics
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            
            vector1 = self._get_vector(text1)
            vector2 = self._get_vector(text2)
            
            # Ensure vectors are 2D for sklearn
            if len(vector1.shape) == 1:
                vector1 = vector1.reshape(1, -1)
            if len(vector2.shape) == 1:
                vector2 = vector2.reshape(1, -1)
            
            # Pad vectors to same length if needed
            if vector1.shape[1] != vector2.shape[1]:
                max_len = max(vector1.shape[1], vector2.shape[1])
                if vector1.shape[1] < max_len:
                    vector1 = np.pad(vector1, ((0, 0), (0, max_len - vector1.shape[1])))
                if vector2.shape[1] < max_len:
                    vector2 = np.pad(vector2, ((0, 0), (0, max_len - vector2.shape[1])))
            
            # Cosine similarity
            similarity = cosine_similarity(vector1, vector2)[0][0]
            
            return float(max(0.0, min(1.0, similarity)))  # Clamp to [0, 1]
            
        except Exception:
            # Fallback to simple word overlap
            return self._simple_similarity(text1, text2)
    
    def _simple_similarity(self, text1: str, text2: str) -> float:
        """
        Fallback similarity using word overlap.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def measure_coherence(self, text: str) -> float:
        """
        Measure internal coherence of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Coherence score (0-1)
        """
        # Split into sentences
        sentences = self._split_sentences(text)
        
        if len(sentences) < 2:
            return 1.0  # Single sentence is coherent by default
        
        # Calculate pairwise similarities
        similarities = []
        
        for i in range(len(sentences) - 1):
            sim = self.calculate_similarity(sentences[i], sentences[i + 1])
            similarities.append(sim)
        
        # Average similarity indicates coherence
        if similarities:
            return float(np.mean(similarities))
        
        return 1.0
    
    def check_context_preservation(
        self,
        context: str,
        prompt: str,
        response: str
    ) -> float:
        """
        Check if response preserves context.
        
        Args:
            context: Original context
            prompt: User prompt
            response: Model response
            
        Returns:
            Context preservation score (0-1)
        """
        # Combine context and prompt
        full_context = f"{context} {prompt}"
        
        # Calculate similarity with response
        preservation_score = self.calculate_similarity(full_context, response)
        
        return preservation_score
    
    def find_similar_responses(
        self,
        response: str,
        candidate_responses: List[str],
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Find most similar responses from candidates.
        
        Args:
            response: Target response
            candidate_responses: List of candidate responses
            top_k: Number of top matches to return
            
        Returns:
            List of (response, similarity_score) tuples
        """
        similarities = []
        
        for candidate in candidate_responses:
            sim = self.calculate_similarity(response, candidate)
            similarities.append((candidate, float(sim)))
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def detect_topic_shift(
        self,
        conversation_history: List[str],
        threshold: float = 0.5
    ) -> List[int]:
        """
        Detect topic shifts in conversation.
        
        Args:
            conversation_history: List of messages in order
            threshold: Similarity threshold for topic shift
            
        Returns:
            List of indices where topic shifts occur
        """
        if len(conversation_history) < 2:
            return []
        
        shift_indices = []
        
        for i in range(len(conversation_history) - 1):
            sim = self.calculate_similarity(
                conversation_history[i],
                conversation_history[i + 1]
            )
            
            if sim < threshold:
                shift_indices.append(i + 1)
        
        return shift_indices
    
    def extract_key_topics(
        self,
        text: str,
        num_topics: int = 5
    ) -> List[str]:
        """
        Extract key topics/themes from text using sentence centrality.
        
        Args:
            text: Text to analyze
            num_topics: Number of topics to extract
            
        Returns:
            List of representative sentences/topics
        """
        sentences = self._split_sentences(text)
        
        if not sentences:
            return []
        
        if len(sentences) <= num_topics:
            return sentences
        
        # Calculate centrality of each sentence
        centrality = []
        
        for i, sent in enumerate(sentences):
            # Calculate average similarity with all other sentences
            sims = []
            for j, other in enumerate(sentences):
                if i != j:
                    sim = self.calculate_similarity(sent, other)
                    sims.append(sim)
            
            avg_sim = np.mean(sims) if sims else 0
            centrality.append((sent, avg_sim))
        
        # Return top central sentences as topics
        centrality.sort(key=lambda x: x[1], reverse=True)
        
        return [sent for sent, _ in centrality[:num_topics]]
    
    def _calculate_relevance_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate overall relevance score from semantic metrics.
        
        Args:
            metrics: Dictionary with semantic metrics
            
        Returns:
            Relevance score (0-100)
        """
        # Weighted average of available metrics
        score = 0.0
        weight_sum = 0.0
        
        if "semantic_similarity" in metrics:
            score += metrics["semantic_similarity"] * 50
            weight_sum += 50
        
        if "topic_coherence" in metrics:
            score += metrics["topic_coherence"] * 30
            weight_sum += 30
        
        if "context_preservation" in metrics:
            score += metrics["context_preservation"] * 20
            weight_sum += 20
        
        if weight_sum > 0:
            return (score / weight_sum) * 100
        
        return 0.0
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting
        # Can be enhanced with proper NLP library
        import re
        
        # Split on sentence boundaries
        sentences = re.split(r'[.!?]+', text)
        
        # Clean and filter
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def batch_analyze(
        self,
        prompt_response_pairs: List[Tuple[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple prompt-response pairs efficiently.
        
        Args:
            prompt_response_pairs: List of (prompt, response) tuples
            
        Returns:
            List of analysis results
        """
        results = []
        
        for prompt, response in prompt_response_pairs:
            analysis = self.analyze_semantic_quality(prompt, response)
            results.append(analysis)
        
        return results
    
    def clear_cache(self):
        """Clear vector cache."""
        self._vector_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        return {
            "cached_vectors": len(self._vector_cache),
            "cache_enabled": self.enable_caching,
            "corpus_size": len(self._corpus),
            "max_features": self.max_features,
            "using_transformers": self.use_transformers and self._transformer_model is not None,
            "method": "transformers" if (self.use_transformers and self._transformer_model) else "tfidf"
        }
