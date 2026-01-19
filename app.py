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
    today_date = now.date()

    # ---------- SALES ----------
    sales_df = pd.DataFrame(sales_sheet.get_all_records())
    if not sales_df.empty:
        sales_df["Cash Total"] = pd.to_numeric(sales_df["Cash Total"], errors="coerce")
        today_sales = sales_df[sales_df["Date"] == today_sales_str]
        total_sales_today = float(today_sales["Cash Total"].sum())
    else:
        total_sales_today = 0.0

    # ---------- EXPENSE ----------
    expense_df = pd.DataFrame(expense_sheet.get_all_records())
    if not expense_df.empty:
        expense_df["Expense Amount"] = pd.to_numeric(expense_df["Expense Amount"], errors="coerce")
        expense_df["Date"] = expense_df["Date & Time"].str.split(" ").str[0]
        total_expense_today = float(
            expense_df[expense_df["Date"] == today_expense_str]["Expense Amount"].sum()
        )
    else:
        total_expense_today = 0.0

    # ---------- OPENING BALANCE (PREVIOUS DAY ONLY) ----------
    balance_df = pd.DataFrame(balance_sheet.get_all_records())

    if not balance_df.empty:
        balance_df["date"] = pd.to_datetime(
            balance_df["Date"],
            format="%d-%m-%Y",
            errors="coerce"
        ).dt.date

        prev_days = balance_df[balance_df["date"] < today_date]

        if not prev_days.empty:
            opening_balance = int(
                prev_days.sort_values("date").iloc[-1]["Closing Balance"]
            )
        else:
            opening_balance = 0
    else:
        opening_balance = 0

    # ---------- CLOSING BALANCE ----------
    closing_balance = opening_balance + total_sales_today - total_expense_today

    # ---------- UI ----------
    st.metric("📥 Opening Balance", f"₹ {opening_balance:,.0f}")
    st.metric("💵 Total Sales Today", f"₹ {total_sales_today:,.0f}")
    st.metric("💸 Total Expense Today", f"₹ {total_expense_today:,.0f}")
    st.metric("💰 Balance Remaining Today", f"₹ {closing_balance:,.0f}")

    # ---------- SAVE CLOSING BALANCE (ONCE PER DAY) ----------
    if st.button("📌 Save Closing Balance for Today"):

        if not balance_df.empty:
            already_saved = balance_df[
                balance_df["date"] == today_date
            ]
        else:
            already_saved = pd.DataFrame()

        if not already_saved.empty:
            st.warning("Closing balance for today is already saved ❗")
        else:
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
# 🧾 EXPENSE ENTRY (BULK / GRID STYLE)
# =================================================
elif section == "🧾 Expense Entry":

    st.markdown("## 🧾 Expense Entry")

    EXPENSE_CATEGORIES = [
        "Groceries",
        "Vegetables",
        "Non-Veg",
        "Milk",
        "Banana Leaf",
        "Maintenance",
        "Electricity",
        "Rent",
        "Salary and Advance",
        "Transportation",
        "Others"
    ]

    with st.form("bulk_expense_form"):

        # ---------- Date & Time ----------
        col1, col2 = st.columns(2)
        with col1:
            exp_date = st.date_input("Expense Date", value=now.date())
        with col2:
            exp_time = st.time_input(
                "Expense Time",
                value=now.time().replace(second=0, microsecond=0)
            )

        exp_datetime = datetime.combine(exp_date, exp_time).strftime("%d/%m/%Y %H:%M")

        st.markdown("---")
        st.markdown("### 🧾 Enter Expenses (tick the category you want to submit)")

        expense_rows = []

        for cat in EXPENSE_CATEGORIES:
            c1, c2, c3, c4, c5, c6 = st.columns([0.5, 2, 2, 1.5, 1.5, 1.5])

            with c1:
                selected = st.checkbox("", key=f"sel_{cat}")

            with c2:
                st.markdown(f"**{cat}**")

            with c3:
                sub_cat = st.text_input(
                    "Sub-category",
                    key=f"sub_{cat}",
                    label_visibility="collapsed"
                )

            with c4:
                amount = st.number_input(
                    "Amount",
                    min_value=0.0,
                    step=1.0,
                    key=f"amt_{cat}",
                    label_visibility="collapsed"
                )

            with c5:
                payment = st.selectbox(
                    "Payment",
                    ["Cash", "UPI", "Cheque"],
                    key=f"pay_{cat}",
                    label_visibility="collapsed"
                )

            with c6:
                by = st.selectbox(
                    "Expense By",
                    ["RK", "AR", "YS"],
                    key=f"by_{cat}",
                    label_visibility="collapsed"
                )

            expense_rows.append({
                "selected": selected,
                "category": cat,
                "sub_category": sub_cat,
                "amount": amount,
                "payment": payment,
                "by": by
            })

        submit = st.form_submit_button("✅ Submit Expenses")

    # ---------- SAVE ----------
    if submit:
        rows_added = 0

        for row in expense_rows:
            if row["selected"] and row["amount"] > 0:
                expense_sheet.append_row([
                    exp_datetime,
                    row["category"],
                    row["sub_category"],
                    float(row["amount"]),
                    row["payment"],
                    row["by"]
                ])
                rows_added += 1

        if rows_added > 0:
            st.success(f"✅ {rows_added} expense(s) recorded successfully")
        else:
            st.warning("⚠️ No expenses selected or amount entered")


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
# 🧑‍🍳 ATTENDANCE (2 SHIFTS: MORNING & NIGHT)
# =================================================
elif section == "🧑‍🍳 Attendance":

    st.markdown("## 🧑‍🍳 Employee Attendance")

    EMPLOYEES = [
        "Vinoth","Ravi","Mani","Ansari","Kumar","Sakthi","Vijaya","Hari",
        "Samuthuram","Ramesh","Punitha","Vembu","Devi",
        "Babu","Latha","Indhra","Ambika","RY","YS",
        "Poosari","Balaji"
    ]

    att_date = st.date_input(
        "Attendance Date",
        value=now.date()
    ).strftime("%d/%m/%Y")

    entry_time = now.strftime("%d/%m/%Y %H:%M")

    st.markdown("### 🌅 Morning (Tick if Absent)")
    morning = {
        emp: st.checkbox(emp, key=f"m_{emp}")
        for emp in EMPLOYEES
    }

    st.markdown("### 🌙 Night (Tick if Absent)")
    night = {
        emp: st.checkbox(emp, key=f"n_{emp}")
        for emp in EMPLOYEES
    }

    if st.button("✅ Submit Attendance"):

        # Remove existing attendance for the same date
        rows = attendance_sheet.get_all_values()
        for i in reversed([
            idx for idx, r in enumerate(rows[1:], start=2)
            if r[0] == att_date
        ]):
            attendance_sheet.delete_rows(i)

        # Insert fresh attendance
        for emp in EMPLOYEES:
            attendance_sheet.append_row([
                att_date,
                emp,
                "✖" if morning[emp] else "✔",
                "✖" if night[emp] else "✔",
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

    st.subheader(cat_expense)
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

    st.markdown("## 📈 Attendance Analytics")

    records = attendance_sheet.get_all_records()
    if not records:
        st.info("No attendance data available yet.")
        st.stop()

    df = pd.DataFrame(records)

    # ---------- Date handling ----------
    df["date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["date"])

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    current_year = now.year
    current_month = now.month

    # ---------- Absence calculation (2 shifts) ----------
    df["absent_shifts"] = (
        (df["Morning"] == "✖").astype(int) +
        (df["Night"] == "✖").astype(int)
    )

    # Convert shifts → leave days
    df["leave_days"] = df["absent_shifts"] / 2

    # =================================================
    # 1️⃣ Monthly vs Yearly Leave Analysis (IN DAYS)
    # =================================================
    st.subheader("📊 Leave Analysis (Days)")

    view_type = st.radio(
        "View leave data for:",
        ["Current Month", "Current Year"],
        horizontal=True,
        index=0
    )

    if view_type == "Current Month":
        temp = df[
            (df["year"] == current_year) &
            (df["month"] == current_month)
        ]
        title = "Leave days taken per employee (Current Month)"
    else:
        temp = df[df["year"] == current_year]
        title = "Leave days taken per employee (Current Year)"

    leave_df = (
        temp.groupby("Employee Name")["leave_days"]
        .sum()
        .sort_values(ascending=False)
    )

    st.caption(title)
    st.bar_chart(leave_df)

    st.markdown("---")

    # =================================================
    # 2️⃣ Shift-wise Absentee Breakdown (2 SHIFTS)
    # =================================================
    st.subheader("⏰ Shift-wise Absentee Breakdown")

    shift_absent = pd.Series({
        "Morning": (df["Morning"] == "✖").sum(),
        "Night": (df["Night"] == "✖").sum(),
    }).sort_values(ascending=False)

    st.caption("Total absentees per shift (all time)")
    st.bar_chart(shift_absent)



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














