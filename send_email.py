import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

sender_email = "your_email@outlook.com"
receiver_email = "recipient@example.com"
password = "your_app_password"

# Tạo message
msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = receiver_email
msg['Subject'] = 'Email with image attachment'

# Thêm nội dung text
msg.attach(MIMEText("This email contains an image as attachment.", 'plain'))

# Đọc và đính kèm ảnh
filename = "image.jpg"
with open(filename, "rb") as attachment:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
    msg.attach(part)

# Gửi mail
with smtplib.SMTP('smtp.office365.com', 587) as server:
    server.starttls()
    server.login(sender_email, password)
    server.send_message(msg)

print("✅ Email sent with image attachment.")
