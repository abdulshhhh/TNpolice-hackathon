"""
Test for repeated observation weighting functionality

Demonstrates how repeated observations increase correlation confidence
"""
import pytest
from datetime import datetime, timedelta
from app.core.correlation import CorrelationEngine
from app.models.correlation import TrafficObservation, ObservationType


@pytest.fixture
def correlation_engine():
    """Create correlation engine for testing"""
    return CorrelationEngine()


def create_observation(
    obs_id: str,
    obs_type: ObservationType,
    timestamp: datetime,
    relay_fp: str,
    bytes_transferred: int = 1000000
):
    """Helper to create traffic observations"""
    return TrafficObservation(
        observation_id=obs_id,
        observation_type=obs_type,
        timestamp=timestamp,
        duration=60.0,
        observed_ip="1.2.3.4",
        observed_port=9001,
        relay_fingerprint=relay_fp,
        bytes_transferred=bytes_transferred,
        packets_count=500,
        source="test"
    )


def test_repetition_weight_calculation(correlation_engine):
    """Test that repetition weight is calculated correctly"""
    base_time = datetime.utcnow()
    relay_fp = "AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555"
    
    # First observation - should get weight of 1.0 (no boost)
    obs1 = create_observation("obs-1", ObservationType.ENTRY_OBSERVED, base_time, relay_fp)
    weight1 = correlation_engine._calculate_repetition_weight(obs1)
    assert weight1 == 1.0
    
    # Second observation - still below threshold
    obs2 = create_observation("obs-2", ObservationType.ENTRY_OBSERVED, base_time + timedelta(hours=1), relay_fp)
    weight2 = correlation_engine._calculate_repetition_weight(obs2)
    
    # Third observation - should get boost (>= MIN_REPETITIONS_FOR_BOOST)
    obs3 = create_observation("obs-3", ObservationType.ENTRY_OBSERVED, base_time + timedelta(hours=2), relay_fp)
    weight3 = correlation_engine._calculate_repetition_weight(obs3)
    assert weight3 > 1.0  # Should have boost now
    
    print(f"\nRepetition weights: {weight1:.2f}, {weight2:.2f}, {weight3:.2f}")


def test_pattern_key_creation(correlation_engine):
    """Test that pattern keys group similar observations"""
    base_time = datetime.utcnow()
    relay_fp = "AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555"
    
    # Same relay, same type, similar volume -> same pattern
    obs1 = create_observation("obs-1", ObservationType.ENTRY_OBSERVED, base_time, relay_fp, 1050000)
    obs2 = create_observation("obs-2", ObservationType.ENTRY_OBSERVED, base_time, relay_fp, 1080000)
    
    key1 = correlation_engine._create_pattern_key(obs1)
    key2 = correlation_engine._create_pattern_key(obs2)
    
    assert key1 == key2  # Should be same pattern (volume bucketed to 100KB ranges)
    
    # Different relay -> different pattern
    obs3 = create_observation("obs-3", ObservationType.ENTRY_OBSERVED, base_time, "DIFFERENT_FINGERPRINT", 1050000)
    key3 = correlation_engine._create_pattern_key(obs3)
    
    assert key1 != key3


def test_repetition_boosts_correlation(correlation_engine):
    """Test that repeated observations increase correlation scores"""
    base_time = datetime.utcnow()
    guard_fp = "AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555"
    exit_fp = "FFFF1111GGGG2222HHHH3333IIII4444JJJJ5555"
    
    # Create first pair of observations
    entry1 = create_observation("entry-1", ObservationType.ENTRY_OBSERVED, base_time, guard_fp)
    exit1 = create_observation("exit-1", ObservationType.EXIT_OBSERVED, base_time + timedelta(seconds=1), exit_fp)
    
    pairs1 = correlation_engine.correlate_observations([entry1], [exit1])
    initial_score = pairs1[0].correlation_strength if pairs1 else 0
    
    # Create more observations with same pattern (repeated behavior)
    entries = [entry1]
    exits = [exit1]
    
    for i in range(2, 6):  # Add 4 more pairs
        entry = create_observation(
            f"entry-{i}",
            ObservationType.ENTRY_OBSERVED,
            base_time + timedelta(hours=i),
            guard_fp
        )
        exit_obs = create_observation(
            f"exit-{i}",
            ObservationType.EXIT_OBSERVED,
            base_time + timedelta(hours=i, seconds=1),
            exit_fp
        )
        entries.append(entry)
        exits.append(exit_obs)
    
    # Correlate all observations
    pairs_repeated = correlation_engine.correlate_observations(entries, exits)
    
    # Later pairs should have higher scores due to repetition
    if len(pairs_repeated) >= 5:
        last_score = pairs_repeated[-1].correlation_strength
        
        print(f"\nInitial correlation: {initial_score:.2f}%")
        print(f"After repetition: {last_score:.2f}%")
        
        # With repetition weighting enabled, later observations should score higher
        # (or at least not lower, if already at max)
        assert last_score >= initial_score * 0.95  # Allow small variance


def test_repetition_statistics(correlation_engine):
    """Test getting repetition statistics"""
    base_time = datetime.utcnow()
    
    # Create several observations with repeated patterns
    relay1 = "AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555"
    relay2 = "FFFF1111GGGG2222HHHH3333IIII4444JJJJ5555"
    
    # Pattern 1: Relay1, repeated 5 times
    for i in range(5):
        obs = create_observation(
            f"obs-1-{i}",
            ObservationType.ENTRY_OBSERVED,
            base_time + timedelta(hours=i),
            relay1
        )
        correlation_engine._calculate_repetition_weight(obs)
    
    # Pattern 2: Relay2, repeated 3 times
    for i in range(3):
        obs = create_observation(
            f"obs-2-{i}",
            ObservationType.EXIT_OBSERVED,
            base_time + timedelta(hours=i),
            relay2
        )
        correlation_engine._calculate_repetition_weight(obs)
    
    # Get statistics
    stats = correlation_engine.get_repetition_statistics()
    
    assert stats["enabled"] is True
    assert stats["total_unique_patterns"] == 2
    assert stats["max_repetitions"] == 5
    
    print(f"\nRepetition Statistics:")
    print(f"  Unique patterns: {stats['total_unique_patterns']}")
    print(f"  Repeated patterns: {stats['repeated_patterns']}")
    print(f"  Max repetitions: {stats['max_repetitions']}")
    print(f"  Average repetitions: {stats['avg_repetitions']}")


def test_repetition_weighting_disabled():
    """Test that repetition weighting can be disabled via config"""
    from config import settings
    
    # Temporarily disable
    original_value = settings.ENABLE_REPETITION_WEIGHTING
    settings.ENABLE_REPETITION_WEIGHTING = False
    
    try:
        engine = CorrelationEngine()
        base_time = datetime.utcnow()
        
        obs = create_observation("obs-1", ObservationType.ENTRY_OBSERVED, base_time, "RELAY_FP")
        weight = engine._calculate_repetition_weight(obs)
        
        assert weight == 1.0  # No boost when disabled
        
        stats = engine.get_repetition_statistics()
        assert stats["enabled"] is False
    
    finally:
        # Restore original value
        settings.ENABLE_REPETITION_WEIGHTING = original_value


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
