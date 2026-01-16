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
# Background Image Function
# -----------------------------
def set_background(image_file):
    with open(image_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        .content-box {{
            background-color: rgba(255, 255, 255, 0.92);
            padding: 30px;
            border-radius: 14px;
            max-width: 600px;
            margin: auto;
            box-shadow: 0px 4px 20px rgba(0,0,0,0.15);
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background("landingpage.png")

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
