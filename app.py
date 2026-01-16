import streamlit as st
import gspread
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

expense_sheet = client.open("MTC-Digitization").Expense
attendance_sheet = client.open("MTC-Digitization").worksheet("Attendance")

# -----------------------------
# Time Handling (IST – reference only)
# -----------------------------
ist = pytz.timezone("Asia/Kolkata")
now = datetime.now(ist)

# -----------------------------
# Tabs
# -----------------------------
expense_tab, attendance_tab = st.tabs(["💸 Expense", "🧑‍🍳 Attendance"])

# =========================================================
# 🧾 EXPENSE TAB (EDITABLE DATE + TIME – FIXED)
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

        # ✅ FIX: NO timezone conversion here
        selected_datetime = datetime.combine(
            expense_date,
            expense_time
        )

        formatted_expense_time = selected_datetime.strftime("%d/%m/%Y %H:%M")

        category = st.selectbox(
            "Category",
            [
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
                "Others",
            ]
        )

        sub_category = st.text_input(
            "Sub-Category",
            placeholder="e.g., Vegetables, Repair, etc."
        )

        expense_amount = st.number_input(
            "Expense Amount",
            min_value=0.0,
            step=1.0
        )

        payment_mode = st.selectbox(
            "Payment Mode",
            ["Cash", "UPI", "Cheque"]
        )

        expense_by = st.selectbox(
            "Expense By",
            ["RK", "AR", "YS"]
        )

        submit_expense = st.form_submit_button("✅ Submit Expense")

    if submit_expense:
        if expense_amount == 0:
            st.error("Expense amount must be greater than 0")
        else:
            expense_sheet.append_row([
                formatted_expense_time,
                category,
                sub_category,
                expense_amount,
                payment_mode,
                expense_by
            ])
            st.success("Expense recorded successfully ✅")

# =========================================================
# 🧑‍🍳 ATTENDANCE TAB (BACKDATED + OVERWRITE – CORRECT)
# =========================================================
with attendance_tab:

    st.markdown("## 🧑‍🍳 Employee Attendance")

    EMPLOYEES = [
        "Vinoth", "Ravi", "Mani", "Ansari", "Kumar", "Hari",
        "Samuthuram", "Ramesh", "Punitha", "Vembu", "Devi",
        "Babu", "Latha", "Indhra", "Ambiga", "RY", "YS",
        "Poosari", "Balaji"
    ]

    attendance_date = st.date_input(
        "Attendance Date",
        value=now.date()
    )

    attendance_date_str = attendance_date.strftime("%d/%m/%Y")
    entry_time = datetime.now(ist).strftime("%d/%m/%Y %H:%M")

    st.markdown("### ❌ Morning Absentees")
    morning_absent = {emp: st.checkbox(emp, key=f"m_{emp}") for emp in EMPLOYEES}

    st.markdown("### ❌ Afternoon Absentees")
    afternoon_absent = {emp: st.checkbox(emp, key=f"a_{emp}") for emp in EMPLOYEES}

    st.markdown("### ❌ Night Absentees")
    night_absent = {emp: st.checkbox(emp, key=f"n_{emp}") for emp in EMPLOYEES}

    if st.button("✅ Submit Attendance"):

        # Delete existing records for selected date
        all_rows = attendance_sheet.get_all_values()
        rows_to_delete = []

        for idx, row in enumerate(all_rows[1:], start=2):
            if row[0] == attendance_date_str:
                rows_to_delete.append(idx)

        for row_idx in reversed(rows_to_delete):
            attendance_sheet.delete_rows(row_idx)

        # Insert new records
        for emp in EMPLOYEES:
            attendance_sheet.append_row([
                attendance_date_str,
                emp,
                "✖" if morning_absent[emp] else "✔",
                "✖" if afternoon_absent[emp] else "✔",
                "✖" if night_absent[emp] else "✔",
                entry_time
            ])

        st.success("Attendance saved successfully (previous entries overwritten) ✅")


