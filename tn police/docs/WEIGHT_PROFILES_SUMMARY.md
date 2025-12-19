# Weight Profiles Feature - Implementation Summary

## ✅ COMPLETED

The TOR Metadata Correlation System now supports **configurable weight profiles per investigation**, allowing different cases to use different correlation weighting schemes based on their specific requirements.

## What Was Implemented

### 1. Weight Profile Model
**File**: [app/models/weight_profile.py](../app/models/weight_profile.py)

Created comprehensive weight profile system with:
- `WeightProfile` Pydantic model with validation
- `ProfileType` enum (standard, time_focused, volume_focused, pattern_focused, custom)
- 4 predefined profiles for common investigation types
- Custom profile creation with automatic validation
- Profile metadata (case_id, created_by, created_at, description)

**Key Features**:
```python
class WeightProfile(BaseModel):
    profile_id: str
    profile_name: str
    profile_type: ProfileType
    weight_time_correlation: float = 0.40
    weight_volume_similarity: float = 0.30
    weight_pattern_similarity: float = 0.30
    case_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    description: Optional[str] = None
    
    def validate_weights_sum(self) -> bool:
        """Ensures weights sum to 1.0"""
```

### 2. Predefined Profiles

#### Standard (Balanced)
- Time: 40%, Volume: 30%, Pattern: 30%
- Use: General-purpose investigations

#### Time-Focused
- Time: 60%, Volume: 20%, Pattern: 20%
- Use: Coordinated attacks, real-time communications

#### Volume-Focused
- Time: 25%, Volume: 50%, Pattern: 25%
- Use: Data exfiltration, large file transfers

#### Pattern-Focused
- Time: 25%, Volume: 25%, Pattern: 50%
- Use: Long-term surveillance, repeat offenders

### 3. Correlation Engine Updates
**File**: [app/core/correlation/engine.py](../app/core/correlation/engine.py)

Modified `CorrelationEngine` to:
- Accept `weight_profile` parameter in `__init__()`
- Use profile weights instead of hardcoded values
- Include profile name in correlation reasoning
- Support dynamic profile switching via `set_weight_profile()`
- Provide `get_weight_profile()` for inspection

**Example**:
```python
# Use predefined profile
engine = CorrelationEngine(weight_profile=get_profile(ProfileType.TIME_FOCUSED))

# Use custom profile
custom_profile = create_custom_profile(...)
engine = CorrelationEngine(weight_profile=custom_profile)

# Switch profiles mid-investigation
engine.set_weight_profile(new_profile)
```

### 4. API Endpoints
**File**: [app/api/routes.py](../app/api/routes.py)

Added 7 new endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/profiles/predefined` | GET | List all predefined profiles |
| `/profiles/{profile_type}` | GET | Get specific predefined profile |
| `/profiles/custom` | POST | Create custom profile |
| `/correlation/weight-profile` | GET | Get current engine profile |
| `/correlation/weight-profile` | POST | Update engine profile |
| `/correlation/analyze-with-profile` | POST | Run correlation with specific profile |
| `/correlation/repetition/statistics` | GET | Get pattern statistics |

**Example API Usage**:
```bash
# Get predefined profiles
curl http://localhost:8000/api/profiles/predefined

# Create custom profile
curl -X POST http://localhost:8000/api/profiles/custom \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "case-001",
    "profile_name": "Case 001 Profile",
    "weight_time": 0.5,
    "weight_volume": 0.3,
    "weight_pattern": 0.2,
    "case_id": "CASE-001",
    "created_by": "inv@tnpolice.gov.in"
  }'

# Analyze with time-focused profile
curl -X POST "http://localhost:8000/api/correlation/analyze-with-profile?profile_type=time_focused"
```

### 5. Configuration
**File**: [.env.example](../.env.example)

Added weight profile configuration:
```bash
# Default Weight Profile
DEFAULT_WEIGHT_PROFILE=standard

