import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Outlook account credentials
sender_email = os.getenv("OUTLOOK_EMAIL")
password = os.getenv("OUTLOOK_PASSWORD")

# List of recipients
receiver_emails = [
    "ITDSIU21091@student.hcmiu.edu.vn",
    "ITDSIU21123@student.hcmiu.edu.vn",
    "ITDSIU21117@student.hcmiu.edu.vn",
]

# Create the email
subject = "⚠ ALERT: Intrusion Detected"
body = "Alert! Someone has intruded the restricted area. See the attached image."

message = MIMEMultipart()
message["From"] = sender_email
message["To"] = ", ".join(receiver_emails)
message["Subject"] = subject
message.attach(MIMEText(body, "plain"))

# Attach the image
filename = "./alert.png"  # Ensure this file exists
try:
    with open(filename, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {filename}",
    )
    message.attach(part)
except FileNotFoundError:
    print(f"❌ File '{filename}' not found. No image attached.")

# Send the email
try:
    with smtplib.SMTP("smtp.office365.com", 587) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_emails, message.as_string())
    print("✅ Email sent successfully to all recipients!")
except Exception as e:
    print("❌ Failed to send email:", e)
