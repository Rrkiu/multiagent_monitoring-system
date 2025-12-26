from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Keys
    google_api_key: str

    # 프로젝트 설정
    project_name: str = "Safety Monitoring Multi-Agent System"
    debug: bool = True

    # 경로 설정
    data_dir: str = "./data"
    events_file: str = "./data/events.json"
    knowledge_base_dir: str = "./data/knowledge_base"
    chroma_persist_dir: str = "./data/vector_store"

    # 임베딩 설정
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # LLM 설정
    llm_model: str = "gemma-3-27b-it"
    llm_temperature: float = 0.7
    max_tokens: int = 2048

    # 멀티모달 설정
    vision_model: str = "gemini-2.5-flash-image"
    max_image_size_mb: int = 10
    supported_image_formats: list = ["jpg", "jpeg", "png", "webp", "gif"]
    image_upload_dir: str = "./data/uploaded_images"

    # JWT 인증 설정
    secret_key: str = "your-secret-key-change-this-in-production-min-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # 데이터베이스 설정
    database_url: str = "sqlite:///./data/safety_auth.db"

    class Config:
        env_file = ".env"
        case_sensitive = False


# 전역 설정 객체
settings = Settings()