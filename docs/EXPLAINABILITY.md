# Explainability Feature Documentation

## Overview

The TOR Metadata Correlation System now includes comprehensive explainability logs that justify every confidence score calculation in plain English. This feature makes the system fully auditable and transparent for legal proceedings.

## Key Features

### 1. Plain English Explanations

Every correlation score includes detailed reasoning that explains:
- **Time Correlation**: Why observations are or aren't temporally related
- **Volume Similarity**: How data volumes compare and what that means
- **Pattern Analysis**: Detection of recurring behaviors
- **Repetition Weighting**: Why repeated patterns boost confidence
- **Guard Hypothesis**: How guard nodes are identified and why
- **Final Assessment**: Overall confidence level with justification

### 2. Detailed Score Breakdown

Each session pair includes a `score_breakdown` dictionary with:
```json
{
  "time_correlation": {
    "score": 99.7,
    "weight": 0.40,
    "contribution": 39.9,
    "reasoning": "Entry and exit observations are nearly simultaneous..."
  },
  "volume_similarity": {
    "score": 98.0,
    "weight": 0.30,
    "contribution": 29.4,
    "reasoning": "Entry traffic: 2.50MB, Exit traffic: 2.52MB..."
  },
  "base_correlation": 69.7,
  "repetition_boost": 1.0,
  "final_correlation": 69.7
}
```

### 3. Reasoning Chain

Every session pair maintains a `reasoning` list with step-by-step explanations:
1. Initial correlation setup
2. Time correlation analysis
3. Volume similarity analysis
4. Pattern similarity (if available)
5. Composite score calculation
6. Repetition boost explanation
7. Guard hypothesis
8. Final confidence assessment

## Example Output

### High Confidence Scenario (69.7%)

**Reasoning Chain:**
1. Analyzing correlation between entry observation 'entry-001' and exit observation 'exit-001'
2. Entry and exit observations are nearly simultaneous (0.80 seconds apart). This is highly indicative of the same TOR session. Time correlation score: 99.7%.
3. Entry traffic: 2.62MB, Exit traffic: 2.64MB. Volumes are nearly identical (difference: 0.8%). This strongly suggests the same data passing through TOR. Volume similarity: 99.2%.
4. Inter-packet timing data is not available. Cannot perform pattern analysis.
5. Calculating composite correlation score using weighted average: Time (40%) × 99.7% = 39.9, Volume (30%) × 99.2% = 29.8. Base correlation: 69.7%.
6. No repetition boost applied (pattern seen for first time or below threshold). Final correlation: 69.7%.
7. Entry observation shows traffic at relay GUARD... Hypothesizing this as the guard node. Guard confidence: 69.7%.
8. MEDIUM CONFIDENCE (69.7%): Moderate correlation detected. Some indicators suggest the same session, but uncertainty remains.

### Score Breakdown:
- **Time Correlation**: 99.7% (weight: 0.40, contribution: 39.9)
- **Volume Similarity**: 99.2% (weight: 0.30, contribution: 29.8)
- **Base Correlation**: 69.7%
- **Repetition Boost**: 1.0x
- **Final Correlation**: 69.7%

## API Access

### Get All Session Pairs
```http
GET /correlation/pairs
```

Returns all session pairs with basic info and reasoning.

### Get Detailed Reasoning for a Specific Pair
```http
GET /correlation/pairs/{pair_id}/reasoning
```

Returns:
```json
{
  "pair_id": "entry-001_exit-001",
  "correlation_strength": 69.7,
  "reasoning": [
    "Analyzing correlation between entry observation...",
    "Entry and exit observations are nearly simultaneous...",
    ...
  ],
  "score_breakdown": {
    "time_correlation": {...},
    "volume_similarity": {...},
    ...
  }
}
```

### Get Repetition Statistics
```http
GET /correlation/repetition/statistics
```

