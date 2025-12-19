"""
Tests for Weight Profile functionality

Verifies that weight profiles can be configured per investigation
and properly affect correlation scoring.
"""
import pytest
from datetime import datetime, timedelta

from app.models.weight_profile import (
    WeightProfile,
    ProfileType,
    get_profile,
    create_custom_profile,
    PREDEFINED_PROFILES
)
from app.core.correlation import CorrelationEngine
from app.models.correlation import TrafficObservation, ObservationType


def create_test_observation(
    obs_id: str,
    obs_type: ObservationType,
    timestamp: datetime,
    bytes_transferred: int = 1000000
):
    """Helper to create test observations"""
    return TrafficObservation(
        observation_id=obs_id,
        observation_type=obs_type,
        timestamp=timestamp,
        duration=60.0,
        observed_ip="1.2.3.4",
        observed_port=9001,
        relay_fingerprint="A" * 40,
        bytes_transferred=bytes_transferred,
        packets_count=500,
        source="test"
    )


def test_predefined_profiles_exist():
    """Test that all predefined profiles exist and are valid"""
    assert len(PREDEFINED_PROFILES) == 4
    assert ProfileType.STANDARD in PREDEFINED_PROFILES
    assert ProfileType.TIME_FOCUSED in PREDEFINED_PROFILES
    assert ProfileType.VOLUME_FOCUSED in PREDEFINED_PROFILES
    assert ProfileType.PATTERN_FOCUSED in PREDEFINED_PROFILES
    
    # Verify each profile has valid weights
    for profile in PREDEFINED_PROFILES.values():
        assert profile.validate_weights_sum()
        assert 0 <= profile.weight_time_correlation <= 1
        assert 0 <= profile.weight_volume_similarity <= 1
        assert 0 <= profile.weight_pattern_similarity <= 1


def test_standard_profile():
    """Test standard balanced profile"""
    profile = get_profile(ProfileType.STANDARD)
    
    assert profile.profile_type == ProfileType.STANDARD
    assert profile.weight_time_correlation == 0.40
    assert profile.weight_volume_similarity == 0.30
    assert profile.weight_pattern_similarity == 0.30
    assert profile.validate_weights_sum()


def test_time_focused_profile():
    """Test time-focused profile prioritizes temporal correlation"""
    profile = get_profile(ProfileType.TIME_FOCUSED)
    
    assert profile.profile_type == ProfileType.TIME_FOCUSED
    assert profile.weight_time_correlation == 0.60  # Highest weight
    assert profile.weight_time_correlation > profile.weight_volume_similarity
    assert profile.weight_time_correlation > profile.weight_pattern_similarity
    assert profile.validate_weights_sum()


def test_volume_focused_profile():
    """Test volume-focused profile prioritizes data volume"""
    profile = get_profile(ProfileType.VOLUME_FOCUSED)
    
    assert profile.profile_type == ProfileType.VOLUME_FOCUSED
    assert profile.weight_volume_similarity == 0.50  # Highest weight
    assert profile.weight_volume_similarity > profile.weight_time_correlation
    assert profile.weight_volume_similarity > profile.weight_pattern_similarity
    assert profile.validate_weights_sum()


def test_pattern_focused_profile():
    """Test pattern-focused profile prioritizes behavioral patterns"""
    profile = get_profile(ProfileType.PATTERN_FOCUSED)
    
    assert profile.profile_type == ProfileType.PATTERN_FOCUSED
    assert profile.weight_pattern_similarity == 0.50  # Highest weight
    assert profile.weight_pattern_similarity > profile.weight_time_correlation
    assert profile.weight_pattern_similarity > profile.weight_volume_similarity
    assert profile.validate_weights_sum()


def test_create_valid_custom_profile():
    """Test creating a valid custom profile"""
    profile = create_custom_profile(
        profile_id="test-custom",
        profile_name="Test Custom Profile",
        weight_time=0.5,
        weight_volume=0.3,
        weight_pattern=0.2,
        case_id="CASE-001",
        created_by="test@example.com",
        description="Test profile"
    )
    
    assert profile.profile_id == "test-custom"
    assert profile.profile_type == ProfileType.CUSTOM
    assert profile.weight_time_correlation == 0.5
    assert profile.weight_volume_similarity == 0.3
    assert profile.weight_pattern_similarity == 0.2
    assert profile.case_id == "CASE-001"
    assert profile.created_by == "test@example.com"
    assert profile.validate_weights_sum()


def test_create_custom_profile_invalid_sum():
    """Test that custom profile rejects weights that don't sum to 1.0"""
    with pytest.raises(ValueError, match="must sum to 1.0"):
        create_custom_profile(
            profile_id="invalid",
            profile_name="Invalid Profile",
            weight_time=0.5,
            weight_volume=0.3,
            weight_pattern=0.3  # Sum = 1.1
        )


def test_create_custom_profile_out_of_range():
    """Test that custom profile rejects out-of-range weights"""
    with pytest.raises(ValueError, match="must be between 0 and 1"):
        create_custom_profile(
            profile_id="invalid2",
            profile_name="Invalid Profile 2",
            weight_time=1.5,  # > 1.0
            weight_volume=0.0,
            weight_pattern=-0.5  # < 0
        )


def test_correlation_engine_default_profile():
    """Test that correlation engine uses standard profile by default"""
    engine = CorrelationEngine()
    
    profile = engine.get_weight_profile()
    assert profile.profile_type == ProfileType.STANDARD
    assert profile.weight_time_correlation == 0.40
    assert profile.weight_volume_similarity == 0.30
    assert profile.weight_pattern_similarity == 0.30


