import streamlit as st
import gspread
import pandas as pd
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
balance_sheet = spreadsheet.worksheet("Daily_Balance")

# -------------------------------------------------
# Time Handling (IST)
# -------------------------------------------------
ist = pytz.timezone("Asia/Kolkata")
now = datetime.now(ist)

# -------------------------------------------------
# Navigation (Dropdown)
# -------------------------------------------------
st.markdown("### 📍 Select Section")

section = st.selectbox(
    "",
    [
        "📊 Today's Summary",
        "🧾 Expense Entry",
        "💰 Sales Entry",
        "🧑‍🍳 Attendance",
        "📊 Expense Analytics",
        "📈 Attendance Analytics",
        "📊 Sales Analytics",
    ],
    index=0
)

# =================================================
# 📊 TODAY SUMMARY (RUNNING BALANCE)
# =================================================
if section == "📊 Today's Summary":

    st.markdown("## 📊 Today's Summary")

    today_sales_str = now.strftime("%d-%m-%Y")
    today_expense_str = now.strftime("%d/%m/%Y")

    # ---------- SALES ----------
    sales_df = pd.DataFrame(sales_sheet.get_all_records())
    if not sales_df.empty:
        sales_df["Cash Total"] = pd.to_numeric(sales_df["Cash Total"])
        today_sales = sales_df[sales_df["Date"] == today_sales_str]

        bigstreet_total = today_sales[today_sales["Store"] == "Bigstreet"]["Cash Total"].sum()
        main_total = today_sales[today_sales["Store"] == "Main"]["Cash Total"].sum()
        orders_total = today_sales[today_sales["Store"] == "Orders"]["Cash Total"].sum()
        total_sales_today = bigstreet_total + main_total + orders_total
    else:
        bigstreet_total = main_total = orders_total = total_sales_today = 0

    # ---------- EXPENSE ----------
    expense_df = pd.DataFrame(expense_sheet.get_all_records())
    if not expense_df.empty:
        expense_df["Expense Amount"] = pd.to_numeric(expense_df["Expense Amount"])
        expense_df["Date"] = expense_df["Date & Time"].str.split(" ").str[0]
        total_expense_today = expense_df[
            expense_df["Date"] == today_expense_str
        ]["Expense Amount"].sum()
    else:
        total_expense_today = 0

    # ---------- OPENING BALANCE ----------
    balance_df = pd.DataFrame(balance_sheet.get_all_records())
    if not balance_df.empty:
        balance_df["Date"] = pd.to_datetime(balance_df["Date"], format="%d-%m-%Y")
        balance_df = balance_df.sort_values("Date")
        opening_balance = balance_df.iloc[-1]["Closing Balance"]
    else:
        opening_balance = 0  # first day

    # ---------- CLOSING BALANCE ----------
    closing_balance = opening_balance + total_sales_today - total_expense_today

    # ---------- UI ----------
    st.metric("📥 Opening Balance", f"₹ {opening_balance:,.0f}")

    st.metric("🏪 Bigstreet Sales", f"₹ {bigstreet_total:,.0f}")
    st.metric("🏬 Main Store Sales", f"₹ {main_total:,.0f}")
    st.metric("📦 Orders Sales", f"₹ {orders_total:,.0f}")

    st.markdown("---")

    st.metric("💵 Total Sales Today", f"₹ {total_sales_today:,.0f}")
    st.metric("💸 Total Expense Today", f"₹ {total_expense_today:,.0f}")

    st.markdown("---")

    st.metric("💰 Balance Remaining Today", f"₹ {closing_balance:,.0f}")

    if st.button("📌 Save Closing Balance for Today"):
       balance_sheet.append_row([
       today_sales_str,
       int(opening_balance),
       int(total_sales_today),
       int(total_expense_today),
       int(closing_balance),
       now.strftime("%d/%m/%Y %H:%M")
    ])
        st.success("Closing balance saved successfully ✅")

