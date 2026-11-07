"""Small helper functions for the dashboard (no database or Streamlit code here)."""
from decimal import Decimal

YEARS = ["All", 2016, 2017, 2018]


def period_bounds(year):
    """Return the (start, end) timestamps for the selected year, or the full period."""
    if year == "All":
        return "2016-01-01 00:00:00", "2018-12-31 23:59:59"
    return f"{year}-01-01 00:00:00", f"{year}-12-31 23:59:59"


def fmt_money(value):
    """Format an amount in Brazilian reais, for example R$ 15,422,462."""
    return f"R$ {value:,.0f}"


def fmt_int(value):
    return f"{int(value):,}"


def decimals_to_float(df):
    """MySQL returns money as Decimal, which charts cannot draw. Convert it to float."""
    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna()
            if len(sample) > 0 and isinstance(sample.iloc[0], Decimal):
                df[col] = df[col].astype(float)
    return df
