import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import KMeans
import os

# ============================================================
# ১. অ্যাপ কনফিগারেশন + কাস্টম স্টাইল
# ============================================================
st.set_page_config(
    page_title="Sales Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetric"] {
        background-color: #1c1f26;
        border: 1px solid #2b2f3a;
        border-radius: 12px;
        padding: 16px 12px;
    }
    div[data-testid="stMetricLabel"] { font-size: 0.85rem; opacity: 0.8; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; }
    .block-container { padding-top: 2rem; }
    h1, h2, h3 { font-weight: 700; }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1c1f26;
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Company Growth & Sales Intelligence Dashboard")
st.caption("Target vs Achievement • Zone Performance • ML-based Customer Segmentation")

PLOTLY_TEMPLATE = "plotly_dark"
COLOR_SEQ = px.colors.qualitative.Set2

# ============================================================
# ২. ডেটা লোড এবং রোবাস্ট ক্লিনিং ফাংশন
# ============================================================
@st.cache_data
def load_data():
    file_path = "data/Sales_Data.csv"

    if not os.path.exists(file_path):
        st.error(f"Error: '{file_path}' ফাইলটি খুঁজে পাওয়া যায়নি। GitHub-এ 'data' ফোল্ডারের ভেতর ফাইলটি আছে কি না নিশ্চিত করুন।")
        st.stop()

    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()

    def clean_currency(value):
        if pd.isna(value) or value == "":
            return 0.0
        value = str(value).replace(',', '').strip()
        if '(' in value and ')' in value:
            value = "-" + value.replace('(', '').replace(')', '')
        return pd.to_numeric(value, errors='coerce')

    target_col = 'Total Yearly Target 26'
    ach_col = 'Total Achievement jan to june'

    if target_col not in df.columns or ach_col not in df.columns:
        st.error(f"Error: ফাইলে '{target_col}' অথবা '{ach_col}' কলামটি খুঁজে পাওয়া যায়নি।")
        st.write("ফাইলে থাকা কলামগুলো হলো:", list(df.columns))
        st.stop()

    df[target_col] = df[target_col].apply(clean_currency).fillna(0)
    df[ach_col] = df[ach_col].apply(clean_currency).fillna(0)

    # অ্যাচিভমেন্ট % (division-by-zero সেফলি হ্যান্ডেল করা)
    df['Achievement_%'] = np.where(
        df[target_col] > 0,
        (df[ach_col] / df[target_col]) * 100,
        0
    ).round(1)

    df['Gap'] = df[target_col] - df[ach_col]

    return df

df = load_data()
target_col = 'Total Yearly Target 26'
ach_col = 'Total Achievement jan to june'

# ============================================================
# ৩. মেশিন লার্নিং: কাস্টমার সেগমেন্টেশন (Clustering)
# ============================================================
X = df[[target_col, ach_col]]
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df['Segment_ID'] = kmeans.fit_predict(X)

cluster_order = (
    df.groupby('Segment_ID')[ach_col]
    .mean()
    .sort_values()
    .index.tolist()
)
segment_names = ["Silver (Low)", "Gold (Mid)", "Platinum (High)"]
segment_map = {cid: name for cid, name in zip(cluster_order, segment_names)}
df['Segment_Name'] = df['Segment_ID'].map(segment_map)

SEGMENT_COLORS = {
    "Silver (Low)": "#9aa5b1",
    "Gold (Mid)": "#e5b567",
    "Platinum (High)": "#7ee8c7",
}

# ============================================================
# ৪. সাইডবার ফিল্টার
# ============================================================
st.sidebar.header("🔍 ফিল্টার অপশন")
zones = st.sidebar.multiselect("জোন নির্বাচন করুন", options=df["Zone"].unique(), default=df["Zone"].unique())
sales_persons = st.sidebar.multiselect("সেলস পারসন নির্বাচন করুন", options=df["Sales Person (Sales Team)"].unique())
segments = st.sidebar.multiselect("সেগমেন্ট নির্বাচন করুন", options=df["Segment_Name"].unique(), default=df["Segment_Name"].unique())

filtered_df = df[df["Zone"].isin(zones) & df["Segment_Name"].isin(segments)]
if sales_persons:
    filtered_df = filtered_df[filtered_df["Sales Person (Sales Team)"].isin(sales_persons)]

st.sidebar.markdown("---")
st.sidebar.download_button(
    "⬇️ ফিল্টারকৃত ডেটা ডাউনলোড (CSV)",
    data=filtered_df.to_csv(index=False).encode("utf-8"),
    file_name="filtered_sales_data.csv",
    mime="text/csv",
)

