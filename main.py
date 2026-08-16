import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
import os

# অ্যাপ কনফিগারেশন
st.set_page_config(page_title="Sales Data Science App", layout="wide")
st.title("🚀 Company Growth & Sales Intelligence Dashboard")

# ১. ডেটা লোড এবং ক্লিনিং ফাংশন
@st.cache_data
def load_data():
    # ফাইলটি যেহেতু data ফোল্ডারে আছে
    file_path = "data/Sales_Data.csv"
    
    if not os.path.exists(file_path):
        st.error(f"Error: '{file_path}' ফাইলটি খুঁজে পাওয়া যায়নি। আপনার GitHub-এ 'data' ফোল্ডারের ভেতর ফাইলটি আছে কি না চেক করুন।")
        st.stop()
        
    df = pd.read_csv(file_path)

    # কারেন্সি ক্লিনিং ফাংশন (কমা এবং ব্র্যাকেট দূর করতে)
    def clean_currency(value):
        if isinstance(value, str):
            value = value.replace(',', '').replace('(', '-').replace(')', '')
        return pd.to_numeric(value, errors='coerce')

    # মূল কলামগুলো ক্লিন করা [১]
    df['Total Yearly Target 26'] = df['Total Yearly Target 26'].apply(clean_currency).fillna(0)
    df['Total Achievement jan to june'] = df['Total Achievement jan to june'].apply(clean_currency).fillna(0)
    
    return df

df = load_data()

# ২. মেশিন লার্নিং: কাস্টমার সেগমেন্টেশন (Clustering)
# টার্গেট এবং অর্জনের ওপর ভিত্তি করে ৩টি গ্রুপে ভাগ করা [১]
X = df[['Total Yearly Target 26', 'Total Achievement jan to june']]
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df['Segment_ID'] = kmeans.fit_predict(X)

# গ্রুপের অর্থবহ নাম দেওয়া
segment_map = {0: "Silver (Low)", 1: "Platinum (High)", 2: "Gold (Mid)"}
df['Segment_Name'] = df['Segment_ID'].map(segment_map)

# ৩. সাইডবার ফিল্টার
st.sidebar.header("🔍 Filter Options")
zones = st.sidebar.multiselect("Select Zones", options=df["Zone"].unique(), default=df["Zone"].unique())
sales_persons = st.sidebar.multiselect("Select Sales Person", options=df["Sales Person (Sales Team)"].unique())

# ডেটা ফিল্টারিং
filtered_df = df[df["Zone"].isin(zones)]
if sales_persons:
    filtered_df = filtered_df[filtered_df["Sales Person (Sales Team)"].isin(sales_persons)]

# ৪. ড্যাশবোর্ড কি-মেট্রিক্স
col1, col2, col3 = st.columns(3)
total_target = filtered_df["Total Yearly Target 26"].sum()
total_ach = filtered_df["Total Achievement jan to june"].sum()
col1.metric("Total Target", f"৳{total_target:,.0f}")
col2.metric("Total Achievement", f"৳{total_ach:,.0f}")
col3.metric("Total Customers", len(filtered_df))

# ৫. ভিজ্যুয়ালাইজেশন (ML Cluster Chart)
st.subheader("🤖 Customer Segmentation (Machine Learning)")
fig_cluster = px.scatter(
    filtered_df, x="Total Yearly Target 26", y="Total Achievement jan to june",
    color="Segment_Name", hover_name="Customer Name",
    title="Customer Groups: Target vs Achievement"
)
st.plotly_chart(fig_cluster, use_container_width=True)

# ৬. জোনভিত্তিক পারফরম্যান্স
st.subheader("📊 Zone-wise Sales Performance")
zone_data = filtered_df.groupby("Zone")["Total Achievement jan to june"].sum().reset_index()
fig_bar = px.bar(zone_data, x="Zone", y="Total Achievement jan to june", color="Zone", text_auto='.2s')
st.plotly_chart(fig_bar, use_container_width=True)

# ৭. জিরো সেলস অ্যালার্ট [১]
zero_sales = filtered_df[filtered_df["Total Achievement jan to june"] == 0]
if not zero_sales.empty:
    st.warning(f"⚠️ নির্বাচিত জোনে {len(zero_sales)} জন কাস্টমারের কোনো সেল হয়নি!")
    if st.checkbox("কাস্টমারদের তালিকা দেখুন"):
        st.write(zero_sales[["Customer Name", "Sales Person (Sales Team)", "Total Yearly Target 26"]])