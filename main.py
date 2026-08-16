import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans

st.set_page_config(page_title="Sales DS Project", layout="wide")
st.title("📊 Sales Analytics & Customer Segmentation")

# ১. ডেটা লোড এবং ক্লিনিং
@st.cache_data
def load_data():
    df = pd.read_csv("Sales_Data.csv")
    
    # সংখ্যাগুলো থেকে কমা এবং ব্র্যাকেট সরিয়ে ফ্লোটে রূপান্তর
    def clean_currency(value):
        if isinstance(value, str):
            value = value.replace(',', '').replace('(', '-').replace(')', '')
        return pd.to_numeric(value, errors='coerce')

    df['Total Yearly Target 26'] = df['Total Yearly Target 26'].apply(clean_currency).fillna(0)
    df['Total Achievement jan to june'] = df['Total Achievement jan to june'].apply(clean_currency).fillna(0)
    return df

df = load_data()

# ২. মেশিন লার্নিং: কাস্টমার সেগমেন্টেশন (Clustering)
# টার্গেট এবং অর্জনের ওপর ভিত্তি করে ৩টি গ্রুপে ভাগ করা
X = df[['Total Yearly Target 26', 'Total Achievement jan to june']]
kmeans = KMeans(n_clusters=3, random_state=42)
df['Customer_Segment'] = kmeans.fit_predict(X)

# গ্রুপের নাম দেওয়া
segment_map = {0: "Silver (Low)", 1: "Platinum (High)", 2: "Gold (Mid)"}
df['Segment_Name'] = df['Customer_Segment'].map(segment_map)

# ৩. ওয়েব অ্যাপ লেআউট (Sidebar)
st.sidebar.header("Filter by Zone")
zones = st.sidebar.multiselect("Select Zones", options=df["Zone"].unique(), default=df["Zone"].unique())
filtered_df = df[df["Zone"].isin(zones)]

# ৪. ভিজ্যুয়ালাইজেশন (Plotly)
st.subheader("🚀 Customer Segmentation Analysis")
fig_scatter = px.scatter(
    filtered_df, x="Total Yearly Target 26", y="Total Achievement jan to june",
    color="Segment_Name", hover_name="Customer Name",
    title="Customer Segments: Target vs Achievement"
)
st.plotly_chart(fig_scatter, use_container_width=True)

# জোনভিত্তিক টোটাল সেলস
st.subheader("🌍 Zone-wise Achievement")
zone_summary = filtered_df.groupby("Zone")["Total Achievement jan to june"].sum().reset_index()
fig_bar = px.bar(zone_summary, x="Zone", y="Total Achievement jan to june", color="Zone")
st.plotly_chart(fig_bar, use_container_width=True)

# ৫. জিরো সেলস কাস্টমার এলার্ট
zero_sales = filtered_df[filtered_df["Total Achievement jan to june"] == 0]
st.error(f"⚠️ {len(zero_sales)} জন কাস্টমারের কাছে এখনো কোনো সেল হয়নি!")
if st.checkbox("কাস্টমারদের তালিকা দেখুন"):
    st.write(zero_sales[["Customer Name", "Sales Person (Sales Team)", "Total Yearly Target 26"]])
