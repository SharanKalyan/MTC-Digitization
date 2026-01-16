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
    page_title="Restaurant Expense Entry",
    layout="centered"
)

# -----------------------------
# PIN Protection
# -----------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# -----------------------------
# PIN Protection
# -----------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("### 🔒 Enter PIN to Access")

    with st.form("pin_form"):
        pin_input = st.text_input(
            "PIN",
            type="password",
            max_chars=6
        )

        pin_submit = st.form_submit_button("➡️ Enter")

    if pin_submit:
        if pin_input == st.secrets["security"]["app_pin"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect PIN ❌")

    st.stop()



# -----------------------------
# Title Section
# -----------------------------
st.markdown('<div class="content-box">', unsafe_allow_html=True)

st.markdown(
    "<h2 style='text-align:center;'>🍽️ Monisha Tiffin Center</h2>"
    "<h4 style='text-align:center;'>Expense Entry</h4>",
    unsafe_allow_html=True
)

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
            "Non-Veg"
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

st.markdown('</div>', unsafe_allow_html=True)






