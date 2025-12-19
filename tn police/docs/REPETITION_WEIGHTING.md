# Repeated Observation Weighting Feature

## Overview

The **Repeated Observation Weighting** feature extends the correlation engine to intelligently increase confidence scores when the same patterns are observed multiple times. This leverages the known behavior of TOR clients to provide more accurate and reliable investigative leads.

## Why This Matters

### TOR Client Behavior
TOR clients typically select a small set of **guard relays** and use them consistently for approximately **90 days**. This means:
- If you observe traffic from the same guard multiple times, it's more likely the same user
- Repeated patterns are statistically less likely to be coincidental
- Guard persistence is a strong behavioral signal

### Investigative Value
1. **Better Signal Detection**: Distinguish real patterns from random noise
2. **Confidence Calibration**: Appropriately higher confidence for repeated observations
3. **Lead Prioritization**: Focus on targets with consistent behavior
4. **Reduced False Positives**: Random coincidences are less likely to repeat

## How It Works

### 1. Pattern Recognition

Each observation is assigned a **pattern key** based on:
- **Relay fingerprint**: Identifies the specific relay
- **Observation type**: Entry or exit
- **Volume bucket**: Traffic volume grouped into 100KB ranges

```python
pattern_key = f"{relay_fingerprint}:{observation_type}:{volume_bucket}"
```

Example:
- `AAAA1111...:entry_observed:1000000`
- `AAAA1111...:entry_observed:1100000` (same pattern - volume bucketed)

### 2. Repetition Tracking

The engine maintains:
- **Observation history**: All observations per relay
- **Pattern frequency**: Count of how many times each pattern appears

```python
pattern_frequency[pattern_key] += 1
```

### 3. Boost Calculation

When a pattern is seen multiple times, a **boost multiplier** is calculated:

```python
if repetition_count >= MIN_REPETITIONS_FOR_BOOST:
    boost = 1.0 + (log2(repetition_count) * (BOOST_FACTOR - 1.0))
    boost = min(boost, MAX_REPETITION_BOOST)
else:
    boost = 1.0  # No boost yet
```

**Logarithmic scaling** provides diminishing returns:
- 2 repetitions → ~1.5x boost
- 4 repetitions → ~2.0x boost
- 8+ repetitions → 2.0x boost (capped at maximum)

### 4. Score Adjustment

The boost is applied to the correlation score:

```python
# Calculate boost for both entry and exit observations
entry_weight = calculate_repetition_weight(entry_observation)
exit_weight = calculate_repetition_weight(exit_observation)
combined_weight = (entry_weight + exit_weight) / 2.0

# Apply boost (softly to avoid over-confidence)
weighted_score = base_score * (1.0 + (combined_weight - 1.0) * 0.5)
weighted_score = min(weighted_score, 100.0)  # Cap at 100%
```

## Configuration

All parameters are configurable in `config.py`:

```python
# Enable/disable feature
ENABLE_REPETITION_WEIGHTING: bool = True

# Minimum repetitions before boost applies
MIN_REPETITIONS_FOR_BOOST: int = 2

# Boost multiplier factor
REPETITION_BOOST_FACTOR: float = 1.5

# Maximum boost cap
MAX_REPETITION_BOOST: float = 2.0
```

## Example Scenario

### Without Repetition Weighting

Observer sees traffic at Guard A and Exit B:
- **First observation**: 65% confidence
- **Second observation**: 65% confidence
- **Third observation**: 65% confidence

All observations treated equally.

### With Repetition Weighting

Observer sees the same pattern repeatedly:
- **First observation**: 65% confidence (no boost)
- **Second observation**: 65% confidence (still below threshold)
- **Third observation**: ~75% confidence (**1.5x boost applied**)
- **Fourth observation**: ~80% confidence (**~2.0x boost applied**)
- **Fifth observation**: ~82% confidence (**capped near maximum**)

Repeated observations appropriately increase confidence.

## API Usage

### Get Repetition Statistics

```bash
curl "http://localhost:8000/api/correlation/repetition-stats"
```

