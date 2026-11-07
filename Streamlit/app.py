"""Run from the project folder:  python -m streamlit run Streamlit/app.py"""
import plotly.express as px
import streamlit as st

import queries as q
from database import run_query
from utils import YEARS, fmt_int, fmt_money, period_bounds

st.set_page_config(page_title="Cart2Insights", page_icon="🛒", layout="wide")

# ---------- Colours ----------
TEAL, ORANGE, RED, NAVY = "#0F766E", "#F59E0B", "#DC2626", "#1E3A5F"
PALETTE = [TEAL, ORANGE, NAVY, "#8B5CF6", "#EC4899", "#14B8A6"]

st.markdown(
    f"""
    <style>
    .banner {{background: linear-gradient(90deg, {NAVY}, {TEAL}); padding: 22px 28px;
              border-radius: 14px; color: white; margin-bottom: 14px;}}
    .banner h1 {{color: white; margin: 0; font-size: 2rem;}}
    .banner p  {{color: #D6EFEC; margin: 4px 0 0 0;}}
    [data-testid="stMetric"] {{background: white; border-left: 6px solid {ORANGE};
              padding: 14px 16px; border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,.12);}}
    [data-testid="stMetricValue"] {{color: {NAVY};}}
    </style>
    <div class="banner">
      <h1>🛒 Cart2Insights</h1>
      <p>Decoding E-Commerce Performance · Olist Brazil, delivered orders 2016-2018 · live from MySQL</p>
    </div>
    """,
    unsafe_allow_html=True,
)


def style(fig):
    """Same look for every chart."""
    fig.update_layout(template="plotly_white", colorway=PALETTE, title_font_size=18,
                      title_font_color=NAVY, margin=dict(t=60, l=10, r=10, b=10),
                      plot_bgcolor="rgba(0,0,0,0)")
    return fig


def show(fig, container=st):
    container.plotly_chart(style(fig))


section = st.sidebar.radio(
    "Section",
    ["Overview", "Sales & Products", "Customers", "Sellers", "Delivery", "Reviews"],
)
year = st.sidebar.selectbox("Year", YEARS)
top_n = st.sidebar.slider("Top N", 5, 20, 10)
start, end = period_bounds(year)
P = {"start": start, "end": end, "top_n": top_n, "min_orders": 30}


def get(sql, **extra):
    return run_query(sql, {**P, **extra})


try:
    if section == "Overview":
        o = get(q.OVERVIEW).iloc[0]
        c = st.columns(5)
        c[0].metric("Orders", fmt_int(o.total_orders))
        c[1].metric("Revenue", fmt_money(o.total_revenue))
        c[2].metric("Avg order value", f"R$ {o.avg_order_value:,.2f}")
        c[3].metric("Customers", fmt_int(o.total_customers))
        c[4].metric("Avg review", f"{o.avg_review_score:.2f} / 5")
        m = get(q.MONTHLY_SALES)
        show(px.area(m, x="month", y="revenue", markers=True, title="Monthly revenue",
                     color_discrete_sequence=[TEAL]))
        show(px.bar(m, x="month", y="orders", title="Monthly orders",
                    color="orders", color_continuous_scale="Tealgrn"))
        st.caption("Late 2016 has very few orders because the dataset starts in Sep 2016, so those months look near zero.")
        g = m[m["month"] >= "2017-02"].copy()
        g["direction"] = g["growth_pct"].apply(lambda v: "Growth" if v >= 0 else "Decline")
        show(px.bar(g, x="month", y="growth_pct", color="direction",
                    color_discrete_map={"Growth": TEAL, "Decline": RED},
                    title="Month-over-month revenue growth (%)"))

    elif section == "Sales & Products":
        cat = get(q.CATEGORY_PERFORMANCE)
        fig = px.bar(cat, x="revenue", y="category", orientation="h", color="avg_review",
                     color_continuous_scale="Tealgrn", title=f"Top {top_n} categories by revenue")
        show(fig.update_yaxes(categoryorder="total ascending"))
        show(px.bar(get(q.SALES_BY_STATE), x="state", y="revenue", color="revenue",
                    color_continuous_scale="Oranges", title="Revenue by state"))
        st.subheader("Top products")
        st.dataframe(get(q.TOP_PRODUCTS))

    elif section == "Customers":
        show(px.bar(get(q.CUSTOMERS_BY_STATE), x="state", y="customers", color="customers",
                    color_continuous_scale="Tealgrn", title="Customers by state"))
        c1, c2 = st.columns(2)
        show(px.bar(get(q.SPENDING_BANDS), x="band", y="customers", title="Spending bands",
                    color_discrete_sequence=[ORANGE]), c1)
        show(px.pie(get(q.REPEAT_VS_NEW), names="customer_type", values="customers", hole=0.5,
                    title="Repeat vs one-time customers", color_discrete_sequence=[NAVY, ORANGE]), c2)
        st.subheader("Top customers")
        st.dataframe(get(q.TOP_CUSTOMERS))

    elif section == "Sellers":
        s = get(q.SELLER_REVENUE)
        fig = px.bar(s, x="revenue", y="seller_id", orientation="h", color="seller_state",
                     title=f"Top {top_n} sellers by revenue", color_discrete_sequence=PALETTE)
        show(fig.update_yaxes(categoryorder="total ascending"))
        r = get(q.SELLER_RATINGS).sort_values("avg_review")
        st.subheader("Lowest-rated sellers (30+ orders)")
        st.dataframe(r.head(top_n))

    elif section == "Delivery":
        d = get(q.DELIVERY_SUMMARY).iloc[0]
        c = st.columns(3)
        c[0].metric("Avg delivery days", f"{d.avg_delivery_days:.1f}")
        c[1].metric("Delayed orders", fmt_int(d.delayed_orders))
        c[2].metric("On-time orders", fmt_int(d.on_time_orders))
        ds = get(q.DELIVERY_BY_STATE)
        show(px.bar(ds, x="state", y="avg_delivery_days", color="pct_delayed",
                    color_continuous_scale="OrRd", title="Average delivery days by state (darker = more late orders)"))

    else:
        rd = get(q.REVIEW_DISTRIBUTION)
        rd["score"] = rd["score"].astype(str)
        show(px.bar(rd, x="score", y="reviews", color="score", title="Review scores",
                    color_discrete_map={"1": RED, "2": "#F97316", "3": ORANGE, "4": "#2DD4BF", "5": TEAL}))
        dv = get(q.DELAY_VS_REVIEW).sort_values("band_order")
        show(px.bar(dv, x="delivery_band", y="avg_review", color="avg_review",
                    color_continuous_scale="RdYlGn", range_color=[1, 5],
                    title="Late deliveries lower the review score"))

except Exception as e:
    st.error("Could not read from MySQL. Check that MySQL is running and Sql.env has the right details.")
    st.exception(e)