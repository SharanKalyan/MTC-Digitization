import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import matplotlib.pyplot as plt

# -------------------------------------------------
# Page Configuration
# -------------------------------------------------
st.set_page_config(page_title="Monisha Tiffin Center", layout="centered")

# -------------------------------------------------
# PIN Protection
# -------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("### Welcome!")
    st.markdown("### 🔒 Enter PIN to Access")

    with st.form("pin_form"):
        pin = st.text_input("PIN", type="password", max_chars=6)
        submit = st.form_submit_button("➡️ Enter")

    if submit:
        if pin == st.secrets["security"]["app_pin"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect PIN ❌")

    st.stop()

# -------------------------------------------------
# Google Sheets Connection
# -------------------------------------------------
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

CREDS = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], SCOPE
)

client = gspread.authorize(CREDS)
spreadsheet = client.open("MTC-Digitization")

expense_sheet = spreadsheet.sheet1
attendance_sheet = spreadsheet.worksheet("Attendance")
sales_sheet = spreadsheet.worksheet("Sales")
balance_sheet = spreadsheet.worksheet("Daily_Balance")

# -------------------------------------------------
# Time Handling (IST)
# -------------------------------------------------
ist = pytz.timezone("Asia/Kolkata")
now = datetime.now(ist)

# -------------------------------------------------
# Navigation
# -------------------------------------------------
section = st.selectbox(
    "📢 Select Section",
    [
        "📊 Today's Summary",
        "🧾 Expense Entry",
        "💰 Sales Entry",
        "🧑‍🍳 Attendance",
        "📊 Expense Analytics",
        "📈 Attendance Analytics",
        "📊 Sales Analytics",
    ],
)

# =================================================
# 📊 EXPENSE ANALYTICS (ENHANCED)
# =================================================
if section == "📊 Expense Analytics":

    st.markdown("## 📊 Expense Analytics")

    records = expense_sheet.get_all_records()
    if not records:
        st.info("No expense data available yet.")
        st.stop()

    df = pd.DataFrame(records)

    # ---------- Data Cleaning ----------
    df["Expense Amount"] = pd.to_numeric(df["Expense Amount"], errors="coerce")

    df["datetime"] = pd.to_datetime(
        df["Date & Time"],
        format="%d/%m/%Y %H:%M",
        errors="coerce"
    )

    df = df.dropna(subset=["datetime", "Expense Amount"])

    df["date"] = df["datetime"].dt.date
    df["week"] = df["datetime"].dt.isocalendar().week
    df["month"] = df["datetime"].dt.to_period("M")
    df["year"] = df["datetime"].dt.year

    # ---------- Total Expense ----------
    st.metric("💸 Total Expense", f"₹ {df['Expense Amount'].sum():,.0f}")
    st.markdown("---")

    # =================================================
    # 1️⃣ Category-wise Expense
    # =================================================
    st.subheader("📂 Category-wise Expense")

    cat_df = (
        df.groupby("Category")["Expense Amount"]
        .sum()
        .sort_values(ascending=False)
    )

    st.bar_chart(cat_df)

    st.markdown("---")

    # =================================================
    # 2️⃣ Daily / Weekly / Monthly Trend
    # =================================================
    st.subheader("📈 Expense Trend")

    trend_type = st.radio(
        "View expense trend by:",
        ["Daily", "Weekly", "Monthly"],
        horizontal=True
    )

    if trend_type == "Daily":
        trend_df = df.groupby("date")["Expense Amount"].sum()

    elif trend_type == "Weekly":
        current_month = now.month
        current_year = now.year

        temp = df[
            (df["datetime"].dt.month == current_month) &
            (df["datetime"].dt.year == current_year)
        ]

        trend_df = temp.groupby("week")["Expense Amount"].sum()
        trend_df.index = trend_df.index.astype(str).map(lambda x: f"Week {x}")

    else:  # Monthly
        current_year = now.year
        temp = df[df["year"] == current_year]

        trend_df = (
            temp.groupby("month")["Expense Amount"]
            .sum()
            .sort_index()
        )
        trend_df.index = trend_df.index.astype(str)

    st.line_chart(trend_df)

    st.markdown("---")

    # =================================================
    # 3️⃣ Payment Mode-wise Expense (Pie)
    # =================================================
    st.subheader("💳 Expense by Payment Mode")

    pay_df = df.groupby("Payment Mode")["Expense Amount"].sum()

    fig1, ax1 = plt.subplots()
    ax1.pie(pay_df, labels=pay_df.index, autopct="%1.1f%%", startangle=90)
    ax1.axis("equal")

    st.pyplot(fig1)

    st.markdown("---")

    # =================================================
    # 4️⃣ Expense By Person
    # =================================================
    st.subheader("👤 Expense by Person")

    by_df = (
        df.groupby("Expense By")["Expense Amount"]
        .sum()
        .sort_values(ascending=False)
    )

    st.bar_chart(by_df)

# =================================================
# 📈 ATTENDANCE ANALYTICS
# =================================================
elif section == "📈 Attendance Analytics":

    st.markdown("## 📈 Attendance Analytics")

    records = attendance_sheet.get_all_records()
    if not records:
        st.info("No attendance data available yet.")
    else:
        df = pd.DataFrame(records)
        df["absent_count"] = (
            (df["Morning"] == "✖").astype(int) +
            (df["Afternoon"] == "✖").astype(int) +
            (df["Night"] == "✖").astype(int)
        )
        st.bar_chart(df.groupby("Employee Name")["absent_count"].sum())

# =================================================
# 📊 SALES ANALYTICS
# =================================================
elif section == "📊 Sales Analytics":

    st.markdown("## 📊 Sales Analytics")

    records = sales_sheet.get_all_records()
    if not records:
        st.info("No sales data available yet.")
    else:
        df = pd.DataFrame(records)
        df["Cash Total"] = pd.to_numeric(df["Cash Total"], errors="coerce")
        st.bar_chart(df.groupby("Store")["Cash Total"].sum())
