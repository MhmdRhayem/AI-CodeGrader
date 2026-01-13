from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application configuration."""

    # OpenAI Configuration
    openai_api_key: str
    model_name: Literal["gpt-4", "gpt-4-turbo", "gpt-4o"] = "gpt-4o"
    temperature: float = 0.3  # Lower for grading consistency
    max_tokens: int = 2000

    # FastAPI Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Gradio Configuration
    gradio_host: str = "0.0.0.0"
    gradio_port: int = 7860
    gradio_share: bool = False

    # Grading Strategy Parameters
    voting_num_voters: int = 5
    evaluator_optimizer_max_iterations: int = 3

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
