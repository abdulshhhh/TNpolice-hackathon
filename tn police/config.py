"""
Configuration management for TOR Correlation System
Centralized settings for all system components
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application-wide configuration settings
    Uses environment variables when available, falls back to defaults
    """
    
    # Application metadata
    APP_NAME: str = "TOR Metadata Correlation System"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Law enforcement analytical platform for TOR metadata correlation"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    API_DEBUG: bool = True
    
    # Project paths
    BASE_DIR: Path = Path(__file__).parent
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    OBSERVATIONS_DIR: Path = DATA_DIR / "observations"
    DATABASE_DIR: Path = BASE_DIR / "database"
    REPORTS_DIR: Path = BASE_DIR / "reports"
    
    # Database configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./database/tor_correlation.db"
    
    # TOR Network Data Sources
    # Official TOR Project consensus documents (public relay metadata)
    TOR_CONSENSUS_URL: str = "https://collector.torproject.org/recent/relay-descriptors/consensuses/"
    TOR_RELAY_DESCRIPTORS_URL: str = "https://collector.torproject.org/recent/relay-descriptors/server-descriptors/"
    TOR_METRICS_API: str = "https://onionoo.torproject.org/"
    
    # Data collection settings
    TOPOLOGY_REFRESH_INTERVAL: int = 3600  # seconds (1 hour)
    MAX_RELAY_AGE: int = 86400  # seconds (24 hours)
    ENABLE_AUTO_REFRESH: bool = False  # Manual refresh for PoC
    
    # Correlation Engine Settings
    # Time correlation window (how close entry/exit timestamps must be)
    TIME_CORRELATION_WINDOW: int = 300  # seconds (5 minutes)
    
    # Minimum confidence threshold for reporting (0-100)
    MIN_CONFIDENCE_THRESHOLD: float = 30.0
    
    # Guard node persistence window (how long to track guard usage)
    GUARD_PERSISTENCE_DAYS: int = 90
    
    # Analysis parameters
    MIN_OBSERVATIONS_FOR_CORRELATION: int = 3
    MAX_CONCURRENT_SESSIONS: int = 1000
    
    # Scoring weights (must sum to 1.0)
    WEIGHT_TIMING_SIMILARITY: float = 0.40
    WEIGHT_REPETITION_FREQUENCY: float = 0.30
    WEIGHT_NODE_STABILITY: float = 0.20
    WEIGHT_GRAPH_LIKELIHOOD: float = 0.10
    
    # Repeated observation weighting
    ENABLE_REPETITION_WEIGHTING: bool = True
    REPETITION_BOOST_FACTOR: float = 1.5  # Multiplier for repeated observations
    MIN_REPETITIONS_FOR_BOOST: int = 2   # Minimum repetitions to apply boost
    MAX_REPETITION_BOOST: float = 2.0    # Maximum boost multiplier
    
    # Forensic reporting
    REPORT_INCLUDE_RAW_DATA: bool = True
    REPORT_INCLUDE_METHODOLOGY: bool = True
    REPORT_INCLUDE_LIMITATIONS: bool = True
    
    # Legal & ethical safeguards
    ENABLE_ANONYMIZATION_CHECK: bool = True
    LOG_ALL_QUERIES: bool = True
    REQUIRE_CASE_NUMBER: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def create_directories(self):
        """Create all required directories if they don't exist"""
        directories = [
            self.DATA_DIR,
            self.RAW_DATA_DIR,
            self.PROCESSED_DATA_DIR,
            self.OBSERVATIONS_DIR,
            self.DATABASE_DIR,
            self.REPORTS_DIR,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
            # Create .gitkeep files for empty directories
            gitkeep = directory / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()


# Global settings instance
settings = Settings()

# Ensure directories exist on import
settings.create_directories()
