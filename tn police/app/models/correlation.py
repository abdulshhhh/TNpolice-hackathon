"""
Data models for traffic observations and correlation analysis
Metadata-only, no payload inspection
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ObservationType(str, Enum):
    """Type of traffic observation"""
    ENTRY_OBSERVED = "entry_observed"  # Observed traffic entering TOR
    EXIT_OBSERVED = "exit_observed"    # Observed traffic exiting TOR
    SYNTHETIC = "synthetic"             # Simulated data for testing


class TrafficObservation(BaseModel):
    """
    A single observation of TOR traffic metadata
    
    CRITICAL: This contains ONLY timing and metadata - no payload, no content
    This is analogous to "call detail records" in telecom - when, where, how much
    """
    observation_id: str = Field(..., description="Unique identifier for this observation")
    observation_type: ObservationType = Field(..., description="Type of observation")
    
    # Temporal information (the most critical data for correlation)
    timestamp: datetime = Field(..., description="Precise timestamp of observation")
    duration: Optional[float] = Field(None, description="Duration of observed session (seconds)")
    
    # Network metadata (what can be observed externally)
    observed_ip: str = Field(..., description="IP address where traffic was observed")
    observed_port: Optional[int] = Field(None, description="Port where traffic was observed")
    
    # For entry observations: this might be a guard relay IP
    # For exit observations: this might be an exit relay IP
    relay_fingerprint: Optional[str] = Field(None, description="If relay is known, its fingerprint")
    
    # Traffic characteristics (metadata only, no payload)
    bytes_transferred: Optional[int] = Field(None, description="Total bytes observed")
    packets_count: Optional[int] = Field(None, description="Number of packets observed")
    
    # Timing patterns (for correlation)
    inter_packet_timings: Optional[List[float]] = Field(None, description="Packet timing patterns (milliseconds)")
    
    # Case tracking (for legal compliance)
    case_number: Optional[str] = Field(None, description="Investigation case number")
    investigator_id: Optional[str] = Field(None, description="Authorized investigator ID")
    
    # Metadata
    source: str = Field("manual", description="Source of this observation (pcap, netflow, synthetic, etc.)")
    notes: Optional[str] = Field(None, description="Investigator notes")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When observation was recorded")
    
    class Config:
        use_enum_values = True


class SessionPair(BaseModel):
    """
    A pair of observations that might represent the same TOR session
    (entry point + exit point correlation hypothesis)
    """
    pair_id: str = Field(..., description="Unique identifier for this session pair")
    
    # The two observations being correlated
    entry_observation_id: str = Field(..., description="Entry observation ID")
    exit_observation_id: str = Field(..., description="Exit observation ID")
    
    # Temporal correlation metrics
    time_delta: float = Field(..., description="Time difference between observations (seconds)")
    time_correlation_score: float = Field(0.0, description="How well timestamps correlate (0-100)")
    
    # Pattern correlation metrics
    pattern_similarity: Optional[float] = Field(None, description="Timing pattern similarity (0-100)")
    volume_similarity: Optional[float] = Field(None, description="Traffic volume similarity (0-100)")
    
    # Guard node hypothesis
    hypothesized_guard: Optional[str] = Field(None, description="Hypothesized guard relay fingerprint")
    guard_confidence: float = Field(0.0, description="Confidence in guard hypothesis (0-100)")
    
    # Overall correlation
    correlation_strength: float = Field(0.0, description="Overall correlation strength (0-100)")
    
    # Explainability - Plain English reasoning
    reasoning: List[str] = Field(default_factory=list, description="Step-by-step explanation of score calculation")
    score_breakdown: Optional[Dict[str, Any]] = Field(None, description="Detailed breakdown of score components")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When correlation was computed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "pair_id": "pair-001",
                "time_delta": 0.5,
                "time_correlation_score": 85.0,
                "correlation_strength": 72.5
            }
        }


class CorrelationCluster(BaseModel):
    """
    A cluster of multiple observations that appear related
    Indicates repeated behavior patterns (e.g., same user, same guard)
    """
    cluster_id: str = Field(..., description="Unique identifier for this cluster")
    
    # Observations in this cluster
    observation_ids: List[str] = Field(default_factory=list, description="All related observations")
    session_pair_ids: List[str] = Field(default_factory=list, description="All session pairs in cluster")
    
    # Temporal span
    first_observation: datetime = Field(..., description="Earliest observation in cluster")
    last_observation: datetime = Field(..., description="Latest observation in cluster")
    observation_count: int = Field(0, description="Number of observations in cluster")
    
    # Pattern characteristics
    avg_time_between_observations: Optional[float] = Field(None, description="Average time between observations")
    consistency_score: float = Field(0.0, description="How consistent the pattern is (0-100)")
    
    # Guard node inference
    probable_guards: List[str] = Field(default_factory=list, description="List of probable guard fingerprints")
    guard_persistence_score: float = Field(0.0, description="How persistent guard usage is (0-100)")
    
    # Overall cluster strength
    cluster_confidence: float = Field(0.0, description="Confidence that this is a real pattern (0-100)")
    
    # Reasoning and explainability
    reasoning: List[str] = Field(default_factory=list, description="Why this cluster was formed")
    
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When cluster was identified")
