from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, SelectField, DateField, PasswordField, HiddenField
from wtforms.validators import DataRequired, Email, Length, NumberRange, EqualTo, ValidationError
from wtforms.widgets import TextArea
from datetime import date
from models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={"class": "form-control"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"class": "form-control"})

class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={"class": "form-control"})
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)], render_kw={"class": "form-control"})
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)], render_kw={"class": "form-control"})
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)], render_kw={"class": "form-control"})
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')], render_kw={"class": "form-control"})
    role = SelectField('Role', choices=[('admin', 'Administrator'), ('worker', 'Worker')], validators=[DataRequired()], render_kw={"class": "form-control"})
    admin_email = StringField('Admin Email (for workers)', render_kw={"class": "form-control"})
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please choose a different one.')
    
    def validate_admin_email(self, admin_email):
        if self.role.data == 'worker':
            if not admin_email.data:
                raise ValidationError('Admin email is required for workers.')
            # Validate email format only if data is provided
            if admin_email.data:
                from wtforms.validators import Email
                email_validator = Email()
                try:
                    email_validator(None, admin_email)
                except ValidationError:
                    raise ValidationError('Please enter a valid email address.')
                
                admin = User.query.filter_by(email=admin_email.data).first()
                if not admin:
                    raise ValidationError(f'No user found with email address: {admin_email.data}. Please check the email address and try again.')
                elif admin.role != 'admin':
                    raise ValidationError(f'The email {admin_email.data} belongs to a {admin.role}, not an administrator. Please enter an admin email address.')

class TaskForm(FlaskForm):
    title = StringField('Task Title', validators=[DataRequired(), Length(min=3, max=200)], render_kw={"class": "form-control"})
    description = TextAreaField('Description', validators=[Length(max=200)], render_kw={"class": "form-control", "rows": 4, "maxlength": "200", "id": "taskDescription"})
    monetary_value = DecimalField('Monetary Value (£)', validators=[DataRequired(), NumberRange(min=0.01)], render_kw={"class": "form-control", "step": "0.01"})
    category = StringField('Category', render_kw={"class": "form-control"})
    priority = SelectField('Priority', choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High')], default='normal', render_kw={"class": "form-control"})

class TaskCompletionForm(FlaskForm):
    task_id = HiddenField('Task ID', validators=[DataRequired()])
    completion_date = DateField('Completion Date', default=date.today, validators=[DataRequired()], render_kw={"class": "form-control"})

class ApprovalForm(FlaskForm):
    completion_id = HiddenField('Completion ID', validators=[DataRequired()])
    status = SelectField('Status', choices=[('approved', 'Approve'), ('rejected', 'Reject')], validators=[DataRequired()], render_kw={"class": "form-control"})
    admin_notes = TextAreaField('Notes', render_kw={"class": "form-control", "rows": 3})

class ReportForm(FlaskForm):
    start_date = DateField('Start Date', validators=[DataRequired()], render_kw={"class": "form-control"})
    end_date = DateField('End Date', validators=[DataRequired()], render_kw={"class": "form-control"})
    worker_id = SelectField('Worker', coerce=int, render_kw={"class": "form-control"})
    status_filter = SelectField('Status Filter', 
                               choices=[('all', 'All'), ('paid', 'Paid'), ('approved', 'Awaiting Payment'), ('rejected', 'Rejected')], 
                               default='all', render_kw={"class": "form-control"})
    priority_filter = SelectField('Priority Filter', 
                                 choices=[('all', 'All'), ('high', 'High'), ('normal', 'Normal'), ('low', 'Low')], 
                                 default='all', render_kw={"class": "form-control"})
    task_status_filter = SelectField('Task Status Filter', 
                                    choices=[('all', 'All'), ('active', 'Active'), ('inactive', 'Inactive')], 
                                    default='all', render_kw={"class": "form-control"})
    
    def validate_end_date(self, end_date):
        if self.start_date.data and end_date.data < self.start_date.data:
            raise ValidationError('End date must be after start date.')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()], render_kw={"class": "form-control"})
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)], render_kw={"class": "form-control"})
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')], render_kw={"class": "form-control"})
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
    
    def validate_current_password(self, current_password):
        if not self.user.check_password(current_password.data):
            raise ValidationError('Current password is incorrect.')

class DeleteAccountForm(FlaskForm):
    confirm_email = StringField('Confirm Your Email', validators=[DataRequired(), Email()], render_kw={"class": "form-control", "placeholder": "Enter your email address"})
    current_password = PasswordField('Current Password', validators=[DataRequired()], render_kw={"class": "form-control", "placeholder": "Enter your current password"})
    confirmation_text = StringField('Type "DELETE" to confirm', validators=[DataRequired()], render_kw={"class": "form-control", "placeholder": "Type DELETE in capital letters"})
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
    
    def validate_confirm_email(self, confirm_email):
        if confirm_email.data != self.user.email:
            raise ValidationError('Email address does not match your account.')
    
    def validate_current_password(self, current_password):
        if not self.user.check_password(current_password.data):
            raise ValidationError('Current password is incorrect.')
    
    def validate_confirmation_text(self, confirmation_text):
        if confirmation_text.data != 'DELETE':
            raise ValidationError('You must type "DELETE" exactly to confirm account deletion.')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()], render_kw={"class": "form-control", "placeholder": "Enter your email address"})
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('No account found with this email address.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)], render_kw={"class": "form-control"})
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')], render_kw={"class": "form-control"})
