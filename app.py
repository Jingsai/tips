"""Streamlit dashboard for tips data: table, statistics, and charts."""

import pandas as pd
import plotly.express as px
import streamlit as st

hide_github_icon = """
    <style>
    .stAppToolbar {visibility: hidden;}
    </style>
    """
st.markdown(hide_github_icon, unsafe_allow_html=True)

DATA_PATH = "./tips.csv"

@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["tip_pct"] = (df["tip"] / df["total_bill"]) * 100
    return df


st.set_page_config(page_title="Tips Explorer", layout="wide")
st.title("Restaurant Tips Explorer")

try:
    df_full = load_data()
except FileNotFoundError:
    st.error(f"Could not find `{DATA_PATH.name}` next to `app.py`.")
    st.stop()

with st.sidebar:
    st.header("Filters")
    day_pick = st.multiselect(
        "Day",
        options=sorted(df_full["day"].unique()),
        default=sorted(df_full["day"].unique()),
    )
    time_pick = st.multiselect(
        "Time",
        options=sorted(df_full["time"].unique()),
        default=sorted(df_full["time"].unique()),
    )
    sex_pick = st.multiselect(
        "Sex",
        options=sorted(df_full["sex"].unique()),
        default=sorted(df_full["sex"].unique()),
    )
    smoker_pick = st.multiselect(
        "Smoker",
        options=sorted(df_full["smoker"].unique()),
        default=sorted(df_full["smoker"].unique()),
    )

mask = (
    df_full["day"].isin(day_pick)
    & df_full["time"].isin(time_pick)
    & df_full["sex"].isin(sex_pick)
    & df_full["smoker"].isin(smoker_pick)
)
df = df_full.loc[mask].copy()

if df.empty:
    st.warning("No rows match the current filters.")
    st.stop()

tab_table, tab_stats, tab_viz = st.tabs(["Table", "Statistics", "Visualizations"])

with tab_table:
    st.dataframe(
        df.drop(columns=["tip_pct"], errors="ignore"),
        use_container_width=True,
        hide_index=True,
        height=420,
    )
    csv_bytes = df.drop(columns=["tip_pct"], errors="ignore").to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered CSV",
        data=csv_bytes,
        file_name="tips_filtered.csv",
        mime="text/csv",
    )

with tab_stats:
    st.subheader("Numeric summary")
    num_cols = ["total_bill", "tip", "size", "tip_pct"]
    st.dataframe(
        df[num_cols].describe().T,
        use_container_width=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**By day** (mean total bill & tip)")
        by_day = (
            df.groupby("day", observed=True)[["total_bill", "tip"]]
            .mean()
            .reindex(["Thur", "Fri", "Sat", "Sun"], fill_value=pd.NA)
        )
        st.dataframe(by_day, use_container_width=True)
    with c2:
        st.markdown("**By time & sex** (count)")
        st.dataframe(
            pd.crosstab(df["time"], df["sex"]),
            use_container_width=True,
        )

    st.subheader("Correlations (numeric)")
    corr = df[num_cols].corr(numeric_only=True)
    st.dataframe(corr, use_container_width=True)

with tab_viz:
    fig_scatter = px.scatter(
        df,
        x="total_bill",
        y="tip",
        color="sex",
        color_discrete_map={"Male": "blue", "Female": "red"},
        category_orders={"sex": ["Male", "Female"]},
        # symbol="smoker",
        size="size",
        hover_data=["day", "time"],
        title="Tip vs total bill",
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    row1, row2 = st.columns(2)
    with row1:
        fig_box = px.box(
            df,
            x="day",
            y="tip",
            color="time",
            category_orders={"day": ["Thur", "Fri", "Sat", "Sun"]},
            title="Tip distribution by day",
        )
        st.plotly_chart(fig_box, use_container_width=True)
    with row2:
        fig_hist = px.histogram(
            df,
            x="tip_pct",
            nbins=30,
            color="sex",
            barmode="overlay",
            opacity=0.65,
            title="Tip as % of bill",
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    fig_bar = px.bar(
        df.groupby(["day", "time"], observed=True)["tip"]
        .mean()
        .reset_index(),
        x="day",
        y="tip",
        color="time",
        barmode="group",
        category_orders={"day": ["Thur", "Fri", "Sat", "Sun"]},
        title="Average tip by day and time",
    )
    st.plotly_chart(fig_bar, use_container_width=True)
