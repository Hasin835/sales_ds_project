import streamlit as st
import pandas as pd
import plotly.express as px

# অ্যাপের শিরোনাম
st.set_page_config(page_title="Sales Analysis Dashboard", layout="wide")
st.title("🚀 Company Growth & Sales Analytics")

# ডেটা লোড করার ফাংশন
@st.cache_data
def load_data():
    # CSV ফাইলটি আপনার প্রজেক্ট ফোল্ডারে থাকতে হবে
    df = pd.read_csv("Sales_Data.csv")
    
    # ডেটা ক্লিনিং: সংখ্যাগুলোকে ফ্লোটে রূপান্তর করা (কমা এবং চিহ্ন সরিয়ে)
    cols_to_clean = ['Total Yearly Target 26', 'Total Achievement jan to june']
    for col in cols_to_clean:
        df[col] = df[col].astype(str).str.replace(',', '').str.replace('(', '').str.replace(')', '').replace('nan', '0')
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

df = load_data()

# --- সাইডবার ফিল্টার ---
st.sidebar.header("Filter Data")
selected_zone = st.sidebar.multiselect("Select Zone", options=df["Zone"].unique(), default=df["Zone"].unique())

filtered_df = df[df["Zone"].isin(selected_zone)]

# --- কি-মেট্রিক্স (Key Metrics) ---
total_target = filtered_df["Total Yearly Target 26"].sum()
total_ach = filtered_df["Total Achievement jan to june"].sum()
avg_ach_perf = (total_ach / total_target) * 100 if total_target > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total Yearly Target", f"৳{total_target:,.0f}")
col2.metric("Total Achievement (Jan-Jun)", f"৳{total_ach:,.0f}")
col3.metric("Overall Performance (%)", f"{avg_ach_perf:.2f}%")

# --- জোনভিত্তিক পারফরম্যান্স গ্রাফ ---
st.subheader("📊 Zone-wise Sales Achievement")
zone_data = filtered_df.groupby("Zone")["Total Achievement jan to june"].sum().reset_index()
fig = px.bar(zone_data, x="Zone", y="Total Achievement jan to june", color="Zone", title="Sales by Zone")
st.plotly_chart(fig, use_container_width=True)

# --- কাস্টমার এনালাইসিস টেবিল ---
st.subheader("🔍 Customer Performance Detail")
st.dataframe(filtered_df[["Customer Name", "Zone", "Total Yearly Target 26", "Total Achievement jan to june", "Achievment%"]])

# --- 'জিরো সেল' কাস্টমার এলার্ট ---
zero_sales_customers = filtered_df[filtered_df["Total Achievement jan to june"] == 0]
st.warning(f"⚠️ There are {len(zero_sales_customers)} customers with ZERO sales in selected zones!")
if st.button("Show Zero Sales List"):
    st.write(zero_sales_customers[["Customer Name", "Sales Person (Sales Team)", "Total Yearly Target 26"]])
