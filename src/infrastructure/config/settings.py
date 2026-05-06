from functools import lru_cache

from cryptography.fernet import Fernet
from pydantic import Field, PostgresDsn, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Chave Fernet válida só para desenvolvimento (troque em produção).
_DEFAULT_DEV_FERNET_KEY = "n6o_Ef9ZJq2f4hW-cWcLG3I8g4QxW2M_8SY2VvDdzfE="


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")

    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="techpanel", alias="POSTGRES_DB")

    jwt_secret_key: str = Field(default="secret", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    fernet_key: str = Field(default=_DEFAULT_DEV_FERNET_KEY, alias="FERNET_KEY")

    github_client_id: str | None = Field(default=None, alias="GITHUB_CLIENT_ID")
    github_client_secret: str | None = Field(default=None, alias="GITHUB_CLIENT_SECRET")
    github_oauth_callback_url: str | None = Field(
        default=None, alias="GITHUB_OAUTH_CALLBACK_URL"
    )
    github_oauth_scope: str = Field(default="repo,read:org", alias="GITHUB_OAUTH_SCOPE")
    frontend_dev_server_url: str | None = Field(
        default="http://localhost:5173",
        alias="FRONTEND_DEV_SERVER_URL",
    )

    @field_validator("fernet_key")
    @classmethod
    def validate_fernet_key(cls, value: str) -> str:
        key = (value or "").strip()
        if not key:
            key = _DEFAULT_DEV_FERNET_KEY
        try:
            Fernet(key.encode("utf-8"))
        except ValueError as e:
            raise ValueError(
                "FERNET_KEY inválida: Fernet exige 32 bytes em base64 URL-safe. "
                'Gere com: python -c "from cryptography.fernet import Fernet; '
                'print(Fernet.generate_key().decode())"'
            ) from e
        return key

    @computed_field
    @property
    def database_url_async(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port,
                path=self.postgres_db,
            )
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
