# Configurable Weight Profiles - Documentation

## Overview

The TOR Metadata Correlation System now supports **configurable weight profiles per investigation**. Different cases can use different weighting schemes based on their specific requirements, making the correlation engine adaptable to various investigation types.

## Key Concept

Correlation scoring combines multiple weak signals:
- **Time Correlation** (when did events occur?)
- **Volume Similarity** (how much data was transferred?)
- **Pattern Similarity** (behavioral patterns)

Each signal receives a **weight** (0-1) that determines its importance. Weights must sum to 1.0 for proper probabilistic interpretation.

## Predefined Profiles

The system includes 4 predefined profiles for common investigation types:

### 1. Standard Profile (Balanced)
```python
Time Correlation:    40%
Volume Similarity:   30%
Pattern Similarity:  30%
```
**Use Case**: General-purpose investigations when all signals are equally important.

**Example**: Routine surveillance, initial correlation analysis.

### 2. Time-Focused Profile
```python
Time Correlation:    60%
Volume Similarity:   20%
Pattern Similarity:  20%
```
**Use Case**: Investigations where precise timing is critical.

**Example**: 
- Coordinated attacks with tight time windows
- Real-time communications analysis
- Synchronized events across multiple nodes

### 3. Volume-Focused Profile
```python
Time Correlation:    25%
Volume Similarity:   50%
Pattern Similarity:  25%
```
**Use Case**: Investigations focused on data volume matching.

**Example**:
- Data exfiltration cases
- Large file transfers
- Bulk data movement tracking

### 4. Pattern-Focused Profile
```python
Time Correlation:    25%
Volume Similarity:   25%
Pattern Similarity:  50%
```
**Use Case**: Long-term surveillance of habitual offenders.

**Example**:
- Repeat offender tracking
- Behavioral pattern analysis
- Routine communication monitoring

## Custom Profiles

Investigators can create custom weight profiles for specific cases:

```python
from app.models.weight_profile import create_custom_profile

profile = create_custom_profile(
    profile_id="case-2025-001-custom",
    profile_name="Narcotics Investigation - Mumbai Cell",
    weight_time=0.50,      # 50% weight on timing
    weight_volume=0.35,    # 35% weight on volume
    weight_pattern=0.15,   # 15% weight on patterns
    case_id="CASE-2025-001",
    created_by="inv.sharma@tnpolice.gov.in",
    description="Custom profile for narcotics trafficking investigation"
)
```

**Requirements**:
- Weights must be between 0 and 1
- Weights must sum to exactly 1.0
- Profile ID must be unique

## API Usage

### Get All Predefined Profiles
```http
GET /api/profiles/predefined
```

**Response**:
```json
{
  "profiles": [
    {
      "profile_id": "standard",
      "profile_name": "Standard Balanced Profile",
      "weight_time_correlation": 0.40,
      "weight_volume_similarity": 0.30,
      "weight_pattern_similarity": 0.30,
      "description": "Balanced weights suitable for most investigations..."
    },
    ...
  ],
  "count": 4
}
```

### Get Specific Profile
```http
GET /api/profiles/time_focused
```

### Create Custom Profile
```http
POST /api/profiles/custom
Content-Type: application/json

{
  "profile_id": "case-2025-042-custom",
  "profile_name": "Dark Web Marketplace Investigation",
  "weight_time": 0.45,
  "weight_volume": 0.40,
  "weight_pattern": 0.15,
  "case_id": "CASE-2025-042",
  "created_by": "inv.patel@tnpolice.gov.in",
  "description": "Emphasis on timing and volume for marketplace transactions"
}
```

### Get Current Profile
```http
GET /api/correlation/weight-profile
```

### Update Engine Profile
```http
POST /api/correlation/weight-profile
Content-Type: application/json

{
  "profile_id": "time-focused",
  "profile_name": "Time-Focused Profile",
  "profile_type": "time_focused",
  "weight_time_correlation": 0.60,
  "weight_volume_similarity": 0.20,
  "weight_pattern_similarity": 0.20
}
```

### Run Analysis with Specific Profile
```http
POST /api/correlation/analyze-with-profile?profile_type=time_focused
```

Or with custom profile:
```http
POST /api/correlation/analyze-with-profile
Content-Type: application/json

{
  "custom_profile": {
    "profile_id": "my-custom",
    "profile_name": "My Custom Profile",
    "profile_type": "custom",
    "weight_time_correlation": 0.5,
    "weight_volume_similarity": 0.3,
    "weight_pattern_similarity": 0.2
  }
}
```

## Python SDK Usage

### Using Predefined Profile
```python
from app.core.correlation import CorrelationEngine
from app.models.weight_profile import get_profile, ProfileType

# Create engine with time-focused profile
profile = get_profile(ProfileType.TIME_FOCUSED)
engine = CorrelationEngine(weight_profile=profile)

# Run correlation
pairs = engine.correlate_observations(entry_obs, exit_obs)
```

### Using Custom Profile
```python
from app.models.weight_profile import create_custom_profile

# Create custom profile
profile = create_custom_profile(
    profile_id="investigation-alpha",
    profile_name="Investigation Alpha",
    weight_time=0.55,
    weight_volume=0.30,
    weight_pattern=0.15,
    case_id="ALPHA-2025",
    created_by="investigator@department.gov"
)

# Use with engine
engine = CorrelationEngine(weight_profile=profile)
```

