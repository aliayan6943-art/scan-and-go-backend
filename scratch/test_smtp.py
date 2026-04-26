import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv(override=True)

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def test_smtp():
    print(f"Testing SMTP with {SMTP_EMAIL}...")
    print(f"Server: {SMTP_SERVER}:{SMTP_PORT}")
    print(f"Password length: {len(SMTP_PASSWORD) if SMTP_PASSWORD else 0}")
    
    msg = MIMEText("SMTP Test Connection")
    msg['Subject'] = "SMTP Test"
    msg['From'] = SMTP_EMAIL
    msg['To'] = SMTP_EMAIL

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            print("Logging in...")
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
            print("SUCCESS! Email sent.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_smtp()
