from datetime import datetime, timedelta, timezone
from decimal import Decimal
from models import TaskCompletion, Task, User
from app import db

def get_week_dates(date_obj=None):
    """Get start and end dates of the week containing the given date"""
    if date_obj is None:
        date_obj = datetime.now(timezone.utc).date()
    
    # Get Monday of the week (start of week)
    days_since_monday = date_obj.weekday()
    start_of_week = date_obj - timedelta(days=days_since_monday)
    end_of_week = start_of_week + timedelta(days=6)
    
    return start_of_week, end_of_week

def calculate_worker_payment(worker_id, start_date, end_date):
    """Calculate total payment for a worker in given date range (approved tasks only)"""
    completions = TaskCompletion.query.join(Task).filter(
        TaskCompletion.worker_id == worker_id,
        TaskCompletion.status == 'approved',
        TaskCompletion.completion_date >= start_date,
        TaskCompletion.completion_date <= end_date
    ).all()
    
    total = Decimal('0.00')
    completion_details = []
    
    for completion in completions:
        total += completion.task.monetary_value
        completion_details.append({
            'task_title': completion.task.title,
            'completion_date': completion.completion_date,
            'value': completion.task.monetary_value,
            'approved_date': completion.reviewed_at,
            'status': completion.status
        })
    
    return {
        'total': total,
        'completions': completion_details,
        'count': len(completion_details)
    }

def get_all_worker_activity(worker_id, start_date, end_date, status_filter='all', priority_filter='all', task_status_filter='all'):
    """Get ALL task completions for a worker in given date range (any status or filtered)"""
    query = TaskCompletion.query.join(Task).filter(
        TaskCompletion.worker_id == worker_id,
        TaskCompletion.completion_date >= start_date,
        TaskCompletion.completion_date <= end_date
    )
    
    # Apply status filter (completion status)
    if status_filter != 'all':
        query = query.filter(TaskCompletion.status == status_filter)
    
    # Apply priority filter
    if priority_filter != 'all':
        query = query.filter(Task.priority == priority_filter)
    
    # Apply task status filter (active/inactive)
    if task_status_filter != 'all':
        if task_status_filter == 'active':
            query = query.filter(Task.is_active == True)
        elif task_status_filter == 'inactive':
            query = query.filter(Task.is_active == False)
    
    completions = query.order_by(TaskCompletion.completion_date.desc()).all()
    
    total_value = Decimal('0.00')
    approved_total = Decimal('0.00')
    paid_total = Decimal('0.00')
    awaiting_payment = Decimal('0.00')
    rejected_total = Decimal('0.00')
    completion_details = []
    
    for completion in completions:
        total_value += completion.task.monetary_value
        if completion.status in ['approved', 'paid']:
            approved_total += completion.task.monetary_value
        if completion.status == 'paid':
            paid_total += completion.task.monetary_value
        elif completion.status == 'approved':
            awaiting_payment += completion.task.monetary_value
        elif completion.status == 'rejected':
            rejected_total += completion.task.monetary_value
            
        completion_details.append({
            'task_title': completion.task.title,
            'completion_date': completion.completion_date,
            'value': completion.task.monetary_value,
            'status': completion.status,
            'reviewed_date': completion.reviewed_at,
            'submitted_date': completion.submitted_at
        })
    
    return {
        'total_value': total_value,
        'approved_total': approved_total,
        'paid_total': paid_total,
        'awaiting_payment': awaiting_payment,
        'rejected_total': rejected_total,
        'completions': completion_details,
        'count': len(completion_details)
    }

def calculate_worker_paid_earnings(worker_id):
    """Calculate total paid earnings for a worker (all time)"""
    completions = TaskCompletion.query.join(Task).filter(
        TaskCompletion.worker_id == worker_id,
        TaskCompletion.status == 'paid'
    ).all()
    
    total = Decimal('0.00')
    completion_details = []
    
    for completion in completions:
        total += completion.task.monetary_value
        completion_details.append({
            'task_title': completion.task.title,
            'completion_date': completion.completion_date,
            'value': completion.task.monetary_value,
            'paid_date': completion.reviewed_at
        })
    
    return {
        'total': total,
        'completions': completion_details,
        'count': len(completion_details)
    }

def calculate_admin_payments(admin_id, start_date, end_date):
    """Calculate payments for all workers under an admin"""
    workers = User.query.filter_by(admin_id=admin_id, role='worker', is_active=True).all()
    
    results = {}
    grand_total = Decimal('0.00')
    
    for worker in workers:
        payment_data = calculate_worker_payment(worker.id, start_date, end_date)
        results[worker.id] = {
            'worker': worker,
            'payment_data': payment_data
        }
        grand_total += payment_data['total']
    
    return {
        'workers': results,
        'grand_total': grand_total,
        'period': f"{start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}"
    }