# Custom weights (only if DEFAULT_WEIGHT_PROFILE=custom)
WEIGHT_TIME_CORRELATION=0.40
WEIGHT_VOLUME_SIMILARITY=0.30
WEIGHT_PATTERN_SIMILARITY=0.30
```

### 6. Comprehensive Testing
**File**: [tests/test_weight_profiles.py](../tests/test_weight_profiles.py)

Created 16 tests covering:
- ✅ Predefined profiles exist and are valid
- ✅ Each profile has correct weights
- ✅ Custom profile creation and validation
- ✅ Weight constraint enforcement (sum to 1.0, range 0-1)
- ✅ Engine integration with profiles
- ✅ Profile switching functionality
- ✅ Different profiles produce different results
- ✅ Profile names appear in reasoning
- ✅ Edge cases (all weight on one signal)
- ✅ Profile metadata storage

**All 16 tests pass** ✅

### 7. Documentation
**Files**:
- [docs/WEIGHT_PROFILES.md](WEIGHT_PROFILES.md) - Complete feature documentation
- [docs/WEIGHT_PROFILES_SUMMARY.md](WEIGHT_PROFILES_SUMMARY.md) - This summary

Documentation includes:
- Concept explanation
- All predefined profiles with use cases
- Custom profile creation guide
- Complete API reference
- Python SDK examples
- Weight impact demonstration
- Best practices
- Investigation type examples

### 8. Verification Script
**File**: [verify_weight_profiles.py](../verify_weight_profiles.py)

Interactive verification demonstrating:
- All 4 predefined profiles
- Custom profile creation
- Engine integration
- Profile impact on correlation scores

## Files Modified

1. **app/models/weight_profile.py** (NEW) - 195 lines
   - WeightProfile model
   - Predefined profiles
   - Helper functions

2. **app/core/correlation/engine.py** - Modified
   - Added weight_profile parameter to __init__
   - Updated weight usage in _create_session_pair
   - Added get_weight_profile() and set_weight_profile()
   - Profile name in reasoning explanations

3. **app/api/routes.py** - Modified
   - Added 7 new endpoints for profile management

4. **.env.example** - Modified
   - Added weight profile configuration section

## Files Created

1. **tests/test_weight_profiles.py** - 306 lines
   - Comprehensive test suite (16 tests)

2. **docs/WEIGHT_PROFILES.md** - 477 lines
   - Complete feature documentation

3. **docs/WEIGHT_PROFILES_SUMMARY.md** - This file
   - Implementation summary

4. **verify_weight_profiles.py** - 123 lines
   - Verification/demonstration script

## Key Benefits

### For Investigators
- **Flexibility**: Adapt correlation to investigation type
- **Precision**: Optimize for specific evidence patterns
- **Control**: Fine-tune weights per case requirements

### For Legal Proceedings
- **Transparency**: Profile name in all reasoning
- **Auditability**: Track who created what profile when
- **Justification**: Explain why specific weights were chosen

### For System Quality
- **Validation**: Automatic weight constraint checking
- **Testing**: Comprehensive test coverage
- **Documentation**: Complete API and usage docs

## Usage Examples

### Real-Time Communications Investigation
```python
profile = get_profile(ProfileType.TIME_FOCUSED)
engine = CorrelationEngine(weight_profile=profile)
# Emphasizes precise timing synchronization
```

### Data Exfiltration Case
```python
profile = get_profile(ProfileType.VOLUME_FOCUSED)
engine = CorrelationEngine(weight_profile=profile)
# Emphasizes data volume matching
```

### Custom Investigation
```python
profile = create_custom_profile(
    profile_id="narcotics-2025-042",
    profile_name="Narcotics Investigation",
    weight_time=0.45,  # Moderate time importance
    weight_volume=0.40,  # High volume importance
    weight_pattern=0.15,  # Low pattern importance
    case_id="CASE-2025-042",
    created_by="inv.sharma@tnpolice.gov.in",
    description="Dark web marketplace transactions"
)
engine = CorrelationEngine(weight_profile=profile)
```

## How It Works

### Before (Hardcoded Weights)
```python
# Fixed weights for all investigations
time_weight = 0.40
volume_weight = 0.30
pattern_weight = 0.30
```

### After (Configurable Per Investigation)
```python
# Weights from profile
time_weight = self.weight_profile.weight_time_correlation
volume_weight = self.weight_profile.weight_volume_similarity
pattern_weight = self.weight_profile.weight_pattern_similarity

# Included in reasoning
f"Calculating composite correlation score using {self.weight_profile.profile_name} weights: ..."
```

## Impact on Scoring

Same observations, different profiles = different scores:

**Scenario**: Good time match (95%), poor volume match (40%), moderate pattern (60%)

| Profile | Time Weight | Volume Weight | Pattern Weight | Final Score |
|---------|------------|---------------|----------------|-------------|
| Standard | 40% | 30% | 30% | 68% |
| Time-Focused | 60% | 20% | 20% | 77% |
| Volume-Focused | 25% | 50% | 25% | 59% |
| Pattern-Focused | 25% | 25% | 50% | 68% |

Different profiles produce different confidence levels for the same evidence!

## Validation

All profiles automatically validate:
```python
# Checks that weights sum to 1.0
profile.validate_weights_sum()

# Checks each weight is 0-1
@field_validator validates ranges

# Prevents invalid profiles
create_custom_profile(0.5, 0.3, 0.3)  # Sum = 1.1
# Raises: ValueError: Weights must sum to 1.0
```

## Next Steps (Optional Enhancements)

While the feature is complete, potential future additions:
1. Profile templates library for common crime types
2. Profile recommendation based on case metadata
3. A/B testing multiple profiles on same data
4. Profile performance analytics
5. Import/export profiles for sharing across departments

## Conclusion

The weight profile feature makes the correlation engine truly **investigation-aware**. Different cases can now use different weighting schemes optimized for their specific requirements, while maintaining full transparency and auditability.

**Status**: ✅ PRODUCTION READY

---

**Implementation Date**: December 2025  
**Test Coverage**: 16/16 tests passing  
**Documentation**: Complete  
**API Endpoints**: 7 new endpoints  
**Predefined Profiles**: 4 (Standard, Time, Volume, Pattern)
