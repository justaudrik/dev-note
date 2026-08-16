# import smtplib
# import ssl
# import os
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart


# # ── Shared SMTP sender ────────────────────────────────────────────────────────

# def _send_email(to_email: str, subject: str, html_body: str) -> bool:
#     """
#     Send an HTML email via SMTP.
#     Returns True on success, False if SMTP is not configured or send fails.

#     Supports all email domains and providers — configure via .env:
#       SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
#       SMTP_SSL=true   → direct SSL on port 465  (some providers)
#       SMTP_SSL=false  → STARTTLS on port 587     (default, works for Gmail/Outlook/Yahoo)
#       SMTP_FROM_NAME  → display name in "From" header (default: "DevNote")
#     """
#     host      = os.getenv("SMTP_HOST", "")
#     port      = int(os.getenv("SMTP_PORT", "587"))
#     user      = os.getenv("SMTP_USER", "")
#     password  = os.getenv("SMTP_PASS", "")
#     use_ssl   = os.getenv("SMTP_SSL", "false").lower() == "true"
#     from_name = os.getenv("SMTP_FROM_NAME", "DevNote")

#     if not all([host, user, password]):
#         return False  # SMTP not configured — caller handles this gracefully

#     msg = MIMEMultipart("alternative")
#     msg["Subject"] = subject
#     msg["From"]    = f"{from_name} <{user}>"   # "DevNote <you@gmail.com>"
#     msg["To"]      = to_email
#     msg.attach(MIMEText(html_body, "html", "utf-8"))

#     try:
#         if use_ssl:
#             # Direct SSL — used by some providers on port 465
#             ctx = ssl.create_default_context()
#             with smtplib.SMTP_SSL(host, port, context=ctx, timeout=10) as server:
#                 server.login(user, password)
#                 server.sendmail(user, to_email, msg.as_string())
#         else:
#             # STARTTLS — default; works with Gmail, Outlook, Yahoo, SendGrid, etc.
#             with smtplib.SMTP(host, port, timeout=10) as server:
#                 server.ehlo()
#                 server.starttls()
#                 server.ehlo()
#                 server.login(user, password)
#                 server.sendmail(user, to_email, msg.as_string())
#         return True
#     except Exception as e:
#         print(f"[DevNote] Email send failed ({type(e).__name__}): {e}")
#         return False


# # ── Email templates ───────────────────────────────────────────────────────────

# def send_verification_email(to_email: str, username: str, verify_url: str) -> bool:
#     """Send an account verification email."""
#     html = f"""<!DOCTYPE html>
# <html>
# <body style="font-family:-apple-system,sans-serif;background:#f5f5f5;padding:40px 20px;margin:0">
#   <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:12px;
#               padding:40px;box-shadow:0 2px 8px rgba(0,0,0,.08)">
#     <div style="font-family:monospace;font-size:20px;font-weight:700;
#                 color:#f0a030;margin-bottom:24px">DN DevNote</div>
#     <h2 style="margin:0 0 12px;color:#1a1a2e;font-size:20px">Verify your email address</h2>
#     <p style="color:#6b7299;margin:0 0 6px;line-height:1.6">
#       Hi <strong style="color:#1a1a2e">{username}</strong>,
#     </p>
#     <p style="color:#6b7299;margin:0 0 28px;line-height:1.6">
#       Click the button below to verify your email and activate your DevNote account.
#     </p>
#     <a href="{verify_url}"
#        style="display:inline-block;background:#f0a030;color:#0b0b12;text-decoration:none;
#               padding:12px 28px;border-radius:8px;font-weight:600;font-size:15px">
#       Verify Email →
#     </a>
#     <p style="color:#94a3b8;font-size:12px;margin:28px 0 0;line-height:1.6">
#       This link can only be used once.<br>
#       If you didn't create a DevNote account, you can safely ignore this email.
#     </p>
#   </div>
# </body>
# </html>"""
#     return _send_email(to_email, "Verify your DevNote email address", html)


