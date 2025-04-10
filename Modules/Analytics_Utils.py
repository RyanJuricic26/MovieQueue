import pandas as pd
import streamlit as st
import plotly.express as px
from Modules.theme_config import CUSTOM_THEME

def records_to_df(result):
    """Safely converts Neo4j result records to a pandas DataFrame"""
    return pd.DataFrame([dict(r) for r in result]) if result else pd.DataFrame()

def safe_bar_chart(df, index_col, value_col, title="", theme=CUSTOM_THEME):
    """Bar chart using a consistent custom theme"""
    if not df.empty and index_col in df.columns and value_col in df.columns:
        st.subheader(title)

        df_sorted = df.sort_values(value_col, ascending=False).reset_index(drop=True)
        df_sorted[index_col] = df_sorted[index_col].astype(str)  # ✅ Force categorical

        fig = px.bar(
            df_sorted,
            x=index_col,
            y=value_col,
            text=value_col,
            color=index_col,
            color_discrete_sequence=theme["color_sequence"],
            labels={index_col: index_col.capitalize(), value_col: value_col.capitalize()},
            template=theme["template"]
        )

        fig.update_traces(textposition="outside")
        fig.update_xaxes(
            tickmode="array",
            tickvals=df_sorted[index_col],
            ticktext=[str(val) for val in df_sorted[index_col]],
            title_font=dict(color=theme["axis_color"]),
            tickfont=dict(color=theme["axis_color"])
        )
        fig.update_yaxes(
            title_font=dict(color=theme["axis_color"]),
            tickfont=dict(color=theme["axis_color"])
        )
        fig.update_layout(
            font=dict(family=theme["font_family"], color=theme["font_color"]),
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=40),
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)
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


def safe_pie_chart(df, names_col, values_col, title=""):
    if not df.empty and names_col in df.columns and values_col in df.columns:
        st.subheader(title)
        fig = px.pie(df, names=names_col, values=values_col, title=title)
        fig.update_traces(textinfo='percent+label', pull=[0.05]*len(df))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No data available for {title.lower()}.")