
# scripts/email_report.py
import os, smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def _parse_recipients(val):
    if not val: return []
    parts = [p.strip() for p in val.split(",") if p.strip()]
    return parts

def send_email(subject: str, body: str, attachments=None):
    sender = os.environ["EMAIL_FROM"]
    to_list = _parse_recipients(os.environ.get("EMAIL_TO",""))
    cc_list = _parse_recipients(os.environ.get("EMAIL_CC",""))
    bcc_list = _parse_recipients(os.environ.get("EMAIL_BCC",""))
    recipients = to_list + cc_list + bcc_list
    if not recipients:
        raise RuntimeError("No recipients: set EMAIL_TO or use segmented sender.")

    host = os.environ.get("SMTP_HOST","smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT","587"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASS"]

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(body, "plain"))
    msg.attach(alt)

    # optional attachments
    for path in (attachments or []):
        if not os.path.exists(path): 
            continue
        with open(path, "rb") as f:
            data = f.read()
        from email.mime.base import MIMEBase
        from email import encoders
        part = MIMEBase("application", "octet-stream")
        part.set_payload(data)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(path)}"')
        msg.attach(part)

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port) as server:
        server.starttls(context=context)
        server.login(user, password)
        server.sendmail(sender, recipients, msg.as_string())

if __name__ == "__main__":
    with open("reports/daily_summary.txt","r") as f:
        text = f.read()
    send_email("Daily Investment Update", text, attachments=["reports/positions_latest.csv"])
    print("Email sent")
