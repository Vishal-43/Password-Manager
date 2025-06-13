import random
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "<your_email>"
SMTP_PASSWORD = "<your_password>"

def generate_reset_code():
    return str(random.randint(100000, 999999))


def send_verification_code(email):
    code = generate_reset_code()
    html = f"""
            <!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SecureVault - Email Verification</title>
</head>
<body style="margin: 0; padding: 0; background-color: #F8F9FA; font-family: Arial, sans-serif;">
    <span style="display: none; font-size: 1px; color: #ffffff; line-height: 1px; max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden;">
        Your SecureVault verification code is here.
    </span>

    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
        <tr>
            <td style="padding: 20px 0;" align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);">
                    <tr>
                        <td align="center" style="background-color: #004D40; padding: 30px 20px; border-top-left-radius: 12px; border-top-right-radius: 12px;">
                            <a href="#" target="_blank" style="text-decoration: none;">
                                <span style="font-family: 'Montserrat', Arial, sans-serif; font-size: 28px; color: #E0E0E0; font-weight: 600;">Secure<span style="color: #66CDAA; font-weight: 700;">Vault</span></span>
                            </a>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 30px;">
                            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td style="font-family: 'Montserrat', Arial, sans-serif; font-size: 24px; font-weight: 600; color: #212529; text-align: center;">
                                        Verify Your Email Address
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 20px 0 0 0; font-family: 'Open Sans', Arial, sans-serif; font-size: 16px; color: #343A40; line-height: 1.6; text-align: center;">
                                        Please use the verification code below to complete your action. This code is essential to ensure the security of your account.
                                    </td>
                                </tr>
                                <tr>
                                    <td align="center" style="padding: 30px 0;">
                                        <table border="0" cellpadding="0" cellspacing="0" style="background-color: #F8F9FA; border: 1px solid #CED4DA; border-radius: 8px;">
                                            <tr>
                                                <td align="center" style="font-family: 'Courier New', Courier, monospace; font-size: 36px; font-weight: 700; color: #004D40; padding: 15px 25px; letter-spacing: 4px;">
                                                    {code}
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="font-family: 'Open Sans', Arial, sans-serif; font-size: 14px; color: #555; line-height: 1.6; text-align: center;">
                                        This code will expire in <strong style="color: #212529;">10 minutes</strong>.
                                        <br/>
                                        <strong style="color: #DC3545;">Never share this code with anyone.</strong> Our team will never ask for your verification code.
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 20px 0 0 0; font-family: 'Open Sans', Arial, sans-serif; font-size: 14px; color: #555; line-height: 1.6; text-align: center;">
                                        If you did not request this code, you can safely ignore this email.
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="background-color: #212529; padding: 20px 30px; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;">
                            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td style="font-family: 'Open Sans', Arial, sans-serif; font-size: 12px; color: #CED4DA; text-align: center;">
                                        &copy; 2025 SecureVault. All rights reserved.
                                        <br/>
                                        <span style="color: #66CDAA;">Your trust, secured.</span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
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
            <!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SecureVault - password reset code</title>
</head>
<body style="margin: 0; padding: 0; background-color: #F8F9FA; font-family: Arial, sans-serif;">
    <span style="display: none; font-size: 1px; color: #ffffff; line-height: 1px; max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden;">
        Your SecureVault password reset code is here.
    </span>

    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
        <tr>
            <td style="padding: 20px 0;" align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="600" style="border-collapse: collapse; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);">
                    <tr>
                        <td align="center" style="background-color: #004D40; padding: 30px 20px; border-top-left-radius: 12px; border-top-right-radius: 12px;">
                            <a href="#" target="_blank" style="text-decoration: none;">
                                <span style="font-family: 'Montserrat', Arial, sans-serif; font-size: 28px; color: #E0E0E0; font-weight: 600;">Secure<span style="color: #66CDAA; font-weight: 700;">Vault</span></span>
                            </a>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 30px;">
                            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td style="font-family: 'Montserrat', Arial, sans-serif; font-size: 24px; font-weight: 600; color: #212529; text-align: center;">
                                        Verify Your Email Address
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 20px 0 0 0; font-family: 'Open Sans', Arial, sans-serif; font-size: 16px; color: #343A40; line-height: 1.6; text-align: center;">
                                        Please use the code below to complete your action. This code is essential to ensure the security of your account.
                                    </td>
                                </tr>
                                <tr>
                                    <td align="center" style="padding: 30px 0;">
                                        <table border="0" cellpadding="0" cellspacing="0" style="background-color: #F8F9FA; border: 1px solid #CED4DA; border-radius: 8px;">
                                            <tr>
                                                <td align="center" style="font-family: 'Courier New', Courier, monospace; font-size: 36px; font-weight: 700; color: #004D40; padding: 15px 25px; letter-spacing: 4px;">
                                                    {code}
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="font-family: 'Open Sans', Arial, sans-serif; font-size: 14px; color: #555; line-height: 1.6; text-align: center;">
                                        This code will expire in <strong style="color: #212529;">10 minutes</strong>.
                                        <br/>
                                        <strong style="color: #DC3545;">Never share this code with anyone.</strong> Our team will never ask for your verification code.
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 20px 0 0 0; font-family: 'Open Sans', Arial, sans-serif; font-size: 14px; color: #555; line-height: 1.6; text-align: center;">
                                        If you did not request this code, you can safely ignore this email.
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="background-color: #212529; padding: 20px 30px; border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;">
                            <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td style="font-family: 'Open Sans', Arial, sans-serif; font-size: 12px; color: #CED4DA; text-align: center;">
                                        &copy; 2025 SecureVault. All rights reserved.
                                        <br/>
                                        <span style="color: #66CDAA;">Your trust, secured.</span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
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
