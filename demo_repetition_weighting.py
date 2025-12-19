"""
Demonstration of Repeated Observation Weighting

This script demonstrates how the correlation engine increases confidence
when the same patterns are observed multiple times.
"""
import asyncio
from datetime import datetime, timedelta
from app.core.topology import TORTopologyEngine
from app.core.correlation import CorrelationEngine
from app.models.correlation import TrafficObservation, ObservationType


async def demonstrate_repetition_weighting():
    """
    Demonstrate the effect of repeated observation weighting
    """
    print("=" * 80)
    print("DEMONSTRATION: Repeated Observation Weighting")
    print("=" * 80)
    
    # Step 1: Load topology (small set for speed)
    print("\n[Step 1] Loading TOR topology...")
    topology_engine = TORTopologyEngine()
    
    try:
        snapshot = await topology_engine.create_topology_snapshot(limit=50)
        print(f"✓ Loaded {snapshot.total_relays} relays")
        
        # Get some guards and exits for testing
        guards = [r for r in snapshot.relays if r.is_guard][:3]
        exits = [r for r in snapshot.relays if r.is_exit][:3]
        
        print(f"✓ Using {len(guards)} guards and {len(exits)} exits for demo")
        
        # Step 2: Initialize correlation engine
        print("\n[Step 2] Initializing correlation engine with repetition weighting...")
        correlation_engine = CorrelationEngine(topology=snapshot)
        print("✓ Correlation engine ready")
        
        # Step 3: Create observations without repetition
        print("\n[Step 3] Testing correlation WITHOUT repetition...")
        base_time = datetime.utcnow()
        
        guard1 = guards[0]
        exit1 = exits[0]
        
        # Single observation pair
        entry_single = TrafficObservation(
            observation_id="entry-single",
            observation_type=ObservationType.ENTRY_OBSERVED,
            timestamp=base_time,
            duration=60.0,
            observed_ip=guard1.address,
            observed_port=guard1.or_port,
            relay_fingerprint=guard1.fingerprint,
            bytes_transferred=1000000,
            packets_count=500,
            source="demo"
        )
        
        exit_single = TrafficObservation(
            observation_id="exit-single",
            observation_type=ObservationType.EXIT_OBSERVED,
            timestamp=base_time + timedelta(seconds=0.5),
            duration=60.0,
            observed_ip=exit1.address,
            observed_port=exit1.or_port,
            relay_fingerprint=exit1.fingerprint,
            bytes_transferred=1050000,
            packets_count=510,
            source="demo"
        )
        
        pairs_single = correlation_engine.correlate_observations([entry_single], [exit_single])
        
        if pairs_single:
            single_score = pairs_single[0].correlation_strength
            print(f"✓ Single observation correlation: {single_score:.2f}%")
        else:
            print("✗ No correlation found")
            return
        
        # Step 4: Create observations WITH repetition
        print("\n[Step 4] Testing correlation WITH repetition (same pattern 5 times)...")
        
        # Create new correlation engine to reset state
        correlation_engine_repeated = CorrelationEngine(topology=snapshot)
        
        entries = []
        exits = []
        
        # Create 5 observation pairs with the same pattern
        for i in range(5):
            entry = TrafficObservation(
                observation_id=f"entry-repeat-{i}",
                observation_type=ObservationType.ENTRY_OBSERVED,
                timestamp=base_time + timedelta(hours=i),
                duration=60.0,
                observed_ip=guard1.address,
                observed_port=guard1.or_port,
                relay_fingerprint=guard1.fingerprint,
                bytes_transferred=1000000 + (i * 10000),  # Slightly varying volume
                packets_count=500 + i,
                source="demo"
            )
            
            exit_obs = TrafficObservation(
                observation_id=f"exit-repeat-{i}",
                observation_type=ObservationType.EXIT_OBSERVED,
                timestamp=base_time + timedelta(hours=i, seconds=0.5),
                duration=60.0,
                observed_ip=exit1.address,
                observed_port=exit1.or_port,
                relay_fingerprint=exit1.fingerprint,
                bytes_transferred=1050000 + (i * 10000),
                packets_count=510 + i,
                source="demo"
            )
            
            entries.append(entry)
            exits.append(exit_obs)
        
        # Correlate all repeated observations
        pairs_repeated = correlation_engine_repeated.correlate_observations(entries, exits)
        
        print(f"✓ Created {len(pairs_repeated)} session pairs")
        
        # Show progression of scores
        print("\n   Correlation scores by observation number:")
        for i, pair in enumerate(pairs_repeated, 1):
            print(f"   Observation {i}: {pair.correlation_strength:.2f}%")
        
        # Step 5: Compare results
        print("\n[Step 5] Comparison:")
        print(f"   Single observation score:  {single_score:.2f}%")
        
        if len(pairs_repeated) >= 3:
            later_score = pairs_repeated[-1].correlation_strength
            print(f"   After 5 repetitions score: {later_score:.2f}%")
            
            improvement = later_score - single_score
            print(f"   Improvement: {improvement:+.2f}%")
            
            if improvement > 0:
                print(f"\n   ✓ Repetition weighting increased confidence by {improvement:.2f}%!")
            else:
                print(f"\n   ℹ Score already at or near maximum")
        
        # Step 6: Show repetition statistics
        print("\n[Step 6] Repetition Statistics:")
        stats = correlation_engine_repeated.get_repetition_statistics()
        
        if stats["enabled"]:
            print(f"   Unique patterns observed: {stats['total_unique_patterns']}")
            print(f"   Patterns with repetition: {stats['repeated_patterns']}")
            print(f"   Maximum repetitions: {stats['max_repetitions']}")
            print(f"   Average repetitions: {stats['avg_repetitions']}")
            
            print(f"\n   Boost parameters:")
            print(f"   - Min repetitions for boost: {stats['boost_parameters']['min_repetitions']}")
            print(f"   - Boost factor: {stats['boost_parameters']['boost_factor']}")
            print(f"   - Max boost: {stats['boost_parameters']['max_boost']}")
            
            if stats['top_patterns']:
                print(f"\n   Top repeated patterns:")
                for pattern_info in stats['top_patterns'][:3]:
                    print(f"   - {pattern_info['pattern']}: {pattern_info['count']} times")
        
        # Step 7: Explanation
        print("\n" + "=" * 80)
        print("EXPLANATION:")
        print("=" * 80)
        print("""
Repeated observation weighting works by:

1. PATTERN TRACKING
   - Each observation is assigned a pattern key (relay + type + volume bucket)
   - The system tracks how many times each pattern appears

2. BOOST CALCULATION
   - When a pattern is seen multiple times, a boost multiplier is calculated
   - Formula: 1.0 + (log2(repetitions) * boost_factor)
   - Logarithmic scaling provides diminishing returns

3. SCORE ADJUSTMENT
   - Base correlation score is multiplied by the boost
   - Helps distinguish repeated behavior from random noise
   - Capped at maximum boost to prevent over-confidence

4. INVESTIGATIVE VALUE
   - Repeated patterns indicate consistent behavior
   - Same guard used repeatedly (TOR clients typically keep guards for 90 days)
   - Higher confidence in guard hypotheses
   - Better lead prioritization

WHY THIS MATTERS FOR INVESTIGATIONS:
   - TOR users typically use the same guard relay for extended periods
   - Repeated observations of the same guard strengthen attribution
   - Helps filter out coincidental correlations
   - Provides more reliable investigative leads
""")
        
        print("=" * 80)
        print("DEMONSTRATION COMPLETE")
        print("=" * 80)
    
    finally:
        await topology_engine.close()


if __name__ == "__main__":
    asyncio.run(demonstrate_repetition_weighting())
