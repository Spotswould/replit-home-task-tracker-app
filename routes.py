from flask import render_template, redirect, url_for, flash, request, abort, make_response, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
import csv
from io import StringIO

from app import app, db, login_manager
from models import User, Task, TaskCompletion
from sqlalchemy import func
from forms import LoginForm, RegisterForm, TaskForm, TaskCompletionForm, ApprovalForm, ReportForm, ChangePasswordForm, DeleteAccountForm, ForgotPasswordForm, ResetPasswordForm
from auth import admin_required, worker_required, owns_worker, owns_task, can_complete_task
from utils import calculate_worker_payment, calculate_admin_payments, get_pending_approvals, get_worker_stats, reset_weekly_tasks, get_week_dates, get_worker_payment_summary, get_all_worker_activity, get_all_admin_activity

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Authentication Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('worker_dashboard'))
    return redirect(url_for('login'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.get_full_name()}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            # Create new user
            user = User(
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                role=form.role.data
            )
            user.set_password(form.password.data)
            
            # If worker, assign to admin
            if form.role.data == 'worker':
                admin = User.query.filter_by(email=form.admin_email.data, role='admin').first()
                if admin:
                    user.admin_id = admin.id
                else:
                    flash('Admin not found. Please check the admin email address.', 'danger')
                    return render_template('register.html', form=form)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Generate reset token
            token = user.generate_reset_token()
            db.session.commit()
            
            # Send email
            from email_utils import send_password_reset_email
            if send_password_reset_email(user, token):
                flash('Password reset instructions have been sent to your email address.', 'success')
            else:
                flash('Failed to send password reset email. Please try again later.', 'danger')
        else:
            # Don't reveal if email exists - security measure
            flash('Password reset instructions have been sent to your email address.', 'success')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html', form=form)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Find user with this token
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.verify_reset_token(token):
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.clear_reset_token()
        db.session.commit()
        flash('Your password has been reset successfully. Please log in with your new password.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', form=form, token=token)

# Admin Routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    # Get admin's workers
    workers = User.query.filter_by(admin_id=current_user.id, role='worker', is_active=True).all()
    
    # Get pending approvals
    pending_approvals = get_pending_approvals(current_user.id)
    
    # Get this week's payment totals
    start_of_week, end_of_week = get_week_dates()
    week_payments = calculate_admin_payments(current_user.id, start_of_week, end_of_week)
    
    # Calculate total awaiting payment (approved but not paid tasks)
    awaiting_payment_total = db.session.query(func.sum(Task.monetary_value)).join(TaskCompletion).filter(
        Task.created_by == current_user.id,
        TaskCompletion.status == 'approved'
    ).scalar() or 0.0
    
    # Get active tasks count
    active_tasks = Task.query.filter_by(created_by=current_user.id, is_active=True).count()
    
    # Get payment summary for each worker
    worker_payment_data = {}
    for worker in workers:
        worker_payment_data[worker.id] = get_worker_payment_summary(worker.id)
    
    return render_template('admin_dashboard.html', 
                         workers=workers,
                         pending_count=len(pending_approvals),
                         week_total=week_payments['grand_total'],
                         awaiting_payment_total=awaiting_payment_total,
                         active_tasks=active_tasks,
                         worker_payment_data=worker_payment_data)

@app.route('/admin/tasks')
@admin_required
def task_list():
    # Get filter parameters from request args
    category_filter = request.args.get('category', 'all')
    priority_filter = request.args.get('priority', 'all')
    status_filter = request.args.get('status', 'all')
    
    # Start with base query
    query = Task.query.filter_by(created_by=current_user.id)
    
    # Apply filters
    if category_filter != 'all':
        if category_filter == 'none':
            query = query.filter(Task.category.is_(None) | (Task.category == ''))
        else:
            query = query.filter(Task.category == category_filter)
    
    if priority_filter != 'all':
        query = query.filter(Task.priority == priority_filter)
    
    if status_filter != 'all':
        if status_filter == 'active':
            query = query.filter(Task.is_active == True)
        else:  # inactive
            query = query.filter(Task.is_active == False)
    
    tasks = query.order_by(Task.created_at.desc()).all()
    
    # Get unique categories for filter dropdown
    all_tasks = Task.query.filter_by(created_by=current_user.id).all()
    categories = set()
    for task in all_tasks:
        if task.category and task.category.strip():
            categories.add(task.category)
    categories = sorted(list(categories))
    
    return render_template('task_list.html', 
                         tasks=tasks, 
                         categories=categories,
                         current_category=category_filter,
                         current_priority=priority_filter,
                         current_status=status_filter)

@app.route('/admin/tasks/new', methods=['GET', 'POST'])
@admin_required
def create_task():
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            monetary_value=form.monetary_value.data,
            category=form.category.data,
            priority=form.priority.data,
            created_by=current_user.id
        )
        db.session.add(task)
        db.session.commit()
        flash('Task created successfully!', 'success')
        return redirect(url_for('task_list'))
    
    return render_template('task_form.html', form=form, title='Create New Task')

