from dataclasses import dataclass
import pandas as pd


@dataclass
class TransformResult:
    accepted: pd.DataFrame
    rejected: pd.DataFrame
    dim_customer: pd.DataFrame
    dim_product: pd.DataFrame
    dim_date: pd.DataFrame
    fact_sales: pd.DataFrame


def transform(raw: pd.DataFrame) -> TransformResult:
    df = raw.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    df = df.rename(columns={
        "invoiceno": "invoice_no", "stockcode": "stock_code",
        "invoicedate": "invoice_date", "unitprice": "unit_price",
        "customerid": "customer_id",
    })
    for col in ["invoice_no", "stock_code", "description", "customer_id", "country"]:
        df[col] = df[col].astype("string").str.strip()
    df["customer_id"] = df["customer_id"].str.replace(r"(?<=\d)\.0$", "", regex=True)
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    reasons = pd.Series("", index=df.index, dtype="string")
    def flag(mask, reason):
        nonlocal reasons
        reasons = reasons.mask(mask & (reasons == ""), reason)

    flag(df["invoice_no"].isna() | df["stock_code"].isna(), "missing_business_key")
    flag(df["invoice_date"].isna(), "invalid_invoice_date")
    flag(df["quantity"].isna() | (df["quantity"] <= 0), "non_positive_quantity")
    flag(df["unit_price"].isna() | (df["unit_price"] <= 0), "non_positive_unit_price")
    flag(df["invoice_no"].str.startswith("C", na=False), "cancelled_invoice")
    duplicate_key = ["invoice_no", "stock_code", "invoice_date"]
    flag(df.duplicated(duplicate_key, keep="first"), "duplicate_transaction")

    rejected = df.loc[reasons != ""].copy()
    rejected["rejection_reason"] = reasons[reasons != ""]
    accepted = df.loc[reasons == ""].copy()
    accepted["customer_id"] = accepted["customer_id"].fillna("UNKNOWN").astype("string")
    accepted["description"] = accepted["description"].fillna("Unknown Product")
    accepted["country"] = accepted["country"].fillna("Unknown")
    accepted["total_amount"] = (accepted["quantity"] * accepted["unit_price"]).round(2)
    accepted["date_key"] = accepted["invoice_date"].dt.strftime("%Y%m%d").astype(int)

    dim_customer = (accepted[["customer_id", "country"]]
                    .drop_duplicates("customer_id")
                    .sort_values("customer_id").reset_index(drop=True))
    dim_customer.insert(0, "customer_key", range(1, len(dim_customer) + 1))

    dim_product = (accepted[["stock_code", "description"]]
                   .drop_duplicates("stock_code")
                   .sort_values("stock_code").reset_index(drop=True))
    dim_product.insert(0, "product_key", range(1, len(dim_product) + 1))

    unique_dates = accepted["invoice_date"].dt.normalize().drop_duplicates().sort_values()
    dim_date = pd.DataFrame({"full_date": unique_dates.dt.date})
    date_series = pd.to_datetime(dim_date["full_date"])
    dim_date["date_key"] = date_series.dt.strftime("%Y%m%d").astype(int)
    dim_date["year"] = date_series.dt.year
    dim_date["quarter"] = date_series.dt.quarter
    dim_date["month"] = date_series.dt.month
    dim_date["month_name"] = date_series.dt.month_name()
    dim_date["day"] = date_series.dt.day
    dim_date["day_name"] = date_series.dt.day_name()
    dim_date = dim_date[["date_key", "full_date", "year", "quarter", "month", "month_name", "day", "day_name"]]

    fact = accepted.merge(dim_customer[["customer_key", "customer_id"]], on="customer_id")
    fact = fact.merge(dim_product[["product_key", "stock_code"]], on="stock_code")
    fact_sales = fact[[
        "invoice_no", "customer_key", "product_key", "date_key", "invoice_date",
        "quantity", "unit_price", "total_amount",
    ]].reset_index(drop=True)
    fact_sales.insert(0, "sales_key", range(1, len(fact_sales) + 1))

    return TransformResult(accepted, rejected, dim_customer, dim_product, dim_date, fact_sales)

