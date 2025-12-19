# Methodology Documentation

## TOR Metadata Correlation System - Technical Methodology

This document explains the technical and investigative methodology used by the system.

## System Architecture

### 1. Data Ingestion Layer

**Purpose**: Collect and normalize TOR network topology data

**Data Sources**:
- TOR Onionoo API: https://onionoo.torproject.org/
- Official TOR Project metrics and relay descriptors
- All data is **publicly available** and published by TOR Project

**What We Collect**:
- Relay fingerprints (public keys)
- IP addresses and ports
- Relay capabilities (Guard, Exit, etc.)
- Bandwidth metrics
- Geographic locations
- Network (AS) information
- Relay status flags

**What We DO NOT Collect**:
- Traffic payloads
- User identities
- Encrypted communications
- Private keys

### 2. Topology Engine

**Purpose**: Build time-aware graph representation of TOR network

**Key Components**:

#### Topology Snapshot
- Point-in-time view of entire TOR network
- ~7,000 relays in production network
- Updated periodically (hourly recommended)

#### Graph Analyzer
- Models TOR network as directed graph
- Implements TOR path selection constraints:
  - No relays in same /16 subnet
  - Proper flag requirements (Guard→Middle→Exit)
  - Consensus weight-based probability

### 3. Correlation Engine

**Purpose**: Identify timing patterns between entry and exit observations

#### Timing Correlation

**Concept**: TOR traffic enters at guard, exits at exit relay. If we observe both with similar timestamps, they might be the same session.

**Formula**:
```
time_correlation_score = 100 * exp(-time_delta / time_window)
```

Where:
- `time_delta`: Time difference between entry and exit observations
- `time_window`: Maximum correlation window (default: 300 seconds)

**Interpretation**:
- 0 seconds delta → 100% time score
- 300 seconds delta → 36.8% time score
- 600 seconds delta → 13.5% time score

#### Volume Correlation

**Concept**: TOR circuits carrying same data should have similar volumes (accounting for TOR overhead)

**Formula**:
```
volume_similarity = 100 * (min_bytes / max_bytes)
```

**TOR Overhead**: ~3-5% typical overhead for cell padding and headers

#### Pattern Correlation

**Concept**: Inter-packet timing patterns survive TOR with some distortion

**Method**: Compare timing pattern statistics:
- Packet count similarity
- Timing distribution similarity
- Burst pattern matching

**Limitations**: TOR multiplexing and batching reduce pattern fidelity

### 4. Composite Confidence Scoring

**Purpose**: Combine multiple weak signals into overall confidence

**Scoring Formula**:
```
correlation_strength = 
    (time_correlation × 0.40) +
    (volume_similarity × 0.30) +
    (pattern_similarity × 0.30)
```

**Weights Rationale**:
- **Time (40%)**: Most reliable signal - TOR has low latency
- **Volume (30%)**: Moderately reliable - overhead is predictable
- **Pattern (30%)**: Less reliable - multiplexing distorts patterns

**Guard Confidence**:
```
guard_confidence = 
    (base_correlation × 0.70) +
    (guard_selection_probability × 0.30)
```

Incorporates:
- Base correlation strength
- Guard's selection probability (consensus weight)

### 5. Cluster Analysis

**Purpose**: Identify repeated patterns indicating persistent behavior

#### Guard Persistence

**TOR Behavior**: Clients typically use the same guard for ~90 days

**Detection**:
1. Group session pairs by hypothesized guard
2. Calculate temporal clustering (same guard over time)
3. Score persistence strength

**Scoring**:
```
guard_persistence_score = min(observation_count × 10, 100)
```

#### Cluster Confidence

**Formula**:
```
cluster_confidence = 
    (consistency_score × 0.60) +
    (guard_persistence_score × 0.40)
```

Where:
- `consistency_score`: Average correlation strength of pairs
- `guard_persistence_score`: How persistent guard usage is

### 6. Probabilistic Inference

**Key Principle**: We generate **hypotheses**, not facts

#### Bayesian Reasoning

For each observation pair:

**Prior Probability**:
- P(same session | random) = very low (network has ~7000 relays)
- P(same session | timing match) = higher but still uncertain

**Evidence**:
- Timing correlation
- Volume similarity
- Pattern matching
- Guard persistence

**Posterior Probability**:
- Combined confidence score
- Always < 100% (never certain)

#### Multiple Hypotheses

System generates multiple competing hypotheses:
- Most likely guard: Highest confidence
- Alternative guards: Lower but non-zero confidence
- Null hypothesis: Random coincidence

### 7. Repeated Observation Weighting

**Purpose**: Increase confidence when the same patterns are observed multiple times

#### Pattern Detection

**Concept**: Repeated observations of the same relay/pattern indicate consistent behavior

**Pattern Key Components**:
- Relay fingerprint
- Observation type (entry/exit)
- Volume bucket (grouped into 100KB ranges)

**Tracking**:
```python
pattern_key = f"{relay}:{obs_type}:{volume_bucket}"
pattern_frequency[pattern_key] += 1
```

#### Boost Calculation

**Formula**:
```
repetition_boost = 1.0 + (log2(repetition_count) × boost_factor)
repetition_boost = min(repetition_boost, MAX_REPETITION_BOOST)
```

**Parameters** (configurable in config.py):
- `MIN_REPETITIONS_FOR_BOOST`: 2 (minimum repetitions to apply boost)
- `REPETITION_BOOST_FACTOR`: 1.5 (boost multiplier)
- `MAX_REPETITION_BOOST`: 2.0 (maximum boost cap)

