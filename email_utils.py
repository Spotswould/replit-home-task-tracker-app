import os
from flask import current_app, url_for
from flask_mail import Mail, Message
from app import app

# Initialize Flask-Mail
mail = Mail()

def init_mail(app):
    """Initialize Flask-Mail with the app"""
    # Configure mail settings
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_USERNAME'))
    
    mail.init_app(app)

def send_password_reset_email(user, token):
    """Send password reset email to user"""
    try:
        reset_url = url_for('reset_password', token=token, _external=True)
        
        msg = Message(
            subject='Home Task Tracker - Password Reset Request',
            recipients=[user.email],
            html=f'''
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #007bff; margin-bottom: 10px;">Home Task Tracker</h1>
                        <h2 style="color: #6c757d; font-weight: normal;">Password Reset Request</h2>
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                        <p>Hello {user.get_full_name()},</p>
                        <p>We received a request to reset your password for your Home Task Tracker account.</p>
                        <p>If you requested this password reset, click the button below to create a new password:</p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Reset Password</a>
                    </div>
                    
                    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                        <p style="margin: 0; color: #856404;"><strong>Important:</strong> This link will expire in 1 hour for security reasons.</p>
                    </div>
                    
                    <p style="font-size: 14px; color: #6c757d;">
                        If you didn't request this password reset, you can safely ignore this email. Your password will remain unchanged.
                    </p>
                    
                    <p style="font-size: 14px; color: #6c757d;">
                        If the button above doesn't work, you can copy and paste this link into your browser:<br>
                        <a href="{reset_url}" style="color: #007bff; word-break: break-all;">{reset_url}</a>
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                    
                    <p style="font-size: 12px; color: #adb5bd; text-align: center;">
                        This email was sent from Home Task Tracker. Please do not reply to this email.
                    </p>
                </div>
            </body>
            </html>
            ''',
            body=f'''
            Home Task Tracker - Password Reset Request
            
            Hello {user.get_full_name()},
            
            We received a request to reset your password for your Home Task Tracker account.
            
            If you requested this password reset, please visit the following link to create a new password:
            {reset_url}
            
            Important: This link will expire in 1 hour for security reasons.
            
            If you didn't request this password reset, you can safely ignore this email. Your password will remain unchanged.
            
            This email was sent from Home Task Tracker. Please do not reply to this email.
            '''
        )
        
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email: {str(e)}")
        return False