**Response**:
```json
{
  "repetition_weighting": {
    "enabled": true,
    "total_unique_patterns": 15,
    "repeated_patterns": 8,
    "max_repetitions": 5,
    "avg_repetitions": 2.3,
    "top_patterns": [
      {
        "pattern": "AAAA1111...:entry_observed:1000000",
        "count": 5
      },
      {
        "pattern": "BBBB2222...:exit_observed:500000",
        "count": 3
      }
    ],
    "boost_parameters": {
      "min_repetitions": 2,
      "boost_factor": 1.5,
      "max_boost": 2.0
    }
  },
  "explanation": "Repeated observation patterns increase correlation confidence..."
}
```

## Testing

### Run Unit Tests

```bash
pytest tests/test_repetition_weighting.py -v
```

Tests cover:
- ✅ Repetition weight calculation
- ✅ Pattern key generation and grouping
- ✅ Correlation score boosting
- ✅ Statistics generation
- ✅ Feature enable/disable

### Run Demonstration

```bash
python demo_repetition_weighting.py
```

This demonstrates:
1. Correlation without repetition (baseline)
2. Correlation with repetition (5 observations)
3. Comparison of confidence scores
4. Repetition statistics
5. Detailed explanation

## Benefits for Investigators

### 1. More Reliable Leads
- Repeated patterns have higher confidence
- Less likely to be false positives
- Better prioritization of investigation targets

### 2. Guard Node Identification
- Leverages TOR client behavior (90-day guard persistence)
- Repeated guard observations strengthen hypotheses
- More accurate guard attribution

### 3. Behavioral Analysis
- Identify users with consistent patterns
- Track behavioral changes over time
- Detect anomalies in pattern frequency

### 4. Resource Optimization
- Focus on high-confidence, repeated patterns
- Deprioritize one-off coincidences
- Better allocation of investigative resources

## Technical Details

### Implementation Location

```
app/core/correlation/engine.py
├── __init__()
│   └── observation_history: Dict[str, List[Observation]]
│   └── pattern_frequency: Dict[str, int]
│
├── _create_pattern_key()
│   └── Generates pattern identifier
│
├── _calculate_repetition_weight()
│   └── Calculates boost multiplier
│
├── _apply_repetition_weighting()
│   └── Applies boost to correlation scores
│
└── get_repetition_statistics()
    └── Returns statistics for API
```

### Performance Considerations

- **Memory**: Stores observation history in memory (consider persistence for production)
- **Computation**: O(1) pattern lookup using dictionary
- **Scalability**: Efficient for thousands of observations

### Future Enhancements

Potential improvements:
1. **Time decay**: Reduce weight of old observations
2. **Persistence**: Store pattern history in database
3. **Adaptive thresholds**: Adjust based on network conditions
4. **Pattern clustering**: Group similar (not identical) patterns
5. **Temporal analysis**: Weight by recency and frequency

## Security & Ethics

### Maintains Ethical Boundaries

- ✅ Still uses only metadata (no payload inspection)
- ✅ Still generates probabilistic leads (not certainty)
- ✅ Still requires validation with additional evidence
- ✅ Improves accuracy within existing constraints

### Transparency

- All boost calculations are logged
- Statistics endpoint shows exactly what's being tracked
- Configuration is explicit and adjustable
- Reasoning is explainable

## Summary

The **Repeated Observation Weighting** feature:

1. **Leverages TOR Behavior**: Uses known guard persistence patterns
2. **Improves Accuracy**: Increases confidence for repeated observations
3. **Reduces Noise**: Helps distinguish signal from random correlations
4. **Maintains Ethics**: Works within existing legal/ethical framework
5. **Fully Configurable**: All parameters adjustable via config
6. **Well Tested**: Comprehensive test suite included
7. **Documented**: Clear API and methodology documentation

**Result**: More reliable investigative leads with better confidence calibration.

---

**Status**: ✅ Production-ready
**Added**: December 20, 2025
**Testing**: Comprehensive unit tests and demonstration included