# def send_share_email(to_email: str, sharer_name: str, doc_title: str, share_url: str) -> bool:
#     """Send a document collaboration invite email."""
#     html = f"""<!DOCTYPE html>
# <html>
# <body style="font-family:-apple-system,sans-serif;background:#f5f5f5;padding:40px 20px;margin:0">
#   <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:12px;
#               padding:40px;box-shadow:0 2px 8px rgba(0,0,0,.08)">
#     <div style="font-family:monospace;font-size:20px;font-weight:700;
#                 color:#f0a030;margin-bottom:24px">DN DevNote</div>
#     <h2 style="margin:0 0 12px;color:#1a1a2e;font-size:20px">
#       {sharer_name} wants to collaborate with you
#     </h2>
#     <p style="color:#6b7299;margin:0 0 24px;line-height:1.6">
#       You've been invited to view and edit
#       <strong style="color:#1a1a2e">"{doc_title}"</strong>.
#       Click below to open the document.
#     </p>
#     <a href="{share_url}"
#        style="display:inline-block;background:#f0a030;color:#0b0b12;text-decoration:none;
#               padding:12px 28px;border-radius:8px;font-weight:600;font-size:15px">
#       Open Document →
#     </a>
#     <p style="color:#94a3b8;font-size:12px;margin:24px 0 0;line-height:1.6">
#       You'll need a DevNote account to edit this document.<br>
#       Create one for free when you follow the link.
#     </p>
#   </div>
# </body>
# </html>"""
#     return _send_email(to_email, f'{sharer_name} invited you to collaborate on "{doc_title}"', html)

# ---------------------- RESEND VERSION --------------------------

import os
import resend

# ── Shared Resend API sender ──────────────────────────────────────────────────

def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Send an HTML email via the Resend HTTP API.
    Returns True on success, False if API key is missing or send fails.
    """
    api_key = os.getenv("RESEND_API_KEY")
    
    if not api_key:
        return False  # Resend not configured — caller handles this gracefully

    resend.api_key = api_key
    
    # Uses your verified domain by default
    from_email = os.getenv("RESEND_FROM_EMAIL", "DevNote <noreply@devnote.ca>")

    try:
        params = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_body
        }
        
        resend.Emails.send(params)
        return True
    except Exception as e:
        print(f"[DevNote] Resend API failed ({type(e).__name__}): {e}")
        return False


# ── Email templates ───────────────────────────────────────────────────────────

def send_verification_email(to_email: str, username: str, verify_url: str) -> bool:
    """Send an account verification email."""
    html = f"""<!DOCTYPE html>
<html>
<body style="font-family:-apple-system,sans-serif;background:#f5f5f5;padding:40px 20px;margin:0">
  <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:12px;
              padding:40px;box-shadow:0 2px 8px rgba(0,0,0,.08)">
    <div style="font-family:monospace;font-size:20px;font-weight:700;
                color:#f0a030;margin-bottom:24px">DN DevNote</div>
    <h2 style="margin:0 0 12px;color:#1a1a2e;font-size:20px">Verify your email address</h2>
    <p style="color:#6b7299;margin:0 0 6px;line-height:1.6">
      Hi <strong style="color:#1a1a2e">{username}</strong>,
    </p>
    <p style="color:#6b7299;margin:0 0 28px;line-height:1.6">
      Click the button below to verify your email and activate your DevNote account.
    </p>
    <a href="{verify_url}"
       style="display:inline-block;background:#f0a030;color:#0b0b12;text-decoration:none;
              padding:12px 28px;border-radius:8px;font-weight:600;font-size:15px">
      Verify Email →
    </a>
    <p style="color:#94a3b8;font-size:12px;margin:28px 0 0;line-height:1.6">
      This link can only be used once.<br>
      If you didn't create a DevNote account, you can safely ignore this email.
    </p>
  </div>
</body>
</html>"""
    return _send_email(to_email, "Verify your DevNote email address", html)


def send_share_email(to_email: str, sharer_name: str, doc_title: str, share_url: str) -> bool:
    """Send a document collaboration invite email."""
    html = f"""<!DOCTYPE html>
<html>
<body style="font-family:-apple-system,sans-serif;background:#f5f5f5;padding:40px 20px;margin:0">
  <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:12px;
              padding:40px;box-shadow:0 2px 8px rgba(0,0,0,.08)">
    <div style="font-family:monospace;font-size:20px;font-weight:700;
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
       style="display:inline-block;background:#f0a030;color:#0b0b12;text-decoration:none;
              padding:12px 28px;border-radius:8px;font-weight:600;font-size:15px">
      Open Document →
    </a>
    <p style="color:#94a3b8;font-size:12px;margin:24px 0 0;line-height:1.6">
      You'll need a DevNote account to edit this document.<br>
      Create one for free when you follow the link.
    </p>
  </div>
</body>
</html>"""
    return _send_email(to_email, f'{sharer_name} invited you to collaborate on "{doc_title}"', html)