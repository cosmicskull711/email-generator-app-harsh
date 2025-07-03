import streamlit as st
import base64
import os
import csv
import json
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# === Send Email via Gmail ===
def send_email_via_gmail(subject, body, recipient):
    try:
        token_info = json.loads(st.secrets["token"])
        creds = Credentials.from_authorized_user_info(token_info, ['https://www.googleapis.com/auth/gmail.send'])
        service = build('gmail', 'v1', credentials=creds)

        message = MIMEText(body)
        message['to'] = recipient
        message['subject'] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        message = {'raw': raw}

        sent_message = service.users().messages().send(userId="me", body=message).execute()
        return f"✅ Email sent to {recipient}! ID: {sent_message['id']}"

    except HttpError as e:
        error_reason = e._get_reason().lower()
        if "rate limit" in error_reason or "quota" in error_reason or "daily limit" in error_reason:
            return f"❌ API limit reached: {error_reason}"
        return f"❌ Failed to send email to {recipient}: {error_reason}"

    except Exception as e:
        return f"❌ Failed to send email to {recipient}: {str(e)}"

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

st.header("Generate & Send Emails 📧")

form_content_file = "email_template.txt"
default_text = read_content_from_file(form_content_file)

form_input = st.text_area('Enter the email topic or message', value=default_text, height=275)

col1, col2 = st.columns(2)
with col1:
    email_sender = st.text_input('Sender Name')
    email_subject = st.text_input('Email Subject')
with col2:
    email_csv_file = "emails.csv"
    email_recipients = read_recipients_from_csv(email_csv_file)
    email_style = st.selectbox(
        'Writing Style',
        ('Formal', 'Appreciating', 'Not Satisfied', 'Neutral'),
        index=0
    )

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
            results = []
            for recipient in email_recipients:
                result = send_email_via_gmail(email_subject, st.session_state.email_body, recipient)
                results.append(result)
                st.success(result)

                # Stop on rate/daily limit
                if "rate limit" in result.lower() or "quota" in result.lower() or "daily limit" in result.lower():
                    st.warning("🚫 Gmail API limit reached. Stopping further emails.")
                    break

            st.session_state.email_ready = False  # Reset after sending
