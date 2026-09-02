-- 1. Monthly revenue and month-over-month growth: CTE + LAG window function.
WITH monthly_revenue AS (
    SELECT DATE_TRUNC('month', invoice_date)::date AS month,
           SUM(total_amount) AS revenue
    FROM fact_sales
    GROUP BY 1
), with_previous AS (
    SELECT month, revenue,
           LAG(revenue) OVER (ORDER BY month) AS previous_month_revenue
    FROM monthly_revenue
)
SELECT month, ROUND(revenue, 2) AS revenue,
       ROUND(100.0 * (revenue - previous_month_revenue)
             / NULLIF(previous_month_revenue, 0), 2) AS growth_pct
FROM with_previous
ORDER BY month;

-- 2. Top five products each month: CTE + RANK partitioned window.
WITH product_monthly_sales AS (
    SELECT DATE_TRUNC('month', f.invoice_date)::date AS month,
           p.stock_code, p.description,
           SUM(f.total_amount) AS revenue
    FROM fact_sales f
    JOIN dim_product p USING (product_key)
    GROUP BY 1, 2, 3
), ranked_products AS (
    SELECT *, RANK() OVER (PARTITION BY month ORDER BY revenue DESC) AS revenue_rank
    FROM product_monthly_sales
)
SELECT month, stock_code, description, ROUND(revenue, 2) AS revenue, revenue_rank
FROM ranked_products
WHERE revenue_rank <= 5
ORDER BY month, revenue_rank;

-- 3. Customer value segmentation: aggregation + CASE expression.
WITH customer_value AS (
    SELECT c.customer_id, c.country,
           COUNT(DISTINCT f.invoice_no) AS orders,
           SUM(f.total_amount) AS lifetime_value
    FROM fact_sales f
    JOIN dim_customer c USING (customer_key)
    GROUP BY c.customer_id, c.country
)
SELECT *,
       CASE
           WHEN lifetime_value >= 2000 THEN 'High Value'
           WHEN lifetime_value >= 750 THEN 'Medium Value'
           ELSE 'Standard'
       END AS customer_segment
FROM customer_value
ORDER BY lifetime_value DESC;

-- 4. Time between customer orders: LAG window function.
WITH customer_orders AS (
    SELECT DISTINCT c.customer_id, f.invoice_no, f.invoice_date::date AS order_date
    FROM fact_sales f
    JOIN dim_customer c USING (customer_key)
), order_history AS (
    SELECT *, LAG(order_date) OVER (
        PARTITION BY customer_id ORDER BY order_date, invoice_no
    ) AS previous_order_date
    FROM customer_orders
)
SELECT *, order_date - previous_order_date AS days_since_previous_order
FROM order_history
ORDER BY customer_id, order_date;

-- 5. CTAS: materialize an analytics-ready monthly product mart.
DROP TABLE IF EXISTS mart_monthly_product_sales;
CREATE TABLE mart_monthly_product_sales AS
SELECT DATE_TRUNC('month', f.invoice_date)::date AS month,
       p.product_key, p.stock_code, p.description,
       SUM(f.quantity) AS units_sold,
       ROUND(SUM(f.total_amount), 2) AS revenue
FROM fact_sales f
JOIN dim_product p USING (product_key)
GROUP BY 1, 2, 3, 4;

CREATE INDEX idx_mart_monthly_product_sales_month
    ON mart_monthly_product_sales(month);