@app.route('/admin/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if not owns_task(task_id):
        abort(403)
    
    form = TaskForm(obj=task)
    if form.validate_on_submit():
        form.populate_obj(task)
        task.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        flash('Task updated successfully!', 'success')
        return redirect(url_for('task_list'))
    
    return render_template('task_form.html', form=form, task=task, title='Edit Task')

@app.route('/admin/tasks/<int:task_id>/delete', methods=['POST'])
@admin_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if not owns_task(task_id):
        abort(403)
    
    task.is_active = False
    db.session.commit()
    flash('Task deactivated successfully!', 'success')
    return redirect(url_for('task_list'))

@app.route('/admin/tasks/<int:task_id>/reactivate', methods=['POST'])
@admin_required
def reactivate_task(task_id):
    task = Task.query.get_or_404(task_id)
    if not owns_task(task_id):
        abort(403)
    
    task.is_active = True
    db.session.commit()
    flash('Task reactivated successfully!', 'success')
    return redirect(url_for('task_list'))

@app.route('/admin/approvals')
@admin_required
def approval_queue():
    pending_approvals = get_pending_approvals(current_user.id)
    return render_template('approval_queue.html', approvals=pending_approvals)

@app.route('/admin/approve/<int:completion_id>', methods=['POST'])
@admin_required
def approve_completion(completion_id):
    completion = TaskCompletion.query.get_or_404(completion_id)
    
    # Verify admin owns this task
    if completion.task.created_by != current_user.id:
        abort(403)
    
    # Get form data directly since template uses raw HTML form
    status = request.form.get('status')
    admin_notes = request.form.get('admin_notes', '')
    
    if status and status in ['approved', 'rejected', 'paid']:
        completion.status = status
        completion.admin_notes = admin_notes
        completion.reviewed_at = datetime.now(timezone.utc)
        completion.reviewed_by = current_user.id
        
        db.session.commit()
        
        if status == 'approved':
            status_text = 'approved'
        elif status == 'rejected':
            status_text = 'rejected'
        else:  # paid
            status_text = 'marked as paid'
        flash(f'Task completion {status_text} successfully!', 'success')
    else:
        flash('Invalid approval status provided.', 'error')
    
    return redirect(url_for('approval_queue'))

@app.route('/admin/mark_paid/<int:completion_id>', methods=['POST'])
@admin_required
def mark_as_paid(completion_id):
    completion = TaskCompletion.query.get_or_404(completion_id)
    
    # Verify admin owns this task
    if completion.task.created_by != current_user.id:
        abort(403)
    
    # Only allow marking approved tasks as paid
    if completion.status != 'approved':
        flash('Only approved tasks can be marked as paid.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    completion.status = 'paid'
    completion.reviewed_at = datetime.now(timezone.utc)
    completion.reviewed_by = current_user.id
    
    db.session.commit()
    
    flash(f'Task "{completion.task.title}" marked as paid for {completion.worker.get_full_name()}!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reports', methods=['GET', 'POST'])
@admin_required
def reports():
    form = ReportForm()
    
    # Set up worker choices
    workers = User.query.filter_by(admin_id=current_user.id, role='worker', is_active=True).all()
    form.worker_id.choices = [(-1, 'All Workers')] + [(w.id, w.get_full_name()) for w in workers]
    
    # Set default dates to current week only if not submitted
    start_of_week, end_of_week = get_week_dates()
    if not form.validate_on_submit():
        form.start_date.data = start_of_week
        form.end_date.data = end_of_week
    
    report_data = None
    
    # Generate default report or handle form submission
    if form.validate_on_submit() or request.method == 'GET':
        # Use form data if submitted, otherwise use defaults
        if form.validate_on_submit():
            start_date = form.start_date.data
            end_date = form.end_date.data
            worker_id = form.worker_id.data
            status_filter = form.status_filter.data if form.status_filter.data else 'all'
            priority_filter = form.priority_filter.data if form.priority_filter.data else 'all'
            task_status_filter = form.task_status_filter.data if form.task_status_filter.data else 'all'
        else:
            # Default values for initial page load
            start_date = start_of_week
            end_date = end_of_week
            worker_id = -1  # All workers
            status_filter = 'all'
            priority_filter = 'all'
            task_status_filter = 'all'
        
        if worker_id == -1:
            # All workers report - show activity based on status, priority, and task status filters
            report_data = get_all_admin_activity(current_user.id, start_date, end_date, status_filter, priority_filter, task_status_filter)
            report_data['single_worker'] = False
        else:
            # Single worker report - show activity based on status, priority, and task status filters
            if owns_worker(worker_id):
                worker = User.query.get(worker_id)
                activity_data = get_all_worker_activity(worker_id, start_date, end_date, status_filter, priority_filter, task_status_filter)
                report_data = {
                    'single_worker': True,
                    'worker': worker,
                    'activity_data': activity_data,
                    'period': f"{start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}"
                }
            else:
                abort(403)
    
    return render_template('reports.html', form=form, report_data=report_data)

@app.route('/admin/reports/export')
@admin_required
def export_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    worker_id = request.args.get('worker_id', type=int)
    status_filter = request.args.get('status_filter', 'all')
    priority_filter = request.args.get('priority_filter', 'all')
    task_status_filter = request.args.get('task_status_filter', 'all')
    
    if not start_date or not end_date:
        flash('Missing date parameters for export.', 'danger')
        return redirect(url_for('reports'))
    
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Create CSV content
    output = StringIO()
    writer = csv.writer(output)
    
    if worker_id == -1:
        # All workers report with status, priority, and task status filters
        report_data = get_all_admin_activity(current_user.id, start_date, end_date, status_filter, priority_filter, task_status_filter)
        filter_text = ""
        if status_filter != 'all' or priority_filter != 'all' or task_status_filter != 'all':
            filter_parts = []
            if status_filter != 'all':
                filter_parts.append(status_filter.title())
            if priority_filter != 'all':
                filter_parts.append(f"{priority_filter.title()} Priority")
            if task_status_filter != 'all':
                filter_parts.append(f"{task_status_filter.title()} Tasks")
            filter_text = f" ({', '.join(filter_parts)})"
        writer.writerow([f'Activity Report - All Workers{filter_text}', report_data['period']])
        writer.writerow(['Worker Name', 'Tasks Completed', 'Total Value (£)', 'Paid (£)', 'Awaiting Payment (£)', 'Rejected (£)'])
        
        for worker_id, data in report_data['workers'].items():
            worker = data['worker']
            activity_data = data['activity_data']
            writer.writerow([
                worker.get_full_name(), 
                activity_data['count'], 
                f"£{activity_data['total_value']:.2f}",
                f"£{activity_data['paid_total']:.2f}",
                f"£{activity_data['awaiting_payment']:.2f}",
                f"£{activity_data['rejected_total']:.2f}"
            ])
        
        writer.writerow(['', 'Grand Total:', f"£{report_data['grand_total_value']:.2f}", f"£{report_data['grand_paid_total']:.2f}", f"£{report_data['grand_awaiting_payment']:.2f}", f"£{report_data['grand_rejected_total']:.2f}"])
    else:
        # Single worker report with status, priority, and task status filters
        if not owns_worker(worker_id):
            abort(403)
        
        worker = User.query.get(worker_id)
        activity_data = get_all_worker_activity(worker_id, start_date, end_date, status_filter, priority_filter, task_status_filter)
        filter_text = ""
        if status_filter != 'all' or priority_filter != 'all' or task_status_filter != 'all':
            filter_parts = []
            if status_filter != 'all':
                filter_parts.append(status_filter.title())
            if priority_filter != 'all':
                filter_parts.append(f"{priority_filter.title()} Priority")
            if task_status_filter != 'all':
                filter_parts.append(f"{task_status_filter.title()} Tasks")
            filter_text = f" ({', '.join(filter_parts)})"
        
        writer.writerow([f'Activity Report - {worker.get_full_name()}{filter_text}', f"{start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}"])
        writer.writerow(['Task', 'Completion Date', 'Value (£)', 'Status', 'Reviewed Date'])
        
        for completion in activity_data['completions']:
            writer.writerow([
                completion['task_title'],
                completion['completion_date'].strftime('%d/%m/%Y'),
                f"£{completion['value']:.2f}",
                completion['status'].title(),
                completion['reviewed_date'].strftime('%d/%m/%Y %H:%M') if completion['reviewed_date'] else 'Pending'
            ])
        
        writer.writerow(['', 'Total:', f"£{activity_data['total_value']:.2f}", '', ''])
        writer.writerow(['', 'Paid:', f"£{activity_data['paid_total']:.2f}", '', ''])
        writer.writerow(['', 'Awaiting Payment:', f"£{activity_data['awaiting_payment']:.2f}", '', ''])
        writer.writerow(['', 'Rejected:', f"£{activity_data['rejected_total']:.2f}", '', ''])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    suffix_parts = []
    if status_filter != 'all':
        suffix_parts.append(status_filter)
    if priority_filter != 'all':
        suffix_parts.append(f"{priority_filter}_priority")
    if task_status_filter != 'all':
        suffix_parts.append(f"{task_status_filter}_tasks")
    suffix = f"_{'_'.join(suffix_parts)}" if suffix_parts else ""
    response.headers['Content-Disposition'] = f'attachment; filename=activity_report_{start_date}_{end_date}{suffix}.csv'
    
    return response

@app.route('/admin/reset-weekly', methods=['POST'])
@admin_required
def reset_weekly():
    success, message = reset_weekly_tasks(current_user.id)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin_dashboard'))

# Worker Routes
@app.route('/worker')
@worker_required
def worker_dashboard():
    # Get status filter from request args, default to 'active'
    status_filter = request.args.get('status', 'active')
    # Get completion status filter for recent activity
    completion_filter = request.args.get('completion_status', 'all')
    
    # Get available tasks from worker's admin based on status filter
    if status_filter == 'active':
        query = Task.query.filter_by(created_by=current_user.admin_id, is_active=True)
    elif status_filter == 'inactive':
        query = Task.query.filter_by(created_by=current_user.admin_id, is_active=False)
    else:  # all
        query = Task.query.filter_by(created_by=current_user.admin_id)
    
    available_tasks = query.order_by(Task.priority.desc(), Task.created_at.desc()).all()
    
    # Get worker stats
    stats = get_worker_stats(current_user.id)
    
    # Get recent completions based on completion status filter
    recent_query = TaskCompletion.query.filter_by(worker_id=current_user.id)
    if completion_filter != 'all':
        if completion_filter == 'awaiting_payment':
            recent_query = recent_query.filter_by(status='approved')
        else:
            recent_query = recent_query.filter_by(status=completion_filter)
    
    recent_completions = recent_query.order_by(TaskCompletion.submitted_at.desc()).limit(10).all()
    
    return render_template('worker_dashboard.html', 
                         tasks=available_tasks,
                         stats=stats,
                         recent_completions=recent_completions,
                         current_status=status_filter,
                         current_completion_filter=completion_filter)

@app.route('/worker/complete/<int:task_id>', methods=['GET', 'POST'])
@worker_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if not can_complete_task(task_id):
        abort(403)
    
    form = TaskCompletionForm()
    form.task_id.data = task_id
    
    if form.validate_on_submit():
        # Check if task already completed on this date by this worker
        existing = TaskCompletion.query.filter_by(
            task_id=task_id,
            worker_id=current_user.id,
            completion_date=form.completion_date.data
        ).first()
        
        if existing:
            if existing.status == 'rejected':
                # Allow resubmission for rejected tasks - update the existing record
                existing.status = 'pending'
                existing.admin_notes = None  # Clear previous rejection notes
                existing.submitted_at = datetime.now(timezone.utc)
                existing.reviewed_at = None
                existing.reviewed_by = None
                db.session.commit()
                flash('Task completion resubmitted for approval!', 'success')
                return redirect(url_for('worker_dashboard'))
            elif existing.status in ['pending', 'approved']:
                flash('You have already completed this task on the selected date.', 'warning')
        else:
            completion = TaskCompletion(
                task_id=task_id,
                worker_id=current_user.id,
                completion_date=form.completion_date.data
            )
            db.session.add(completion)
            db.session.commit()
            flash('Task completion submitted for approval!', 'success')
            return redirect(url_for('worker_dashboard'))
    
    return render_template('task_form.html', form=form, task=task, title='Complete Task')

@app.route('/worker/history')
@worker_required
def completion_history():
    # Get filter parameter from request args
    status_filter = request.args.get('filter', 'all')
    
    # Start with base query
    query = TaskCompletion.query.filter_by(worker_id=current_user.id)
    
    # Apply status filter
    if status_filter != 'all':
        if status_filter == 'awaiting_payment':
            query = query.filter_by(status='approved')
        else:
            query = query.filter_by(status=status_filter)
    
    completions = query.order_by(TaskCompletion.submitted_at.desc()).all()
    return render_template('completion_history.html', completions=completions, current_filter=status_filter)

# Profile Routes
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # Password change form
    password_form = ChangePasswordForm(current_user)
    
    if password_form.validate_on_submit():
        current_user.set_password(password_form.new_password.data)
        db.session.commit()
        flash('Password updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    # If worker, get stats for the profile page
    worker_stats = None
    if current_user.is_worker():
        worker_stats = get_worker_stats(current_user.id)
    
    return render_template('profile.html', worker_stats=worker_stats, password_form=password_form)

@app.route('/delete-account', methods=['GET', 'POST'])
@login_required
def delete_account():
    delete_form = DeleteAccountForm(current_user)
    
    if delete_form.validate_on_submit():
        user_email = current_user.email
        user_role = current_user.role
        
        # Handle data cleanup based on user role
        if current_user.is_admin():
            # Check if admin has workers
            worker_count = User.query.filter_by(admin_id=current_user.id, is_active=True).count()
            if worker_count > 0:
                flash(f'Cannot delete account. You have {worker_count} active workers. Please deactivate or transfer them first.', 'error')
                return render_template('delete_account.html', form=delete_form)
            
            # Delete all tasks created by admin (cascade will handle completions)
            Task.query.filter_by(created_by=current_user.id).delete()
        
        elif current_user.is_worker():
            # Delete all task completions by this worker
            TaskCompletion.query.filter_by(worker_id=current_user.id).delete()
        
        # Delete the user account
        db.session.delete(current_user)
        db.session.commit()
        
        # Log out the user
        logout_user()
        
        flash(f'Account {user_email} ({user_role}) has been permanently deleted.', 'info')
        return redirect(url_for('login'))
    
    return render_template('delete_account.html', form=delete_form)

# Error Handlers
@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Context Processors
@app.context_processor
def inject_user():
    return dict(current_user=current_user)