**Logarithmic Scaling** (diminishing returns):
- 2 repetitions → ~1.5x boost
- 4 repetitions → ~2.0x boost (capped)
- 8+ repetitions → 2.0x boost (capped at max)

#### Score Application

**Weighted Correlation**:
```
entry_weight = calculate_repetition_weight(entry_observation)
exit_weight = calculate_repetition_weight(exit_observation)
combined_weight = (entry_weight + exit_weight) / 2.0

weighted_score = base_score × (1.0 + (combined_weight - 1.0) × 0.5)
weighted_score = min(weighted_score, 100.0)
```

**Soft Application**: Uses 0.5 multiplier to avoid over-boosting

#### Investigative Rationale

**TOR Client Behavior**:
- TOR clients typically use the same guard relay for ~90 days
- Repeated observations of the same guard indicate persistent user behavior
- Same pattern across multiple sessions strengthens attribution hypothesis

**Benefits**:
1. **Signal vs Noise**: Repeated patterns are statistically less likely to be coincidental
2. **Guard Persistence**: Leverages known TOR client behavior
3. **Confidence Calibration**: Appropriately higher confidence for repeated observations
4. **Lead Prioritization**: Focus investigative resources on patterns with repetition

**Example**:
- First observation of Guard A → Base confidence 65%
- After 3 observations of Guard A → Boosted to ~75-80%
- After 5 observations of Guard A → Boosted to ~80-85% (approaching cap)

## What This System Can and Cannot Do

### ✅ What It CAN Do

1. **Identify Timing Patterns**
   - Correlate entry/exit events within time window
   - Measure temporal clustering

2. **Infer Probable Guards**
   - Hypothesize which guard relays were likely used
   - Rank hypotheses by confidence

3. **Detect Behavioral Patterns**
   - Identify repeated guard usage
   - Find temporal patterns in observations

4. **Generate Investigative Leads**
   - Provide ranked list of probable scenarios
   - Explain reasoning transparently

5. **Support Decision-Making**
   - Give investigators starting points
   - Prioritize further investigation

### ❌ What It CANNOT Do

1. **Deanonymize Users**
   - Cannot identify real-world individuals
   - Cannot attribute traffic to specific persons

2. **Break TOR Encryption**
   - Cannot decrypt TOR traffic
   - Cannot read message contents

3. **Prove Identity**
   - Provides probabilities, not proof
   - Not sufficient evidence alone

4. **Guarantee Accuracy**
   - False positives are possible
   - Coincidental correlations occur

5. **Violate Privacy**
   - Uses only public metadata
   - No payload inspection

## Validation and Limitations

### Known Limitations

1. **False Positive Rate**
   - Coincidental timing matches occur
   - Busy time periods increase false positives
   - Requires manual validation

2. **False Negative Rate**
   - Long sessions may exceed correlation window
   - Timing jitter can break correlations
   - Multiple concurrent sessions interfere

3. **Guard Inference Uncertainty**
   - Guards cannot be proven, only inferred
   - Multiple guards may have similar probabilities
   - Guard rotation breaks patterns

4. **Scalability**
   - Full TOR network: ~7000 relays
   - High traffic volume: millions of observations
   - Real-time correlation is challenging

### Validation Methods

1. **Synthetic Data Testing**
   - Generate known correlations
   - Measure detection rate
   - Tune parameters

2. **Statistical Validation**
   - Compare confidence scores to outcomes
   - Calibrate probability estimates
   - Measure precision/recall

3. **Null Hypothesis Testing**
   - Test against random data
   - Measure false positive rate
   - Set appropriate thresholds

## Ethical Framework

### Legal Compliance

✅ **Lawful**:
- Uses publicly available data
- Statistical analysis only
- Supports authorized investigations

❌ **Not Lawful For**:
- Unauthorized surveillance
- Privacy violations
- Individual targeting without cause

### Transparency

All analysis is explainable:
- Clear confidence scores
- Documented reasoning
- Traceable evidence chains

### Limitations Disclosure

System explicitly states:
- Probabilistic nature
- Uncertainty levels
- Need for validation

## Operational Guidelines

### Recommended Use

1. **Starting Point**: Use for initial lead generation
2. **Prioritization**: Rank investigative targets
3. **Validation**: Always validate with additional evidence
4. **Documentation**: Maintain audit trail
5. **Limitations**: Understand and communicate uncertainties

### Not Recommended For

1. **Sole Evidence**: Never use alone for attribution
2. **Real-Time Tracking**: Not designed for live surveillance
3. **Mass Surveillance**: Not appropriate for dragnet analysis
4. **Proof**: Cannot provide definitive proof

## References

### TOR Protocol

- TOR Path Selection: https://spec.torproject.org/path-spec
- TOR Protocol Specification: https://spec.torproject.org/tor-spec
- TOR Directory Protocol: https://spec.torproject.org/dir-spec

### Research Background

- Timing Correlation Attacks (academic research)
- Traffic Analysis on TOR (published literature)
- Guard Node Behavior (TOR Project research)

### Legal Framework

- Lawful Intercept Guidelines
- Data Protection Regulations
- Law Enforcement Use of Technical Tools

---

**Disclaimer**: This methodology is for educational and authorized law enforcement use only. Any deployment must comply with applicable laws and regulations.
