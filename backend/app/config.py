from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gigachat_credentials: str = ""
    gigachat_scope: str = "GIGACHAT_API_PERS"
    gigachat_model: str = "GigaChat"
    gigachat_verify_ssl_certs: bool = False

    database_url: str = "postgresql+psycopg://solyaris:solyaris@localhost:5432/solyaris"
    backend_cors_origins: str = "http://localhost:5173,http://localhost:8080"
    data_dir: str = "data"

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.backend_cors_origins.split(",") if item.strip()]

    @property
    def gigachat_ready(self) -> bool:
        return bool(self.gigachat_credentials.strip())


settings = Settings()
