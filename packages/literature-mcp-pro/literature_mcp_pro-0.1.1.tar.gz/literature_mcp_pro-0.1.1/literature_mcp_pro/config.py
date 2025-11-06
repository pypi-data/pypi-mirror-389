"""Configuration management for Literature MCP Pro."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for the Literature MCP Pro server."""

    # API Keys
    PUBMED_API_KEY: Optional[str] = os.getenv("PUBMED_API_KEY")
    NCBI_EMAIL: Optional[str] = os.getenv("NCBI_EMAIL")
    GOOGLE_SCHOLAR_API_KEY: Optional[str] = os.getenv("GOOGLE_SCHOLAR_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

    # Database
    DATABASE_PATH: Path = Path(os.getenv("DATABASE_PATH", "./data/literature.db"))

    # Cache settings
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "86400"))  # 24 hours default
    CACHE_DIR: Path = Path("./data/cache")

    # Performance settings
    MAX_CONCURRENT_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # User agent for web requests
    USER_AGENT: str = "Literature-MCP-Pro/0.1.0 (https://github.com/yourusername/literature-mcp-pro)"

    # Data source URLs
    PUBMED_BASE_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    ARXIV_BASE_URL: str = "http://export.arxiv.org/api/"
    EUROPEPMC_BASE_URL: str = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
    CROSSREF_BASE_URL: str = "https://api.crossref.org/"

    # AI settings
    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-4")
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.7"))
    AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "2000"))

    @classmethod
    def ensure_directories(cls):
        """Ensure all necessary directories exist."""
        cls.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls) -> list[str]:
        """Validate configuration and return list of warnings/errors."""
        warnings = []
        
        if not cls.NCBI_EMAIL:
            warnings.append("NCBI_EMAIL not set - PubMed API may be rate-limited")
        
        if not cls.OPENAI_API_KEY and not cls.ANTHROPIC_API_KEY:
            warnings.append("No AI API key set - AI features will be disabled")
        
        return warnings


# Initialize directories on import
Config.ensure_directories()
