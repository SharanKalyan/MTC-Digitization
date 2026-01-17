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
sales_sheet = spreadsheet.worksheet("Sales")

# -------------------------------------------------
# Time Handling (IST)
# -------------------------------------------------
ist = pytz.timezone("Asia/Kolkata")
now = datetime.now(ist)

# -------------------------------------------------
# Tabs
# -------------------------------------------------
(
    expense_tab,
    attendance_tab,
    sales_tab,
    expense_analytics_tab,
    attendance_analytics_tab,
    sales_analytics_tab
) = st.tabs([
    "🧾 Expense",
    "🧑‍🍳 Attendance",
    "💰 Sales",
    "📊 Expense Analytics",
    "📈 Attendance Analytics",
    "📊 Sales Analytics"
])

# =================================================
# 🧾 EXPENSE TAB (UNCHANGED)
# =================================================
with expense_tab:
    st.markdown("## 🧾 Expense Entry")

    with st.form("expense_form"):
        exp_date = st.date_input("Expense Date", value=now.date())
        exp_time = st.time_input("Expense Time", value=now.time().replace(second=0, microsecond=0))
        exp_datetime = datetime.combine(exp_date, exp_time)
        exp_datetime_str = exp_datetime.strftime("%d/%m/%Y %H:%M")

        category = st.selectbox("Category", [
            "Groceries","Vegetables","Non-Veg","Milk","Banana Leaf",
            "Maintenance","Electricity","Rent",
            "Salary and Advance","Transportation","Others"
        ])

        sub_category = st.text_input("Sub-Category")
        amount = st.number_input("Expense Amount", min_value=0.0, step=1.0)
        payment = st.selectbox("Payment Mode", ["Cash","UPI","Cheque"])
        by = st.selectbox("Expense By", ["RK","AR","YS"])

        submit_expense = st.form_submit_button("✅ Submit Expense")

    if submit_expense:
        if amount == 0:
            st.error("Expense amount must be greater than 0")
        else:
            expense_sheet.append_row([
                exp_datetime_str, category, sub_category,
                amount, payment, by
            ])
            st.success("Expense recorded successfully ✅")

# =================================================
# 🧑‍🍳 ATTENDANCE TAB (UNCHANGED)
# =================================================
with attendance_tab:
    st.markdown("## 🧑‍🍳 Employee Attendance")

    EMPLOYEES = [
        "Vinoth","Ravi","Mani","Ansari","Kumar","Hari",
        "Samuthuram","Ramesh","Punitha","Vembu","Devi",
        "Babu","Latha","Indhra","Ambiga","RY","YS",
        "Poosari","Balaji"
    ]

    att_date = st.date_input("Attendance Date", value=now.date())
    att_date_str = att_date.strftime("%d/%m/%Y")
    entry_time = now.strftime("%d/%m/%Y %H:%M")

    st.markdown("### ❌ Morning Absentees")
    m = {e: st.checkbox(e, key=f"m_{e}") for e in EMPLOYEES}

    st.markdown("### ❌ Afternoon Absentees")
    a = {e: st.checkbox(e, key=f"a_{e}") for e in EMPLOYEES}

    st.markdown("### ❌ Night Absentees")
    n = {e: st.checkbox(e, key=f"n_{e}") for e in EMPLOYEES}

    if st.button("✅ Submit Attendance"):
        rows = attendance_sheet.get_all_values()
        delete_rows = [i for i, r in enumerate(rows[1:], start=2) if r[0] == att_date_str]
        for i in reversed(delete_rows):
            attendance_sheet.delete_rows(i)

        for e in EMPLOYEES:
            attendance_sheet.append_row([
                att_date_str,
                e,
                "✖" if m[e] else "✔",
                "✖" if a[e] else "✔",
                "✖" if n[e] else "✔",
                entry_time
            ])
        st.success("Attendance saved successfully ✅")

# =================================================
# 💰 SALES TAB (BUG-FREE & SIMPLE)
# =================================================
with sales_tab:

    st.markdown("## 💰 Sales Entry")

    with st.form("sales_form"):

        sale_date = st.date_input("Sale Date", value=now.date())
        sale_date_str = sale_date.strftime("%d-%m-%Y")

        store = st.selectbox("Store", ["Bigstreet", "Main", "Orders"])

        time_slot = st.radio(
            "Time Slot",
            ["Morning", "Night", "Full Day"],
            horizontal=True
        )

        cash_total = st.number_input(
            "Cash Total",
            min_value=0.0,
            step=100.0
        )

        submit_sale = st.form_submit_button("✅ Submit Sales")

    if submit_sale:
        if cash_total == 0:
            st.error("Cash total must be greater than 0")
        else:
            rows = sales_sheet.get_all_values()
            delete_rows = [
                i for i, r in enumerate(rows[1:], start=2)
                if r[0] == sale_date_str and r[1] == store and r[2] == time_slot
            ]

            for i in reversed(delete_rows):
                sales_sheet.delete_rows(i)

            sales_sheet.append_row([
                sale_date_str,
                store,
                time_slot,
                cash_total,
                now.strftime("%d/%m/%Y %H:%M")
            ])

            st.success("Sales recorded successfully ✅")


# =================================================
# 📊 SALES ANALYTICS (NEW)
# =================================================
with sales_analytics_tab:
    st.markdown("## 📊 Sales Analytics")

    records = sales_sheet.get_all_records()
    if not records:
        st.info("No sales data yet.")
    else:
        df = pd.DataFrame(records)

        df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y")
        df["Cash Total"] = pd.to_numeric(df["Cash Total"])

        st.metric("💵 Total Sales", f"₹ {df['Cash Total'].sum():,.0f}")

        st.markdown("### 📈 Daily Sales Trend")
        daily_sales = df.groupby("Date")["Cash Total"].sum()
        st.line_chart(daily_sales)

        st.markdown("### 🏪 Store-wise Sales")
        store_sales = df.groupby("Store")["Cash Total"].sum()
        st.bar_chart(store_sales)

        st.markdown("### ⏱ Sales by Time Slot")
        slot_sales = df.groupby("Time Slot")["Cash Total"].sum()
        st.bar_chart(slot_sales)




