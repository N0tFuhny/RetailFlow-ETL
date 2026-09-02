from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    database: str = os.getenv("POSTGRES_DB", "retail_dw")
    user: str = os.getenv("POSTGRES_USER", "retail_user")
    password: str = os.getenv("POSTGRES_PASSWORD", "retail_password")
    input_csv: str = os.getenv("INPUT_CSV", "data/raw/online_retail.csv")
    rejected_csv: str = os.getenv("REJECTED_CSV", "data/rejected/rejected_rows.csv")


settings = Settings()