### Changing Profile Mid-Investigation
```python
# Start with standard
engine = CorrelationEngine()

# Run initial correlation
pairs_1 = engine.correlate_observations(entry_obs, exit_obs)

# Switch to time-focused for follow-up analysis
time_profile = get_profile(ProfileType.TIME_FOCUSED)
engine.set_weight_profile(time_profile)

# Re-run with new weights
pairs_2 = engine.correlate_observations(entry_obs, exit_obs)
```

## How Weights Affect Scoring

Example scenario:
- Time correlation: 95%
- Volume similarity: 40%
- Pattern similarity: 60%

### With Standard Profile (40/30/30):
```
Composite Score = (95 × 0.40) + (40 × 0.30) + (60 × 0.30)
                = 38 + 12 + 18
                = 68%
```

### With Time-Focused Profile (60/20/20):
```
Composite Score = (95 × 0.60) + (40 × 0.20) + (60 × 0.20)
                = 57 + 8 + 12
                = 77%
```

### With Volume-Focused Profile (25/50/25):
```
Composite Score = (95 × 0.25) + (40 × 0.50) + (60 × 0.25)
                = 23.75 + 20 + 15
                = 58.75%
```

**Result**: Same observations produce different confidence scores based on investigation priorities!

## Reasoning & Transparency

Weight profiles are mentioned in correlation reasoning:

```
"Calculating composite correlation score using Time-Focused Profile weights:
Time (60%) × 95.0% = 57.0, Volume (20%) × 40.0% = 8.0, Pattern (20%) × 60.0% = 12.0.
Base correlation: 77.0%."
```

This ensures full transparency about how scores were calculated.

## Best Practices

### 1. Choose Profile Based on Case Type
- **Time-critical operations**: Use Time-Focused
- **Data exfiltration**: Use Volume-Focused  
- **Long-term surveillance**: Use Pattern-Focused
- **General cases**: Use Standard

### 2. Document Profile Choices
Always record:
- Which profile was used
- Why it was chosen
- Who authorized it
- When it was applied

### 3. Validate Custom Profiles
Before deployment:
```python
# Test that weights sum to 1.0
profile.validate_weights_sum()  # Raises ValueError if invalid
```

### 4. Per-Investigation Profiles
Create separate profiles for different cases:
```python
case_001_profile = create_custom_profile(
    profile_id="case-001-profile",
    case_id="CASE-001",
    ...
)

case_002_profile = create_custom_profile(
    profile_id="case-002-profile",
    case_id="CASE-002",
    ...
)
```

### 5. Profile Metadata
Include comprehensive metadata:
```python
profile = create_custom_profile(
    profile_id=f"case-{case_number}-{timestamp}",
    profile_name=f"Case {case_number} - {investigation_type}",
    case_id=case_number,
    created_by=investigator_email,
    description=f"Optimized for {investigation_type} with focus on {primary_signal}"
)
```

## Testing

Comprehensive test suite validates:
- Predefined profiles exist and are valid
- Custom profiles enforce weight constraints
- Different profiles produce different results
- Profile changes are properly applied
- Reasoning includes profile information

Run tests:
```bash
pytest tests/test_weight_profiles.py -v
```

All 16 tests pass ✅

## Configuration

Default profile can be set in `.env`:
```bash
# Default Weight Profile
DEFAULT_WEIGHT_PROFILE=standard

# Custom weights (only if DEFAULT_WEIGHT_PROFILE=custom)
WEIGHT_TIME_CORRELATION=0.40
WEIGHT_VOLUME_SIMILARITY=0.30
WEIGHT_PATTERN_SIMILARITY=0.30
```

## Examples by Investigation Type

### Cybercrime - Real-Time Chat
```python
profile = get_profile(ProfileType.TIME_FOCUSED)
# Prioritizes precise timing synchronization
```

### Data Breach - Exfiltration
```python
profile = get_profile(ProfileType.VOLUME_FOCUSED)
# Prioritizes large data volume matching
```

### Organized Crime - Long-Term
```python
profile = get_profile(ProfileType.PATTERN_FOCUSED)
# Prioritizes recurring behavioral patterns
```

### Terrorism - Coordinated Attack
```python
profile = create_custom_profile(
    profile_id="terror-investigation",
    profile_name="Coordinated Attack Analysis",
    weight_time=0.70,  # Extremely time-sensitive
    weight_volume=0.15,
    weight_pattern=0.15
)
```

### Financial Crime - Money Laundering
```python
profile = create_custom_profile(
    profile_id="fincrimes-laundering",
    profile_name="Money Laundering Patterns",
    weight_time=0.30,
    weight_volume=0.40,  # Follow the money
    weight_pattern=0.30  # Recurring patterns
)
```

## Summary

Weight profiles provide:
- ✅ **Flexibility**: Adapt correlation to investigation type
- ✅ **Transparency**: Profile name appears in reasoning
- ✅ **Validation**: Automatic weight constraint checking
- ✅ **Audit Trail**: Metadata tracks who created what
- ✅ **API Support**: Full REST API for profile management
- ✅ **Testing**: Comprehensive test coverage

This makes the correlation engine truly investigation-aware and adaptable to diverse law enforcement scenarios.
