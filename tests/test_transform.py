import pandas as pd
from src.transform import transform


def sample_frame():
    return pd.DataFrame([
        {"InvoiceNo": "100", "StockCode": "P1", "Description": "Mug", "Quantity": 2,
         "InvoiceDate": "2025-01-02 10:00", "UnitPrice": 5.0, "CustomerID": "C1", "Country": "UK"},
        {"InvoiceNo": "C101", "StockCode": "P2", "Description": "Bag", "Quantity": 1,
         "InvoiceDate": "2025-01-03 10:00", "UnitPrice": 8.0, "CustomerID": "C2", "Country": "UK"},
        {"InvoiceNo": "102", "StockCode": "P2", "Description": "Bag", "Quantity": -1,
         "InvoiceDate": "2025-01-04 10:00", "UnitPrice": 8.0, "CustomerID": None, "Country": "FR"},
    ])


def test_transform_accepts_and_rejects_expected_rows():
    result = transform(sample_frame())
    assert len(result.accepted) == 1
    assert len(result.rejected) == 2
    assert set(result.rejected["rejection_reason"]) == {"cancelled_invoice", "non_positive_quantity"}
    assert result.fact_sales.iloc[0]["total_amount"] == 10.0


def test_star_schema_keys_are_populated():
    result = transform(sample_frame())
    assert result.fact_sales[["customer_key", "product_key", "date_key"]].notna().all().all()
    assert result.dim_customer["customer_id"].is_unique
    assert result.dim_product["stock_code"].is_unique


def test_numeric_customer_ids_do_not_keep_csv_float_suffix():
    raw = sample_frame()
    raw.loc[0, "CustomerID"] = 12345.0

    result = transform(raw)

    assert "12345" in set(result.dim_customer["customer_id"])

