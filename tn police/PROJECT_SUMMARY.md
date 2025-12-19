# TN Police Hackathon 2025 - Project Summary

## 🎯 Project Overview

**Name**: TOR Metadata Correlation System  
**Purpose**: Law enforcement analytical platform for TOR network metadata correlation  
**Target**: Tamil Nadu Police Hackathon 2025  
**Status**: Production-ready proof-of-concept  

## ⚖️ Legal & Ethical Framework

### ✅ What This System Does (LEGAL)

1. **Public Data Analysis**
   - Uses only publicly available TOR relay metadata
   - Sources data from official TOR Project APIs
   - No unauthorized data collection

2. **Statistical Correlation**
   - Analyzes timing patterns between observations
   - Performs probabilistic inference
   - Generates investigative leads with confidence scores

3. **Transparent Methodology**
   - All algorithms are explainable
   - Confidence scores show reasoning
   - Audit trail for all queries

### ❌ What This System Does NOT Do (ETHICAL BOUNDARIES)

1. **Does NOT break TOR**
   - No encryption breaking
   - No deanonymization of users
   - No traffic decryption

2. **Does NOT identify individuals**
   - Provides probabilistic leads only
   - Requires validation with additional evidence
   - Not sufficient for attribution alone

3. **Does NOT violate privacy**
   - No payload inspection
   - Metadata-only analysis
   - Designed for lawful use only

## 🏗️ System Architecture

```
TOR Correlation System
│
├── Data Ingestion Layer
│   ├── TOR Topology Engine
│   │   ├── Fetches public relay metadata (Onionoo API)
│   │   ├── Parses relay descriptors
│   │   └── Creates time-aware snapshots
│   │
│   └── Traffic Observation Layer
│       ├── Accepts timing-only metadata
│       ├── Supports synthetic data generation
│       └── Normalizes into unified schema
│
├── Analysis Engine
│   ├── Correlation Engine
│   │   ├── Time-based entry-exit correlation
│   │   ├── Volume similarity analysis
│   │   ├── Pattern matching
│   │   └── Guard node inference
│   │
│   └── Graph Analyzer
│       ├── TOR topology modeling
│       ├── Path feasibility checking
│       └── Probability estimation
│
├── Confidence Scoring
│   ├── Multi-signal composite scoring
│   ├── Explainable reasoning
│   └── Uncertainty quantification
│
└── API Layer (FastAPI)
    ├── RESTful endpoints
    ├── JSON responses
    └── Interactive documentation
```

## 🔧 Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.11+ |
| API Framework | FastAPI | 0.109.0 |
| Data Processing | Pandas | 2.1.4 |
| Graph Analysis | NetworkX | 3.2.1 |
| HTTP Client | httpx/aiohttp | Latest |
| Database | SQLite | Built-in |
| Server | Uvicorn | 0.27.0 |

## 📁 Project Structure

```
tn police/
├── app/
│   ├── api/              # FastAPI routes
│   │   └── routes.py
│   ├── core/             # Core business logic
│   │   ├── topology/     # TOR topology engine
│   │   │   ├── engine.py
│   │   │   └── graph_analyzer.py
│   │   └── correlation/  # Correlation algorithms
│   │       └── engine.py
│   ├── models/           # Data models
│   │   ├── topology.py
│   │   └── correlation.py
│   └── utils/            # Utilities
│       ├── synthetic_data.py
│       └── logging_config.py
│
├── data/                 # Data storage
│   ├── raw/             # Raw TOR metadata
│   ├── processed/       # Topology snapshots
│   └── observations/    # Traffic observations
│
├── database/            # SQLite databases
├── reports/             # Generated reports
├── tests/              # Unit & integration tests
├── docs/               # Documentation
│
├── config.py           # Configuration management
├── main.py            # FastAPI application
├── run.py             # Entry point
└── requirements.txt   # Dependencies
```

## 🚀 Quick Start Guide

### Installation

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
python run.py
```

### Access Points

- **API Server**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### Basic Workflow

```bash
# 1. Fetch TOR topology (limited for testing)
curl -X POST "http://localhost:8000/api/topology/fetch?limit=100"

# 2. Generate synthetic test data
curl -X POST "http://localhost:8000/api/observations/generate-synthetic?num_sessions=10&num_noise=20"

# 3. Run correlation analysis
curl -X POST "http://localhost:8000/api/correlation/analyze"

# 4. View results
curl "http://localhost:8000/api/correlation/summary"
```

## 🧪 Testing

```bash
# Run unit tests
pytest tests/test_topology.py -v
pytest tests/test_correlation.py -v

# Run integration test
pytest tests/test_integration.py -v

# Run all tests
pytest tests/ -v
```

## 📊 Key Features

### 1. TOR Topology Engine

- Fetches live TOR network data from official sources
- Maintains time-aware topology snapshots
- Parses ~7,000 relays with full metadata
- Graph-based network modeling

**Output**: Complete TOR network graph with relay capabilities

### 2. Correlation Engine

- Time-based entry-exit correlation
- Volume similarity analysis
- Pattern matching algorithms
- Composite confidence scoring

**Output**: Ranked session pairs with confidence scores (0-100%)

### 3. Cluster Analysis

- Detects repeated behavioral patterns
- Identifies guard node persistence
- Groups related observations
- Temporal pattern recognition

**Output**: Correlation clusters with reasoning

### 4. Explainable AI

Every result includes:
- Confidence score breakdown
- Reasoning for scores
- Contributing factors
- Uncertainty levels

### 5. RESTful API

- Complete CRUD operations
- JSON-based communication
- Auto-generated documentation
- Error handling and validation

## 📈 Confidence Scoring Methodology

### Session Pair Confidence

```
correlation_strength = 
    (time_correlation × 40%) +
    (volume_similarity × 30%) +
    (pattern_similarity × 30%)
