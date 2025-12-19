"""
Test for explainability and plain English reasoning

Verifies that all confidence score changes are justified with clear explanations
"""
import pytest
from datetime import datetime, timedelta
from app.core.correlation import CorrelationEngine
from app.models.correlation import TrafficObservation, ObservationType


def create_test_observation(
    obs_id: str,
    obs_type: ObservationType,
    timestamp: datetime,
    relay_fp: str = "AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555",
    bytes_transferred: int = 1000000,
    packets: int = 500
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
        packets_count=packets,
        source="test"
    )


def test_time_correlation_explanation():
    """Test that time correlation includes plain English explanation"""
    engine = CorrelationEngine()
    
    # Test very close timestamps
    score, explanation = engine._calculate_time_correlation(0.5)
    assert "nearly simultaneous" in explanation.lower()
    assert score > 95
    
    # Test moderate gap
    score, explanation = engine._calculate_time_correlation(60.0)
    assert "seconds apart" in explanation
    assert "60.0" in explanation
    
    # Test large gap
    score, explanation = engine._calculate_time_correlation(600.0)
    assert "correlation window" in explanation.lower()
    
    print("\nTime Correlation Explanations:")
    print(f"  0.5s: {explanation[:100]}...")
    print(f"  Score: {score:.1f}%")


def test_volume_similarity_explanation():
    """Test that volume similarity includes plain English explanation"""
    engine = CorrelationEngine()
    base_time = datetime.utcnow()
    
    # Test very similar volumes
    entry = create_test_observation("entry-1", ObservationType.ENTRY_OBSERVED, base_time, bytes_transferred=1000000)
    exit_obs = create_test_observation("exit-1", ObservationType.EXIT_OBSERVED, base_time, bytes_transferred=1050000)
    
    score, explanation = engine._calculate_volume_similarity(entry, exit_obs)
    
    assert "MB" in explanation
    assert "similar" in explanation.lower()
    assert score > 90
    
    # Test very different volumes
    exit_diff = create_test_observation("exit-2", ObservationType.EXIT_OBSERVED, base_time, bytes_transferred=5000000)
    score_diff, explanation_diff = engine._calculate_volume_similarity(entry, exit_diff)
    
    assert "difference" in explanation_diff.lower()
    assert score_diff < score
    
    print("\nVolume Similarity Explanations:")
    print(f"  Similar: {explanation[:100]}...")
    print(f"  Different: {explanation_diff[:100]}...")


def test_session_pair_reasoning():
    """Test that session pairs include comprehensive reasoning"""
    engine = CorrelationEngine()
    base_time = datetime.utcnow()
    
    entry = create_test_observation(
        "entry-test",
        ObservationType.ENTRY_OBSERVED,
        base_time,
        bytes_transferred=2000000
    )
    
    exit_obs = create_test_observation(
        "exit-test",
        ObservationType.EXIT_OBSERVED,
        base_time + timedelta(seconds=1.5),
        relay_fp="BBBB2222CCCC3333DDDD4444EEEE5555FFFF6666",
        bytes_transferred=2100000
    )
    
    pairs = engine.correlate_observations([entry], [exit_obs])
    
    assert len(pairs) == 1
    pair = pairs[0]
    
    # Check reasoning exists
    assert pair.reasoning is not None
    assert len(pair.reasoning) > 0
    
    # Check score breakdown exists
    assert pair.score_breakdown is not None
    assert "time_correlation" in pair.score_breakdown
    assert "volume_similarity" in pair.score_breakdown
    
    # Verify explanations are in plain English
    full_reasoning = " ".join(pair.reasoning)
    assert "observation" in full_reasoning.lower()
    assert "%" in full_reasoning  # Should mention percentages
    
    print("\nSession Pair Reasoning:")
    for i, reason in enumerate(pair.reasoning, 1):
        print(f"  {i}. {reason}")
    
    print("\nScore Breakdown:")
    for key, value in pair.score_breakdown.items():
        if isinstance(value, dict):
            print(f"  {key}: {value.get('score', 'N/A'):.1f}% (contribution: {value.get('contribution', 'N/A'):.1f})")
        else:
            print(f"  {key}: {value}")


