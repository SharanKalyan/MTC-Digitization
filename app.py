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
# 📊 TODAY SUMMARY
# =================================================
if section == "📊 Today's Summary":

    st.markdown("## 📊 Today's Summary")

    today_sales_str = now.strftime("%d-%m-%Y")
    today_expense_str = now.strftime("%d/%m/%Y")

    # ---------- SALES ----------
    sales_df = pd.DataFrame(sales_sheet.get_all_records())
    if not sales_df.empty:
        sales_df["Cash Total"] = pd.to_numeric(sales_df["Cash Total"], errors="coerce")
        today_sales = sales_df[sales_df["Date"] == today_sales_str]
        total_sales_today = today_sales["Cash Total"].sum()
    else:
        total_sales_today = 0

    # ---------- EXPENSE ----------
    expense_df = pd.DataFrame(expense_sheet.get_all_records())
    if not expense_df.empty:
        expense_df["Expense Amount"] = pd.to_numeric(expense_df["Expense Amount"], errors="coerce")
        expense_df["Date"] = expense_df["Date & Time"].str.split(" ").str[0]
        total_expense_today = expense_df[
            expense_df["Date"] == today_expense_str
        ]["Expense Amount"].sum()
    else:
        total_expense_today = 0

    # ---------- OPENING BALANCE ----------
    balance_df = pd.DataFrame(balance_sheet.get_all_records())
    if not balance_df.empty:
        opening_balance = int(balance_df.iloc[-1]["Closing Balance"])
    else:
        opening_balance = 0

    closing_balance = opening_balance + total_sales_today - total_expense_today

    st.metric("📥 Opening Balance", f"₹ {opening_balance:,.0f}")
    st.metric("💵 Total Sales Today", f"₹ {total_sales_today:,.0f}")
    st.metric("💸 Total Expense Today", f"₹ {total_expense_today:,.0f}")
    st.metric("💰 Balance Remaining Today", f"₹ {closing_balance:,.0f}")

    if st.button("📌 Save Closing Balance for Today"):
        balance_sheet.append_row([
        today_sales_str,
        int(opening_balance),
        float(total_sales_today),
        float(total_expense_today),
        float(closing_balance),
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

        category = st.selectbox(
            "Category",
            ["Groceries","Vegetables","Non-Veg","Milk","Banana Leaf",
             "Maintenance","Electricity","Rent",
             "Salary and Advance","Transportation","Others"]
        )

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

    attendance = {}
    for emp in EMPLOYEES:
        attendance[emp] = st.checkbox(emp)

    if st.button("✅ Submit Attendance"):
        for emp, present in attendance.items():
            attendance_sheet.append_row([
                att_date, emp,
                "✔" if present else "✖",
                entry_time
            ])
        st.success("Attendance saved successfully ✅")

# =================================================
# 📊 EXPENSE ANALYTICS (ENHANCED)
# =================================================
elif section == "📊 Expense Analytics":

    st.markdown("## 📊 Expense Analytics")

    df = pd.DataFrame(expense_sheet.get_all_records())
    if df.empty:
        st.info("No expense data available yet.")
        st.stop()

    df["Expense Amount"] = pd.to_numeric(df["Expense Amount"], errors="coerce")
    df["datetime"] = pd.to_datetime(df["Date & Time"], format="%d/%m/%Y %H:%M", errors="coerce")

    df = df.dropna(subset=["datetime", "Expense Amount"])

    df["date"] = df["datetime"].dt.date
    df["week"] = df["datetime"].dt.isocalendar().week
    df["month"] = df["datetime"].dt.to_period("M")
    df["year"] = df["datetime"].dt.year

    st.metric("💸 Total Expense", f"₹ {df['Expense Amount'].sum():,.0f}")

    st.subheader("📂 Category-wise Expense")

    cat_expense = (
        df.groupby("Category")["Expense Amount"]
        .sum()
        .sort_values(ascending=False)
    )
    
    st.bar_chart(cat_expense)


    st.subheader("📈 Expense Trend")
    trend = st.radio("Trend Type", ["Daily","Weekly","Monthly"], horizontal=True)

    if trend == "Daily":
        trend_df = df.groupby("date")["Expense Amount"].sum()
    elif trend == "Weekly":
        trend_df = df.groupby("week")["Expense Amount"].sum()
    else:
        trend_df = df.groupby("month")["Expense Amount"].sum()

    st.line_chart(trend_df)

    st.subheader("💳 Payment Mode")
    pie_df = df.groupby("Payment Mode")["Expense Amount"].sum()
    fig, ax = plt.subplots()
    ax.pie(pie_df, labels=pie_df.index, autopct="%1.1f%%")
    st.pyplot(fig)

    st.subheader("👤 Expense By")
    st.bar_chart(df.groupby("Expense By")["Expense Amount"].sum())

# =================================================
# 📈 ATTENDANCE ANALYTICS
# =================================================
elif section == "📈 Attendance Analytics":

    df = pd.DataFrame(attendance_sheet.get_all_records())
    if df.empty:
        st.info("No attendance data.")
    else:
        st.bar_chart(df.groupby("Employee Name").size())

# =================================================
# 📊 SALES ANALYTICS
# =================================================
elif section == "📊 Sales Analytics":

    df = pd.DataFrame(sales_sheet.get_all_records())
    if df.empty:
        st.info("No sales data.")
    else:
        df["Cash Total"] = pd.to_numeric(df["Cash Total"], errors="coerce")
        st.bar_chart(df.groupby("Store")["Cash Total"].sum())


