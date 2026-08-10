# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str
    API_V1_STR: str
    DATABASE_URL: str

    # Seguridad
    API_KEY: str = "super_secret_tour_os_key_2026_CAMBIAR_EN_PROD"
    FRONTEND_SECRET: str = "SST_FRONT_ACCESS_SECRET_2026"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Supabase Auth
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""  
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # n8n
    N8N_WEBHOOK_URL: str = "http://localhost:5678/webhook/formulario_de_reserva"
    N8N_WEBHOOK_UPDATE_URL: str = "http://localhost:5678/webhook/actualizacion-reserva"
    N8N_HEADER_NAME: str = "formulario_tours"
    N8N_HEADER_PASSWORD: str = "Aqui.no.se.roba"

    # Le decimos a Pydantic que busque estas variables en el archivo .env
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

# Instancia única (Singleton) para usar en todo el proyecto
settings = Settings()