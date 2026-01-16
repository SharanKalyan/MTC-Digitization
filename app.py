import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Restaurant Expense Entry",
    layout="centered"
)

st.title("🧾 Expense Entry")

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
sheet = client.open("MTC-Digitization").sheet1

# sheets = client.openall()
# st.write([s.title for s in sheets])



# -----------------------------
# IST Timestamp
# -----------------------------
ist = pytz.timezone("Asia/Kolkata")
current_time = datetime.now(ist).strftime("%d/%m/%Y %H:%M")

# -----------------------------
# UI Form
# -----------------------------
with st.form("expense_form"):

    st.text_input(
        "Date & Time",
        value=current_time,
        disabled=True
    )

    category = st.selectbox(
        "Category",
        [
            "Groceries",
            "Vegetables",
            "Milk",
            "Banana Leaf",
            "Maintenance",
            "Electricity",
            "Rent",
            "Salary and Advance",
            "Transportation"
        ]
    )

    sub_category = st.text_input(
        "Sub-Category",
        placeholder="e.g., Vegetables, repair Etc. "
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

    submitted = st.form_submit_button("✅ Submit Expense")

# -----------------------------
# Save to Google Sheets
# -----------------------------
if submitted:

    if expense_amount == 0:
        st.error("Expense amount must be greater than 0")
    else:
        row = [
            current_time,
            category,
            sub_category,
            expense_amount,
            payment_mode,
            expense_by
        ]

        sheet.append_row(row)

        st.success("Expense recorded successfully ✅")

