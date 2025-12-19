"""
Data models for TOR network topology and relay information
Based on official TOR Project relay descriptor specifications
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class RelayFlags(str, Enum):
    """Official TOR relay flags as defined in dir-spec.txt"""
    AUTHORITY = "Authority"
    BAD_EXIT = "BadExit"
    EXIT = "Exit"
    FAST = "Fast"
    GUARD = "Guard"
    HS_DIR = "HSDir"
    RUNNING = "Running"
    STABLE = "Stable"
    VALID = "Valid"
    V2DIR = "V2Dir"


class TORRelay(BaseModel):
    """
    Represents a single TOR relay with its metadata
    Data sourced from TOR consensus and relay descriptors
    """
    # Unique identifiers
    fingerprint: str = Field(..., description="40-character hex fingerprint (SHA-1 of relay's public key)")
    nickname: Optional[str] = Field(None, description="Relay operator-chosen nickname")
    
    # Network information
    address: str = Field(..., description="IPv4 address of the relay")
    or_port: int = Field(..., description="Onion Router protocol port")
    dir_port: Optional[int] = Field(None, description="Directory protocol port")
    
    # Bandwidth capabilities (in bytes/second)
    observed_bandwidth: int = Field(0, description="Measured bandwidth capacity")
    advertised_bandwidth: int = Field(0, description="Self-reported bandwidth")
    consensus_weight: int = Field(0, description="Consensus weight for path selection")
    
    # Relay flags (capabilities and characteristics)
    flags: List[RelayFlags] = Field(default_factory=list, description="Assigned flags by directory authorities")
    
    # Geographic and network information
    country_code: Optional[str] = Field(None, description="Two-letter ISO country code")
    as_number: Optional[int] = Field(None, description="Autonomous System number")
    as_name: Optional[str] = Field(None, description="Autonomous System name/organization")
    
    # Temporal information
    first_seen: datetime = Field(..., description="When relay was first observed")
    last_seen: datetime = Field(..., description="Most recent observation timestamp")
    last_changed_address_or_port: Optional[datetime] = Field(None, description="Last address/port change")
    
    # Version information
    platform: Optional[str] = Field(None, description="TOR version and OS")
    version: Optional[str] = Field(None, description="TOR software version")
    
    # Contact and policy
    contact: Optional[str] = Field(None, description="Operator contact info")
    exit_policy_summary: Optional[Dict[str, List[str]]] = Field(None, description="Exit policy summary")
    
    # Metadata for our system
    snapshot_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When we captured this data")
    is_guard: bool = Field(False, description="Computed: Is this a guard-capable relay?")
    is_exit: bool = Field(False, description="Computed: Is this an exit-capable relay?")
    
    @validator('is_guard', always=True)
    def compute_is_guard(cls, v, values):
        """Determine if relay can serve as guard node"""
        if 'flags' in values:
            return RelayFlags.GUARD in values['flags']
        return v
    
    @validator('is_exit', always=True)
    def compute_is_exit(cls, v, values):
        """Determine if relay can serve as exit node"""
        if 'flags' in values:
            return RelayFlags.EXIT in values['flags'] and RelayFlags.BAD_EXIT not in values['flags']
        return v
    
    class Config:
        use_enum_values = True


class TopologySnapshot(BaseModel):
    """
    A complete snapshot of TOR network topology at a specific time
    Represents the consensus view of the network
    """
    snapshot_id: str = Field(..., description="Unique identifier for this snapshot")
    valid_after: datetime = Field(..., description="Consensus valid-after timestamp")
    valid_until: datetime = Field(..., description="Consensus valid-until timestamp")
    fresh_until: datetime = Field(..., description="Consensus fresh-until timestamp")
    
    total_relays: int = Field(0, description="Total number of relays in this snapshot")
    guard_relays: int = Field(0, description="Number of guard-capable relays")
    exit_relays: int = Field(0, description="Number of exit-capable relays")
    
    relays: List[TORRelay] = Field(default_factory=list, description="All relays in this snapshot")
    
    # Graph statistics
    avg_bandwidth: float = Field(0.0, description="Average relay bandwidth")
    total_bandwidth: int = Field(0, description="Total network bandwidth")
    
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When we created this snapshot")
    
    class Config:
        json_schema_extra = {
            "example": {
                "snapshot_id": "consensus-2025-12-20-12-00-00",
                "valid_after": "2025-12-20T12:00:00Z",
                "total_relays": 7000,
                "guard_relays": 2500,
                "exit_relays": 1200
            }
        }


class RelayEdge(BaseModel):
    """
    Represents a potential path segment in the TOR network
    Used for graph-based analysis
    """
    source_fingerprint: str = Field(..., description="Source relay fingerprint")
    target_fingerprint: str = Field(..., description="Target relay fingerprint")
    edge_type: str = Field(..., description="Type of connection (guard->middle, middle->exit, etc.)")
    probability: float = Field(0.0, description="Computed probability of this path segment")
    
    # Path constraints (why this edge exists or doesn't)
    same_family: bool = Field(False, description="Are these relays in the same family?")
    same_subnet: bool = Field(False, description="Are these relays in the same /16 subnet?")
    valid_path: bool = Field(True, description="Is this a valid path segment per TOR rules?")


class TORCircuit(BaseModel):
    """
    Represents a hypothetical 3-hop TOR circuit
    Used for correlation analysis
    """
    circuit_id: str = Field(..., description="Unique identifier for this circuit hypothesis")
    
    # The three hops
    guard_fingerprint: str = Field(..., description="Entry/Guard relay")
    middle_fingerprint: str = Field(..., description="Middle relay")
    exit_fingerprint: str = Field(..., description="Exit relay")
    
    # Path validation
    is_valid_circuit: bool = Field(True, description="Does this circuit satisfy TOR path selection rules?")
    path_constraints_met: List[str] = Field(default_factory=list, description="Which constraints are satisfied")
    
    # Temporal information
    hypothesized_at: datetime = Field(default_factory=datetime.utcnow, description="When we hypothesized this circuit")
    
    # For correlation analysis
    probability_score: float = Field(0.0, description="Likelihood this circuit was actually used")