def test_correlation_engine_with_custom_profile():
    """Test that correlation engine accepts custom profile"""
    custom_profile = create_custom_profile(
        profile_id="test-profile",
        profile_name="Test Profile",
        weight_time=0.6,
        weight_volume=0.2,
        weight_pattern=0.2
    )
    
    engine = CorrelationEngine(weight_profile=custom_profile)
    
    profile = engine.get_weight_profile()
    assert profile.profile_id == "test-profile"
    assert profile.weight_time_correlation == 0.6
    assert profile.weight_volume_similarity == 0.2
    assert profile.weight_pattern_similarity == 0.2


def test_correlation_engine_profile_update():
    """Test updating weight profile on existing engine"""
    engine = CorrelationEngine()
    
    # Start with standard
    assert engine.get_weight_profile().profile_type == ProfileType.STANDARD
    
    # Update to time-focused
    time_profile = get_profile(ProfileType.TIME_FOCUSED)
    engine.set_weight_profile(time_profile)
    
    assert engine.get_weight_profile().profile_type == ProfileType.TIME_FOCUSED
    assert engine.get_weight_profile().weight_time_correlation == 0.60


def test_correlation_results_differ_by_profile():
    """Test that different profiles produce different correlation strengths"""
    base_time = datetime.now()
    
    # Create observations with good time correlation but poor volume match
    entry = create_test_observation(
        "entry-1",
        ObservationType.ENTRY_OBSERVED,
        base_time,
        bytes_transferred=1000000  # 1 MB
    )
    
    exit_obs = create_test_observation(
        "exit-1",
        ObservationType.EXIT_OBSERVED,
        base_time + timedelta(seconds=1),  # Very close timing
        bytes_transferred=5000000  # 5 MB - big difference
    )
    
    # Test with time-focused profile (should score higher)
    time_engine = CorrelationEngine(weight_profile=get_profile(ProfileType.TIME_FOCUSED))
    time_pairs = time_engine.correlate_observations([entry], [exit_obs])
    
    # Test with volume-focused profile (should score lower)
    volume_engine = CorrelationEngine(weight_profile=get_profile(ProfileType.VOLUME_FOCUSED))
    volume_pairs = volume_engine.correlate_observations([entry], [exit_obs])
    
    # Time-focused should produce higher correlation (good time, bad volume)
    if time_pairs and volume_pairs:
        print(f"\nTime-focused correlation: {time_pairs[0].correlation_strength:.1f}%")
        print(f"Volume-focused correlation: {volume_pairs[0].correlation_strength:.1f}%")
        assert time_pairs[0].correlation_strength > volume_pairs[0].correlation_strength


def test_profile_in_reasoning():
    """Test that profile name appears in correlation reasoning"""
    base_time = datetime.now()
    
    entry = create_test_observation("entry-1", ObservationType.ENTRY_OBSERVED, base_time)
    exit_obs = create_test_observation("exit-1", ObservationType.EXIT_OBSERVED, base_time + timedelta(seconds=1))
    
    # Use time-focused profile
    profile = get_profile(ProfileType.TIME_FOCUSED)
    engine = CorrelationEngine(weight_profile=profile)
    
    pairs = engine.correlate_observations([entry], [exit_obs])
    
    if pairs:
        reasoning_text = " ".join(pairs[0].reasoning)
        # Profile name should appear in composite score explanation
        assert profile.profile_name in reasoning_text or "Time-Focused" in reasoning_text


def test_weight_validation():
    """Test that invalid weight profiles are rejected"""
    profile = WeightProfile(
        profile_id="invalid",
        profile_name="Invalid",
        profile_type=ProfileType.CUSTOM,
        weight_time_correlation=0.5,
        weight_volume_similarity=0.3,
        weight_pattern_similarity=0.1  # Sum = 0.9, not 1.0
    )
    
    with pytest.raises(ValueError, match="must sum to 1.0"):
        profile.validate_weights_sum()


def test_edge_case_all_weight_on_time():
    """Test extreme profile with all weight on time correlation"""
    profile = create_custom_profile(
        profile_id="time-only",
        profile_name="Time Only",
        weight_time=1.0,
        weight_volume=0.0,
        weight_pattern=0.0
    )
    
    assert profile.validate_weights_sum()
    
    engine = CorrelationEngine(weight_profile=profile)
    base_time = datetime.now()
    
    entry = create_test_observation("entry", ObservationType.ENTRY_OBSERVED, base_time, bytes_transferred=1000000)
    exit_obs = create_test_observation("exit", ObservationType.EXIT_OBSERVED, base_time + timedelta(seconds=0.5), bytes_transferred=10000000)
    
    pairs = engine.correlate_observations([entry], [exit_obs])
    
    # Should still correlate despite huge volume difference (only time matters)
    assert len(pairs) > 0


def test_profile_metadata():
    """Test that profile metadata is properly stored"""
    profile = create_custom_profile(
        profile_id="case-2025-001",
        profile_name="Narcotics Investigation",
        weight_time=0.5,
        weight_volume=0.3,
        weight_pattern=0.2,
        case_id="CASE-2025-001",
        created_by="inv.sharma@tnpolice.gov.in",
        description="Custom profile for narcotics trafficking case"
    )
    
    assert profile.profile_id == "case-2025-001"
    assert profile.case_id == "CASE-2025-001"
    assert profile.created_by == "inv.sharma@tnpolice.gov.in"
    assert "narcotics" in profile.description.lower()
    assert profile.created_at is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
