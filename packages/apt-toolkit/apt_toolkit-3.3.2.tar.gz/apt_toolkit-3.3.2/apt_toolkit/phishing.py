
import os
import smtplib
import threading
import time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

_EMAIL_RATE_LIMIT_SECONDS = 3
_last_email_sent_at = 0.0
_send_lock = threading.Lock()


def _apply_rate_limit():
    """Pause until it is safe to send the next SMTP email."""
    global _last_email_sent_at
    with _send_lock:
        now = time.monotonic()
        elapsed = now - _last_email_sent_at
        if elapsed < _EMAIL_RATE_LIMIT_SECONDS:
            time.sleep(_EMAIL_RATE_LIMIT_SECONDS - elapsed)
        _last_email_sent_at = time.monotonic()

def send_email(sender_email, sender_password, receiver_email, subject, body, attachment_path, smtp_server, smtp_port):
    """
    Sends an email with an attachment.

    Args:
        sender_email (str): The email address of the sender.
        sender_password (str): The password of the sender.
        receiver_email (str): The email address of the receiver.
        subject (str): The subject of the email.
        body (str): The body of the email.
        attachment_path (str): The path to the attachment file.
        smtp_server (str): The SMTP server address.
        smtp_port (int): The SMTP server port.
    """
    _apply_rate_limit()

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    if attachment_path and os.path.exists(attachment_path):
        filename = os.path.basename(attachment_path)
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {filename}",
        )
        msg.attach(part)

    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        print(f"Email sent successfully to {receiver_email}!")
    except Exception as e:
        print(f"Failed to send email to {receiver_email}: {e}")
