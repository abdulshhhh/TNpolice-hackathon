"""
Unit tests for TOR Topology Engine
"""
import pytest
from datetime import datetime
from app.core.topology import TORTopologyEngine
from app.models.topology import TORRelay, RelayFlags


@pytest.mark.asyncio
async def test_topology_engine_initialization():
    """Test that topology engine initializes correctly"""
    engine = TORTopologyEngine()
    assert engine is not None
    await engine.close()


@pytest.mark.asyncio
async def test_create_topology_snapshot():
    """Test creating a topology snapshot with limited relays"""
    engine = TORTopologyEngine()
    
    try:
        # Fetch only 10 relays for quick test
        snapshot = await engine.create_topology_snapshot(limit=10)
        
        assert snapshot is not None
        assert snapshot.total_relays > 0
        assert len(snapshot.relays) > 0
        assert snapshot.snapshot_id.startswith("snapshot-")
        
        # Check that we have at least some guards and exits
        guard_count = sum(1 for r in snapshot.relays if r.is_guard)
        exit_count = sum(1 for r in snapshot.relays if r.is_exit)
        
        assert guard_count == snapshot.guard_relays
        assert exit_count == snapshot.exit_relays
        
    finally:
        await engine.close()


@pytest.mark.asyncio
async def test_relay_parsing():
    """Test that relays are parsed with correct attributes"""
    engine = TORTopologyEngine()
    
    try:
        snapshot = await engine.create_topology_snapshot(limit=5)
        
        for relay in snapshot.relays:
            # Check required fields
            assert relay.fingerprint
            assert relay.address
            assert relay.or_port > 0
            
            # Check flags are properly parsed
            assert isinstance(relay.flags, list)
            
            # Check computed fields
            if RelayFlags.GUARD in relay.flags:
                assert relay.is_guard
            
            if RelayFlags.EXIT in relay.flags and RelayFlags.BAD_EXIT not in relay.flags:
                assert relay.is_exit
    
    finally:
        await engine.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
