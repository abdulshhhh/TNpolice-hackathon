"""
Demonstration of Explainability Features

Shows how the system generates plain English explanations for confidence scores.
"""
from datetime import datetime, timedelta
from app.core.correlation import CorrelationEngine
from app.models.correlation import TrafficObservation, ObservationType


def print_separator(title: str):
    """Print a formatted separator"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def create_demo_observation(
    obs_id: str,
    obs_type: ObservationType,
    timestamp: datetime,
    bytes_mb: float = 1.5,
    relay_fp: str = None
):
    """Create a demo traffic observation"""
    return TrafficObservation(
        observation_id=obs_id,
        observation_type=obs_type,
        timestamp=timestamp,
        duration=60.0,
        observed_ip="203.0.113.42",
        observed_port=9001,
        relay_fingerprint=relay_fp or "DEMO" + "A" * 36,
        bytes_transferred=int(bytes_mb * 1024 * 1024),
        packets_count=int(bytes_mb * 1000),
        source="demonstration"
    )


def demo_high_confidence_scenario():
    """Demonstrate high confidence correlation with explanations"""
    print_separator("Scenario 1: HIGH CONFIDENCE CORRELATION")
    
    engine = CorrelationEngine()
    base_time = datetime.utcnow()
    
    # Very tight timing and volume match
    entry = create_demo_observation(
        "entry-001",
        ObservationType.ENTRY_OBSERVED,
        base_time,
        bytes_mb=2.5,
        relay_fp="GUARD" + "B" * 35
    )
    
    exit_obs = create_demo_observation(
        "exit-001",
        ObservationType.EXIT_OBSERVED,
        base_time + timedelta(seconds=0.8),
        bytes_mb=2.52
    )
    
    pairs = engine.correlate_observations([entry], [exit_obs])
    
    if pairs:
        pair = pairs[0]
        print(f"\n📊 Correlation Strength: {pair.correlation_strength:.1f}%")
        print(f"🎯 Hypothesized Guard: {pair.hypothesized_guard[:20]}...")
        print(f"⚖️  Confidence Level: {'HIGH' if pair.correlation_strength >= 70 else 'MEDIUM' if pair.correlation_strength >= 50 else 'LOW'}")
        
        print("\n📝 REASONING CHAIN:")
        for i, reason in enumerate(pair.reasoning, 1):
            print(f"\n  Step {i}:")
            print(f"    {reason}")
        
        print("\n📈 DETAILED SCORE BREAKDOWN:")
        for component, data in pair.score_breakdown.items():
            if isinstance(data, dict) and "score" in data:
                print(f"\n  {component.replace('_', ' ').title()}:")
                print(f"    Score: {data['score']:.1f}%")
                print(f"    Weight: {data['weight']:.2f}")
                print(f"    Contribution: {data['contribution']:.1f}")
                print(f"    Reasoning: {data['reasoning']}")
            else:
                print(f"\n  {component.replace('_', ' ').title()}: {data}")


def demo_medium_confidence_scenario():
    """Demonstrate medium confidence with explanations"""
    print_separator("Scenario 2: MEDIUM CONFIDENCE CORRELATION")
    
    engine = CorrelationEngine()
    base_time = datetime.utcnow()
    
    # Moderate timing gap, similar volumes
    entry = create_demo_observation(
        "entry-002",
        ObservationType.ENTRY_OBSERVED,
        base_time,
        bytes_mb=1.8
    )
    
    exit_obs = create_demo_observation(
        "exit-002",
        ObservationType.EXIT_OBSERVED,
        base_time + timedelta(seconds=45),
        bytes_mb=1.9
    )
    
    pairs = engine.correlate_observations([entry], [exit_obs])
    
    if pairs:
        pair = pairs[0]
        print(f"\n📊 Correlation Strength: {pair.correlation_strength:.1f}%")
        print(f"⚖️  Confidence Level: MEDIUM")
        
        print("\n📝 KEY REASONING POINTS:")
        for reason in pair.reasoning:
            if "time" in reason.lower() or "volume" in reason.lower() or "correlation" in reason.lower():
                print(f"  • {reason}")


def demo_low_confidence_scenario():
    """Demonstrate low confidence with explanations"""
    print_separator("Scenario 3: LOW CONFIDENCE CORRELATION")
    
    engine = CorrelationEngine()
    base_time = datetime.utcnow()
    
    # Large timing gap, different volumes
    entry = create_demo_observation(
        "entry-003",
        ObservationType.ENTRY_OBSERVED,
        base_time,
        bytes_mb=1.2
    )
    
    exit_obs = create_demo_observation(
        "exit-003",
        ObservationType.EXIT_OBSERVED,
        base_time + timedelta(seconds=180),
        bytes_mb=4.5
    )
    
    pairs = engine.correlate_observations([entry], [exit_obs])
    
    if pairs:
        pair = pairs[0]
        print(f"\n📊 Correlation Strength: {pair.correlation_strength:.1f}%")
        print(f"⚖️  Confidence Level: LOW")
        print(f"⚠️  Warning: This correlation is weak and should be treated with caution")
        
        print("\n📝 EXPLANATION FOR LOW CONFIDENCE:")
        for reason in pair.reasoning:
            print(f"  • {reason}")
    else:
        print(f"\n⚠️  No correlation found above minimum threshold (30%)")
        print(f"   Time gap: 180 seconds, Volume difference: {((4.5 - 1.2) / 1.2 * 100):.1f}%")
        print(f"   This demonstrates the system's ability to reject weak correlations.")


def demo_repetition_weighting():
    """Demonstrate repetition weighting with explanations"""
    print_separator("Scenario 4: REPEATED OBSERVATION PATTERN")
    
    from config import settings
    
    if not settings.ENABLE_REPETITION_WEIGHTING:
        print("\n⚠️  Repetition weighting is disabled in config.py")
        print("   Enable it by setting ENABLE_REPETITION_WEIGHTING = True")
        return
    
    engine = CorrelationEngine()
    base_time = datetime.utcnow()
    
    guard_fp = "PERSISTENT_GUARD" + "C" * 24
    
    # Create multiple observations with same guard
    entries = []
    exits = []
    
    for i in range(5):
        offset = timedelta(hours=i)
        
        entry = create_demo_observation(
            f"entry-repeat-{i}",
            ObservationType.ENTRY_OBSERVED,
            base_time + offset,
            bytes_mb=2.0,
            relay_fp=guard_fp
        )
        entries.append(entry)
        
        exit_obs = create_demo_observation(
            f"exit-repeat-{i}",
            ObservationType.EXIT_OBSERVED,
            base_time + offset + timedelta(seconds=1),
            bytes_mb=2.1
        )
        exits.append(exit_obs)
    
    # Correlate first observation
    pairs_first = engine.correlate_observations([entries[0]], [exits[0]])
    
    print("\n🔍 FIRST OBSERVATION:")
    if pairs_first:
        print(f"  Base Correlation: {pairs_first[0].score_breakdown.get('base_correlation', 0):.1f}%")
        print(f"  Final Correlation: {pairs_first[0].correlation_strength:.1f}%")
        print(f"  Repetition Boost: None (first occurrence)")
    
    # Correlate later observations to see boost
    all_pairs = []
    for i in range(1, 5):
        pairs = engine.correlate_observations(entries[:i+1], exits[:i+1])
        if pairs:
            latest = [p for p in pairs if p.entry_observation_id == entries[i].observation_id]
            if latest:
                all_pairs.append(latest[0])
    
    if all_pairs:
        print("\n📈 REPETITION WEIGHTING EFFECT:")
        for i, pair in enumerate(all_pairs, 2):
            base = pair.score_breakdown.get("base_correlation", 0)
            final = pair.correlation_strength
            boost = final - base
            
            print(f"\n  Observation #{i}:")
            print(f"    Base Score: {base:.1f}%")
            print(f"    Repetition Boost: +{boost:.1f}%")
            print(f"    Final Score: {final:.1f}%")
            
            # Show repetition reasoning
            rep_reason = [r for r in pair.reasoning if "repeated" in r.lower() or "pattern" in r.lower()]
            if rep_reason:
                print(f"    Explanation: {rep_reason[0]}")
    
    # Show statistics
    stats = engine.get_repetition_statistics()
    print("\n📊 REPETITION STATISTICS:")
    print(f"  Total Patterns Tracked: {stats['total_patterns']}")
    print(f"  Most Common Pattern: {stats.get('most_common_pattern_count', 0)} occurrences")


def demo_api_usage():
    """Show how to access reasoning through API"""
    print_separator("API USAGE EXAMPLE")
    
    print("""
