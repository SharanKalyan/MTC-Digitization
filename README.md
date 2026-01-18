# Monisha Tiffin Center – SMB Digitalization & Analytics System

## Project Context

This project began when a small and medium-sized restaurant (SMB) owner approached me with a common but critical problem:

All sales, expenses, and employee attendance were being written manually in notebooks.
There was no visibility into daily performance, profits, or cash position — only handwritten records.

As the business grew, this manual process became:

- Error-prone
- Time-consuming
- Impossible to analyze
- Completely disconnected from decision-making

The owner wanted a simple, mobile-friendly solution that:
- Replaced pen-and-paper entries
- Required no technical knowledge
- Worked seamlessly on an Android phone
- Provided real-time visibility into business performance

This project is the result of that initiative. A full digital data entry + analytics pipeline tailored specifically for an SMB restaurant. 
https://www.google.com/maps/place/monisha+tiffin+centre/data=!4m2!3m1!1s0x3a52662014ac5a59:0xfdde7cced4ca755c?sa=X&ved=1t:242&ictx=111

## Objectives

The primary goals of this system were:
- Digitize daily operational data entry
- Minimize user friction (large buttons, mobile-first UI)
- Centralize data in a single source of truth
- Provide real-time analytics without complex tools
- Track actual cash position, not just daily profit

## Solution Overview

The solution is a Streamlit-based web application backed by Google Sheets as a lightweight database.

Why this stack?
Component	Reason
Streamlit	Rapid UI development, mobile-friendly, simple deployment. Google Sheets was Familiar to the SMB users, cloud-based, no database setup
Python + Pandas	Reliable analytics and data transformations
Service Account Auth	Secure access without user login complexity

The app is deployed on Streamlit Cloud and accessed via a browser, often saved to the phone’s home screen like an app.

## Security Model

- PIN-based access (stored securely using Streamlit Secrets)
- Google Sheets access restricted via service account
- No public credentials exposed in the repository
- Core Functional Modules
- Expense Management

Allows daily recording of expenses with:

Date & time (editable for backdated entries)

Category & sub-category

Amount

Payment mode

Person responsible

Outcome:

Complete visibility into where money is spent

Foundation for expense trend analytics

2️⃣ Sales Tracking

Handles sales across multiple revenue sources:

Bigstreet

Main Store

Orders

Key features:

Morning / Night / Full Day slots

Overwrites duplicate entries for accuracy

Cash-based entry (as per current business needs)

Outcome:

Clean daily sales data

Store-wise and slot-wise analysis

3️⃣ Employee Attendance

Attendance is recorded once per day with:

Morning, Afternoon, Night shifts

Grouped employee selection (mobile-optimized)

Absentees marked explicitly

Previous entries overwritten to avoid duplicates

Outcome:

Clear attendance history

Ability to identify frequently absent employees

Shift-wise absence analysis

4️⃣ Real-Time Analytics Dashboards

Built-in dashboards provide insights such as:

Expense Analytics

Day-wise expense trends

Historical expense tracking

Sales Analytics

Store-wise revenue breakdown

Time-slot analysis

Attendance Analytics

Total absences per employee

Shift-wise absentee trends

All analytics update in real time as data is entered.

5️⃣ Daily Cash Balance Tracking (Key Feature)

One of the most important additions was running cash balance tracking.

Instead of only showing:

Sales - Expenses = Today’s Profit


The system tracks:

Opening balance (carried forward)

Today’s total sales

Today’s total expenses

Closing balance (saved explicitly)

This mirrors real-world cash management in small businesses.

Example:

Yesterday Closing Balance: ₹25,000
Today Sales: ₹50,000
Today Expenses: ₹25,000

→ Today Closing Balance: ₹50,000


This gives the owner a true picture of cash-in-hand, not just daily margins.

📁 Data Architecture (Google Sheets)

Each operational area maps cleanly to its own sheet:

Sheet1 → Expenses

Attendance → Employee attendance

Sales → Sales entries

Daily_Balance → Opening & closing balances

This structure keeps data simple, auditable, and easy to export.

📱 Mobile-First Design Philosophy

Since the owner primarily uses an Android phone, the UI was designed with:

Dropdown-based navigation (instead of tabs)

Minimal typing

Large clickable elements

Simple forms

Clear success/error feedback

The goal was usability over complexity.

🚀 Impact & Outcomes

Eliminated handwritten notebooks

Reduced manual errors

Enabled data-driven decisions

Provided daily financial clarity

Created a foundation for future dashboards and forecasting

Most importantly, the owner now knows:

“How is my business actually performing — today, not later.”

🔮 Future Enhancements

Potential next steps include:

Weekly & monthly profit reports

Automatic daily closing reminders

Role-based access

Export to PDF / Excel

WhatsApp or push notifications

🧠 Final Note

This project demonstrates how simple tools, when designed correctly, can bring real operational clarity to small businesses.

It’s not about building complex systems — it’s about solving the right problem, in the right way, for the right user.
