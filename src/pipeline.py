import sys
import logging
from pathlib import Path
from src.config import settings
from src.extract import extract_csv
from src.transform import transform
from src.load import full_refresh


logging.basicConfig(level=logging.INFO,format="%(asctime)s | %(levelname)s | %(message)s",stream=sys.stdout,)
log = logging.getLogger(__name__)


def run():
    log.info("Extracting %s", settings.input_csv)
    raw = extract_csv(settings.input_csv)
    log.info("Transforming %d raw rows", len(raw))
    result = transform(raw)

    rejected_path = Path(settings.rejected_csv)
    rejected_path.parent.mkdir(parents=True, exist_ok=True)
    result.rejected.to_csv(rejected_path, index=False)

    if result.fact_sales.empty:
        raise RuntimeError("No valid transactions remain after transformation")
    if result.fact_sales["sales_key"].duplicated().any():
        raise RuntimeError("Duplicate sales keys detected")
    if result.fact_sales["total_amount"].le(0).any():
        raise RuntimeError("Invalid non-positive sales amount detected")

    log.info("Loading PostgreSQL star schema")
    full_refresh(result)
    log.info(
        "ETL completed successfully | raw_rows=%d accepted_rows=%d rejected_rows=%d",
        len(raw), len(result.accepted), len(result.rejected),
    )


if __name__ == "__main__":
    run()
