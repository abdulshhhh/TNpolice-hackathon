"""
Synthetic data generator for testing and demonstration

Generates realistic TOR traffic observations for testing the correlation engine.
This is for PoC demonstration - in production, data would come from actual
network monitoring (with proper legal authorization).
"""
import random
import uuid
from datetime import datetime, timedelta
from typing import List

from app.models.correlation import TrafficObservation, ObservationType
from app.models.topology import TopologySnapshot


class SyntheticDataGenerator:
    """
    Generates synthetic TOR traffic observations
    
    Creates realistic test data that mimics actual TOR sessions:
    - Entry and exit observations with correlated timestamps
    - Realistic bandwidth patterns
    - Guard node persistence
    """
    
    def __init__(self, topology: TopologySnapshot):
        self.topology = topology
        self.guards = [r for r in topology.relays if r.is_guard]
        self.exits = [r for r in topology.relays if r.is_exit]
    
    def generate_session(
        self,
        base_time: datetime,
        guard_fingerprint: str,
        exit_fingerprint: str,
        duration: float = 60.0
    ) -> tuple[TrafficObservation, TrafficObservation]:
        """
        Generate a pair of correlated entry/exit observations
        
        Args:
            base_time: Base timestamp for the session
            guard_fingerprint: Fingerprint of guard relay
            exit_fingerprint: Fingerprint of exit relay
            duration: Session duration in seconds
        
        Returns:
            Tuple of (entry_observation, exit_observation)
        """
        # Session ID for correlation
        session_id = str(uuid.uuid4())[:8]
        
        # Entry observation (at guard)
        entry_time = base_time
        entry_bytes = random.randint(50000, 5000000)  # 50KB to 5MB
        
        entry_obs = TrafficObservation(
            observation_id=f"entry-{session_id}",
            observation_type=ObservationType.ENTRY_OBSERVED,
            timestamp=entry_time,
            duration=duration,
            observed_ip=self._get_relay_ip(guard_fingerprint),
            observed_port=random.randint(40000, 65000),
            relay_fingerprint=guard_fingerprint,
            bytes_transferred=entry_bytes,
            packets_count=random.randint(100, 1000),
            source="synthetic",
            notes=f"Synthetic session {session_id}"
        )
        
        # Exit observation (at exit relay)
        # Add slight timing variation (TOR circuit overhead)
        exit_time = entry_time + timedelta(seconds=random.uniform(0.1, 2.0))
        exit_bytes = int(entry_bytes * random.uniform(0.95, 1.05))  # Similar but not exact
        
        exit_obs = TrafficObservation(
            observation_id=f"exit-{session_id}",
            observation_type=ObservationType.EXIT_OBSERVED,
            timestamp=exit_time,
            duration=duration,
            observed_ip=self._get_relay_ip(exit_fingerprint),
            observed_port=random.randint(40000, 65000),
            relay_fingerprint=exit_fingerprint,
            bytes_transferred=exit_bytes,
            packets_count=random.randint(100, 1000),
            source="synthetic",
            notes=f"Synthetic session {session_id}"
        )
        
        return entry_obs, exit_obs
    
    def generate_user_sessions(
        self,
        num_sessions: int,
        base_time: datetime,
        time_spread_hours: int = 24,
        guard_persistence: bool = True
    ) -> tuple[List[TrafficObservation], List[TrafficObservation]]:
        """
        Generate multiple sessions simulating a single user
        
        Args:
            num_sessions: Number of sessions to generate
            base_time: Starting time
            time_spread_hours: Spread sessions over this many hours
            guard_persistence: If True, user keeps the same guard (realistic)
        
        Returns:
            Tuple of (entry_observations, exit_observations)
        """
        entry_observations = []
        exit_observations = []
        
        # Select a persistent guard if enabled
        persistent_guard = random.choice(self.guards).fingerprint if guard_persistence else None
        
        for i in range(num_sessions):
            # Random time within spread
            session_time = base_time + timedelta(hours=random.uniform(0, time_spread_hours))
            
            # Select relays
            guard = persistent_guard if persistent_guard else random.choice(self.guards).fingerprint
            exit_relay = random.choice(self.exits).fingerprint
            
            # Generate session
            entry_obs, exit_obs = self.generate_session(
                session_time,
                guard,
                exit_relay,
                duration=random.uniform(30.0, 300.0)
            )
            
            entry_observations.append(entry_obs)
            exit_observations.append(exit_obs)
        
        return entry_observations, exit_observations
    
    def generate_noise_observations(
        self,
        num_observations: int,
        base_time: datetime,
        time_spread_hours: int = 24
    ) -> tuple[List[TrafficObservation], List[TrafficObservation]]:
        """
        Generate uncorrelated noise observations
        
        These represent other users' traffic that should NOT correlate
        """
        entry_observations = []
        exit_observations = []
        
        for i in range(num_observations):
            session_time = base_time + timedelta(hours=random.uniform(0, time_spread_hours))
            
            guard = random.choice(self.guards).fingerprint
            exit_relay = random.choice(self.exits).fingerprint
            
            # Generate observations but with random time offsets (no correlation)
            entry_obs, _ = self.generate_session(session_time, guard, exit_relay)
            
            # Exit observation at completely different time
            exit_time = base_time + timedelta(hours=random.uniform(0, time_spread_hours))
            _, exit_obs = self.generate_session(exit_time, guard, exit_relay)
            
            entry_observations.append(entry_obs)
            exit_observations.append(exit_obs)
        
        return entry_observations, exit_observations
    
    def _get_relay_ip(self, fingerprint: str) -> str:
        """Get IP address for a relay fingerprint"""
        for relay in self.topology.relays:
            if relay.fingerprint == fingerprint:
                return relay.address
        return "0.0.0.0"
