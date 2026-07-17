from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MUFFIN API - Hospital Sub Regional de Andahuaylas"
    app_env: str = "development"
    database_url: str = "sqlite:///./muffin.db"
    jwt_secret: SecretStr = SecretStr("development-only-secret-change-before-deploy")
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    default_institution_name: str = "Hospital Sub Regional de Andahuaylas"
    default_institution_slug: str = "andahuaylas"
    bootstrap_admin_username: str | None = None
    bootstrap_admin_password: SecretStr | None = None
    bootstrap_admin_given_name: str = "Administrador"
    bootstrap_admin_family_name: str = "MUFFIN"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def ensure_secure_production_settings(self) -> None:
        secret = self.jwt_secret.get_secret_value()
        if self.app_env.lower() == "production" and (len(secret) < 32 or secret.startswith("development-only")):
            raise RuntimeError("JWT_SECRET must contain at least 32 unique characters in production.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
