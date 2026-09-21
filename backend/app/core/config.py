from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "METEORA AI Weather & Risk Advisory Engine"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # PostgreSQL Database URL
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/meteora_db"
    
    # Hugging Face AI / LLM Configuration
    HUGGINGFACE_API_KEY: Optional[str] = None
    HUGGINGFACE_MODEL_ID: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    HUGGINGFACE_DATASET_OWNER: str = ""
    HUGGINGFACE_DATASET_IDS: str = ""
    
    # Meteorological Feeds
    IMD_BULLETIN_API_URL: str = "https://mausam.imd.gov.in/api/warnings"
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1"
    OPEN_METEO_GEOCODING_URL: str = "https://geocoding-api.open-meteo.com/v1"
    
    # Server & CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
