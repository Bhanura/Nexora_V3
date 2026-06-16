"""
Configuration management for Nexora001. 
Loads settings from environment variables with validation.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from dotenv import load_dotenv

# Load .env file from project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MongoDB Configuration
    mongodb_uri: str = Field(
        default="",
        description="MongoDB Atlas connection string"
    )
    mongodb_database: str = Field(
        default="nexora001",
        description="MongoDB database name"
    )
    
    # Google AI Configuration
    google_api_key: str = Field(
        default="",
        description="Google Gemini API key"
    )
    
    # Vector Search Configuration
    use_qdrant: bool = Field(
        default=True,
        description="Use Qdrant for vector search (True) or MongoDB Atlas (False)"
    )
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Qdrant server URL"
    )
    qdrant_api_key: Optional[str] = Field(
        default=None,
        description="Qdrant API key (optional, for cloud instances)"
    )
    
    # Application Configuration
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    environment: str = Field(default="development")
    
    # Crawling Configuration
    crawl_delay: float = Field(default=1.0)
    max_crawl_depth: int = Field(default=2)
    user_agent: str = Field(default="Nexora001-Bot/1.0")
    respect_robots_txt: bool = Field(default=True)
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    
    # Security
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT secret key for token generation"
    )
    
    # Use model_config instead of inner Config class (Pydantic v2 style)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # This allows extra env variables without error
    )
    
    @property
    def is_configured(self) -> bool:
        """Check if all required settings are configured."""
        mongodb_ok = (
            bool(self.mongodb_uri) and 
            "mongodb" in self.mongodb_uri. lower() and
            "<" not in self. mongodb_uri
        )
        google_ok = (
            bool(self. google_api_key) and 
            len(self.google_api_key) > 10 and
            not self.google_api_key.startswith("your_")
        )
        return mongodb_ok and google_ok


# Create settings instance
try:
    settings = Settings()
except Exception as e:
    print(f"Error loading settings: {e}")
    # Create with defaults if loading fails
    settings = Settings(
        mongodb_uri="",
        mongodb_database="nexora001",
        google_api_key="",
        debug=True,
        log_level="INFO",
        environment="development",
        crawl_delay=1.0,
        max_crawl_depth=2,
        user_agent="Nexora001-Bot/1. 0",
        respect_robots_txt=True,
        api_host="0. 0.0.0",
        api_port=8000
    )


def print_config_status():
    """Print configuration status for debugging."""
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    table = Table(title="Nexora001 Configuration Status")
    table. add_column("Setting", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Value", style="yellow")
    
    # MongoDB
    if settings.mongodb_uri and "<" not in settings. mongodb_uri and "mongodb" in settings. mongodb_uri.lower():
        mongo_status = "✅ Configured"
        mongo_display = settings.mongodb_uri[:40] + "..." if len(settings.mongodb_uri) > 40 else settings. mongodb_uri
    else:
        mongo_status = "❌ Not Set"
        mongo_display = "Not configured"
    table.add_row("MongoDB URI", mongo_status, mongo_display)
    
    table.add_row("MongoDB Database", "✅ Set", settings.mongodb_database)
    
    # Google API
    if settings. google_api_key and len(settings. google_api_key) > 10 and not settings.google_api_key. startswith("your_"):
        google_status = "✅ Configured"
        google_display = "***hidden***"
    else:
        google_status = "❌ Not Set"
        google_display = "Not configured"
    table.add_row("Google API Key", google_status, google_display)
    
    # Qdrant
    if settings.use_qdrant:
        qdrant_display = settings.qdrant_url
        table.add_row("Vector Search", "✅ Qdrant", qdrant_display)
    else:
        table.add_row("Vector Search", "⚠️ MongoDB Atlas", "Legacy mode")
    
    # Other settings
    table. add_row("Environment", "✅ Set", settings.environment)
    table. add_row("Debug Mode", "✅ Set", str(settings.debug))
    table.add_row("Log Level", "✅ Set", settings.log_level)
    table.add_row("Crawl Delay", "✅ Set", str(settings. crawl_delay))
    
    console.print(table)
    
    if not settings.is_configured:
        console.print("\n[bold red]⚠️  Some required settings are missing![/bold red]")
        console.print("Please update your .env file with valid values.\n")
    else:
        console.print("\n[bold green]✅ All required settings configured![/bold green]\n")


if __name__ == "__main__":
    print_config_status()