```

**Interpretation**:
- **70-100%**: High confidence - strong evidence
- **40-70%**: Medium confidence - possible correlation
- **0-40%**: Low confidence - weak or spurious

### Guard Inference Confidence

```
guard_confidence = 
    (base_correlation × 70%) +
    (guard_selection_probability × 30%)
```

### Cluster Confidence

```
cluster_confidence = 
    (consistency_score × 60%) +
    (guard_persistence × 40%)
```

## 🎓 Use Cases

### Investigative Scenarios

1. **Pattern Recognition**
   - Identify repeated TOR usage patterns
   - Detect consistent guard node selection
   - Find temporal clusters in activity

2. **Lead Generation**
   - Generate ranked list of probable guards
   - Prioritize investigation targets
   - Focus resources on high-confidence leads

3. **Behavioral Analysis**
   - Understand TOR usage patterns
   - Identify persistence behaviors
   - Map activity timelines

## ⚠️ Important Limitations

### What Investigators Must Understand

1. **Probabilistic Nature**
   - Outputs are hypotheses, not proof
   - Confidence scores indicate likelihood, not certainty
   - Multiple competing hypotheses are normal

2. **Validation Required**
   - Never use as sole evidence
   - Requires corroboration with other intelligence
   - Manual review essential

3. **False Positives**
   - Coincidental correlations occur
   - Busy time periods increase false matches
   - Filtering and validation critical

4. **Technical Constraints**
   - Cannot break TOR encryption
   - Cannot identify end users
   - Cannot decrypt communications
   - Metadata analysis only

## 🔐 Security & Deployment

### For Production Deployment

1. **Authentication & Authorization**
   - Implement API authentication (OAuth2/JWT)
   - Role-based access control
   - Case number tracking mandatory

2. **Data Protection**
   - Encrypt databases
   - Secure API with HTTPS/TLS
   - Audit logging for all queries

3. **Legal Compliance**
   - Require case authorization
   - Log investigator IDs
   - Maintain chain of custody
   - Document limitations

4. **Infrastructure**
   - Replace SQLite with PostgreSQL
   - Implement rate limiting
   - Add caching layer
   - Deploy behind firewall

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Project overview |
| [docs/API_USAGE.md](docs/API_USAGE.md) | API guide with examples |
| [docs/METHODOLOGY.md](docs/METHODOLOGY.md) | Technical methodology |
| This file | Project summary |

## 🏆 Hackathon Submission Highlights

### Innovation

1. **Novel Approach**: Combines multiple weak signals for robust correlation
2. **Explainable AI**: Transparent reasoning for all outputs
3. **Legal Framework**: Explicitly designed within ethical boundaries
4. **Production-Ready**: Clean architecture, comprehensive testing

### Technical Excellence

1. **Clean Code**: Modular, well-documented, follows best practices
2. **Scalable Design**: Can handle full TOR network (~7,000 relays)
3. **Comprehensive Testing**: Unit tests, integration tests included
4. **API-First**: RESTful design with auto-generated docs

### Practical Value

1. **Immediate Use**: Working proof-of-concept
2. **Investigative Value**: Generates actionable leads
3. **Extensible**: Easy to add new correlation algorithms
4. **Educational**: Clear methodology documentation

## 🎯 Demonstration Script

### For Hackathon Judges

```bash
# Terminal 1: Start the server
python run.py

# Terminal 2: Run demonstration
# 1. Fetch limited topology (fast)
curl -X POST "http://localhost:8000/api/topology/fetch?limit=50"

# 2. Generate realistic test data
curl -X POST "http://localhost:8000/api/observations/generate-synthetic?num_sessions=10&num_noise=15&guard_persistence=true"

# 3. Run analysis
curl -X POST "http://localhost:8000/api/correlation/analyze"

# 4. View results
curl "http://localhost:8000/api/correlation/summary" | python -m json.tool
```

**Expected Results**:
- 10 correlated session pairs (from synthetic data)
- 1-2 high-confidence clusters
- Clear guard node hypotheses
- Explainable confidence scores

### Interactive Demo

Visit: http://localhost:8000/docs

1. Try `POST /api/topology/fetch`
2. Try `POST /api/observations/generate-synthetic`
3. Try `POST /api/correlation/analyze`
4. Try `GET /api/correlation/summary`

## 📞 Technical Support

### Troubleshooting

**Issue**: Topology fetch fails
- **Solution**: Check internet connection, TOR API may be down

**Issue**: Low correlation scores
- **Solution**: Increase `num_sessions` for synthetic data

**Issue**: No clusters found
- **Solution**: Need minimum 3 observations per guard (configurable)

## 🎓 Learning Resources

### TOR Protocol
- https://www.torproject.org/
- https://spec.torproject.org/

### Traffic Analysis Research
- Academic papers on timing correlation
- TOR Project security research

## 📄 License & Attribution

**For Hackathon Use**: Educational and demonstration purposes

**Production Deployment**: Requires proper legal authorization and compliance review

---

## ✅ Checklist for Judges

- [x] Clear project structure
- [x] Well-documented code
- [x] Ethical framework documented
- [x] Working proof-of-concept
- [x] Comprehensive API
- [x] Unit tests included
- [x] Integration tests included
- [x] Methodology documentation
- [x] Usage examples
- [x] Production deployment guidance

---

**Built with precision for Tamil Nadu Police Hackathon 2025** 🚔

**Remember**: This is an investigative support tool, not a hacking system. Use responsibly and lawfully.
