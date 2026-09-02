-- Null checks in required fact columns.
SELECT COUNT(*) AS null_required_fields
FROM fact_sales
WHERE invoice_no IS NULL OR customer_key IS NULL OR product_key IS NULL
   OR date_key IS NULL OR total_amount IS NULL;

-- Invalid numeric measures.
SELECT COUNT(*) AS invalid_measures
FROM fact_sales
WHERE quantity <= 0 OR unit_price <= 0 OR total_amount <= 0;

-- Orphan foreign keys (expected: zero rows).
SELECT 'customer' AS relationship, COUNT(*) AS orphan_rows
FROM fact_sales f LEFT JOIN dim_customer d USING (customer_key)
WHERE d.customer_key IS NULL
UNION ALL
SELECT 'product', COUNT(*)
FROM fact_sales f LEFT JOIN dim_product d USING (product_key)
WHERE d.product_key IS NULL
UNION ALL
SELECT 'date', COUNT(*)
FROM fact_sales f LEFT JOIN dim_date d USING (date_key)
WHERE d.date_key IS NULL;

-- Row-count summary for pipeline evidence.
SELECT 'fact_sales' AS table_name, COUNT(*) AS row_count FROM fact_sales
UNION ALL SELECT 'dim_customer', COUNT(*) FROM dim_customer
UNION ALL SELECT 'dim_product', COUNT(*) FROM dim_product
UNION ALL SELECT 'dim_date', COUNT(*) FROM dim_date;

