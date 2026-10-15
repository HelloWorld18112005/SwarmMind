"""Application configuration using Pydantic Settings."""

from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", description="Environment: development, test, production")
    app_secret_key: str = Field(default="dev-secret-key-swarmmind-hackathon-2026", description="Application secret key")
    frontend_origin: str = Field(default="http://localhost:5173", description="Frontend origin for CORS")

    # Graph Persistence Backend
    graph_backend: Literal["local", "falkordb"] = Field(
        default="local",
        description="Graph storage backend ('local' for development, 'falkordb' for FalkorDB Cloud/Instance)",
    )

    # FalkorDB Cloud / Remote credentials
    falkordb_host: str = Field(default="", description="FalkorDB host endpoint")
    falkordb_port: int = Field(default=6379, description="FalkorDB port")
    falkordb_username: str = Field(default="", description="FalkorDB username")
    falkordb_password: str = Field(default="", description="FalkorDB password")
    falkordb_ssl: bool = Field(default=True, description="Enable SSL/TLS for FalkorDB connection")
    falkordb_graph: str = Field(default="swarmmind", description="Graph identifier/name")

    # LLM Settings
    llm_provider: str = Field(default="mock", description="LLM provider: mock, gemini, openai, anthropic")
    llm_api_key: str = Field(default="", description="API key for selected LLM provider")
    llm_model: str = Field(default="", description="LLM model name")

    # Swarm Execution Budgets
    max_concurrent_agents: int = Field(default=3, description="Max concurrent agents executing tasks")
    max_agent_steps: int = Field(default=20, description="Max execution steps per agent in a run")
    max_run_duration_seconds: int = Field(default=600, description="Maximum total run timeout in seconds")


_settings_instance: Settings | None = None


def get_settings() -> Settings:
    """Retrieve cached application settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
