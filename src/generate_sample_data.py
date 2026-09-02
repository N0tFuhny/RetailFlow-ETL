import argparse
from pathlib import Path
import numpy as np
import pandas as pd


PRODUCTS = [
    ("P001", "Ceramic Mug", 6.50), ("P002", "Canvas Tote Bag", 9.75),
    ("P003", "Desk Organizer", 12.00), ("P004", "Notebook Set", 7.25),
    ("P005", "Reusable Bottle", 15.50), ("P006", "LED Reading Lamp", 22.00),
    ("P007", "Phone Stand", 8.90), ("P008", "Wireless Mouse", 18.75),
    ("P009", "Travel Pouch", 11.40), ("P010", "Mechanical Pencil", 4.20),
]
COUNTRIES = ["United Kingdom", "France", "Germany", "Netherlands", "Spain"]


def generate(rows: int, output: str, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    product_idx = rng.integers(0, len(PRODUCTS), rows)
    dates = pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 365, rows), unit="D")
    dates += pd.to_timedelta(rng.integers(8 * 60, 21 * 60, rows), unit="m")
    invoice_ids = rng.integers(10000, 15500, rows).astype(str)
    cancelled = rng.random(rows) < 0.025
    invoice_ids = np.where(cancelled, np.char.add("C", invoice_ids), invoice_ids)
    customer_ids = rng.integers(12000, 12400, rows).astype(object)
    customer_ids[rng.random(rows) < 0.04] = None
    quantities = rng.integers(1, 12, rows)
    quantities[rng.random(rows) < 0.015] *= -1
    prices = np.array([PRODUCTS[i][2] for i in product_idx])
    prices = np.round(prices * rng.uniform(0.95, 1.08, rows), 2)
    prices[rng.random(rows) < 0.005] = 0

    df = pd.DataFrame({
        "InvoiceNo": invoice_ids,
        "StockCode": [PRODUCTS[i][0] for i in product_idx],
        "Description": [PRODUCTS[i][1] for i in product_idx],
        "Quantity": quantities,
        "InvoiceDate": dates,
        "UnitPrice": prices,
        "CustomerID": customer_ids,
        "Country": rng.choice(COUNTRIES, rows, p=[0.64, 0.10, 0.11, 0.07, 0.08]),
    })
    # Add a few exact duplicates to prove the validation path works.
    duplicates = df.sample(min(20, rows), random_state=seed)
    df = pd.concat([df, duplicates], ignore_index=True)
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=25000)
    parser.add_argument("--output", default="data/raw/online_retail.csv")
    args = parser.parse_args()
    result = generate(args.rows, args.output)
    print(f"Generated {len(result):,} rows at {args.output}")