def test_confidence_levels_explanation():
    """Test that different confidence levels get appropriate explanations"""
    engine = CorrelationEngine()
    base_time = datetime.utcnow()
    
    # High confidence scenario
    entry_high = create_test_observation("entry-high", ObservationType.ENTRY_OBSERVED, base_time, bytes_transferred=1000000)
    exit_high = create_test_observation("exit-high", ObservationType.EXIT_OBSERVED, base_time + timedelta(seconds=0.5), bytes_transferred=1020000)
    
    pairs_high = engine.correlate_observations([entry_high], [exit_high])
    
    # Should produce a correlation (even if not quite 70%)
    assert pairs_high
    assert pairs_high[0].correlation_strength > 60  # Should be reasonably high
    
    # Low confidence scenario
    entry_low = create_test_observation("entry-low", ObservationType.ENTRY_OBSERVED, base_time, bytes_transferred=1000000)
    exit_low = create_test_observation("exit-low", ObservationType.EXIT_OBSERVED, base_time + timedelta(seconds=200), bytes_transferred=5000000)
    
    pairs_low = engine.correlate_observations([entry_low], [exit_low])
    
    # Should be significantly lower than high confidence
    if pairs_low:
        assert pairs_low[0].correlation_strength < pairs_high[0].correlation_strength
        
        print("\nConfidence Level Explanations:")
        print(f"  High ({pairs_high[0].correlation_strength:.1f}%): {pairs_high[0].reasoning[-1]}")
        print(f"  Low ({pairs_low[0].correlation_strength:.1f}%): {pairs_low[0].reasoning[-1]}")
    else:
        print(f"\nLow confidence scenario filtered out (below minimum threshold of 30%)")
        print(f"High confidence: {pairs_high[0].correlation_strength:.1f}%")


def test_reasoning_includes_all_components():
    """Test that reasoning includes all scoring components"""
    engine = CorrelationEngine()
    base_time = datetime.utcnow()
    
    entry = create_test_observation("entry-full", ObservationType.ENTRY_OBSERVED, base_time)
    exit_obs = create_test_observation("exit-full", ObservationType.EXIT_OBSERVED, base_time + timedelta(seconds=2))
    
    pairs = engine.correlate_observations([entry], [exit_obs])
    
    assert len(pairs) == 1
    pair = pairs[0]
    
    reasoning_text = " ".join(pair.reasoning).lower()
    
    # Should mention time correlation
    assert "time" in reasoning_text or "seconds" in reasoning_text
    
    # Should mention volume
    assert "volume" in reasoning_text or "bytes" in reasoning_text or "mb" in reasoning_text
    
    # Should mention overall correlation
    assert "correlation" in reasoning_text
    
    # Should have final assessment
    assert "confidence" in reasoning_text
    
    print("\nComplete Reasoning Chain:")
    for step in pair.reasoning:
        print(f"  → {step[:150]}...")


def test_score_breakdown_structure():
    """Test that score breakdown has correct structure"""
    engine = CorrelationEngine()
    base_time = datetime.utcnow()
    
    entry = create_test_observation("entry-bd", ObservationType.ENTRY_OBSERVED, base_time)
    exit_obs = create_test_observation("exit-bd", ObservationType.EXIT_OBSERVED, base_time + timedelta(seconds=1))
    
    pairs = engine.correlate_observations([entry], [exit_obs])
    
    assert len(pairs) == 1
    breakdown = pairs[0].score_breakdown
    
    # Check structure
    assert "time_correlation" in breakdown
    assert "volume_similarity" in breakdown
    assert "base_correlation" in breakdown
    assert "final_correlation" in breakdown
    
    # Check time correlation details
    time_data = breakdown["time_correlation"]
    assert "score" in time_data
    assert "weight" in time_data
    assert "contribution" in time_data
    assert "reasoning" in time_data
    
    # Verify math
    time_contribution = time_data["score"] * time_data["weight"]
    assert abs(time_contribution - time_data["contribution"]) < 0.01
    
    print("\nScore Breakdown Structure:")
    print(f"  Time: {time_data['score']:.1f}% × {time_data['weight']:.2f} = {time_data['contribution']:.1f}")
    print(f"  Reasoning: {time_data['reasoning'][:100]}...")


def test_guard_hypothesis_explanation():
    """Test that guard hypothesis includes explanation"""
    engine = CorrelationEngine()
    base_time = datetime.utcnow()
    
    guard_fp = "GUARD_FINGERPRINT_1234567890ABCDEF1234567890"
    
    entry = create_test_observation("entry-guard", ObservationType.ENTRY_OBSERVED, base_time, relay_fp=guard_fp)
    exit_obs = create_test_observation("exit-guard", ObservationType.EXIT_OBSERVED, base_time + timedelta(seconds=1))
    
    pairs = engine.correlate_observations([entry], [exit_obs])
    
    assert len(pairs) == 1
    pair = pairs[0]
    
    # Should have guard hypothesis
    assert pair.hypothesized_guard == guard_fp
    
    # Reasoning should mention guard
    reasoning_text = " ".join(pair.reasoning).lower()
    assert "guard" in reasoning_text or "relay" in reasoning_text
    
    print("\nGuard Hypothesis Explanation:")
    guard_reasons = [r for r in pair.reasoning if "guard" in r.lower() or "relay" in r.lower()]
    for reason in guard_reasons:
        print(f"  {reason}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
