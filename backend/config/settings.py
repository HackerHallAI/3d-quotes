"""
Application settings and configuration for the 3D Quotes application.
"""
from typing import List

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # Application Settings
    app_name: str = Field(default="3D Quotes Tool", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    secret_key: str = Field(default="test-secret-key", env="SECRET_KEY")

    # Server Configuration
    host: str = Field(default="localhost", env="HOST")
    port: int = Field(default=8000, env="PORT")
    cors_origins: List[str] = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")

    # Stripe Configuration
    stripe_secret_key: str = Field(default="sk_test_fake", env="STRIPE_SECRET_KEY")
    stripe_publishable_key: str = Field(default="pk_test_fake", env="STRIPE_PUBLISHABLE_KEY")
    stripe_webhook_secret: str = Field(default="whsec_test_fake", env="STRIPE_WEBHOOK_SECRET")

    # Zoho Configuration
    zoho_client_id: str = Field(default="test_client_id", env="ZOHO_CLIENT_ID")
    zoho_client_secret: str = Field(default="test_client_secret", env="ZOHO_CLIENT_SECRET")
    zoho_refresh_token: str = Field(default="test_refresh_token", env="ZOHO_REFRESH_TOKEN")
    zoho_redirect_uri: str = Field(default="http://localhost:8000/auth/zoho/callback", env="ZOHO_REDIRECT_URI")
    zoho_scope: str = Field(default="ZohoCRM.modules.ALL,ZohoInventory.FullAccess.all", env="ZOHO_SCOPE")
    zoho_accounts_url: str = Field(default="https://accounts.zoho.com", env="ZOHO_ACCOUNTS_URL")
    zoho_crm_url: str = Field(default="https://www.zohoapis.com/crm/v2", env="ZOHO_CRM_URL")
    zoho_inventory_url: str = Field(default="https://www.zohoapis.com/inventory/v1", env="ZOHO_INVENTORY_URL")

    # Email Configuration
    smtp_host: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: str = Field(default="test@test.com", env="SMTP_USERNAME")
    smtp_password: str = Field(default="test_password", env="SMTP_PASSWORD")
    smtp_tls: bool = Field(default=True, env="SMTP_TLS")
    supplier_email: str = Field(default="supplier@test.com", env="SUPPLIER_EMAIL")

    # File Upload Configuration
    max_file_size: str = Field(default="50MB", env="MAX_FILE_SIZE")
    allowed_extensions: List[str] = Field(default=[".stl"], env="ALLOWED_EXTENSIONS")
    temp_upload_dir: str = Field(default="data/temp_uploads", env="TEMP_UPLOAD_DIR")
    file_cleanup_timeout: int = Field(default=3600, env="FILE_CLEANUP_TIMEOUT")

    # HP MJF Printer Constraints (in mm)
    hp_mjf_max_x: float = Field(default=380.0, env="HP_MJF_MAX_X")
    hp_mjf_max_y: float = Field(default=284.0, env="HP_MJF_MAX_Y")
    hp_mjf_max_z: float = Field(default=380.0, env="HP_MJF_MAX_Z")

    # Pricing Configuration
    minimum_order_usd: float = Field(default=20.0, env="MINIMUM_ORDER_USD")
    markup_percentage: float = Field(default=15.0, env="MARKUP_PERCENTAGE")
    currency: str = Field(default="USD", env="CURRENCY")

    # Material Pricing (per cm³)
    pa12_grey_rate: float = Field(default=0.50, env="PA12_GREY_RATE")
    pa12_black_rate: float = Field(default=0.55, env="PA12_BLACK_RATE")
    pa12_gb_rate: float = Field(default=0.60, env="PA12_GB_RATE")

    # Shipping Configuration (NZ)
    shipping_small_cost: float = Field(default=5.0, env="SHIPPING_SMALL_COST")
    shipping_medium_cost: float = Field(default=10.0, env="SHIPPING_MEDIUM_COST")
    shipping_large_cost: float = Field(default=15.0, env="SHIPPING_LARGE_COST")
    shipping_small_threshold: float = Field(default=100.0, env="SHIPPING_SMALL_THRESHOLD")
    shipping_medium_threshold: float = Field(default=500.0, env="SHIPPING_MEDIUM_THRESHOLD")

    # Database Configuration
    database_url: str = Field(default="sqlite:///./quotes.db", env="DATABASE_URL")

    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")

    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    @validator('allowed_extensions', pre=True)
    def parse_allowed_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(',')]
        return v

    @validator('max_file_size')
    def parse_max_file_size(cls, v):
        if isinstance(v, str):
            if v.upper().endswith('MB'):
                return int(v[:-2]) * 1024 * 1024
            elif v.upper().endswith('KB'):
                return int(v[:-2]) * 1024
            elif v.upper().endswith('GB'):
                return int(v[:-2]) * 1024 * 1024 * 1024
            else:
                return int(v)
        return v

    @property
    def material_rates(self) -> dict:
        """Get material rates as a dictionary."""
        return {
            "PA12_GREY": self.pa12_grey_rate,
            "PA12_BLACK": self.pa12_black_rate,
            "PA12_GB": self.pa12_gb_rate
        }

    @property
    def printer_constraints(self) -> dict:
        """Get printer constraints as a dictionary."""
        return {
            "max_x": self.hp_mjf_max_x,
            "max_y": self.hp_mjf_max_y,
            "max_z": self.hp_mjf_max_z
        }

    @property
    def shipping_costs(self) -> dict:
        """Get shipping costs as a dictionary."""
        return {
            "SMALL": self.shipping_small_cost,
            "MEDIUM": self.shipping_medium_cost,
            "LARGE": self.shipping_large_cost
        }

    @property
    def shipping_thresholds(self) -> dict:
        """Get shipping thresholds as a dictionary."""
        return {
            "SMALL": self.shipping_small_threshold,
            "MEDIUM": self.shipping_medium_threshold
        }

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
