"""
Weight Profile Models

Configurable weight profiles for different investigation types.
Allows customization of correlation scoring weights per case.
"""
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class ProfileType(str, Enum):
    """Predefined investigation profile types"""
    STANDARD = "standard"  # Balanced weights for general investigations
    TIME_FOCUSED = "time_focused"  # Prioritize temporal correlation
    VOLUME_FOCUSED = "volume_focused"  # Prioritize data volume matching
    PATTERN_FOCUSED = "pattern_focused"  # Prioritize behavioral patterns
    CUSTOM = "custom"  # User-defined weights


class WeightProfile(BaseModel):
    """
    Correlation weight profile for an investigation
    
    Defines how different signals are weighted in correlation scoring.
    Weights must sum to 1.0 for proper probabilistic interpretation.
    """
    profile_id: str
    profile_name: str
    profile_type: ProfileType
    
    # Correlation weights (must sum to 1.0)
    weight_time_correlation: float = 0.40  # Temporal proximity weight
    weight_volume_similarity: float = 0.30  # Data volume matching weight
    weight_pattern_similarity: float = 0.30  # Behavioral pattern weight
    
    # Metadata
    case_id: Optional[str] = None  # Associated case/investigation
    created_by: Optional[str] = None  # Investigator who created profile
    created_at: Optional[datetime] = None
    description: Optional[str] = None
    
    @model_validator(mode='after')
    def set_defaults(self):
        """Set default created_at if not provided"""
        if self.created_at is None:
            self.created_at = datetime.now()
        return self
    
    @field_validator('weight_time_correlation', 'weight_volume_similarity', 'weight_pattern_similarity')
    @classmethod
    def validate_weight_range(cls, v):
        """Ensure weights are between 0 and 1"""
        if not 0 <= v <= 1:
            raise ValueError(f"Weight must be between 0 and 1, got {v}")
        return v
    
    def validate_weights_sum(self) -> bool:
        """
        Validate that all weights sum to 1.0
        
        Returns:
            True if weights sum to 1.0 (within tolerance)
        
        Raises:
            ValueError if weights don't sum to 1.0
        """
        total = (
            self.weight_time_correlation +
            self.weight_volume_similarity +
            self.weight_pattern_similarity
        )
        
        # Allow small floating-point tolerance
        if not abs(total - 1.0) < 0.0001:
            raise ValueError(
                f"Weights must sum to 1.0, got {total:.4f}. "
                f"Time: {self.weight_time_correlation}, "
                f"Volume: {self.weight_volume_similarity}, "
                f"Pattern: {self.weight_pattern_similarity}"
            )
        
        return True
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": "case-2025-001-standard",
                "profile_name": "Case 2025-001 Standard Profile",
                "profile_type": "standard",
                "weight_time_correlation": 0.40,
                "weight_volume_similarity": 0.30,
                "weight_pattern_similarity": 0.30,
                "case_id": "CASE-2025-001",
                "created_by": "inv.sharma@tnpolice.gov.in",
                "description": "Balanced weights for narcotics trafficking investigation"
            }
        }


# Predefined weight profiles for common investigation types
PREDEFINED_PROFILES = {
    ProfileType.STANDARD: WeightProfile(
        profile_id="standard",
        profile_name="Standard Balanced Profile",
        profile_type=ProfileType.STANDARD,
        weight_time_correlation=0.40,
        weight_volume_similarity=0.30,
        weight_pattern_similarity=0.30,
        description="Balanced weights suitable for most investigations. Equal consideration of all signals."
    ),
    
    ProfileType.TIME_FOCUSED: WeightProfile(
        profile_id="time-focused",
        profile_name="Time-Focused Profile",
        profile_type=ProfileType.TIME_FOCUSED,
        weight_time_correlation=0.60,
        weight_volume_similarity=0.20,
        weight_pattern_similarity=0.20,
        description="Prioritizes temporal correlation. Use when precise timing is critical (e.g., coordinated attacks)."
    ),
    
    ProfileType.VOLUME_FOCUSED: WeightProfile(
        profile_id="volume-focused",
        profile_name="Volume-Focused Profile",
        profile_type=ProfileType.VOLUME_FOCUSED,
        weight_time_correlation=0.25,
        weight_volume_similarity=0.50,
        weight_pattern_similarity=0.25,
        description="Prioritizes data volume matching. Use for data exfiltration or large file transfer cases."
    ),
    
    ProfileType.PATTERN_FOCUSED: WeightProfile(
        profile_id="pattern-focused",
        profile_name="Pattern-Focused Profile",
        profile_type=ProfileType.PATTERN_FOCUSED,
        weight_time_correlation=0.25,
        weight_volume_similarity=0.25,
        weight_pattern_similarity=0.50,
        description="Prioritizes behavioral patterns. Use for habitual offenders or long-term surveillance."
    ),
}


def get_profile(profile_type: ProfileType) -> WeightProfile:
    """
    Get a predefined weight profile
    
    Args:
        profile_type: Type of profile to retrieve
    
    Returns:
        WeightProfile instance
    """
    return PREDEFINED_PROFILES[profile_type]


def create_custom_profile(
    profile_id: str,
    profile_name: str,
    weight_time: float,
    weight_volume: float,
    weight_pattern: float,
    case_id: Optional[str] = None,
    created_by: Optional[str] = None,
    description: Optional[str] = None
) -> WeightProfile:
    """
    Create a custom weight profile
    
    Args:
        profile_id: Unique identifier
        profile_name: Human-readable name
        weight_time: Time correlation weight (0-1)
        weight_volume: Volume similarity weight (0-1)
        weight_pattern: Pattern similarity weight (0-1)
        case_id: Associated case ID
        created_by: Investigator email/ID
        description: Profile description
    
    Returns:
        WeightProfile instance
    
    Raises:
        ValueError: If weights don't sum to 1.0 or are out of range
    """
    profile = WeightProfile(
        profile_id=profile_id,
        profile_name=profile_name,
        profile_type=ProfileType.CUSTOM,
        weight_time_correlation=weight_time,
        weight_volume_similarity=weight_volume,
        weight_pattern_similarity=weight_pattern,
        case_id=case_id,
        created_by=created_by,
        description=description
    )
    
    # Validate weights sum to 1.0
    profile.validate_weights_sum()
    
    return profile
