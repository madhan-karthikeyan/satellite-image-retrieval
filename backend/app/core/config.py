from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    APP_NAME: str = "Satellite Visual Search"
    DEBUG: bool = True
    
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    CHROMA_DIR: Path = BASE_DIR / "chroma_db"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    DATA_DIR: Path = BASE_DIR / "data"
    
    EMBEDDING_MODEL: str = "resnet50"
    EMBEDDING_DIM: int = 2048
    DEVICE: str = "cuda"
    
    SEARCH_THRESHOLD: float = 0.65
    MAX_RESULTS: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
