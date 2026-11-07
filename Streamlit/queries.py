"""SQL queries used by the dashboard.

Every query that depends on the date filter uses the parameters :start and :end.
Revenue = sum of customer payments (payment_value) of delivered orders,
except in the category and seller queries, where revenue = sum of item prices.
"""

# Common filter: delivered orders inside the selected period
DELIVERED_IN_PERIOD = """
    o.order_status = 'delivered'
    AND o.order_purchase_timestamp BETWEEN :start AND :end
"""

# ---------------------------------------------------------------- 1. Business overview
OVERVIEW = f"""
WITH order_totals AS (
    SELECT o.order_id, o.customer_id, SUM(p.payment_value) AS order_value
    FROM orders o
    JOIN order_payments p ON o.order_id = p.order_id
    WHERE {DELIVERED_IN_PERIOD}
    GROUP BY o.order_id, o.customer_id
)
SELECT
    COUNT(*)                          AS total_orders,
    ROUND(SUM(order_value), 2)        AS total_revenue,
    ROUND(AVG(order_value), 2)        AS avg_order_value,
    (SELECT COUNT(DISTINCT c.customer_unique_id)
       FROM customers c JOIN order_totals t ON c.customer_id = t.customer_id) AS total_customers,
    (SELECT COUNT(DISTINCT i.seller_id)
       FROM order_items i JOIN order_totals t ON i.order_id = t.order_id)     AS total_sellers,
    (SELECT ROUND(AVG(r.review_score), 2)
       FROM order_reviews r JOIN order_totals t ON r.order_id = t.order_id)   AS avg_review_score
FROM order_totals
"""

# ---------------------------------------------------------------- 2. Sales analysis
MONTHLY_SALES = f"""
WITH monthly AS (
    SELECT DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m') AS month,
           COUNT(DISTINCT o.order_id) AS orders,
           SUM(p.payment_value)       AS revenue
    FROM orders o
    JOIN order_payments p ON o.order_id = p.order_id
    WHERE {DELIVERED_IN_PERIOD}
    GROUP BY DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m')
)
SELECT month,
       orders,
       ROUND(revenue, 2) AS revenue,
       ROUND((revenue - LAG(revenue) OVER (ORDER BY month))
             / LAG(revenue) OVER (ORDER BY month) * 100, 1) AS growth_pct
FROM monthly
ORDER BY month
"""

CATEGORY_PERFORMANCE = f"""
SELECT t.product_category_name_english AS category,
       COUNT(DISTINCT i.order_id)      AS orders,
       ROUND(SUM(i.price), 2)          AS revenue,
       ROUND(AVG(r.score), 2)          AS avg_review
FROM order_items i
JOIN orders o   ON i.order_id = o.order_id
JOIN products p ON i.product_id = p.product_id
JOIN product_category_translation t ON p.product_category_name = t.product_category_name
LEFT JOIN (SELECT order_id, AVG(review_score) AS score
           FROM order_reviews GROUP BY order_id) r ON r.order_id = o.order_id
WHERE {DELIVERED_IN_PERIOD}
GROUP BY t.product_category_name_english
ORDER BY revenue DESC
LIMIT :top_n
"""

TOP_PRODUCTS = f"""
SELECT i.product_id,
       t.product_category_name_english AS category,
       COUNT(*)                        AS units_sold,
       ROUND(SUM(i.price), 2)          AS revenue
FROM order_items i
JOIN orders o   ON i.order_id = o.order_id
JOIN products p ON i.product_id = p.product_id
JOIN product_category_translation t ON p.product_category_name = t.product_category_name
WHERE {DELIVERED_IN_PERIOD}
GROUP BY i.product_id, t.product_category_name_english
ORDER BY units_sold DESC
LIMIT :top_n
"""

SALES_BY_STATE = f"""
SELECT c.customer_state AS state,
       COUNT(DISTINCT o.order_id)     AS orders,
       ROUND(SUM(p.payment_value), 2) AS revenue
FROM orders o
JOIN customers c      ON o.customer_id = c.customer_id
JOIN order_payments p ON o.order_id = p.order_id
WHERE {DELIVERED_IN_PERIOD}
GROUP BY c.customer_state
ORDER BY revenue DESC
"""

# ---------------------------------------------------------------- 3. Customer analysis
CUSTOMER_CTE = f"""
WITH cust AS (
    SELECT c.customer_unique_id,
           MIN(c.customer_state)       AS state,
           COUNT(DISTINCT o.order_id)  AS orders,
           SUM(p.payment_value)        AS spending
    FROM orders o
    JOIN customers c      ON o.customer_id = c.customer_id
    JOIN order_payments p ON o.order_id = p.order_id
    WHERE {DELIVERED_IN_PERIOD}
    GROUP BY c.customer_unique_id
)
"""

CUSTOMERS_BY_STATE = CUSTOMER_CTE + """
SELECT state, COUNT(*) AS customers
FROM cust
GROUP BY state
ORDER BY customers DESC
"""

SPENDING_BANDS = CUSTOMER_CTE + """
SELECT band_order, band, COUNT(*) AS customers
FROM (
    SELECT CASE WHEN spending < 50  THEN 1
                WHEN spending < 100 THEN 2
                WHEN spending < 200 THEN 3
                WHEN spending < 500 THEN 4
                ELSE 5 END AS band_order,
           CASE WHEN spending < 50  THEN 'Under 50'
                WHEN spending < 100 THEN '50 to 100'
                WHEN spending < 200 THEN '100 to 200'
                WHEN spending < 500 THEN '200 to 500'
                ELSE '500 and above' END AS band
    FROM cust
) b
GROUP BY band_order, band
ORDER BY band_order
"""

