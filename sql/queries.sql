
-- Q1. Top 5 funds by AUM
SELECT
    amfi_code,
    scheme_name,
    fund_house,
    aum_crore
FROM fact_performance
ORDER BY aum_crore DESC
LIMIT 5;


-- Q2. Average NAV per month
SELECT
    substr(date, 1, 7) AS year_month,
    ROUND(AVG(nav), 2) AS average_nav
FROM fact_nav
GROUP BY substr(date, 1, 7)
ORDER BY year_month;


-- Q3. Total investment transactions by state
SELECT
    state,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;


-- Q4. Funds with expense ratio below 1%
SELECT
    amfi_code,
    scheme_name,
    fund_house,
    expense_ratio_pct
FROM fact_performance
WHERE expense_ratio_pct < 1
ORDER BY expense_ratio_pct ASC;


-- Q5. Transaction count and amount by transaction type
SELECT
    transaction_type,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr
FROM fact_transactions
GROUP BY transaction_type
ORDER BY total_amount_inr DESC;


-- Q6. Top 10 funds by 5-year return
SELECT
    amfi_code,
    scheme_name,
    return_5yr_pct
FROM fact_performance
WHERE return_5yr_pct IS NOT NULL
ORDER BY return_5yr_pct DESC
LIMIT 10;


-- Q7. Average 3-year return by fund category
SELECT
    category,
    ROUND(AVG(return_3yr_pct), 2) AS average_3yr_return_pct,
    COUNT(*) AS fund_count
FROM fact_performance
GROUP BY category
ORDER BY average_3yr_return_pct DESC;


-- Q8. Monthly transaction totals
SELECT
    substr(transaction_date, 1, 7) AS year_month,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr
FROM fact_transactions
GROUP BY substr(transaction_date, 1, 7)
ORDER BY year_month;


-- Q9. Monthly AUM by fund house
SELECT
    date,
    fund_house,
    ROUND(SUM(aum_crore), 2) AS total_aum_crore
FROM fact_aum
GROUP BY date, fund_house
ORDER BY date, total_aum_crore DESC;


-- Q10. Transaction totals by investor age group
SELECT
    age_group,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr
FROM fact_transactions
GROUP BY age_group
ORDER BY total_amount_inr DESC;



-- Q11. Monthly SIP inflows and reported YoY growth
SELECT
    month,
    sip_inflow_crore,
    yoy_growth_pct
FROM fact_sip_inflows
ORDER BY month;
