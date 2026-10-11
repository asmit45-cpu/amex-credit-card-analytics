/* ============================================================================
   AmEx Credit Card Customer Analytics - SQL Analysis
   Database: amex_analytics.db (SQLite)
   Tables: dim_customer, fact_monthly_spend, fact_transactions, customer_true_labels
   Period: Jul 2022 - Jun 2024 (monthly spend), Jul 2023 - Jun 2024 (transactions)
   Scale: 1,500 customers, 288,000 monthly-spend rows, 60,000 transactions
   ============================================================================ */


/* ----------------------------------------------------------------------------
   Q1. CUSTOMER SEGMENTATION BY CARD TYPE - average monthly spend & count
   Business use: understand portfolio mix and revenue contribution by tier
---------------------------------------------------------------------------- */
SELECT
    c.card_type,
    COUNT(DISTINCT c.customer_id)                          AS num_customers,
    ROUND(SUM(s.spend), 0)                                 AS total_spend_all_time,
    ROUND(SUM(s.spend) / COUNT(DISTINCT c.customer_id), 0) AS avg_lifetime_spend_per_customer
FROM dim_customer c
JOIN fact_monthly_spend s ON c.customer_id = s.customer_id
GROUP BY c.card_type
ORDER BY avg_lifetime_spend_per_customer DESC;


/* ----------------------------------------------------------------------------
   Q2. SPEND BY MERCHANT CATEGORY - where is wallet share concentrated
   Business use: co-brand partnership and rewards-category prioritisation
---------------------------------------------------------------------------- */
SELECT
    category,
    ROUND(SUM(spend), 0)                              AS total_spend,
    ROUND(100.0 * SUM(spend) / (SELECT SUM(spend) FROM fact_monthly_spend), 1) AS pct_of_total_spend
FROM fact_monthly_spend
GROUP BY category
ORDER BY total_spend DESC;


/* ----------------------------------------------------------------------------
   Q3. MONTHLY SPEND TREND (all customers combined) - seasonality check
   Business use: identify peak spend months for campaign timing
---------------------------------------------------------------------------- */
SELECT
    date,
    ROUND(SUM(spend), 0) AS total_spend
FROM fact_monthly_spend
GROUP BY date
ORDER BY date;


/* ----------------------------------------------------------------------------
   Q4. CUSTOMER MOMENTUM - recent 6-month spend vs prior 6-month spend
   (early-warning signal for churn - cross-checked against the Python
    classification model in 07_churn_model.py)
   Business use: flag accounts trending down before they go fully inactive
---------------------------------------------------------------------------- */
WITH monthly_cust AS (
    SELECT customer_id, date, SUM(spend) AS spend
    FROM fact_monthly_spend
    GROUP BY customer_id, date
),
recent AS (
    SELECT customer_id, AVG(spend) AS avg_recent
    FROM monthly_cust
    WHERE date >= '2024-01-01'
    GROUP BY customer_id
),
prior AS (
    SELECT customer_id, AVG(spend) AS avg_prior
    FROM monthly_cust
    WHERE date >= '2023-07-01' AND date < '2024-01-01'
    GROUP BY customer_id
)
SELECT
    c.customer_id,
    c.card_type,
    c.city,
    ROUND(p.avg_prior, 0)  AS avg_monthly_spend_prior_6mo,
    ROUND(r.avg_recent, 0) AS avg_monthly_spend_recent_6mo,
    ROUND(100.0 * (r.avg_recent - p.avg_prior) / p.avg_prior, 1) AS momentum_pct
FROM recent r
JOIN prior p ON r.customer_id = p.customer_id
JOIN dim_customer c ON c.customer_id = r.customer_id
ORDER BY momentum_pct ASC
LIMIT 20;
-- Most negative momentum_pct = highest churn-risk candidates


/* ----------------------------------------------------------------------------
   Q5. FRAUD RATE BY MERCHANT CATEGORY
   Business use: which merchant categories need tighter fraud rules
---------------------------------------------------------------------------- */
SELECT
    merchant_category,
    COUNT(*)                                            AS total_transactions,
    SUM(is_fraud)                                       AS fraud_transactions,
    ROUND(100.0 * SUM(is_fraud) / COUNT(*), 2)          AS fraud_rate_pct,
    ROUND(AVG(CASE WHEN is_fraud=1 THEN amount END), 0) AS avg_fraud_amount,
    ROUND(AVG(CASE WHEN is_fraud=0 THEN amount END), 0) AS avg_genuine_amount
FROM fact_transactions
GROUP BY merchant_category
ORDER BY fraud_rate_pct DESC;


/* ----------------------------------------------------------------------------
   Q6. FRAUD PATTERN - time of day analysis
   Business use: informs real-time fraud-rule thresholds (e.g. step-up auth
   for late-night transactions)
---------------------------------------------------------------------------- */
SELECT
    hour_of_day,
    COUNT(*)                                   AS total_transactions,
    SUM(is_fraud)                              AS fraud_transactions,
    ROUND(100.0 * SUM(is_fraud) / COUNT(*), 2) AS fraud_rate_pct
FROM fact_transactions
GROUP BY hour_of_day
ORDER BY hour_of_day;


/* ----------------------------------------------------------------------------
   Q7. HIGH-VALUE CUSTOMER IDENTIFICATION (Pareto / 80-20 check)
   Business use: identify the customer segment driving most revenue,
   for premium retention/relationship-manager focus
---------------------------------------------------------------------------- */
WITH cust_spend AS (
    SELECT customer_id, SUM(spend) AS total_spend
    FROM fact_monthly_spend
    GROUP BY customer_id
),
ranked AS (
    SELECT
        customer_id,
        total_spend,
        SUM(total_spend) OVER (ORDER BY total_spend DESC) AS running_total,
        SUM(total_spend) OVER ()                            AS grand_total,
        ROW_NUMBER() OVER (ORDER BY total_spend DESC)        AS rnk
    FROM cust_spend
)
SELECT
    rnk,
    customer_id,
    ROUND(total_spend, 0) AS total_spend,
    ROUND(100.0 * running_total / grand_total, 1) AS cumulative_pct_of_revenue
FROM ranked
WHERE rnk <= 150  -- top 10% of 1500 customers
ORDER BY rnk;


/* ----------------------------------------------------------------------------
   Q8. CITY-WISE PORTFOLIO PERFORMANCE
   Business use: geographic expansion / relationship-manager staffing decisions
---------------------------------------------------------------------------- */
SELECT
    c.city,
    COUNT(DISTINCT c.customer_id)              AS num_customers,
    ROUND(AVG(c.credit_limit), 0)              AS avg_credit_limit,
    ROUND(SUM(s.spend), 0)                     AS total_spend
FROM dim_customer c
JOIN fact_monthly_spend s ON c.customer_id = s.customer_id
GROUP BY c.city
ORDER BY total_spend DESC;
