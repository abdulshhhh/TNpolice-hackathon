"""
Integration test demonstrating the complete workflow
"""
import pytest
import asyncio
from datetime import datetime
from app.core.topology import TORTopologyEngine, TORGraphAnalyzer
from app.core.correlation import CorrelationEngine
from app.utils import SyntheticDataGenerator


@pytest.mark.asyncio
async def test_complete_workflow():
    """
    Test the complete analysis workflow:
    1. Fetch topology
    2. Generate synthetic data
    3. Run correlation analysis
    4. Verify results
    """
    print("\n" + "=" * 80)
    print("INTEGRATION TEST: Complete Workflow")
    print("=" * 80)
    
    # Step 1: Fetch topology
    print("\n[1] Fetching TOR topology...")
    topology_engine = TORTopologyEngine()
    
    try:
        snapshot = await topology_engine.create_topology_snapshot(limit=50)
        print(f"    ✓ Loaded {snapshot.total_relays} relays")
        print(f"    ✓ {snapshot.guard_relays} guards, {snapshot.exit_relays} exits")
        
        assert snapshot.total_relays > 0
        assert snapshot.guard_relays > 0
        assert snapshot.exit_relays > 0
        
        # Step 2: Generate synthetic data
        print("\n[2] Generating synthetic observations...")
        generator = SyntheticDataGenerator(snapshot)
        
        # Generate correlated sessions (same user)
        entry_obs, exit_obs = generator.generate_user_sessions(
            num_sessions=5,
            base_time=datetime.utcnow(),
            time_spread_hours=24,
            guard_persistence=True
        )
        
        print(f"    ✓ Generated {len(entry_obs)} entry observations")
        print(f"    ✓ Generated {len(exit_obs)} exit observations")
        
        assert len(entry_obs) == 5
        assert len(exit_obs) == 5
        
        # Step 3: Run correlation analysis
        print("\n[3] Running correlation analysis...")
        correlation_engine = CorrelationEngine(topology=snapshot)
        
        pairs = correlation_engine.correlate_observations(entry_obs, exit_obs)
        print(f"    ✓ Found {len(pairs)} session pairs")
        
        assert len(pairs) > 0
        
        # Show top pairs
        pairs_sorted = sorted(pairs, key=lambda p: p.correlation_strength, reverse=True)
        print("\n    Top correlated pairs:")
        for i, pair in enumerate(pairs_sorted[:3], 1):
            print(f"      {i}. {pair.pair_id}: {pair.correlation_strength:.1f}% confidence")
            print(f"         Time delta: {pair.time_delta:.2f}s")
            if pair.hypothesized_guard:
                print(f"         Hypothesized guard: {pair.hypothesized_guard[:16]}...")
        
        # Step 4: Create clusters
        print("\n[4] Identifying correlation clusters...")
        clusters = correlation_engine.cluster_session_pairs(pairs)
        print(f"    ✓ Identified {len(clusters)} clusters")
        
        if len(clusters) > 0:
            cluster = clusters[0]
            print(f"\n    Top cluster: {cluster.cluster_id}")
            print(f"      Observations: {cluster.observation_count}")
            print(f"      Confidence: {cluster.cluster_confidence:.1f}%")
            print(f"      Guard persistence: {cluster.guard_persistence_score:.1f}%")
            print(f"      Reasoning:")
            for reason in cluster.reasoning:
                print(f"        - {reason}")
        
        # Step 5: Graph analysis
        print("\n[5] Running graph analysis...")
        graph_analyzer = TORGraphAnalyzer(snapshot)
        
        guards = graph_analyzer.get_possible_guards()
        print(f"    ✓ {len(guards)} possible guard relays")
        
        if len(guards) > 0:
            top_guard = guards[0]
            probability = graph_analyzer.estimate_guard_selection_probability(
                top_guard.fingerprint
            )
            print(f"    ✓ Top guard selection probability: {probability:.2f}%")
        
        print("\n" + "=" * 80)
        print("INTEGRATION TEST: SUCCESS")
        print("=" * 80)
        
    finally:
        await topology_engine.close()


if __name__ == "__main__":
    asyncio.run(test_complete_workflow())
