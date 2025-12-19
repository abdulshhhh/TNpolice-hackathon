"""
Correlation Engine - Core Analysis Component

This module performs the core investigative analysis:
1. Correlates entry and exit observations using timing patterns
2. Detects repeated patterns across multiple sessions
3. Infers probable guard nodes using statistical methods
4. Generates explainable confidence scores

METHODOLOGY:
- Timing correlation: Match entry/exit events within a time window
- Pattern analysis: Identify repeated behaviors
- Guard inference: Use guard node persistence (users tend to keep same guards)
- No deanonymization: Outputs are probabilistic leads, not identities
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
import math

from app.models.correlation import (
    TrafficObservation,
    SessionPair,
    CorrelationCluster,
    ObservationType
)
from app.models.topology import TopologySnapshot
from app.models.weight_profile import WeightProfile, ProfileType, get_profile
from app.core.topology import TORGraphAnalyzer
from config import settings
from collections import defaultdict


logger = logging.getLogger(__name__)


class CorrelationEngine:
    """
    Analyzes traffic observations to find potential entry-exit correlations
    
    This is the heart of the investigative system. It uses multiple
    weak signals to build confidence in correlations.
    """
    
    def __init__(self, topology: Optional[TopologySnapshot] = None, weight_profile: Optional[WeightProfile] = None):
        self.topology = topology
        self.graph_analyzer = TORGraphAnalyzer(topology) if topology else None
        
        # Correlation parameters from config
        self.time_window = settings.TIME_CORRELATION_WINDOW
        self.min_confidence = settings.MIN_CONFIDENCE_THRESHOLD
        
        # Weight profile for this investigation
        self.weight_profile = weight_profile or get_profile(ProfileType.STANDARD)
        self.weight_profile.validate_weights_sum()  # Ensure weights are valid
        
        # Repeated observation tracking
        self.observation_history: Dict[str, List[TrafficObservation]] = defaultdict(list)
        self.pattern_frequency: Dict[str, int] = defaultdict(int)
        
        logger.info(f"Correlation Engine initialized with weight profile: {self.weight_profile.profile_name}")
        logger.info(f"Weights - Time: {self.weight_profile.weight_time_correlation:.2f}, "
                   f"Volume: {self.weight_profile.weight_volume_similarity:.2f}, "
                   f"Pattern: {self.weight_profile.weight_pattern_similarity:.2f}")
    
    def correlate_observations(
        self,
        entry_observations: List[TrafficObservation],
        exit_observations: List[TrafficObservation]
    ) -> List[SessionPair]:
        """
        Correlate entry and exit observations to identify potential session pairs
        
        Args:
            entry_observations: List of entry point observations
            exit_observations: List of exit point observations
        
        Returns:
            List of SessionPair objects with correlation scores
        """
        logger.info(f"Correlating {len(entry_observations)} entry observations "
                   f"with {len(exit_observations)} exit observations")
        
        session_pairs = []
        
        for entry_obs in entry_observations:
            for exit_obs in exit_observations:
                # Check if observations fall within time window
                time_delta = abs((exit_obs.timestamp - entry_obs.timestamp).total_seconds())
                
                if time_delta <= self.time_window:
                    # Create session pair
                    pair = self._create_session_pair(entry_obs, exit_obs, time_delta)
                    
                    # Only include if meets minimum confidence
                    if pair.correlation_strength >= self.min_confidence:
                        session_pairs.append(pair)
        
        logger.info(f"Found {len(session_pairs)} potential session pairs")
        return session_pairs
    
    def _create_session_pair(
        self,
        entry_obs: TrafficObservation,
        exit_obs: TrafficObservation,
        time_delta: float
    ) -> SessionPair:
        """
        Create a session pair with correlation scores
        
        Correlation scoring combines multiple factors:
        1. Time proximity (closer timestamps = higher score)
        2. Volume similarity (similar data volumes = higher score)
        3. Pattern similarity (similar timing patterns = higher score)
        
        All calculations include plain English explanations for auditability.
        """
        pair_id = f"pair-{entry_obs.observation_id}-{exit_obs.observation_id}"
        
        # Track all reasoning steps
        reasoning = []
        reasoning.append(f"Analyzing correlation between entry observation '{entry_obs.observation_id}' and exit observation '{exit_obs.observation_id}'.")
        
        # Score 1: Time correlation
        time_score, time_explanation = self._calculate_time_correlation(time_delta)
        reasoning.append(time_explanation)
        
        # Score 2: Volume similarity
        volume_score, volume_explanation = self._calculate_volume_similarity(entry_obs, exit_obs)
        reasoning.append(volume_explanation)
        
        # Score 3: Pattern similarity (if timing patterns available)
        pattern_score, pattern_explanation = self._calculate_pattern_similarity(entry_obs, exit_obs)
        if pattern_explanation:
            reasoning.append(pattern_explanation)
        
        # Use weights from profile (configurable per investigation)
        time_weight = self.weight_profile.weight_time_correlation
        volume_weight = self.weight_profile.weight_volume_similarity
        pattern_weight = self.weight_profile.weight_pattern_similarity if pattern_score is not None else 0.0
        
        # Calculate composite correlation score using profile weights
        if pattern_score is not None:
            # All three signals available
            base_correlation = (
                time_score * time_weight +
                volume_score * volume_weight +
                pattern_score * pattern_weight
            )
            composite_explanation = (
                f"Calculating composite correlation score using {self.weight_profile.profile_name} weights: "
                f"Time ({time_weight:.0%}) × {time_score:.1f}% = {time_score * time_weight:.1f}, "
                f"Volume ({volume_weight:.0%}) × {volume_score:.1f}% = {volume_score * volume_weight:.1f}, "
                f"Pattern ({pattern_weight:.0%}) × {pattern_score:.1f}% = {pattern_score * pattern_weight:.1f}. "
                f"Base correlation: {base_correlation:.1f}%."
            )
        else:
            # Only time and volume available, renormalize weights
            total_weight = time_weight + volume_weight
            norm_time_weight = time_weight / total_weight
            norm_volume_weight = volume_weight / total_weight
            
            base_correlation = (
                time_score * norm_time_weight +
                volume_score * norm_volume_weight
            )
            composite_explanation = (
                f"Calculating composite correlation score using {self.weight_profile.profile_name} weights: "
                f"Time ({norm_time_weight:.0%}) × {time_score:.1f}% = {time_score * norm_time_weight:.1f}, "
                f"Volume ({norm_volume_weight:.0%}) × {volume_score:.1f}% = {volume_score * norm_volume_weight:.1f}. "
                f"Base correlation: {base_correlation:.1f}%."
            )
        reasoning.append(composite_explanation)
        logger.info(f"Composite Score Calculation: {composite_explanation}")
        
        # Apply repetition weighting to boost repeated patterns
        correlation_strength, repetition_boost = self._apply_repetition_weighting(
            base_correlation,
            entry_obs,
            exit_obs
        )
        
        # Log boost if significant
        if repetition_boost > 1.1:
            boost_explanation = f"Repetition boost applied: This pattern has been observed multiple times before. Increasing confidence from {base_correlation:.1f}% to {correlation_strength:.1f}% (boost factor: {repetition_boost:.2f}x). Repeated patterns are statistically more significant."
            reasoning.append(boost_explanation)
            logger.info(f"Repetition Boost: {boost_explanation}")
        elif settings.ENABLE_REPETITION_WEIGHTING:
            reasoning.append(f"No repetition boost applied (pattern seen for first time or below threshold). Final correlation: {correlation_strength:.1f}%.")
        
        # Hypothesize guard node if relay fingerprints are known
        hypothesized_guard = None
        guard_confidence = 0.0
        
        if entry_obs.relay_fingerprint:
            hypothesized_guard = entry_obs.relay_fingerprint
            guard_confidence = self._calculate_guard_confidence(
                entry_obs.relay_fingerprint,
                correlation_strength
            )
            
            guard_explanation = f"Entry observation shows traffic at relay {entry_obs.relay_fingerprint[:16]}... Hypothesizing this as the guard node. Guard confidence: {guard_confidence:.1f}%."
            if self.graph_analyzer:
                guard_prob = self.graph_analyzer.estimate_guard_selection_probability(entry_obs.relay_fingerprint)
                guard_explanation += f" This relay has {guard_prob:.2f}% probability of being selected as a guard based on network consensus weight."
            reasoning.append(guard_explanation)
            logger.info(f"Guard Hypothesis: {guard_explanation}")
        else:
            reasoning.append("No relay fingerprint available for guard hypothesis.")
        
        # Create detailed score breakdown
        score_breakdown = {
            "time_correlation": {
                "score": time_score,
                "weight": time_weight,
                "contribution": time_score * time_weight,
                "reasoning": time_explanation
            },
            "volume_similarity": {
                "score": volume_score,
                "weight": volume_weight,
                "contribution": volume_score * volume_weight,
                "reasoning": volume_explanation
            },
            "base_correlation": base_correlation,
            "repetition_boost": repetition_boost,
            "final_correlation": correlation_strength
        }
        
        if pattern_score is not None:
            score_breakdown["pattern_similarity"] = {
                "score": pattern_score,
                "weight": pattern_weight,
                "contribution": pattern_score * pattern_weight,
                "reasoning": pattern_explanation
            }
        
        # Add final summary
        if correlation_strength >= 70:
            final_summary = f"HIGH CONFIDENCE ({correlation_strength:.1f}%): Strong evidence suggests these observations represent the same TOR session. Multiple indicators align well."
        elif correlation_strength >= 40:
            final_summary = f"MEDIUM CONFIDENCE ({correlation_strength:.1f}%): Moderate correlation detected. Some indicators suggest the same session, but uncertainty remains."
        else:
            final_summary = f"LOW CONFIDENCE ({correlation_strength:.1f}%): Weak correlation. May be coincidental or different sessions."
        
        reasoning.append(final_summary)
        logger.info(f"Final Assessment: {final_summary}")
        
        pair = SessionPair(
            pair_id=pair_id,
            entry_observation_id=entry_obs.observation_id,
            exit_observation_id=exit_obs.observation_id,
            time_delta=time_delta,
            time_correlation_score=time_score,
            pattern_similarity=pattern_score,
            volume_similarity=volume_score,
            hypothesized_guard=hypothesized_guard,
            guard_confidence=guard_confidence,
            correlation_strength=correlation_strength,
            reasoning=reasoning,
            score_breakdown=score_breakdown
        )
        
        return pair
    
    def _calculate_time_correlation(self, time_delta: float) -> tuple[float, str]:
        """
        Calculate time correlation score (0-100)
        
        Uses exponential decay: perfect match at 0 seconds,
        decreases as time delta increases
        
        Returns:
            Tuple of (score, plain_english_explanation)
        """
        # Normalize to 0-1 range using exponential decay
        # At time_window seconds, score is ~36.8% (1/e)
        normalized = math.exp(-time_delta / self.time_window)
        
        # Convert to 0-100 scale
        score = normalized * 100
        
        # Generate plain English explanation
        if time_delta < 1.0:
            explanation = f"Entry and exit observations are nearly simultaneous ({time_delta:.2f} seconds apart). This is highly indicative of the same TOR session. Time correlation score: {score:.1f}%."
        elif time_delta < 30:
            explanation = f"Observations are {time_delta:.1f} seconds apart, which is very close. TOR circuits typically add only 1-2 seconds of latency. Time correlation score: {score:.1f}%."
        elif time_delta < 120:
            explanation = f"Observations are {time_delta:.1f} seconds apart. This is within typical TOR latency variance. Time correlation score: {score:.1f}%."
        elif time_delta < self.time_window:
            explanation = f"Observations are {time_delta:.1f} seconds apart. Still within the correlation window ({self.time_window}s), but confidence decreases with larger gaps. Time correlation score: {score:.1f}%."
        else:
            explanation = f"Observations are {time_delta:.1f} seconds apart, exceeding the correlation window ({self.time_window}s). Low confidence in temporal correlation. Time correlation score: {score:.1f}%."
        
        logger.info(f"Time Correlation Analysis: {explanation}")
        
        return score, explanation
    
    def _calculate_volume_similarity(
        self,
        entry_obs: TrafficObservation,
        exit_obs: TrafficObservation
    ) -> tuple[float, str]:
        """
        Calculate volume similarity score (0-100)
        
        Compares bytes transferred in both observations
        TOR adds some overhead, so we allow for differences
        
        Returns:
            Tuple of (score, plain_english_explanation)
        """
        if not entry_obs.bytes_transferred or not exit_obs.bytes_transferred:
            explanation = "Volume data is unavailable for one or both observations. Using neutral score of 50%. Cannot make volume-based assessment."
            logger.info(f"Volume Similarity Analysis: {explanation}")
            return 50.0, explanation
        
        entry_bytes = entry_obs.bytes_transferred
        exit_bytes = exit_obs.bytes_transferred
        
        # Calculate relative difference
        if entry_bytes == 0 and exit_bytes == 0:
            explanation = "Both observations show zero bytes transferred. Perfect volume match. Score: 100%."
            logger.info(f"Volume Similarity Analysis: {explanation}")
            return 100.0, explanation
        
        max_bytes = max(entry_bytes, exit_bytes)
        min_bytes = min(entry_bytes, exit_bytes)
        
        if max_bytes == 0:
            explanation = "Invalid volume data (max is zero). Cannot calculate similarity. Score: 0%."
            logger.warning(f"Volume Similarity Analysis: {explanation}")
            return 0.0, explanation
        
        # Similarity ratio
        similarity = (min_bytes / max_bytes) * 100
        
        # Calculate percentage difference
        diff_percent = ((max_bytes - min_bytes) / max_bytes) * 100
        
        # Generate explanation
        entry_mb = entry_bytes / 1_000_000
        exit_mb = exit_bytes / 1_000_000
        
        if similarity >= 95:
            explanation = f"Entry traffic: {entry_mb:.2f}MB, Exit traffic: {exit_mb:.2f}MB. Volumes are nearly identical (difference: {diff_percent:.1f}%). This strongly suggests the same data passing through TOR. Volume similarity: {similarity:.1f}%."
        elif similarity >= 85:
            explanation = f"Entry traffic: {entry_mb:.2f}MB, Exit traffic: {exit_mb:.2f}MB. Volumes are very similar (difference: {diff_percent:.1f}%). The ~3-5% variance is consistent with TOR protocol overhead. Volume similarity: {similarity:.1f}%."
        elif similarity >= 70:
            explanation = f"Entry traffic: {entry_mb:.2f}MB, Exit traffic: {exit_mb:.2f}MB. Volumes are reasonably similar (difference: {diff_percent:.1f}%). Could be the same session with some buffering variance. Volume similarity: {similarity:.1f}%."
        elif similarity >= 50:
            explanation = f"Entry traffic: {entry_mb:.2f}MB, Exit traffic: {exit_mb:.2f}MB. Moderate volume difference (difference: {diff_percent:.1f}%). May indicate different sessions or significant protocol overhead. Volume similarity: {similarity:.1f}%."
        else:
            explanation = f"Entry traffic: {entry_mb:.2f}MB, Exit traffic: {exit_mb:.2f}MB. Large volume difference (difference: {diff_percent:.1f}%). Unlikely to be the same session. Volume similarity: {similarity:.1f}%."
        
        logger.info(f"Volume Similarity Analysis: {explanation}")
        
        return similarity, explanation
    
    def _calculate_pattern_similarity(
        self,
        entry_obs: TrafficObservation,
        exit_obs: TrafficObservation
    ) -> tuple[Optional[float], Optional[str]]:
        """
        Calculate timing pattern similarity (0-100)
        
        Compares inter-packet timing patterns if available
        Uses simple correlation for PoC
        
        Returns:
            Tuple of (score, plain_english_explanation)
        """
        if not entry_obs.inter_packet_timings or not exit_obs.inter_packet_timings:
            explanation = "Inter-packet timing data is not available. Cannot perform pattern analysis."
            logger.debug(f"Pattern Similarity Analysis: {explanation}")
            return None, explanation
        
        # Simple implementation: compare pattern lengths and basic statistics
        entry_pattern = entry_obs.inter_packet_timings
        exit_pattern = exit_obs.inter_packet_timings
        
        # Length similarity
        max_len = max(len(entry_pattern), len(exit_pattern))
        min_len = min(len(entry_pattern), len(exit_pattern))
        
        if max_len == 0:
            explanation = "Pattern data exists but is empty. Cannot calculate similarity."
            logger.debug(f"Pattern Similarity Analysis: {explanation}")
            return None, explanation
        
        length_similarity = (min_len / max_len) * 100
        
        # Generate explanation
        if length_similarity >= 90:
            explanation = f"Entry pattern: {len(entry_pattern)} packets, Exit pattern: {len(exit_pattern)} packets. Packet counts are nearly identical, suggesting the same data stream. Pattern similarity: {length_similarity:.1f}%."
        elif length_similarity >= 70:
            explanation = f"Entry pattern: {len(entry_pattern)} packets, Exit pattern: {len(exit_pattern)} packets. Packet counts are similar, consistent with TOR multiplexing. Pattern similarity: {length_similarity:.1f}%."
        else:
            explanation = f"Entry pattern: {len(entry_pattern)} packets, Exit pattern: {len(exit_pattern)} packets. Significant difference in packet counts. May indicate different sessions or heavy multiplexing. Pattern similarity: {length_similarity:.1f}%."
        
        logger.info(f"Pattern Similarity Analysis: {explanation}")
        
        # For PoC, just use length similarity
        # In production, would use more sophisticated correlation techniques
        return length_similarity, explanation
    
    def _calculate_guard_confidence(self, guard_fingerprint: str, base_correlation: float) -> float:
        """
        Calculate confidence in guard node hypothesis
        
        Factors:
        - Base correlation strength
        - Guard's selection probability in network
        """
        if not self.graph_analyzer:
            return base_correlation
        
        # Get guard selection probability
        guard_probability = self.graph_analyzer.estimate_guard_selection_probability(guard_fingerprint)
        
        # Combine base correlation with guard probability
        # Higher probability guards are more likely to be selected
        confidence = (base_correlation * 0.7) + (guard_probability * 0.3)
        
        return min(confidence, 100.0)
    
    def _calculate_repetition_weight(self, observation: TrafficObservation) -> float:
        """
        Calculate weight boost based on observation repetition
        
        Repeated observations of similar patterns increase confidence:
        - Same relay fingerprint seen multiple times
        - Similar timing patterns
        - Consistent behavior
        
        Args:
            observation: The observation to calculate weight for
        
        Returns:
            Weight multiplier (1.0 = no boost, up to MAX_REPETITION_BOOST)
        """
        if not settings.ENABLE_REPETITION_WEIGHTING:
            return 1.0
        
        if not observation.relay_fingerprint:
            return 1.0
        
        # Track this observation
        pattern_key = self._create_pattern_key(observation)
        self.observation_history[observation.relay_fingerprint].append(observation)
        self.pattern_frequency[pattern_key] += 1
        
        # Get repetition count for this pattern
        repetition_count = self.pattern_frequency[pattern_key]
        
        # Calculate boost
        if repetition_count < settings.MIN_REPETITIONS_FOR_BOOST:
            return 1.0
        
        # Logarithmic scaling: more repetitions = higher confidence, but with diminishing returns
        # Formula: 1.0 + (log2(repetitions) * boost_factor)
        boost = 1.0 + (math.log2(repetition_count) * (settings.REPETITION_BOOST_FACTOR - 1.0))
        
        # Cap at maximum boost
        boost = min(boost, settings.MAX_REPETITION_BOOST)
        
        logger.debug(f"Repetition weight for {pattern_key}: {boost:.2f}x (count: {repetition_count})")
        
        return boost
    
    def _create_pattern_key(self, observation: TrafficObservation) -> str:
        """
        Create a unique key for pattern matching
        
        Groups observations by:
        - Relay fingerprint
        - Observation type
        - Approximate volume (bucketed)
        
        Args:
            observation: The observation to create key for
        
        Returns:
            Pattern key string
        """
        relay = observation.relay_fingerprint or "unknown"
        obs_type = observation.observation_type.value if hasattr(observation.observation_type, 'value') else observation.observation_type
        
        # Bucket volume into ranges for pattern matching
        # This allows similar (but not identical) volumes to be grouped
        if observation.bytes_transferred:
            # Bucket into 100KB ranges
            volume_bucket = (observation.bytes_transferred // 100000) * 100000
        else:
            volume_bucket = 0
        
        return f"{relay}:{obs_type}:{volume_bucket}"
    
    def _apply_repetition_weighting(
        self,
        base_score: float,
        entry_obs: TrafficObservation,
        exit_obs: TrafficObservation
    ) -> Tuple[float, float]:
        """
        Apply repetition weighting to correlation score
        
        Args:
            base_score: Base correlation strength
            entry_obs: Entry observation
            exit_obs: Exit observation
        
        Returns:
            Tuple of (weighted_score, repetition_boost)
        """
        if not settings.ENABLE_REPETITION_WEIGHTING:
            return base_score, 1.0
        
        # Calculate weights for both observations
        entry_weight = self._calculate_repetition_weight(entry_obs)
        exit_weight = self._calculate_repetition_weight(exit_obs)
        
        # Use average of both weights
        combined_weight = (entry_weight + exit_weight) / 2.0
        
        # Apply weight to score
        # Use a softer application to avoid over-boosting
        weighted_score = base_score * (1.0 + (combined_weight - 1.0) * 0.5)
        
        # Cap at 100%
        weighted_score = min(weighted_score, 100.0)
        
        return weighted_score, combined_weight
    
    def cluster_session_pairs(self, session_pairs: List[SessionPair]) -> List[CorrelationCluster]:
        """
        Group session pairs into clusters based on repeated patterns
        
        Clusters indicate:
        - Same user across multiple sessions
        - Consistent guard node usage
        - Behavioral patterns
        
        Args:
            session_pairs: List of correlated session pairs
        
        Returns:
            List of CorrelationCluster objects
        """
        logger.info(f"Clustering {len(session_pairs)} session pairs")
        
        # Group by hypothesized guard
        guard_groups: Dict[str, List[SessionPair]] = {}
        
        for pair in session_pairs:
            if pair.hypothesized_guard:
                if pair.hypothesized_guard not in guard_groups:
                    guard_groups[pair.hypothesized_guard] = []
                guard_groups[pair.hypothesized_guard].append(pair)
        
        # Create clusters
        clusters = []
        cluster_id = 1
        
        for guard_fp, pairs in guard_groups.items():
            # Only cluster if we have multiple observations
            if len(pairs) >= settings.MIN_OBSERVATIONS_FOR_CORRELATION:
                cluster = self._create_cluster(cluster_id, guard_fp, pairs)
                clusters.append(cluster)
                cluster_id += 1
        
        logger.info(f"Created {len(clusters)} correlation clusters")
        return clusters
    
    def _create_cluster(
        self,
        cluster_id: int,
        guard_fp: str,
        pairs: List[SessionPair]
    ) -> CorrelationCluster:
        """Create a correlation cluster from related session pairs"""
        
        # Extract all observation IDs
        observation_ids = set()
        for pair in pairs:
            observation_ids.add(pair.entry_observation_id)
            observation_ids.add(pair.exit_observation_id)
        
        # Extract timestamps (would need to pass observations for real implementation)
        # For PoC, use pair creation timestamps
        timestamps = [pair.created_at for pair in pairs]
        first_obs = min(timestamps)
        last_obs = max(timestamps)
        
        # Calculate consistency score
        avg_correlation = sum(p.correlation_strength for p in pairs) / len(pairs)
        consistency_score = avg_correlation
        
        # Guard persistence score (high if same guard appears repeatedly)
        guard_persistence = min(len(pairs) * 10, 100)  # Simple scoring
        
        # Overall cluster confidence
        cluster_confidence = (consistency_score * 0.6) + (guard_persistence * 0.4)
        
        # Generate reasoning
        reasoning = [
            f"Found {len(pairs)} correlated session pairs",
            f"All pairs share hypothesized guard: {guard_fp}",
            f"Average correlation strength: {avg_correlation:.1f}%",
            f"Observations span {(last_obs - first_obs).total_seconds() / 3600:.1f} hours",
        ]
        
        if guard_persistence > 70:
            reasoning.append("Strong guard persistence indicates consistent user behavior")
        
        cluster = CorrelationCluster(
            cluster_id=f"cluster-{cluster_id}",
            observation_ids=list(observation_ids),
            session_pair_ids=[p.pair_id for p in pairs],
            first_observation=first_obs,
            last_observation=last_obs,
            observation_count=len(observation_ids),
            consistency_score=consistency_score,
            probable_guards=[guard_fp],
            guard_persistence_score=guard_persistence,
            cluster_confidence=cluster_confidence,
            reasoning=reasoning
        )
        
        return cluster
    
    def get_repetition_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about repeated observation patterns
        
        Returns:
            Dictionary containing:
            - total_patterns: Number of unique patterns tracked
            - total_observations: Total observations across all patterns
            - most_common_pattern: Most frequently observed pattern
            - most_common_pattern_count: Count of most common pattern
            - average_repetitions: Average repetitions per pattern
        """
        if not self.pattern_frequency:
            return {
                "total_patterns": 0,
                "total_observations": 0,
                "most_common_pattern": None,
                "most_common_pattern_count": 0,
                "average_repetitions": 0.0
            }
        
        total_observations = sum(self.pattern_frequency.values())
        most_common = max(self.pattern_frequency.items(), key=lambda x: x[1])
        
        return {
            "total_patterns": len(self.pattern_frequency),
            "total_observations": total_observations,
            "most_common_pattern": most_common[0],
            "most_common_pattern_count": most_common[1],
            "average_repetitions": total_observations / len(self.pattern_frequency)
        }
    
    def get_weight_profile(self) -> WeightProfile:
        """
        Get the current weight profile being used
        
        Returns:
            WeightProfile instance
        """
        return self.weight_profile
    
    def set_weight_profile(self, profile: WeightProfile) -> None:
        """
        Update the weight profile for future correlations
        
        Args:
            profile: New WeightProfile to use
        
        Raises:
            ValueError: If profile weights don't sum to 1.0
        """
        profile.validate_weights_sum()
        self.weight_profile = profile
        logger.info(f"Weight profile updated to: {profile.profile_name}")
        logger.info(f"New weights - Time: {profile.weight_time_correlation:.2f}, "
                   f"Volume: {profile.weight_volume_similarity:.2f}, "
                   f"Pattern: {profile.weight_pattern_similarity:.2f}")