Returns:
```json
{
  "total_patterns": 5,
  "total_observations": 15,
  "most_common_pattern": "GUARD...:entry:2000000",
  "most_common_pattern_count": 5,
  "average_repetitions": 3.0
}
```

## Confidence Levels

The system categorizes correlations into three levels:

### HIGH CONFIDENCE (≥70%)
**Message**: "Strong evidence suggests these observations represent the same TOR session. Multiple indicators align well."

**Interpretation**: Multiple signals (time, volume, patterns) strongly align. Suitable for high-priority investigative leads.

### MEDIUM CONFIDENCE (40-69%)
**Message**: "Moderate correlation detected. Some indicators suggest the same session, but uncertainty remains."

**Interpretation**: Some signals align, but not all. Suitable for broader investigative context or combined with other evidence.

### LOW CONFIDENCE (<40%)
**Message**: "Weak correlation. May be coincidental or different sessions."

**Interpretation**: Most signals don't align well. Should be treated as possible false positive.

**Note**: Correlations below the minimum threshold (30% by default) are automatically filtered out.

## Implementation Details

### Modified Components

1. **app/models/correlation.py**
   - Added `reasoning: List[str]` field to SessionPair
   - Added `score_breakdown: Dict[str, Any]` field to SessionPair

2. **app/core/correlation/engine.py**
   - Modified `_calculate_time_correlation()` to return `(score, explanation)` tuple
   - Modified `_calculate_volume_similarity()` to return `(score, explanation)` tuple
   - Modified `_calculate_pattern_similarity()` to return `(score, explanation)` tuple
   - Updated `_create_session_pair()` to collect all reasoning steps
   - Added detailed score breakdown dictionary construction
   - Added `get_repetition_statistics()` method

3. **app/api/routes.py**
   - Added `GET /correlation/pairs/{pair_id}/reasoning` endpoint

## Testing

Comprehensive test suite in `tests/test_explainability.py`:
- ✅ Time correlation explanations
- ✅ Volume similarity explanations
- ✅ Session pair reasoning chain
- ✅ Confidence level categorization
- ✅ Complete reasoning component coverage
- ✅ Score breakdown structure validation
- ✅ Guard hypothesis explanations

All tests pass successfully.

## Demonstration

Run `demo_explainability.py` to see the feature in action:

```bash
python demo_explainability.py
```

This demonstrates:
1. High confidence correlation with full explanations
2. Medium confidence correlation
3. Low confidence/rejected correlation
4. Repetition weighting effect with explanations
5. API usage examples

## Legal & Ethical Benefits

### Transparency
Every score is backed by plain English justification, making the system's decision process fully transparent.

### Auditability
Complete reasoning chains can be included in legal reports, allowing judges and lawyers to understand exactly how correlations were calculated.

### Accountability
Detailed breakdowns show which signals contributed most to each correlation, enabling proper evaluation of evidence quality.

### Court Presentation
Non-technical stakeholders can understand the system's reasoning without requiring deep technical knowledge.

## Best Practices

1. **Always include reasoning in reports**: Use the `/reasoning` endpoint to get full explanations
2. **Review score breakdowns**: Check which components contributed most to each correlation
3. **Consider confidence levels**: Higher confidence correlations warrant more investigative resources
4. **Document thresholds**: Make note of the minimum confidence threshold used (30% default)
5. **Track repetition statistics**: Repeated patterns significantly boost confidence

## Future Enhancements

Potential improvements:
- [ ] Customizable explanation verbosity levels
- [ ] Natural language generation for even more readable explanations
- [ ] Comparison explanations (why correlation A is stronger than correlation B)
- [ ] Visual diagrams showing score composition
- [ ] Explanation templates for different audiences (technical vs. legal)

## Conclusion

The explainability feature transforms the TOR Metadata Correlation System from a "black box" into a transparent, auditable tool suitable for legal proceedings. Every confidence score is now backed by detailed plain English justifications that make the system's reasoning clear to all stakeholders.
