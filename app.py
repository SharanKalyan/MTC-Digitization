import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import base64

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

expense_sheet = client.open("MTC-Digitization").sheet1
attendance_sheet = client.open("MTC-Digitization").worksheet("Attendance")

# -----------------------------
# Time Handling
# -----------------------------
ist = pytz.timezone("Asia/Kolkata")
current_time = datetime.now(ist)
formatted_time = current_time.strftime("%d/%m/%Y %H:%M")
today_date = current_time.strftime("%d/%m/%Y")

# -----------------------------
# Tabs
# -----------------------------
expense_tab, attendance_tab = st.tabs(["🧾 Expense", "🧑‍🍳 Attendance"])

# =========================================================
# 🧾 EXPENSE TAB
# =========================================================
with expense_tab:

    st.markdown("## 🧾 Expense Entry")

    with st.form("expense_form"):

        st.text_input("Date & Time", value=formatted_time, disabled=True)

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
                formatted_time,
                category,
                sub_category,
                expense_amount,
                payment_mode,
                expense_by
            ])
            st.success("Expense recorded successfully ✅")

# =========================================================
# 🧑‍🍳 ATTENDANCE TAB
# =========================================================
with attendance_tab:

    st.markdown("## 🧑‍🍳 Employee Attendance")

    EMPLOYEES = ["RK", "AR", "YS"]

    st.text_input("Date", value=today_date, disabled=True)

    absentees = st.multiselect(
        "Select absentees (leave empty if all are present)",
        EMPLOYEES
    )

    if st.button("✅ Submit Attendance"):

        for emp in EMPLOYEES:
            status = "Absent" if emp in absentees else "Present"

            attendance_sheet.append_row([
                today_date,
                emp,
                status,
                formatted_time
            ])

        st.success("Attendance recorded successfully ✅")
