import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_share_email(
    to_email: str,
    sharer_name: str,
    doc_title: str,
    share_url: str
) -> bool:
    """
    Sends a collaboration invite email.
    Returns True on success, False if SMTP is not configured or send fails.

    Required environment variables (.env):
        SMTP_HOST   e.g. smtp.gmail.com
        SMTP_PORT   e.g. 587  (default)
        SMTP_USER   your Gmail address
        SMTP_PASS   your Gmail App Password (not your regular password)
        APP_URL     e.g. http://localhost:8000
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if not all([smtp_host, smtp_user, smtp_pass]):
        return False  # Email not configured — caller handles this gracefully

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f'{sharer_name} invited you to collaborate on "{doc_title}"'
    msg["From"] = smtp_user
    msg["To"] = to_email

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family:-apple-system,sans-serif;background:#f5f5f5;padding:40px 20px;margin:0">
      <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:12px;
                  padding:40px;box-shadow:0 2px 8px rgba(0,0,0,0.08)">
        <div style="font-family:monospace;font-size:20px;font-weight:bold;
                    color:#f0a030;margin-bottom:24px">DN DevNote</div>
        <h2 style="margin:0 0 12px;color:#1a1a2e;font-size:20px">
          {sharer_name} wants to collaborate with you
        </h2>
        <p style="color:#6b7299;margin:0 0 24px;line-height:1.6">
          You've been invited to view and edit
          <strong style="color:#1a1a2e">"{doc_title}"</strong>.
          Click below to open the document.
        </p>
        <a href="{share_url}"
           style="display:inline-block;background:#f0a030;color:#0b0b12;
                  text-decoration:none;padding:12px 28px;border-radius:8px;
                  font-weight:600;font-size:15px">
          Open Document →
        </a>
        <p style="color:#94a3b8;font-size:12px;margin:24px 0 0;line-height:1.5">
          You'll need a DevNote account to edit this document.<br>
          Create one for free when you follow the link.
        </p>
      </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[DevNote] Email send failed: {e}")
        return False