if filtered_df.empty:
    st.warning("নির্বাচিত ফিল্টারে কোনো ডেটা নেই। ফিল্টার পরিবর্তন করুন।")
    st.stop()

# ============================================================
# ৫. টপ-লেভেল KPI
# ============================================================
total_target = filtered_df[target_col].sum()
total_ach = filtered_df[ach_col].sum()
overall_pct = (total_ach / total_target * 100) if total_target > 0 else 0
zero_sales = filtered_df[filtered_df[ach_col] == 0]

top_zone = filtered_df.groupby("Zone")[ach_col].sum().idxmax() if not filtered_df.empty else "-"
top_person_series = filtered_df.groupby("Sales Person (Sales Team)")[ach_col].sum()
top_person = top_person_series.idxmax() if not top_person_series.empty else "-"

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("মোট টার্গেট", f"৳{total_target:,.0f}")
k2.metric("মোট অর্জন", f"৳{total_ach:,.0f}", f"{overall_pct:.1f}% অর্জিত")
k3.metric("মোট কাস্টমার", len(filtered_df))
k4.metric("সেরা জোন", top_zone)
k5.metric("সেরা সেলস পারসন", top_person)

st.markdown("---")

# ============================================================
# ৬. ট্যাব-ভিত্তিক লেআউট
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 ওভারভিউ", "🤖 সেগমেন্টেশন", "🧑‍💼 সেলস টিম পারফরম্যান্স", "📋 বিস্তারিত ডেটা"
])

# ---------- Tab 1: Overview ----------
with tab1:
    c1, c2 = st.columns([1, 1])

    with c1:
        st.subheader("🎯 Overall Achievement")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=overall_pct,
            number={'suffix': "%"},
            gauge={
                'axis': {'range': [0, 150]},
                'bar': {'color': "#7ee8c7"},
                'steps': [
                    {'range': [0, 50], 'color': "#3a2b2b"},
                    {'range': [50, 90], 'color': "#3a3520"},
                    {'range': [90, 150], 'color': "#20351f"},
                ],
                'threshold': {'line': {'color': "white", 'width': 3}, 'value': 100},
            },
        ))
        fig_gauge.update_layout(template=PLOTLY_TEMPLATE, height=320, margin=dict(t=20, b=10))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with c2:
        st.subheader("📊 জোন অনুযায়ী টার্গেট বনাম অর্জন")
        zone_data = filtered_df.groupby("Zone")[[target_col, ach_col]].sum().reset_index()
        zone_data = zone_data.melt(id_vars="Zone", value_vars=[target_col, ach_col],
                                    var_name="Type", value_name="Amount")
        fig_bar = px.bar(
            zone_data, x="Zone", y="Amount", color="Type", barmode="group",
            text_auto='.2s', template=PLOTLY_TEMPLATE, color_discrete_sequence=COLOR_SEQ
        )
        fig_bar.update_layout(height=320, legend_title=None, margin=dict(t=20, b=10))
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("📈 জোনভিত্তিক অ্যাচিভমেন্ট %")
    zone_pct = filtered_df.groupby("Zone").apply(
        lambda g: (g[ach_col].sum() / g[target_col].sum() * 100) if g[target_col].sum() > 0 else 0
    ).reset_index(name="Achievement_%")
    fig_pct = px.bar(
        zone_pct.sort_values("Achievement_%"), x="Achievement_%", y="Zone", orientation="h",
        text="Achievement_%", template=PLOTLY_TEMPLATE, color="Achievement_%",
        color_continuous_scale="Tealgrn"
    )
    fig_pct.update_traces(texttemplate='%{text:.1f}%')
    fig_pct.add_vline(x=100, line_dash="dash", line_color="white", opacity=0.5)
    fig_pct.update_layout(height=350, coloraxis_showscale=False, margin=dict(t=20, b=10))
    st.plotly_chart(fig_pct, use_container_width=True)

    if not zero_sales.empty:
        st.error(f"⚠️ সতর্কতা: নির্বাচিত ফিল্টারে {len(zero_sales)} জন টার্গেট কাস্টমারের কোনো সেল হয়নি!")
        with st.expander("জিরো সেল কাস্টমারদের তালিকা দেখুন"):
            st.dataframe(
                zero_sales[["Customer Name", "Sales Person (Sales Team)", target_col]],
                use_container_width=True
            )

