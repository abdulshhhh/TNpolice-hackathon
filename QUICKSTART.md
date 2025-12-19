# Quick Start Guide

## TN Police Hackathon 2025 - TOR Correlation System

### Get Up and Running in 5 Minutes

---

## Step 1: Setup Environment

```powershell
# Navigate to project directory
cd "c:\Users\LENOVO\PROJECTSSS\tn police"

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Expected time**: 2-3 minutes

---

## Step 2: Start the Server

```powershell
# Run the application
python run.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Server is now running!** ✅

---

## Step 3: Open API Documentation

Open your browser and navigate to:

🌐 **http://localhost:8000/docs**

You'll see interactive API documentation (Swagger UI)

---

## Step 4: Run Your First Analysis

### Option A: Use Interactive API Docs

1. Go to http://localhost:8000/docs
2. Click on `POST /api/topology/fetch`
3. Click "Try it out"
4. Set `limit` to `50` (for speed)
5. Click "Execute"

**Wait ~10-15 seconds** for topology to load

6. Click on `POST /api/observations/generate-synthetic`
7. Click "Try it out"
8. Set parameters:
   - `num_sessions`: 10
   - `num_noise`: 15
   - `guard_persistence`: true
9. Click "Execute"

10. Click on `POST /api/correlation/analyze`
11. Click "Try it out"
12. Click "Execute"

13. Click on `GET /api/correlation/summary`
14. Click "Try it out"
15. Click "Execute"

**View your results!** 🎉

### Option B: Use Command Line (PowerShell)

Open a new terminal:

```powershell
# 1. Fetch topology
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/topology/fetch?limit=50"

# 2. Generate test data
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/observations/generate-synthetic?num_sessions=10&num_noise=15&guard_persistence=true"

# 3. Run analysis
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/correlation/analyze"

# 4. View results
Invoke-RestMethod -Uri "http://localhost:8000/api/correlation/summary" | ConvertTo-Json -Depth 10
```

---

## Step 5: Understand the Results

### What You'll See

```json
{
  "total_pairs": 15,
  "total_clusters": 2,
  "average_correlation": 75.3,
  "confidence_distribution": {
    "high_confidence (>=70%)": 8,
    "medium_confidence (40-70%)": 5,
    "low_confidence (<40%)": 2
  },
  "top_clusters": [
    {
      "cluster_id": "cluster-1",
      "confidence": 82.5,
      "observations": 10,
      "probable_guards": ["AAAA1111BBBB2222..."]
    }
  ]
}
```

### Interpretation

- **Total Pairs**: Number of correlated entry-exit observations
- **Clusters**: Repeated patterns (same guard usage)
- **Confidence**: Higher = stronger correlation
- **Probable Guards**: Hypothesized guard relays

---

## Step 6: Run Tests (Optional)

```powershell
# Install test dependencies (if not already installed)
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v

# Run integration test (demonstrates complete workflow)
pytest tests/test_integration.py -v
```

---

## Common Issues & Solutions

### Issue: "ModuleNotFoundError"
**Solution**: Make sure virtual environment is activated and dependencies installed
```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: "Port 8000 already in use"
**Solution**: Change port in config.py or kill process using port
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Issue: Topology fetch takes too long
**Solution**: Use smaller limit
```powershell
# Use limit=20 for very quick testing
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/topology/fetch?limit=20"
```

### Issue: No internet connection / TOR API unreachable
**Solution**: System needs internet to fetch TOR relay data. Check connection.

---

## What to Try Next

### Experiment with Parameters

```powershell
# Generate more correlated sessions
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/observations/generate-synthetic?num_sessions=20&num_noise=10&guard_persistence=true"

# Run analysis again
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/correlation/analyze"

# View high-confidence pairs only
Invoke-RestMethod -Uri "http://localhost:8000/api/correlation/pairs?min_confidence=70"
```

### Explore API Endpoints

Visit http://localhost:8000/docs and try:
- `/api/topology/guards` - See guard relays
- `/api/topology/exits` - See exit relays
- `/api/correlation/clusters` - View clusters

---

## Understanding the System

### What's Happening Behind the Scenes

1. **Topology Fetch**: Downloads public TOR relay metadata from official TOR Project API
2. **Synthetic Data**: Generates realistic TOR session observations with timing patterns
3. **Correlation**: Matches entry and exit observations using timing and volume similarity
4. **Clustering**: Groups sessions that share the same hypothesized guard relay

### Why This Matters for Law Enforcement

- **Lead Generation**: Identifies probable guard relays for investigation
- **Pattern Recognition**: Detects repeated behaviors over time
- **Confidence Scoring**: Ranks leads by likelihood
- **Explainable**: Shows reasoning for every correlation

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────┐
│                     TOR Network                         │
│  (7,000+ relays - public metadata from torproject.org) │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   Topology Engine             │
        │   - Fetches relay metadata    │
        │   - Builds network graph      │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   Traffic Observations        │
        │   - Entry/exit timestamps     │
        │   - Metadata only (no payload)│
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   Correlation Engine          │
        │   - Timing correlation        │
        │   - Volume similarity         │
        │   - Pattern matching          │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   Results & Confidence Scores │
        │   - Session pairs             │
        │   - Clusters                  │
        │   - Guard hypotheses          │
        └───────────────────────────────┘
```

---

## System Capabilities Summary

### ✅ What This System CAN Do

- Correlate timing patterns between observations
- Infer probable guard relays
- Detect behavioral patterns
- Generate ranked investigative leads
- Provide confidence scores with reasoning

### ❌ What This System CANNOT Do

- Break TOR encryption
- Deanonymize users
- Identify individuals
- Decrypt communications
- Provide definitive proof

**This is an investigative support tool, not a hacking system.**

---

## Next Steps

1. **Read Full Documentation**:
   - [README.md](README.md) - Project overview
   - [docs/API_USAGE.md](docs/API_USAGE.md) - Detailed API guide
   - [docs/METHODOLOGY.md](docs/METHODOLOGY.md) - Technical methodology
   - [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Complete summary

2. **Run Integration Test**:
   ```powershell
   pytest tests/test_integration.py -v -s
   ```
   This shows the complete workflow with detailed output.

3. **Explore the Code**:
   - `app/core/topology/engine.py` - TOR topology fetching
   - `app/core/correlation/engine.py` - Correlation algorithms
   - `app/api/routes.py` - API endpoints

4. **Customize for Your Needs**:
   - Edit `config.py` to adjust parameters
   - Modify correlation weights
   - Add new correlation algorithms

---

## Support & Resources

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/health

---

## Ready for Hackathon Presentation? ✅

You now have:
- ✅ Working proof-of-concept
- ✅ Interactive API
- ✅ Test data and results
- ✅ Documentation

**Good luck with the Tamil Nadu Police Hackathon 2025!** 🚔🏆

---

*Built with precision and ethics in mind.*
