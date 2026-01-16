import streamlit as st
import gspread
import pandas as pd
import matplotlib.pyplot as plt
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Monisha Tiffin Center",
    layout="centered"
)

# -----------------------------
# PIN Protection
# -----------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("### 🔒 Enter PIN to Access")

    with st.form("pin_form"):
        pin_input = st.text_input("PIN", type="password", max_chars=6)
        pin_submit = st.form_submit_button("➡️ Enter")

    if pin_submit:
        if pin_input == st.secrets["security"]["app_pin"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect PIN ❌")

    st.stop()

# -----------------------------
# Google Sheets Connection
# -----------------------------
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

# -----------------------------
# Time Handling (IST reference)
# -----------------------------
ist = pytz.timezone("Asia/Kolkata")
now = datetime.now(ist)

# -----------------------------
# Tabs
# -----------------------------
expense_tab, attendance_tab, expense_analytics_tab, attendance_analytics_tab = st.tabs(
    ["🧾 Expense", "🧑‍🍳 Attendance", "📊 Expense Analytics", "📈 Attendance Analytics"]
)

# =========================================================
# 🧾 EXPENSE TAB
# =========================================================
with expense_tab:

    st.markdown("## 🧾 Expense Entry")

    with st.form("expense_form"):

        expense_date = st.date_input(
            "Expense Date",
            value=now.date()
        )

        expense_time = st.time_input(
            "Expense Time",
            value=now.time().replace(second=0, microsecond=0)
        )

        # IMPORTANT: no timezone conversion
        expense_datetime = datetime.combine(expense_date, expense_time)
        expense_datetime_str = expense_datetime.strftime("%d/%m/%Y %H:%M")

        category = st.selectbox(
            "Category",
            [
                "Groceries", "Vegetables", "Non-Veg", "Milk",
                "Banana Leaf", "Maintenance", "Electricity",
                "Rent", "Salary and Advance", "Transportation", "Others"
            ]
        )

        sub_category = st.text_input("Sub-Category")
        amount = st.number_input("Expense Amount", min_value=0.0, step=1.0)
        payment_mode = st.selectbox("Payment Mode", ["Cash", "UPI", "Cheque"])
        expense_by = st.selectbox("Expense By", ["RK", "AR", "YS"])

        submit_expense = st.form_submit_button("✅ Submit Expense")

    if submit_expense:
        if amount == 0:
            st.error("Expense amount must be greater than 0")
        else:
            expense_sheet.append_row([
                expense_datetime_str,
                category,
                sub_category,
                amount,
                payment_mode,
                expense_by
            ])
            st.success("Expense recorded successfully ✅")

# =========================================================
# 🧑‍🍳 ATTENDANCE TAB
# =========================================================
with attendance_tab:

    st.markdown("## 🧑‍🍳 Employee Attendance")

    EMPLOYEES = [
        "Vinoth", "Ravi", "Mani", "Ansari", "Kumar", "Hari",
        "Samuthuram", "Ramesh", "Punitha", "Vembu", "Devi",
        "Babu", "Latha", "Indhra", "Ambiga", "RY", "YS",
        "Poosari", "Balaji"
    ]

    attendance_date = st.date_input("Attendance Date", value=now.date())
    attendance_date_str = attendance_date.strftime("%d/%m/%Y")
    entry_time = now.strftime("%d/%m/%Y %H:%M")

    st.markdown("### ❌ Morning Absentees")
    m = {e: st.checkbox(e, key=f"m_{e}") for e in EMPLOYEES}

    st.markdown("### ❌ Afternoon Absentees")
    a = {e: st.checkbox(e, key=f"a_{e}") for e in EMPLOYEES}

    st.markdown("### ❌ Night Absentees")
    n = {e: st.checkbox(e, key=f"n_{e}") for e in EMPLOYEES}

    if st.button("✅ Submit Attendance"):

        # delete existing rows for that date
        rows = attendance_sheet.get_all_values()
        delete_rows = [i for i, r in enumerate(rows[1:], start=2) if r[0] == attendance_date_str]
        for i in reversed(delete_rows):
            attendance_sheet.delete_rows(i)

        # insert fresh rows
        for e in EMPLOYEES:
            attendance_sheet.append_row([
                attendance_date_str,
                e,
                "✖" if m[e] else "✔",
                "✖" if a[e] else "✔",
                "✖" if n[e] else "✔",
                entry_time
            ])

        st.success("Attendance saved successfully ✅")

# =========================================================
# 📊 EXPENSE ANALYTICS
# =========================================================
with expense_analytics_tab:

    st.markdown("## 📊 Expense Analytics")

    records = expense_sheet.get_all_records()
    if not records:
        st.info("No expense data available yet.")
    else:
        df = pd.DataFrame(records)

        df["datetime"] = pd.to_datetime(df.iloc[:, 0], format="%d/%m/%Y %H:%M")
        df["date"] = df["datetime"].dt.date
        df["amount"] = pd.to_numeric(df.iloc[:, 3])

        st.metric("💰 Total Spend", f"₹ {df['amount'].sum():,.0f}")

        st.markdown("### 📈 Daily Spend Trend")
        daily = df.groupby("date")["amount"].sum()
        st.line_chart(daily)

        st.markdown("### 📊 Category-wise Spend")
        category_spend = df.groupby(df.iloc[:, 1])["amount"].sum()
        st.bar_chart(category_spend)

        st.markdown("### 💳 Payment Mode Split")
        payment_spend = df.groupby(df.iloc[:, 4])["amount"].sum()

        fig, ax = plt.subplots()
        ax.pie(
            payment_spend,
            labels=payment_spend.index,
            autopct="%1.0f%%",
            startangle=90
        )
        ax.axis("equal")
        st.pyplot(fig)

# =========================================================
# 📈 ATTENDANCE ANALYTICS
# =========================================================
with attendance_analytics_tab:

    st.markdown("## 📈 Attendance Analytics")

    records = attendance_sheet.get_all_records()
    if not records:
        st.info("No attendance data available yet.")
    else:
        df = pd.DataFrame(records)

        st.metric("👥 Total Employees", df["employee_name"].nunique())

        absents = {
            "Morning": (df["morning"] == "✖").sum(),
            "Afternoon": (df["afternoon"] == "✖").sum(),
            "Night": (df["night"] == "✖").sum()
        }

        st.markdown("### ❌ Absentees by Shift")
        st.bar_chart(pd.Series(absents))
