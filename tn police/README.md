# TN Police Hackathon 2025 - TOR Metadata Correlation System

## Project Overview
This is a **proof-of-concept** investigative decision-support platform for the Tamil Nadu Police Hackathon 2025.

**Purpose**: Assist law enforcement in analyzing TOR network metadata using timing correlation and probabilistic inference.

## ⚖️ Legal & Ethical Boundaries

**CRITICAL CONSTRAINTS:**
- ✅ Uses ONLY publicly available TOR relay metadata
- ✅ Analyzes timing patterns and statistical correlations
- ✅ Generates probabilistic investigative leads with confidence scores
- ✅ All outputs are explainable and court-presentable
- ❌ Does NOT attempt to break TOR encryption
- ❌ Does NOT deanonymize individual users
- ❌ Does NOT decrypt or inspect traffic payloads
- ❌ Does NOT identify real-world individuals

**This is an analytical support tool, not a hacking system.**

## System Architecture

### 1. Data Ingestion & Topology Engine
- Fetches public TOR relay metadata from official sources
- Maintains time-aware snapshots of TOR network topology
- Builds graph-based representation of relay relationships

### 2. Traffic Observation Layer
- Processes timing-only metadata from synthetic/simulated sessions
- Normalizes observations into unified event schema
- No payload inspection - metadata only

### 3. Correlation & Analysis Engine
- Time-based entry-exit correlation analysis
- Guard node persistence pattern detection
- Cross-session pattern recognition
- Statistical inference using multiple weak signals

### 4. Confidence Scoring Engine
- Combines multiple correlation signals
- Generates explainable confidence percentages
- Logs reasoning for each score change
- Transparent evidence weighting

### 5. API & Visualization Layer
- RESTful API for system interaction
- JSON-formatted outputs for dashboards
- Graph and timeline visualizations

### 6. Forensic Report Generator
- Structured evidence summaries
- Timeline reconstructions
- Confidence explanations
- Explicit limitations documentation

## Tech Stack
- **Python**: 3.11+
- **API Framework**: FastAPI
- **Data Processing**: Pandas, NumPy
- **Graph Modeling**: NetworkX
- **Database**: SQLite
- **Export Formats**: JSON, CSV

## Project Structure
```
tor-correlation-system/
├── app/                          # Main application code
│   ├── api/                      # FastAPI routes and endpoints
│   ├── core/                     # Core business logic
│   │   ├── topology/            # TOR topology engine
│   │   ├── correlation/         # Correlation algorithms
│   │   ├── scoring/             # Confidence scoring
│   │   └── forensics/           # Report generation
│   ├── models/                   # Data models and schemas
│   ├── services/                 # Business logic services
│   └── utils/                    # Utilities and helpers
├── data/                         # Data storage
│   ├── raw/                     # Raw TOR metadata
│   ├── processed/               # Processed topologies
│   └── observations/            # Traffic observations
├── database/                     # SQLite database files
├── reports/                      # Generated forensic reports
├── tests/                        # Unit and integration tests
└── docs/                         # Additional documentation
```

## Installation

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the FastAPI server
python run.py

# Access API documentation
# http://localhost:8000/docs
```

## Development Guidelines

1. **Explainability First**: Every algorithm must log its reasoning
2. **Modular Design**: Keep components loosely coupled
3. **Strong Documentation**: Document investigative logic clearly
4. **Deterministic Logic**: Prefer explainable algorithms over black-box ML
5. **Auditability**: Every major output must be traceable

## Disclaimer

This system is a research prototype for educational and law enforcement training purposes. It is designed to assist investigators with lawful analysis of publicly available data. Any use must comply with applicable laws and regulations.

---

**Built for Tamil Nadu Police Hackathon 2025**
