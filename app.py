import streamlit as st
import gspread
import pandas as pd
import matplotlib.pyplot as plt
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz

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

# -------------------------------------------------
# Time Handling (IST)
# -------------------------------------------------
ist = pytz.timezone("Asia/Kolkata")
now = datetime.now(ist)

# -------------------------------------------------
# Tabs
# -------------------------------------------------
expense_tab, attendance_tab, expense_analytics_tab, attendance_analytics_tab = st.tabs(
    ["🧾 Expense", "🧑‍🍳 Attendance", "📊 Expense Analytics", "📈 Attendance Analytics"]
)

# =================================================
# 🧾 EXPENSE TAB
# =================================================
with expense_tab:

    st.markdown("## 🧾 Expense Entry")

    with st.form("expense_form"):
        exp_date = st.date_input("Expense Date", value=now.date())
        exp_time = st.time_input(
            "Expense Time",
            value=now.time().replace(second=0, microsecond=0)
        )

        exp_datetime = datetime.combine(exp_date, exp_time)
        exp_datetime_str = exp_datetime.strftime("%d/%m/%Y %H:%M")

        category = st.selectbox("Category", [
            "Groceries", "Vegetables", "Non-Veg", "Milk", "Banana Leaf",
            "Maintenance", "Electricity", "Rent",
            "Salary and Advance", "Transportation", "Others"
        ])

        sub_category = st.text_input("Sub-Category")
        amount = st.number_input("Expense Amount", min_value=0.0, step=1.0)
        payment = st.selectbox("Payment Mode", ["Cash", "UPI", "Cheque"])
        by = st.selectbox("Expense By", ["RK", "AR", "YS"])

        submit_expense = st.form_submit_button("✅ Submit Expense")

    if submit_expense:
        if amount == 0:
            st.error("Expense amount must be greater than 0")
        else:
            expense_sheet.append_row([
                exp_datetime_str,
                category,
                sub_category,
                amount,
                payment,
                by
            ])
            st.success("Expense recorded successfully ✅")

# =================================================
# 🧑‍🍳 ATTENDANCE TAB
# =================================================
with attendance_tab:

    st.markdown("## 🧑‍🍳 Employee Attendance")

    EMPLOYEES = [
        "Vinoth", "Ravi", "Mani", "Ansari", "Kumar", "Hari",
        "Samuthuram", "Ramesh", "Punitha", "Vembu", "Devi",
        "Babu", "Latha", "Indhra", "Ambiga", "RY", "YS",
        "Poosari", "Balaji"
    ]

    att_date = st.date_input("Attendance Date", value=now.date())
    att_date_str = att_date.strftime("%d/%m/%Y")
    entry_time = now.strftime("%d/%m/%Y %H:%M")

    st.markdown("### ❌ Morning Absentees")
    morning = {e: st.checkbox(e, key=f"m_{e}") for e in EMPLOYEES}

    st.markdown("### ❌ Afternoon Absentees")
    afternoon = {e: st.checkbox(e, key=f"a_{e}") for e in EMPLOYEES}

    st.markdown("### ❌ Night Absentees")
    night = {e: st.checkbox(e, key=f"n_{e}") for e in EMPLOYEES}

    if st.button("✅ Submit Attendance"):

        rows = attendance_sheet.get_all_values()
        delete_rows = [
            i for i, r in enumerate(rows[1:], start=2)
            if r[0] == att_date_str
        ]

        for i in reversed(delete_rows):
            attendance_sheet.delete_rows(i)

        for e in EMPLOYEES:
            attendance_sheet.append_row([
                att_date_str,
                e,
                "✖" if morning[e] else "✔",
                "✖" if afternoon[e] else "✔",
                "✖" if night[e] else "✔",
                entry_time
            ])

        st.success("Attendance saved successfully ✅")

# =================================================
# 📊 EXPENSE ANALYTICS
# =================================================
with expense_analytics_tab:

    st.markdown("## 📊 Expense Analytics")

    records = expense_sheet.get_all_records()
    if not records:
        st.info("No expense data yet.")
    else:
        df = pd.DataFrame(records)

        df["Date & Time"] = pd.to_datetime(
            df["Date & Time"], format="%d/%m/%Y %H:%M"
        )
        df["Date"] = df["Date & Time"].dt.date
        df["Week"] = df["Date & Time"].dt.to_period("W").astype(str)
        df["Month"] = df["Date & Time"].dt.to_period("M").astype(str)
        df["Expense Amount"] = pd.to_numeric(df["Expense Amount"])

        st.metric("💰 Total Spend", f"₹ {df['Expense Amount'].sum():,.0f}")

        view = st.radio("View", ["Daily", "Weekly", "Monthly"], horizontal=True)

        if view == "Daily":
            trend = df.groupby("Date")["Expense Amount"].sum()
        elif view == "Weekly":
            trend = df.groupby("Week")["Expense Amount"].sum()
        else:
            trend = df.groupby("Month")["Expense Amount"].sum()

        st.line_chart(trend)

        st.markdown("### 📊 Top 5 Expense Categories")
        top_cat = df.groupby("Category")["Expense Amount"].sum().nlargest(5)
        st.bar_chart(top_cat)

        avg_daily = df.groupby("Date")["Expense Amount"].sum().mean()
        st.metric("📉 Avg Daily Spend", f"₹ {avg_daily:,.0f}")

# =================================================
# 📈 ATTENDANCE ANALYTICS
# =================================================
with attendance_analytics_tab:

    st.markdown("## 📈 Attendance Analytics")

    records = attendance_sheet.get_all_records()
    if not records:
        st.info("No attendance data yet.")
    else:
        df = pd.DataFrame(records)

        df["absent_count"] = (
            (df["Morning"] == "✖").astype(int) +
            (df["Afternoon"] == "✖").astype(int) +
            (df["Night"] == "✖").astype(int)
        )

        st.markdown("### 📈 Day-wise Absentees")
        daily_absent = df.groupby("Date")["absent_count"].sum()
        st.line_chart(daily_absent)

        st.markdown("### 🚨 Top 5 Absent Employees")
        top_absent = df.groupby("Employee Name")["absent_count"].sum().nlargest(5)
        st.bar_chart(top_absent)

        st.markdown("### ❌ Absentees by Shift")
        shift_absent = {
            "Morning": (df["Morning"] == "✖").sum(),
            "Afternoon": (df["Afternoon"] == "✖").sum(),
            "Night": (df["Night"] == "✖").sum()
        }
        st.bar_chart(pd.Series(shift_absent))
