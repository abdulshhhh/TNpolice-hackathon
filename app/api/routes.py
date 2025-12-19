"""
FastAPI Application - Main API Routes

Provides RESTful API for:
- Topology management
- Traffic observation ingestion
- Correlation analysis
- Results retrieval
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from datetime import datetime
import logging

from app.models.topology import TopologySnapshot
from app.models.correlation import TrafficObservation, SessionPair, CorrelationCluster
from app.models.weight_profile import WeightProfile, ProfileType, get_profile, create_custom_profile, PREDEFINED_PROFILES
from app.core import TORTopologyEngine, CorrelationEngine
from app.utils import SyntheticDataGenerator


logger = logging.getLogger(__name__)
router = APIRouter()

# Global state (in production, use proper state management/database)
current_topology: Optional[TopologySnapshot] = None
topology_engine: Optional[TORTopologyEngine] = None
correlation_engine: Optional[CorrelationEngine] = None
stored_observations: List[TrafficObservation] = []
stored_pairs: List[SessionPair] = []
stored_clusters: List[CorrelationCluster] = []


@router.get("/", tags=["General"])
async def root():
    """API root endpoint with system information"""
    return {
        "system": "TOR Metadata Correlation System",
        "version": "1.0.0",
        "purpose": "Law enforcement analytical platform for TOR metadata correlation",
        "status": "operational",
        "legal_notice": "This system analyzes only publicly available TOR relay metadata. "
                       "No deanonymization or traffic decryption is performed.",
        "endpoints": {
            "topology": "/api/topology/*",
            "observations": "/api/observations/*",
            "correlation": "/api/correlation/*",
            "documentation": "/docs"
        }
    }


@router.get("/health", tags=["General"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "topology_loaded": current_topology is not None,
        "total_relays": current_topology.total_relays if current_topology else 0,
        "observations_count": len(stored_observations)
    }


# ============================================================================
# TOPOLOGY ENDPOINTS
# ============================================================================

@router.post("/topology/fetch", response_model=TopologySnapshot, tags=["Topology"])
async def fetch_topology(limit: Optional[int] = None):
    """
    Fetch current TOR network topology from official sources
    
    Args:
        limit: Optional limit on number of relays (for testing)
    
    Returns:
        Complete topology snapshot
    """
    global current_topology, topology_engine, correlation_engine
    
    logger.info(f"Fetching topology (limit={limit})...")
    
    try:
        # Initialize topology engine if needed
        if topology_engine is None:
            topology_engine = TORTopologyEngine()
        
        # Fetch and create snapshot
        snapshot = await topology_engine.create_topology_snapshot(limit=limit)
        
        # Update global state
        current_topology = snapshot
        correlation_engine = CorrelationEngine(topology=snapshot)
        
        logger.info(f"Topology fetched successfully: {snapshot.total_relays} relays")
        
        return snapshot
    
    except Exception as e:
        logger.error(f"Failed to fetch topology: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch topology: {str(e)}"
        )


@router.get("/topology/current", response_model=TopologySnapshot, tags=["Topology"])
async def get_current_topology():
    """Get currently loaded topology snapshot"""
    if current_topology is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No topology loaded. Use POST /topology/fetch to load topology."
        )
    
    return current_topology


@router.get("/topology/snapshots", tags=["Topology"])
async def list_topology_snapshots():
    """List all available topology snapshots"""
    global topology_engine
    
    if topology_engine is None:
        topology_engine = TORTopologyEngine()
    
    snapshots = topology_engine.list_snapshots()
    
    return {
        "snapshots": snapshots,
        "count": len(snapshots)
    }


@router.get("/topology/guards", tags=["Topology"])
async def get_guard_relays(limit: int = 50):
    """Get list of guard-capable relays"""
    if current_topology is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No topology loaded"
        )
    
    guards = [r for r in current_topology.relays if r.is_guard]
    guards.sort(key=lambda r: r.consensus_weight, reverse=True)
    
    return {
        "total_guards": len(guards),
        "guards": guards[:limit]
    }


@router.get("/topology/exits", tags=["Topology"])
async def get_exit_relays(limit: int = 50):
    """Get list of exit-capable relays"""
    if current_topology is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No topology loaded"
        )
    
    exits = [r for r in current_topology.relays if r.is_exit]
    exits.sort(key=lambda r: r.consensus_weight, reverse=True)
    
    return {
        "total_exits": len(exits),
        "exits": exits[:limit]
    }


# ============================================================================
# OBSERVATION ENDPOINTS
# ============================================================================

@router.post("/observations/add", response_model=TrafficObservation, tags=["Observations"])
async def add_observation(observation: TrafficObservation):
    """
    Add a traffic observation
    
    In production, this would validate case numbers and authorization.
    For PoC, accepts any valid observation.
    """
    global stored_observations
    
    logger.info(f"Adding observation: {observation.observation_id}")
    
    stored_observations.append(observation)
    
    return observation


@router.get("/observations/list", response_model=List[TrafficObservation], tags=["Observations"])
async def list_observations(limit: int = 100):
    """List all stored observations"""
    return stored_observations[:limit]


@router.post("/observations/generate-synthetic", tags=["Observations"])
async def generate_synthetic_observations(
    num_sessions: int = 5,
    num_noise: int = 10,
    guard_persistence: bool = True
):
    """
    Generate synthetic observations for testing
    
    Args:
        num_sessions: Number of correlated sessions to generate
        num_noise: Number of uncorrelated noise observations
        guard_persistence: Whether to use persistent guard (realistic)
    """
    global stored_observations, current_topology
    
    if current_topology is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No topology loaded. Fetch topology first."
        )
    
    logger.info(f"Generating {num_sessions} synthetic sessions + {num_noise} noise observations")
    
    generator = SyntheticDataGenerator(current_topology)
    base_time = datetime.utcnow()
    
    # Generate correlated sessions
    entry_obs, exit_obs = generator.generate_user_sessions(
        num_sessions=num_sessions,
        base_time=base_time,
        time_spread_hours=24,
        guard_persistence=guard_persistence
    )
    
    # Generate noise
    noise_entry, noise_exit = generator.generate_noise_observations(
        num_observations=num_noise,
        base_time=base_time,
        time_spread_hours=24
    )
    
    # Store all observations
    all_observations = entry_obs + exit_obs + noise_entry + noise_exit
    stored_observations.extend(all_observations)
    
    return {
        "generated": len(all_observations),
        "correlated_sessions": num_sessions,
        "noise_observations": num_noise * 2,
        "total_observations": len(stored_observations)
    }


# ============================================================================
# CORRELATION ENDPOINTS
# ============================================================================

@router.post("/correlation/analyze", tags=["Correlation"])
async def analyze_correlations():
    """
    Run correlation analysis on stored observations
    
    Identifies potential entry-exit pairs and clusters
    """
    global correlation_engine, stored_observations, stored_pairs, stored_clusters
    
    if correlation_engine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No correlation engine initialized. Load topology first."
        )
    
    if len(stored_observations) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No observations available for correlation"
        )
    
    logger.info(f"Analyzing {len(stored_observations)} observations...")
    
    # Separate entry and exit observations
    entry_obs = [o for o in stored_observations if o.observation_type.value == "entry_observed"]
    exit_obs = [o for o in stored_observations if o.observation_type.value == "exit_observed"]
    
    logger.info(f"Found {len(entry_obs)} entry observations and {len(exit_obs)} exit observations")
    
    # Run correlation
    pairs = correlation_engine.correlate_observations(entry_obs, exit_obs)
    stored_pairs = pairs
    
    # Create clusters
    clusters = correlation_engine.cluster_session_pairs(pairs)
    stored_clusters = clusters
    
    return {
        "observations_analyzed": len(stored_observations),
        "entry_observations": len(entry_obs),
        "exit_observations": len(exit_obs),
        "session_pairs_found": len(pairs),
        "clusters_identified": len(clusters),
        "message": "Correlation analysis complete"
    }


@router.get("/correlation/pairs", response_model=List[SessionPair], tags=["Correlation"])
async def get_session_pairs(min_confidence: float = 0.0, limit: int = 100):
    """
    Get identified session pairs
    
    Args:
        min_confidence: Minimum correlation strength to return
        limit: Maximum number of results
    """
    filtered_pairs = [
        p for p in stored_pairs
        if p.correlation_strength >= min_confidence
    ]
    
    # Sort by correlation strength (highest first)
    filtered_pairs.sort(key=lambda p: p.correlation_strength, reverse=True)
    
    return filtered_pairs[:limit]


@router.get("/correlation/clusters", response_model=List[CorrelationCluster], tags=["Correlation"])
async def get_correlation_clusters(min_confidence: float = 0.0):
    """
    Get identified correlation clusters
    
    Args:
        min_confidence: Minimum cluster confidence to return
    """
    filtered_clusters = [
        c for c in stored_clusters
        if c.cluster_confidence >= min_confidence
    ]
    
    # Sort by confidence (highest first)
    filtered_clusters.sort(key=lambda c: c.cluster_confidence, reverse=True)
    
    return filtered_clusters


@router.get("/correlation/summary", tags=["Correlation"])
async def get_correlation_summary():
    """Get summary statistics of correlation analysis"""
    if len(stored_pairs) == 0:
        return {
            "status": "no_analysis",
            "message": "No correlation analysis has been run yet"
        }
    
    # Calculate statistics
    avg_correlation = sum(p.correlation_strength for p in stored_pairs) / len(stored_pairs)
    high_confidence = sum(1 for p in stored_pairs if p.correlation_strength >= 70)
    medium_confidence = sum(1 for p in stored_pairs if 40 <= p.correlation_strength < 70)
    low_confidence = sum(1 for p in stored_pairs if p.correlation_strength < 40)
    
    return {
        "total_pairs": len(stored_pairs),
        "total_clusters": len(stored_clusters),
        "average_correlation": round(avg_correlation, 2),
        "confidence_distribution": {
            "high_confidence (>=70%)": high_confidence,
            "medium_confidence (40-70%)": medium_confidence,
            "low_confidence (<40%)": low_confidence
        },
        "top_clusters": [
            {
                "cluster_id": c.cluster_id,
                "confidence": c.cluster_confidence,
                "observations": c.observation_count,
                "probable_guards": c.probable_guards
            }
            for c in sorted(stored_clusters, key=lambda x: x.cluster_confidence, reverse=True)[:5]
        ]
    }


@router.get("/correlation/repetition-stats", tags=["Correlation"])
async def get_repetition_statistics():
    """
    Get statistics about repeated observation patterns
    
    Shows how many patterns have been observed multiple times,
    which can increase correlation confidence.
    """
    global correlation_engine
    
    if correlation_engine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No correlation engine initialized. Load topology first."
        )
    
    stats = correlation_engine.get_repetition_statistics()
    
    return {
        "repetition_weighting": stats,
        "explanation": "Repeated observation patterns increase correlation confidence. "
                      "When the same relay/pattern is observed multiple times, "
                      "it strengthens the hypothesis that this is consistent behavior."
    }


@router.get("/correlation/pairs/{pair_id}/reasoning", tags=["Correlation"])
async def get_pair_reasoning(pair_id: str):
    """
    Get detailed plain-English reasoning for a specific session pair
    
    Args:
        pair_id: The ID of the session pair
    
    Returns:
        Detailed reasoning and score breakdown
    """
    global stored_pairs
    
    # Find the pair
    pair = next((p for p in stored_pairs if p.pair_id == pair_id), None)
    
    if pair is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session pair '{pair_id}' not found"
        )
    
    return {
        "pair_id": pair.pair_id,
        "correlation_strength": pair.correlation_strength,
        "reasoning": pair.reasoning,
        "score_breakdown": pair.score_breakdown,
        "observations": {
            "entry": pair.entry_observation_id,
            "exit": pair.exit_observation_id,
            "time_delta_seconds": pair.time_delta
        },
        "hypothesis": {
            "guard_relay": pair.hypothesized_guard,
            "guard_confidence": pair.guard_confidence
        }
    }


# =============================================================================
# Weight Profile Management Endpoints
# =============================================================================

@router.get("/profiles/predefined", tags=["Weight Profiles"])
async def get_predefined_profiles():
    """
    Get all predefined weight profiles
    
    Returns list of standard profiles for common investigation types:
    - standard: Balanced weights (40% time, 30% volume, 30% pattern)
    - time_focused: Prioritizes temporal correlation (60% time)
    - volume_focused: Prioritizes data volume matching (50% volume)
    - pattern_focused: Prioritizes behavioral patterns (50% pattern)
    
    Returns:
        List of predefined WeightProfile objects
    """
    return {
        "profiles": list(PREDEFINED_PROFILES.values()),
        "count": len(PREDEFINED_PROFILES),
        "description": "Predefined weight profiles for common investigation types"
    }


@router.get("/profiles/{profile_type}", tags=["Weight Profiles"])
async def get_profile_by_type(profile_type: str):
    """
    Get a specific predefined weight profile
    
    Args:
        profile_type: One of: standard, time_focused, volume_focused, pattern_focused
    
    Returns:
        WeightProfile object
    """
    try:
        prof_type = ProfileType(profile_type)
        profile = get_profile(prof_type)
        
        return {
            "profile": profile,
            "usage": f"Use this profile by passing it to the correlation engine",
            "example_weights": {
                "time_correlation": profile.weight_time_correlation,
                "volume_similarity": profile.weight_volume_similarity,
                "pattern_similarity": profile.weight_pattern_similarity
            }
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid profile type. Must be one of: {', '.join([pt.value for pt in ProfileType if pt != ProfileType.CUSTOM])}"
        )


@router.post("/profiles/custom", tags=["Weight Profiles"])
async def create_custom_weight_profile(
    profile_id: str,
    profile_name: str,
    weight_time: float,
    weight_volume: float,
    weight_pattern: float,
    case_id: Optional[str] = None,
    created_by: Optional[str] = None,
    description: Optional[str] = None
):
    """
    Create a custom weight profile for a specific investigation
    
    Args:
        profile_id: Unique identifier (e.g., "case-2025-001-custom")
        profile_name: Human-readable name
        weight_time: Time correlation weight (0-1)
        weight_volume: Volume similarity weight (0-1)
        weight_pattern: Pattern similarity weight (0-1)
        case_id: Associated case ID (optional)
        created_by: Investigator email/ID (optional)
        description: Profile description (optional)
    
    Note: Weights must sum to 1.0
    
    Returns:
        Created WeightProfile
    """
    try:
        profile = create_custom_profile(
            profile_id=profile_id,
            profile_name=profile_name,
            weight_time=weight_time,
            weight_volume=weight_volume,
            weight_pattern=weight_pattern,
            case_id=case_id,
            created_by=created_by,
            description=description
        )
        
        return {
            "status": "success",
            "message": "Custom weight profile created",
            "profile": profile,
            "weights_sum": weight_time + weight_volume + weight_pattern
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/correlation/weight-profile", tags=["Correlation"])
async def get_current_weight_profile():
    """
    Get the current weight profile being used by the correlation engine
    
    Returns:
        Current WeightProfile
    """
    global correlation_engine
    
    if correlation_engine is None:
        # Return default profile
        return {
            "status": "no_engine",
            "message": "Correlation engine not initialized. Default profile shown.",
            "profile": get_profile(ProfileType.STANDARD)
        }
    
    return {
        "status": "active",
        "profile": correlation_engine.get_weight_profile(),
        "message": "This profile is currently used for all correlations"
    }


@router.post("/correlation/weight-profile", tags=["Correlation"])
async def update_weight_profile(profile: WeightProfile):
    """
    Update the weight profile for the correlation engine
    
    This affects all future correlation calculations.
    
    Args:
        profile: WeightProfile to use
    
    Returns:
        Confirmation with new profile details
    """
    global correlation_engine
    
    if correlation_engine is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Correlation engine not initialized. Run /correlation/analyze first."
        )
    
    try:
        # Validate weights
        profile.validate_weights_sum()
        
        # Update engine
        correlation_engine.set_weight_profile(profile)
        
        return {
            "status": "success",
            "message": f"Weight profile updated to: {profile.profile_name}",
            "profile": profile,
            "effect": "All future correlations will use these weights"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/correlation/analyze-with-profile", tags=["Correlation"])
async def analyze_with_custom_profile(
    profile_type: Optional[str] = "standard",
    custom_profile: Optional[WeightProfile] = None
):
    """
    Run correlation analysis with a specific weight profile
    
    This creates a new correlation engine with the specified profile
    and analyzes all stored observations.
    
    Args:
        profile_type: Predefined profile type (standard, time_focused, etc.)
        custom_profile: Custom WeightProfile (overrides profile_type if provided)
    
    Returns:
        Correlation results with profile information
    """
    global stored_observations, correlation_engine, stored_pairs, current_topology
    
    if not stored_observations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No observations available. Add observations first via /observations/add"
        )
    
    # Get profile
    if custom_profile:
        profile = custom_profile
        profile.validate_weights_sum()
    else:
        try:
            prof_type = ProfileType(profile_type)
            profile = get_profile(prof_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid profile type: {profile_type}"
            )
    
    # Create new correlation engine with profile
    correlation_engine = CorrelationEngine(topology=current_topology, weight_profile=profile)
    
    # Separate entry and exit observations
    entry_obs = [obs for obs in stored_observations if obs.observation_type == "entry"]
    exit_obs = [obs for obs in stored_observations if obs.observation_type == "exit"]
    
    # Run correlation
    pairs = correlation_engine.correlate_observations(entry_obs, exit_obs)
    stored_pairs = pairs
    
    return {
        "status": "success",
        "profile_used": {
            "name": profile.profile_name,
            "type": profile.profile_type,
            "weights": {
                "time": profile.weight_time_correlation,
                "volume": profile.weight_volume_similarity,
                "pattern": profile.weight_pattern_similarity
            }
        },
        "results": {
            "session_pairs_found": len(pairs),
            "entry_observations": len(entry_obs),
            "exit_observations": len(exit_obs)
        },
        "top_correlations": sorted(
            [{"pair_id": p.pair_id, "strength": p.correlation_strength} for p in pairs],
            key=lambda x: x["strength"],
            reverse=True
        )[:10]
    }
