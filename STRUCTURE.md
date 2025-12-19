# Project Structure

```
tn police/
│
├── 📄 README.md                    # Main project documentation
├── 📄 QUICKSTART.md                # 5-minute setup guide
├── 📄 PROJECT_SUMMARY.md           # Comprehensive project overview
├── 📄 requirements.txt             # Python dependencies
├── 📄 .gitignore                   # Git ignore patterns
├── 📄 .env.example                 # Environment configuration template
│
├── 📄 config.py                    # Application configuration
├── 📄 main.py                      # FastAPI application
├── 📄 run.py                       # Application entry point
│
├── 📁 app/                         # Main application code
│   ├── 📄 __init__.py
│   │
│   ├── 📁 api/                     # API layer
│   │   ├── 📄 __init__.py
│   │   └── 📄 routes.py            # API endpoints
│   │
│   ├── 📁 core/                    # Core business logic
│   │   ├── 📄 __init__.py
│   │   │
│   │   ├── 📁 topology/            # TOR topology engine
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 engine.py        # Topology fetching & management
│   │   │   └── 📄 graph_analyzer.py # Graph-based analysis
│   │   │
│   │   └── 📁 correlation/         # Correlation engine
│   │       ├── 📄 __init__.py
│   │       └── 📄 engine.py        # Correlation algorithms
│   │
│   ├── 📁 models/                  # Data models
│   │   ├── 📄 __init__.py
│   │   ├── 📄 topology.py          # Topology data models
│   │   └── 📄 correlation.py       # Correlation data models
│   │
│   └── 📁 utils/                   # Utilities
│       ├── 📄 __init__.py
│       ├── 📄 synthetic_data.py    # Synthetic data generator
│       └── 📄 logging_config.py    # Logging configuration
│
├── 📁 docs/                        # Documentation
│   ├── 📄 API_USAGE.md             # API usage guide with examples
│   └── 📄 METHODOLOGY.md           # Technical methodology
│
├── 📁 tests/                       # Test suite
│   ├── 📄 __init__.py
│   ├── 📄 test_topology.py         # Topology engine tests
│   ├── 📄 test_correlation.py      # Correlation engine tests
│   └── 📄 test_integration.py      # Integration tests
│
├── 📁 data/                        # Data storage (created on first run)
│   ├── 📁 raw/                     # Raw TOR metadata cache
│   ├── 📁 processed/               # Processed topology snapshots
│   └── 📁 observations/            # Traffic observations
│
├── 📁 database/                    # Database files (created on first run)
│   └── 📄 tor_correlation.db       # SQLite database
│
├── 📁 reports/                     # Generated reports (created on first run)
│   └── ...                         # Forensic reports
│
└── 📁 logs/                        # Application logs (created on first run)
    └── 📄 tor_correlation_YYYYMMDD.log
```

## File Descriptions

### Root Level

| File | Purpose |
|------|---------|
| README.md | Project overview, architecture, and ethical framework |
| QUICKSTART.md | 5-minute setup and first-run guide |
| PROJECT_SUMMARY.md | Comprehensive hackathon submission summary |
| requirements.txt | Python package dependencies |
| config.py | Centralized configuration management |
| main.py | FastAPI application initialization |
| run.py | Application entry point |

### Application Code (`app/`)

#### API Layer (`app/api/`)
- **routes.py**: All REST API endpoints
  - Topology management
  - Observation ingestion
  - Correlation analysis
  - Results retrieval

#### Core Logic (`app/core/`)

**Topology Module** (`app/core/topology/`)
- **engine.py**: TOR topology fetching and management
  - Fetches from Onionoo API
  - Parses relay descriptors
  - Creates snapshots
- **graph_analyzer.py**: Graph-based network analysis
  - Path feasibility checking
  - Probability estimation
  - Constraint validation

**Correlation Module** (`app/core/correlation/`)
- **engine.py**: Correlation algorithms
  - Time correlation
  - Volume similarity
  - Pattern matching
  - Cluster analysis
  - Confidence scoring

#### Data Models (`app/models/`)
- **topology.py**: TOR network data structures
  - TORRelay
  - TopologySnapshot
  - TORCircuit
  - RelayEdge
- **correlation.py**: Correlation data structures
  - TrafficObservation
  - SessionPair
  - CorrelationCluster

#### Utilities (`app/utils/`)
- **synthetic_data.py**: Test data generation
- **logging_config.py**: Logging setup

### Documentation (`docs/`)

| File | Content |
|------|---------|
| API_USAGE.md | API endpoint reference and examples |
| METHODOLOGY.md | Technical methodology and algorithms |

### Tests (`tests/`)

| File | Tests |
|------|-------|
| test_topology.py | Topology engine unit tests |
| test_correlation.py | Correlation engine unit tests |
| test_integration.py | End-to-end integration test |

### Data Directories

Created automatically on first run:

- **data/raw/**: Cached TOR metadata from API
- **data/processed/**: Topology snapshot JSON files
- **data/observations/**: Stored traffic observations
- **database/**: SQLite database files
- **reports/**: Generated forensic reports
- **logs/**: Application log files

## Module Dependencies

```
main.py
└── app/
    ├── api/routes.py
    │   ├── models/topology.py
    │   ├── models/correlation.py
    │   ├── core/topology/engine.py
    │   ├── core/correlation/engine.py
    │   └── utils/synthetic_data.py
    │
    ├── core/topology/engine.py
    │   ├── models/topology.py
    │   └── config.py
    │
    ├── core/topology/graph_analyzer.py
    │   └── models/topology.py
    │
    ├── core/correlation/engine.py
    │   ├── models/correlation.py
    │   ├── models/topology.py
    │   ├── core/topology/graph_analyzer.py
    │   └── config.py
    │
    └── utils/synthetic_data.py
        ├── models/correlation.py
        └── models/topology.py
```

## Key Design Patterns

### 1. Modular Architecture
- Clear separation of concerns
- Loosely coupled components
- Easy to test and extend

### 2. Configuration Management
- Centralized in `config.py`
- Environment variable support
- Sensible defaults

### 3. Data Models
- Pydantic models for validation
- Type safety
- JSON serialization

### 4. Async/Await
- Async HTTP requests
- Non-blocking I/O
- Better performance

### 5. Explainability
- Every score has reasoning
- Transparent algorithms
- Audit trails

## Code Statistics

- **Python files**: ~2,500 lines
- **Documentation**: ~2,000 lines
- **Test coverage**: Core modules
- **API endpoints**: 15+
- **Data models**: 10+

## Technology Stack Summary

| Layer | Technology |
|-------|-----------|
| API Framework | FastAPI 0.109.0 |
| Data Processing | Pandas 2.1.4 |
| Graph Analysis | NetworkX 3.2.1 |
| HTTP Client | httpx + aiohttp |
| Data Validation | Pydantic 2.5.3 |
| Database | SQLite + aiosqlite |
| Server | Uvicorn 0.27.0 |
| Testing | pytest + pytest-asyncio |

---

**Project Status**: ✅ Production-ready proof-of-concept

**Last Updated**: December 20, 2025
