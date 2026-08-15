import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import io

st.set_page_config(page_title="Sales Data Dashboard", layout="wide")

st.title("📊 Sales Data Foundation Dashboard")
st.write("আপনার সেলস ডাটা ক্লিন, রিশেপ এবং কোয়ালিটি অ্যানালাইসিস করার ওয়েব অ্যাপ।")

# পাথ সেটআপ
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "Sales_Data.xlsx"

META_COLS = ["ID", "Sales Person (Sales Team)", "Coordinators", "Customer Name", "Customer Group", "Zone"]
TAIL_COLS = ["Total Yearly Target 26", "Total Achievement jan to june ", "Achievment%"]

# ফাংশনসমূহ (আপনার মূল কোড থেকে নেওয়া)
def reshape_to_long(df: pd.DataFrame) -> pd.DataFrame:
    cols = list(df.columns)
    brand_block = [c for c in cols if c not in META_COLS and c not in TAIL_COLS]
    records = []
    for i in range(0, len(brand_block), 3):
        if i+2 < len(brand_block):
            brand_col, ach_col, achpct_col = brand_block[i], brand_block[i + 1], brand_block[i + 2]
            tmp = df[META_COLS + [brand_col, ach_col, achpct_col]].copy()
            tmp.columns = META_COLS + ["Target", "Achievement", "Achievement_pct"]
            tmp["Brand"] = brand_col.strip()
            records.append(tmp)
    long_df = pd.concat(records, ignore_index=True)
    return long_df[META_COLS + ["Brand", "Target", "Achievement", "Achievement_pct"]]

def add_flags(long_df: pd.DataFrame) -> pd.DataFrame:
    df = long_df.copy()
    df["has_target"] = df["Target"].notna() & (df["Target"] > 0)
    df["has_achievement"] = df["Achievement"].notna() & (df["Achievement"] > 0)
    df["activity_flag"] = np.where(df["has_target"] | df["has_achievement"], "has_activity", "no_activity")
    df["target_gap_flag"] = (~df["has_target"]) & df["has_achievement"]
    df["negative_value_flag"] = (df["Target"] < 0) | (df["Achievement"] < 0)
    return df

def build_customer_master(long_df: pd.DataFrame) -> pd.DataFrame:
    master = long_df.drop_duplicates(subset=["ID"])[META_COLS].reset_index(drop=True)
    totals = long_df.groupby("ID").agg(
        Total_Target=("Target", "sum"),
        Total_Achievement=("Achievement", "sum"),
        N_brands_active=("activity_flag", lambda x: (x == "has_activity").sum()),
    ).reset_index()
    master = master.merge(totals, on="ID", how="left")
    master["is_zero_achiever"] = (master["Total_Target"] > 0) & (master["Total_Achievement"].fillna(0) == 0)
    return master

# ডাটা লোড ও প্রসেস পার্ট
if INPUT_FILE.exists():
    try:
        df = pd.read_excel(INPUT_FILE)
        
        # প্রসেসিং
        long_df = reshape_to_long(df)
        long_df = add_flags(long_df)
        master = build_customer_master(long_df)
        
        clean_activity = long_df[long_df["activity_flag"] == "has_activity"].copy()
        target_gap_list = long_df[long_df["target_gap_flag"]].sort_values("Achievement", ascending=False)
        zero_achievers = master[master["is_zero_achiever"]].sort_values("Total_Target", ascending=False)
        
        # --- স্ট্রিমলাইট ইন্টারফেস লেআউট ---
        tabs = st.tabs(["📋 কোয়ালিটি রিপোর্ট", "⚠️ টার্গেট গ্যাপ লিস্ট", "🎯 জিরো অ্যাচিভার্স", "👥 কাস্টমার মাস্টার"])
        
        with tabs[0]:
            st.header("Data Quality Metrics")
            col1, col2, col3 = st.columns(3)
            col1.metric("মোট কাস্টমার-ব্র্যান্ড কম্বিনেশন", len(long_df))
            col2.metric("টার্গেট গ্যাপ রো (Sale আছে টার্গেট নেই)", long_df["target_gap_flag"].sum())
            col3.metric("মোট ইউনিক কাস্টমার", master["ID"].nunique())
            
            st.subheader("অ্যাক্টিভিটি ডাটা প্রিভিউ")
            st.dataframe(clean_activity.head(100), use_container_width=True)
            
        with tabs[1]:
            st.header("Target Gap List (বিক্রি হয়েছে কিন্তু টার্গেট ছিল না)")
            st.dataframe(target_gap_list[["Customer Name", "Sales Person (Sales Team)", "Zone", "Brand", "Achievement"]], use_container_width=True)
            
        with tabs[2]:
            st.header("Zero Achievers (টার্গেট আছে কিন্তু বিক্রি শূন্য)")
            st.dataframe(zero_achievers[["Customer Name", "Sales Person (Sales Team)", "Zone", "Total_Target"]], use_container_width=True)
            
        with tabs[3]:
            st.header("Customer Master Table")
            st.dataframe(master, use_container_width=True)

    except Exception as e:
        st.error(f"ডাটা প্রসেস করতে সমস্যা হয়েছে: {e}")
else:
    st.warning(f"আপনার প্রজেক্টের `data/` ফোল্ডারে `Sales_Data.xlsx` ফাইলটি খুঁজে পাওয়া যায়নি। অনুগ্রহ করে ফাইলটি সঠিক জায়গায় রাখুন।")
