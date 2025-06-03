import random
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


SMPT_SERVER = "smtp.gmail.com"
SMPT_PORT = 587
SMPT_EMAIL = "binaryvoids@gmail.com"
SMPT_PASSWORD = "joylzzngqgicmlou"

def generate_reset_code():
    return str(random.randint(100000, 999999))


def send_verification_code(email):
    code = generate_reset_code()
    html = f"""
            <html>
    <body style="font-family: 'Segoe UI', sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h2 style="color: #f0c75e; font-family: 'Dancing Script', cursive;">Stockly</h2>
            <h3 style="color: #333;">Verify Your Email</h3>
            <p style="font-size: 16px; color: #555;">
                Use the verification code below to verify your email address:
            </p>
            <div style="font-size: 28px; font-weight: bold; color: #f0c75e; background: #e3f2fd; padding: 10px 20px; border-radius: 8px; display: inline-block;">
                {code}
            </div>
            <p style="margin-top: 20px; font-size: 14px; color: #999;">
                This code will expire in 10 minutes. If you didn't request this, you can ignore this email.
            </p>
            <p style="margin-top: 30px; font-size: 14px; color: #777;">— The Stockly Team</p>
        </div>
    </body>
    </html>
"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMPT_EMAIL
        msg['To'] = email
        msg['Subject'] = "Email verification Code"
        msg.attach(MIMEText(html, 'html'))
        server = smtplib.SMTP(SMPT_SERVER, SMPT_PORT)
        server.starttls()
        server.login(SMPT_EMAIL, SMPT_PASSWORD)
        server.sendmail(SMPT_EMAIL, email, msg.as_string())
        server.quit()
        print("Password code email sent successfully.")
    except Exception as e:
        print(f"Error sending password reset code email: {e}")
        return False
    return code


def send_password_reset_code(email):
    code = generate_reset_code()
    html = f"""
            <html>
    <body style="font-family: 'Segoe UI', sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <h2 style="color: #f0c75e; font-family: 'Dancing Script', cursive;">Stockly</h2>
            <h3 style="color: #333;">Verify Your Email</h3>
            <p style="font-size: 16px; color: #555;">
                Use the verification code below to reset your password:
            </p>
            <div style="font-size: 28px; font-weight: bold; color: #f0c75e; background: #e3f2fd; padding: 10px 20px; border-radius: 8px; display: inline-block;">
                {code}
            </div>
            <p style="margin-top: 20px; font-size: 14px; color: #999;">
                This code will expire in 10 minutes. If you didn't request this, you can ignore this email.
            </p>
            <p style="margin-top: 30px; font-size: 14px; color: #777;">— The Stockly Team</p>
        </div>
    </body>
    </html>
"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMPT_EMAIL
        msg['To'] = email
        msg['Subject'] = "Password reset Code"
        msg.attach(MIMEText(html, 'html'))
        server = smtplib.SMTP(SMPT_SERVER, SMPT_PORT)
        server.starttls()
        server.login(SMPT_EMAIL, SMPT_PASSWORD)
        server.sendmail(SMPT_EMAIL, email, msg.as_string())
        server.quit()
        print("Password code email sent successfully.")
    except Exception as e:
        print(f"Error sending password reset code email: {e}")
        return False
    return code
