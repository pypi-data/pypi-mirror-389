from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ragflow_api_key: str = ""
    ragflow_base_url: str = "http://10.130.10.2:3380"

    class Config:
        env_prefix = "RAGFLOW_"

settings = Settings()
