"""
Semantic analysis for AI/LLM responses.

Provides semantic similarity, relevance scoring, and topic analysis
using sentence transformers and NLP techniques.
"""

from typing import Dict, List, Optional, Any, Tuple
import numpy as np


class SemanticAnalyzer:
    """
    Analyzes semantic quality of AI/LLM responses.
    
    Features:
    - Semantic similarity between prompt and response
    - Topic coherence analysis
    - Context preservation checking
    - Embedding-based relevance scoring
    
    Note: Requires sentence-transformers library.
    Install with: pip install sentence-transformers
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        enable_caching: bool = True
    ):
        """
        Initialize semantic analyzer.
        
        Args:
            model_name: SentenceTransformer model name
            enable_caching: Cache embeddings for repeated texts
        """
        self.model_name = model_name
        self.enable_caching = enable_caching
        self._model = None
        self._embedding_cache: Dict[str, np.ndarray] = {}
    
    def _get_model(self):
        """Lazy load the transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for semantic analysis. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for text with caching.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        # Check cache
        if self.enable_caching and text in self._embedding_cache:
            return self._embedding_cache[text]
        
        # Generate embedding
        model = self._get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        
        # Cache if enabled
        if self.enable_caching:
            self._embedding_cache[text] = embedding
        
        return embedding
    
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
        embedding1 = self._get_embedding(text1)
        embedding2 = self._get_embedding(text2)
        
        # Cosine similarity
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
        
        return float(similarity)
    
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
        response_embedding = self._get_embedding(response)
        
        similarities = []
        for candidate in candidate_responses:
            candidate_embedding = self._get_embedding(candidate)
            
            sim = np.dot(response_embedding, candidate_embedding) / (
                np.linalg.norm(response_embedding) * np.linalg.norm(candidate_embedding)
            )
            
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
        Extract key topics/themes from text.
        
        Args:
            text: Text to analyze
            num_topics: Number of topics to extract
            
        Returns:
            List of topic keywords
        """
        # Simple keyword extraction based on sentence similarity
        sentences = self._split_sentences(text)
        
        if not sentences:
            return []
        
        # For now, return most representative sentences
        # (Can be enhanced with proper topic modeling)
        
        if len(sentences) <= num_topics:
            return sentences
        
        # Calculate centrality of each sentence
        centrality = []
        
        for i, sent in enumerate(sentences):
            sent_emb = self._get_embedding(sent)
            
            # Calculate average similarity with all other sentences
            sims = []
            for j, other in enumerate(sentences):
                if i != j:
                    other_emb = self._get_embedding(other)
                    sim = np.dot(sent_emb, other_emb) / (
                        np.linalg.norm(sent_emb) * np.linalg.norm(other_emb)
                    )
                    sims.append(sim)
            
            centrality.append((sent, np.mean(sims) if sims else 0))
        
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
        """Clear embedding cache."""
        self._embedding_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        return {
            "cached_embeddings": len(self._embedding_cache),
            "cache_enabled": self.enable_caching,
            "model_name": self.model_name
        }