# ---------- Tab 2: Segmentation ----------
with tab2:
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("🤖 কাস্টমার সেগমেন্টেশন (Machine Learning)")
        fig_cluster = px.scatter(
            filtered_df, x=target_col, y=ach_col,
            color="Segment_Name", hover_name="Customer Name", size=ach_col,
            labels={target_col: "Yearly Target (৳)", ach_col: "Achievement (৳)"},
            template=PLOTLY_TEMPLATE, color_discrete_map=SEGMENT_COLORS,
        )
        fig_cluster.update_layout(height=420, legend_title=None, margin=dict(t=20, b=10))
        st.plotly_chart(fig_cluster, use_container_width=True)

    with c2:
        st.subheader("🧩 সেগমেন্ট ব্রেকডাউন")
        seg_counts = filtered_df["Segment_Name"].value_counts().reset_index()
        seg_counts.columns = ["Segment", "Count"]
        fig_pie = px.pie(
            seg_counts, names="Segment", values="Count", hole=0.55,
            color="Segment", color_discrete_map=SEGMENT_COLORS, template=PLOTLY_TEMPLATE,
        )
        fig_pie.update_layout(height=420, showlegend=True, margin=dict(t=20, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("📌 সেগমেন্ট সামারি")
    seg_summary = filtered_df.groupby("Segment_Name").agg(
        Customers=("Customer Name", "count"),
        Total_Target=(target_col, "sum"),
        Total_Achievement=(ach_col, "sum"),
        Avg_Achievement_pct=("Achievement_%", "mean"),
    ).reindex(segment_names).dropna(how="all").reset_index()
    st.dataframe(
        seg_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Total_Target": st.column_config.NumberColumn("Total_Target", format="৳%,.0f"),
            "Total_Achievement": st.column_config.NumberColumn("Total_Achievement", format="৳%,.0f"),
            "Avg_Achievement_pct": st.column_config.NumberColumn("Avg_Achievement_pct", format="%.1f%%"),
        },
    )

# ---------- Tab 3: Sales Team Performance ----------
with tab3:
    st.subheader("🏆 সেলস পারসন লিডারবোর্ড")
    leaderboard = filtered_df.groupby("Sales Person (Sales Team)").agg(
        Customers=("Customer Name", "count"),
        Total_Target=(target_col, "sum"),
        Total_Achievement=(ach_col, "sum"),
    ).reset_index()
    leaderboard["Achievement_%"] = np.where(
        leaderboard["Total_Target"] > 0,
        (leaderboard["Total_Achievement"] / leaderboard["Total_Target"] * 100),
        0
    ).round(1)
    leaderboard = leaderboard.sort_values("Total_Achievement", ascending=False).reset_index(drop=True)
    leaderboard.index = leaderboard.index + 1

    st.dataframe(
        leaderboard,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Total_Target": st.column_config.NumberColumn("Total_Target", format="৳%,.0f"),
            "Total_Achievement": st.column_config.NumberColumn("Total_Achievement", format="৳%,.0f"),
            "Achievement_%": st.column_config.ProgressColumn(
                "Achievement_%", format="%.1f%%", min_value=0,
                max_value=max(150, float(leaderboard["Achievement_%"].max() or 0)),
            ),
        },
    )

    st.subheader("📉 টপ ১০ সেলস পারসন (অর্জন অনুযায়ী)")
    top10 = leaderboard.head(10)
    fig_top = px.bar(
        top10, x="Total_Achievement", y="Sales Person (Sales Team)", orientation="h",
        color="Achievement_%", color_continuous_scale="Tealgrn",
        template=PLOTLY_TEMPLATE, text_auto='.2s'
    )
    fig_top.update_layout(height=400, yaxis={'categoryorder': 'total ascending'}, margin=dict(t=20, b=10))
    st.plotly_chart(fig_top, use_container_width=True)

# ---------- Tab 4: Detailed Data ----------
with tab4:
    st.subheader("📋 ফিল্টারকৃত ডেটা তালিকা")
    display_cols = [
        "Customer Name", "Zone", "Sales Person (Sales Team)",
        target_col, ach_col, "Achievement_%", "Gap", "Segment_Name"
    ]
    st.dataframe(
        filtered_df[display_cols],
        use_container_width=True,
        hide_index=True,
        height=500,
        column_config={
            target_col: st.column_config.NumberColumn(target_col, format="৳%,.0f"),
            ach_col: st.column_config.NumberColumn(ach_col, format="৳%,.0f"),
            "Gap": st.column_config.NumberColumn("Gap", format="৳%,.0f"),
            "Achievement_%": st.column_config.NumberColumn("Achievement_%", format="%.1f%%"),
        },
    )