To access explainability data through the API:

1️⃣  GET /correlation/pairs
   Returns all session pairs with basic info

2️⃣  GET /correlation/pairs/{pair_id}/reasoning
   Returns detailed reasoning and score breakdown for specific pair

Example Response:
{
  "pair_id": "entry-001_exit-001",
  "correlation_strength": 92.5,
  "reasoning": [
    "Entry and exit observations are nearly simultaneous (0.80 seconds apart)...",
    "Entry traffic: 2.50MB, Exit traffic: 2.52MB. Volumes are nearly identical...",
    "Composite correlation score: 92.5% (weighted average of all signals)",
    "Guard hypothesis: Entry relay GUARDBBBBBBBBBBBBBBB... (probability: 85%)"
  ],
  "score_breakdown": {
    "time_correlation": {
      "score": 98.7,
      "weight": 0.40,
      "contribution": 39.5,
      "reasoning": "Entry and exit observations are nearly simultaneous..."
    },
    "volume_similarity": {
      "score": 99.2,
      "weight": 0.35,
      "contribution": 34.7,
      "reasoning": "Entry traffic: 2.50MB, Exit traffic: 2.52MB..."
    },
    ...
  }
}

3️⃣  GET /correlation/repetition/statistics
   Returns statistics about repeated observation patterns
    """)


def main():
    """Run all demonstrations"""
    print("\n")
    print("=" * 80)
    print(" " * 20 + "EXPLAINABILITY DEMONSTRATION" + " " * 32)
    print(" " * 15 + "TN Police TOR Metadata Correlation" + " " * 30)
    print("=" * 80)
    
    demo_high_confidence_scenario()
    demo_medium_confidence_scenario()
    demo_low_confidence_scenario()
    demo_repetition_weighting()
    demo_api_usage()
    
    print("\n" + "=" * 80)
    print("  DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\n💡 All confidence scores include detailed plain English justifications")
    print("📊 Score breakdowns show contribution of each signal")
    print("🔍 Enables full auditability and transparency for legal proceedings\n")


if __name__ == "__main__":
    main()
