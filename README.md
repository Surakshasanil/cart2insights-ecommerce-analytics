# Cart2Insights: Decoding E-Commerce Performance

An end-to-end data analytics project on the Olist Brazilian e-commerce dataset (about 100,000 orders, 2016 to 2018). It covers data cleaning, EDA, statistical tests, SQL analysis and an interactive Streamlit dashboard.

Author: Suraksha Sanil

## Objective
Find out what drives sales, customer behaviour, delivery performance and customer satisfaction, and turn it into business recommendations.

## Dataset
Olist Brazilian E-Commerce dataset (Kaggle: olistbr/brazilian-ecommerce). Nine tables: customers, orders, order items, payments, reviews, products, sellers, geolocation and category translation. The data is not included in this repository. Download it from Kaggle and put the CSVs in a folder named `Raw data`.

## Approach
1. Load the nine CSVs with pandas and parse dates.
2. Quality checks: missing values, duplicates, outliers, invalid values, summary statistics.
3. Cleaning: fix types, handle missing values and duplicates, add missing ZIP prefixes, one review score per order, save to `Cleaned data`.
4. Database: design a MySQL schema (primary keys, foreign keys) and load the cleaned tables.
5. Feature engineering: delivery time, delay, order value, customer and seller metrics.
6. EDA: sales trends, categories, states, customers, delivery and reviews.
7. Statistical tests: Welch t-test, ANOVA, chi-square.
8. SQL analysis: joins, GROUP BY / HAVING, subqueries, CTEs, window functions.
9. Dashboard: Streamlit + Plotly reading live from MySQL.
10. Insights: see `insights.md`.

## Key findings
- 96,477 delivered orders, R$ 15.42M revenue, average order value R$ 159.86.
- Sao Paulo gives 37% of revenue; SP, RJ and MG give 63%.
- Only 3.0% of customers order again.
- Average delivery takes 12.56 days; 8.1% of orders are late.
- Average review is 4.29 for on-time orders and 1.73 for orders 8+ days late. Late delivery is the biggest driver of bad reviews.

## Project structure
    Cart 2 insight.ipynb     main notebook (all steps)
    Streamlit/               dashboard: app.py, queries.py, database.py, utils.py
    requirements.txt
    insights.md
    .gitignore
Not in the repo: `Raw data/`, `Cleaned data/`, `Sql.env`.

## Setup
1. Install Python 3.10+ and MySQL 8.
2. `pip install -r requirements.txt`
3. Put the Kaggle CSVs in `Raw data/`.
4. Create `Sql.env` next to the notebook (never commit it):
       DB_USER=your_user
       DB_PASSWORD=your_password
       DB_HOST=localhost
       DB_PORT=3306
       DB_NAME=cart2insights
5. Run the notebook top to bottom.
6. Start the dashboard from the project folder: `python -m streamlit run Streamlit/app.py`

## Tools
Python, pandas, NumPy, SciPy, Matplotlib, Seaborn, Plotly, MySQL, SQLAlchemy, Streamlit.