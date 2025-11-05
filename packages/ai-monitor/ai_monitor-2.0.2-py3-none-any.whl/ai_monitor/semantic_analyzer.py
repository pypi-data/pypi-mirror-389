"""
Ultra-lightweight semantic analysis using pure Python (no compiled dependencies).

Uses TF-IDF with pure Python implementation for semantic similarity.
No scikit-learn, no scipy, no torch - just numpy and pure Python!
Perfect for Docker and constrained environments.
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
import numpy as np
from collections import Counter, defaultdict
import re
import math

logger = logging.getLogger(__name__)


class PurePythonTfidfVectorizer:
    """Pure Python TF-IDF implementation (no sklearn needed)."""
    
    def __init__(
        self,
        max_features: int = 1000,
        min_df: int = 1,
        max_df: float = 0.85,
        stop_words: Optional[List[str]] = None
    ):
        self.max_features = max_features
        self.min_df = min_df
        self.max_df = max_df
        self.stop_words = set(stop_words or self._get_english_stop_words())
        self.vocabulary_ = {}
        self.idf_ = {}
        
    def _get_english_stop_words(self) -> List[str]:
        """Common English stop words."""
        return [
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'the', 'this', 'but', 'they', 'have',
            'had', 'what', 'said', 'each', 'which', 'do', 'how', 'their', 'if',
            'up', 'out', 'many', 'then', 'them', 'these', 'so', 'some', 'her',
            'would', 'make', 'like', 'into', 'him', 'time', 'two', 'more',
            'go', 'no', 'way', 'could', 'my', 'than', 'first', 'been', 'call',
            'who', 'oil', 'sit', 'now', 'find', 'down', 'day', 'did', 'get',
            'may', 'part', 'over', 'think', 'where', 'much', 'through', 'back'
        ]
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        # Convert to lowercase and extract words
        words = re.findall(r'\b\w+\b', text.lower())
        # Remove stop words
        words = [w for w in words if w not in self.stop_words and len(w) > 2]
        return words
    
    def _build_vocabulary(self, documents: List[str]) -> None:
        """Build vocabulary from documents."""
        # Count document frequency for each term
        doc_freq = defaultdict(int)
        total_docs = len(documents)
        
        for doc in documents:
            unique_words = set(self._tokenize(doc))
            for word in unique_words:
                doc_freq[word] += 1
        
        # Filter by min_df and max_df
        vocab = {}
        for word, freq in doc_freq.items():
            df_ratio = freq / total_docs
            if freq >= self.min_df and df_ratio <= self.max_df:
                vocab[word] = len(vocab)
        
        # Limit vocabulary size
        if len(vocab) > self.max_features:
            # Keep most frequent terms
            sorted_vocab = sorted(
                vocab.items(), 
                key=lambda x: doc_freq[x[0]], 
                reverse=True
            )
            vocab = {word: i for i, (word, _) in enumerate(sorted_vocab[:self.max_features])}
        
        self.vocabulary_ = vocab
        
        # Calculate IDF values
        for word in vocab:
            df = doc_freq[word]
            idf = math.log(total_docs / df)
            self.idf_[word] = idf
    
    def fit_transform(self, documents: List[str]) -> np.ndarray:
        """Fit vocabulary and transform documents to TF-IDF matrix."""
        self._build_vocabulary(documents)
        return self.transform(documents)
    
    def transform(self, documents: List[str]) -> np.ndarray:
        """Transform documents to TF-IDF matrix."""
        n_docs = len(documents)
        n_features = len(self.vocabulary_)
        
        if n_features == 0:
            return np.zeros((n_docs, 1))
        
        tfidf_matrix = np.zeros((n_docs, n_features))
        
        for doc_idx, doc in enumerate(documents):
            words = self._tokenize(doc)
            word_counts = Counter(words)
            total_words = len(words)
            
            if total_words == 0:
                continue
                
            for word, count in word_counts.items():
                if word in self.vocabulary_:
                    word_idx = self.vocabulary_[word]
                    tf = count / total_words  # Term frequency
                    idf = self.idf_.get(word, 0)  # Inverse document frequency
                    tfidf_matrix[doc_idx, word_idx] = tf * idf
        
        return tfidf_matrix


def cosine_similarity_pure(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Pure Python cosine similarity (no scipy needed)."""
    # Flatten vectors
    vec1 = vec1.flatten()
    vec2 = vec2.flatten()
    
    # Calculate dot product
    dot_product = np.dot(vec1, vec2)
    
    # Calculate magnitudes
    magnitude1 = np.sqrt(np.sum(vec1 ** 2))
    magnitude2 = np.sqrt(np.sum(vec2 ** 2))
    
    # Avoid division by zero
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)


class SemanticAnalyzer:
    """
    Ultra-lightweight semantic analysis using pure Python.
    
    No scikit-learn, no scipy, no torch - just numpy and pure Python!
    Perfect for Docker and constrained environments.
    """
    
    def __init__(
        self,
        max_features: int = 1000,
        enable_caching: bool = True,
        use_transformers: bool = False
    ):
        """
        Initialize ultra-lightweight semantic analyzer.
        
        Args:
            max_features: Maximum vocabulary size for TF-IDF
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
        
        logger.info("Initialized ultra-lightweight semantic analyzer (pure Python)")
        
    def _get_vectorizer(self):
        """Lazy load the pure Python TF-IDF vectorizer."""
        if self._vectorizer is None:
            self._vectorizer = PurePythonTfidfVectorizer(
                max_features=self.max_features,
                min_df=1,
                max_df=0.85
            )
        return self._vectorizer
    
    def _get_transformer_model(self):
        """Lazy load transformer model if requested and available."""
        if self._transformer_model is None and self.use_transformers:
            try:
                from sentence_transformers import SentenceTransformer
                self._transformer_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Loaded transformer model (optional)")
            except ImportError:
                logger.info("sentence-transformers not available, using pure Python TF-IDF")
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
        
        # Use pure Python TF-IDF (ultra-lightweight)
        vectorizer = self._get_vectorizer()
        
        # Add to corpus if not already fitted
        if text not in self._corpus:
            self._corpus.append(text)
            # Refit vectorizer with updated corpus
            try:
                vectorizer.fit_transform(self._corpus)
            except Exception:
                # If fitting fails, use simple word overlap
                return self._simple_vector(text)
        
        # Transform text
        try:
            vector = vectorizer.transform([text])
            vector = vector[0] if len(vector) > 0 else np.zeros(100)
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
            vector1 = self._get_vector(text1)
            vector2 = self._get_vector(text2)
            
            # Ensure vectors are same length
            if len(vector1) != len(vector2):
                max_len = max(len(vector1), len(vector2))
                if len(vector1) < max_len:
                    vector1 = np.pad(vector1, (0, max_len - len(vector1)))
                if len(vector2) < max_len:
                    vector2 = np.pad(vector2, (0, max_len - len(vector2)))
            
            # Cosine similarity
            similarity = cosine_similarity_pure(vector1.reshape(1, -1), vector2.reshape(1, -1))
            
            return float(max(0.0, min(1.0, similarity)))  # Clamp to [0, 1]
            
        except Exception as e:
            logger.warning(f"TF-IDF similarity calculation failed: {e}")
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
        self._corpus.clear()
    
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
            "method": "transformers" if (self.use_transformers and self._transformer_model) else "pure_python_tfidf"
        }


# Convenience function
def create_semantic_analyzer(**kwargs) -> SemanticAnalyzer:
    """Create ultra-lightweight semantic analyzer."""
    return SemanticAnalyzer(**kwargs)