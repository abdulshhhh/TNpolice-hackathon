"""
Unit tests for Correlation Engine
"""
import pytest
from datetime import datetime, timedelta
from app.core.correlation import CorrelationEngine
from app.models.correlation import TrafficObservation, ObservationType


@pytest.fixture
def sample_observations():
    """Create sample traffic observations for testing"""
    base_time = datetime.utcnow()
    
    # Entry observation
    entry = TrafficObservation(
        observation_id="entry-001",
        observation_type=ObservationType.ENTRY_OBSERVED,
        timestamp=base_time,
        duration=60.0,
        observed_ip="1.2.3.4",
        observed_port=9001,
        relay_fingerprint="AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555",
        bytes_transferred=1000000,
        packets_count=500,
        source="test"
    )
    
    # Exit observation (correlated - close timestamp)
    exit_correlated = TrafficObservation(
        observation_id="exit-001",
        observation_type=ObservationType.EXIT_OBSERVED,
        timestamp=base_time + timedelta(seconds=1),  # Very close
        duration=60.0,
        observed_ip="5.6.7.8",
        observed_port=9001,
        relay_fingerprint="FFFF1111GGGG2222HHHH3333IIII4444JJJJ5555",
        bytes_transferred=1050000,  # Similar volume
        packets_count=520,
        source="test"
    )
    
    # Exit observation (uncorrelated - distant timestamp)
    exit_uncorrelated = TrafficObservation(
        observation_id="exit-002",
        observation_type=ObservationType.EXIT_OBSERVED,
        timestamp=base_time + timedelta(hours=2),  # Far away
        duration=60.0,
        observed_ip="9.10.11.12",
        observed_port=9001,
        relay_fingerprint="KKKK1111LLLL2222MMMM3333NNNN4444OOOO5555",
        bytes_transferred=500000,  # Different volume
        packets_count=250,
        source="test"
    )
    
    return {
        "entry": [entry],
        "exit_correlated": [exit_correlated],
        "exit_uncorrelated": [exit_uncorrelated]
    }


def test_correlation_engine_initialization():
    """Test correlation engine initializes without topology"""
    engine = CorrelationEngine()
    assert engine is not None


def test_time_correlation_scoring(sample_observations):
    """Test time correlation scoring formula"""
    engine = CorrelationEngine()
    
    # Very close timestamps should score high
    score_close = engine._calculate_time_correlation(1.0)  # 1 second
    assert score_close > 95.0
    
    # Distant timestamps should score low
    score_far = engine._calculate_time_correlation(600.0)  # 10 minutes
    assert score_far < 50.0


def test_volume_correlation_scoring(sample_observations):
    """Test volume similarity scoring"""
    engine = CorrelationEngine()
    
    entry = sample_observations["entry"][0]
    exit_correlated = sample_observations["exit_correlated"][0]
    
    # Similar volumes should score high
    score = engine._calculate_volume_similarity(entry, exit_correlated)
    assert score > 90.0


def test_session_pair_creation(sample_observations):
    """Test creating session pairs with correlation scores"""
    engine = CorrelationEngine()
    
    entry = sample_observations["entry"]
    exit_correlated = sample_observations["exit_correlated"]
    
    pairs = engine.correlate_observations(entry, exit_correlated)
    
    assert len(pairs) > 0
    pair = pairs[0]
    
    # Check pair attributes
    assert pair.entry_observation_id == "entry-001"
    assert pair.exit_observation_id == "exit-001"
    assert pair.correlation_strength > 0


def test_correlation_filtering(sample_observations):
    """Test that uncorrelated observations are filtered"""
    engine = CorrelationEngine()
    
    entry = sample_observations["entry"]
    exit_uncorrelated = sample_observations["exit_uncorrelated"]
    
    # Should not correlate due to large time gap
    pairs = engine.correlate_observations(entry, exit_uncorrelated)
    
    # Either no pairs or very low confidence
    if len(pairs) > 0:
        assert pairs[0].correlation_strength < 30.0


def test_cluster_creation(sample_observations):
    """Test creating correlation clusters"""
    engine = CorrelationEngine()
    
    # Create multiple correlated pairs with same guard
    entry = sample_observations["entry"] * 3  # Repeat 3 times
    exit_correlated = sample_observations["exit_correlated"] * 3
    
    pairs = engine.correlate_observations(entry, exit_correlated)
    
    clusters = engine.cluster_session_pairs(pairs)
    
    # Should create at least one cluster
    assert len(clusters) > 0
    
    cluster = clusters[0]
    assert cluster.observation_count > 0
    assert cluster.cluster_confidence > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