def get_all_admin_activity(admin_id, start_date, end_date, status_filter='all', priority_filter='all', task_status_filter='all'):
    """Get ALL task activity for all workers under an admin in given date range (any status or filtered)"""
    workers = User.query.filter_by(admin_id=admin_id, role='worker', is_active=True).all()
    
    results = {}
    grand_total_value = Decimal('0.00')
    grand_approved_total = Decimal('0.00')
    grand_paid_total = Decimal('0.00')
    grand_awaiting_payment = Decimal('0.00')
    grand_rejected_total = Decimal('0.00')
    
    for worker in workers:
        activity_data = get_all_worker_activity(worker.id, start_date, end_date, status_filter, priority_filter, task_status_filter)
        results[worker.id] = {
            'worker': worker,
            'activity_data': activity_data
        }
        grand_total_value += activity_data['total_value']
        grand_approved_total += activity_data['approved_total']
        
        # Calculate paid, awaiting payment, and rejected totals
        for completion in activity_data['completions']:
            if completion['status'] == 'paid':
                grand_paid_total += completion['value']
            elif completion['status'] == 'approved':
                grand_awaiting_payment += completion['value']
            elif completion['status'] == 'rejected':
                grand_rejected_total += completion['value']
    
    return {
        'workers': results,
        'grand_total_value': grand_total_value,
        'grand_approved_total': grand_approved_total,
        'grand_paid_total': grand_paid_total,
        'grand_awaiting_payment': grand_awaiting_payment,
        'grand_rejected_total': grand_rejected_total,
        'period': f"{start_date.strftime('%d/%m/%Y')} to {end_date.strftime('%d/%m/%Y')}"
    }

def get_pending_approvals(admin_id):
    """Get all pending task completions for an admin's workers"""
    return TaskCompletion.query.join(Task).join(User, TaskCompletion.worker_id == User.id).filter(
        Task.created_by == admin_id,
        TaskCompletion.status == 'pending'
    ).order_by(TaskCompletion.submitted_at.desc()).all()

def get_approved_tasks_for_payment(admin_id, worker_id=None):
    """Get approved tasks that haven't been paid yet"""
    query = TaskCompletion.query.join(Task).join(User, TaskCompletion.worker_id == User.id).filter(
        Task.created_by == admin_id,
        TaskCompletion.status == 'approved'
    )
    
    if worker_id:
        query = query.filter(TaskCompletion.worker_id == worker_id)
    
    return query.order_by(TaskCompletion.reviewed_at.desc()).all()

def get_worker_payment_summary(worker_id):
    """Get payment summary for a specific worker"""
    approved_tasks = TaskCompletion.query.join(Task).filter(
        TaskCompletion.worker_id == worker_id,
        TaskCompletion.status == 'approved'
    ).all()
    
    paid_tasks = TaskCompletion.query.join(Task).filter(
        TaskCompletion.worker_id == worker_id,
        TaskCompletion.status == 'paid'
    ).all()
    
    approved_total = sum(completion.task.monetary_value for completion in approved_tasks)
    paid_total = sum(completion.task.monetary_value for completion in paid_tasks)
    
    return {
        'approved_count': len(approved_tasks),
        'approved_total': approved_total,
        'paid_count': len(paid_tasks),
        'paid_total': paid_total,
        'unpaid_tasks': approved_tasks
    }

def get_worker_stats(worker_id):
    """Get statistics for a worker"""
    total_completed = TaskCompletion.query.filter_by(worker_id=worker_id).count()
    approved_count = TaskCompletion.query.filter_by(worker_id=worker_id, status='approved').count()
    rejected_count = TaskCompletion.query.filter_by(worker_id=worker_id, status='rejected').count()
    pending_count = TaskCompletion.query.filter_by(worker_id=worker_id, status='pending').count()
    paid_count = TaskCompletion.query.filter_by(worker_id=worker_id, status='paid').count()
    
    # Calculate total awaiting payment (approved but not paid)
    approved_tasks = TaskCompletion.query.join(Task).filter(
        TaskCompletion.worker_id == worker_id,
        TaskCompletion.status == 'approved'
    ).all()
    awaiting_payment_total = sum(completion.task.monetary_value for completion in approved_tasks)
    
    # Calculate total paid earnings
    paid_earnings = calculate_worker_paid_earnings(worker_id)
    
    # Calculate this week's earnings (all approved/paid tasks this week)
    start_of_week, end_of_week = get_week_dates()
    week_payment = calculate_worker_payment(worker_id, start_of_week, end_of_week)
    
    return {
        'total_completed': total_completed,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'pending_count': pending_count,
        'paid_count': paid_count,
        'approval_rate': (approved_count / total_completed * 100) if total_completed > 0 else 0,
        'awaiting_payment_total': awaiting_payment_total,
        'awaiting_payment_count': approved_count,
        'total_paid_earnings': paid_earnings['total'],
        'paid_earnings_count': paid_earnings['count'],
        'this_week_earnings': week_payment['total'],
        'this_week_count': week_payment['count']
    }

def reset_weekly_tasks(admin_id):
    """Reset weekly task completion status for admin's workers"""
    from models import WeeklyReset
    from datetime import date
    
    # Check if reset already done today
    today = date.today()
    existing_reset = WeeklyReset.query.filter_by(admin_id=admin_id, reset_date=today).first()
    
    if existing_reset:
        return False, "Weekly reset already performed today."
    
    # Get all pending completions for this admin's workers
    pending_completions = TaskCompletion.query.join(Task).filter(
        Task.created_by == admin_id,
        TaskCompletion.status == 'pending'
    ).all()
    
    # Remove pending completions (preserve approved/rejected for history)
    for completion in pending_completions:
        db.session.delete(completion)
    
    # Record the reset
    reset_record = WeeklyReset(admin_id=admin_id, reset_date=today)
    db.session.add(reset_record)
    
    try:
        db.session.commit()
        return True, f"Weekly reset completed. {len(pending_completions)} pending tasks reset."
    except Exception as e:
        db.session.rollback()
        return False, f"Error during reset: {str(e)}"
