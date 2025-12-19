# Repeated Observation Weighting - Quick Reference

## What Is It?

A feature that **increases correlation confidence** when the same patterns are observed multiple times.

## Why?

TOR clients use the same guard relay for ~90 days. Repeated observations = stronger evidence of consistent behavior.

## How Does It Work?

```
Pattern seen 1x  → No boost (1.0x)
Pattern seen 2x  → No boost (1.0x) - below threshold
Pattern seen 3x  → 1.5x boost ✓
Pattern seen 4x  → 2.0x boost ✓
Pattern seen 5x+ → 2.0x boost (capped)
```

## Key Concepts

**Pattern Key**: `relay_fingerprint:obs_type:volume_bucket`
- Identifies unique patterns
- Volume bucketed to 100KB for grouping

**Boost Formula**: `1.0 + (log2(repetitions) × boost_factor)`
- Logarithmic = diminishing returns
- Capped at maximum to prevent over-confidence

**Score Application**: `weighted_score = base_score × boost_adjustment`
- Soft application (50% of boost) to avoid over-boosting
- Always capped at 100%

## Configuration (config.py)

```python
ENABLE_REPETITION_WEIGHTING = True   # On/off switch
MIN_REPETITIONS_FOR_BOOST = 2        # Minimum repetitions needed
REPETITION_BOOST_FACTOR = 1.5        # Boost multiplier
MAX_REPETITION_BOOST = 2.0           # Maximum boost cap
```

## API Usage

**Get Statistics**:
```bash
GET /api/correlation/repetition-stats
```

**Response**:
```json
{
  "total_unique_patterns": 15,
  "repeated_patterns": 8,
  "max_repetitions": 5,
  "avg_repetitions": 2.3
}
```

## Testing

```bash
# Run tests
pytest tests/test_repetition_weighting.py -v

# Run demo
python demo_repetition_weighting.py
```

## Example

**Scenario**: Investigating suspect using TOR

**Without Repetition Weighting**:
- See Guard A → 65% confidence
- See Guard A again → 65% confidence
- See Guard A again → 65% confidence

**With Repetition Weighting**:
- See Guard A → 65% confidence
- See Guard A again → 65% confidence
- See Guard A again → **~75% confidence** ⬆ (boost applied!)
- See Guard A again → **~80% confidence** ⬆
- See Guard A again → **~82% confidence** ⬆

**Result**: Higher confidence for repeated patterns = better leads

## Benefits

1. ✅ **More Accurate**: Repeated patterns get appropriate confidence
2. ✅ **Less Noise**: Random coincidences stay low confidence
3. ✅ **Better Leads**: Focus on consistent behavior
4. ✅ **Leverages TOR Behavior**: Uses guard persistence
5. ✅ **Configurable**: Adjust all parameters
6. ✅ **Transparent**: All boosts logged and explainable

## Files

**Core Logic**: `app/core/correlation/engine.py`
**Tests**: `tests/test_repetition_weighting.py`
**Demo**: `demo_repetition_weighting.py`
**Docs**: `docs/REPETITION_WEIGHTING.md`

## Quick Test

```bash
# Start server
python run.py

# Fetch topology
curl -X POST "http://localhost:8000/api/topology/fetch?limit=50"

# Generate data with repetition
curl -X POST "http://localhost:8000/api/observations/generate-synthetic?num_sessions=10&guard_persistence=true"

# Analyze
curl -X POST "http://localhost:8000/api/correlation/analyze"

# Check repetition stats
curl "http://localhost:8000/api/correlation/repetition-stats"
```

## Key Takeaway

**Repeated observations → Higher confidence → Better investigative leads**

The system now automatically detects and weights recurring patterns, providing more reliable results while maintaining ethical boundaries.

---

✅ Production-ready | ✅ Fully tested | ✅ Well documented
