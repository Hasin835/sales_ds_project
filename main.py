import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
import os

# ১. অ্যাপ কনফিগারেশন
st.set_page_config(page_title="Sales Intelligence Dashboard", layout="wide")
st.title("Company Growth & Sales Intelligence Dashboard")

# ২. ডেটা লোড এবং রোবাস্ট ক্লিনিং ফাংশন
@st.cache_data
def load_data():
    # ফাইল প্যাথ নিশ্চিত করা (data ফোল্ডারের ভেতর)
    file_path = "data/Sales_Data.csv"

    if not os.path.exists(file_path):
        st.error(f"Error: '{file_path}' ফাইলটি খুঁজে পাওয়া যায়নি। GitHub-এ 'data' ফোল্ডারের ভেতর ফাইলটি আছে কি না নিশ্চিত করুন।")
        st.stop()

    df = pd.read_csv(file_path)

    # কলামের নামের বাড়তি অদৃশ্য স্পেস মুছে ফেলা (KeyError সমাধান করবে)
    df.columns = df.columns.str.strip()

    # কারেন্সি ক্লিনিং ফাংশন (কমা এবং ব্র্যাকেট দূর করতে)
    def clean_currency(value):
        if pd.isna(value) or value == "":
            return 0.0
        value = str(value).replace(',', '').strip()
        if '(' in value and ')' in value:  # নেগেটিভ বা ব্র্যাকেট ভ্যালু হ্যান্ডেল করা
            value = "-" + value.replace('(', '').replace(')', '')
        return pd.to_numeric(value, errors='coerce')

    # মূল কলামগুলো ক্লিন করা
    target_col = 'Total Yearly Target 26'
    ach_col = 'Total Achievement jan to june'

    # কলামগুলো আছে কি না চেক করা
    if target_col not in df.columns or ach_col not in df.columns:
        st.error(f"Error: ফাইলে '{target_col}' অথবা '{ach_col}' কলামটি খুঁজে পাওয়া যায়নি।")
        st.write("ফাইলে থাকা কলামগুলো হলো:", list(df.columns))
        st.stop()

    df[target_col] = df[target_col].apply(clean_currency).fillna(0)
    df[ach_col] = df[ach_col].apply(clean_currency).fillna(0)

    return df

# ডেটা কল করা
df = load_data()

# ৩. মেশিন লার্নিং: কাস্টমার সেগমেন্টেশন (Clustering)
# টার্গেট এবং অর্জনের ওপর ভিত্তি করে ৩টি গ্রুপে ভাগ করা
X = df[['Total Yearly Target 26', 'Total Achievement jan to june']]
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df['Segment_ID'] = kmeans.fit_predict(X)

# গ্রুপের অর্থবহ নাম দেওয়া
# KMeans প্রতিবার cluster_id 0/1/2 কে একই গ্রুপে দেয় না, তাই সরাসরি
# {0: "Silver", 1: "Platinum", 2: "Gold"} ম্যাপ করলে ভুল নাম বসে যেতে পারে।
# তাই achievement-এর গড় মান অনুযায়ী cluster গুলো সাজিয়ে তারপর নাম বসানো হচ্ছে।
cluster_order = (
    df.groupby('Segment_ID')['Total Achievement jan to june']
    .mean()
    .sort_values()
    .index.tolist()
)
segment_names = ["Silver (Low)", "Gold (Mid)", "Platinum (High)"]
segment_map = {cluster_id: name for cluster_id, name in zip(cluster_order, segment_names)}
df['Segment_Name'] = df['Segment_ID'].map(segment_map)

# ৪. সাইডবার ফিল্টার
st.sidebar.header("🔍 ফিল্টার অপশন")
zones = st.sidebar.multiselect("জোন নির্বাচন করুন", options=df["Zone"].unique(), default=df["Zone"].unique())
sales_persons = st.sidebar.multiselect("সেলস পারসন নির্বাচন করুন", options=df["Sales Person (Sales Team)"].unique())

# ডেটা ফিল্টারিং
filtered_df = df[df["Zone"].isin(zones)]
if sales_persons:
    filtered_df = filtered_df[filtered_df["Sales Person (Sales Team)"].isin(sales_persons)]

# ৫. ড্যাশবোর্ড কি-মেট্রিক্স (Key Metrics)
col1, col2, col3 = st.columns(3)
total_target = filtered_df["Total Yearly Target 26"].sum()
total_ach = filtered_df["Total Achievement jan to june"].sum()
col1.metric("মোট টার্গেট", f"৳{total_target:,.0f}")
col2.metric("মোট অর্জন (জানু-জুন)", f"৳{total_ach:,.0f}")
col3.metric("মোট কাস্টমার সংখ্যা", len(filtered_df))

# ৬. মেশিন লার্নিং ভিজ্যুয়ালাইজেশন (Cluster Chart)
st.subheader("🤖 কাস্টমার সেগমেন্টেশন (Machine Learning)")
fig_cluster = px.scatter(
    filtered_df, x="Total Yearly Target 26", y="Total Achievement jan to june",
    color="Segment_Name", hover_name="Customer Name",
    labels={
        "Total Yearly Target 26": "Yearly Target (৳)",
        "Total Achievement jan to june": "Achievement (৳)"
    },
    title="কাস্টমার গ্রুপ: টার্গেট বনাম অর্জন"
)
st.plotly_chart(fig_cluster, use_container_width=True)

# ৭. জোনভিত্তিক পারফরম্যান্স চার্ট
st.subheader("📊 জোন অনুযায়ী বিক্রয় অর্জন")
zone_data = filtered_df.groupby("Zone")["Total Achievement jan to june"].sum().reset_index()
fig_bar = px.bar(zone_data, x="Zone", y="Total Achievement jan to june", color="Zone", text_auto='.2s')
st.plotly_chart(fig_bar, use_container_width=True)

# ৮. জিরো সেলস অ্যালার্ট
zero_sales = filtered_df[filtered_df["Total Achievement jan to june"] == 0]
if not zero_sales.empty:
    st.error(f"⚠️ সতর্কতা: নির্বাচিত জোনে {len(zero_sales)} জন টার্গেট কাস্টমারের কোনো সেল হয়নি!")
    with st.expander("জিরো সেল কাস্টমারদের তালিকা দেখুন"):
        st.table(zero_sales[["Customer Name", "Sales Person (Sales Team)", "Total Yearly Target 26"]])

# ৯. ডেটা টেবিল প্রিভিউ
st.subheader("📋 ফিল্টারকৃত ডেটা তালিকা")
st.dataframe(filtered_df[["Customer Name", "Zone", "Sales Person (Sales Team)", "Total Yearly Target 26", "Total Achievement jan to june", "Segment_Name"]])