# =================================================
# 🧾 EXPENSE ENTRY
# =================================================
elif section == "🧾 Expense Entry":

    st.markdown("## 🧾 Expense Entry")

    with st.form("expense_form"):
        exp_date = st.date_input("Expense Date", value=now.date())
        exp_time = st.time_input("Expense Time", value=now.time().replace(second=0, microsecond=0))
        exp_datetime = datetime.combine(exp_date, exp_time).strftime("%d/%m/%Y %H:%M")

        category = st.selectbox("Category", [
            "Groceries","Vegetables","Non-Veg","Milk","Banana Leaf",
            "Maintenance","Electricity","Rent",
            "Salary and Advance","Transportation","Others"
        ])

        sub_category = st.text_input("Sub-Category")
        amount = st.number_input("Expense Amount", min_value=0.0, step=1.0)
        payment = st.selectbox("Payment Mode", ["Cash","UPI","Cheque"])
        by = st.selectbox("Expense By", ["RK","AR","YS"])

        submit = st.form_submit_button("✅ Submit Expense")

    if submit:
        expense_sheet.append_row([exp_datetime, category, sub_category, amount, payment, by])
        st.success("Expense recorded successfully ✅")

# =================================================
# 💰 SALES ENTRY
# =================================================
elif section == "💰 Sales Entry":

    st.markdown("## 💰 Sales Entry")

    with st.form("sales_form"):
        sale_date = st.date_input("Sale Date", value=now.date()).strftime("%d-%m-%Y")
        store = st.selectbox("Store", ["Bigstreet", "Main", "Orders"])
        time_slot = st.radio("Time Slot", ["Morning", "Night", "Full Day"], horizontal=True)
        cash_total = st.number_input("Cash Total", min_value=0.0, step=100.0)
        submit = st.form_submit_button("✅ Submit Sales")

    if submit:
        rows = sales_sheet.get_all_values()
        for i in reversed([
            idx for idx, r in enumerate(rows[1:], start=2)
            if r[0] == sale_date and r[1] == store and r[2] == time_slot
        ]):
            sales_sheet.delete_rows(i)

        sales_sheet.append_row([
            sale_date, store, time_slot,
            cash_total, now.strftime("%d/%m/%Y %H:%M")
        ])
        st.success("Sales recorded successfully ✅")

# =================================================
# 🧑‍🍳 ATTENDANCE
# =================================================
elif section == "🧑‍🍳 Attendance":

    st.markdown("## 🧑‍🍳 Employee Attendance")

    EMPLOYEES = [
        "Vinoth","Ravi","Mani","Ansari","Kumar","Hari",
        "Samuthuram","Ramesh","Punitha","Vembu","Devi",
        "Babu","Latha","Indhra","Ambiga","RY","YS",
        "Poosari","Balaji"
    ]

    att_date = st.date_input("Attendance Date", value=now.date()).strftime("%d/%m/%Y")
    entry_time = now.strftime("%d/%m/%Y %H:%M")

    st.markdown("### 🌅 Morning")
    morning = {e: st.checkbox(e, key=f"m_{e}") for e in EMPLOYEES}

    st.markdown("### ☀️ Afternoon")
    afternoon = {e: st.checkbox(e, key=f"a_{e}") for e in EMPLOYEES}

    st.markdown("### 🌙 Night")
    night = {e: st.checkbox(e, key=f"n_{e}") for e in EMPLOYEES}

    if st.button("✅ Submit Attendance"):
        rows = attendance_sheet.get_all_values()
        for i in reversed([
            idx for idx, r in enumerate(rows[1:], start=2)
            if r[0] == att_date
        ]):
            attendance_sheet.delete_rows(i)

        for emp in EMPLOYEES:
            attendance_sheet.append_row([
                att_date,
                emp,
                "✖" if morning[emp] else "✔",
                "✖" if afternoon[emp] else "✔",
                "✖" if night[emp] else "✔",
                entry_time
            ])

        st.success("Attendance saved successfully ✅")

# =================================================
# 📊 EXPENSE ANALYTICS
# =================================================
elif section == "📊 Expense Analytics":
    st.markdown("## 📊 Expense Analytics")
    df = pd.DataFrame(expense_sheet.get_all_records())
    df["Expense Amount"] = pd.to_numeric(df["Expense Amount"])
    st.line_chart(df.groupby(df["Date & Time"].str[:10])["Expense Amount"].sum())

# =================================================
# 📈 ATTENDANCE ANALYTICS
# =================================================
elif section == "📈 Attendance Analytics":
    st.markdown("## 📈 Attendance Analytics")
    df = pd.DataFrame(attendance_sheet.get_all_records())
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
    df = pd.DataFrame(sales_sheet.get_all_records())
    df["Cash Total"] = pd.to_numeric(df["Cash Total"])
    st.bar_chart(df.groupby("Store")["Cash Total"].sum())

