import streamlit as st
from email.mime.text import MIMEText
from googleapiclient.discovery import build
import base64
import csv
import os
from utils import get_gmail_service

# === Gmail API Email Sending Function ===
def send_email_via_gmail(subject, body, recipient):
    try:
        service = get_gmail_service()
        message = MIMEText(body)
        message['to'] = recipient
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        message = {'raw': raw}
        sent_message = service.users().messages().send(userId="me", body=message).execute()
        return f"Email sent successfully to {recipient}! ID: {sent_message['id']}"
    except Exception as e:
        return f"Failed to send email to {recipient}: {str(e)}"

# === Read Emails from CSV ===
def read_recipients_from_csv(filename):
    recipients = []
    with open(filename, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if 'email' in row and row['email'].strip():
                recipients.append(row['email'].strip())
    return recipients

# === Read content from file ===
def read_content_from_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()

# === Convert image to base64 ===
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    else:
        return ""

# === Streamlit UI ===
st.set_page_config(
    page_title="Generate & Send Emails",
    page_icon='📧',
    layout='centered',
    initial_sidebar_state='collapsed'
)

# OPTIONAL BACKGROUND IMAGE — skip if not needed

st.header("Generate & Send Emails 📧")

# ✅ Use relative path for deployment
form_content_file = "email_template.txt"
default_text = read_content_from_file(form_content_file)

# Prefill the text area with editable content
form_input = st.text_area('Enter the email topic or message', value=default_text, height=275)

col1, col2 = st.columns(2)
with col1:
    email_sender = st.text_input('Sender Name')
    email_subject = st.text_input('Email Subject')
with col2:
    email_csv_file = "emails.csv"  # must also be in repo
    email_recipients = read_recipients_from_csv(email_csv_file)
    email_style = st.selectbox(
        'Writing Style',
        ('Formal', 'Appreciating', 'Not Satisfied', 'Neutral'),
        index=0
    )

# Session state to track email generation
if "email_body" not in st.session_state:
    st.session_state.email_body = ""
if "email_ready" not in st.session_state:
    st.session_state.email_ready = False

if st.button("Generate Email"):
    st.session_state.email_body = form_input
    st.session_state.email_ready = True
    st.success("Email Generated ✅")

if st.session_state.email_ready:
    st.markdown("**Preview:**")
    st.markdown(f"<div class='email-preview'>{st.session_state.email_body}</div>", unsafe_allow_html=True)

    if st.button("Send Email via Gmail"):
        with st.spinner("Sending Email..."):
            results = [send_email_via_gmail(email_subject, st.session_state.email_body, recipient) for recipient in email_recipients]
            for res in results:
                st.success(res)
            st.session_state.email_ready = False  # Reset after sending
