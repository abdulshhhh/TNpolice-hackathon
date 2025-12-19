# API Usage Guide

## TOR Metadata Correlation System - API Documentation

This guide provides practical examples for using the TOR Correlation System API.

## Quick Start

### 1. Start the Server

```bash
python run.py
```

Server will start at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### 2. Basic Workflow

#### Step 1: Fetch TOR Topology

```bash
# Fetch full topology (may take time)
curl -X POST "http://localhost:8000/api/topology/fetch"

# Fetch limited topology for testing
curl -X POST "http://localhost:8000/api/topology/fetch?limit=100"
```

**Response:**
```json
{
  "snapshot_id": "snapshot-20251220-120000",
  "total_relays": 100,
  "guard_relays": 35,
  "exit_relays": 20,
  "relays": [...]
}
```

#### Step 2: View Current Topology

```bash
curl "http://localhost:8000/api/topology/current"
```

#### Step 3: Get Guard and Exit Relays

```bash
# Get guard relays
curl "http://localhost:8000/api/topology/guards?limit=10"

# Get exit relays
curl "http://localhost:8000/api/topology/exits?limit=10"
```

#### Step 4: Generate Synthetic Test Data

```bash
curl -X POST "http://localhost:8000/api/observations/generate-synthetic?num_sessions=10&num_noise=20&guard_persistence=true"
```

**Response:**
```json
{
  "generated": 60,
  "correlated_sessions": 10,
  "noise_observations": 40,
  "total_observations": 60
}
```

#### Step 5: Run Correlation Analysis

```bash
curl -X POST "http://localhost:8000/api/correlation/analyze"
```

**Response:**
```json
{
  "observations_analyzed": 60,
  "entry_observations": 30,
  "exit_observations": 30,
  "session_pairs_found": 15,
  "clusters_identified": 2,
  "message": "Correlation analysis complete"
}
```

#### Step 6: View Results

**Get High-Confidence Session Pairs:**
```bash
curl "http://localhost:8000/api/correlation/pairs?min_confidence=70&limit=10"
```

**Get Correlation Clusters:**
```bash
curl "http://localhost:8000/api/correlation/clusters?min_confidence=50"
```

**Get Summary Statistics:**
```bash
curl "http://localhost:8000/api/correlation/summary"
```

**Get Repetition Statistics:**
```bash
curl "http://localhost:8000/api/correlation/repetition-stats"
```

## API Endpoints Reference

### General Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | System information and legal notice |
| `/api/health` | GET | Health check |

### Topology Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/topology/fetch` | POST | Fetch current TOR topology |
| `/api/topology/current` | GET | Get loaded topology |
| `/api/topology/snapshots` | GET | List all saved snapshots |
| `/api/topology/guards` | GET | Get guard-capable relays |
| `/api/topology/exits` | GET | Get exit-capable relays |

### Observations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/observations/add` | POST | Add traffic observation |
| `/api/observations/list` | GET | List stored observations |
| `/api/observations/generate-synthetic` | POST | Generate test data |

### Correlation Analysis

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/correlation/analyze` | POST | Run correlation analysis |
| `/api/correlation/pairs` | GET | Get session pairs |
| `/api/correlation/clusters` | GET | Get correlation clusters |
| `/api/correlation/summary` | GET | Get analysis summary |
| `/api/correlation/repetition-stats` | GET | Get repetition weighting statistics |

## Example: Complete Analysis Workflow

```python
import httpx
import asyncio

async def run_analysis():
    client = httpx.AsyncClient(base_url="http://localhost:8000")
    
    # 1. Fetch topology (limited for speed)
    print("Fetching topology...")
    topology = await client.post("/api/topology/fetch?limit=100")
    print(f"Loaded {topology.json()['total_relays']} relays")
    
    # 2. Generate synthetic data
    print("\nGenerating synthetic observations...")
    gen_result = await client.post(
        "/api/observations/generate-synthetic",
        params={
            "num_sessions": 15,
            "num_noise": 30,
            "guard_persistence": True
        }
    )
    print(f"Generated {gen_result.json()['generated']} observations")
    
    # 3. Run correlation analysis
    print("\nRunning correlation analysis...")
    analysis = await client.post("/api/correlation/analyze")
    result = analysis.json()
    print(f"Found {result['session_pairs_found']} session pairs")
    print(f"Identified {result['clusters_identified']} clusters")
    
    # 4. Get high-confidence results
    print("\nHigh-confidence session pairs:")
    pairs = await client.get("/api/correlation/pairs?min_confidence=70")
    for pair in pairs.json()[:5]:
        print(f"  Pair {pair['pair_id']}: {pair['correlation_strength']:.1f}% confidence")
    
    # 5. Get clusters
    print("\nCorrelation clusters:")
    clusters = await client.get("/api/correlation/clusters?min_confidence=50")
    for cluster in clusters.json():
        print(f"  {cluster['cluster_id']}:")
        print(f"    - Observations: {cluster['observation_count']}")
        print(f"    - Confidence: {cluster['cluster_confidence']:.1f}%")
        print(f"    - Probable guards: {cluster['probable_guards']}")
    
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(run_analysis())
```

## Understanding the Output

### Session Pair Confidence Scores

Confidence scores (0-100%) are calculated using:

1. **Time Correlation (40%)**: How close entry/exit timestamps are
2. **Volume Similarity (30%)**: How similar data volumes are
3. **Pattern Similarity (30%)**: Inter-packet timing pattern matching

**Interpretation:**
- **70-100%**: High confidence - strong correlation
- **40-70%**: Medium confidence - possible correlation
- **0-40%**: Low confidence - weak or spurious correlation

### Correlation Clusters

Clusters represent repeated patterns across multiple sessions:

- **Guard Persistence**: Same guard used repeatedly (realistic user behavior)
- **Consistency Score**: How consistent the pattern is
- **Cluster Confidence**: Overall likelihood this represents real user behavior

## Legal and Ethical Considerations

**REMEMBER:**
- This system provides **investigative leads**, not proof
- Outputs are **probabilistic hypotheses**, requiring validation
- **No deanonymization** occurs - only metadata correlation
- Proper **legal authorization** required for operational use
- All analysis must comply with applicable laws

## Production Deployment Notes

For production use:

1. **Add Authentication**: Implement proper API authentication
2. **Add Case Tracking**: Require case numbers for all queries
3. **Database Integration**: Replace in-memory storage with proper database
4. **Rate Limiting**: Implement API rate limits
5. **Audit Logging**: Log all queries for accountability
6. **HTTPS**: Use TLS for all communications
7. **Access Control**: Implement role-based access control

## Support

For issues or questions about the system:
- Check API documentation: `/docs`
- Review source code comments
- Consult methodology documentation