REPEAT_VS_NEW = CUSTOMER_CTE + """
SELECT CASE WHEN orders > 1 THEN 'Repeat customers'
            ELSE 'New customers (1 order)' END AS customer_type,
       COUNT(*)                AS customers,
       ROUND(SUM(spending), 2) AS revenue
FROM cust
GROUP BY customer_type
"""

TOP_CUSTOMERS = CUSTOMER_CTE + """
SELECT RANK() OVER (ORDER BY spending DESC) AS spending_rank,
       customer_unique_id,
       state,
       orders,
       ROUND(spending, 2) AS spending
FROM cust
ORDER BY spending_rank
LIMIT :top_n
"""

# ---------------------------------------------------------------- 4. Seller and product analysis
SELLER_REVENUE = f"""
WITH seller_stats AS (
    SELECT i.seller_id,
           s.seller_state,
           ROUND(SUM(i.price), 2)      AS revenue,
           COUNT(DISTINCT i.order_id)  AS orders
    FROM order_items i
    JOIN orders o  ON i.order_id = o.order_id
    JOIN sellers s ON i.seller_id = s.seller_id
    WHERE {DELIVERED_IN_PERIOD}
    GROUP BY i.seller_id, s.seller_state
)
SELECT RANK() OVER (ORDER BY revenue DESC) AS revenue_rank,
       seller_id, seller_state, revenue, orders
FROM seller_stats
ORDER BY revenue_rank
LIMIT :top_n
"""

SELLER_RATINGS = f"""
SELECT i.seller_id,
       COUNT(DISTINCT i.order_id) AS orders,
       ROUND(AVG(r.score), 2)     AS avg_review
FROM order_items i
JOIN orders o ON i.order_id = o.order_id
JOIN (SELECT order_id, AVG(review_score) AS score
      FROM order_reviews GROUP BY order_id) r ON r.order_id = i.order_id
WHERE {DELIVERED_IN_PERIOD}
GROUP BY i.seller_id
HAVING COUNT(DISTINCT i.order_id) >= :min_orders
"""

# ---------------------------------------------------------------- 5. Delivery analysis
DELIVERY_SUMMARY = """
SELECT COUNT(*) AS delivered_orders,
       ROUND(AVG(TIMESTAMPDIFF(SECOND, o.order_purchase_timestamp,
                               o.order_delivered_customer_date)) / 86400, 2) AS avg_delivery_days,
       SUM(CASE WHEN o.order_delivered_customer_date >  o.order_estimated_delivery_date THEN 1 ELSE 0 END) AS delayed_orders,
       SUM(CASE WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date THEN 1 ELSE 0 END) AS on_time_orders
FROM orders o
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_purchase_timestamp BETWEEN :start AND :end
"""

DELIVERY_BY_STATE = """
SELECT c.customer_state AS state,
       COUNT(*) AS orders,
       ROUND(AVG(TIMESTAMPDIFF(SECOND, o.order_purchase_timestamp,
                               o.order_delivered_customer_date)) / 86400, 2) AS avg_delivery_days,
       ROUND(100 * AVG(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
                            THEN 1 ELSE 0 END), 2) AS pct_delayed
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
  AND o.order_purchase_timestamp BETWEEN :start AND :end
GROUP BY c.customer_state
ORDER BY avg_delivery_days DESC
"""

# ---------------------------------------------------------------- 6. Customer experience
REVIEW_DISTRIBUTION = """
SELECT r.review_score AS score, COUNT(*) AS reviews
FROM order_reviews r
JOIN orders o ON r.order_id = o.order_id
WHERE o.order_purchase_timestamp BETWEEN :start AND :end
GROUP BY r.review_score
ORDER BY r.review_score
"""

DELAY_VS_REVIEW = """
SELECT band_order, delivery_band, COUNT(*) AS orders, ROUND(AVG(score), 2) AS avg_review
FROM (
    SELECT CASE WHEN d.delay_days <= 0 THEN 1
                WHEN d.delay_days <= 3 THEN 2
                WHEN d.delay_days <= 7 THEN 3
                ELSE 4 END AS band_order,
           CASE WHEN d.delay_days <= 0 THEN 'On time'
                WHEN d.delay_days <= 3 THEN '1 to 3 days late'
                WHEN d.delay_days <= 7 THEN '4 to 7 days late'
                ELSE '8+ days late' END AS delivery_band,
           r.score AS score
    FROM (SELECT o.order_id,
                 TIMESTAMPDIFF(SECOND, o.order_estimated_delivery_date,
                               o.order_delivered_customer_date) / 86400 AS delay_days
          FROM orders o
          WHERE o.order_status = 'delivered'
            AND o.order_delivered_customer_date IS NOT NULL
            AND o.order_purchase_timestamp BETWEEN :start AND :end) d
    JOIN (SELECT order_id, AVG(review_score) AS score
          FROM order_reviews GROUP BY order_id) r ON r.order_id = d.order_id
) x
GROUP BY band_order, delivery_band
ORDER BY band_order
"""
