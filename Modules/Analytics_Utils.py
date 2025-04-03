import pandas as pd
import streamlit as st

def records_to_df(result):
    """Safely converts Neo4j result records to a pandas DataFrame"""
    return pd.DataFrame([dict(r) for r in result]) if result else pd.DataFrame()

def safe_bar_chart(df, index_col, value_col, title=""):
    """Safely plots a bar chart or shows fallback message"""
    if not df.empty and index_col in df.columns and value_col in df.columns:
        st.subheader(title)
        st.bar_chart(df.set_index(index_col)[value_col])
    else:
        st.info(f"No data available for {title.lower()}.")

def safe_metric(label, value, decimals=2):
    """Prints a metric, handling None safely"""
    if value is None:
        st.metric(label, "N/A")
    elif isinstance(value, (int, float)):
        st.metric(label, round(value, decimals))
    else:
        st.metric(label, value)