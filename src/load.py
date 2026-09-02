from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values
from src.config import settings


TABLE_ORDER = ["fact_sales", "dim_date", "dim_product", "dim_customer"]


def connect():
    return psycopg2.connect(
        host=settings.host, port=settings.port, dbname=settings.database,
        user=settings.user, password=settings.password,
    )


def execute_schema(conn):
    schema_path = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"
    schema = schema_path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(schema)


def insert_frame(cur, table, frame):
    columns = list(frame.columns)
    query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES %s"
    def native(value):
        if str(value) in {"<NA>", "NaT", "nan"}:
            return None
        return value.item() if hasattr(value, "item") else value
    values = [tuple(native(v) for v in row) for row in frame.itertuples(index=False, name=None)]
    execute_values(cur, query, values, page_size=5000)


def full_refresh(result):
    with connect() as conn:
        execute_schema(conn)
        with conn.cursor() as cur:
            cur.execute("TRUNCATE fact_sales, dim_date, dim_product, dim_customer RESTART IDENTITY CASCADE")
            insert_frame(cur, "dim_customer", result.dim_customer)
            insert_frame(cur, "dim_product", result.dim_product)
            insert_frame(cur, "dim_date", result.dim_date)
            insert_frame(cur, "fact_sales", result.fact_sales)
